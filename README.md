# WATERWHEEL

**WATERWHEEL** (**WATER**loo **W**ater and **H**ydrologic **E**ntity **E**xtractor and **L**inker) is a [spaCy](https://spacy.io/) pipeline component that detects rivers, lakes, and other hydrologic entities, and links these entities to [Wikidata](https://www.wikidata.org/).

## Usage

### Matching Text

```python
import spacy
from waterwheel import WaterWheel

nlp = spacy.load('en_core_web_sm')
ww = WaterWheel(nlp)
nlp.add_pipe(ww)
doc = nlp("Any Text like Amazon is awesome!")

#display results using displacy
displacy.render(doc, style="ent", jupyter=True)

# Access to the wikidata:
[print (ent, ent._.wikilink) for ent in doc.ents]
```