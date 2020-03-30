import requests
from tqdm import tqdm
import json
import re

url = 'https://query.wikidata.org/sparql'
subquery = """
SELECT ?item ?itemLabel ?altLabel
WHERE
{
  ?item p:P31/ps:P31/wdt:P279* wd:Q35657.
  ?article schema:about ?item.
  OPTIONAL { ?item skos:altLabel ?altLabel . FILTER (lang(?altLabel) = "en") }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
"""

waterbodies = {}
query = subquery + "} GROUP BY ?item ?itemLabel ?altLabel"


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
    print (str(e))

print(query)

pairs = []
for key, names in waterbodies.items():
    for name in names:
        pairs.append((key, name))

print ("length of waterbodies", len(pairs))

try:
    csv = "Name,ID\n"
    for key, name in pairs:
        csv += f"{name.replace(',', ';')},{key.replace(',', ';')}\n"

    with open("wikidata_us_states.csv", "w") as file:
        file.write(csv.encode('ascii', 'ignore').decode())
except Exception as e:
    print (str(e))
