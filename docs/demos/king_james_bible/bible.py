import sys
import os.path

import regex
import pawpaw
from pawpaw import arborform

"""
DEMO: KING JAMES BIBLE

This demo shows how to parse, visualize, and query the King James Bible using Pawpaw.

Note: The King James Bible was taken from: https://www.gutenberg.org/cache/epub/10/pg10.txt
"""

def get_parser() -> arborform.Itorator:
    testament_splitter = arborform.Split(
        regex.compile(r'(?<=\n{5})(?=The Old Testament of the King James Version of the Bible|The New Testament of the King James Bible)|(?<=\n{4})(?=\*\*\* END OF THE PROJECT GUTENBERG EBOOK)', regex.DOTALL),
        boundary_retention=arborform.Split.BoundaryRetention.NONE,
        desc='testament',
        tag='Testament splitter')

    testament_filter = arborform.Filter(
        lambda ito: ito.str_startswith(('The Old Testament', 'The New Testament')),
        tag='Testament filter')
    con = arborform.Connectors.Delegate(testament_filter)
    testament_splitter.connections.append(con)

    testament_stripper = arborform.Itorator.wrap(
        lambda ito: (ito.str_rstrip('\n*'),),
        tag='Testament stripper')
    con = arborform.Connectors.Delegate(testament_stripper)
    testament_filter.connections.append(con)

    testament_title_text_extractor = arborform.Extract(
        regex.compile(r'(?<title>.+?)\n{5}(?<text>.+)', regex.DOTALL),
        tag='Testament title & text extractor')
    con = arborform.Connectors.Children.Add(testament_title_text_extractor)
    testament_stripper.connections.append(con)

    book_splitter = arborform.Split(
        regex.compile(r'\n{5}', regex.DOTALL),
        boundary_retention=arborform.Split.BoundaryRetention.NONE,
        desc='book',
        tag='Book splitter')
    con = arborform.Connectors.Children.Add(book_splitter, 'text')
    testament_title_text_extractor.connections.append(con)

    book_title_text_extractor = arborform.Extract(
        regex.compile(r'(?<title>.+?)\n{3}(?<text>.+)', regex.DOTALL),
        tag='Book title & text extractor')
    con = arborform.Connectors.Children.Add(book_title_text_extractor)
    book_splitter.connections.append(con)

    chapter_splitter = arborform.Split(
        regex.compile(r'(?<=(\d+):\d+ .+?[ \n])(?=\d+:\d+)(?=(?!\1))', regex.DOTALL),
        boundary_retention=arborform.Split.BoundaryRetention.NONE,
        desc='chapter',
        tag='Chapter splitter')
    con = arborform.Connectors.Children.Add(chapter_splitter, 'text')
    book_title_text_extractor.connections.append(con)

    chapter_stripper = arborform.Itorator.wrap(
        lambda ito: (ito.str_strip(),),
        tag='Chapter stripper')
    con = arborform.Connectors.Delegate(chapter_stripper)
    chapter_splitter.connections.append(con)

    passage_splitter = arborform.Split(
        regex.compile(r'(?<=[\n ])(?=\d+:\d+ )', regex.DOTALL),  # Note: some passages are not separated with line breaks, e.g., Malachi 4:6
        boundary_retention=arborform.Split.BoundaryRetention.NONE,
        desc='passage',
        tag='Passage splitter')
    con = arborform.Connectors.Children.Add(passage_splitter)
    chapter_stripper.connections.append(con)

    passage_stripper = arborform.Itorator.wrap(
        lambda ito: (ito.str_rstrip(' \n'),),
        tag='Passage stripper')
    con = arborform.Connectors.Delegate(passage_stripper)
    passage_splitter.connections.append(con)

    chap_verse_extractor = arborform.Extract(
        regex.compile(r'(?<chapter_num>\d+):(?<verse_num>\d+) (?<text>.+)', regex.DOTALL),
        tag='Chapter, verse, text extractor')
    con = arborform.Connectors.Children.AddHierarchical(chap_verse_extractor)
    passage_stripper.connections.append(con)

    return testament_splitter

def get_text() -> pawpaw.Ito:
    with open(os.path.join(sys.path[0], 'bible.txt'), 'r', encoding='utf-8') as f:
        return pawpaw.Ito(f.read(), desc='bible')

# Process
print('\nPROCESSING... ', end='', flush=True)
i = get_text()
parser = get_parser()
i.children.add(*parser(i))
print('done.')

# Visualize
print('\nVISUALIZE:\n')
tree_vis = pawpaw.visualization.pepo.Tree()
print(tree_vis.dumps(i))

# Queries
print('\nQUERIES:\n')

print('1. Find books having 35 or more chapters:\n')
for book in i.find_all('**[d:book]'):
    cnt = sum(1 for chap in book.find_all('**[d:chapter]'))
    if cnt >= 35:
        print(f'\tTITLE: {book.find('*[d:title]'):%value!a}')
        print(f'\tCHAPTERS: {cnt:,}')
        print()

print('2. Find all passages containing the substring \'wolves\'\n')
query = '**[d:passage]{*[d:text] & [p:contains_wolves]}'
predicates = {'contains_wolves': lambda ei: str(ei.ito).casefold().find('wolves') != -1}
for num, passage in enumerate(i.find_all(query, predicates=predicates)):
    print(f'\tInstance {num:,}')
    print(f'\t\tTESTAMENT: "{passage.find('...[d:testament]/*[d:title]'):%value}"')
    print(f'\t\tBOOK: "{passage.find('...[d:book]/*[d:title]'):%value}"')
    print(f'\t\tCHAPTER: {passage.find('*[d:chapter_num]'):%value}')
    print(f'\t\tVERSE: {passage.find('*[d:verse_num]'):%value}')
    print(f'\t\tTEXT: "{passage.find('*[d:text]'):%value!a}"')
    print()
