import re
import os
import pickle
import json
import pandas as pd
from tqdm import tqdm
from pathlib import Path
from typing import Dict, List

import spacy
from spacy.matcher import PhraseMatcher
from spacy.tokens import Doc, Span, DocBin

from .wheel_util import read_files


class WaterWheel():
    """Class for finding hydrologic entities in text"""

    def __init__(self, nlp):
        """Initialize the class.
        
        Parameters
        ----------
        nlp :
            spacy nlp object
        """

        self.matcher = None
        #self.nlp = spacy.load('en_core_web_sm')
        self.nlp = nlp
        self.vocab = {}
        self.wikidata = {}
        self.stop_words = set()
        
        self.vocab, self.wikidata, self.stop_words, self.matcher = read_files(self.nlp) 
        Span.set_extension('wikilink', default=None, force=True)

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
        return 'WATER_BODY'

    def __call__(self, doc: Doc):
        """Match given text against vocab.
        
        Parameters
        ----------
        doc : Doc
            spacy Doc to search for water bodies.
        
        Returns
        -------
        doc: Doc
            spaCy Doc object containing entities with matches.
            To be rendered as:
                displacy.render(doc, style="ent", jupyter=True)
            Get list of extra attributes for each entity/match:
                 [ent._.wikilink for ent in doc.ents]
        final_matches: List
            List of matches found in the text.
            Format:
                [(match_word, start, end), ...]
        all_matches: List
            List of all matches including the ones filtered out in the final matches.
        """

        if self.matcher is None:
            raise AttributeError('Model is not set.')
        
        matches = [(str(doc[match[1]:match[2]]), self.match_type(match[0]), match[1], match[2])
                   for match in self.matcher(doc)]

        entities = []
        final_matches = []
        for match in matches:
            if match[0].lower() in self.stop_words:
                if str(doc[match[3]:match[3] + 1]).lower() not in ['river', 'lake']:
                    continue
            elif re.search('^[\sA-Z]+$', match[0]) or re.search('^[\sa-z]+$', match[0]):
                continue
            entity = Span(doc, match[2], match[3], label=match[1])
            if match[1] in self.wikidata and match[0].lower() in self.wikidata[match[1]]:
                entity._.set(
                    'wikilink',
                    'https://www.wikidata.org/wiki/' + self.wikidata[match[1]][match[0].lower()]
                )
            try:
                doc.ents = entities + [entity]
            except ValueError:
                continue
            entities.append(entity)
            final_matches.append(match)
        doc.ents = entities
        return doc, final_matches, matches
