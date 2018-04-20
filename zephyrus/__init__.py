# -*- coding: utf-8 -*-

"""Top-level package for zephyrus."""

__author__ = """Wairton de Abreu Rebouças"""
__email__ = 'wairtonjr@gmail.com'
__version__ = '0.5.0'


import logging
# log_format = "%(created)s"
# %(created)f
# FORMAT = '%(asctime)-15s %(message)s'
FORMAT = '%(created)f %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)
