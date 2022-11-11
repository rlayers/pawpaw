import json
import pickle

from pawpaw import Ito
from tests.util import _TestIto


class TestItoSerialization(_TestIto):
    def setUp(self) -> None:
        super().setUp()

        s = 'See Jack run.'
        self.h_ito = Ito(s, desc='Phrase')
        self.h_ito.children.add(*self.h_ito.str_split())
        for c in self.h_ito.children:
            c.desc = 'Word'
            self.add_chars_as_children(c, 'Char')

    def test_pickle_serialize(self):
        word = self.h_ito.find('**[d:Word]')
        pickle_data = pickle.dumps(word)
        self.assertLess(0, len(pickle_data))
      
    def test_pickle_deserialize(self):
        w_orig = self.h_ito.find('**[d:Word]')
        pickle_data = pickle.dumps(w_orig)
        w_deser = pickle.loads(pickle_data)
        self.assertEqual(w_orig, w_deser)

    def test_json_serialize(self):
        word = self.h_ito.find('**[d:Word]')
        js_data = json.dumps(word, cls=Ito.JsonEncoder)
        expected_prefix = '{"__type__": "typing.Tuple[str, Ito]", "string": "' + \
            word.string + \
            '", "ito": {"__type__": "Ito", "span": ' + \
            str(list(word.span)) + \
            ', "desc": "' + \
            word.desc + \
            '"'
        self.assertTrue(js_data.startswith(expected_prefix))      

    def test_json_deserialize(self):
        w_orig = self.h_ito.find('**[d:Word]')
        js_data = json.dumps(w_orig, cls=Ito.JsonEncoder)
        w_deser = json.loads(js_data, object_hook=Ito.json_decoder)
        self.assertEqual(w_orig, w_deser)
        
    def test_json_stringless_serialize(self):
        word = self.h_ito.find('**[d:Word]')
        js_data = json.dumps(word, cls=Ito.JsonEncoderStringless)
        expected_prefix = '{"__type__": "Ito", "span": ' + \
            str(list(word.span)) + \
            ', "desc": "' + \
            word.desc + \
            '"'
        self.assertTrue(js_data.startswith(expected_prefix))      

    def test_json_stringless_deserialize(self):
        w_orig = self.h_ito.find('**[d:Word]')
        js_data = json.dumps(w_orig, cls=Ito.JsonEncoderStringless)
        w_deser = json.loads(js_data, object_hook=Ito.json_decoder_stringless)
        self.assertNotEqual(w_orig, w_deser)
        w_deser._set_string(w_orig.string)
        self.assertListEqual([w_orig, *w_orig.children], [w_deser, *w_deser.children])
