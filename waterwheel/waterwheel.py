import re
import pickle
import pandas as pd
from tqdm import tqdm
from pathlib import Path
from typing import Dict, List

import spacy
from spacy.matcher import PhraseMatcher
from spacy.tokens import Doc, Span


class WaterWheel():
    """Class for finding hydrologic entities in text"""

    def __init__(self, nlp, matcher_file: Path = Path('resources/hydromatch.pkl')):
        """Initialize the class.
        
        Parameters
        ----------
        nlp :
            spacy nlp object
        matcher_file : Path, optional
            File path to load the vocab and wikidata.
            File created using HydroMatch::save_vocab method should be used for this.
        """

        self.matcher = None
        #self.nlp = spacy.load('en_core_web_sm')
        self.nlp = nlp
        self.vocab = {}
        self.wikidata = {}
        self.stop_words = set()

        try:
            with open(matcher_file, 'rb') as file:
                self.vocab, self.matcher, self.wikidata, self.stop_words = pickle.load(file)
        except Exception as e:
            raise RuntimeError(f'Failed to load water bodies from {matcher_file}.\nError: {str(e)}')

        Span.set_extension('wikilink', default=None, force=True)

    def load_vocab_csvs(self, data_dir: Path = Path('../data'), append: bool = True):
        """Load data from csv files.
        
        Parameters
        ----------
        data_dir : Path, optional
            Path to the directory with csv files.
            Format:
                Each csv file should contain columns Name and ID
                Filename should be wikidata_{water_body_type}s.csv
                For example wikidata_rivers.csv
        append : bool, optional
            If True then the new data is appended on top of the previous data.
            Otherwise old data is done away with.
        """
        
        water_bodies = {}
        
        files = data_dir.glob('wikidata_*s.csv')
        files = [str(f) for f in files]
        
        for file in files:
            try:
                wb_type = file.split('wikidata_')[1].split('s.csv')[0].upper()
                water_bodies[wb_type] = []
                df = pd.read_csv(file)
                for i in range(len(df)):
                    if type(df['Name'][i]) is str and (not re.search('^Q[0-9]+', df['Name'][i])):
                        water_bodies[wb_type].append((df['Name'][i].lower(), df['ID'][i]))
            except Exception as e:
                raise RuntimeError(f'Could not load {file}.\nError: {str(e)}')
        
        self.load_vocab(water_bodies, append=append)

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

        if append is False or self.matcher is None:
            self.matcher = PhraseMatcher(self.nlp.vocab, attr='LOWER')
            self.vocab = {}
            self.wikidata = {}
        for key in water_bodies:
            phrases = [self.nlp(wb) for wb, _ in tqdm(water_bodies[key], desc=f'Loading {key}(s)')]
            self.vocab[key] = self.nlp.vocab.strings[key]
            self.matcher.add(key.upper(), None, *phrases)
            if key not in self.wikidata:
                self.wikidata[key] = {}
            for name, id in water_bodies[key]:
                self.wikidata[key][name.lower()] = id

    def save_vocab(self, filename = Path('resources/hydromatch.pkl')):
        """Save vocab and wikidata to file.
        
        Parameters
        ----------
        filename : Path, optional
            Path to file to save the vocab and wikidata to.
        """

        try:
            with open(filename, 'wb') as file:
                pickle.dump((self.vocab, self.matcher, self.wikidata, self.stop_words), file)
        except Exception as e:
            raise RuntimeError(f'Failed to store vocab in {filename}.\nError: {str(e)}')

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
            final_matches.append(match)
            entity = Span(doc, match[2], match[3], label=match[1])
            if match[1] in self.wikidata and match[0].lower() in self.wikidata[match[1]]:
                entity._.set(
                    'wikilink',
                    'https://www.wikidata.org/wiki/' + self.wikidata[match[1]][match[0].lower()]
                )
            entities.append(entity)
        doc.ents = entities
        return doc, final_matches, matches
