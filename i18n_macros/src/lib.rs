use proc_macro::TokenStream;
use quote::quote;
use syn::parse::{Parse, ParseStream};
use syn::punctuated::Punctuated;
use syn::{Ident, LitStr, Token, braced, bracketed, parse_macro_input};

struct I18nInput {
    locales: Vec<Ident>,
    commands: Vec<CommandGroup>,
    global: Vec<Translation>,
}

struct CommandGroup {
    name: Ident,
    commands: Vec<Command>,
}

struct Command {
    name: Ident,
    command_names: Vec<LocaleValue>,
    help_texts: Vec<LocaleValue>,
    args: Vec<CommandArg>,
    trans: Vec<Translation>,
}

struct CommandArg {
    name: Ident,
    arg_names: Vec<LocaleValue>,
    descriptions: Vec<LocaleValue>,
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
        // Parse locales
        input.parse::<Ident>()?; // "locales"
        input.parse::<Token![:]>()?;
        let locales_content;
        bracketed!(locales_content in input);
        let locales: Punctuated<Ident, Token![,]> =
            locales_content.parse_terminated(Ident::parse, Token![,])?;
        input.parse::<Token![,]>()?;

        let mut commands = Vec::new();
        let mut global = Vec::new();

        while !input.is_empty() {
            let section: Ident = input.parse()?;
            input.parse::<Token![:]>()?;

            if section == "commands" {
                let commands_content;
                braced!(commands_content in input);

                while !commands_content.is_empty() {
                    let group_name: Ident = commands_content.parse()?;
                    commands_content.parse::<Token![=>]>()?;

                    let group_content;
                    braced!(group_content in commands_content);

                    let mut group_commands = Vec::new();

                    while !group_content.is_empty() {
                        let cmd_name: Ident = group_content.parse()?;
                        group_content.parse::<Token![=>]>()?;

                        let cmd_content;
                        braced!(cmd_content in group_content);

                        let mut command_names = Vec::new();
                        let mut help_texts = Vec::new();
                        let mut args = Vec::new();
                        let mut trans = Vec::new();

                        while !cmd_content.is_empty() {
                            let field: Ident = cmd_content.parse()?;
                            cmd_content.parse::<Token![:]>()?;

                            match field.to_string().as_str() {
                                "name" => {
                                    let name_content;
                                    braced!(name_content in cmd_content);
                                    command_names = parse_locale_values(&name_content)?;
                                }
                                "help" => {
                                    let help_content;
                                    braced!(help_content in cmd_content);
                                    help_texts = parse_locale_values(&help_content)?;
                                }
                                "args" => {
                                    let args_content;
                                    braced!(args_content in cmd_content);
                                    args = parse_args(&args_content)?;
                                }
                                "trans" => {
                                    let trans_content;
                                    braced!(trans_content in cmd_content);
                                    trans = parse_translations(&trans_content)?;
                                }
                                _ => {
                                    return Err(syn::Error::new(
                                        field.span(),
                                        "Unknown command field",
                                    ));
                                }
                            }

                            if !cmd_content.is_empty() {
                                cmd_content.parse::<Token![,]>()?;
                            }
                        }

                        group_commands.push(Command {
                            name: cmd_name,
                            command_names,
                            help_texts,
                            args,
                            trans,
                        });

                        if !group_content.is_empty() {
                            group_content.parse::<Token![,]>()?;
                        }
                    }

                    commands.push(CommandGroup {
                        name: group_name,
                        commands: group_commands,
                    });

                    if !commands_content.is_empty() {
                        commands_content.parse::<Token![,]>()?;
                    }
                }
            } else if section == "global" {
                let global_content;
                braced!(global_content in input);
                global = parse_translations(&global_content)?;
            }

            if !input.is_empty() {
                input.parse::<Token![,]>()?;
            }
        }

        Ok(I18nInput {
            locales: locales.into_iter().collect(),
            commands,
            global,
        })
    }
}

fn parse_locale_values(input: ParseStream) -> syn::Result<Vec<LocaleValue>> {
    let mut values = Vec::new();
    while !input.is_empty() {
        let locale: Ident = input.parse()?;
        input.parse::<Token![:]>()?;
        let value: LitStr = input.parse()?;
        values.push(LocaleValue { locale, value });

        if !input.is_empty() {
            input.parse::<Token![,]>()?;
        }
    }
    Ok(values)
}

