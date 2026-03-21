from . import models
from . import patch


def post_load():
    patch.apply()
