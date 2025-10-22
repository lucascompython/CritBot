use i18n_macros::i18n;

use crate::bot_data::BotData;

i18n! {
    locales: [Pt, En],
    commands: {
        config => {
            change_locale => {
                name: { Pt: "mudar-idioma", En: "change-locale" },
                help: {
                    Pt: "Muda o idioma do bot para este servidor",
                    En: "Changes the bot's language for this server"
                },
                args: {
                    new_locale => {
                        name: { Pt: "idioma", En: "locale" },
                        description: {
                            Pt: "O idioma a definir",
                            En: "The locale to set"
                        }
                    }
                },
                trans: {
                    already_set => {
                        Pt: "O seu idioma já está definido para este valor.",
                        En: "Your locale is already set to this value."
                    },
                    updated => {
                        Pt: "Idioma atualizado para {locale}",
                        En: "Locale updated to {locale}"
                    },
                    error_updating => {
                        Pt: "Erro ao atualizar o idioma",
                        En: "Error updating locale"
                    },
                    pt => { Pt: "Português", En: "Portuguese" },
                    en => { Pt: "Inglês", En: "English" }
                }
            }
        },
        misc => {
            hey => {
                name: { Pt: "olá", En: "hey" },
                help: {
                    Pt: "Diz olá!",
                    En: "Says hey!"
                },
                trans: {
                    response => { Pt: "Olá!", En: "Hey!" },
                    messages => {
                        greeting => {
                            Pt: "Olá, {user}! Bem-vindo!",
                            En: "Hey, {user}! Welcome!"
                        }
                    }
                }
            }
        }
    },
    global: {
        // TODO: handle errors
        errors => {
            unknown_error => {
                Pt: "Ocorreu um erro desconhecido",
                En: "An unknown error occurred"
            }
        }
    }
}

// TODO: this could be generated and "unrolled" by a macro, and there wouldn't be a need to all this COMMANDS_META boilerplate, thus making the i18n! macro simpler
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
