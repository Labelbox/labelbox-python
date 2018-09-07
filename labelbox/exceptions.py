"""
Exception classes for the labelbox python package.
"""


class UnknownFormatError(Exception):
    """Exception raised for unknown label_format"""

    def __init__(self, label_format):
        Exception.__init__(self)
        self.message = "Provided label_format '{}' is unsupported".format(label_format)
