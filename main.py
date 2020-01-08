#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    author: Noémi Vadász
    last update: 2020.01.08.

"""

from collections import defaultdict
import sys
import csv

pron_persnum = {('Sing', '1'): 'én',
                ('Sing', '2'): 'te',
                ('Sing', '3'): 'ő/az',
                ('Plur', '1'): 'mi',
                ('Plur', '2'): 'ti',
                ('Plur', '3'): 'ők/azok',
                ('X', 'X'): 'X'}

emmorph_number = {'Sing': 'Sg',
                  'Plur': 'Pl',
                  'X': 'X'}


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

    def print_token(self):
        print('\t'.join(
            [self.id, self.form, self.lemma, self.upos, self.xpostag, self.feats, self.head, self.deprel, self.deps,
             self.misc]))


class EmZero:
    def __init__(self, source_fields=None, target_fields=None):
        # Custom code goes here

        # Field names for xtsv (the code below is mandatory for an xtsv module)
        if source_fields is None:
            source_fields = set()

        if target_fields is None:
            target_fields = []

        self.source_fields = source_fields
        self.target_fields = target_fields

    @staticmethod
    def base_features(pro, head):
        """
        feature-ök, amelyeket a zéró elem attól a fejtől örököl
        :param pro: zéró elem
        :param head: fej
        :return:
        """

        for field in vars(head):
            setattr(pro, field, getattr(head, field))

    @staticmethod
    def parse_udfeats(feats):
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
    def pro_default_features(dropped):
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

    def pro_calc_features(self, head, role):
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
        self.pro_default_features(pro)

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

        pro.xpostag = '[/N|Pro][' + pro.feats['Person'] + emmorph_number[pro.feats['Number']] + '][' + pro.feats[
            'Case'] + ']'
        # pro.xpostag = 'PRON'
        pro.lemma = pron_persnum[(pro.feats['Number'], pro.feats['Person'])]
        pro.feats = '|'.join(feat + '=' + pro.feats[feat] for feat in sorted(pro.feats, key=str.lower))
        pro.anas = '[]'

        return pro

    def actor_features(self, corpus):
        """

        :return:
        """

        actor_list = []  # actorlista: mondatok listaja, kulcs az ige, ertek a vonzatok listaja

        for sent in corpus:

            deps = []
            for head in sent:  # head
                for dep in sent:
                    if dep.head == head.id:
                        deps.append((head, dep))

                if head.upos in ('VERB',) and head not in deps:  # TODO nem csak igék! minden vonzatos cucc
                    deps.append((head, head))

            # egy elemhez hozzarendeli az osszes ramutato fuggosegi viszonyt
            # egy headhez az osszes depot
            deps_dict = {}
            for a, b in deps:
                deps_dict.setdefault(a, []).append(b)

            for head in deps_dict:

                if head.upos in ('VERB',):  # TODO nem csak igék! minden vonzatos cucc

                    verb = Word()
                    self.base_features(verb, head)
                    verb.feats = self.parse_udfeats(verb.feats)

                    actors = defaultdict(list)
                    actors[verb] = []

                    for dep in deps_dict[head]:

                        if dep.deprel in ('SUBJ', 'OBJ', 'OBL', 'DAT', 'POSS', 'INF', 'LOCY'):  # TODO egyéb határozók

                            actor = Word()
                            self.base_features(actor, dep)
                            actor.feats = self.parse_udfeats(actor.feats)

                            actor.sent_nr = verb.sent_nr

                            if 'Number[psor]' in actor.feats:

                                for ifposs in sent:
                                    if ifposs.head == dep.id and ifposs.deprel == 'POSS' \
                                            and ifposs.upos in ('NOUN', 'PROPN', 'ADJ', 'NUM', 'DET', 'PRON'):
                                        # ifposs.print_token()
                                        ifposs.upos = 'PRON'

                                        newactor = Word()
                                        self.base_features(newactor, ifposs)
                                        newactor.feats = self.parse_udfeats(ifposs.feats)

                                        actors[verb].append(newactor)

                            actors[verb].append(actor)

                    actor_list.append(actors)

        return actor_list

    @staticmethod
    def remove_dropped(head, deps, role):
        """
        kitorli a actors kozul azokat a droppolt alanyokat, targyakat, amikhez van testes
        :param? head:
        :param deps: az aktualis ige vonzatai
        :param role: szerep
        :return:
        """

        subj_obj_poss = False
        for actor in deps:
            if actor.head == head and actor.deprel == role and actor.form != 'DROP':
                subj_obj_poss = True

        if subj_obj_poss:
            for actor in deps:
                if actor.head == head and actor.deprel == role and actor.form == 'DROP':
                    deps.remove(actor)

    def insert_pro(self, actor_list):
        """
        letrehoz droppolt alanyt, targyat
        alanyt: minden igenek
        targyat: csak a definit ragozasu igeknek
        :param actor_list: a actors adatszerkezete
        :return:
        """

        for actors in actor_list:
            for verb, deps in actors.items():

                subj = self.pro_calc_features(verb, 'SUBJ')
                actors[verb].append(subj)

                if 'Definite' in verb.feats and verb.feats['Definite'] in ('Def', '2'):

                    inf = False
                    for actor in actors[verb]:
                        if actor.deprel == 'INF':
                            inf = True
                            break

                    if not inf:
                        obj = self.pro_calc_features(verb, 'OBJ')
                        actors[verb].append(obj)

                for actor in deps:
                    if 'Number[psor]' in actor.feats:
                        poss = self.pro_calc_features(actor, 'POSS')
                        actors[verb].append(poss)

                # print(verb.form)
                # for actor in deps:
                #     print(actor.form, actor.deprel, sep='\t')
                # print('')

                # kitorli a droppolt alanyt, targyat, ha van testes megfeleloje
                self.remove_dropped(verb.id, deps, 'SUBJ')
                self.remove_dropped(verb.id, deps, 'OBJ')
                for actor in deps:
                    self.remove_dropped(actor.id, deps, 'POSS')

    @staticmethod
    def print_pro(header, token, actors):

        for sent in actors:
            for key, value in sent.items():
                for dep in value:
                    if dep.abs_index == token.abs_index:
                        if dep.form == 'DROP':
                            print('\t'.join(getattr(dep, field) for field in header))

    def print_corpus(self, header, actors, corpus):

        print('\t'.join(field for field in header))

        for sentence in corpus:
            for token in sentence:  # TODO zéró és testes feje sorrend!
                print('\t'.join(getattr(token, field) for field in header))
                self.print_pro(header, token, actors)
            print('')

    @staticmethod
    def parse_fields(token, line, header):

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
                    self.parse_fields(token, line, header)
                    token.sent_nr = str(counter)
                    token.abs_index = str(abs_counter)

                    sent.append(token)

            else:
                counter += 1
                corp.append(sent)
                sent = list()

        corp.append(sent)

        # for sent in corp:
        #     for token in sent:
        #         print(token.form)
        #     print('')

        return header, corp


def main():
    zero = EmZero()

    # beolvassa az xtsv-t
    header, corpus = zero.read_file()
    orig_corpus = corpus

    # berakja a kivant adatszerkezetbe
    actors = zero.actor_features(corpus)

    # letrehozza a droppolt alanyokat, targyakat, birtokosokat, majd torli a foloslegeseket
    zero.insert_pro(actors)

    # kiirja
    zero.print_corpus(header, actors, orig_corpus)


if __name__ == '__main__':
    main()
