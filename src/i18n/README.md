# Custom I18N system for CritBot
Proc-macro [here](/i18n_macros/)

## Overview

The i18n system supports:
- Multiple locales (currently `Pt` and `En`)
- Command-specific translations (names, help text, arguments, and custom translations)
- Global translations accessible anywhere
- Nested translation keys
- Variable substitution with placeholder support
- IDE autocomplete support through enums
- Blazing fast performance with close to zero runtime overhead (only formatting cost basically) - ~4 times faster than fluent

## Defining Translations

Translations are defined in `src/i18n/translations.rs` using the `i18n!` macro:

```rust
use i18n_macros::i18n;

i18n! {
    locales: [Pt, En],
    commands: {
        misc => {
            welcome => {
                // required: command name translations
                name: { Pt: "boas-vindas", En: "welcome" },

                // required: command help/description translations
                help: {
                    Pt: "Este comando dá as boas vindas a um utilizador mencionado.",
                    En: "This command welcomes a mentioned user."
                },

                // optional: command argument translations
                args: {
                    user => {
                        name: { Pt: "utilizador", En: "user" },
                        description: {
                            Pt: "O utilizador a quem dar as boas vindas",
                            En: "The user to welcome"
                        }
                    }
                },

                // optional: command-specific translations (supports nested keys)
                trans: {
                    welcome_message => {
                        Pt: "Bem-vindo ao servidor, {user}!",
                        En: "Welcome to the server, {user}!"
                    },
                    farewell => {
                        goodbye => {
                            Pt: "Adeus, {user}!",
                            En: "Goodbye, {user}!"
                        }
                    }
                }
            }
        }
    },
    global: {
        // simple global translations
        bot_name => { Pt: "CritBot", En: "CritBot" },

        // nested global translations
        events => {
            guild_join => {
                Pt: "Juntei-me ao servidor {guild_name}!",
                En: "Joined the server {guild_name}!"
            },
            guild_leave => {
                Pt: "Saí do servidor {guild_name}.",
                En: "Left the server {guild_name}."
            }
        }
    }
}
```

## Using Translations

### In Commands (with `#[i18n_command]` attribute)

The `#[i18n_command]` attribute macro injects a special `t!` macro that automatically:
1. **Infers the command context from the `category` attribute and function name**
2. Gets the user's locale from the context
3. Provides a shorthand syntax

```rust
use i18n_macros::i18n_command;

// category="Misc" + function name "welcome" = commands::misc::welcome
#[i18n_command(slash_command, category = "Misc")]
pub async fn welcome(ctx: Context<'_>, user: User) -> Result<(), Error> {
    // access command-specific translations without full path
    // t!(key_name, arg1, arg2, ...)

    // simple translation (no arguments)
    let msg = t!(WelcomeMessage, user = user.name.as_str());
    ctx.say(msg).await?;

    // with variable shorthand (when variable name matches placeholder)
    let user = user.name.as_str();
    let msg = t!(WelcomeMessage, user); // equivalent to: user = user
    ctx.say(msg).await?;

    // nested command translations
    let msg = t!(Messages::Greeting, user);
    ctx.say(msg).await?;

    // access global translations with explicit global:: prefix
    let bot_name = t!(global::BotName);
    ctx.say(format!("I am {}!", bot_name)).await?;

    // nested global translations
    let msg = t!(global::Events::GuildJoin, guild_name = "My Server");
    ctx.say(msg).await?;

    Ok(())
}
```

### Global Translations (anywhere in code)

Use the `t!` macro from `crate::i18n::t!` with explicit context:

```rust
use crate::i18n::t;

// simple global translation
let bot_name = t!(ctx, BotName);

// nested global translation
let msg = t!(ctx, Events::GuildJoin, guild_name = "My Server");

// with variable shorthand
let guild_name = "My Server";
let msg = t!(ctx, Events::GuildJoin, guild_name);
```

### Accessing Command Translations Outside Commands

You can access command-specific translations from anywhere using the full path:

```rust
use crate::i18n::t;

// access command translations with full path
let msg = t!(ctx, commands::config::change_locale::AlreadySet);

// with arguments
let locale = "English";
let msg = t!(ctx, commands::config::change_locale::Updated, locale);

// nested command translations
let user = "John";
let msg = t!(ctx, commands::misc::welcome::Messages::Greeting, user);
```

### Direct Translation API (without macros)

For more complex scenarios or outside of command contexts:

