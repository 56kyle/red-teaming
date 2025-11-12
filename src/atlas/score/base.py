"""Module containing the abstract base that atlas compatible scorers will derive from."""
from abc import ABC

from pyrit.score import Scorer


class AtlasScorer(Scorer, ABC):
    """Base class for atlas compatible scorers."""
