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
        self.assertEqual(str(doc.ents[4]), 'Churchill')
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
        self.assertEqual(str(doc.ents[1]), 'Ontario')
        self.assertEqual(str(doc.ents[2]), 'Erie')
        self.assertEqual(str(doc.ents[3]), 'Saint Lawrence')
        self.assertEqual(str(doc.ents[4]), 'Mississippi')
        self.assertEqual(str(doc.ents[5]), 'Missouri')

        for ent in doc.ents:
            self.assertIsNotNone(ent._.wikilink)

    def test_common_names(self):
        doc = self.nlp('Is Nile an actual river?')
        self.assertNotEqual(str(doc.ents[0]), 'Is')

        doc = self.nlp('There is an actual river named Is river or is river or IS river.')
        self.assertEqual(str(doc.ents[0]), 'Is')
        self.assertEqual(str(doc.ents[1]), 'is')
        self.assertEqual(str(doc.ents[2]), 'IS')
        for ent in doc.ents:
            self.assertIsNotNone(ent._.wikilink)
    
    def test_issue20(self):
        doc = self.nlp('The Mackenzie River flows from the Great Slave Lake into the Arctic Ocean.')
        self.assertEqual(str(doc.ents[1]), 'Great Slave')
        self.assertEqual(str(doc.ents[1].label_), 'LAKE')
        doc = self.nlp('The Mackenzie River flows from the great slave lake into the Arctic Ocean.')
        self.assertEqual(str(doc.ents[1]), 'great slave')
        self.assertEqual(str(doc.ents[1].label_), 'LAKE')

        for ent in doc.ents:
            self.assertIsNotNone(ent._.wikilink)

if __name__ == '__main__':
    unittest.main()