use proc_macro::TokenStream;
use quote::quote;
use syn::parse::{Parse, ParseStream};
use syn::punctuated::Punctuated;
use syn::{Ident, LitStr, Token, parse_macro_input};

struct I18nInput {
    locales: Vec<Ident>,
    translations: Vec<Translation>,
}

enum Translation {
    Simple {
        key: Ident,
        values: Vec<LocaleValue>,
    },
    Nested {
        namespace: Ident,
        entries: Vec<NestedEntry>,
    },
}

struct NestedEntry {
    key: Ident,
    values: Vec<LocaleValue>,
}

struct LocaleValue {
    locale: Ident,
    value: LitStr,
}

impl Parse for I18nInput {
    fn parse(input: ParseStream) -> syn::Result<Self> {
        input.parse::<Ident>()?; // "locales"
        input.parse::<Token![:]>()?;
        let locales_content;
        syn::bracketed!(locales_content in input);
        let locales: Punctuated<Ident, Token![,]> =
            locales_content.parse_terminated(Ident::parse, Token![,])?;
        input.parse::<Token![,]>()?;

        input.parse::<Ident>()?; // "translations"
        input.parse::<Token![:]>()?;
        let trans_content;
        syn::braced!(trans_content in input);

        let mut translations = Vec::new();

        while !trans_content.is_empty() {
            let key: Ident = trans_content.parse()?;
            trans_content.parse::<Token![=>]>()?;

            let values_content;
            syn::braced!(values_content in trans_content);

            let fork = values_content.fork();
            let _first_ident: Ident = fork.parse()?;

            if fork.peek(Token![=>]) {
                let mut entries = Vec::new();

                while !values_content.is_empty() {
                    let nested_key: Ident = values_content.parse()?;
                    values_content.parse::<Token![=>]>()?;

                    let nested_values_content;
                    syn::braced!(nested_values_content in values_content);

                    let mut values = Vec::new();
                    while !nested_values_content.is_empty() {
                        let locale: Ident = nested_values_content.parse()?;
                        nested_values_content.parse::<Token![:]>()?;
                        let value: LitStr = nested_values_content.parse()?;
                        values.push(LocaleValue { locale, value });

                        if !nested_values_content.is_empty() {
                            nested_values_content.parse::<Token![,]>()?;
                        }
                    }

                    entries.push(NestedEntry {
                        key: nested_key,
                        values,
                    });

                    if !values_content.is_empty() {
                        values_content.parse::<Token![,]>()?;
                    }
                }

                translations.push(Translation::Nested {
                    namespace: key,
                    entries,
                });
            } else {
                let mut values = Vec::new();
                while !values_content.is_empty() {
                    let locale: Ident = values_content.parse()?;
                    values_content.parse::<Token![:]>()?;
                    let value: LitStr = values_content.parse()?;
                    values.push(LocaleValue { locale, value });

                    if !values_content.is_empty() {
                        values_content.parse::<Token![,]>()?;
                    }
                }

                translations.push(Translation::Simple { key, values });
            }

            if !trans_content.is_empty() {
                trans_content.parse::<Token![,]>()?;
            }
        }

        Ok(I18nInput {
            locales: locales.into_iter().collect(),
            translations,
        })
    }
}

fn to_pascal_case(s: &str) -> String {
    s.split('_')
        .map(|part| {
            let mut chars = part.chars();
            match chars.next() {
                Some(first) => first.to_uppercase().collect::<String>() + chars.as_str(),
                None => String::new(),
            }
        })
        .collect::<String>()
}