fn parse_args(input: ParseStream) -> syn::Result<Vec<CommandArg>> {
    let mut args = Vec::new();

    while !input.is_empty() {
        let arg_name: Ident = input.parse()?;
        input.parse::<Token![=>]>()?;

        let arg_content;
        braced!(arg_content in input);

        let mut arg_names = Vec::new();
        let mut descriptions = Vec::new();

        while !arg_content.is_empty() {
            let field: Ident = arg_content.parse()?;
            arg_content.parse::<Token![:]>()?;

            match field.to_string().as_str() {
                "name" => {
                    let name_content;
                    braced!(name_content in arg_content);
                    arg_names = parse_locale_values(&name_content)?;
                }
                "description" => {
                    let desc_content;
                    braced!(desc_content in arg_content);
                    descriptions = parse_locale_values(&desc_content)?;
                }
                _ => return Err(syn::Error::new(field.span(), "Unknown arg field")),
            }

            if !arg_content.is_empty() {
                arg_content.parse::<Token![,]>()?;
            }
        }

        args.push(CommandArg {
            name: arg_name,
            arg_names,
            descriptions,
        });

        if !input.is_empty() {
            input.parse::<Token![,]>()?;
        }
    }

    Ok(args)
}

fn parse_translations(input: ParseStream) -> syn::Result<Vec<Translation>> {
    let mut translations = Vec::new();

    while !input.is_empty() {
        let key: Ident = input.parse()?;
        input.parse::<Token![=>]>()?;

        let values_content;
        braced!(values_content in input);

        let fork = values_content.fork();
        let _first_ident: Ident = fork.parse()?;

        if fork.peek(Token![=>]) {
            // nested translation
            let mut entries = Vec::new();

            while !values_content.is_empty() {
                let nested_key: Ident = values_content.parse()?;
                values_content.parse::<Token![=>]>()?;

                let nested_values_content;
                braced!(nested_values_content in values_content);

                let values = parse_locale_values(&nested_values_content)?;

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
            // simple translation
            let values = parse_locale_values(&values_content)?;
            translations.push(Translation::Simple { key, values });
        }

        if !input.is_empty() {
            input.parse::<Token![,]>()?;
        }
    }

    Ok(translations)
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

fn to_snake_case(s: &str) -> String {
    let mut result = String::new();
    for (i, ch) in s.chars().enumerate() {
        if ch.is_uppercase() {
            if i > 0 {
                result.push('_');
            }
            result.push(ch.to_lowercase().next().unwrap());
        } else {
            result.push(ch);
        }
    }
    result
}

#[proc_macro]
pub fn i18n(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as I18nInput);

    let locale_variants = &input.locales;

    // locale patterns for from_code
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

    let mut command_modules = Vec::new();

    for group in &input.commands {
        let group_name = &group.name;
        let mut group_command_modules = Vec::new();

        for cmd in &group.commands {
            let cmd_name = &cmd.name;

            // Name enum
            let name_arms: Vec<_> = cmd
                .command_names
                .iter()
                .map(|lv| {
                    let locale = &lv.locale;
                    let value = &lv.value;
                    quote! { Locale::#locale => #value }
                })
                .collect();

            // Help enum
            let help_arms: Vec<_> = cmd
                .help_texts
                .iter()
                .map(|lv| {
                    let locale = &lv.locale;
                    let value = &lv.value;
                    quote! { Locale::#locale => #value }
                })
                .collect();

            // args module
            let mut arg_modules = Vec::new();
            for arg in &cmd.args {
                let arg_name = &arg.name;

                let arg_name_arms: Vec<_> = arg
                    .arg_names
                    .iter()
                    .map(|lv| {
                        let locale = &lv.locale;
                        let value = &lv.value;
                        quote! { Locale::#locale => #value }
                    })
                    .collect();

                let arg_desc_arms: Vec<_> = arg
                    .descriptions
                    .iter()
                    .map(|lv| {
                        let locale = &lv.locale;
                        let value = &lv.value;
                        quote! { Locale::#locale => #value }
                    })
                    .collect();

                arg_modules.push(quote! {
                    pub mod #arg_name {
                        use super::super::super::super::Locale;

                        pub fn name(locale: Locale) -> &'static str {
                            match locale {
                                #(#arg_name_arms,)*
                            }
                        }

                        pub fn description(locale: Locale) -> &'static str {
                            match locale {
                                #(#arg_desc_arms,)*
                            }
                        }
                    }
                });
            }

            let (trans_variants, trans_arms, trans_nested_modules) =
                generate_trans_items(&cmd.trans, &input.locales);

            group_command_modules.push(quote! {
                pub mod #cmd_name {
                    use super::super::super::Locale;

                    pub fn name(locale: Locale) -> &'static str {
                        match locale {
                            #(#name_arms,)*
                        }
                    }

                    pub fn help(locale: Locale) -> &'static str {
                        match locale {
                            #(#help_arms,)*
                        }
                    }

                    pub mod args {
                        #(#arg_modules)*
                    }

                    #(#trans_nested_modules)*

                    #[derive(Debug, Clone, Copy)]
                    pub enum Trans {
                        #(#trans_variants),*
                    }

                    impl Trans {
                        #[inline]
                        fn get_template(self, locale: Locale) -> &'static str {
                            match (locale, self) {
                                #(#trans_arms,)*
                            }
                        }

                        pub fn translate(self, locale: Locale, args: &[(&str, &str)]) -> String {
                            let template = self.get_template(locale);
                            crate::i18n::do_translate(template, args)
                        }
                    }
                }
            });
        }

        command_modules.push(quote! {
            pub mod #group_name {
                #(#group_command_modules)*
            }
        });
    }

    // global translations
    let (global_variants, global_arms, global_nested_modules) =
        generate_trans_items(&input.global, &input.locales);

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

        pub mod commands {
            use super::Locale;
            #(#command_modules)*
        }

        pub mod global {
            use super::Locale;

            #(#global_nested_modules)*

            #[derive(Debug, Clone, Copy)]
            pub enum Trans {
                #(#global_variants),*
            }

            impl Trans {
                #[inline]
                fn get_template(self, locale: Locale) -> &'static str {
                    match (locale, self) {
                        #(#global_arms,)*
                    }
                }

                pub fn translate(self, locale: Locale, args: &[(&str, &str)]) -> String {
                    let template = self.get_template(locale);
                    crate::i18n::do_translate(template, args)
                }
            }
        }
    };

    TokenStream::from(expanded)
}

