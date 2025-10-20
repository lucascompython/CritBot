use i18n_macro::i18n_command;
use poise::command;
use tracing::error;

use crate::{
    context::Context,
    i18n::translations::{Locale, change_locale},
};

type Error = serenity::Error;

/// A command to display help information about the bot's commands.
#[command(prefix_command, slash_command, aliases("h"))]
pub async fn help(ctx: Context<'_>, command: Option<String>) -> Result<(), Error> {
    let configuration = poise::builtins::HelpConfiguration {
        extra_text_at_bottom: "Type `.help <command>` for more info on a command.",
        ephemeral: false,
        show_context_menu_commands: true,
        show_subcommands: true,
        include_description: true,
        ..Default::default()
    };
    poise::builtins::help(ctx, command.as_deref(), configuration).await?;
    Ok(())
}

/// A simple ping command to check if the bot is online.
#[command(prefix_command, slash_command, category = "Misc")]
pub async fn ping(ctx: Context<'_>) -> Result<(), Error> {
    ctx.reply("Pong!").await?;

    Ok(())
}

#[i18n_command(prefix_command, slash_command, category = "Misc")]
pub async fn hey(ctx: Context<'_>) -> Result<(), Error> {
    ctx.reply(t!(Hey)).await?;

    Ok(())
}

// TODO: Translate descriptions, etc.

/// Change the bot's locale for the current guild.
#[i18n_command(prefix_command, slash_command, category = "Misc")]
pub async fn locale(ctx: Context<'_>, locale: Locale) -> Result<(), Error> {
    if let Err(e) = change_locale(ctx, locale).await {
        error!("Error changing locale: {}", e);
        ctx.say(t!(ChangeLocale::ErrorUpdating)).await?;
    }

    Ok(())
}

/// Get the bot's invite link.
#[command(prefix_command, slash_command, category = "Misc")]
pub async fn invite(ctx: Context<'_>) -> Result<(), Error> {
    let invite_link = &ctx.data().bot_config.discord.invite_link;
    ctx.say(format!(
        "Invite me to your server by clicking [here]({})!",
        invite_link
    ))
    .await?;

    Ok(())
}
