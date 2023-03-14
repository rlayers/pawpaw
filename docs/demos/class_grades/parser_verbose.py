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
    con = arborform.Connectors.Children.Add(name_grades)
    school_splitter.connections.append(con)

    grade_splitter = arborform.Split(
        regex.compile(r'(?<=\n)(?=Grade =)', regex.DOTALL),
        desc='grade',
        tag='grade splitter')
    con = arborform.Connectors.Delegate(grade_splitter, lambda ito: ito.desc == 'grades')
    name_grades.connections.append(con)

    grade = arborform.Extract(
        regex.compile(r'Grade = (?<key>\d+)\nStudent number, Name\n(?<stu_num_names>.+?)\nStudent number, Score\n(?<stu_num_scores>.+)', regex.DOTALL),
        tag='grade & stu_num/name * stu_num/score')
    con = arborform.Connectors.Children.Add(grade)
    grade_splitter.connections.append(con)

    stu_num_names = arborform.Extract(
        regex.compile(r'(?<stu_num>\d+), (?<name>.+?)\n', regex.DOTALL),
        tag='stu num/name pairs')
    con = arborform.Connectors.Children.Add(stu_num_names, lambda ito: ito.desc == 'stu_num_names')
    grade.connections.append(con)

    stu_num_scores = arborform.Extract(
        regex.compile(r'(?<stu_num>\d+), (?<score>\d+)(?:$|\n)', regex.DOTALL),
        tag='stu num/score pairs')
    con = arborform.Connectors.Children.Add(stu_num_scores)
    grade.connections.append(con)

    return school_splitter
