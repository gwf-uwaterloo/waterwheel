import re
import os
import pickle
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List
from tqdm import tqdm

from spacy.tokens import Doc, Span, DocBin
from spacy.matcher import PhraseMatcher

doc_bin_file = Path(os.path.dirname(os.path.realpath(__file__))) / 'resources/doc_bin.pkl'
vocab_file = Path(os.path.dirname(os.path.realpath(__file__))) / 'resources/vocab.json'
wikidata_file = Path(os.path.dirname(os.path.realpath(__file__))) / 'resources/wikidata.json'
stop_words_file = Path(os.path.dirname(os.path.realpath(__file__))) / 'resources/stop_words.txt'

def read_files(nlp):
    """Load necessary data from resource files.
    
    Parameters
    ----------
    nlp:
        spacy nlp object
    
    Returns
    -------
    vocab: Dict
        A dictionary containing the different water body types and their hash value.
    wikidata: Dict
        A dictionary with each wikilink data for every water_body
    stop_words: List
        A set of common words in English
    matcher: PhraseMatcher
        A PhraseMatcher object with all vocab loaded.
    """
    
    vocab = {}
    wikidata = {}
    stop_words = set()
    matcher = None
    
    try:
        with open(vocab_file) as file:
            vocab = json.load(file)
    except Exception as e:
        raise RuntimeError(f'Failed to load vocab from {vocab_file}.\nError: {str(e)}')

    try:
        with open(wikidata_file) as file:
            wikidata = json.load(file)
    except Exception as e:
        raise RuntimeError(f'Failed to load wikidata from {wikidata_file}.\nError: {str(e)}')

    try:
        with open(stop_words_file) as file:
            stop_words = set(file.read().splitlines())
    except Exception as e:
        raise RuntimeError(f'Failed to load stop_words from {stop_words_file}.\nError: {str(e)}')

    try:
        with open(doc_bin_file, 'rb') as file:
            doc_bins_bytes = pickle.load(file)
        doc_bins = {key: DocBin().from_bytes(value) for key, value in doc_bins_bytes.items()}
        phrases_bin = {key: list(bin.get_docs(nlp.vocab)) for key, bin in doc_bins.items()}
        matcher = PhraseMatcher(nlp.vocab, attr='LOWER')
        for key, phrases in phrases_bin.items():
            matcher.add(key.upper(), None, *phrases)
            #matcher.add(key.upper(), phrases)
    except Exception as e:
        raise RuntimeError(f'Failed to load water bodies from {doc_bin_file_file}.\nError: {str(e)}')
    
    return vocab, wikidata, stop_words, matcher

def write_files(vocab, wikidata, phrase_map):
    """Writes necessary data to resource files.
    
    Parameters
    ----------
    vocab: Dict
        A dictionary containing the different water body types and their hash value.
    wikidata: Dict
        A dictionary with each wikilink data for every water_body
    phrase_map: Dict
        A map of different water body types and DocBin of phrases.
    """
    
    try:
        with open(vocab_file, 'w') as file:
            json.dump(vocab, file)
    except Exception as e:
        raise RuntimeError(f'Failed to write vocab to {vocab_file}.\nError: {str(e)}')
    
    try:
        with open(wikidata_file, 'w') as file:
            json.dump(wikidata, file)
    except Exception as e:
        raise RuntimeError(f'Failed to write wikidata to {wikidata_file}.\nError: {str(e)}')
    
    try:
        doc_bins = {}
        for key in phrase_map:
            doc_bin = DocBin()
            for doc in phrase_map[key]:
                doc_bin.add(doc)
            doc_bins[key] = doc_bin.to_bytes()
        with open(doc_bin_file, 'wb') as file:
            pickle.dump(doc_bins, file)
    except Exception as e:
        raise RuntimeError(f'Failed to write water_bodies to {doc_bin_file}.\nError: {str(e)}')       

def add_vocab(water_bodies: Dict, nlp, append: bool = True):
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
    nlp:
        spacy nlp object
    append : bool, optional
        If True then the new data is appended on top of the previous data.
        Otherwise old data is done away with.
    """
    
    if append:
        vocab, wikidata, stop_words, matcher = read_files(nlp)
    else:
        matcher = PhraseMatcher(nlp.vocab, attr='LOWER')
        vocab = {}
        wikidata = {}
    
    phrase_map = {}
    for key in water_bodies:
        phrases = [nlp(wb) for wb, _ in tqdm(water_bodies[key], desc=f'Loading {key}(s)')]
        phrase_map[key] = phrases
        vocab[key] = nlp.vocab.strings[key]
        matcher.add(key.upper(), None, *phrases)
        #matcher.add(key.upper(), phrases)
        if key not in wikidata:
            wikidata[key] = {}
        for name, id in water_bodies[key]:
            wikidata[key][name.lower()] = id
    
    write_files(vocab, wikidata, phrase_map)

def add_vocab_csvs(data_dir: Path, nlp, append: bool = True):
    """Load data from csv files.
    
    Parameters
    ----------
    data_dir : Path
        Path to the directory with csv files.
        Format:
            Each csv file should contain columns Name and ID
            Filename should be wikidata_{water_body_type}s.csv
            For example wikidata_rivers.csv
    nlp:
        spacy nlp object
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
                if (type(df['Name'][i]) is str and
                        len(df['Name'][i]) > 1 and
                        (not re.search('^Q[0-9]+', df['Name'][i]))):
                    water_bodies[wb_type].append((df['Name'][i].lower(), df['ID'][i]))
        except Exception as e:
            raise RuntimeError(f'Could not load {file}.\nError: {str(e)}')
    
    add_vocab(water_bodies, nlp, append=append)