use i18n_macro::i18n;

use crate::t;

i18n! {
    locales: [Pt, En],
    translations: {
        change_locale => {
            already_set => { Pt: "O seu idioma já está definido para este valor.", En: "Your locale is already set to this value." },
            updated => { Pt: "Idioma atualizado para {locale}", En: "Locale updated to {locale}" },
            error_updating => { Pt: "Erro ao atualizar o idioma", En: "Error updating locale" }
        },
        hey => { Pt: "Olá", En: "Hey" }
    }
}

// TODO: Handle errors properly and move this logic away from this file
type Error = Box<dyn std::error::Error + Send + Sync>;

/// Insert or update the guild locale in the database and cache
pub async fn update_guild_locale(
    ctx: &crate::context::Context<'_>,
    locale: Locale,
) -> Result<(), Error> {
    let pool = &ctx.data().db.get_pool().await;
    let stmt = pool
        .prepare_cached("INSERT INTO guilds (locale, id) VALUES ($1, $2) ON CONFLICT (id) DO UPDATE SET locale = EXCLUDED.locale")
        .await?;

    let guild_id = ctx.guild_id().unwrap().get();
    let guild_id_i64 = guild_id as i64;
    pool.execute(&stmt, &[&locale, &guild_id_i64]).await?;

    let pinned_guild_cache = ctx.data().guild_cache.pin();
    pinned_guild_cache.insert(
        guild_id,
        crate::context::Guild {
            locale: Some(locale),
        },
    );

    Ok(())
}

pub async fn change_locale(ctx: crate::context::Context<'_>, locale: Locale) -> Result<(), Error> {
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
            ctx.say(t!(&ctx, ChangeLocale::AlreadySet)).await?;
            Ok(())
        }
        Action::Update => {
            update_guild_locale(&ctx, locale).await?;
            ctx.say(t!(&ctx, ChangeLocale::Updated, locale = locale.code()))
                .await?;
            Ok(())
        }
    }
}
