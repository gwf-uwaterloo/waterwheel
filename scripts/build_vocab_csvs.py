import spacy
from util import *
nlp = spacy.load('en_core_web_sm')
build_vocab_csvs(nlp)
