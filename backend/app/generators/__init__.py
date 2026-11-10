"""Generator registry. Import every generator module here so its @register calls run."""
from . import common, litteral, pythagore, vocab  # noqa: F401
from .base import GENERATORS, GenContext, Generated

__all__ = ["GENERATORS", "GenContext", "Generated"]
