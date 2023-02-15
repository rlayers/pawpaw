import sys
import os.path

import regex
from pawpaw import Ito, visualization
import pandas as pd

while ((answer := input('Select (C)ompact or (V)erbose parser: ').casefold()) not in 'cv'):
    pass

# read file
with open(os.path.join(sys.path[0], 'input.txt')) as f:
    ito = Ito(f.read(), desc='all')

# parse
if answer == 'c':
    from parser_compact import get_parser
else:
    from parser_verbose import get_parser
parser = get_parser()
ito.children.add(*parser(ito))

# display Pawpaw tree
tree_vis = visualization.pepo.Tree()
print(tree_vis.dumps(ito))

# build pandas DataFrame
d = []
for school in ito.find_all('*[d:school]'):
    school_name = str(school.find('*[d:name]'))
    for grade in school.find_all('**[d:grade]'):
        grade_key = int(str(grade.find('*[d:key]')))
        for stu_num in grade.find_all('*[d:stu_num_names]/*[d:stu_num]'):
            stu_name = str(stu_num.find('>[d:name]'))
            stu_num = str(stu_num)
            stu_score = int(str(grade.find('*[d:stu_num_scores]/*[d:stu_num]&[s:' + stu_num + ']/>[d:score]')))
            d.append({'School': school_name, 'Grade': grade_key, 'Student number': stu_num, 'Name': stu_name, 'Score': stu_score})
data = pd.DataFrame(d)
data.set_index(['School', 'Grade', 'Student number'], inplace=True)
data = data.groupby(level=data.index.names).first()

# display pandas DataFrame
print(data)
