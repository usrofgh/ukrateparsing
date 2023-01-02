import json

with open("countries_codes/ukraine.json", encoding="windows-1251") as reader:
    cities_codes = json.load(reader)
i = 0
for k, v in cities_codes.items():
    for k1, v1 in cities_codes[k].items():
        for k2, v2 in cities_codes[k][k1].items():
            for k3, v3 in cities_codes[k][k1][k2].items():
                print(k3, v3)
