use serde::Deserialize;

#[derive(Deserialize)]
pub struct DiscordConfig {
    pub token: String,
    pub invite_link: String,
}

#[derive(Deserialize)]
pub struct Config {
    pub discord: DiscordConfig,
}

impl Config {
    pub fn new() -> Result<Self, simd_json::Error> {
        let mut config_data =
            std::fs::read_to_string("appconfig.json").expect("Failed to read appconfig.json file");

        unsafe { simd_json::from_str(&mut config_data) }
    }
}
