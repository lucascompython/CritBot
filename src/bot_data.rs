use ahash::RandomState;
use papaya::HashMap;

use crate::{db, i18n::translations::Locale};

pub struct Guild {
    pub locale: Option<crate::i18n::translations::Locale>,
}

pub type Context<'a> = poise::Context<'a, BotData, serenity::Error>;

pub struct BotData {
    pub db: db::Db,
    pub bot_config: &'static crate::config::Config,
    pub guild_cache: HashMap<u64, Guild, RandomState>,
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

        let pinned_guild_cache = self.guild_cache.pin();
        pinned_guild_cache.insert(
            guild_id,
            crate::bot_data::Guild {
                locale: Some(locale),
            },
        );

        Ok(())
    }
}
