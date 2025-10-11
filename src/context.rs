pub struct BotData {
    pub pool: deadpool_postgres::Pool,
    pub bot_config: &'static crate::config::Config,
}

pub type Context<'a> = poise::Context<'a, BotData, serenity::Error>;
