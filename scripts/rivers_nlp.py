import spacy
from spacy.matcher import PhraseMatcher

import pickle
import re
from tqdm import tqdm

class RiverMatch():
    
    def __init__(self, matcher_file = "rivers_matcher.pkl"):
        self.matcher = None
        self.nlp = spacy.load("en_core_web_sm")
        try:
            with open(matcher_file, "rb") as file:
                self.matcher = pickle.load(file)
            print (f"Loaded rivers from {matcher_file}")
        except Exception as e:
            print (str(e))
            print (f"Failed to load rivers from {matcher_file}")
    
    def load_rivers(self, rivers, append = True):
        phrases = [self.nlp(river) for river in tqdm(rivers)]
        if append == False or self.matcher is None:
            self.matcher = PhraseMatcher(self.nlp.vocab, attr = 'LOWER')
        self.matcher.add("RIVER", None, *phrases)
    
    def save_vocab(self, filename = "rivers_matcher.pkl"):
        try:
            with open(filename, "wb") as file:
                pickle.dump(self.matcher, file)
            print (f"Vocab stored in {filename}")
        except Exception as e:
            print (str(e))
            print (f"Failed to store vocab in {filename}")
    
    def match(self, text):
        if self.matcher is None:
            raise AttributeError("Model is not set.")
        
        doc = self.nlp(text)
        matches = [str(doc[match[1]:match[2]]) for match in self.matcher(doc)]
       
        entities = [{
            "text": text,
            "ents": []
        }]
        for match in matches:
            for m in re.finditer(match, text):
                entities[0]["ents"].append({
                    "start": m.start(), "end": m.end(), "label": "RIVER", "title": None
                })
        return matches, entities