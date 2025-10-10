use poise::{Context, command};

type Error = serenity::Error;

#[command(prefix_command, slash_command)]
pub async fn help(ctx: Context<'_, (), Error>, command: Option<String>) -> Result<(), Error> {
    let configuration = poise::builtins::HelpConfiguration {
        ephemeral: false,
        show_context_menu_commands: true,
        show_subcommands: true,
        include_description: true,
        ..Default::default()
    };
    poise::builtins::help(ctx, command.as_deref(), configuration).await?;
    Ok(())
}

#[command(prefix_command, slash_command)]
pub async fn ping(ctx: Context<'_, (), Error>) -> Result<(), Error> {
    ctx.reply("Pong!").await?;

    Ok(())
}
