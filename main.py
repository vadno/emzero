#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    author: Noémi Vadász
    last update: 2020.01.10.
"""

from collections import defaultdict
import sys
import csv

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

    def __init__(self):
        self.form = None  # token
        self.anas = None  # anas
        self.lemma = None  # egyértelműsített lemma
        self.xpostag = None  # emtag
        self.upos = None  # emmorph2ud
        self.feats = None  # emmorph2ud
        self.id = None  # függőségi elemzéshez id
        self.deprel = None  # függőségi él típusa
        self.head = None  # amitől függ az elem
        self.sent_nr = None  # saját mondatszámláló
        self.abs_index = None  # saját tokenszámláló
        self.deps = None
        self.misc = None

    def _print_token(self):
        print(self)

    def __str__(self):
        return '\t'.join(
            [self.id, self.form, self.lemma, self.upos, self.xpostag, self.feats, self.head, self.deprel, self.deps,
             self.misc])

    def __repr__(self):
        return repr([self.id, self.form, self.lemma, self.upos, self.xpostag, self.feats, self.head, self.deprel,
                     self.deps, self.misc])


class EmZero:
    def __init__(self, source_fields=None, target_fields=None):
        # Custom code goes here
        self._actor_list = []

        # Field names for xtsv (the code below is mandatory for an xtsv module)
        if source_fields is None:
            source_fields = set()

        if target_fields is None:
            target_fields = []

        self.source_fields = source_fields
        self.target_fields = target_fields

    @staticmethod
    def _base_features(pro, head):
        """
        feature-ök, amelyeket a zéró elem attól a fejtől örököl
        :param pro: zéró elem
        :param head: fej
        :return:
        """

        for field in vars(head):
            setattr(pro, field, getattr(head, field))

    @staticmethod
    def _parse_udfeats(feats):
        """
        az UD jegyek sztringjét dolgozza fel (| és = mentén)
        :param feats: UD jegyek sztringje
        :return: dictbe rendezett kulcs-érték párok
        """

        featdict = dict()

        if feats != '_':
            for feat in feats.split('|'):
                feat = feat.split('=')
                featdict[feat[0]] = feat[1]

        return featdict

    @staticmethod
    def _pro_default_features(dropped):
        """
        a droppolt nevmas alapjegyeit allitja be
        :param dropped: a droppolt actor adatszerkezete
        :return:
        """

        dropped.form = 'DROP'
        dropped.upos = 'PRON'
        dropped.feats = dict()
        if dropped.deprel == 'SUBJ':
            dropped.feats['Case'] = 'Nom'
        elif dropped.deprel == 'OBJ':
            dropped.feats['Case'] = 'Acc'
        elif dropped.deprel == 'POSS':
            dropped.feats['Case'] = 'Gen'
        dropped.feats['PronType'] = 'Prs'

    def _pro_calc_features(self, head, role):
        """
        a droppolt névmás jegyeit nyeri ki a fejből (annak UD jegyeiből)
        :param head:
        :param role:
        :return:
        """

        pro = Word()
        pro.id = head.id + '.' + role  # TODO ha alany és tárgy is van, a tárgy .2 legyen (az alany pedig .1)
        pro.sent_nr = head.sent_nr
        pro.abs_index = head.abs_index
        pro.deprel = role
        pro.head = head.id
        self._pro_default_features(pro)

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

        pro.xpostag = '[/N|Pro][' + pro.feats['Person'] + EMMORPH_NUMBER[pro.feats['Number']] + '][' + pro.feats[
            'Case'] + ']'
        pro.lemma = PRON_PERSNUM[(pro.feats['Number'], pro.feats['Person'])]
        pro.feats = '|'.join(feat + '=' + pro.feats[feat] for feat in sorted(pro.feats, key=str.lower))
        pro.anas = '[]'

        return pro

    def process_sentence(self, sent):

        sent_actors = list()
        deps_dict = defaultdict(list)

        # elmenti az összes függőséget
        # dictet épít: az anyacsomóponthoz a gyerekeit listázza
        for head in sent:
            for dep in sent:
                if dep.head == head.id:
                    deps_dict[head].append(dep)

            # TODO miért kell ez?
            if head.upos in VERBS and head not in deps_dict:
                deps_dict[head].append(head)

        for head in deps_dict:
            if head.upos in VERBS:

                # TODO egybevonni
                verb = Word()
                self._base_features(verb, head)
                verb.feats = self._parse_udfeats(verb.feats)

                actors = defaultdict(list)
                actors[verb] = []

                for dep in deps_dict[head]:
                    if dep.deprel in ARGUMENTS:

                        # TODO egybevonni
                        actor = Word()
                        self._base_features(actor, dep)
                        actor.feats = self._parse_udfeats(actor.feats)

                        actor.sent_nr = verb.sent_nr

                        # itt megnézi, hogy vannak-e birtokok a mondatban
                        if 'Number[psor]' in actor.feats:
                            for ifposs in sent:
                                # van-e birtokos függőségi viszony
                                # TODO ez most a korkorpuszra van hangolva (eredeti tagset: ATT)
                                if ifposs.head == dep.id and ifposs.deprel == 'POSS' and ifposs.upos in NOMINALS:

                                    newactor = Word()
                                    self._base_features(newactor, ifposs)
                                    newactor.feats = self._parse_udfeats(newactor.feats)

                                    actors[verb].append(newactor)

                        actors[verb].append(actor)

                sent_actors.append(actors)

        self._actor_list.extend(sent_actors)

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

    def insert_pro(self):
        """
        letrehoz droppolt alanyt, targyat
        alanyt: minden igenek
        targyat: csak a definit ragozasu igeknek
        :param
        :return:
        """

        for actors in self._actor_list:
            for verb in actors.keys():

                subj = self._pro_calc_features(verb, 'SUBJ')
                actors[verb].append(subj)

                if 'Definite' in verb.feats and verb.feats['Definite'] in {'Def', '2'}:
                    inf = any(actor.deprel == 'INF' for actor in actors[verb])

                    if not inf:
                        obj = self._pro_calc_features(verb, 'OBJ')
                        actors[verb].append(obj)

                for actor in actors[verb]:
                    if 'Number[psor]' in actor.feats:
                        poss = self._pro_calc_features(actor, 'POSS')
                        actors[verb].append(poss)

                # kitorli a droppolt alanyt, targyat, ha van testes megfeleloje
                actors[verb] = self._remove_dropped(verb.id, actors[verb], 'SUBJ')
                actors[verb] = self._remove_dropped(verb.id, actors[verb], 'OBJ')
                for actor in actors[verb]:
                    actors[verb] = self._remove_dropped(actor.id, actors[verb], 'POSS')

    @staticmethod
    def print_pro(header, token, actors):

        for sent in actors:
            for key, value in sent.items():
                for dep in value:
                    if dep.abs_index == token.abs_index:
                        if dep.form == 'DROP':
                            print('\t'.join(getattr(dep, field) for field in header))

    def print_corpus(self, header, corpus):

        print('\t'.join(field for field in header))

        for sentence in corpus:
            for token in sentence:
                print('\t'.join(getattr(token, field) for field in header))
                self.print_pro(header, token, self._actor_list)
            print('')

    @staticmethod
    def _parse_fields(token, line, header):

        for field in header:
            setattr(token, field, line[header.index(field)])

    def read_file(self):

        reader = csv.reader(iter(sys.stdin.readline, ''), delimiter='\t', quoting=csv.QUOTE_NONE)
        header = next(reader)

        corp = list()

        abs_counter = 0
        counter = 0

        sent = list()

        for line in reader:

            if len(line) > 1:
                abs_counter += 1

                if line:
                    token = Word()
                    self._parse_fields(token, line, header)
                    token.sent_nr = str(counter)
                    token.abs_index = str(abs_counter)

                    sent.append(token)

            else:
                counter += 1
                corp.append(sent)
                sent = list()

        corp.append(sent)

        return header, corp


def main():
    zero = EmZero()

    # beolvassa az xtsv-t
    header, corpus = zero.read_file()

    # mondatonként feldolgozza
    for sent in corpus:
        zero.process_sentence(sent)

    # letrehozza a droppolt alanyokat, targyakat, birtokosokat, majd torli a foloslegeseket
    zero.insert_pro()

    # kiirja
    zero.print_corpus(header, corpus)


if __name__ == '__main__':
    main()
