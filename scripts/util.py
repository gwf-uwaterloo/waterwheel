import re
import os
import srsly
import pandas as pd
from pathlib import Path
from typing import Dict, Tuple
from tqdm import tqdm
from collections import OrderedDict

from spacy.tokens import DocBin
from spacy.language import Language

data_dir = Path(os.path.dirname(os.path.realpath(__file__))) / 'data'
doc_bins_file = Path(os.path.dirname(os.path.realpath(__file__))) / 'data/doc_bins.msgpack'
vocab_file = Path(os.path.dirname(os.path.realpath(__file__))) / 'data/vocab.json'
wikidata_file = Path(os.path.dirname(os.path.realpath(__file__))) / 'data/wikidata.json'
stop_words_file = Path(os.path.dirname(os.path.realpath(__file__))) / 'data/stop_words.json'

def read_data_files():
    """Load necessary data from data files.

    Returns
    -------
    vocab: Dict
        A dictionary containing the different water body types and their hash value.
    wikidata: Dict
        A dictionary with each wikilink data for every water_body
    stop_words: set
        A set of common words in English
    """

    vocab = srsly.read_json(vocab_file)
    wikidata = srsly.read_json(wikidata_file)
    stop_words = set(srsly.read_json(stop_words_file)['stop_words'])
    return vocab, wikidata, stop_words

def write_data_files(vocab: Dict, wikidata: Dict, stop_words: set, doc_bins_bytes: Dict):
    """Writes necessary data to resource files.

    Parameters
    ----------
    vocab: Dict
        A dictionary containing the different water body types and their hash value.
    wikidata: Dict
        A dictionary with each wikilink data for every water_body
    stop_words: set
        A set of commong words in English.
    doc_bins_bytes: Dict
        A dictionary of DocBin bytes for each water body type.
    """

    serial = OrderedDict(
        (
            ('stop_words', list(stop_words)),
            ('vocab', vocab),
            ('wikidata', wikidata),
            ('doc_bins', doc_bins_bytes),
        )
    )
    srsly.write_msgpack(doc_bins_file, serial)

def name_split(name: str):
    """Function to split waterbody names.

    Parameters
    ----------
    name : str
        name of the waterbody eg 'amazon riverbasin'

    Returns
    -------
    names : Tuple
        all possible variations of name
        eg ('amazon riverbasin', 'amazon')
    """

    s = name.lower()
    tokens = ['river', 'lake', 'basin', 'ocean', 'sea']
    for token in tokens:
        s = s.replace(token, "")
    return s.strip()

def build_vocab(water_bodies: Dict, nlp: Language):
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
    nlp: Language
        spacy nlp object
    """

    vocab = {}
    wikidata = {}
    doc_bins_bytes = {}
    stop_words = set(srsly.read_json(stop_words_file)['stop_words'])

    for key in water_bodies:
        doc_bin = DocBin()
        for wb, _ in tqdm(water_bodies[key], desc=f'Loading {key}(s)'):
            doc_bin.add(nlp(wb))
        doc_bins_bytes[key] = doc_bin.to_bytes()

        if key not in wikidata:
            wikidata[key] = {}
        for name, id in water_bodies[key]:
            wikidata[key][name.lower()] = id

        vocab[str(nlp.vocab.strings[key])] = key
    write_data_files(vocab, wikidata, stop_words, doc_bins_bytes)

def build_vocab_csvs(nlp: Language, data_dir: Path = data_dir):
    """Load data from csv files.

    Parameters
    ----------
    nlp : Language
        spacy nlp object
    data_dir : Path
        Path to the directory with csv files.
        Format:
            Each csv file should contain columns Name and ID
            Filename should be wikidata_{water_body_type}s.csv
            For example wikidata_rivers.csv
    """

    water_bodies = {}

    files = data_dir.glob('wikidata_*s.csv')
    files = [str(f) for f in files]
    
    for file in files:
        wb_type = file.split('wikidata_')[1].split('s.csv')[0].upper()
        water_bodies[wb_type] = []
        df = pd.read_csv(file)
        for i in range(len(df)):
            if (type(df['Name'][i]) is str and
            len(df['Name'][i]) > 1 and
            (not re.search('^Q[0-9]+', df['Name'][i]))):
                name = name_split(df['Name'][i])
                if re.search('^[^a-zA-Z\d]+$', name):
                    continue
                water_bodies[wb_type].append((name, df['ID'][i]))
    build_vocab(water_bodies, nlp)
