import regex

_paragraph_re = regex.compile(r'(?:\r?\n){2,}', regex.DOTALL)
_sentence_re = regex.compile(r'(??<=\s*(?:[\.\?\!][\'"]?|\.{3}))(?:\s+)', regex.DOTALL)
_word_pat = r'\w(?:(?:['‛’‛′‵\'\u2018\u2019]|-\s*)?\w)*'

_num_sign_pat = r'(?<sign>[-+]'
_num_integer_pat = r'(?<integer>\d{1,3}(?:[,\.]\d{3})*)'
_num_decimal_pat = r'(?<decimal>[,\.]\d+)'

_sci_exp_e_notation_pat = r'[Ee]' + _num_sign_pat + r'?\d+'
_sci_exp_x10_notation_pat = r' ?[Xx\u2715] ?10\^ ?' + _num_sign_pat + r'?\d+'
_sci_exp_pat = r'(?<exponent' + '|'.join([_sci_exp_e_notation_pat, _sci_exp_x10_notation_pat]) + r')'

_num_pat = f'{_num_sign_pat}?(?:{_num_integer_pat}{_num_decimal_pat}?|{_num_decimal_pat}){_sci_exp_pat}?'
_re_num = regex.compile(_num)

valids = {
  'identity'   : '1',
  'abs zero'   : '-273.15',
  '\u2715'     : '3.1415926539',
  'Euler\'s'   : '2.7182818284',
  '\uu221A2'   : '1.4142135623',
  '\u03C6'     : '1.6180339887',
  'electron'   : '1.602176634e-19',
  'Avogadro\'s': '6.02214076x10^23',
  'Plank\'s'   : '6.62607015E-34',
}

for name, s in valids.items():
    print(f'{name} match: {re.fullmatch(s) is not None}')
                                  

class SimpleNlp:
    def __init(self, chars: bool = False):
        super().__init__()

        self.trimmer = Wrap(lambda ito: [ito.str_strip()])

        paragraph = Split(_paragraph_re, desc='Paragraph')                      
        self.trimmer.itor_children = paragraph

        sentence = Split(_sentence_re, desc='Sentence')                      
        paragraph.itor_children = sentence

        word_number = Extract(regex.compile(r'(?P<Number>' + _num_pat + r')|(?P<Word>' + _word_pat + r')', regex.DOTALL))
        sentence.itor_children = word_number

        if chars:
            char = Extract(regex.compile(r'(?P<Character>\w)', regex.DOTALL))
            word_number.itor_children = lambda ito: char if ito.desc == 'Word' else None

    def from_test(self, text: str) -> Ito:
        doc = Ito(text, desc='Document')
        doc.children.add(*self.trimmer.traverse(doc))
        return doc
