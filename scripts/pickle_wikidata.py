import pandas as pd
import re
import pickle
import spacy
from spacy.matcher import PhraseMatcher
from spacy.tokens import Doc, Span, Token

import pickle
import re
from tqdm import tqdm

L = pd.read_csv("H:\\Courses\\RA\\wikidata-water-features\\data\\wikidata_lakes.csv")
R = pd.read_csv("H:\\Courses\\RA\\wikidata-water-features\\data\\wikidata_rivers.csv")
C = pd.read_csv("H:\\Courses\\RA\\wikidata-water-features\\data\\wikidata_canadian_provinces.csv")
O = pd.read_csv("H:\\Courses\\RA\\wikidata-water-features\\data\\wikidata_oceans.csv")
U = pd.read_csv("H:\\Courses\\RA\\wikidata-water-features\\data\\wikidata_us_states.csv")

wikidata = {"LAKE": {}, "RIVER": {}, "PROVINCE": {}, "OCEAN": {}, "STATE": {}}

for i in range(len(L)):
    if not re.search("^Q[0-9]+", L["Name"][i]):
        wikidata["LAKE"][L["Name"][i].lower()] = L["ID"][i]
for i in range(len(R)):
    if not re.search("^Q[0-9]+", R["Name"][i]):
        wikidata["RIVER"][R["Name"][i].lower()] = R["ID"][i]
for i in range(len(C)):
    if not re.search("^Q[0-9]+", C["Name"][i]):
        wikidata["PROVINCE"][C["Name"][i].lower()] = C["ID"][i]
for i in range(len(O)):
    if not re.search("^Q[0-9]+", O["Name"][i]):
        wikidata["OCEAN"][O["Name"][i].lower()] = O["ID"][i]
for i in range(len(U)):
    if not re.search("^Q[0-9]+", U["Name"][i]):
        wikidata["STATE"][U["Name"][i].lower()] = U["ID"][i]

with open("H:\\Courses\\RA\\wikidata-water-features\\scripts\\hydro_matcher.pkl", "rb") as file:
    vocab, matcher = pickle.load(file)

with open("H:\\Courses\\RA\\wikidata-water-features\\scripts\\hydro_matcher_new.pkl", "wb") as file:
    pickle.dump((vocab, matcher, wikidata), file)


with open("H:\\Courses\\RA\\wikidata-water-features\\scripts\\hydro_matcher_new.pkl", "rb") as file:
    vocab, matcher, wikidata = pickle.load(file)
