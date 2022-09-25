from orjson import loads
from yaml import safe_load

with open("./config/appsettings.yaml", "r") as f:
    data = safe_load(f)

with open("./prefixes.json", "r") as f:
    prefixes = loads(f.read())

















