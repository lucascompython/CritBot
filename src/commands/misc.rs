use poise::{Context, command};

type Error = serenity::Error;

/// A command to display help information about the bot's commands.
#[command(prefix_command, slash_command)]
pub async fn help(ctx: Context<'_, (), Error>, command: Option<String>) -> Result<(), Error> {
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
#[command(prefix_command, slash_command)]
pub async fn ping(ctx: Context<'_, (), Error>) -> Result<(), Error> {
    ctx.reply("Pong!").await?;

    Ok(())
}
