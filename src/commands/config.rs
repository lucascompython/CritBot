use i18n_macros::i18n_command;
use serenity::Error;
use tracing::error;

use crate::{bot_data::Context, i18n::translations::Locale};

// TODO: Translate descriptions, etc.
#[i18n_command(prefix_command, slash_command, category = "Config")]
pub async fn change_locale(ctx: Context<'_>, new_locale: Locale) -> Result<(), Error> {
    if let Err(e) = change_locale_logic(ctx, new_locale).await {
        error!("Error changing locale: {}", e);
        ctx.say(t!(ErrorUpdating)).await?;
    }

    Ok(())
}

async fn change_locale_logic(
    ctx: crate::bot_data::Context<'_>,
    locale: Locale,
) -> Result<(), Error> {
    let guild_id = ctx.guild_id().unwrap().get();

    let pref = ctx.guild().unwrap().preferred_locale.clone();

    let ctx_data = &ctx.data();

    enum Action {
        AlreadySet,
        Update,
    }

    let action = {
        let pinned_guild_cache = ctx_data.guild_cache.pin();
        match pinned_guild_cache.get(&guild_id) {
            Some(guild) => {
                if let Some(custom_locale) = &guild.locale {
                    if custom_locale == &locale {
                        Action::AlreadySet
                    } else {
                        Action::Update
                    }
                } else if Locale::from_code(&pref) == locale {
                    Action::AlreadySet
                } else {
                    Action::Update
                }
            }
            None => Action::Update,
        }
    };

    match action {
        Action::AlreadySet => {
            let msg = crate::i18n::t!(&ctx, commands::config::change_locale::AlreadySet);
            ctx.say(msg).await?;
            Ok(())
        }
        Action::Update => {
            ctx.data()
                .update_guild_locale(locale, guild_id)
                .await
                .unwrap();

            let locale_str = match locale {
                Locale::En => crate::i18n::t!(&ctx, commands::config::change_locale::En),
                Locale::Pt => crate::i18n::t!(&ctx, commands::config::change_locale::Pt),
            };

            let msg = crate::i18n::t!(
                &ctx,
                commands::config::change_locale::Updated,
                locale = locale_str.as_str()
            );
            ctx.say(msg).await?;
            Ok(())
        }
    }
}
