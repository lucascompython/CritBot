# Custom I18N system for CritBot

## Usage

```rust
use i18n_macro::{i18n, i18n_command};

use i18n_macro::i18n;

i18n! {
    locales: [Pt, En],
    translations: {
        change_locale => {
            already_set => { Pt: "O seu idioma já está definido para este valor.", En: "Your locale is already set to this value." },
            updated => { Pt: "Idioma atualizado para {locale}", En: "Locale updated to {locale}" },
            error_updating => { Pt: "Erro ao atualizar o idioma", En: "Error updating locale" },
            pt => { Pt: "Português", En: "Portuguese" },
            en => { Pt: "Inglês", En: "English" }

        },
        hey => { Pt: "Olá", En: "Hey" }
    }
}

// The i18n_command macro injects the t! macro into the function scope, and registers the command using poise::command.
#[i18n_command(prefix_command, slash_command, category = "Misc")]
pub async fn hey(ctx: Context<'_>) -> Result<(), Error> {
    ctx.reply(t!(Hey)).await?; // since we are using the i18n_command macro, we can use the t! macro without passing ctx.

    Ok(())
}


// More complex example
#[i18n_command(prefix_command, slash_command, category = "Settings")]
pub async fn change_locale(
    ctx: Context<'_>,
    locale: Locale,
) -> Result<(), Error> {
    let user_id = ctx.author().id.0 as i64;

    let current_locale = get_user_locale(user_id).await?;

    if current_locale == locale {
        ctx.reply(t!(Change_Locale::Already_Set)).await?; // Nested keys are accessed using double colons
        return Ok(());
    }

    match set_user_locale(user_id, locale).await {
        Ok(_) => {
            let locale_name = match locale {
                Locale::Pt => t!(Change_Locale::Pt),
                Locale::En => t!(Change_Locale::En),
            };
            ctx.reply(t!(Change_Locale::Updated, locale = locale_name)) // Nested keys with named parameters
                .await?;
        }
        Err(_) => {
            ctx.reply(t!(Change_Locale::Error_Updating)).await?;
        }
    }

    Ok(())
}



i18n! {
    locales: [Pt, En, Fr],
    translations: {
        welcome => {
            Pt: "Bem-vindo, {name}!",
            En: "Welcome, {name}!",
            Fr: "Bienvenue, {name}!"
        },
    }
}

// use the t! macro by passing the context
async fn some_function(ctx: &Context<'_>) {
    let name = String::from("Bob");
    let greeting = t!(ctx, Welcome, name); // shorthand for t!(ctx, Welcome, name = name)
}
```
