use serenity::{
    async_trait,
    gateway::client::{Context, EventHandler, FullEvent},
};
use tracing::{error, info};

use crate::bot_data::BotData;

pub struct Handler;
#[async_trait]
impl EventHandler for Handler {
    async fn dispatch(&self, ctx: &Context, event: &FullEvent) {
        match event {
            FullEvent::Ready { data_about_bot, .. } => {
                info!("Logged in as {}", data_about_bot.user.name);
            }
            FullEvent::GuildCreate { guild, is_new, .. } => {
                if *is_new == Some(true) {
                    info!("Joined new guild: {} (id {})", guild.name, guild.id);

                    let data = ctx.data::<BotData>();
                    let pool = data.db.get_pool().await;
                    let stmt = pool
                        .prepare_cached(
                            "INSERT INTO guilds (id) VALUES ($1) ON CONFLICT (id) DO NOTHING",
                        )
                        .await
                        .unwrap();
                    let guild_id = guild.id.get();
                    data.guild_cache.pin().insert(
                        guild_id,
                        crate::bot_data::Guild {
                            locale: None,
                            prefix: data.bot_config.discord.default_prefix.clone(),
                        },
                    );

                    if let Err(e) = pool.execute(&stmt, &[&(guild_id as i64)]).await {
                        error!("Failed to insert guild into database: {}", e);
                    }
                }
            }

            FullEvent::GuildDelete {
                incomplete, full, ..
            } => {
                if !incomplete.unavailable {
                    let guild_name = if let Some(full) = full {
                        &full.name
                    } else {
                        "Unknown"
                    };
                    info!("Removed from guild: {} (id {})", guild_name, incomplete.id);

                    let data = ctx.data::<BotData>();

                    let pool = data.db.get_pool().await;
                    let stmt = pool
                        .prepare_cached("DELETE FROM guilds WHERE id = $1")
                        .await
                        .unwrap();
                    let guild_id = incomplete.id.get();

                    data.guild_cache.pin().remove(&guild_id);

                    if let Err(e) = pool.execute(&stmt, &[&(guild_id as i64)]).await {
                        error!("Failed to remove guild from database: {}", e);
                    }
                } else if let Some(full) = full {
                    info!("Guild became unavailable: {} (id {})", full.name, full.id);
                }
            }
            _ => {}
        }
    }
}
