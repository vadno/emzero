#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from emzero import EmZero


def main():
    zero = EmZero()

    # beolvassa az xtsv-t
    header, corpus = zero.read_file()

    print('\t'.join(field for field in header))

    # mondatonként feldolgozza
    for sent in corpus:
        actors = zero.process_sentence(sent)

    # letrehozza a droppolt alanyokat, targyakat, birtokosokat, majd torli a foloslegeseket
        zero.insert_pro(actors)

        # kiirja
        for token in sent:
            print('\t'.join(getattr(token, field) for field in header))
            zero.print_pro(header, token, actors)
        print('')


if __name__ == '__main__':
    main()
