import itertools
import typing

import regex
import pawpaw
from pawpaw.ontology import Ontology
from tests.util import _TestIto


class TestOntology(_TestIto):
    def setUp(self) -> None:
        super().setUp()

        self.ontology = Ontology(
            {
                'vehicle': Ontology(
                    {
                        'car': Ontology(
                            {
                                'Ford': Ontology(
                                    rules=[
                                        pawpaw.arborform.Extract(
                                            regex.compile(
                                                r'(?P<Mustang>(?:Ford\s+)?Mustang(?:(?:-|\s+)\L<subtypes>)?)',
                                                regex.IGNORECASE | regex.DOTALL,
                                                subtypes=['EcoBoost', 'LX', 'GT', 'GT350', 'GT500', 'Mach-E', 'Dark Horse']
                                            )
                                        ),
                                        pawpaw.arborform.Extract(
                                            regex.compile(
                                                r'(?P<F_Series>F(?:ord)?-(?:150(?:\s+Lightningt)?|[3-7]50|600))',
                                                regex.IGNORECASE | regex.DOTALL
                                            )
                                        ),
                                    ]
                                )
                            }
                        ),
                        'airplane': Ontology(
                            {
                                'Cessna': Ontology(
                                    rules=[
                                        pawpaw.arborform.Extract(
                                            regex.compile(
                                                r'(?P<Skyhawk>Cessna\s+172(?:\s+Skyhawk)?|(?:Cessna\s+)?172\s+Skyhawk)',
                                                regex.IGNORECASE | regex.DOTALL
                                            )
                                        ),
                                        pawpaw.arborform.Extract(
                                            regex.compile(
                                                r'(?P<Skylane>Cessna\s+182(?:\s+Skylane)?|(?:Cessna\s+)?182\s+Skylane)',
                                                regex.IGNORECASE | regex.DOTALL
                                            )
                                        ),
                                        pawpaw.arborform.Extract(
                                            regex.compile(
                                                r'(?P<Stationair>Cessna\s+206(?:\s+Stationair)?|(?:Cessna\s+)?206\s+Stationair)',
                                                regex.IGNORECASE | regex.DOTALL
                                            )
                                        ),
                                        pawpaw.arborform.Extract(
                                            regex.compile(
                                                r'(?P<Caravan>Cessna\s+208(?:\s+Caravan)?|(?:Cessna\s+)?208\s+Caravan)',
                                                regex.IGNORECASE | regex.DOTALL
                                            )
                                        ),
                                    ]
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
        s = 'The vehicle John loves to drive most is his F-150, not his Cessna 172.'
        ito = pawpaw.Ito(s)

        discoveries = self.ontology.discover(ito)

        vehicles = [*itertools.chain.from_iterable(rule(ito) for rule in self.ontology['vehicle'].rules)]
        self.assertLess(0, len(vehicles))
        self.assertSequenceEqual(vehicles, discoveries['vehicle'].itos)

        fords = [*itertools.chain.from_iterable(rule(ito) for rule in self.ontology['vehicle']['car']['Ford'].rules)]
        self.assertLess(0, len(fords))
        self.assertSequenceEqual(fords, discoveries['vehicle']['car']['Ford'].itos)

        cessnas = [*itertools.chain.from_iterable(rule(ito) for rule in self.ontology['vehicle']['airplane']['Cessna'].rules)]
        self.assertLess(0, len(cessnas))
        self.assertSequenceEqual(cessnas, discoveries['vehicle']['airplane']['Cessna'].itos)