fn generate_trans_items(
    translations: &[Translation],
    locales: &[Ident],
) -> (
    Vec<proc_macro2::TokenStream>,
    Vec<proc_macro2::TokenStream>,
    Vec<proc_macro2::TokenStream>,
) {
    let mut variants = Vec::new();
    let mut arms = Vec::new();
    let mut nested_modules = Vec::new();

    for trans in translations {
        match trans {
            Translation::Simple { key, values } => {
                let variant_name = syn::Ident::new(&to_pascal_case(&key.to_string()), key.span());
                variants.push(quote! { #variant_name });

                for lv in values {
                    let locale = &lv.locale;
                    let value = &lv.value;
                    arms.push(quote! {
                        (Locale::#locale, Trans::#variant_name) => #value
                    });
                }

                // TODO: possibly remove this missing locales with "missing translation"
                for locale in locales {
                    if !values.iter().any(|v| &v.locale == locale) {
                        arms.push(quote! {
                            (Locale::#locale, Trans::#variant_name) => "missing translation"
                        });
                    }
                }
            }
            Translation::Nested { namespace, entries } => {
                let namespace_pascal =
                    syn::Ident::new(&to_pascal_case(&namespace.to_string()), namespace.span());

                let mut nested_variants = Vec::new();
                let mut nested_arms = Vec::new();

                for entry in entries {
                    let entry_variant =
                        syn::Ident::new(&to_pascal_case(&entry.key.to_string()), entry.key.span());
                    nested_variants.push(quote! { #entry_variant });

                    for lv in &entry.values {
                        let locale = &lv.locale;
                        let value = &lv.value;
                        nested_arms.push(quote! {
                            (Locale::#locale, #namespace_pascal::#entry_variant) => #value
                        });
                    }

                    // missing locales
                    for locale in locales {
                        if !entry.values.iter().any(|v| &v.locale == locale) {
                            nested_arms.push(quote! {
                                (Locale::#locale, #namespace_pascal::#entry_variant) => "missing translation"
                            });
                        }
                    }
                }

                nested_modules.push(quote! {
                    #[derive(Debug, Clone, Copy)]
                    pub enum #namespace_pascal {
                        #(#nested_variants),*
                    }

                    impl #namespace_pascal {
                        #[inline]
                        fn get_template(self, locale: Locale) -> &'static str {
                            match (locale, self) {
                                #(#nested_arms,)*
                            }
                        }

                        pub fn translate(self, locale: Locale, args: &[(&str, &str)]) -> String {
                            let template = self.get_template(locale);
                            crate::i18n::do_translate(template, args)
                        }
                    }
                });

                variants.push(quote! { #namespace_pascal(#namespace_pascal) });

                for locale in locales {
                    arms.push(quote! {
                        (Locale::#locale, Trans::#namespace_pascal(nested)) => nested.get_template(Locale::#locale)
                    });
                }
            }
        }
    }

    (variants, arms, nested_modules)
}

/// Attribute macro to inject the t! macro into the function with command context and wrap poise::command attribute macro.
/// In commands that have a category, it also injects a function scoped variable, `locale`, which is the locale from the ctx.
#[proc_macro_attribute]
pub fn i18n_command(attr: TokenStream, item: TokenStream) -> TokenStream {
    let attr_input = proc_macro2::TokenStream::from(attr);
    let mut func = parse_macro_input!(item as syn::ItemFn);

    let func_name = func.sig.ident.to_string();
    let func_name_snake = to_snake_case(&func_name);

    let attr_tokens: Vec<_> = attr_input.into_iter().collect();
    let mut category = None;
    let mut poise_attrs = Vec::new();
    let mut iter = attr_tokens.iter().peekable();

    while let Some(token) = iter.next() {
        if let proc_macro2::TokenTree::Ident(ident) = token {
            if ident == "category" {
                if let Some(proc_macro2::TokenTree::Punct(punct)) = iter.peek()
                    && punct.as_char() == '='
                {
                    iter.next();
                }

                if let Some(proc_macro2::TokenTree::Literal(lit)) = iter.next() {
                    let cat_str = lit.to_string();
                    let cat_str = cat_str.trim_matches('"');
                    category = Some(cat_str.to_lowercase());
                }
                if let Some(proc_macro2::TokenTree::Punct(punct)) = iter.peek()
                    && punct.as_char() == ','
                {
                    iter.next();
                }
            } else {
                poise_attrs.push(token.clone());
            }
        } else {
            poise_attrs.push(token.clone());
        }
    }

    let original_body = &func.block;

    // build command path if category is found
    let injected_block = if let Some(cat) = category {
        let cat_ident = syn::Ident::new(&cat, proc_macro2::Span::call_site());
        let cmd_ident = syn::Ident::new(&func_name_snake, proc_macro2::Span::call_site());

        quote! {
            {
                let locale = crate::i18n::get_locale(&ctx);

                macro_rules! t {
                    // global translation with explicit global:: prefix t!(global::Key)
                    (global :: $key:ident $(, $($rest:tt)*)?) => {{
                        let args_slice: &[(&str, &str)] = $crate::i18n::t!(@args $($($rest)*)?);
                        $crate::i18n::translations::global::Trans::$key.translate(locale, args_slice)
                    }};

                    // blobal nested translation with explicit global:: prefix t!(global::Namespace::Key)
                    (global :: $namespace:ident :: $key:ident $(, $($rest:tt)*)?) => {{
                        let args_slice: &[(&str, &str)] = $crate::i18n::t!(@args $($($rest)*)?);
                        $crate::i18n::translations::global::Trans::$namespace(
                            $crate::i18n::translations::global::$namespace::$key
                        ).translate(locale, args_slice)
                    }};

                    // command-local nested translation (e.g., t!(Nested::Key))
                    ($namespace:ident :: $key:ident $(, $($rest:tt)*)?) => {{
                        let args_slice: &[(&str, &str)] = $crate::i18n::t!(@args $($($rest)*)?);
                        $crate::i18n::translations::commands::#cat_ident::#cmd_ident::Trans::$namespace(
                            $crate::i18n::translations::commands::#cat_ident::#cmd_ident::$namespace::$key
                        ).translate(locale, args_slice)
                    }};

                    // command-local simple translation (e.g., t!(Key))
                    ($key:ident $(, $($rest:tt)*)?) => {{
                        let args_slice: &[(&str, &str)] = $crate::i18n::t!(@args $($($rest)*)?);
                        $crate::i18n::translations::commands::#cat_ident::#cmd_ident::Trans::$key.translate(locale, args_slice)
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


                #original_body

            }
        }
    } else {
        // no category, just inject regular t! macro
        quote! {
            {
                // TODO: consider caching locale in ctx data to avoid fetching it every time
                macro_rules! t {
                    ($($tt:tt)*) => {
                        crate::i18n::t!(&ctx, $($tt)*)
                    };
                }

                #original_body
            }
        }
    };

    func.block = syn::parse_quote!(#injected_block);

    let poise_attr_stream: proc_macro2::TokenStream = poise_attrs.into_iter().collect();
    let poise_attr = if poise_attr_stream.is_empty() {
        quote! { #[poise::command(slash_command)] }
    } else {
        quote! { #[poise::command(#poise_attr_stream)] }
    };

    let output = quote! {
        #poise_attr
        #func
    };

    output.into()
}
