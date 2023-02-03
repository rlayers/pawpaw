import sys
import os.path

import regex
import pawpaw

"""
DEMO: US CONSTITUTION

This demo shows an exmaple of how to parse, visualize, and query the US Constitution using Pawpaw.

Note: The text for the constitution was taken from https://www.archives.gov/founding-docs/constitution-transcript
"""

def get_parser() -> pawpaw.arborform.Itorator:
    # Article (can also be preamble)
    a_splitter = pawpaw.arborform.Split(
        regex.compile(r'(?<=\n+)(?=Article\.)', regex.DOTALL),
        boundary_retention=pawpaw.arborform.Split.BoundaryRetention.NONE)

    a_desc = pawpaw.arborform.Desc(
        desc=lambda ito: 'article' if ito.str_startswith('Article.') else 'preamble')
    a_splitter.itor_next = a_desc

    a_extractor = pawpaw.arborform.Extract(regex.compile(r'Article\. (?<key>[A-Z]+)\.\n(?<value>.+)', regex.DOTALL))
    a_desc.itor_children = (lambda ito: ito.desc == 'article', a_extractor)

    # Section (only some articles have sections)
    s_splitter = pawpaw.arborform.Split(
        regex.compile(r'(?<=\n+)(?=Section\.)', regex.DOTALL),
        boundary_retention=pawpaw.arborform.Split.BoundaryRetention.LEADING,
        desc='section')
    nlp = pawpaw.nlp.SimpleNlp().itor
    # a_extractor.itor_children = lambda ito: (s_splitter if ito.str_startswith('Section.') else nlp) if ito.desc == 'value' else None
    a_extractor.itor_children.append((lambda ito: ito.desc == 'value' and ito.str_startswith('Section.'), s_splitter))
    a_extractor.itor_children.append((lambda ito: ito.desc == 'value', nlp))

    s_extractor = pawpaw.arborform.Extract(regex.compile(r'Section\. (?<key>\d+)\.\n(?<value>.+)', regex.DOTALL))
    s_splitter.itor_children = s_extractor

    s_extractor.itor_children = (lambda ito: ito.desc == 'value', nlp)

    return a_splitter


def get_text() -> pawpaw.Ito:
    with open(os.path.join(sys.path[0], 'us_constitution.txt')) as f:
        return pawpaw.Ito(f.read(), desc='constitution')


# Visualize
print(f'\nVISUALIZE:\n')
i = get_text()
tree_vis = pawpaw.visualization.pepo.Tree()
parser = get_parser()
i.children.add(*parser.traverse(i))
print(tree_vis.dumps(i))

# Query
print(f'\nQUERY:\n')
print(f'\tGoal: Find sections containing words \'power\' or \'right\'\n')
query = '**[d:section]{**[d:word] & [lcs:power,right]}'
print(f'\tPlumule Query: {query}\n')
print(f'\tResults:\n')
for i, section in enumerate(i.find_all(query)):
    article_key = section.find('...[d:article]/*[d:key]')
    section_key = section.find('*[d:key]')
    section_value = section.find('*[d:value]')
    print(f'\t\tMatch {i}: Article {article_key}, Section {section_key}')
    print(f'\t\t\t{section_value:%substr:45…}')
