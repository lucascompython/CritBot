use mimalloc::MiMalloc;
use serenity::{
    client::{ClientBuilder, FullEvent},
    prelude::*,
};
use tracing::{error, info};

use crate::{config::Config, context::Data};

mod commands;
mod config;
mod context;

#[global_allocator]
static GLOBAL: MiMalloc = MiMalloc;

async fn event_handler(
    _ctx: &Context,
    event: &FullEvent,
    _framework: poise::FrameworkContext<'_, Data, serenity::Error>,
) -> Result<(), serenity::Error> {
    match event {
        FullEvent::Ready { data_about_bot, .. } => {
            info!("Logged in as {}", data_about_bot.user.name);
        }
        FullEvent::GuildCreate { guild, is_new } => {
            if *is_new == Some(true) {
                info!("Joined new guild: {} (id {})", guild.name, guild.id);
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
    let config = Config::new().expect("Failed to load config");

    let options = poise::FrameworkOptions::<Data, serenity::Error> {
        commands: vec![commands::misc::ping(), commands::misc::help()],
        prefix_options: poise::PrefixFrameworkOptions {
            prefix: Some(".".into()),
            mention_as_prefix: true,
            ignore_bots: true,
            case_insensitive_commands: true,
            ..Default::default()
        },

        event_handler: |ctx, event, framework, _data| {
            Box::pin(event_handler(ctx, event, framework))
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
                Ok(Data { pool })
            })
        })
        .options(options)
        .build();

    let intents = GatewayIntents::non_privileged()
        | GatewayIntents::MESSAGE_CONTENT
        | GatewayIntents::DIRECT_MESSAGES;

    let mut client = ClientBuilder::new(&config.discord_token, intents)
        .framework(framework)
        .await
        .expect("Err creating client");

    if let Err(why) = client.start().await {
        error!("Client error: {:?}", why);
    }
}
