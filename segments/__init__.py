from segments._version import __version__
del _version

from segments.errors import Errors
del errors

from segments.span import Span
del span

from segments.ito import Types, Ito, ChildItos
del ito

import segments.itorator
import segments.query
import segments._xml

del segments
