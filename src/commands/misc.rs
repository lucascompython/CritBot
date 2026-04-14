use i18n_macros::i18n_command;
use poise::command;

use crate::bot_data::{Context, Error};

// TODO: Translate help command, show localized names(aliases) and descriptions
// TODO: Fix help command
// A command to display help information about the bot's commands.
// #[command(prefix_command, slash_command, aliases("h"))]
#[i18n_command(
    prefix_command,
    slash_command,
    aliases("h"),
    category = "Misc",
    hide_in_help
)]
pub async fn help(ctx: Context<'_>, command: Option<String>) -> Result<(), Error> {
    let discord_locale_code = locale.discord_code();

    if let Some(cmd_name) = command {
        if let Some(cmd) = ctx
            .framework()
            .options
            .commands
            .iter()
            .find(|c| c.name == cmd_name || c.aliases.contains(&Cow::Borrowed(&cmd_name)))
        {
            let default_desc = Cow::Owned(t!(NoDescription));
            let description = if let Some((_, desc)) = cmd
                .description_localizations
                .iter()
                .find(|(loc, _)| loc == discord_locale_code)
            {
                desc
            } else {
                cmd.description.as_ref().unwrap_or(&default_desc)
            };

            let cmd_params = cmd
                .parameters
                .iter()
                .map(|param| {
                    let default_param_desc = Cow::Owned(t!(NoDescription));
                    let param_desc = if let Some((_, desc)) = param
                        .description_localizations
                        .iter()
                        .find(|(loc, _)| loc == discord_locale_code)
                    {
                        desc
                    } else {
                        param.description.as_ref().unwrap_or(&default_param_desc)
                    };
                    format!("<{}: {}>", param.name, param_desc)
                })
                .collect::<Vec<_>>()
                .join(" ");

            let aliases = if !cmd.aliases.is_empty() {
                format!(" (aliases: {})", cmd.aliases.join(", "))
            } else {
                String::new()
            };

            ctx.reply(format!(
                "**/{} {}**: {}{}",
                cmd.name, cmd_params, description, aliases
            ))
            .await?;
        } else {
            ctx.reply(t!(CmdNotFound, command = &cmd_name)).await?;
        }
    } else {
        let mut categories = std::collections::BTreeMap::new();

        for cmd in ctx.framework().options.commands.iter() {
            if cmd.hide_in_help {
                continue;
            }
            let default_category: Cow<'_, str> = Cow::Owned(t!(Uncategorized));
            let category = cmd
                .category
                .clone()
                .unwrap_or_else(|| default_category.clone());
            let entry = categories.entry(category).or_insert_with(Vec::new);

            let default_uncategorized: Cow<'_, str> = Cow::Owned(t!(Uncategorized));
            let (name, description): (&str, Cow<'_, str>) = if let Some(((_, name), (_, desc))) =
                cmd.name_localizations
                    .iter()
                    .zip(cmd.description_localizations.iter())
                    .find(|((loc, _), _)| loc == discord_locale_code)
            {
                (name, Cow::Borrowed(desc))
            } else {
                let desc = cmd.description.clone();
                (
                    &cmd.name,
                    desc.unwrap_or_else(|| default_uncategorized.clone()),
                )
            };

            entry.push((name, description));
        }

        let mut help_message = String::new();
        for (category, cmds) in categories {
            help_message.push_str(&format!("**{}:**\n", category));
            for (name, description) in cmds {
                help_message.push_str(&format!("  /{}  {}\n", name, description));
            }
            help_message.push('\n');
        }

        let prefix = {
            let data = ctx.data();
            let pinned_cache = data.guild_cache.pin();
            let cached_guild = pinned_cache.get(&ctx.guild_id().unwrap().get()).unwrap();
            cached_guild.prefix.clone() // TODO: see if it possible to not have to clone this
        };

        help_message.push_str(&t!(TypeHelper, prefix = &prefix));

        ctx.reply(help_message).await?;
    }

    Ok(())
}

/// A simple ping command to check if the bot is online.
#[command(prefix_command, slash_command, category = "Misc")]
pub async fn ping(ctx: Context<'_>) -> Result<(), Error> {
    ctx.reply("Pong!").await?;

    Ok(())
}

#[poise::command(prefix_command, owners_only, hide_in_help)]
pub async fn register(ctx: Context<'_>) -> Result<(), Error> {
    poise::samples::register_application_commands_buttons(ctx).await?;
    Ok(())
}

#[i18n_command(prefix_command, slash_command, category = "Misc")]
pub async fn hey(ctx: Context<'_>) -> Result<(), Error> {
    ctx.reply(t!(Response)).await?;

    let user = ctx.author().name.to_uppercase();

    ctx.say(t!(Messages::Greeting, user = user.as_str()))
        .await?;

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
