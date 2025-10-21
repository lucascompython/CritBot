use i18n_macro::i18n;

i18n! {
    locales: [Pt, En],
    // commands: {
    //     welcome => {
    //         name => { Pt: "boas-vindas", En: "welcome" },
    //         description => { Pt: "Dá as boas vindas a um utitilizador", En: "Welcomes a user" },
    //         help => {
    //             Pt: "Este comando dá as boas vindas a um utilizador mencionado.",
    //             En: "This command welcomes a mentioned user."
    //         },
    //         args => {
    //             user => {
    //                 name => { Pt: "utilizador", En: "user" },
    //                 description => { Pt: "O utilizador a quem dar as boas vindas", En: "The user to welcome" }
    //             }
    //         }
    //     }
    // },
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
