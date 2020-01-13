#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    author: Noémi Vadász
    last update: 2020.01.11.
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

ARGUMENTS = {'SUBJ', 'OBJ', 'OBL', 'DAT', 'POSS', 'INF', 'LOCY'}
NOMINALS = {'NOUN', 'PROPN', 'ADJ', 'NUM', 'DET', 'PRON'}
VERBS = {'VERB'}


class Word:

    def __init__(self, form=None, anas=None, lemma=None, xpostag=None, upos=None, feats=None, tid=None, deprel=None,
                 head=None, sent_nr=None, abs_index=None, deps=None, misc=None):
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
        self.misc = misc

    @classmethod
    def inherit_base_features(cls, head):
        """
        feature-ök, amelyeket a zéró elem attól a fejtől örököl
        :return:
        """
        return cls(head.form, head.anas, head.lemma, head.xpostag, head.upos, head.feats, head.id, head.deprel,
                   head.head, head.sent_nr, head.abs_index, head.deps, head.misc)

    def format(self):
        if len(self.feats) == 0:
            feats = '_'
        elif isinstance(self.feats, dict):
            feats = '|'.join('{0}={1}'.format(feat, val) for feat, val in sorted(self.feats.items(),
                                                                                 key=lambda x: x[0].lower()))
        else:
            feats = self.feats

        formatted_list = [str(i) for i in [self.id, self.form, self.lemma, self.upos, self.xpostag, feats,
                                           self.head, self.deprel, self.deps, self.misc] if i is not None]
        return formatted_list

    def __str__(self):
        return '\t'.join(self.format())

    def __repr__(self):
        return repr([self.id, self.form, self.lemma, self.upos, self.xpostag, self.feats, self.head, self.deprel,
                     self.deps, self.misc])


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
    def _pro_default_features(deprel):
        """
        a droppolt nevmas alapjegyeit allitja be
        :param deprel: a droppolt actor adatszerkezete (deprel)
        :return:
        """

        ret = {'form': 'DROP', 'upos': 'PRON', 'feats': dict()}
        if deprel == 'SUBJ':
            ret['feats']['Case'] = 'Nom'
        elif deprel == 'OBJ':
            ret['feats']['Case'] = 'Acc'
        elif deprel == 'POSS':
            ret['feats']['Case'] = 'Gen'
        ret['feats']['PronType'] = 'Prs'

        return ret

    def _pro_calc_features(self, head, role):
        """
        a droppolt névmás jegyeit nyeri ki a fejből (annak UD jegyeiből)
        :param head:
        :param role:
        :return:
        """

        pro = Word(tid=head.id + '.' + role,  # TODO ha alany és tárgy is van, a tárgy .2 legyen (az alany pedig .1)
                   sent_nr=head.sent_nr,
                   abs_index=head.abs_index,
                   deprel=role,
                   head=head.id, **self._pro_default_features(role))

        if role == 'OBJ':
            pro.feats['Number'] = 'Sing'

            if head.feats['Definite'] == '2':
                pro.feats['Person'] = '2'
            else:
                pro.feats['Person'] = '3'

        elif role == 'SUBJ':
            if 'VerbForm' in head.feats:
                if head.feats['VerbForm'] == 'Fin':
                    pro.feats['Person'] = head.feats['Person']
                    pro.feats['Number'] = head.feats['Number']

                elif head.feats['VerbForm'] == 'Inf':
                    # TODO check INF alanya
                    if 'Person' in head.feats:
                        pro.feats['Person'] = head.feats['Person']
                        pro.feats['Number'] = head.feats['Number']
                    else:
                        pro.feats['Person'] = 'X'
                        pro.feats['Number'] = 'X'

        else:
            pro.feats['Person'] = head.feats['Person[psor]']
            pro.feats['Number'] = head.feats['Number[psor]']

        pro.xpostag = '[/N|Pro][{0}{1}][{2}]'.format(pro.feats['Person'], EMMORPH_NUMBER[pro.feats['Number']],
                                                     pro.feats['Case'])
        pro.lemma = PRON_PERSNUM[(pro.feats['Number'], pro.feats['Person'])]
        pro.anas = '[]'

        return pro

    def process_sentence(self, inp_sent, field_indices):

        self._counter += 1
        sent = []

        for tok in inp_sent:
            self._abs_counter += 1
            token = Word(tid=tok[field_indices[0]], form=tok[field_indices[1]], lemma=tok[field_indices[2]],
                         upos=tok[field_indices[3]], xpostag=tok[field_indices[4]], feats=tok[field_indices[5]],
                         head=tok[field_indices[6]], deprel=tok[field_indices[7]],
                         sent_nr=str(self._counter), abs_index=str(self._abs_counter))
            sent.append(token)

        sent_actors = list()
        deps_dict = defaultdict(list)

        # elmenti az összes függőséget
        # dictet épít: az anyacsomóponthoz a gyerekeit listázza
        for head in sent:
            for dep in sent:
                if dep.head == head.id and head.upos in VERBS and dep.deprel in ARGUMENTS:
                    deps_dict[head].append(dep)

            # TODO miért is kell ez?
            if head.upos in VERBS and head not in deps_dict:
                deps_dict[head].append(head)

        for head in deps_dict:

            verb = Word.inherit_base_features(head)

            actors = defaultdict(list)

            for dep in deps_dict[head]:

                actor = Word.inherit_base_features(dep)

                actor.sent_nr = verb.sent_nr

                # itt megnézi, hogy vannak-e birtokok a mondatban
                if 'Number[psor]' in actor.feats:
                    for ifposs in sent:
                        # van-e birtokos függőségi viszony
                        # TODO ez most a korkorpuszra van hangolva (eredeti tagset: ATT)
                        if ifposs.head == dep.id and ifposs.deprel == 'POSS' and ifposs.upos in NOMINALS:
                            newactor = Word.inherit_base_features(ifposs)

                            actors[verb].append(newactor)

                actors[verb].append(actor)

            sent_actors.append(actors)

        # letrehozza a droppolt alanyokat, targyakat, birtokosokat, majd torli a foloslegeseket
        self._insert_pro(sent_actors)

        # kiirja
        for token in sent:
            yield token.format()
            for actors in sent_actors:
                for verb in actors.keys():
                    for dep in actors[verb]:
                        if dep.abs_index == token.abs_index and dep.form == 'DROP':
                            yield dep.format()

        return sent_actors

    @staticmethod
    def _remove_dropped(head, deps, role):
        """
        kitorli a actors kozul azokat a droppolt alanyokat, targyakat, amikhez van testes
        :param? head:
        :param deps: az aktualis ige vonzatai
        :param role: szerep
        :return:
        """

        if any(actor.head == head and actor.deprel == role and actor.form != 'DROP' for actor in deps):
            deps = [actor for actor in deps if actor.head != head or actor.deprel != role or actor.form != 'DROP']

        return deps

    def _insert_pro(self, actorlist):
        """
        letrehoz droppolt alanyt, targyat
        alanyt: minden igenek
        targyat: csak a definit ragozasu igeknek
        :param
        :return:
        """

        for actors in actorlist:

            for verb in actors.keys():

                subj = self._pro_calc_features(verb, 'SUBJ')
                actors[verb].append(subj)
                actors[verb] = self._remove_dropped(verb.id, actors[verb], 'SUBJ')

                if 'Definite' in verb.feats and verb.feats['Definite'] in {'Def', '2'} \
                        and not any(actor.deprel == 'INF' for actor in actors[verb]):
                    obj = self._pro_calc_features(verb, 'OBJ')
                    actors[verb].append(obj)
                    actors[verb] = self._remove_dropped(verb.id, actors[verb], 'OBJ')

                for actor in actors[verb]:
                    if 'Number[psor]' in actor.feats:
                        poss = self._pro_calc_features(actor, 'POSS')
                        actors[verb].append(poss)
                        actors[verb] = self._remove_dropped(actor.id, actors[verb], 'POSS')
