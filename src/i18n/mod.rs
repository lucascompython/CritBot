use crate::{bot_data::Context, i18n::translations::Locale};

pub mod translations;

thread_local! {
    static STRING_BUFFER: std::cell::RefCell<Vec<u8>> =
        std::cell::RefCell::new(Vec::with_capacity(512));
}

pub fn do_translate(template: &str, args: &[(&str, &str)]) -> String {
    STRING_BUFFER.with(|buf| {
        if args.is_empty() {
            return template.to_string();
        }

        let mut buffer = buf.borrow_mut();
        buffer.clear();

        let bytes = template.as_bytes();
        let len = bytes.len();
        let mut i = 0;

        unsafe {
            while i < len {
                let byte = *bytes.get_unchecked(i);

                if byte == b'{' && i + 1 < len {
                    let start = i + 1;
                    let mut end = start;

                    while end < len && *bytes.get_unchecked(end) != b'}' {
                        end += 1;
                    }

                    if end < len {
                        let placeholder = std::str::from_utf8_unchecked(&bytes[start..end]);

                        let mut found = false;
                        for &(name, value) in args {
                            if placeholder == name {
                                buffer.extend_from_slice(value.as_bytes());
                                found = true;
                                break;
                            }
                        }

                        if !found {
                            buffer.extend_from_slice(&bytes[i..=end]);
                        }

                        i = end + 1;
                    } else {
                        buffer.push(byte);
                        i += 1;
                    }
                } else {
                    buffer.push(byte);
                    i += 1;
                }
            }

            String::from_utf8_unchecked(buffer.clone())
        }
    })
}

pub fn get_locale(ctx: &Context) -> Locale {
    if let Some(code) = ctx.locale() {
        Locale::from_code(code)
    } else if let Some(guild_id) = ctx.guild_id()
        && let Some(cached_guild) = ctx.data().guild_cache.pin().get(&guild_id.get())
        && let Some(custom_locale) = cached_guild.locale
    {
        custom_locale
    } else {
        Locale::from_code(&ctx.guild().unwrap().preferred_locale) // defaults to en-US if unknown
    }
}

#[macro_export]
macro_rules! t {
    // simple key: t!(ctx, Hey) or t!(ctx, Hey, name = "John") or t!(ctx, Hey, name)
    ($ctx:expr, $key:ident $(, $($rest:tt)*)?) => {{
        let locale = $crate::i18n::get_locale($ctx);
        let args_slice: &[(&str, &str)] = $crate::t!(@args $($($rest)*)?);
        $crate::i18n::translations::TransKey::$key.translate(locale, args_slice)
    }};

    // nested key: t!(ctx, Namespace::Key) or t!(ctx, Namespace::Key, title = "Hello") or t!(ctx, Namespace::Key, title)
    // expands to TransKey::Namespace(translations::Namespace::Key)
    ($ctx:expr, $namespace:ident :: $key:ident $(, $($rest:tt)*)?) => {{
        let locale = $crate::i18n::get_locale($ctx);
        let args_slice: &[(&str, &str)] = $crate::t!(@args $($($rest)*)?);
        $crate::i18n::translations::TransKey::$namespace(
            $crate::i18n::translations::$namespace::$key
        ).translate(locale, args_slice)
    }};

    // args helpers
    (@args) => (&[]);

    (@args $($name:ident = $value:expr),+ $(,)?) => (&[
        $((stringify!($name), $value)),+
    ]);

    (@args $($name:ident),+ $(,)?) => (&[
        $((stringify!($name), $name)),+
    ]);
}

// TODO: Re-enable tests

// pub use i18n_macro::i18n;

// #[cfg(test)]
// mod tests {
//     use super::*;

//     i18n! {
//         locales: [Pt, En, Fr],
//         translations: {
//             hello => { Pt: "Olá, {name}!", En: "Hello, {name}!", Fr: "Bonjour, {name}!" },
//             goodbye => { Pt: "Adeus, {name}!", En: "Goodbye, {name}!", Fr: "Au revoir, {name}!" },
//             ping => { Pt: "Pong!", En: "Pong!", Fr: "Pong!" },
//             multi_arg => {
//                 Pt: "Nome: {name}, Idade: {age}, Profissão: {job}",
//                 En: "Name: {name}, Age: {age}, Job: {job}",
//                 Fr: "Nom: {name}, Âge: {age}, Métier: {job}"
//             },

//             message => {
//                 title => { Pt: "Título: {title}", En: "Title: {title}", Fr: "Titre: {title}" },
//                 body => { Pt: "Corpo: {body}", En: "Body: {body}", Fr: "Corps: {body}" },
//                 footer => { Pt: "Rodapé", En: "Footer", Fr: "Pied de page" },
//             }
//         }
//     }

//     #[test]
//     fn test_simple_translation_pt() {
//         let ctx = Ctx {
//             guild_id: None,
//             locale: Some("pt-PT"),
//         };

//         let result = t!(ctx, Hello, name = "Maria");
//         assert_eq!(result, "Olá, Maria!");
//     }

//     #[test]
//     fn test_simple_translation_en() {
//         let ctx = Ctx {
//             guild_id: None,
//             locale: Some("en-US"),
//         };

