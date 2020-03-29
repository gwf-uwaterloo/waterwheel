import unittest
import spacy
from waterwheel import WaterWheel

class TestWaterWheel(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.nlp = spacy.load('en_core_web_sm')
        self.ww = WaterWheel(self.nlp)
        self.nlp.add_pipe(self.ww)

    def test_pipeline_added(self):
        self.assertEqual(self.nlp.pipe_names[-1], 'waterwheel')

    def test_proper_nouns(self):
        text = '''The amazon, arctic, ontario are something 
        and the AMAZON, ARCTIC, ONTARIO are something.
        '''
        doc = self.nlp(text)
        self.assertEqual(len(doc.ents), 0)

        text = 'The Amazon, Arctic, Ontario are something.'
        doc = self.nlp(text)
        self.assertEqual(str(doc.ents[0]), 'Amazon')
        self.assertEqual(str(doc.ents[0].label_), 'RIVER')
        self.assertEqual(str(doc.ents[1]), 'Arctic')
        self.assertEqual(str(doc.ents[1].label_), 'OCEAN')
        self.assertEqual(str(doc.ents[2]), 'Ontario')
        self.assertEqual(str(doc.ents[2].label_), 'CANADIAN_PROVINCE')
        for ent in doc.ents:
            self.assertIsNotNone(ent._.wikilink)

    def test_common_uncommon_overlap(self):
        text = '''The River Cherwell is a major tributary 
        of the River Thames in central England.
        '''
        doc = self.nlp(text)
        self.assertEqual(str(doc.ents[0]), 'River Cherwell')
        self.assertEqual(str(doc.ents[0].label_), 'RIVER')
        self.assertEqual(str(doc.ents[1]), 'River Thames')
        self.assertEqual(str(doc.ents[1].label_), 'RIVER')
        for ent in doc.ents:
            self.assertIsNotNone(ent._.wikilink)
        text = '''The Lake Ontario is surely awesome and 
        so is river Thames.
        '''
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
        Mackenzie and Nelson-Churchill River Basins;
        Arctic-Indian Oceans and Ontario-Alberta provinces.
        '''
        doc = self.nlp(text)

        self.assertEqual(str(doc.ents[0]), 'Mississippi')
        self.assertEqual(str(doc.ents[0].label_), 'RIVER')
        self.assertEqual(str(doc.ents[1]), 'Missouri Rivers')
        self.assertEqual(str(doc.ents[1].label_), 'RIVER')
        self.assertEqual(str(doc.ents[2]), 'Mackenzie')
        self.assertEqual(str(doc.ents[2].label_), 'RIVER')
        self.assertEqual(str(doc.ents[3]), 'Nelson')
        self.assertEqual(str(doc.ents[3].label_), 'RIVER')
        self.assertEqual(str(doc.ents[4]), 'Churchill River')
        self.assertEqual(str(doc.ents[4].label_), 'RIVER')
        self.assertEqual(str(doc.ents[5]), 'Arctic')
        self.assertEqual(str(doc.ents[5].label_), 'OCEAN')
        self.assertEqual(str(doc.ents[6]), 'Indian Oceans')
        self.assertEqual(str(doc.ents[6].label_), 'OCEAN')
        self.assertEqual(str(doc.ents[7]), 'Ontario')
        self.assertEqual(str(doc.ents[7].label_), 'CANADIAN_PROVINCE')
        self.assertEqual(str(doc.ents[8]), 'Alberta')
        self.assertEqual(str(doc.ents[8].label_), 'CANADIAN_PROVINCE')

        for ent in doc.ents:
            self.assertIsNotNone(ent._.wikilink)

    def test_conjunctions(self):
        text = '''When a second fault line, the Saint Lawrence rift,
        formed approximately 570 million years ago,[15] the basis for
        Lakes Ontario and Erie were created, along with what would become
         the Saint Lawrence River. And the Mississippi and Missouri Rivers.
         Arctic and Indian Oceans and Ontario and Alberta provinces.
        '''
        doc = self.nlp(text)

        self.assertEqual(str(doc.ents[0]), 'Saint Lawrence')
        self.assertEqual(str(doc.ents[0].label_), 'RIVER')
        self.assertEqual(str(doc.ents[1]), 'Lakes Ontario')
        self.assertEqual(str(doc.ents[1].label_), 'LAKE')
        self.assertEqual(str(doc.ents[2]), 'Erie')
        self.assertEqual(str(doc.ents[2].label_), 'LAKE')
        self.assertEqual(str(doc.ents[3]), 'Saint Lawrence River')
        self.assertEqual(str(doc.ents[3].label_), 'RIVER')
        self.assertEqual(str(doc.ents[4]), 'Mississippi')
        self.assertEqual(str(doc.ents[4].label_), 'RIVER')
        self.assertEqual(str(doc.ents[5]), 'Missouri Rivers')
        self.assertEqual(str(doc.ents[5].label_), 'RIVER')
        self.assertEqual(str(doc.ents[6]), 'Arctic')
        self.assertEqual(str(doc.ents[6].label_), 'OCEAN')
        self.assertEqual(str(doc.ents[7]), 'Indian Oceans')
        self.assertEqual(str(doc.ents[7].label_), 'OCEAN')
        self.assertEqual(str(doc.ents[8]), 'Ontario')
        self.assertEqual(str(doc.ents[8].label_), 'CANADIAN_PROVINCE')
        self.assertEqual(str(doc.ents[9]), 'Alberta')
        self.assertEqual(str(doc.ents[9].label_), 'CANADIAN_PROVINCE')

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

        text = 'Is Ontario a province or a lake?'
        doc = self.nlp(text)
        self.assertEqual(str(doc.ents[0]), 'Ontario')
        self.assertEqual(str(doc.ents[0].label_), 'CANADIAN_PROVINCE')
        for ent in doc.ents:
            self.assertIsNotNone(ent._.wikilink)

        text = 'Is Lake Ontario a province or a lake?'
        doc = self.nlp(text)
        self.assertEqual(str(doc.ents[0]), 'Lake Ontario')
        self.assertEqual(str(doc.ents[0].label_), 'LAKE')
        for ent in doc.ents:
            self.assertIsNotNone(ent._.wikilink)

        text = 'Is Arctic an ocean or lake?'
        doc = self.nlp(text)
        self.assertEqual(str(doc.ents[0]), 'Arctic')
        self.assertEqual(str(doc.ents[0].label_), 'OCEAN')
        for ent in doc.ents:
            self.assertIsNotNone(ent._.wikilink)
        
        text = 'Is Arctic lake an ocean or lake?'
        doc = self.nlp(text)
        self.assertEqual(str(doc.ents[0]), 'Arctic lake')
        self.assertEqual(str(doc.ents[0].label_), 'LAKE')
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
    
    def test_province_abbreviations(self):
        doc = self.nlp('My address is something, something, on or On or oN.')
        self.assertEqual(len(doc.ents), 0)
        doc = self.nlp('Some address is university avenue, ON, canada.')
        self.assertEqual(str(doc.ents[0]), 'ON')
        self.assertEqual(str(doc.ents[0].label_), 'CANADIAN_PROVINCE')

        for ent in doc.ents:
            self.assertIsNotNone(ent._.wikilink)
    
    def test_nonalphabetical_matches(self):
        doc = self.nlp('There is no waterbody in this (), ( ) sentence.')
        self.assertEqual(len(doc.ents), 0)

if __name__ == '__main__':
    unittest.main()
