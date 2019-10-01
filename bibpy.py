#!/usr/bin/env python3
import os
import argparse as arg
import json
import bibtexparser
import titlecase
from bibtexparser.bparser import BibTexParser
#from bibtexparser.customization import homogenize_latex_encoding


journal_db_file = os.path.dirname(os.path.realpath(__file__)) + "/journals.json"


def parse_bibfile(bibfile):
    parser = BibTexParser()
    #parser.customization = homogenize_latex_encoding
    with open(bibfile, "r") as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file, parser=parser)
    return bib_database


if __name__ == "__main__":
    parser = arg.ArgumentParser()
    parser.add_argument("bibfile", help="Input bibliography file")
    parser.add_argument("outfile", help="Output bibliography file")
    args = parser.parse_args()

    with open(journal_db_file, "r") as journal_file:
        journals = json.load(journal_file)

    journals_tc = {j.title(): journals[j] for j in journals.keys()}
    journal_abbrevs = [j.title() for j in journals.values()]

    # load the input bib file
    bib = parse_bibfile(args.bibfile)

    # try to find the journal
    for entry in bib.entries:
        current_journal = entry.get("journal", None)
        if not current_journal:
            continue
            print("No journal name for entry {}.".format(entry))

        current_journal = current_journal.title()
        if current_journal in journals_tc.keys():
            # print("Not abbreviated:", current_journal)
            entry["journal"] = journals_tc[current_journal]
        elif current_journal in journal_abbrevs:
            # print("Already abbreviated: ", current_journal)
            entry["journal"] = current_journal
        else:
            print("not found", current_journal)

        # make everything title-case
        title = entry.get("title", None)
        booktitle = entry.get("booktitle", None)
        if title is not None:
            entry["title"] = titlecase.titlecase(title)
        if booktitle is not None:
            entry["booktitle"] = titlecase.titlecase(booktitle)

    with open(args.outfile, 'w') as bibtex_file:
        bibtexparser.dump(bib, bibtex_file)