#[proc_macro]
pub fn i18n(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as I18nInput);

    let locale_variants = &input.locales;

    let locale_patterns: Vec<_> = input
        .locales
        .iter()
        .map(|locale| {
            let locale_str = locale.to_string();
            let mut chars = locale_str.chars();
            let first_char = chars.next().unwrap().to_lowercase().next().unwrap() as u8;
            let second_char = chars.next().unwrap().to_lowercase().next().unwrap() as u8;
            quote! {
                (#first_char, #second_char) => Locale::#locale
            }
        })
        .collect();

    let mut key_variants = Vec::new();
    let mut nested_modules = Vec::new();
    let mut translate_arms = Vec::new();

    for trans in &input.translations {
        match trans {
            Translation::Simple { key, values } => {
                let variant_name = syn::Ident::new(&to_pascal_case(&key.to_string()), key.span());
                key_variants.push(quote! { #variant_name });

                for lv in values {
                    let locale = &lv.locale;
                    let value = &lv.value;
                    translate_arms.push(quote! {
                        (Locale::#locale, TransKey::#variant_name) => #value
                    });
                }
            }
            Translation::Nested { namespace, entries } => {
                let namespace_pascal =
                    syn::Ident::new(&to_pascal_case(&namespace.to_string()), namespace.span());

                let mut nested_variants = Vec::new();
                let mut nested_translate_arms = Vec::new();

                for entry in entries {
                    let entry_variant =
                        syn::Ident::new(&to_pascal_case(&entry.key.to_string()), entry.key.span());
                    nested_variants.push(quote! { #entry_variant });

                    for lv in &entry.values {
                        let locale = &lv.locale;
                        let value = &lv.value;
                        nested_translate_arms.push(quote! {
                            (Locale::#locale, #namespace_pascal::#entry_variant) => #value
                        });
                    }
                }

                nested_modules.push(quote! {
                    pub enum #namespace_pascal {
                        #(#nested_variants),*
                    }

                    impl #namespace_pascal {
                        fn get_template(self, locale: Locale) -> &'static str {
                            match (locale, self) {
                                #(#nested_translate_arms,)*
                            }
                        }

                        pub fn translate(self, locale: Locale, args: &[(&str, &str)]) -> String {
                            let template = self.get_template(locale);
                            if args.is_empty() {
                                template.to_string()
                            } else {
                                crate::do_translate(template, args)
                            }
                        }
                    }
                });

                key_variants.push(quote! { #namespace_pascal(#namespace_pascal) });
            }
        }
    }

    let namespace_names: Vec<_> = input
        .translations
        .iter()
        .filter_map(|trans| {
            if let Translation::Nested { namespace, .. } = trans {
                let namespace_pascal =
                    syn::Ident::new(&to_pascal_case(&namespace.to_string()), namespace.span());
                Some(namespace_pascal)
            } else {
                None
            }
        })
        .collect();

    let expanded = quote! {
        #[derive(Debug, Clone, Copy, PartialEq, postgres_types::ToSql, postgres_types::FromSql, poise::ChoiceParameter)]
        pub enum Locale {
            #(#locale_variants),*
        }

        impl Locale {
            pub fn from_code(code: &str) -> Self {
                let bytes = code.as_bytes();
                if bytes.len() >= 2 {
                    match (unsafe { bytes.get_unchecked(0) } | 32, unsafe { bytes.get_unchecked(1) } | 32) {
                        #(#locale_patterns,)*
                        _ => Locale::En,
                    }
                } else {
                    Locale::En
                }
            }

            pub fn code(self) -> &'static str {
                match self {
                    #(Locale::#locale_variants => stringify!(#locale_variants),)*
                }
            }
        }

        #(#nested_modules)*

        pub enum TransKey {
            #(#key_variants),*
        }

        impl TransKey {
            #[inline]
            fn get_template(self, locale: Locale) -> &'static str {
                match (locale, self) {
                    #(#translate_arms,)*
                    _ => "missing translation",
                }
            }

            pub fn translate(self, locale: Locale, args: &[(&str, &str)]) -> String {
                match self {
                    #(TransKey::#namespace_names(nested) => nested.translate(locale, args),)*
                    _ => {
                        let template = self.get_template(locale);
                        crate::do_translate(template, args)
                    }
                }
            }
        }
    };

    TokenStream::from(expanded)
}

/// Attribute macro to inject the t! macro into the function, so that we don't have to pass ctx every call to t! and also support poise command attribute macro and it's arguments.
#[proc_macro_attribute]
pub fn i18n_command(attr: TokenStream, item: TokenStream) -> TokenStream {
    let attr_ts: proc_macro2::TokenStream = attr.into();

    let mut func = parse_macro_input!(item as syn::ItemFn);

    let original_body = &func.block;

    let injected_block = quote! {
        {
            macro_rules! t {
                ($($tt:tt)*) => {
                    crate::i18n::t!(&ctx, $($tt)*)
                };
            }

            #original_body
        }
    };

    func.block = syn::parse_quote!(#injected_block);

    let poise_attr = if attr_ts.is_empty() {
        quote! { #[poise::command] }
    } else {
        quote! { #[poise::command(#attr_ts)] }
    };

    let output = quote! {
        #poise_attr
        #func
    };

    output.into()
}
