import pandas as pd
from pathlib import Path
from typing import Dict, List
import re
import os
from tqdm import tqdm
from spacy.matcher import PhraseMatcher

matcher_file = Path(os.path.dirname(os.path.realpath(__file__))) / 'hydromatch.pkl'

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
        vocab, matcher, wikidata, stop_words = pickle.load(matcher_file)

    if append is False:
        matcher = PhraseMatcher(nlp.vocab, attr='LOWER')
        vocab = {}
        wikidata = {}
    for key in water_bodies:
        phrases = [nlp(wb) for wb, _ in tqdm(water_bodies[key], desc=f'Loading {key}(s)')]
        vocab[key] = nlp.vocab.strings[key]
        matcher.add(key.upper(), None, *phrases)
        if key not in wikidata:
            wikidata[key] = {}
        for name, id in water_bodies[key]:
            wikidata[key][name.lower()] = id
    
    try:
        with open(matcher_file, 'wb') as file:
            pickle.dump((vocab, matcher, wikidata, stop_words), file)
    except Exception as e:
        raise RuntimeError(f'Failed to store vocab in {filename}.\nError: {str(e)}')

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
                if type(df['Name'][i]) is str and (not re.search('^Q[0-9]+', df['Name'][i])):
                    water_bodies[wb_type].append((df['Name'][i].lower(), df['ID'][i]))
        except Exception as e:
            raise RuntimeError(f'Could not load {file}.\nError: {str(e)}')
    
    add_vocab(water_bodies, nlp, append=append)