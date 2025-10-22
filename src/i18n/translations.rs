use i18n_macros::i18n;

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
                    locale => {
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
                        },
                        farewell => {
                            Pt: "Adeus, {user}!",
                            En: "Goodbye, {user}!"
                        }
                    }
                }
            }
        }
    },
    global: {
        bot_name => { Pt: "CritBot", En: "CritBot" },
        errors => {
            unknown_error => {
                Pt: "Ocorreu um erro desconhecido",
                En: "An unknown error occurred"
            }
        }
    }
}
