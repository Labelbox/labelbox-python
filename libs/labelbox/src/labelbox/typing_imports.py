"""
This module imports types that differ across python versions, so other modules 
don't have to worry about where they should be imported from.
"""

import sys
if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated