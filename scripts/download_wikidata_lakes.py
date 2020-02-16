import requests
from tqdm import tqdm
import json

url = 'https://query.wikidata.org/sparql'
subquery = """
SELECT ?item ?itemLabel ?area
WHERE 
{
  ?item wdt:P31 wd:Q23397.
  ?item wdt:P2046 ?area
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
            lakes[key] = (entry['itemLabel']['value'], entry['area']['value'])
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
    csv = "Name,ID,Area\n"
    for key, value in lakes.items():
        csv += f"{value[0].replace(',', ';')},{key.replace(',', ';')},{value[1]}\n"

    with open("wikidata_lakes.csv", "w") as file:
        file.write(csv.encode('ascii', 'ignore').decode())
except Exception as e:
    print (str(e))
