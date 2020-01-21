#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    author: Noémi Vadász
    last update: 2020.01.21.
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


def parse_feats(feats):
    return dict(feat.split('=', maxsplit=1) for feat in feats.split('|') if feats != '_')


def format_word(word, ind_to_names):
    if isinstance(word['feats'], dict):
        word['feats'] = '|'.join('{0}={1}'.format(feat, val) for feat, val in sorted(word['feats'].items(),
                                                                                     key=lambda x: x[0].lower()))
    else:
        word['feats'] = '_'

    return [word.get(i, '_') for i in ind_to_names.keys()]  # Place _ to unknown fields


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
        return {k: v for k, v in field_names.items() if isinstance(k, str)}, field_names['id']

    @staticmethod
    def _pro_calc_features(head, role):
        """
        a droppolt névmás jegyeit nyeri ki a fejből (annak UD jegyeiből)
        :param head:
        :param role:
        :return:
        """

        pro = {'id': head['id'] + '.' + role, 'sent_nr': head['sent_nr'], 'abs_index': head['abs_index'],
               'deprel': role, 'head': head['id'], 'form': 'DROP', 'upos': 'PRON', 'feats': {'PronType': 'Prs'}}

        if role == 'OBJ':
            pro['feats']['Case'] = 'Acc'
            pro['feats']['Number'] = 'Sing'
            if head['feats']['Definite'] == '2':
                pro['feats']['Person'] = '2'
            else:
                pro['feats']['Person'] = '3'

        elif role == 'SUBJ':
            pro['feats']['Case'] = 'Nom'
            if 'VerbForm' in head['feats']:
                if head['feats']['VerbForm'] == 'Fin':
                    pro['feats']['Person'] = head['feats']['Person']
                    pro['feats']['Number'] = head['feats']['Number']

                elif head['feats']['VerbForm'] == 'Inf':
                    if 'Person' in head['feats']:
                        pro['feats']['Person'] = head['feats']['Person']
                        pro['feats']['Number'] = head['feats']['Number']
                    else:
                        pro['feats']['Person'] = 'X'
                        pro['feats']['Number'] = 'X'

        elif role == 'ATT':
            pro['id'] = pro['id'][:-3] + 'POSS'
            pro['feats']['Case'] = 'Gen'
            pro['feats']['Person'] = head['feats']['Person[psor]']
            pro['feats']['Number'] = head['feats']['Number[psor]']
        else:
            exit(1)

        pro['xpostag'] = '[/N|Pro][{0}{1}][{2}]'.format(pro['feats']['Person'], EMMORPH_NUMBER[pro['feats']['Number']],
                                                        pro['feats']['Case'])
        pro['lemma'] = PRON_PERSNUM[(pro['feats']['Number'], pro['feats']['Person'])]
        pro['anas'] = '[]'

        return pro

    def process_sentence(self, inp_sent, field_names_and_id_ind):
        field_names, id_field_ind = field_names_and_id_ind

        self._counter += 1
        sent_dict = defaultdict(list)
        verbs = {}
        possessum_with_possessor = set()
        possessum = {}

        for token_nr, tok in enumerate(inp_sent):
            self._abs_counter += 1
            token = {k: tok[v] for k, v in field_names.items()}
            token['sent_nr'] = self._counter
            token['abs_index'] = self._abs_counter
            token['feats'] = parse_feats(token['feats'])

            if token['deprel'] in ARGUMENTS:
                sent_dict[token['head']].append(token)
            if token['upos'] in VERBS:
                verbs[token['id']] = token
            if token['deprel'] == 'ATT' and token['upos'] in NOMINALS:
                possessum_with_possessor.add(token['head'])
            # Posessum is always placed after the posesssor  # TODO: Ez igaz?
            if 'Number[psor]' in token['feats'] and token['id'] not in possessum_with_possessor:
                possessum[token['head']] = token  # verb (id) -> candidate possessums

        zeros = defaultdict(list)
        for verb_id, verb in verbs.items():
            subj = False
            obj = False
            inf = False
            for tok in sent_dict[verb_id]:
                subj |= tok['deprel'] == 'SUBJ'
                obj |= tok['deprel'] == 'OBJ'
                inf |= tok['deprel'] == 'INF'
            if not subj:
                zeros[verb_id].append(self._pro_calc_features(verb, 'SUBJ'))
            if not obj and 'Definite' in verb['feats'] and verb['feats']['Definite'] in DEFINITE and not inf:
                zeros[verb_id].append(self._pro_calc_features(verb, 'SUBJ'))

        for verb_id, token in possessum.items():
            if verb_id in verbs and token['id']:
                zeros[token['id']].append(self._pro_calc_features(token, 'ATT'))
                break

        for token in inp_sent:  # Output the original tokens
            yield token
            for zero in zeros[token[id_field_ind]]:  # Insert extra tokens when needed
                yield format_word(zero, field_names)
