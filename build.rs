fn main() {
    let config_path = std::path::Path::new("appconfig.json");
    if !config_path.exists() {
        std::fs::copy("appconfig.example.json", "appconfig.json")
            .expect("Failed to copy example config");
        println!("\nCreated appconfig.json from example. Please edit it with your configuration.");

        std::process::exit(1);
    }
}
