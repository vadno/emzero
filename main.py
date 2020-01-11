#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from xtsv import build_pipeline
import sys


def main():

    # Set input and output iterators...
    input_iterator = open('globv_1.xtsv', encoding='UTF-8')
    output_iterator = sys.stdout

    # Set the tagger name as in the tools dictionary
    used_tools = ['zero']
    presets = []

    # Init and run the module as it were in xtsv

    # The relevant part of config.py
    # from emdummy import DummyTagger
    em_zero = ('emzero', 'EmZero', 'HELPER SZÖVEG AMI A WEB felületen jelenik meg',
               (), {'source_fields': {'form', 'lemma', 'xpostag', 'upos', 'feats', 'id', 'head', 'deprel'},
                    'target_fields': []})
    tools = [(em_zero, ('zero', 'emZero'))]

    # Run the pipeline on input and write result to the output...
    output_iterator.writelines(build_pipeline(input_iterator, used_tools, tools, presets))


if __name__ == '__main__':
    main()
