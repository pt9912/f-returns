# SPDX-License-Identifier: MIT
# rolling_returns/exceptions.py
"""Projektweite, typisierte Exceptions für rolling_returns.

Diese Exceptions sind für die Library-Schicht gedacht. Die CLI fängt sie ab
und mappt sie auf Exit-Codes.
"""


class RollingReturnsError(Exception):
    """Basisklasse für domänenspezifische Fehler."""


class DataLoadError(RollingReturnsError):
    """Quell-/Eingabedaten konnten nicht geladen oder waren leer."""


class InvalidInputError(RollingReturnsError):
    """Ungültige, widersprüchliche oder fehlende Benutzereingaben."""
