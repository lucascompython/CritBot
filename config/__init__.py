from yaml import safe_load

with open("./config/appsettings.yaml", "r") as f:
    data = safe_load(f)
