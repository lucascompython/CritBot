use deadpool_postgres::Pool;

pub struct Db(Pool);

const SCHEMA: &str = include_str!("../sql/schema.sql");

impl Db {
    pub async fn new() -> Result<Self, deadpool_postgres::CreatePoolError> {
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
            Ok(p) => {
                let client = p.get().await.unwrap();
                client.batch_execute(SCHEMA).await.unwrap();

                Ok(Db(p))
            }
            Err(e) => Err(e),
        }
    }

    pub async fn get_pool(&self) -> deadpool_postgres::Object {
        self.0.get().await.unwrap()
    }
}
