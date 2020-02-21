import spacy
from spacy.matcher import PhraseMatcher
from spacy.tokens import Doc, Span, Token

from typing import Dict, List, Tuple
import pickle
import re
from tqdm import tqdm

class HydroMatch():
    """Class for NLP related to Hydrology"""
    def __init__(self, matcher_file: str = "hydro_matcher.pkl"):
        """Initialize the class.
        
        Parameters
        ----------
        matcher_file : str, optional
            File path to load the vocab and wikidata.
            File created using HydroMatch::save_vocab method should be used for this.
        """
        
        self.matcher = None
        self.nlp = spacy.load("en_core_web_sm")
        self.vocab = {}
        self.wikidata = {}
        try:
            with open(matcher_file, "rb") as file:
                self.vocab, self.matcher, self.wikidata = pickle.load(file)
            print (f"Loaded water bodies from {matcher_file}")
        except Exception as e:
            print (str(e))
            print (f"Failed to load water bodies from {matcher_file}")
        Span.set_extension("wikilink", default = None)
    
    def load_vocab(self, water_bodies: Dict, append: bool = True):
        """Load new vocab and wikidata.
        
        Parameters
        ----------
        water_bodies : Dict
            Dictionary containing the list of new water bodies to be loaded.
            Format:
            {
                "LAKE": [(Name, Wiki_Id), ...],
                "RIVER": [(Name, Wiki_Id), ...],
                ...
            }
        append : bool, optional
            If True then the new data is appended on top of the previous data.
            Otherwise old data is done away with.
        """
        if append == False or self.matcher is None:
            self.matcher = PhraseMatcher(self.nlp.vocab, attr = 'LOWER')
            self.vocab = {}
            self.wikidata = {}
        for key in water_bodies:
            print (f"Loading {key}")
            phrases = [self.nlp(wb) for wb, _ in tqdm(water_bodies[key])]
            self.vocab[key] = self.nlp.vocab.strings[key]
            self.matcher.add(key.upper(), None, *phrases)
            if key not in self.wikidata:
                self.wikidata[key] = {}
            for name, id in water_bodies[key]:
                self.wikidata[key][name.lower()] = id
    
    def save_vocab(self, filename = "hydro_matcher.pkl"):
        """Save vocab and wikidata to file.
        
        Parameters
        ----------
        filename : str, optional
            Path to file to save the vocab and wikidata to.
        """
        try:
            with open(filename, "wb") as file:
                pickle.dump((self.vocab, self.matcher, self.wikidata), file)
            print (f"Vocab stored in {filename}")
        except Exception as e:
            print (str(e))
            print (f"Failed to store vocab in {filename}")
    
    def match_type(self, hash: int):
        """Determine the type for the water body.
        
        Parameters
        ----------
        hash : int
            The hash of the string representing each type
        
        Returns
        -------
        type: str
            Type of the water body eg LAKE, RIVER
        """
        for key in self.vocab:
            if self.vocab[key] == hash:
                return key
        return "WATER_BODY"
    
    def match(self, text: str):
        """Match given text against vocab.
        
        Parameters
        ----------
        text : str
            Text to search for water bodies.
        
        Returns
        -------
        final_matches: List
            List of matches found in the text.
            Format:
                [(match_word, start, end), ...]
        doc: Doc
            spaCy Doc object containing entities with matches.
            To be rendered as:
                displacy.render(doc, style="ent", jupyter=True)
            Get list of extra attributes for each entity/match:
                 [ent._.wikilink for ent in doc.ents]
        """
        if self.matcher is None:
            raise AttributeError("Model is not set.")
        
        doc = self.nlp(text)
        matches = [(str(doc[match[1]:match[2]]), self.match_type(match[0]), match[1], match[2]) 
                         for match in self.matcher(doc)]
       
        entities = []
        final_matches = []
        for match in matches:
            if re.search("^[\sA-Z]+$", match[0]) or re.search("^[\sa-z]+$", match[0]):
                continue
            final_matches.append(match)
            entity = Span(doc, match[2], match[3], label=match[1])
            if match[1] in self.wikidata and match[0].lower() in self.wikidata[match[1]]:
                entity._.set(
                    "wikilink", 
                    "https://www.wikidata.org/wiki/" + self.wikidata[match[1]][match[0].lower()]
                )
            entities.append(entity)
        doc.ents = entities
        return final_matches, doc