use mimalloc::MiMalloc;
use serenity::{
    client::{ClientBuilder, FullEvent},
    prelude::*,
};
use tracing::{error, info};

use crate::{config::Config, context::BotData};

mod commands;
mod config;
mod context;

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

                let pool = data.pool.get().await.unwrap();
                let stmt = pool
                    .prepare_cached(
                        "INSERT INTO guilds (id) VALUES ($1) ON CONFLICT (id) DO NOTHING",
                    )
                    .await
                    .unwrap();
                let guild_id = guild.id.get() as i64;

                if let Err(e) = pool.execute(&stmt, &[&guild_id]).await {
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

    let options = poise::FrameworkOptions::<BotData, serenity::Error> {
        commands: vec![
            commands::misc::ping(),
            commands::misc::help(),
            commands::misc::invite(),
        ],
        prefix_options: poise::PrefixFrameworkOptions {
            prefix: Some(".".into()),
            mention_as_prefix: true,
            ignore_bots: true,
            case_insensitive_commands: true,
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
                let config = deadpool_postgres::Config {
                    user: Some("lucas".to_string()),
                    dbname: Some("crit".to_string()),
                    manager: Some(deadpool_postgres::ManagerConfig {
                        recycling_method: deadpool_postgres::RecyclingMethod::Fast,
                    }),
                    host: Some("/run/postgresql".to_string()),
                    ..Default::default()
                };

                let pool = config
                    .create_pool(
                        Some(deadpool_postgres::Runtime::Tokio1),
                        tokio_postgres::NoTls,
                    )
                    .expect("Failed to create pool");

                poise::builtins::register_globally(ctx, &framework.options().commands).await?;
                Ok(BotData { pool, bot_config })
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
