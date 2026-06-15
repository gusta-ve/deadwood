"""Importing this package registers every level (each module self-registers via
the @register decorator)."""

from deadwood.levels import (  # noqa: F401
    l01_first_blood,
    l02_whispers,
    l03_the_telegraph,
    l04_back_door,
)