```rust
use crate::i18n::{translations, get_locale};

// get locale from context
let locale = get_locale(&ctx);

// command translations
let cmd_name = translations::commands::misc::welcome::name(locale);
let cmd_help = translations::commands::misc::welcome::help(locale);
let arg_name = translations::commands::misc::welcome::args::user::name(locale);

// command-specific translations
let msg = translations::commands::misc::welcome::Trans::WelcomeMessage
    .translate(locale, &[("user", "John")]);

// global translations
let bot_name = translations::global::Trans::BotName
    .translate(locale, &[]);

let event_msg = translations::global::Trans::Events(
    translations::global::Events::GuildJoin
).translate(locale, &[("guild_name", "My Server")]);
```

## Variable Substitution

Placeholders in translations are enclosed in curly braces: `{variable_name}`

```rust
// translation: "Welcome, {user}! You joined {guild}."

// long form
let msg = t!(ctx, Welcome, user = "John", guild = "My Server");

// shorthand (when variable names match)
let user = "John";
let guild = "My Server";
let msg = t!(ctx, Welcome, user, guild);

// mixed
let user = "John";
let msg = t!(ctx, Welcome, user, guild = "My Server");
```

## IDE Autocomplete

The system uses enums for translation keys, providing full IDE autocomplete:

```rust
// After typing `t!(`, your IDE will suggest:
// - All global translation keys
// - Nested namespaces (e.g., Events::)

// Inside a command with #[i18n_command], after typing `t!(`:
// - All command-specific translation keys
// - Nested command translations

// In the translations definition, the IDE will warn about non-used translations
```

## Generated Structure

The `i18n!` macro generates the following structure:

```
translations::
├── Locale (enum with from_code(), code() methods)
├── commands::
│   └── {group}::
│       └── {command}::
│           ├── name(locale) -> &'static str
│           ├── help(locale) -> &'static str
│           ├── args::
│           │   └── {arg}::
│           │       ├── name(locale) -> &'static str
│           │       └── description(locale) -> &'static str
│           └── Trans (enum)
└── global::
    └── Trans (enum with nested variants)
```

## Example: Complete Command

```rust
use i18n_macros::i18n_command;
use crate::bot_data::Context;

// command path is automatically inferred: category="Moderation" + fn name "kick" = commands::moderation::kick
#[i18n_command(
    slash_command,
    required_permissions = "KICK_MEMBERS",
    category = "Moderation"
)]
pub async fn kick(
    ctx: Context<'_>,
    user: User,
    reason: Option<String>,
) -> Result<(), Error> {
    // kick the user
    ctx.guild_id().unwrap()
        .kick(ctx, user.id)
        .await?;

    // send success message using command-specific translation
    let reason = reason.as_deref().unwrap_or("No reason provided");
    let username = user.name.as_str();

    // shorthand syntax - variables match placeholder names
    ctx.say(t!(Success, username, reason)).await?;

    // can also access global translations with explicit prefix
    let bot_name = t!(global::BotName);

    // or nested command translations
    ctx.say(t!(Messages::KickConfirm, username)).await?;

    Ok(())
}
```

With the corresponding translation:

```rust
i18n! {
    locales: [Pt, En],
    commands: {
        moderation => {
            kick => {
                name: { Pt: "expulsar", En: "kick" },
                help: {
                    Pt: "Expulsa um utilizador do servidor",
                    En: "Kicks a user from the server"
                },
                args: {
                    user => {
                        name: { Pt: "utilizador", En: "user" },
                        description: {
                            Pt: "O utilizador a expulsar",
                            En: "The user to kick"
                        }
                    },
                    reason => {
                        name: { Pt: "razão", En: "reason" },
                        description: {
                            Pt: "A razão da expulsão",
                            En: "The reason for kicking"
                        }
                    }
                },
                trans: {
                    success => {
                        Pt: "✅ {username} foi expulso. Razão: {reason}",
                        En: "✅ {username} was kicked. Reason: {reason}"
                    },
                    messages => {
                        kick_confirm => {
                            Pt: "{username} foi removido do servidor.",
                            En: "{username} has been removed from the server."
                        }
                    }
                }
            }
        }
    }
}
```

## Iterating Over Locales and Commands

The i18n system generates metadata that allows you to iterate over all locales and commands. This is useful for applying translations to command metadata programmatically.

### Available Metadata

```rust
use crate::i18n::translations::{Locale, COMMANDS_META, CommandMeta, ArgMeta};

// All available locales
Locale::ALL // &'static [Locale]

// All command metadata
COMMANDS_META // &'static [CommandMeta]
```

### CommandMeta Structure

```rust
pub struct CommandMeta {
    pub group: &'static str,           // e.g., "misc", "config"
    pub name: &'static str,            // e.g., "hey", "change_locale"
    pub get_name: fn(Locale) -> &'static str,    // Get localized command name
    pub get_help: fn(Locale) -> &'static str,    // Get localized help text
    pub args: &'static [ArgMeta],      // Argument metadata
}

pub struct ArgMeta {
    pub name: &'static str,            // Argument name
    pub get_name: fn(Locale) -> &'static str,           // Get localized arg name
    pub get_description: fn(Locale) -> &'static str,    // Get localized arg description
}
```

### Example: Applying Translations to Poise Commands

```rust
use crate::i18n::translations::{Locale, COMMANDS_META};

pub fn apply_translations(commands: &mut [poise::Command<BotData, serenity::Error>]) {
    for cmd_meta in COMMANDS_META {
        if let Some(cmd) = commands
            .iter_mut()
            .find(|c| c.name.as_str() == cmd_meta.name)
        {
            // set defaults to English
            cmd.name = (cmd_meta.get_name)(Locale::En).to_string();
            cmd.description = Some((cmd_meta.get_help)(Locale::En).to_string());

            for &locale in Locale::ALL {
                let locale_code = locale.discord_code();

                let localized_name = (cmd_meta.get_name)(locale).to_string();

                cmd.name_localizations
                    .insert(locale_code.to_string(), localized_name.clone());
                cmd.description_localizations.insert(
                    locale_code.to_string(),
                    (cmd_meta.get_help)(locale).to_string(),
                );

                // set aliases for the commands nmes for locales other than english

                if locale != Locale::En && !cmd.aliases.contains(&localized_name) {
                    cmd.aliases.push(localized_name);
                }
            }

            for arg_meta in cmd_meta.args {
                if let Some(param) = cmd
                    .parameters
                    .iter_mut()
                    .find(|p| p.name.as_str() == arg_meta.name)
                {
                    param.name = (arg_meta.get_name)(Locale::En).to_string();
                    param.description = Some((arg_meta.get_description)(Locale::En).to_string());

                    for &locale in Locale::ALL {
                        let locale_code = locale.discord_code();

                        param.name_localizations.insert(
                            locale_code.to_string(),
                            (arg_meta.get_name)(locale).to_string(),
                        );
                        param.description_localizations.insert(
                            locale_code.to_string(),
                            (arg_meta.get_description)(locale).to_string(),
                        );
                    }
                }
            }
        }
    }
}
```

### Example: Generate Documentation

```rust
use crate::i18n::translations::{Locale, COMMANDS_META};

fn generate_command_docs() {
    for cmd_meta in COMMANDS_META {
        println!("## Command: {} (group: {})", cmd_meta.name, cmd_meta.group);

        for &locale in Locale::ALL {
            let name = (cmd_meta.get_name)(locale);
            let help = (cmd_meta.get_help)(locale);
            println!("  [{}] {}: {}", locale.code(), name, help);
        }

        if !cmd_meta.args.is_empty() {
            println!("  Arguments:");
            for arg_meta in cmd_meta.args {
                println!("    - {}", arg_meta.name);
                for &locale in Locale::ALL {
                    let name = (arg_meta.get_name)(locale);
                    let desc = (arg_meta.get_description)(locale);
                    println!("      [{}] {}: {}", locale.code(), name, desc);
                }
            }
        }
        println!();
    }
}
```

### Example: Validate All Translations

```rust
use crate::i18n::translations::{Locale, COMMANDS_META};

fn validate_translations() {
    for cmd_meta in COMMANDS_META {
        for &locale in Locale::ALL {
            let name = (cmd_meta.get_name)(locale);
            let help = (cmd_meta.get_help)(locale);

            assert!(!name.is_empty(), "Command {} has empty name for locale {}", cmd_meta.name, locale.code());
            assert!(!help.is_empty(), "Command {} has empty help for locale {}", cmd_meta.name, locale.code());

            for arg_meta in cmd_meta.args {
                let arg_name = (arg_meta.get_name)(locale);
                let arg_desc = (arg_meta.get_description)(locale);

                assert!(!arg_name.is_empty(), "Arg {} has empty name for locale {}", arg_meta.name, locale.code());
                assert!(!arg_desc.is_empty(), "Arg {} has empty desc for locale {}", arg_meta.name, locale.code());
            }
        }
    }
}
```
