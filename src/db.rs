use deadpool_postgres::Pool;

pub struct Db(Pool);

impl Db {
    pub fn new() -> Result<Self, deadpool_postgres::CreatePoolError> {
        // TODO: Run the schema here
        let config = deadpool_postgres::Config {
            user: Some("lucas".to_string()),
            dbname: Some("crit".to_string()),
            manager: Some(deadpool_postgres::ManagerConfig {
                recycling_method: deadpool_postgres::RecyclingMethod::Fast,
            }),
            host: Some("/run/postgresql".to_string()),
            ..Default::default()
        };

        let pool = config.create_pool(
            Some(deadpool_postgres::Runtime::Tokio1),
            tokio_postgres::NoTls,
        );

        match pool {
            Ok(p) => Ok(Db(p)),
            Err(e) => Err(e),
        }
    }

    pub async fn get_pool(&self) -> deadpool_postgres::Object {
        self.0.get().await.unwrap()
    }
}
