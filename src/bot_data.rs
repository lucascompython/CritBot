use std::sync::Arc;

use ahash::RandomState;
use lavalink_rs::client::LavalinkClient;
use papaya::HashMap;

use crate::{db, i18n::translations::Locale};

pub struct Guild {
    pub locale: Option<crate::i18n::translations::Locale>,
    pub prefix: String,
}

// pub type Error = Box<dyn std::error::Error + Send + Sync>;
// define error enum for all the bots errors

#[derive(thiserror::Error, Debug)]
pub enum Error {
    #[error("Database error: {0}")]
    Database(#[from] tokio_postgres::Error),
    #[error("Lavalink error: {0}")]
    Lavalink(#[from] lavalink_rs::error::LavalinkError),
    #[error("Serenity error: {0}")]
    Serenity(#[from] serenity::Error),
    #[error("Songbird join error: {0}")]
    SongbirdJoin(#[from] songbird::error::JoinError),
    #[error("IO error: {0}")]
    Other(String),
}

pub type Context<'a> = poise::Context<'a, BotData, Error>;

pub struct BotData {
    pub db: db::Db,
    pub bot_config: &'static crate::config::Config,
    pub guild_cache: HashMap<u64, Guild, RandomState>,
    pub manager: Arc<songbird::Songbird>,
    pub lavalink: LavalinkClient,
}

impl BotData {
    /// Insert or update the guild locale in the database and cache
    pub async fn update_guild_locale(
        &self,
        locale: Locale,
        guild_id: u64,
    ) -> Result<(), tokio_postgres::Error> {
        let pool = self.db.get_pool().await;
        let stmt = pool
                .prepare_cached("INSERT INTO guilds (locale, id) VALUES ($1, $2) ON CONFLICT (id) DO UPDATE SET locale = EXCLUDED.locale")
                .await?;

        let guild_id_i64 = guild_id as i64;
        pool.execute(&stmt, &[&locale, &guild_id_i64]).await?;

        let pinned_guild_cache = self.guild_cache.pin_owned();

        pinned_guild_cache.update_or_insert(
            guild_id,
            |guild| crate::bot_data::Guild {
                locale: Some(locale),
                prefix: guild.prefix.clone(),
            },
            crate::bot_data::Guild {
                locale: Some(locale),
                prefix: self.bot_config.discord.default_prefix.clone(),
            },
        );

        Ok(())
    }

    pub async fn update_guild_prefix(
        &self,
        prefix: String,
        guild_id: u64,
    ) -> Result<(), tokio_postgres::Error> {
        let pool = self.db.get_pool().await;
        let stmt = pool
                .prepare_cached("INSERT INTO guilds (prefix, id) VALUES ($1, $2) ON CONFLICT (id) DO UPDATE SET prefix = EXCLUDED.prefix")
                .await?;

        let guild_id_i64 = guild_id as i64;
        pool.execute(&stmt, &[&prefix, &guild_id_i64]).await?;

        let pinned_guild_cache = self.guild_cache.pin_owned();

        pinned_guild_cache.update_or_insert(
            guild_id,
            |guild| crate::bot_data::Guild {
                locale: guild.locale,
                prefix: prefix.clone(),
            },
            crate::bot_data::Guild {
                locale: None,
                prefix: prefix.clone(),
            },
        );

        Ok(())
    }
}
