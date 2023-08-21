import typing

import regex
import pawpaw
from pawpaw.ontology import Ontology
from tests.util import _TestIto


class TestOntology(_TestIto):
    def setUp(self) -> None:
        super().setUp()

        self.ito = pawpaw.Ito('The vehicle John loves to drive most is his F-150, not his Cessna 172.')

        self.ontology = Ontology(
            {
                'vehicle': Ontology(
                    {
                        'car': Ontology(
                            {
                                'Ford': Ontology(
                                    rules=[pawpaw.arborform.Extract(regex.compile(r'(?P<F150>F\-150)', regex.IGNORECASE))]
                                )
                            }
                        ),
                        'airplane': Ontology(
                            {
                                'Cessna': Ontology(
                                    rules=[pawpaw.arborform.Extract(regex.compile(r'(?P<Skyhawk>Cessna\s172(?:\sSkyhawk)?)', regex.IGNORECASE))]
                                )
                            }
                        ),                        
                    },
                    rules=[pawpaw.arborform.Extract(regex.compile(r'(?P<vehicle>vehicles?)', regex.IGNORECASE))]
                )
            }
        )

    def test_ctor(self):
        for rules in [], [pawpaw.arborform.Extract(regex.compile(r'abc'))]:
            for items in {}, {'a': Ontology()}, {'a': Ontology(), 'rules': Ontology()}:
                for b in None, Ontology():
                    with self.subTest(rules=rules, items=items, b=b):
                        args = []
                        if len(items) > 0:
                            args.append(items)
                        
                        kwargs = {}
                        if b is not None:
                            kwargs['b'] = b
                        items_expected = (items | kwargs).items()
                        
                        if len(rules) > 0:
                            kwargs['rules'] = rules
                        
                        ont = Ontology(*args, **kwargs)
                        
                        self.assertSequenceEqual(items_expected, ont.items())
                        self.assertSequenceEqual(rules, ont.rules)

    def test_path_index_access(self):
        paths = [
            ('vehicle', ),
            ('vehicle', 'car'),
            ('vehicle', 'car', 'Ford'),
            ('vehicle', 'airplane', 'Cessna'),
        ]
        for path in paths:
            with self.subTest(path=path):
                expected = self.ontology
                for s in path:
                    expected = expected[s]
                self.assertIs(expected, self.ontology[path])

    def test_discover(self):
        discoveries = self.ontology.discover(self.ito)

        vehicles = [*self.ontology['vehicle'].rules[0](self.ito)]
        self.assertLess(0, len(vehicles))
        self.assertSequenceEqual(vehicles, discoveries['vehicle'].itos)

        fords = [*self.ontology['vehicle']['car']['Ford'].rules[0](self.ito)]
        self.assertLess(0, len(fords))
        self.assertSequenceEqual(fords, discoveries['vehicle']['car']['Ford'].itos)

        cessnas = [*self.ontology['vehicle']['airplane']['Cessna'].rules[0](self.ito)]
        self.assertLess(0, len(cessnas))
        self.assertSequenceEqual(cessnas, discoveries['vehicle']['airplane']['Cessna'].itos)
