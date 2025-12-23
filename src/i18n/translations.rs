use std::borrow::Cow;

use i18n_macros::i18n;

use crate::bot_data::{BotData, Error};

// TODO: handle "normal" aliases here, so there are less places to look at for command metadata
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
            },
            change_prefix => {
                name: { Pt: "mudar-prefixo", En: "change-prefix" },
                help: {
                    Pt: "Muda o prefixo do bot para este servidor",
                    En: "Changes the bot's prefix for this server"
                },
                args: {
                    prefix => {
                        name: { Pt: "prefixo", En: "prefix" },
                        description: {
                            Pt: "O novo prefixo a definir",
                            En: "The new prefix to set"
                        }
                    }
                },
                trans: {
                    updated => {
                        Pt: "Prefixo atualizado para `{prefix}`",
                        En: "Prefix updated to `{prefix}`"
                    },
                    error_updating => {
                        Pt: "Erro ao atualizar o prefixo",
                        En: "Error updating prefix"
                    }
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
        },
        music => {
            play => {
                name: { Pt: "tocar", En: "play" },
                help: {
                    Pt: "Toca uma música a partir de uma URL ou pesquisa",
                    En: "Plays a song from a URL or search"
                },
                args: {
                    query => {
                        name: { Pt: "consulta", En: "query" },
                        description: {
                            Pt: "A URL ou termo de pesquisa da música",
                            En: "The URL or search term of the song"
                        }
                    }
                },
                trans: {
                    added_playlist => {
                      Pt: "Playlist adicionada à fila: {name}", En: "Added playlist to queue: {name}"
                    },
                    added_track => {
                        En: "Added to queue: [{author} - {title}](<{uri}>)", Pt: "Adicionado à fila: [{author} - {title}](<{uri}>)"
                    },
                    not_found => {
                        Pt: "Nenhuma música encontrada para: `{query}`",
                        En: "No song found for query: `{query}`"
                    },
                    now_playing => {
                        Pt: "A tocar agora: [{author} - {title}](<{uri}>) | Requisitado por <@!{requester_id}>",
                        En: "Now playing: [{author} - {title}](<{uri}>) | Requested by <@!{requester_id}>"
                    }

                },
        },
        skip => {
            name: { Pt: "saltar", En: "skip" },
            help: {
                Pt: "Salta a música atual à frente",
                En: "Skips the current song"
            },
            trans: {
                not_in_channel => {
                    Pt: "Não estou num canal de voz!",
                    En: "I'm in a voice channel!"
                },
                nothing_playing => {
                    Pt: "Nada está a ser reproduzido!",
                    En: "Nothing is playing!"
                },
            }
        },
        join => {
            name: { Pt: "entrar", En: "join" },
            help: {
                Pt: "Faz o bot entrar no canal de voz",
                En: "Makes the bot join the voice channel"
            },
            args: {
                channel => {
                    name: { Pt: "canal", En: "channel" },
                    description: {
                        Pt: "O canal de voz para o bot entrar (padrão: seu canal atual)",
                        En: "The voice channel for the bot to join (default: your current channel)"
                    }
                }
            },
            trans: {
                joined => {
                    Pt: "A entrar em {channel}!",
                    En: "Joined {channel}!",
                },
                already_in_channel => {
                    Pt: "Já estou num canal de voz!",
                    En: "I'm already in a voice channel!"
                },
                you_not_in_channel => {
                    Pt: "Não estás num canal de voz!",
                    En: "You are not in a voice channel!"
                },
                error_joining => {
                    Pt: "Erro ao entrar no canal de voz: {error}",
                    En: "Error joining voice channel: {error}"
                }
            }
        },
        leave => {
            name: { Pt: "sair", En: "leave" },
            help: {
                Pt: "Faz o bot sair do canal de voz",
                En: "Makes the bot leave the voice channel"
            },
            trans: {
                left => {
                    Pt: "Saí do canal de voz.",
                    En: "Left the voice channel."
                },
                not_in_channel => {
                    Pt: "Não estou num canal de voz!",
                    En: "I'm not in a voice channel!"
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
pub fn apply_translations(commands: &mut [poise::Command<BotData, Error>]) {
    for cmd_meta in COMMANDS_META {
        if let Some(cmd) = commands.iter_mut().find(|c| c.name == cmd_meta.name) {
            // set defaults to English
            cmd.name = (cmd_meta.get_name)(Locale::En).into();
            cmd.description = Some((cmd_meta.get_help)(Locale::En).into());

            let name_localizations = cmd.name_localizations.to_mut();
            let description_localizations = cmd.description_localizations.to_mut();
            let aliases = cmd.aliases.to_mut();

            for &locale in Locale::ALL {
                let locale_code: Cow<'static, str> = locale.discord_code().into();

                let localized_name: Cow<'static, str> = (cmd_meta.get_name)(locale).into();

                name_localizations.push((locale_code.clone(), localized_name.clone()));
                description_localizations.push((locale_code, (cmd_meta.get_help)(locale).into()));

                // set aliases for the commands nmes for locales other than english

                if locale != Locale::En && !aliases.contains(&localized_name) {
                    aliases.push(localized_name);
                }
            }

            for arg_meta in cmd_meta.args {
                if let Some(param) = cmd.parameters.iter_mut().find(|p| p.name == arg_meta.name) {
                    param.name = (arg_meta.get_name)(Locale::En).into();
                    param.description = Some((arg_meta.get_description)(Locale::En).into());

                    let name_localizations = param.name_localizations.to_mut();
                    let description_localizations = param.description_localizations.to_mut();

                    for &locale in Locale::ALL {
                        let locale_code = locale.discord_code();

                        name_localizations
                            .push((locale_code.into(), (arg_meta.get_name)(locale).into()));
                        description_localizations.push((
                            locale_code.into(),
                            (arg_meta.get_description)(locale).into(),
                        ));
                    }
                }
            }
        }
    }
}
