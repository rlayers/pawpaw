from __future__ import annotations
import json
import typing

from pawpaw import Ito, Types
from pawpaw.arborform import Itorator

# {
#     'vehicle':
#     {
#        'car':
#        {
#            'Ford': itor,
#            'Chevy': itor,
#        }
#        'plane':
#        {
#            'Beechcraft': itor,
#            'Cessna': itor,
#        }
#    }
# }


# r'\[vehicle/plane]|[vehicle/car/ford\]){1,3}
# r'\[(?:vehicle/plane|vehicle/car/ford)\]{1,3}

# r'\[(?:/vehicle/plane|ford)\]{1,3}  'startswith '/' -> root anchored; otherwise root or sub-path

# r'\[(?:/vehicle/plane|ford/pinto)\]{1,3}



# r'\[(?:/vehicle/plane|ford/pinto)\]{1,3}


# full_path: /vehicle/car/ford/pinto/

# Full anchors
# /vehicle/car/ford/pinto/
# /vehicle/car/ford/pinto/
# r'(/vehicle/car/ford/pinto/)

# Start anchor only
# /vehicle/car:
# /vehicle/car[/a/b/c...]/
# r'(/vehicle/car   (?:/[^\)]+)*   /   )
 
# End anchor only
# ford/pinto/:
# /[a/b/c/...]ford/pinto/
# r'(   /   ([^\)]+/)*   ford/pinto/   )


# No anchors
# ford/pinto:
# /[a/b/c/...]ford/pinto[/a/b/c...]
# r'(   /   ([^\)]+/)*   ford/pinto   (?:/[^\)]+)*   /   )



# r'\(    (?:[^\)]+/)*   ford/pinto    (?:/[^\)]+)*    )

# /vehicle/ford/pinto:
# r'\(/vehicle/ford/pinto    (?:/[^\)]+)*     )

C_RULE = Itorator | Types.F_ITO_2_IT_ITOS
C_RULES = dict[str, C_RULE]
C_PATH = typing.Sequence[str]

class Discoveries(dict):
    def __init__(self, *args, **kwargs):
        self._itos: list[Ito] = list(kwargs.pop('itos', tuple()))
        dict.__init__(self, *args, **kwargs )

    @property
    def itos(self) -> list[Ito]:
        return self._itos   
    
    def __str__(self):
        c = ', '.join(f'{k}: {str(v)}' for k, v in self.items())
        return f'{{itos: {self._itos}, {c}}}'   

class Ontology(dict):
    def __getitem__(self, key: int | C_PATH | slice) -> Ontology:
        if isinstance(key, typing.Sequence):
            lk = len(key)
            if lk == 0:
                return self
            
            rv = super()[str(key[0])]
            if lk == 1:
                return rv
            else:
                return rv[key[1:]]

        return super().__getitem__(key)
    
    def __init__(self, *args, **kwargs):
        self._rules: list[C_RULE] = kwargs.pop('rules', [])
        dict.__init__(self, *args, **kwargs )

    @property
    def rules(self) -> list[C_RULE]:
        return self._rules

    def __str__(self):
        c = ', '.join(f'{k}: {str(v)}' for k, v in self.items())
        return f'{{rules: {self._rules}, {c}}}'   
    
    def discover(self, *itos: Ito) -> Discoveries:
        rv = Discoveries()

        for rule in self._rules:
            for i in itos:
                rv.itos.extend(rule(i))

        for k, v in self.items():
            rv[k] = v.discover(*itos)

        return rv    
    
# class Ontology(dict):
#     def __getitem__(self, key: int | slice) -> typing.Union[Ontology, C_RULES]:
#         if isinstance(key, typing.Sequence):
#             lk = len(key)
#             if lk == 0:
#                 return self
            
#             rv = super()[str(key[0])]
#             if lk == 1:
#                 return rv
#             else:
#                 return rv[key[1:]]

#         return super().__getitem__(key)
    
#     def discover_flat(self, *itos: Ito, grow_leaves: bool = False, include_empties: bool = False) -> C_DISCOVERIES_FLAT:
#         rv: C_DISCOVERIES_FLAT = {}

#         for k, v in self.items():
#             if isinstance(v, Itorator):
#                 results = []
#                 for i in itos:
#                     results.extend(v(i))
#                 if include_empties or len(results) > 0:
#                     rv[(k,)] = results
#             else:
#                 for s_path, s_itos in self.discover_flat(v, *itos, include_empties=include_empties).items():
#                     rv[(k, *s_path)] = s_itos

#         return rv

#     def discover_dict(self, *itos: Ito, include_empties: bool = False) -> C_DISCOVERIES_DICT:
#         rv: C_DISCOVERIES_DICT = {}

#         for k, v in self.items():
#             if isinstance(v, Itorator):
#                 results = []
#                 for i in itos:
#                     results.extend(v(i))
#                 if include_empties or len(results) > 0:
#                     rv[k] = results
#             else:
#                 sub = self.discover_dict(v, *itos, include_empties=include_empties)
#                 if include_empties or len(sub) > 0:
#                     rv[k] = sub

#         return rv

# # to_path(??) -> str:
# #   return 'vehicle/car/Ford'

# PATH_SEPARATOR = '/'
# def by_path_str(ontology, path: str) -> C_RULES | Ontology:
#     rv = ontology
#     for p in path.split(PATH_SEPARATOR):
#         rv = rv[p]
#     return rv

# from pawpaw.arborform import Extract
# import regex
# ont = Ontology({
#     'vehicle': Ontology({
#         'car': {'Ford': Extract(regex.compile(r'(?P<F150>F\-150)', regex.IGNORECASE)) },
#         'cessna': {'Skyhawk': Extract(regex.compile(r'(?P<Skyhawk>Cessna\s172\s(?:Skyhawk)?)', regex.IGNORECASE)) },
#     })
# })

# itos = [Ito('John loves to drive his F-150.')]
# discoveries = ont.discover_flat(ont, *itos, include_empties=True)
# print(discoveries)
# print()

# import json  # used for pretty-print
# discoveries = ont.discover_dict(ont, *itos, include_empties=True)
# print(json.dumps(discoveries, cls=Ito.JsonEncoderStringless, indent=4))
# print()

from pawpaw.arborform import Extract
import regex

ont = Ontology()
print(ont)
ont = Ontology({'a': Ontology()}, rules=[Extract(regex.compile(r'abc'))])
print(ont)
ont = Ontology({'a': Ontology()}, rules=[Extract(regex.compile(r'abc'))], b=Ontology())
print(ont)
ont = Ontology({'a': Ontology(), 'rules': Ontology()}, rules=[Extract(regex.compile(r'abc'))], b=Ontology())
print(ont)

exit(0)

ont = Ontology(
    {
        'vehicle': Ontology(
            {
                'car': Ontology(
                    {
                        'Ford': Ontology(
                            rules=[Extract(regex.compile(r'(?P<F150>F\-150)', regex.IGNORECASE))]
                        )
                    }
                ),
                'cessna': Ontology(
                    {
                        'Skyhawk': Ontology(
                            rules=[Extract(regex.compile(r'(?P<Skyhawk>Cessna\s172(?:\sSkyhawk)?)', regex.IGNORECASE))]
                        )
                    }
                ),
            }
        )
    }
)

itos = [Ito('John loves to drive his F-150 more than his Cessna 172.')]
discoveries = ont.discover(*itos)
print(discoveries)
print()