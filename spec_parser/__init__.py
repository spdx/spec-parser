import logging
from .helper import addErrorFilter

logging.basicConfig(format="%(levelname)-8s: %(message)s")
logger = logging.getLogger()
addErrorFilter(logger)

from .__version__ import *
from .spec_parser import *
from .helper import *
from .parser import *
from .config import *
