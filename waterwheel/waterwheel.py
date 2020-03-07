import re
import os
import srsly
from pathlib import Path
from typing import Dict
from collections import defaultdict, OrderedDict

from spacy.util import ensure_path
from spacy.language import Language
from spacy.pipeline import EntityRuler
from spacy.tokens import Doc, Span, DocBin

DOC_BIN_FILE = Path(os.path.dirname(os.path.realpath(__file__))) / 'resources/doc_bins.msgpack'

class WaterWheel(EntityRuler):
    """WATERWHEEL (WATERloo Water and Hydrologic Entity Extractor and Linker)
    is a spaCy  pipeline component that detects rivers, lakes, and other 
    hydrologic entities, and links these entities to Wikidata. The
    component is typically added to the pipeline using `nlp.add_pipe`
    """

    name = 'waterwheel'

    def __init__(self, nlp: Language, overwrite_ents: bool = True):
        """Initialize the class.
        
        Parameters
        ----------
        nlp : Language
            spacy nlp object
        overwrite_ents : bool, optional
            If True then doc.ents from preceeding pipeline components
            are removed/overwritten. Otherwise, previous doc.ents are kept
            intact.
        """
        super().__init__(nlp, phrase_matcher_attr='LOWER', overwrite_ents=overwrite_ents)
        self._ent_ids = defaultdict(lambda: "WATER_BODY")
        self._stop_words = set()
        self._wikidata = {}
        self._doc_bins = {}
        self.from_disk(DOC_BIN_FILE)
        Span.set_extension('wikilink', default=None, force=True)

    def __call__(self, doc: Doc):
        """Find matches in document and add them as entities
        
        Parameters
        ----------
        doc : Doc
            The Doc object in the pipeline.
        
        Returns
        -------
        doc : Doc
            The Doc with added entities, if available.
        """

        matches = list(self.phrase_matcher(doc))
        matches = set(
            [(m_id, start, end) for m_id, start, end in matches if start != end]
        )
        get_sort_key = lambda m: (m[2] - m[1], m[1])
        matches = sorted(matches, key=get_sort_key, reverse=True)
        entities = [] if self.overwrite else list(doc.ents)
        new_entities = []
        seen_tokens = set()
        for match_id, start, end in matches:
            if any(t.ent_type for t in doc[start:end]) and not self.overwrite:
                continue
            # check for end - 1 here because boundaries are inclusive
            if start in seen_tokens or end - 1 in seen_tokens:
                continue
            label = self._ent_ids[match_id]
            span = Span(doc, start, end, label=label)
            # custom checks
            match_str = str(span)
            if match_str.lower() in self._stop_words:
                if str(doc[end:end+1]).lower() not in ['river', 'lake']:
                    continue
            elif re.search('^[\sA-Z]+$', match_str) or re.search('^[\sa-z]+$', match_str):
                # skip mathces that are ALL_CAPS or all_small.
                continue
            try:
                doc.ents = new_entities + [span]
            except ValueError:
                # skip overlapping or intersecting matches.
                continue
            
            new_entities.append(span)
            entities = [
                e for e in entities if not (e.start < end and e.end > start)
            ]
            seen_tokens.update(range(start, end))
            
            # TODO maybe explore Entity Linking here. 
            if label in self._wikidata and match_str.lower() in self._wikidata[label]:
                span._.set(
                    'wikilink',
                    'https://www.wikidata.org/wiki/' + self._wikidata[label][match_str.lower()]
                )
            
        doc.ents = entities + new_entities
        return doc
    
    def __len__(self):
        """The number of all water_bodies."""
        n_phrases = 0
        for key in self._doc_bins:
            n_phrases += len(self._doc_bins[key])
        return n_phrases

    def to_bytes(self, **kwargs):
        """Serialize waterwheel data to a bytestring.
        
        Returns
        -------
        serial : bytes
            The serialized bytes data.
        """

        doc_bins_bytes = {key: bin.to_bytes() for key, bin in self._doc_bins.items()}
        serial = OrderedDict(
            (
                ('stop_words', list(self._stop_words)),
                ('vocab', self._ent_ids),
                ('wikidata', self._wikidata),
                ('doc_bins', doc_bins_bytes),
            )
        )
        return srsly.msgpack_dumps(serial)
    
    def from_bytes(self, serial: bytes, **kwargs):
        """Load waterwheel from a bytestring.

        Parameters
        ----------
        serial : bytes
            The serialized bytes data.
        
        Returns
        -------
        self : WaterWheel
            The loaded WaterWheel object.
        """

        cfg = srsly.msgpack_loads(serial)
        if isinstance(cfg, dict):
            vocab = cfg.get('vocab', {})
            for hash, label in vocab.items():
                self._ent_ids[int(hash)] = label
            self._stop_words = cfg.get('stop_words', [])
            self._stop_words = set(self._stop_words)
            self._wikidata = cfg.get('wikidata', {})

            doc_bins_bytes = cfg.get('doc_bins', {})
            self._doc_bins = {key: DocBin().from_bytes(value) for key, value in doc_bins_bytes.items()}
            phrases_bin = {key: list(bin.get_docs(self.nlp.vocab)) for key, bin in self._doc_bins.items()}
            for key, phrases in phrases_bin.items():
                self.phrase_matcher.add(key.upper(), phrases)
        return self

    def to_disk(self, path, **kwargs):
        """Serialize waterwheel data to a file.
        
        Parameters
        ----------
        path : Path
            path to file.
        """

        path = ensure_path(path)
        serial = self.to_bytes()
        srsly.write_msgpack(path, serial)
        
    def from_disk(self, path, **kwargs):
        """Load waterwheel from a file. Expects file to contain
        a bytestring of the following dict format:
        {
            'stop_words': {},
            'vocab': {},
            'wikidata': {},
            'doc_bins': doc_bins_bytes,
        }

        Parameters
        ----------
        path : Path
            path to the serialized file.
        
        Returns
        -------
        self : WaterWheel
            The loaded WaterWheel object.
        """

        path = ensure_path(path)
        with open(path, 'rb') as file:
            serial = file.read()
        self.from_bytes(serial)
        return self