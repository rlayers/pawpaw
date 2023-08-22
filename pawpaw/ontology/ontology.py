from __future__ import annotations
import json
import typing

from pawpaw import Ito, Types
from pawpaw.arborform import Itorator

C_RULE = Itorator | Types.F_ITO_2_IT_ITOS
C_RULES = dict[str, C_RULE]
C_PATH = typing.Sequence[str]

class Discoveries(dict):
    mathematical_white_square_brackets = {
        'LEFT': '\u27E6',   # ⟦
        'RIGHT': '\u27E7',  # ⟧
    }

    def __init__(self, *args, **kwargs):
        self._itos: list[Ito] = list(kwargs.pop('itos', tuple()))
        dict.__init__(self, *args, **kwargs )

    @property
    def itos(self) -> list[Ito]:
        return self._itos   
    
    def __str__(self):
        c = ', '.join(f'{k}: {str(v)}' for k, v in self.items())
        return f'{{itos: {[str(i) for i in self._itos]}, {c}}}'
    
    def transform(
        self, 
        entity_start_char: str = mathematical_white_square_brackets.LEFT,
        entity_stop_char: str = mathematical_white_square_brackets.RIGHT
    ) -> str:
        raise NotImplemented()
        

class Ontology(dict):
    def __missing__(self, key):
        if isinstance(key, typing.Sequence) and (lk := len(key)) > 0 and not isinstance(key, str):
            rv = self[key[0]]
            if lk > 1:
                rv = rv[key[1:]]
            return rv
        else:
            raise KeyError(key)

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

    def discover_flat(self, *itos: Ito) -> dict[C_PATH, list[Ito]]:
        rv: dict[C_PATH, list[Ito]] = {}

        for v in self.rules:
            for i in itos:
                rv[tuple()] = [*v(i)]

        for k, v in self.items():
            d = {(k, *sk): sv for sk, sv in v.discover_flat(*itos).items()}
            rv |= d

        return rv
