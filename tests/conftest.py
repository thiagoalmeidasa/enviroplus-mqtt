"""Stub Enviro+ hardware modules so the source under `src/` can be
imported on a non-Pi development machine."""

import sys
import types
from unittest.mock import MagicMock


def _register(name: str, **attrs) -> types.ModuleType:
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


# bme280: src/logger.py does `from bme280 import BME280`.
_register("bme280", BME280=MagicMock())

# ltr559: src/logger.py runs `from ltr559 import LTR559; ltr559 = LTR559()`
# at import time, so LTR559 must be callable and the returned object must
# expose at least get_proximity / get_lux for any later call paths.
_register("ltr559", LTR559=MagicMock(return_value=MagicMock()))

# enviroplus.gas: `from enviroplus import gas`.
_register("enviroplus")
_register("enviroplus.gas", read_all=MagicMock())
sys.modules["enviroplus"].gas = sys.modules["enviroplus.gas"]

# pms5003: `from pms5003 import PMS5003`.
_register("pms5003", PMS5003=MagicMock())

# ST7735: `import ST7735` then `ST7735.ST7735(...)`.
_register("ST7735", ST7735=MagicMock())

# fonts.ttf: `from fonts.ttf import RobotoMedium`.
_register("fonts")
_register("fonts.ttf", RobotoMedium=MagicMock())
sys.modules["fonts"].ttf = sys.modules["fonts.ttf"]

# PIL: `from PIL import Image, ImageDraw, ImageFont`. Pillow isn't a
# default dependency on macOS (it sits in the `device` extra), so stub it.
_register("PIL", Image=MagicMock(), ImageDraw=MagicMock(), ImageFont=MagicMock())
_register("PIL.Image")
_register("PIL.ImageDraw")
_register("PIL.ImageFont")
