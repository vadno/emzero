# emZero

emZero inserts nodes for droped pronouns into an [xtsv](https://github.com/dlt-rilmta/xtsv) file. The rule-based script inserts:
* zero subject of a finite verb if it does not have an overt one
* zero object of a definite finite verb if it does not have an overt one
* zero possessor of a possessum if it does not have an overt one
* zero subject of an inflected or not inflected infinite verb

## Usage

emZero can be used
* as a module of [emtsv](https://github.com/dlt-rilmta/emtsv)
* independently by issuing `python3 -m emzero` as it reads from standard input and writes to standard output

### Input and output

The input and output format of emZero is [xtsv](https://github.com/dlt-rilmta/xtsv).

### Dependencies

This module can be applied on dependency parsed text, therefore it fits after [emDep](https://github.com/dlt-rilmta/emdeppy) module of [emtsv](https://github.com/dlt-rilmta/emtsv).

## Citing and License

**emZero** can be used under GNU General Public License v3.0 license.

Please, cite this article:

```
@inproceedings{korkor,
    author = {Vadász, Noémi},
    title = {{K}or{K}orpusz: kézzel annotált, többrétegű pilotkorpusz építése},
    booktitle = {{XVI}. {M}agyar {S}zámítógépes {N}yelvészeti {K}onferencia ({MSZNY} 2020)},
    editor = {Berend, Gábor and Gosztolya, Gábor and Vincze, Veronika},
    pages = {141--154},
    publisher = {Szegedi Tudományegyetem, TTIK, Informatikai Intézet},
    address = {Szeged},
    year = {2020}
}
```