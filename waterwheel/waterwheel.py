import re
import os
import pickle
import json
import pandas as pd
from tqdm import tqdm
from pathlib import Path
from typing import Dict, List

import spacy
from spacy import language
from spacy.matcher import PhraseMatcher
from spacy.tokens import Doc, Span, DocBin


class WaterWheel():
    """Class for finding hydrologic entities in text"""

    def __init__(self, nlp: language):
        """Initialize the class.
        
        Parameters
        ----------
        nlp : language
            spacy nlp object
        """

        self.matcher = None
        #self.nlp = spacy.load('en_core_web_sm')
        self.nlp = nlp
        self.vocab = {}
        self.wikidata = {}
        self.stop_words = set()
        
        self.load_features_data() 
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
                # skip mathces that are ALL_CAPS or all_small.
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
                # skip overlapping or intersecting matches.
                continue
            entities.append(entity)
            final_matches.append(match)
        doc.ents = entities
        return doc, final_matches, matches
    
    def load_features_data(self):
        """Load necessary data from resource files.
        """
        
        doc_bin_file = Path(os.path.dirname(os.path.realpath(__file__))) / 'resources/doc_bin.pkl'
        vocab_file = Path(os.path.dirname(os.path.realpath(__file__))) / 'resources/vocab.json'
        wikidata_file = Path(os.path.dirname(os.path.realpath(__file__))) / 'resources/wikidata.json'
        stop_words_file = Path(os.path.dirname(os.path.realpath(__file__))) / 'resources/stop_words.txt'
        
        try:
            with open(vocab_file) as file:
                self.vocab = json.load(file)
        except Exception as e:
            raise RuntimeError(f'Failed to load vocab from {vocab_file}.\nError: {str(e)}')

        try:
            with open(wikidata_file) as file:
                self.wikidata = json.load(file)
        except Exception as e:
            raise RuntimeError(f'Failed to load wikidata from {wikidata_file}.\nError: {str(e)}')

        try:
            with open(stop_words_file) as file:
                self.stop_words = set(file.read().splitlines())
        except Exception as e:
            raise RuntimeError(f'Failed to load stop_words from {stop_words_file}.\nError: {str(e)}')

        try:
            with open(doc_bin_file, 'rb') as file:
                doc_bins_bytes = pickle.load(file)
            doc_bins = {key: DocBin().from_bytes(value) for key, value in doc_bins_bytes.items()}
            phrases_bin = {key: list(bin.get_docs(self.nlp.vocab)) for key, bin in doc_bins.items()}
            self.matcher = PhraseMatcher(self.nlp.vocab, attr='LOWER')
            for key, phrases in phrases_bin.items():
                self.matcher.add(key.upper(), None, *phrases)
                #matcher.add(key.upper(), phrases)
        except Exception as e:
            raise RuntimeError(f'Failed to load water bodies from {doc_bin_file_file}.\nError: {str(e)}')
