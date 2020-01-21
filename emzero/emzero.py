#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    author: Noémi Vadász
    last update: 2020.01.20.
"""

from collections import defaultdict

PRON_PERSNUM = {('Sing', '1'): 'én',
                ('Sing', '2'): 'te',
                ('Sing', '3'): 'ő/az',
                ('Plur', '1'): 'mi',
                ('Plur', '2'): 'ti',
                ('Plur', '3'): 'ők/azok',
                ('X', 'X'): 'X'}

EMMORPH_NUMBER = {'Sing': 'Sg',
                  'Plur': 'Pl',
                  'X': 'X'}

ARGUMENTS = {'SUBJ', 'OBJ', 'OBL', 'DAT', 'ATT', 'INF', 'LOCY'}
NOMINALS = {'NOUN', 'PROPN', 'ADJ', 'NUM', 'DET', 'PRON'}
VERBS = {'VERB'}
DEFINITE = {'Def', '2'}


class Word:

    def __init__(self, form=None, anas=None, lemma=None, xpostag=None, upos=None, feats=None, tid=None, deprel=None,
                 head=None, sent_nr=None, abs_index=None, deps=None):
        """
            Explicit megadva a feature-öket
        """
        self.form = form  # token
        self.anas = anas  # anas
        self.lemma = lemma  # egyértelműsített lemma
        self.xpostag = xpostag  # emtag
        self.upos = upos  # emmorph2ud
        if isinstance(feats, str):
            feats = dict(feat.split('=', maxsplit=1) for feat in feats.split('|') if feats != '_')
            # feats = self._parse_udfeats(feats)
        self.feats = feats  # emmorph2ud
        self.id = tid  # függőségi elemzéshez id
        self.deprel = deprel  # függőségi él típusa
        self.head = head  # amitől függ az elem
        self.sent_nr = sent_nr  # saját mondatszámláló
        self.abs_index = abs_index  # saját tokenszámláló
        self.deps = deps

    @classmethod
    def inherit_base_features(cls, head):
        """
        feature-ök, amelyeket a zéró elem attól a fejtől örököl
        :return:
        """
        return cls(head.form, head.anas, head.lemma, head.xpostag, head.upos, head.feats, head.id, head.deprel,
                   head.head, head.sent_nr, head.abs_index, head.deps)

    def format(self):
        if len(self.feats) == 0:
            feats = '_'
        elif isinstance(self.feats, dict):
            feats = '|'.join('{0}={1}'.format(feat, val) for feat, val in sorted(self.feats.items(),
                                                                                 key=lambda x: x[0].lower()))
        else:
            feats = self.feats

        formatted_list = [str(i) for i in [self.id, self.form, self.lemma, self.upos, self.xpostag, feats,
                                           self.head, self.deprel, self.deps] if i is not None]
        return formatted_list

    def __str__(self):
        return '\t'.join(self.format())

    def __repr__(self):
        return repr([self.id, self.form, self.lemma, self.upos, self.xpostag, self.feats, self.head, self.deprel,
                     self.deps])


class EmZero:
    def __init__(self, source_fields=None, target_fields=None):
        # Custom code goes here
        self._abs_counter = 0
        self._counter = 0

        # Field names for xtsv (the code below is mandatory for an xtsv module)
        if source_fields is None:
            source_fields = set()

        if target_fields is None:
            target_fields = []

        self.source_fields = source_fields
        self.target_fields = target_fields

    @staticmethod
    def prepare_fields(field_names):
        return [field_names['id'], field_names['form'], field_names['lemma'], field_names['upos'],
                field_names['xpostag'], field_names['feats'], field_names['head'], field_names['deprel']]

    @staticmethod
    def _pro_calc_features(head, role):
        """
        a droppolt névmás jegyeit nyeri ki a fejből (annak UD jegyeiből)
        :param head:
        :param role:
        :return:
        """

        pro = Word(tid=head.id + '.' + role,
                   sent_nr=head.sent_nr,
                   abs_index=head.abs_index,
                   deprel=role,
                   head=head.id, **{'form': 'DROP', 'upos': 'PRON', 'feats': {'PronType': 'Prs'}})

        if role == 'OBJ':
            pro.feats['Case'] = 'Acc'
            pro.feats['Number'] = 'Sing'
            if head.feats['Definite'] == '2':
                pro.feats['Person'] = '2'
            else:
                pro.feats['Person'] = '3'

        elif role == 'SUBJ':
            pro.feats['Case'] = 'Nom'
            if 'VerbForm' in head.feats:
                if head.feats['VerbForm'] == 'Fin':
                    pro.feats['Person'] = head.feats['Person']
                    pro.feats['Number'] = head.feats['Number']

                elif head.feats['VerbForm'] == 'Inf':
                    if 'Person' in head.feats:
                        pro.feats['Person'] = head.feats['Person']
                        pro.feats['Number'] = head.feats['Number']
                    else:
                        pro.feats['Person'] = 'X'
                        pro.feats['Number'] = 'X'

        elif role == 'ATT':
            pro.feats['Case'] = 'Gen'
            pro.feats['Person'] = head.feats['Person[psor]']
            pro.feats['Number'] = head.feats['Number[psor]']
        else:
            exit(1)

        pro.xpostag = '[/N|Pro][{0}{1}][{2}]'.format(pro.feats['Person'], EMMORPH_NUMBER[pro.feats['Number']],
                                                     pro.feats['Case'])
        pro.lemma = PRON_PERSNUM[(pro.feats['Number'], pro.feats['Person'])]
        pro.anas = '[]'

        return pro

    def process_sentence(self, inp_sent, field_indices):

        self._counter += 1
        sent = []
        sent_dict = defaultdict(list)
        verbs = {}
        possessum_with_possessor = set()
        possessum = {}

        for tok in inp_sent:
            self._abs_counter += 1
            token = Word(tid=tok[field_indices[0]], form=tok[field_indices[1]], lemma=tok[field_indices[2]],
                         upos=tok[field_indices[3]], xpostag=tok[field_indices[4]], feats=tok[field_indices[5]],
                         head=tok[field_indices[6]], deprel=tok[field_indices[7]],
                         sent_nr=str(self._counter), abs_index=str(self._abs_counter))
            sent.append(token)
            if token.deprel in ARGUMENTS:
                sent_dict[token.head].append(token)
            if token.upos in VERBS:
                verbs[token.id] = token
            if token.deprel == 'ATT' and token.upos in NOMINALS:
                possessum_with_possessor.add(token.head)
            if 'Number[psor]' in token.feats:
                possessum[token] = token.head

        zeros = defaultdict(list)
        for verb_id, verb in verbs.items():
            subj = False
            obj = False
            inf = False
            for tok in sent_dict[verb_id]:
                subj |= tok.deprel == 'SUBJ'
                obj |= tok.deprel == 'OBJ'
                inf |= tok.deprel == 'INF'
            if not subj:
                zeros[verb_id].append(self._pro_calc_features(verb, 'SUBJ'))
            if not obj and 'Definite' in verb.feats and verb.feats['Definite'] in DEFINITE and not inf:
                zeros[verb_id].append(self._pro_calc_features(verb, 'SUBJ'))

        for birtok, verb_id in possessum.items():
            if verb_id in verbs and birtok.id not in possessum_with_possessor:
                zeros[birtok.id].append(
                    self._pro_calc_features(birtok, 'ATT'))

        for token in sent:
            yield token.format()
            for zero in zeros[token.id]:
                yield zero.format()
