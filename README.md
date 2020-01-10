# emZero

emZero inserts nodes for droped pronouns into an [xtsv](https://github.com/dlt-rilmta/xtsv) file. The rule-based script inserts:
* zero subject of a finite verb if it does not have an overt one
* zero object of a definite finite verb if it does not have an overt one
* zero possessor of a possessum if it does not have an overt one
* zero subject of an inflected or not inflected infinite verb

# Usage

emZero can be used
* as a module of [emtsv](https://github.com/dlt-rilmta/emtsv)
* independently as it reads from standard input and writes to standard output

## Input and output

The input and output format of emZero is [xtsv](https://github.com/dlt-rilmta/xtsv).

# License

The script can be used under GNU General Public License v3.0 license.