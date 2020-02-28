import requests
from tqdm import tqdm
import json

url = 'https://query.wikidata.org/sparql'
subquery = """
SELECT ?item ?itemLabel
WHERE 
{
  ?item wdt:P31 wd:Q23397.
  ?article schema:about ?item.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
  FILTER (CONTAINS(STR(?item), 
"""
combinations = [f"Q{n}" for n in range(10, 100)]
lakes = {}
for comb in tqdm(combinations):
    query = subquery + f"'{comb}'))" + "}"
    try:
        r = requests.get(url, params = {'format': 'json', 'query': query})
        data = r.json()
        for entry in data["results"]["bindings"]:
            key = entry["item"]["value"].split("/")[-1]
            lakes[key] = entry['itemLabel']['value']
    except Exception as e:
        print (str(e))
        print (comb)

print ("length of lakes", len(lakes))
try:
    with open("wikidata_lakes.json", "w") as file:
        file.write(json.dumps(lakes, ensure_ascii = False))
except Exception as e:
    print (str(e))

try:
    csv = "Name,ID\n"
    for key, value in lakes.items():
        csv += f"{value.replace(',', ';')},{key.replace(',', ';')}\n"

    with open("wikidata_lakes.csv", "w") as file:
        file.write(csv.encode('ascii', 'ignore').decode())
except Exception as e:
    print (str(e))
