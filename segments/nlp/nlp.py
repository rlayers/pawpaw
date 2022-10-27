import regex
import segments


class SimpleNlp:
    _paragraph_re = regex.compile(r'(?:\r?\n){2,}', regex.DOTALL)
    _sentence_re = regex.compile(r'(?<=\s*(?:[\.\?\!][\'"]?|\.{3}))(?:\s+)', regex.DOTALL)

    _apostrophe_pat = r'[' + '|'.join(("'", '‛', '‵', '′', '’', '\u2018', '\u2018\u2019')) + r']'
    _word_pat = r'\w(?:(?:' + _apostrophe_pat + r'|-\s*)?\w)*'

    _num_sign_pat = r'(?<sign>[-+])'
    _num_integer_pat = r'(?<integer>\d{1,3}(?:[,\.]\d{3})*)'
    _num_decimal_pat = r'(?<decimal>[,\.]\d+)'
    _num_sci_exp_e_notation_pat = r'[Ee]' + _num_sign_pat + r'?\d+'
    _num_sci_exp_x10_notation_pat = r' ?[Xx\u2715] ?10\^ ?' + _num_sign_pat + r'?\d+'
    _num_sci_exp_pat = r'(?<exponent>' + '|'.join([_num_sci_exp_e_notation_pat, _num_sci_exp_x10_notation_pat]) + r')'
    _num_pat = f'{_num_sign_pat}?(?:{_num_integer_pat}{_num_decimal_pat}?|{_num_decimal_pat}){_num_sci_exp_pat}?'
    _num_re = regex.compile(_num_pat)

    def __init__(self, chars: bool = False):
        super().__init__()

        trimmer = segments.itorator.Wrap(lambda ito: [ito.str_strip()])

        paragraph = segments.itorator.Split(self._paragraph_re, desc='Paragraph')
        trimmer.itor_children = paragraph

        sentence = segments.itorator.Split(self._sentence_re, desc='Sentence')
        paragraph.itor_children = sentence

        word_number = segments.itorator.Extract(regex.compile(r'(?P<Number>' + self._num_pat + r')|(?P<Word>' + self._word_pat + r')', regex.DOTALL))
        sentence.itor_children = word_number

        if chars:
            char = segments.itorator.Extract(regex.compile(r'(?P<Character>\w)', regex.DOTALL))
            word_number.itor_children = lambda ito: char if ito.desc == 'Word' else None

        self.itor = trimmer

    def from_text(self, text: str) -> segments.Ito:
        doc = segments.Ito(text, desc='Document')
        doc.children.add(*self.itor.traverse(doc))
        return doc
