from ._version import __version__
from segments.ito import Span, Ito, ChildItos, slice_indices_to_span
from segments.errors import Errors
del ito

import segments.itorator
import segments.xml