//         let result = t!(ctx, Hello, name = "John");
//         assert_eq!(result, "Hello, John!");
//     }

//     #[test]
//     fn test_simple_translation_fr() {
//         let ctx = Ctx {
//             guild_id: None,
//             locale: Some("fr-FR"),
//         };

//         let result = t!(ctx, Goodbye, name = "Pierre");
//         assert_eq!(result, "Au revoir, Pierre!");
//     }

//     #[test]
//     fn test_no_args_translation() {
//         let ctx = Ctx {
//             guild_id: None,
//             locale: Some("en-US"),
//         };

//         let result = t!(ctx, Ping);
//         assert_eq!(result, "Pong!");
//     }

//     #[test]
//     fn test_multiple_args() {
//         let ctx = Ctx {
//             guild_id: None,
//             locale: Some("pt-PT"),
//         };

//         let result = t!(ctx, MultiArg, name = "João", age = "25", job = "Engenheiro");
//         assert_eq!(result, "Nome: João, Idade: 25, Profissão: Engenheiro");
//     }

//     #[test]
//     fn test_nested_translation() {
//         let ctx = Ctx {
//             guild_id: None,
//             locale: Some("en-US"),
//         };

//         let result = t!(ctx, Message::Title, title = "Test Title");
//         assert_eq!(result, "Title: Test Title");
//     }

//     #[test]
//     fn test_nested_translation_pt() {
//         let ctx = Ctx {
//             guild_id: None,
//             locale: Some("pt-PT"),
//         };

//         let result = t!(ctx, Message::Body, body = "Test Body");
//         assert_eq!(result, "Corpo: Test Body");
//     }

//     #[test]
//     fn test_nested_no_args() {
//         let ctx = Ctx {
//             guild_id: None,
//             locale: Some("fr-FR"),
//         };

//         let result = t!(ctx, Message::Footer);
//         assert_eq!(result, "Pied de page");
//     }

//     #[test]
//     fn test_guild_locale_cache() {
//         let cache = guild_locales();
//         cache.pin().insert(123, "pt-PT".into());
//         cache.pin().insert(456, "fr-FR".into());

//         let ctx_pt = Ctx {
//             guild_id: Some(123),
//             locale: None,
//         };

//         let ctx_fr = Ctx {
//             guild_id: Some(456),
//             locale: None,
//         };

//         let result_pt = t!(ctx_pt, Hello, name = "Carlos");
//         assert_eq!(result_pt, "Olá, Carlos!");

//         let result_fr = t!(ctx_fr, Hello, name = "Marie");
//         assert_eq!(result_fr, "Bonjour, Marie!");
//     }

//     #[test]
//     fn test_default_locale() {
//         let ctx = Ctx {
//             guild_id: None,
//             locale: None,
//         };

//         // Should default to English
//         let result = t!(ctx, Hello, name = "World");
//         assert_eq!(result, "Hello, World!");
//     }

//     #[test]
//     fn test_unknown_guild_defaults_to_en() {
//         let ctx = Ctx {
//             guild_id: Some(999999),
//             locale: None,
//         };

//         let result = t!(ctx, Hello, name = "Test");
//         assert_eq!(result, "Hello, Test!");
//     }

//     #[test]
//     fn test_locale_priority() {
//         // Locale in context should override guild locale
//         let cache = guild_locales();
//         cache.pin().insert(789, "pt-PT".into());

//         let ctx = Ctx {
//             guild_id: Some(789),
//             locale: Some("fr-FR"),
//         };

//         let result = t!(ctx, Hello, name = "Test");
//         assert_eq!(result, "Bonjour, Test!"); // Should use fr-FR, not pt-PT
//     }

//     #[test]
//     fn test_do_translate_function() {
//         let template = "Hello, {name}! You are {age} years old.";
//         let args = &[("name", "Alice"), ("age", "30")];

//         let result = do_translate(template, args);
//         assert_eq!(result, "Hello, Alice! You are 30 years old.");
//     }

//     #[test]
//     fn test_do_translate_missing_placeholder() {
//         let template = "Hello, {name}! You are {age} years old.";
//         let args = &[("name", "Bob")];

//         let result = do_translate(template, args);
//         assert_eq!(result, "Hello, Bob! You are {age} years old.");
//     }

//     #[test]
//     fn test_do_translate_no_placeholders() {
//         let template = "Hello, World!";
//         let args: &[(&str, &str)] = &[];

//         let result = do_translate(template, args);
//         assert_eq!(result, "Hello, World!");
//     }

//     #[test]
//     fn test_locale_from_code() {
//         assert!(matches!(Locale::from_code("en-US"), Locale::En));
//         assert!(matches!(Locale::from_code("EN-US"), Locale::En));
//         assert!(matches!(Locale::from_code("pt-PT"), Locale::Pt));
//         assert!(matches!(Locale::from_code("PT-BR"), Locale::Pt));
//         assert!(matches!(Locale::from_code("fr-FR"), Locale::Fr));
//         assert!(matches!(Locale::from_code("FR"), Locale::Fr));
//         assert!(matches!(Locale::from_code("unknown"), Locale::En)); // defaults to En
//     }
// }
