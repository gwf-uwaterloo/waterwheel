import requests
from tqdm import tqdm
import json
import re
import sys

url = 'https://query.wikidata.org/sparql'
subquery = """
SELECT ?item ?itemLabel ?altLabel
WHERE 
{
  ?item wdt:P31 wd:Q8502.
  ?item wdt:P2660 ?height
  OPTIONAL { ?item skos:altLabel ?altLabel . FILTER (lang(?altLabel) = "en") }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
  FILTER (CONTAINS(STR(?item), 
"""
combinations = [f"Q{n}" for n in range(10, 100)]
waterbodies = {}
not_done = []
"""
combinations = []
for c in ["Q21", "Q27"]:
    for i in range(10):
        combinations.append(c+str(i))
"""
combinations = [f"Q{sys.argv[1]}"]
for comb in tqdm(combinations):
    query = subquery + f"'{comb}'))" + "} GROUP BY ?item ?itemLabel ?altLabel"
    try:
        r = requests.get(url, params = {'format': 'json', 'query': query})
        data = r.json()
        for entry in data["results"]["bindings"]:
            key = entry["item"]["value"].split("/")[-1]
            label = entry['itemLabel']['value'] if 'itemLabel' in entry else ""
            alias = entry['altLabel']['value'] if 'altLabel' in entry else ""
            
            if not (re.search('^Q[0-9]+', label) or label == ""):
                if key not in waterbodies:
                    waterbodies[key] = set()
                waterbodies[key].add(label.lower())
            
            if not (re.search('^Q[0-9]+', alias) or alias == ""):
                if key not in waterbodies:
                    waterbodies[key] = set()
                waterbodies[key].add(alias.lower())
    except Exception as e:
        #raise(e)
        print (str(e))
        print (comb)
        not_done.append(comb)
print (not_done)
pairs = []
for key, names in waterbodies.items():
    for name in names:
        pairs.append((key, name))

print ("length of waterbodies", len(pairs))

try:
    #csv = "Name,ID\n"
    csv = ""
    for key, name in pairs:
        csv += f"{name.replace(',', ';')},{key.replace(',', ';')}\n"

    with open("wikidata_mountains.csv", "a") as file:
        file.write(csv.encode('ascii', 'ignore').decode())
except Exception as e:
    print (str(e))
