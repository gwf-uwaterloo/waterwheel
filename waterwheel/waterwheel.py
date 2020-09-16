import re
import os
import srsly
from pathlib import Path
from typing import Dict, List
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
            The shared nlp object to pass the vocab to the matchers
            and process phrase patterns.
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
        self._qualifiers = defaultdict(lambda: [])
        # if a match without a qualifier can be of multiple potential types then
        # this is used to set priority.
        self._pq = {
            label: iter for iter, label in enumerate([
                'OCEAN', 'COUNTRY', 'CANADIAN_PROVINCE', 'RIVER',
                'US_STATE', 'LAKE', 'MOUNTAIN', 'DRAINAGEBASIN', 
                'WATERCOURSE', 'WATER_BODY', 'CHINESE_PROVINCE'
        ])}
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

        if self.overwrite:
            doc.ents = []
        matches = list(self.phrase_matcher(doc))
        matches = sorted([(start, end, self._ent_ids[m_id]) for m_id, start, end in matches if start != end])
        match_dicts = []
        # stick together qualifiers with matcher wherever possible.
        for start, end, label in matches:
            if any(t.ent_type for t in doc[start:end]) and not self.overwrite:
                continue
            match_str = str(doc[start:end])
            is_non_alphabetical = re.search('^[^a-zA-Z\d]+$', match_str) is not None
            if is_non_alphabetical:
                continue
            is_all_caps = re.search('^[\sA-Z]+$', match_str) is not None
            is_all_lower =  re.search('^[\sa-z]+$', match_str) is not None
            is_improper_noun = is_all_caps or is_all_lower
            is_stop_word = match_str.lower() in self._stop_words
            q_before = str(doc[start-1:start]).lower() in self._qualifiers[label]
            q_after = str(doc[end:end+1]).lower() in self._qualifiers[label]
            end += q_after
            # precedence given to proceeding qualifier over preceding one.
            start -= q_before and not q_after
            # prelimenary filters
            if not (q_before or q_after):
                # skip unqualified/improper/stop_words
                # unless it is province abbreviation
                if label in ['US_STATE', 'CANADIAN_PROVINCE']:
                    # all abbreviations are 4 chars or less.
                    if len(match_str) < 5:
                        if not is_all_caps:
                            continue
                    elif is_stop_word or is_improper_noun:
                        continue
                    #quick filter to filter out CT Scan to avoid ambiguity
                    if (match_str == 'CT' and str(doc[end:end+1]).lower() == 'scan'):
                        continue
                elif is_stop_word or is_improper_noun:
                    continue
            match_dicts.append({
                'match_str': match_str,
                'start': start, 
                'end': end, 
                'label': label,
                'is_qualified': q_before or q_after,
                'is_uncommon': not is_stop_word,
                'is_proper_noun': not is_improper_noun,
                'length': end - start,
                'priority': self._pq[label]
            })
        match_dicts = sorted(match_dicts, key = lambda x: x['start'])
        current_range = set()
        match_groups = []
        # arrange the matches in overlapping groups.
        for match in match_dicts:
            if match['start'] in current_range or match['end'] - 1 in current_range:
                current_range.update(range(match['start'], match['end']))
            else:
                current_range = set(range(match['start'], match['end']))
                match_groups.append([])
            match_groups[-1].append(match)
        # filter out best matches in each group.
        final_matches = self._filter_matches(match_groups)
        # set wikilinks to final matches.
        for match in final_matches:
            span = Span(doc, match['start'], match['end'], label = match['label'])
            span._.set(
                'wikilink',
                'https://www.wikidata.org/wiki/' + self._wikidata[match['label']].get(match['match_str'].lower())
            )
            try:
                doc.ents = list(doc.ents) + [span]
            except ValueError:
                # skip overlapping or intersecting matches.
                continue
        return doc
        
    
    def __len__(self):
        """The number of all water_bodies."""
        n_phrases = 0
        for key in self._doc_bins:
            n_phrases += len(self._doc_bins[key])
        return n_phrases
    
    def _filter_matches(self, match_groups: List):
        """Filter matches according to following procedure:
        In case of overlap, give precedence to uncommon words over common words.
            Example: In 'The Lake Ontario', 'Lake Ontario' is chosen over 'The Lake'.
        In case of multiple potential match types, decide according to qualifier.
            Example: In 'Mississippi River', type 'RIVER' is set over 'LAKE'.
        In case of overlap, give precedence to maximal span.
            Example: In 'Nile River', 'Nile River' is matched over just 'Nile'.
        In case of multiple potential match types and no qualifier,
            decicde according to default type priority.
            Example: In 'Mississipi is something', type 'RIVER' is set over 'LAKE'.
        In case of overlap, give precedence to match with proper noun.
            Example: In 'superior lake Ontario', 'lake Ontario' is chosen over 
                'superior lake'.
        In case of overlap, consume match from left to right and ignore leftovers.
            Example: In 'Great Slave Lake Ontario', 'Great Slave Lake' is chosen
                and 'Lake Ontario' is ignored/skipped.
        Parameters
        ----------
        match_groups : List
            List of matches in same overlapping regions.
        
        Returns
        -------
        final_matches : List
            List of non overlapping matches filtered by the procedure.
        """
        final_matches = []
        seen = set()
        for group in match_groups:
            ordered_lists = [[i for i in range(len(group))]]
            new_ordered_lists = []

            for lst in ordered_lists:
                new_ordered_lists.extend(self._separator(group, lst, 'is_uncommon'))
            ordered_lists = new_ordered_lists
            new_ordered_lists = []

            for lst in ordered_lists:
                new_ordered_lists.extend(self._separator(group, lst, 'is_qualified'))
            ordered_lists = new_ordered_lists
            new_ordered_lists = []

            for lst in ordered_lists:
                new_ordered_lists.append(self._sorter(group, lst, 'length', reverse = True))
            ordered_lists = new_ordered_lists
            new_ordered_lists = []

            for lst in ordered_lists:
                new_ordered_lists.append(self._sorter(group, lst, 'priority'))
            ordered_lists = new_ordered_lists
            new_ordered_lists = []

            for lst in ordered_lists:
                new_ordered_lists.extend(self._separator(group, lst, 'is_proper_noun'))
            ordered_lists = new_ordered_lists
            new_ordered_lists = []

            for lst in ordered_lists:
                new_ordered_lists.append(self._sorter(group, lst, 'start'))
            ordered_lists = new_ordered_lists
            new_ordered_lists = []
            
            for lst in ordered_lists:
                for index in lst:
                    if group[index]['start'] in seen and group[index]['end'] - 1 in seen:
                        continue
                    seen.update(range(group[index]['start'], group[index]['end']))
                    final_matches.append(group[index])
        return final_matches
    
    def _separator(self, group: List, lst: List, attr: str):
        """Separates a list into two lists according to
        bool value of match attr in the list.
        
        Parameters
        ----------
        group : List
            A list of overlapping matches.
        lst : List
            A ordering of matches in group.
        attr : str
            Attribute to check for in matches.
        
        Returns
        -------
        ret_list : List
            A list containing:
            1) A list of matches with attr value True.
            2) A list of matches with attr value False.
        """
        list_a = [i for i in lst if group[i][attr]]
        list_b = [i for i in lst if not group[i][attr]]
        ret_list = []
        if len(list_a) > 0:
            ret_list.append(list_a)
        if len(list_b) > 0:
            ret_list.append(list_b)
        return [list_a, list_b]
    
    def _sorter(self, group: List, lst: List, attr: str, reverse: bool = False):
        """Separates a list into two lists according to
        bool value of match attr in the list.
        
        Parameters
        ----------
        group : List
            A list of overlapping matches.
        lst : List
            A ordering of matches in group.
        attr : str
            Attribute to check for in matches.
        reverse : bool, optional
            True for descending sort. 
            False (by default) for ascending sort.
        
        Returns
        -------
        ret_list : List
            A list sorted according attr value.
        """
        return sorted(lst, key = lambda x: group[x][attr], reverse = reverse)

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
                self._qualifiers[label] = [label.lower(), label.lower()+'s']
            self._qualifiers['MOUNTAIN'].extend(['mount', 'mounts', 'mt.'])
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
