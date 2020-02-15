import requests
from tqdm import tqdm
import json

url = 'https://query.wikidata.org/sparql'
subquery = """
SELECT ?item ?itemLabel ?length
WHERE 
{
  ?item wdt:P31 wd:Q4022.
  ?item wdt:P2043 ?length
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
            rivers[key] = (entry['itemLabel']['value'], entry['length']['value'])
    except Exception as e:
        print (str(e))
        print (comb)

print ("length of rivers", len(rivers))
with open("wikidata_rivers.json", "w") as file:
    file.write(json.dumps(rivers))

csv = "Name,ID,Length\n"
for key, value in rivers.items():
    csv += f"{value[0].replace(',', ';')},{key.replace(',', ';')},{value[1]}\n"

with open("wikidata_rivers.csv", "w") as file:
    file.write(csv)
