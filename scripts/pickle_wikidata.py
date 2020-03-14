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
J = pd.read_csv("H:\\Courses\\RA\\wikidata-water-features\\data\\wikidata_canadianprovinces.csv")
K = pd.read_csv("H:\\Courses\\RA\\wikidata-water-features\\data\\wikidata_oceans.csv")
wikidata = {"LAKE": {}, "RIVER": {}, "PROVINCE": {}, "OCEAN": {}}

for i in range(len(L)):
    if not re.search("^Q[0-9]+", L["Name"][i]):
        wikidata["LAKE"][L["Name"][i].lower()] = L["ID"][i]
for i in range(len(R)):
    if not re.search("^Q[0-9]+", R["Name"][i]):
        wikidata["RIVER"][R["Name"][i].lower()] = R["ID"][i]
for i in range(len(J)):
    if not re.search("^Q[0-9]+", R["Name"][i]):
        wikidata["PROVINCE"][R["Name"][i].lower()] = R["ID"][i]
for i in range(len(K)):
    if not re.search("^Q[0-9]+", R["Name"][i]):
        wikidata["OCEAN"][R["Name"][i].lower()] = R["ID"][i]

with open("H:\\Courses\\RA\\wikidata-water-features\\scripts\\hydro_matcher.pkl", "rb") as file:
    vocab, matcher = pickle.load(file)

with open("H:\\Courses\\RA\\wikidata-water-features\\scripts\\hydro_matcher_new.pkl", "wb") as file:
    pickle.dump((vocab, matcher, wikidata), file)


with open("H:\\Courses\\RA\\wikidata-water-features\\scripts\\hydro_matcher_new.pkl", "rb") as file:
    vocab, matcher, wikidata = pickle.load(file)
