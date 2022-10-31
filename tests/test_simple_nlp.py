import segments
from tests.util import _TestIto, IntIto


class TestSimpleNlp(_TestIto):
    _valid_numbers = {
        'identity': '1',
        'with thousands sep': '1,234,567.89',
        'without thousands sep': '1234567.89',
        'abs zero': '-273.15',
        '\u2715': '3.1415926539',
        'Euler\'s': '2.7182818284',
        '\u221A2': '1.4142135623',
        '\u03C6': '1.6180339887',
        'electron': '1.602176634e-19',
        'Avogadro\'s': '6.02214076x10^23',
        'Plank\'s': '6.62607015E-34',
    }

    def test_num_valid(self):
        re = segments.nlp.Number(thousands_seps={'', ','}).re
        for name, s in self._valid_numbers.items():
            with self.subTest(name=name, string=s):
                self.assertTrue(re.fullmatch(s) is not None)

    def test_num_valid(self):
        re = segments.nlp.Number(thousands_seps={'', ','}).re
        for s in '', ' ', 'abc', '1x2', 'two':
            with self.subTest(string=s):
                self.assertTrue(re.fullmatch(s) is None)

    def test_num_thousands_seps(self):
        for seps in None, ('',), ('', ','), (',',), ('', '.'):
            if seps is None:
                number = segments.nlp.Number()
                seps = (',',)
            else:
                number = segments.nlp.Number(thousands_seps=seps)

            vals = ['123', '456']
            for sep in seps:
                val = (',' if sep is None else sep).join(vals)
                val += '.789' if ',' in seps else ',789'
                with self.subTest(thousands_seps=seps, val=val):
                    self.assertTrue(number.re.fullmatch(val) is not None)

    def test_from_text(self):
        nlp = segments.nlp.SimpleNlp()
        for name, data in {
            'Simple sentence': {
                'See Jack run.':
                    {'Document': 1, 'Paragraph': 1, 'Sentence': 1, 'Word': 3, 'Number': 0}
            },

            'Sentence with numbers': {
                'This sentence has 4 words, not 10.':
                    {'Document': 1, 'Paragraph': 1, 'Sentence': 1, 'Word': 5, 'Number': 2}
            },

            'Two short paragraphs': {
                '\tI am.  I was.\r\n\r\n\tI will be.\r\n\r\n':
                    {'Document': 1, 'Paragraph': 2, 'Sentence': 3, 'Word': 7, 'Number': 0}
            },

            'Moby Dick': {
                """Call me Ishmael. Some years ago — never mind how long precisely — having
                little or no money in my purse, and nothing particular to interest me on shore,
                I thought I would sail about a little and see the watery part of the world.""":
                    {'Document': 1, 'Paragraph': 1, 'Sentence': 2, 'Word': 43, 'Number': 0}
            },

            'Poe': {
                """Once upon a midnight dreary, while I pondered, weak and weary,
                Over many a quaint and curious volume of forgotten lore—
                While I nodded, nearly napping, suddenly there came a tapping,
                As of some one gently rapping, rapping at my chamber door.
                “’Tis some visitor,” I muttered, “tapping at my chamber door—
                Only this and nothing more.”""":
                    {'Document': 1, 'Paragraph': 1, 'Sentence': 2, 'Word': 57, 'Number': 0}
            }
        }.items():
            for text, counts in data.items():
                for desc, count in counts.items():
                    result = nlp.from_text(text)
                    with self.subTest(name=name, desc=desc):
                        actual = sum(1 for i in result.find_all(f'**![d:{desc}]'))
                        self.assertEqual(count, actual)