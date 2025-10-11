use mimalloc::MiMalloc;
use serenity::{
    client::{ClientBuilder, FullEvent},
    prelude::*,
};

use crate::config::Config;

mod commands;
mod config;

#[global_allocator]
static GLOBAL: MiMalloc = MiMalloc;

async fn event_handler(
    _ctx: &Context,
    event: &FullEvent,
    _framework: poise::FrameworkContext<'_, (), serenity::Error>,
) -> Result<(), serenity::Error> {
    if let FullEvent::Ready { data_about_bot, .. } = event {
        println!("Logged in as {}", data_about_bot.user.name);
    }
    Ok(())
}

#[tokio::main]
async fn main() {
    let config = Config::new().expect("Failed to load config");

    let options = poise::FrameworkOptions {
        commands: vec![commands::misc::ping(), commands::misc::help()],
        prefix_options: poise::PrefixFrameworkOptions {
            prefix: Some(".".into()),
            mention_as_prefix: true,
            ignore_bots: true,
            case_insensitive_commands: true,
            ..Default::default()
        },
        event_handler: |ctx, event, framework, ()| Box::pin(event_handler(ctx, event, framework)),
        ..Default::default()
    };

    let framework = poise::Framework::builder()
        .setup(move |ctx, _ready, framework| {
            Box::pin(async move {
                poise::builtins::register_globally(ctx, &framework.options().commands).await?;
                Ok(())
            })
        })
        .options(options)
        .build();

    let intents = GatewayIntents::GUILD_MESSAGES | GatewayIntents::MESSAGE_CONTENT;

    let mut client = ClientBuilder::new(&config.discord_token, intents)
        .framework(framework)
        .await
        .expect("Err creating client");

    if let Err(why) = client.start().await {
        println!("Client error: {:?}", why);
    }
}
