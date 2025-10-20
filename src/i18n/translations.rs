use i18n_macro::i18n;

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
