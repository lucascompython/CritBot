use serde::Deserialize;

#[derive(Deserialize)]
pub struct DiscordConfig {
    pub token: serenity::all::Token,
    pub invite_link: String,
    pub default_prefix: String,
}

#[derive(Deserialize)]
pub struct Config {
    pub discord: DiscordConfig,
}

impl Config {
    pub fn new() -> Result<Self, serde_json::Error> {
        let config_data =
            std::fs::read_to_string("appconfig.json").expect("Failed to read appconfig.json file");

        serde_json::from_str(&config_data)

        // unsafe { simd_json::from_str(&mut config_data) }
    }
}
