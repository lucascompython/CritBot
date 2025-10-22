use i18n_macros::i18n_command;
use poise::command;
use serenity::Error;

use crate::bot_data::Context;

// TODO: Translate help command, show localized names(aliases) and descriptions
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
    ctx.reply(t!(Response)).await?;

    let user = ctx.author().name.to_uppercase();

    ctx.say(t!(Messages::Greeting, user = user.as_str()))
        .await?;

    let bot_name = t!(global::BotName);
    ctx.say(format!("I am {}!", bot_name)).await?;

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
