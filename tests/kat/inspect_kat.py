import json
d = json.load(open("tests/kat/encapdecap.json", encoding="utf-8"))
for g in d["testGroups"]:
    print(g["tgId"], g["testType"], g["parameterSet"], g["function"],
          len(g["tests"]), sorted(g["tests"][0].keys()))