# WATERWHEEL

**WATERWHEEL** (**WATER**loo **W**ater and **H**ydrologic **E**ntity **E**xtractor and **L**inker) is a [spaCy](https://spacy.io/) pipeline component that detects rivers, lakes, and other hydrologic entities, and links these entities to [Wikidata](https://www.wikidata.org/).
Although an acronym, we typically style the name as WaterWheel to avoid the impression that we're screaming all the time.

**PyPI:** https://pypi.org/project/waterwheel/

## Simple Usage

WaterWheel is written as a [spaCy module](https://spacy.io/).
Sample usage:

```python
import spacy
from waterwheel import WaterWheel

nlp = spacy.load('en_core_web_sm')
nlp.add_pipe(WaterWheel(nlp))

doc = nlp('The ultimate source of the Mackenzie River is Thutade Lake.')

for ent in doc.ents:
    print(f'{ent.text}, type: {ent.label_}, {ent._.wikilink} [{ent.start_char}, {ent.end_char}]')

# Results:
# Mackenzie River, type: RIVER, https://www.wikidata.org/wiki/Q3411 [27, 42]
# Thutade Lake, type: LAKE, https://www.wikidata.org/wiki/Q7333634 [46, 58]
```
