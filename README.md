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

### Matching Text

```python
from waterwheel import WaterWheel

import spacy
nlp = spacy.load('en_core_web_sm')
doc = nlp("Any Text like Amazon is awesome!")

ww = WaterWheel(nlp)
processed, matches, _ = ww(doc)

#display results using displacy
displacy.render(processed, style="ent", jupyter=True)

# Access to the wikidata:
[print (ent, ent._.wikilink) for ent in processed.ents]
```

### (Re)Loading Vocab

```python
from waterwheel import wheel_util

wheel_util.add_vocab_csvs(data_dir, nlp, append = True)
# for details check documentation.
```