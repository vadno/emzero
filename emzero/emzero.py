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
            feats = self._parse_udfeats(feats)
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

        # Field names for xtsv (the code below is mandatory for an xtsv module)
        if source_fields is None:
            source_fields = set()

        if target_fields is None:
            target_fields = []

        self.source_fields = source_fields
        self.target_fields = target_fields

    @staticmethod
    def prepare_fields(field_names):
        return [field_names['form'], field_names['lemma'], field_names['xpostag'], field_names['upos'],
                field_names['feats'], field_names['id'], field_names['head'], field_names['deprel']]

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
        pro.feats = '|'.join('{0}={1}'.format(feat, val) for feat, val in sorted(pro.feats.items(),
                                                                                 key=lambda x: x[0].lower()))
        pro.anas = '[]'

        return pro

    @staticmethod
    def process_sentence(sent):

        sent_actors = list()
        deps_dict = defaultdict(list)

        # elmenti az összes függőséget
        # dictet épít: az anyacsomóponthoz a gyerekeit listázza
        for head in sent:
            for dep in sent:
                if dep.head == head.id:
                    deps_dict[head].append(dep)

            # TODO miért is kell ez?
            if head.upos in VERBS and head not in deps_dict:
                deps_dict[head].append(head)

        for head in deps_dict:
            if head.upos in VERBS:

                verb = Word.inherit_base_features(head)

                actors = defaultdict(list)
                actors[verb] = []

                for dep in deps_dict[head]:
                    if dep.deprel in ARGUMENTS:

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

    def insert_pro(self, actorlist):
        """
        letrehoz droppolt alanyt, targyat
        alanyt: minden igenek
        targyat: csak a definit ragozasu igeknek
        :param
        :return:
        """

        # for actors in self._actor_list:
        for actors in actorlist:
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
    def print_pro(header, token, actorlist):

        for actors in actorlist:
            for verb in actors.keys():
                for dep in actors[verb]:
                    if dep.abs_index == token.abs_index:
                        if dep.form == 'DROP':
                            print('\t'.join(getattr(dep, field) for field in header))

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
