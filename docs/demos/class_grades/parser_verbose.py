import regex
from pawpaw import arborform

def get_parser() -> arborform.Itorator:
    school_splitter = arborform.Split(
        regex.compile(r'(?<=(?:^|\n))(?=School =)', regex.DOTALL),
        desc='school',
        tag='school splitter')

    name_grades = arborform.Extract(
        regex.compile(r'School = (?<name>.+?)\n(?<grades>.+)(?:$|\n)', regex.DOTALL),
        tag='school name & grades')
    school_splitter.itor_children = name_grades

    grade_splitter = arborform.Split(
        regex.compile(r'(?<=\n)(?=Grade =)', regex.DOTALL),
        desc='grade',
        tag='grade splitter')
    name_grades.itor_next = lambda ito: ito.desc == 'grades', grade_splitter

    grade = arborform.Extract(
        regex.compile(r'Grade = (?<key>\d+)\nStudent number, Name\n(?<stu_num_names>.+?)\nStudent number, Score\n(?<stu_num_scores>.+)', regex.DOTALL),
        tag='grade & stu_num/name * stu_num/score')
    grade_splitter.itor_children = grade

    stu_num_names = arborform.Extract(
        regex.compile(r'(?<stu_num>\d+), (?<name>.+?)\n', regex.DOTALL),
        tag='stu num/name pairs')
    grade.itor_children = lambda ito: ito.desc == 'stu_num_names', stu_num_names

    stu_num_scores = arborform.Extract(
        regex.compile(r'(?<stu_num>\d+), (?<score>\d+)(?:$|\n)', regex.DOTALL),
        tag='stu num/score pairs')
    grade.itor_children.append(stu_num_scores)

    return school_splitter
