import sys
import os.path

import regex
import pawpaw
from pawpaw import arborform

"""
DEMO: US CONSTITUTION

This demo shows an example of how to parse, visualize, and query the US Constitution using Pawpaw.

Note: The text for the constitution was taken from https://www.archives.gov/founding-docs/constitution-transcript
"""

def get_parser() -> arborform.Itorator:
    # Article: could be preamble
    a_splitter = arborform.Split(
        regex.compile(r'(?<=\n+)(?=Article\.)', regex.DOTALL),
        boundary_retention=arborform.Split.BoundaryRetention.NONE,
        tag='article splitter')

    a_desc = arborform.Desc(
        desc=lambda ito: 'article' if ito.str_startswith('Article.') else 'preamble',
        tag='article desc')
    con = arborform.Connectors.Delegate(a_desc)
    a_splitter.connections.append(con)

    con = arborform.Connectors.Children.Add(pawpaw.nlp.SimpleNlp().itor, lambda ito: ito.desc == 'preamble')
    a_desc.connections.append(con)

    a_extractor = arborform.Extract(
        regex.compile(r'Article\. (?<key>[A-Z]+)\.\n(?<value>.+)', regex.DOTALL),
        tag='article extractor')
    con = arborform.Connectors.Children.Add(a_extractor, lambda ito: ito.desc == 'article')
    a_desc.connections.append(con)

    # Section: only some articles have sections
    s_splitter = arborform.Split(
        regex.compile(r'(?<=\n+)(?=Section\.)', regex.DOTALL),
        boundary_retention=arborform.Split.BoundaryRetention.LEADING,
        desc='section',
        tag='section splitter')
    con = arborform.Connectors.Children.Add(s_splitter, lambda ito: ito.desc == 'value' and ito.str_startswith('Section.'))
    a_extractor.connections.append(con)
    con = arborform.Connectors.Children.Add(pawpaw.nlp.SimpleNlp().itor, lambda ito: ito.desc == 'value' and not ito.str_startswith('Section.'))
    a_extractor.connections.append(con)

    s_extractor = arborform.Extract(regex.compile(r'Section\. (?<key>\d+)\.\n(?<value>.+)', regex.DOTALL))
    con = arborform.Connectors.Children.Add(s_extractor)
    s_splitter.connections.append(con)
    con = arborform.Connectors.Children.Add(pawpaw.nlp.SimpleNlp().itor, lambda ito: ito.desc == 'value')
    s_extractor.connections.append(con)

    return a_splitter


def get_text() -> pawpaw.Ito:
    with open(os.path.join(sys.path[0], 'us_constitution.txt')) as f:
        return pawpaw.Ito(f.read(), desc='constitution')


# Visualize
print(f'\nVISUALIZE:\n')
i = get_text()
tree_vis = pawpaw.visualization.pepo.Tree()
parser = get_parser()
i.children.add(*parser(i))
print(tree_vis.dumps(i))

# Query
print(f'\nQUERY:\n')
print(f'\tGoal: Find sections containing words \'power\' or \'right\'\n')
query = '**[d:section]{**[d:word] & [lcs:power,right]}'
print(f'\tPlumule Query: {query}\n')
print(f'\tResults:\n')
for i, section in enumerate(i.find_all(query)):
    article_key = section.find('..[d:article]/*[d:key]')
    section_key = section.find('*[d:key]')
    section_value = section.find('*[d:value]')
    print(f'\t\tMatch {i}: Article {article_key}, Section {section_key}')
    print(f'\t\t\t{section_value:%substr:45…}')
