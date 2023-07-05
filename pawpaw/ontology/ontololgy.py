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


C_RULES = dict[str, Itorator]
C_PATH = typing.Sequence[str]

class Ontology(dict):
    def __getitem__(self, key: int | slice) -> typing.Union[Ontology, C_RULES]:
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

C_PATH = tuple[str]
C_DISCOVERIES = dict[C_PATH, list[Ito]]

def discover_flat(ontology: Ontology, *itos: Ito, include_empties: bool = False) -> C_DISCOVERIES:
    rv: C_DISCOVERIES = {}

    for k, v in ontology.items():
        if isinstance(v, Itorator):
            results = []
            for i in itos:
                results.extend(v(i))
            if include_empties or len(results) > 0:
                rv[(k,)] = results
        else:
            for s_path, s_itos in discover_flat(v, *itos, include_empties=include_empties).items():
                rv[(k, *s_path)] = s_itos

    return rv

def discover_dict(ontology: Ontology, *itos: Ito, include_empties: bool = False) -> C_DISCOVERIES:
    rv: C_DISCOVERIES = {}

    for k, v in ontology.items():
        if isinstance(v, Itorator):
            results = []
            for i in itos:
                results.extend(v(i))
            if include_empties or len(results) > 0:
                rv[k] = results
        else:
            sub = discover_dict(v, *itos, include_empties=include_empties)
            if include_empties or len(sub) > 0:
                rv[k] = sub

    return rv

# to_path(??) -> str:
#   return 'vehicle/car/Ford'

PATH_SEPARATOR = '/'
def by_path_str(ontology, path: str) -> C_RULES | Ontology:
    rv = ontology
    for p in path.split(PATH_SEPARATOR):
        rv = rv[p]
    return rv



from pawpaw.arborform import Extract
import regex
ont = Ontology({
    'vehicle': Ontology({
        'car': {'Ford': Extract(regex.compile(r'(?P<F150>F\-150)', regex.IGNORECASE)) },
        'cessna': {'Skyhawk': Extract(regex.compile(r'(?P<Skyhawk>Cessna\s172\s(?:Skyhawk)?)', regex.IGNORECASE)) },
    })
})

itos = [Ito('John loves to drive his F-150.')]
discoveries = discover_flat(ont, *itos, include_empties=True)
print(discoveries)
print()

import json  # used for pretty-print
discoveries = discover_dict(ont, *itos, include_empties=True)
print(json.dumps(discoveries, cls=Ito.JsonEncoderStringless, indent=4))
print()