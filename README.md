# WATERWHEEL

**WATERWHEEL** (**WATER**loo **W**ater and **H**ydrologic **E**ntity **E**xtractor and **L**inker) is a [spaCy](https://spacy.io/) module that detects rivers, lakes, and other hydrologic entities, and links these entities to [Wikidata](https://www.wikidata.org/).

## Dependencies

Following packages are required to be installed:

```python
pip install -U spacy
python -m spacy validate
python -m spacy download en_core_web_sm

pip install pandas

pip install tqdm
```

## Usage

Use the module file `waterwheel/hydromatch.py`

### Matching Text

```python
from hydromatch import *
hm = HydroMatch()
matches, doc, _ = hm.match("Any Text")

#display results using displacy
displacy.render(doc, style="ent", jupyter=True)

# Access to the wikidata:
[print (ent, ent._.wikilink) for ent in doc.ents]
```

### (Re)Loading Vocab

```python
from hydromatch import *
hm = HydroMatch()

#load from csv files (check documentation for details)
hm.load_vocab_csvs(data_dir, append = False)

#load directly from dict object (check documentation for details)
hm.load_vocab(water_bodies, append = False)

#save vocab
hm.save_vocab()
```