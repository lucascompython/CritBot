pub struct Data {
    pub pool: deadpool_postgres::Pool,
}

pub type Context<'a> = poise::Context<'a, Data, serenity::Error>;
