import regex
from pawpaw import arborform

def get_parser() -> arborform.Itorator:
    return arborform.Extract(
        regex.compile(
            r'(?<school>School = (?<name>.+?)\n'
            r'(?<grade>Grade = (?<key>\d+)\n'
            r'Student number, Name\n(?P<stu_num_names>(?:(?P<stu_num>\d+), (?P<name>.+?)\n)+)\n'
            r'Student number, Score\n(?P<stu_num_scores>(?:(?P<stu_num>\d+), (?P<score>\d+)(?:$|\n))+)(?:$|\n)'
            r')+)+',
            regex.DOTALL
    )
)
