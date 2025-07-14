import sys
import os
import json
from datetime import datetime, timezone, timedelta

SRC_PATH = './src'
YAHOO_API_KEY = os.environ.get('YAHOO_API_KEY')

if SRC_PATH not in sys.path:
    sys.path.append(SRC_PATH)

from src.modules.values import bounding_box, coordinate
from src.modules.rain_data import RainData
from src.core.logger import get_logger

logger = get_logger(__name__)


def main():
    pass

if __name__ == "__main__":
    main()

