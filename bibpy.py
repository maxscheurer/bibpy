#!/usr/bin/env python3
import os
import argparse as arg
import json
import bibtexparser
import titlecase
from bibtexparser.bparser import BibTexParser
from pylatexenc.latex2text import LatexNodes2Text


journal_db_file = os.path.dirname(
    os.path.realpath(__file__)) + "/journals.json"


def tex_to_unicode(tex):
    return LatexNodes2Text().latex_to_text(tex)


def nice_citation_key(entry):
    """
    Create a citation key of the sort
        <First Author><Year><First word of title>
    """
    authors_last_names = get_authors(entry)
    assert len(authors_last_names)
    first_author = authors_last_names[0]
    first_title_word = ""

    def pick_word(title_text):
        blacklist = [
            "the", "a", "an"
        ]
        blacklist_chars = [  # hyphen not allowed in key
            "-", "–"
        ]
        words = [w.strip(" {}").lower() for w in title_text.split()]
        for w in words:
            no_blk_chars = all(x not in blacklist_chars for x in w)
            if w not in blacklist and no_blk_chars:
                return w

    year = entry.get("year", None)
    title = entry.get("title", None)
    booktitle = entry.get("booktitle", None)
    if title is not None:
        entry["title"] = titlecase.titlecase(title)
        first_title_word = pick_word(entry["title"])
    if booktitle is not None:
        entry["booktitle"] = titlecase.titlecase(booktitle)
        first_title_word = pick_word(entry["booktitle"])
    if year is None:
        year = ""
        # print("No year for entry \"{}\"".format(entry["ID"]))
    new_citation_key = (
        first_author.lower() + year +
        first_title_word
    )
    return new_citation_key


def get_authors(entry):
    """
    Returns a list of the authors' last names from the bibtex entry
    """
    try:
        author = entry['author']
    except AttributeError:
        return None
    split_and = author.split(" and ")
    authors_ret = []
    for author in split_and:
        # check if comma-separated
        split_comma = author.split(",")
        if len(split_comma) == 1:  # name is correctly ordered: John Doe
            authors_ret.append(
                tex_to_unicode(split_comma[0].split()[-1].strip())
            )
        else:  # last name first: Doe, John
            authors_ret.append(
                tex_to_unicode(split_comma[0].strip())
            )
    return authors_ret


def parse_bibfile(bibfile):
    parser = BibTexParser()
    with open(bibfile, "r") as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file, parser=parser)
    return bib_database


if __name__ == "__main__":
    parser = arg.ArgumentParser()
    parser.add_argument("bibfile", help="Input bibliography file")
    parser.add_argument("outfile", help="Output bibliography file")
    parser.add_argument("--remove-duplicates", "-r",
                        help="Remove duplicate entries (based on DOI)",
                        action="store_true", default=False)
    args = parser.parse_args()

    with open(journal_db_file, "r") as journal_file:
        journals = json.load(journal_file)

    journals_tc = {j.title(): journals[j] for j in journals.keys()}
    journal_abbrevs = [j.title() for j in journals.values()]

    # load the input bib file
    bib = parse_bibfile(args.bibfile)

    # try to find the journal
    dois = []
    new_entries = []
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

        # look for duplicates (DOI)
        doi = entry.get("doi", None)
        if doi:
            if doi in dois:
                # print("Duplicate found:", entry["title"])
                if args.remove_duplicates:
                    continue
            else:
                dois.append(doi)

        # sanitize citation key
        entry["ID"] = nice_citation_key(entry)

        # make everything title-case
        title = entry.get("title", None)
        booktitle = entry.get("booktitle", None)
        if title is not None:
            entry["title"] = titlecase.titlecase(title)
            first_title_word = entry["title"].split()[0].strip().lower()
        if booktitle is not None:
            entry["booktitle"] = titlecase.titlecase(booktitle)
            first_title_word = entry["booktitle"].split()[0].strip().lower()
        new_entries.append(entry)

    print("Number of entries before: ", len(bib.entries))
    bib.entries = new_entries
    print("Number of entries after cleanup: ", len(bib.entries))
    with open(args.outfile, 'w') as bibtex_file:
        bibtexparser.dump(bib, bibtex_file)
