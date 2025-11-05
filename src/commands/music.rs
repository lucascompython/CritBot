use i18n_macros::i18n_command;
use serenity::Error;

use crate::bot_data::Context;

#[i18n_command(
    prefix_command,
    slash_command,
    aliases("p", "toca")
    category = "Music",
)]
pub async fn play(ctx: Context<'_>, query: String) -> Result<(), Error> {
    ctx.reply("play").await?;
    Ok(())
}
