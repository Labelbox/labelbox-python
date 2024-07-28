"""
This module imports types that differ across python versions, so other modules 
don't have to worry about where they should be imported from.
"""

import sys
if sys.version_info >= (3, 8):
    pass
else:
    pass