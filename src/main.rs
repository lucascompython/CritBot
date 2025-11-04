use std::{io::Read, str::FromStr, sync::Arc};

use ahash::RandomState;
use base64::{Engine, prelude::BASE64_STANDARD_NO_PAD};
use lavalink_rs::prelude::*;
use mimalloc::MiMalloc;
use papaya::HashMap;
use serenity::prelude::*;
use songbird::Songbird;
use tracing::error;

use crate::{
    bot_data::BotData,
    config::Config,
    events::{discord_events::Handler, lavalink_events},
    i18n::translations::{Locale, apply_translations},
};

mod bot_data;
mod commands;
mod config;
mod db;
mod events;
mod i18n;

#[global_allocator]
static GLOBAL: MiMalloc = MiMalloc;

async fn setup(bot_config: &'static Config) -> Result<BotData, serenity::Error> {
    let db = db::Db::new().await.expect("Failed to create database pool");
    let guild_cache = {
        let cache = HashMap::builder().hasher(RandomState::new()).build();
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
            pinned_guild_cache.insert(guild_id as u64, bot_data::Guild { locale, prefix });
        }
        drop(pinned_guild_cache);
        cache
    };

    let lavalink = {
        let events = lavalink_rs::model::events::Events {
            raw: Some(lavalink_events::raw_event),
            ready: Some(lavalink_events::ready_event),
            track_start: Some(lavalink_events::track_start),
            track_end: Some(lavalink_events::track_end),
            ..Default::default()
        };

        let bot_id: u64 = {
            // the bot id is stored in the in the first 24 characters of the token encoded in base64

            let token_part = &bot_config.discord.token[0..24];
            let mut decoded_bytes = [0u8; 68]; // 16 bytes = 128 bits
            BASE64_STANDARD_NO_PAD
                .decode_slice(token_part, &mut decoded_bytes)
                .expect("Failed to decode bot id from token");
            let s = unsafe { std::str::from_utf8_unchecked(&decoded_bytes) };
            let s = s.trim_matches('\0');
            s.parse()
                .expect("Failed to parse bot id from decoded token part")
        };

        let node_local = lavalink_rs::node::NodeBuilder {
            hostname: bot_config.lavalink.hostname.clone(),
            is_ssl: bot_config.lavalink.is_ssl,
            events: lavalink_rs::model::events::Events::default(),
            password: bot_config.lavalink.password.clone(),
            user_id: bot_id.into(), // probably better way to get the bot id, still waiting for response from maintainer
            session_id: None,
        };

        lavalink_rs::client::LavalinkClient::new(
            events,
            vec![node_local],
            NodeDistributionStrategy::round_robin(),
        )
        .await
    };

    let manager = Songbird::serenity();

    Ok(BotData {
        db,
        bot_config,
        guild_cache,
        manager,
        lavalink,
    })
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();
    let bot_config: &'static Config =
        Box::leak(Box::new(Config::new().expect("Failed to load config")));

    let mut commands: Vec<poise::Command<BotData, SerenityError>> = vec![
        commands::misc::ping(),
        // commands::misc::help(),
        commands::misc::invite(),
        commands::misc::register(),
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
                    let data = ctx.framework.user_data();
                    let pinned_cache = data.guild_cache.pin();
                    let cached_guild = pinned_cache.get(&ctx.guild_id.unwrap().get()).unwrap();

                    Ok(Some(cached_guild.prefix.clone().into()))
                })
            }),
            ..Default::default()
        },

        ..Default::default()
    };

    let framework = poise::Framework::builder().options(options).build();

    let bot_data = match setup(bot_config).await {
        Ok(data) => data,
        Err(why) => {
            error!("Failed to setup bot data: {:?}", why);
            return;
        }
    };

    let intents = GatewayIntents::all();

    let token = serenity::secrets::Token::from_str(&bot_config.discord.token).unwrap();

    let mut client = poise::serenity_prelude::ClientBuilder::new(token, intents)
        .event_handler(Handler)
        .voice_manager::<Songbird>(bot_data.manager.clone())
        .compression(serenity::all::TransportCompression::None)
        .framework(framework)
        .data(Arc::new(bot_data))
        .activity(serenity::all::ActivityData::custom(":)"))
        .await
        .expect("Err creating client");

    if let Err(why) = client.start().await {
        error!("Client error: {:?}", why);
    }
}
