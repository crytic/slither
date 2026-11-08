from fractions import Fraction

import pytest

from slither.utils.integer_conversion import convert_string_to_fraction


@pytest.mark.parametrize(
    ("literal", "expected"),
    [
        ("1e-1", Fraction(1, 10)),
        ("3E-2", Fraction(3, 100)),
        ("1.25e-2", Fraction(1, 80)),
        ("1e-324", Fraction(1, 10**324)),
        ("0e-400", Fraction(0)),
        ("12e2", Fraction(1200)),
    ],
)
def test_scientific_notation_is_exact(literal, expected):
    assert convert_string_to_fraction(literal) == expected
