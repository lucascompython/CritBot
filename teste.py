import json

with open("./teste.json", "w") as f:
    json.dump({"ola": "ola"}, f)