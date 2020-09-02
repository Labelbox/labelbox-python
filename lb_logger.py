import logging
"""
Instantiates a logger object with level set to INFO

This will be used in all other files as the default logger object
"""

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)