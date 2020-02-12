import requests
from tqdm import tqdm
import json

url = 'https://query.wikidata.org/sparql'
subquery = """
SELECT ?item ?itemLabel 
WHERE 
{
  ?item wdt:P31 wd:Q4022.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
  FILTER (CONTAINS(STR(?item), 
"""
combinations = [f"Q{n}" for n in range(10, 100)]
rivers = {}
for comb in tqdm(combinations):
    query = subquery + f"'{comb}'))" + "}"
    try:
        r = requests.get(url, params = {'format': 'json', 'query': query})
        data = r.json()
        for entry in data["results"]["bindings"]:
            key = entry["item"]["value"].split("/")[-1]
            if key in rivers:
                print ("haye oyee rabba")
            rivers[key] = entry['itemLabel']['value']
    except Exception as e:
        print (str(e))
        print (comb)

with open("wikidata_rivers.json", "w") as file:
    file.write(json.dumps(rivers))

csv = "ItemLabel,Item\n"
for key, value in rivers.items():
    csv += f"{value.replace(',', ';')},{key.replace(',', ';')}\n"

with open("wikidata_rivers.csv", "w") as file:
    file.write(csv)
