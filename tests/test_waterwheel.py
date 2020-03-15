import unittest
import spacy
from waterwheel import WaterWheel
from util import *

class TestWaterWheel(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.nlp = spacy.load('en_core_web_sm')
        self.ww = WaterWheel(self.nlp)
        self.nlp.add_pipe(self.ww)

    def test_pipeline_added(self):
        self.assertEqual(self.nlp.pipe_names[-1], 'waterwheel')

    def test_proper_nouns(self):
        text = 'The amazon is something and the AMAZON is something.'
        doc = self.nlp(text)
        self.assertEqual(len(doc.ents), 0)

        text = 'The Amazon is something.'
        doc = self.nlp(text)
        self.assertEqual(str(doc.ents[0]), 'Amazon')
        self.assertEqual(str(doc.ents[0].label_), 'RIVER')
        for ent in doc.ents:
            self.assertIsNotNone(ent._.wikilink)

        text = 'The amazon river is something and the AMAZON river is something'
        doc = self.nlp(text)
        self.assertEqual(str(doc.ents[0]), 'amazon river')
        self.assertEqual(str(doc.ents[0].label_), 'RIVER')
        self.assertEqual(str(doc.ents[1]), 'AMAZON river')
        self.assertEqual(str(doc.ents[1].label_), 'RIVER')
        for ent in doc.ents:
            self.assertIsNotNone(ent._.wikilink)

        doc = self.nlp('This image of the Pacific Ocean seafloor and PACIFIC ocean was created by the World Data Center.')
        self.assertEqual(str(doc.ents[0]), 'Pacific Ocean')
        self.assertEqual(str(doc.ents[0].label_), 'OCEAN')
        self.assertEqual(str(doc.ents[1]), 'PACIFIC ocean')
        self.assertEqual(str(doc.ents[1].label_), 'OCEAN')
        for ent in doc.ents:
            self.assertIsNotNone(ent._.wikilink)

        text = 'Province of Ontario is something and ONTARIO is something else'
        doc = self.nlp(text)
        self.assertEqual(str(doc.ents[0]), 'Ontario')
        self.assertEqual(str(doc.ents[0].label_), 'PROVINCE')
        self.assertEqual(str(doc.ents[1]), 'ONTARIO')
        self.assertEqual(str(doc.ents[1].label_), 'PROVINCE')
        for ent in doc.ents:
            self.assertIsNotNone(ent._.wikilink)

    def test_common_uncommon_overlap(self):
        text = 'The River Cherwell is a major tributary of the River Thames in central England.'
        doc = self.nlp(text)
        self.assertEqual(str(doc.ents[0]), 'River Cherwell')
        self.assertEqual(str(doc.ents[0].label_), 'RIVER')
        self.assertEqual(str(doc.ents[1]), 'River Thames')
        self.assertEqual(str(doc.ents[1].label_), 'RIVER')
        for ent in doc.ents:
            self.assertIsNotNone(ent._.wikilink)
        text = 'The Lake Ontario is surely awesome and so is river Thames.'
        doc = self.nlp(text)
        self.assertEqual(str(doc.ents[0]), 'Lake Ontario')
        self.assertEqual(str(doc.ents[0].label_), 'LAKE')
        self.assertEqual(str(doc.ents[1]), 'river Thames')
        self.assertEqual(str(doc.ents[1].label_), 'RIVER')
        for ent in doc.ents:
            self.assertIsNotNone(ent._.wikilink)

    def test_compound_references(self):
        text = '''Aggregated gridded soil texture dataset
        for Mississippi/Missouri Rivers,
        Mackenzie and Nelson-Churchill River Basins.'''
        doc = self.nlp(text)

        self.assertEqual(str(doc.ents[0]), 'Mississippi')
        self.assertEqual(str(doc.ents[0].label_), 'RIVER')
        self.assertEqual(str(doc.ents[1]), 'Missouri')
        self.assertEqual(str(doc.ents[1].label_), 'RIVER')
        self.assertEqual(str(doc.ents[2]), 'Mackenzie')
        self.assertEqual(str(doc.ents[2].label_), 'RIVER')
        self.assertEqual(str(doc.ents[3]), 'Nelson')
        self.assertEqual(str(doc.ents[3].label_), 'RIVER')
        self.assertEqual(str(doc.ents[4]), 'Churchill River')
        self.assertEqual(str(doc.ents[4].label_), 'RIVER')

        for ent in doc.ents:
            self.assertIsNotNone(ent._.wikilink)

    def test_conjunctions(self):
        text = '''When a second fault line, the Saint Lawrence rift,
        formed approximately 570 million years ago,[15] the basis for
        Lakes Ontario and Erie were created, along with what would become
         the Saint Lawrence River. And the Mississippi and Missouri Rivers.
        '''
        doc = self.nlp(text)

        self.assertEqual(str(doc.ents[0]), 'Saint Lawrence')
        self.assertEqual(str(doc.ents[0].label_), 'RIVER')
        self.assertEqual(str(doc.ents[1]), 'Ontario')
        self.assertEqual(str(doc.ents[1].label_), 'LAKE')
        self.assertEqual(str(doc.ents[2]), 'Erie')
        self.assertEqual(str(doc.ents[2].label_), 'LAKE')
        self.assertEqual(str(doc.ents[3]), 'Saint Lawrence River')
        self.assertEqual(str(doc.ents[3].label_), 'RIVER')
        self.assertEqual(str(doc.ents[4]), 'Mississippi')
        self.assertEqual(str(doc.ents[4].label_), 'RIVER')
        self.assertEqual(str(doc.ents[5]), 'Missouri')
        self.assertEqual(str(doc.ents[5].label_), 'RIVER')

        for ent in doc.ents:
            self.assertIsNotNone(ent._.wikilink)

        doc = self.nlp(' Eastern boundary of Yukon mostly follows the divide between the Yukon River and the Mackenzie River.')
        self.assertEqual(str(doc.ents[0]), 'Yukon')
        self.assertEqual(str(doc.ents[0].label_), 'PROVINCE')
        self.assertEqual(str(doc.ents[1]), 'Yukon River')
        self.assertEqual(str(doc.ents[1].label_), 'RIVER')
        self.assertEqual(str(doc.ents[2]), 'Mackenzie River')
        self.assertEqual(str(doc.ents[2].label_), 'RIVER')
        for ent in doc.ents:
            self.assertIsNotNone(ent._.wikilink)

        text = 'Pacific and Indian Ocean are two important waterbodies in the world.'
        doc = self.nlp(text)
        self.assertEqual(str(doc.ents[0]), 'Pacific')
        self.assertEqual(str(doc.ents[0].label_), 'OCEAN')
        self.assertEqual(str(doc.ents[1]), 'Indian Ocean')
        self.assertEqual(str(doc.ents[1].label_), 'OCEAN')
        for ent in doc.ents:
            self.assertIsNotNone(ent._.wikilink)

        text = 'The treaty between Ontario and Quebec were established.'
        doc = self.nlp(text)
        self.assertEqual(str(doc.ents[0]), 'Ontario')
        self.assertEqual(str(doc.ents[0].label_), 'PROVINCE')
        self.assertEqual(str(doc.ents[1]), 'Quebec')
        self.assertEqual(str(doc.ents[1].label_), 'PROVINCE')
        for ent in doc.ents:
            self.assertIsNotNone(ent._.wikilink)

    def test_qualifier_effect(self):
        text = 'Is Mississippi a river or a lake?'
        doc = self.nlp(text)
        self.assertEqual(str(doc.ents[0]), 'Mississippi')
        self.assertEqual(str(doc.ents[0].label_), 'RIVER')
        for ent in doc.ents:
            self.assertIsNotNone(ent._.wikilink)
        text = 'Is Mississippi Lake a river or a lake?'
        doc = self.nlp(text)
        self.assertEqual(str(doc.ents[0]), 'Mississippi Lake')
        self.assertEqual(str(doc.ents[0].label_), 'LAKE')
        for ent in doc.ents:
            self.assertIsNotNone(ent._.wikilink)

        text = 'Is Ontario Lake a province or a lake?'
        doc = self.nlp(text)
        self.assertEqual(str(doc.ents[0]), 'Ontario')
        self.assertEqual(str(doc.ents[0].label_), 'PROVINCE')
        for ent in doc.ents:
            self.assertIsNotNone(ent._.wikilink)

        text = 'Is Lake Ontario Lake a province or a lake?'
        doc = self.nlp(text)
        self.assertEqual(str(doc.ents[0]), 'Lake Ontario')
        self.assertEqual(str(doc.ents[0].label_), 'LAKE')
        for ent in doc.ents:
            self.assertIsNotNone(ent._.wikilink)

        text = 'Is arctic wolf an animal in Arctic?'
        doc = self.nlp(text)
        self.assertEqual(str(doc.ents[0]), 'Arctic')
        self.assertEqual(str(doc.ents[0].label_), 'OCEAN')
        for ent in doc.ents:
            self.assertIsNotNone(ent._.wikilink)

        text = 'Is Arctic wolf an animal in Arctic?'
        doc = self.nlp(text)
        self.assertEqual(str(doc.ents[0]), 'Arctic')
        self.assertEqual(str(doc.ents[0].label_), 'OCEAN')
        self.assertEqual(str(doc.ents[1]), 'Arctic')
        self.assertEqual(str(doc.ents[1].label_), 'OCEAN')
        for ent in doc.ents:
            self.assertIsNotNone(ent._.wikilink)

        text = 'Is Arctic wolf an animal in ocean arctic?'
        doc = self.nlp(text)
        self.assertEqual(str(doc.ents[0]), 'Arctic')
        self.assertEqual(str(doc.ents[0].label_), 'OCEAN')
        self.assertEqual(str(doc.ents[1]), 'ocean arctic')
        self.assertEqual(str(doc.ents[1].label_), 'OCEAN')
        for ent in doc.ents:
            self.assertIsNotNone(ent._.wikilink)

    def test_left_priority(self):
        text = 'Is Great Slave Lake Ontario related?'
        doc = self.nlp(text)
        self.assertEqual(str(doc.ents[0]), 'Great Slave Lake')
        self.assertEqual(str(doc.ents[0].label_), 'LAKE')
        self.assertEqual(len(doc.ents), 1)
        for ent in doc.ents:
            self.assertIsNotNone(ent._.wikilink)

        text = 'Is Arctic Lake Ontario related?'
        doc = self.nlp(text)
        self.assertEqual(str(doc.ents[0]), 'Arctic Lake')
        self.assertEqual(str(doc.ents[0].label_), 'LAKE')
        self.assertEqual(len(doc.ents), 1)
        for ent in doc.ents:
            self.assertIsNotNone(ent._.wikilink)

    def test_common_names(self):
        doc = self.nlp('Is Nile an actual river?')
        self.assertNotEqual(str(doc.ents[0]), 'Is')
        for ent in doc.ents:
            self.assertIsNotNone(ent._.wikilink)

        doc = self.nlp('There is an actual river named Is river or is river or IS river.')
        self.assertEqual(str(doc.ents[0]), 'Is river')
        self.assertEqual(str(doc.ents[0].label_), 'RIVER')
        self.assertEqual(str(doc.ents[1]), 'is river')
        self.assertEqual(str(doc.ents[1].label_), 'RIVER')
        self.assertEqual(str(doc.ents[2]), 'IS river')
        self.assertEqual(str(doc.ents[2].label_), 'RIVER')
        for ent in doc.ents:
            self.assertIsNotNone(ent._.wikilink)

    def test_issue20(self):
        doc = self.nlp('The Mackenzie River flows from the Great Slave Lake into the Arctic Ocean.')
        self.assertEqual(str(doc.ents[1]), 'Great Slave Lake')
        self.assertEqual(str(doc.ents[1].label_), 'LAKE')
        doc = self.nlp('The Mackenzie River flows from the great slave lake into the Arctic Ocean.')
        self.assertEqual(str(doc.ents[1]), 'great slave lake')
        self.assertEqual(str(doc.ents[1].label_), 'LAKE')

        for ent in doc.ents:
            self.assertIsNotNone(ent._.wikilink)

if __name__ == '__main__':
    unittest.main()
