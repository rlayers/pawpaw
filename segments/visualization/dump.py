import segments


class ItoDump:
    def __init__(self, indent: str = '  ', substring: bool = False):
        self.indent = indent
        self.substring = substring

    def _dump(self, ei: segments.Types.C_EITO, level: int = 0):
        print(f'{self.indent * level}{ei.index:,}: .span={ei.ito.span} .desc=\'{ei.ito.desc}\'', end='')
        if self.substring:
            print(f' .__str__(): \'{ei.ito}\'', end='')
        print()

    def dump(self, *itos: segments.Types.C_ITO):
        counter = 0
        for ei in (segments.Types.C_EITO(i, ito) for i, ito in enumerate(itos)):
            self._dump(ei, counter)
            counter += 1
            for d_count, d_ei in enumerate(ei.ito.walk_descendants_levels(start=1), start=counter):
                self._dump(segments.Types.C_EITO(d_count, d_ei.ito), level=d_ei.index)
