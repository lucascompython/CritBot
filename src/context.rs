use ahash::RandomState;
use papaya::HashMap;

use crate::db;

pub struct Guild {
    pub locale: Option<crate::i18n::translations::Locale>,
}

pub struct BotData {
    pub db: db::Db,
    pub bot_config: &'static crate::config::Config,
    pub guild_cache: HashMap<u64, Guild, RandomState>,
}

pub type Context<'a> = poise::Context<'a, BotData, serenity::Error>;
