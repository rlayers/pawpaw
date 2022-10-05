from segments._version import __version__
del _version

from segments.ito import Span, Ito, ChildItos, slice_indices_to_span
del ito

from segments.errors import Errors
del errors

import segments.itorator
import segments.xml

del segments
