macro_rules! println {
    () => {
        ::std::println!("cargo:warning=\x1b[2K\r");
    };
    ($($arg:tt)*) => {
        ::std::println!("cargo:warning=\x1b[2K\r{}", ::std::format!($($arg)*));
    }
}

fn main() {
    let config_path = std::path::Path::new("appconfig.json");
    let lavalink_config_path = std::path::Path::new("application.yaml");
    if !config_path.exists() {
        std::fs::copy("appconfig.example.json", "appconfig.json")
            .expect("Failed to copy example config");
        println!("\nCreated appconfig.json from example. Please edit it with your configuration.");

        std::process::exit(1);
    }

    if !lavalink_config_path.exists() {
        std::fs::copy("application.example.yaml", "application.yaml")
            .expect("Failed to copy example lavalink config");
        println!(
            "\nCreated application.yaml from example. Please edit it with your configuration."
        );

        std::process::exit(1);
    }

    if std::env::var("DOWNLOAD_LAVALINK").is_ok() {
        let lavalink_url =
            "https://github.com/lavalink-devs/Lavalink/releases/latest/download/Lavalink.jar";

        println!("Downloading Lavalink from {}", lavalink_url);
        let response = reqwest::blocking::get(lavalink_url).expect("Failed to download Lavalink");
        let bytes = response
            .bytes()
            .expect("Failed to read Lavalink response bytes");
        std::fs::write("Lavalink.jar", &bytes).expect("Failed to write Lavalink.jar file");
        println!("Downloaded Lavalink.jar");
    }
}
