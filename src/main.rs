use ahash::RandomState;
use mimalloc::MiMalloc;
use papaya::HashMap;
use serenity::{
    client::{ClientBuilder, FullEvent},
    prelude::*,
};
use tracing::{error, info};

use crate::{
    bot_data::BotData,
    config::Config,
    i18n::translations::{Locale, apply_translations},
};

mod bot_data;
mod commands;
mod config;
mod db;
mod i18n;

#[global_allocator]
static GLOBAL: MiMalloc = MiMalloc;

async fn event_handler(
    _ctx: &Context,
    event: &FullEvent,
    _framework: poise::FrameworkContext<'_, BotData, serenity::Error>,
    data: &BotData,
) -> Result<(), serenity::Error> {
    match event {
        FullEvent::Ready { data_about_bot, .. } => {
            info!("Logged in as {}", data_about_bot.user.name);
        }
        FullEvent::GuildCreate { guild, is_new } => {
            if *is_new == Some(true) {
                info!("Joined new guild: {} (id {})", guild.name, guild.id);

                let pool = data.db.get_pool().await;
                let stmt = pool
                    .prepare_cached(
                        "INSERT INTO guilds (id) VALUES ($1) ON CONFLICT (id) DO NOTHING",
                    )
                    .await
                    .unwrap();
                let guild_id = guild.id.get();
                data.guild_cache.pin().insert(
                    guild_id,
                    crate::bot_data::Guild {
                        locale: None,
                        prefix: data.bot_config.discord.default_prefix.clone(),
                    },
                );

                if let Err(e) = pool.execute(&stmt, &[&(guild_id as i64)]).await {
                    error!("Failed to insert guild into database: {}", e);
                }
            }
        }

        FullEvent::GuildDelete { incomplete, full } => {
            if !incomplete.unavailable {
                let guild_name = if let Some(full) = full {
                    &full.name
                } else {
                    "Unknown"
                };
                info!("Removed from guild: {} (id {})", guild_name, incomplete.id);

                let pool = data.db.get_pool().await;
                let stmt = pool
                    .prepare_cached("DELETE FROM guilds WHERE id = $1")
                    .await
                    .unwrap();
                let guild_id = incomplete.id.get();

                data.guild_cache.pin().remove(&guild_id);

                if let Err(e) = pool.execute(&stmt, &[&(guild_id as i64)]).await {
                    error!("Failed to remove guild from database: {}", e);
                }
            } else if let Some(full) = full {
                info!("Guild became unavailable: {} (id {})", full.name, full.id);
            }
        }
        _ => {}
    }

    Ok(())
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();
    let bot_config: &'static Config =
        Box::leak(Box::new(Config::new().expect("Failed to load config")));

    let mut commands: Vec<poise::Command<BotData, SerenityError>> = vec![
        commands::misc::ping(),
        commands::misc::help(),
        commands::misc::invite(),
        commands::misc::hey(),
        commands::config::change_locale(),
        commands::config::change_prefix(),
    ];

    apply_translations(&mut commands);

    let options = poise::FrameworkOptions::<BotData, serenity::Error> {
        commands,
        prefix_options: poise::PrefixFrameworkOptions {
            mention_as_prefix: true,
            ignore_bots: true,
            case_insensitive_commands: true,
            dynamic_prefix: Some(|ctx| {
                Box::pin(async move {
                    let pinned_cache = ctx.data.guild_cache.pin();
                    let cached_guild = pinned_cache.get(&ctx.guild_id.unwrap().get()).unwrap();

                    Ok(Some(cached_guild.prefix.to_string()))
                })
            }),
            ..Default::default()
        },

        event_handler: |ctx, event, framework, data| {
            Box::pin(event_handler(ctx, event, framework, data))
        },
        ..Default::default()
    };

    let framework = poise::Framework::builder()
        .setup(move |ctx, _ready, framework| {
            Box::pin(async move {
                let db = db::Db::new().await.expect("Failed to create database pool");

                let guild_cache = {
                    let cache = HashMap::builder()
                        .hasher(RandomState::new())
                        .capacity(ctx.cache.guild_count())
                        .build();

                    let db_pool = db.get_pool().await;
                    let stmt = db_pool
                        .prepare_cached("SELECT id, locale, prefix FROM guilds")
                        .await
                        .unwrap();
                    let rows = db_pool.query(&stmt, &[]).await.unwrap();

                    let pinned_guild_cache = cache.pin();
                    for row in rows {
                        let guild_id: i64 = row.get(0);
                        let locale: Option<Locale> = row.get(1);
                        let prefix: String = row.get(2);
                        pinned_guild_cache
                            .insert(guild_id as u64, bot_data::Guild { locale, prefix });
                    }

                    drop(pinned_guild_cache);

                    cache
                };

                poise::builtins::register_globally(ctx, &framework.options().commands).await?;
                Ok(BotData {
                    db,
                    bot_config,
                    guild_cache,
                })
            })
        })
        .options(options)
        .build();

    let intents = GatewayIntents::non_privileged()
        | GatewayIntents::MESSAGE_CONTENT
        | GatewayIntents::DIRECT_MESSAGES;

    let mut client = ClientBuilder::new(&bot_config.discord.token, intents)
        .framework(framework)
        .await
        .expect("Err creating client");

    if let Err(why) = client.start().await {
        error!("Client error: {:?}", why);
    }
}
