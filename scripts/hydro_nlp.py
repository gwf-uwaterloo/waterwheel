import spacy
from spacy.matcher import PhraseMatcher

import pickle
import re
from tqdm import tqdm

class HydroMatch():
    
    def __init__(self, matcher_file = "hydro_matcher.pkl"):
        self.matcher = None
        self.nlp = spacy.load("en_core_web_sm")
        self.vocab = {}
        try:
            with open(matcher_file, "rb") as file:
                self.vocab, self.matcher = pickle.load(file)
            print (f"Loaded water bodies from {matcher_file}")
        except Exception as e:
            print (str(e))
            print (f"Failed to load water bodies from {matcher_file}")
    
    def load_vocab(self, water_bodies, append = True):
        if append == False or self.matcher is None:
            self.matcher = PhraseMatcher(self.nlp.vocab, attr = 'LOWER')
            self.vocab = {}
        for key in water_bodies:
            print (f"Loading {key}")
            phrases = [self.nlp(wb) for wb in tqdm(water_bodies[key])]
            self.vocab[key] = self.nlp.vocab.strings[key]
            self.matcher.add(key.upper(), None, *phrases)
    
    def save_vocab(self, filename = "hydro_matcher.pkl"):
        try:
            with open(filename, "wb") as file:
                pickle.dump((self.vocab, self.matcher), file)
            print (f"Vocab stored in {filename}")
        except Exception as e:
            print (str(e))
            print (f"Failed to store vocab in {filename}")
    
    def match_type(self, hash):
        for key in self.vocab:
            if self.vocab[key] == hash:
                return key
        return "WATER_BODY"
    
    def match(self, text):
        if self.matcher is None:
            raise AttributeError("Model is not set.")
        
        doc = self.nlp(text)
        matches = [(str(doc[match[1]:match[2]]), self.match_type(match[0])) 
                         for match in self.matcher(doc)]
       
        entities = [{
            "text": text,
            "ents": []
        }]
        final_matches = []
        for match in matches:
            if re.search("^[\sA-Z]+$", match[0]) or re.search("^[\sa-z]+$", match[0]):
                continue
            final_matches.append(match)
            for m in re.finditer(match[0], text):
                entities[0]["ents"].append({
                    "start": m.start(), "end": m.end(), "label": match[1], "title": None
                })
        return final_matches, entities