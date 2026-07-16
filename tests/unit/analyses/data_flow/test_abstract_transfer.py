"""Focused soundness tests for nonlinear abstract interval transfer."""

from __future__ import annotations

from collections.abc import Iterable

import pytest

from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    NumericInterval,
)
from slither.analyses.data_flow.analyses.interval.operations.binary.abstract_transfer import (
    AbstractTransferKind,
    transfer_binary_interval,
)
from slither.slithir.operations.binary import BinaryType


def _interval(lower: int, upper: int | None = None) -> NumericInterval:
    return NumericInterval(lower, lower if upper is None else upper)


def _all_intervals(values: Iterable[int]) -> tuple[NumericInterval, ...]:
    concrete = tuple(values)
    return tuple(
        NumericInterval(lower, upper)
        for lower in concrete
        for upper in concrete
        if lower <= upper
    )


def _decode_wrapped(value: int, bit_width: int, is_signed: bool) -> int:
    modulus = 1 << bit_width
    wrapped = value % modulus
    if is_signed and wrapped >= 1 << (bit_width - 1):
        wrapped -= modulus
    return wrapped


def _concrete_multiplication_results(
    left: NumericInterval,
    right: NumericInterval,
    *,
    bit_width: int,
    is_signed: bool,
    is_checked: bool,
) -> set[int]:
    type_interval = NumericInterval.type_range(bit_width, is_signed)
    results: set[int] = set()
    for left_value in range(left.lower, left.upper + 1):
        for right_value in range(right.lower, right.upper + 1):
            product = left_value * right_value
            if is_checked:
                if type_interval.lower <= product <= type_interval.upper:
                    results.add(product)
            else:
                results.add(_decode_wrapped(product, bit_width, is_signed))
    return results


@pytest.mark.parametrize("bit_width", [2, 3])
@pytest.mark.parametrize("is_signed", [False, True])
@pytest.mark.parametrize("is_checked", [False, True])
def test_multiplication_is_sound_for_every_small_width_interval(
    bit_width: int,
    is_signed: bool,
    is_checked: bool,
) -> None:
    """Every concrete successful product is contained in the abstract result."""
    type_interval = NumericInterval.type_range(bit_width, is_signed)
    intervals = _all_intervals(range(type_interval.lower, type_interval.upper + 1))

    for left in intervals:
        for right in intervals:
            result = transfer_binary_interval(
                BinaryType.MULTIPLICATION,
                left,
                right,
                bit_width=bit_width,
                is_signed=is_signed,
                is_checked=is_checked,
            )
            concrete = _concrete_multiplication_results(
                left,
                right,
                bit_width=bit_width,
                is_signed=is_signed,
                is_checked=is_checked,
            )

            assert type_interval.lower <= result.interval.lower
            assert result.interval.upper <= type_interval.upper
            assert result.supported
            assert all(
                result.interval.lower <= value <= result.interval.upper for value in concrete
            ), (left, right, result, concrete)
            if not concrete:
                # Operation-local bottom is deliberately represented by top; the
                # checked continuation facts retain the infeasibility information.
                assert result.interval == type_interval


@pytest.mark.parametrize(
    ("left", "right", "is_signed", "expected"),
    [
        (_interval(2, 4), _interval(3, 5), False, _interval(6, 20)),
        (_interval(-3, 4), _interval(-2, 5), True, _interval(-15, 20)),
        (_interval(5), _interval(10), False, _interval(50)),
    ],
)
def test_finite_checked_multiplication_is_algebraically_bounded(
    left: NumericInterval,
    right: NumericInterval,
    is_signed: bool,
    expected: NumericInterval,
) -> None:
    result = transfer_binary_interval(
        BinaryType.MULTIPLICATION,
        left,
        right,
        bit_width=8,
        is_signed=is_signed,
        is_checked=True,
    )

    assert result.interval == expected
    assert result.kind is (
        AbstractTransferKind.EXACT
        if expected.lower == expected.upper
        else AbstractTransferKind.INTERVAL
    )
    assert not result.may_wrap


def test_checked_multiplication_keeps_only_successful_nonoverflowing_values() -> None:
    result = transfer_binary_interval(
        BinaryType.MULTIPLICATION,
        _interval(100, 200),
        _interval(2, 3),
        bit_width=8,
        is_signed=False,
        is_checked=True,
    )

    assert result.interval == _interval(200, 255)
    assert result.kind is AbstractTransferKind.INTERVAL
    assert not result.may_wrap


def test_checked_signed_square_uses_same_operand_relation() -> None:
    result = transfer_binary_interval(
        BinaryType.MULTIPLICATION,
        _interval(-3, 4),
        _interval(-3, 4),
        bit_width=8,
        is_signed=True,
        is_checked=True,
        same_operand=True,
    )

    assert result.interval == _interval(0, 16)


def test_unchecked_signed_square_returns_top_when_wrapping_can_change_sign() -> None:
    result = transfer_binary_interval(
        BinaryType.MULTIPLICATION,
        _interval(-128, 127),
        _interval(-128, 127),
        bit_width=8,
        is_signed=True,
        is_checked=False,
        same_operand=True,
    )

    assert result.interval == _interval(-128, 127)
    assert result.kind is AbstractTransferKind.TOP
    assert result.may_wrap


def test_unchecked_multiplication_wraps_constants_and_tops_nonconvex_images() -> None:
    constant = transfer_binary_interval(
        BinaryType.MULTIPLICATION,
        _interval(200),
        _interval(2),
        bit_width=8,
        is_signed=False,
        is_checked=False,
    )
    wrapping = transfer_binary_interval(
        BinaryType.MULTIPLICATION,
        _interval(200, 255),
        _interval(2),
        bit_width=8,
        is_signed=False,
        is_checked=False,
    )
    unconstrained = transfer_binary_interval(
        BinaryType.MULTIPLICATION,
        _interval(0, 255),
        _interval(0, 255),
        bit_width=8,
        is_signed=False,
        is_checked=False,
    )

    assert constant.interval == _interval(144)
    assert constant.kind is AbstractTransferKind.EXACT
    assert constant.may_wrap
    assert wrapping.interval == unconstrained.interval == _interval(0, 255)
    assert wrapping.kind is unconstrained.kind is AbstractTransferKind.TOP
    assert wrapping.may_wrap and unconstrained.may_wrap


@pytest.mark.parametrize(
    ("operation", "left", "right", "is_signed", "expected"),
    [
        (BinaryType.DIVISION, _interval(10, 20), _interval(2, 5), False, _interval(2, 10)),
        (
            BinaryType.DIVISION,
            _interval(-20, 20),
            _interval(-5, -2),
            True,
            _interval(-10, 10),
        ),
        (BinaryType.MODULO, _interval(10, 20), _interval(3, 5), False, _interval(0, 4)),
        (BinaryType.MODULO, _interval(-20, -10), _interval(3, 5), True, _interval(-4, 0)),
        (BinaryType.MODULO, _interval(-7), _interval(3), True, _interval(-1)),
    ],
)
def test_division_and_modulo_representative_intervals(
    operation: BinaryType,
    left: NumericInterval,
    right: NumericInterval,
    is_signed: bool,
    expected: NumericInterval,
) -> None:
    result = transfer_binary_interval(
        operation,
        left,
        right,
        bit_width=8,
        is_signed=is_signed,
        is_checked=True,
    )

    assert result.interval == expected
    assert result.supported


@pytest.mark.parametrize(
    ("operation", "expected"),
    [
        (BinaryType.DIVISION, _interval(1)),
        (BinaryType.MODULO, _interval(0)),
        (BinaryType.AND, _interval(3, 9)),
        (BinaryType.OR, _interval(3, 9)),
        (BinaryType.CARET, _interval(0)),
    ],
)
def test_same_operand_identities(operation: BinaryType, expected: NumericInterval) -> None:
    result = transfer_binary_interval(
        operation,
        _interval(3, 9),
        _interval(3, 9),
        bit_width=8,
        is_signed=False,
        is_checked=True,
        same_operand=True,
    )

    assert result.interval == expected


def test_zero_only_divisor_conservatively_returns_top() -> None:
    result = transfer_binary_interval(
        BinaryType.DIVISION,
        _interval(1, 10),
        _interval(0),
        bit_width=8,
        is_signed=False,
        is_checked=True,
    )

    assert result.interval == _interval(0, 255)
    assert result.kind is AbstractTransferKind.TOP


@pytest.mark.parametrize(
    "case",
    [
        (_interval(2, 3), _interval(2), 8, False, True, _interval(4, 9)),
        (_interval(-3, 2), _interval(2), 8, True, True, _interval(0, 9)),
        (_interval(2, 3), _interval(2, 3), 8, False, True, _interval(4, 27)),
        (_interval(0), _interval(0, 3), 8, False, True, _interval(0, 1)),
        (_interval(20), _interval(2), 8, False, False, _interval(144)),
    ],
)
def test_power_representative_intervals(
    case: tuple[NumericInterval, NumericInterval, int, bool, bool, NumericInterval],
) -> None:
    base, exponent, bit_width, is_signed, is_checked, expected = case
    result = transfer_binary_interval(
        BinaryType.POWER,
        base,
        exponent,
        bit_width=bit_width,
        is_signed=is_signed,
        is_checked=is_checked,
    )

    assert result.interval == expected


def test_unbounded_power_is_tagged_unsupported_top() -> None:
    result = transfer_binary_interval(
        BinaryType.POWER,
        _interval(2, 3),
        _interval(0, 2048),
        bit_width=16,
        is_signed=False,
        is_checked=True,
    )

    assert result.interval == _interval(0, (1 << 16) - 1)
    assert result.kind is AbstractTransferKind.TOP
    assert not result.supported


@pytest.mark.parametrize(
    ("operation", "left", "right", "is_signed", "expected"),
    [
        (BinaryType.LEFT_SHIFT, _interval(1, 3), _interval(1), False, _interval(2, 6)),
        (BinaryType.RIGHT_SHIFT, _interval(8, 16), _interval(1, 2), False, _interval(2, 8)),
        (BinaryType.RIGHT_SHIFT, _interval(-8, -1), _interval(1), True, _interval(-4, -1)),
        (BinaryType.RIGHT_SHIFT, _interval(-8, 7), _interval(8), True, _interval(-1, 0)),
    ],
)
def test_shift_representative_intervals(
    operation: BinaryType,
    left: NumericInterval,
    right: NumericInterval,
    is_signed: bool,
    expected: NumericInterval,
) -> None:
    result = transfer_binary_interval(
        operation,
        left,
        right,
        bit_width=8,
        is_signed=is_signed,
        is_checked=True,
    )

    assert result.interval == expected


def test_left_shift_wraps_constants_and_tops_nonconvex_images() -> None:
    constant = transfer_binary_interval(
        BinaryType.LEFT_SHIFT,
        _interval(200),
        _interval(1),
        bit_width=8,
        is_signed=False,
        is_checked=True,
    )
    interval = transfer_binary_interval(
        BinaryType.LEFT_SHIFT,
        _interval(100, 200),
        _interval(1),
        bit_width=8,
        is_signed=False,
        is_checked=True,
    )

    assert constant.interval == _interval(144)
    assert constant.kind is AbstractTransferKind.EXACT
    assert constant.may_wrap
    assert interval.interval == _interval(0, 255)
    assert interval.kind is AbstractTransferKind.TOP
    assert interval.may_wrap


@pytest.mark.parametrize(
    ("operation", "left", "right", "expected"),
    [
        (BinaryType.AND, _interval(0b1010), _interval(0b1100), _interval(0b1000)),
        (BinaryType.OR, _interval(0b1010), _interval(0b0101), _interval(0b1111)),
        (BinaryType.CARET, _interval(0b1010), _interval(0b1100), _interval(0b0110)),
        (BinaryType.AND, _interval(0, 15), _interval(0, 3), _interval(0, 3)),
        (BinaryType.OR, _interval(1, 2), _interval(4), _interval(0, 7)),
    ],
)
def test_bitwise_representative_intervals(
    operation: BinaryType,
    left: NumericInterval,
    right: NumericInterval,
    expected: NumericInterval,
) -> None:
    result = transfer_binary_interval(
        operation,
        left,
        right,
        bit_width=8,
        is_signed=False,
        is_checked=True,
    )

    assert result.interval == expected
    assert result.supported


@pytest.mark.parametrize("operation", [BinaryType.AND, BinaryType.OR, BinaryType.CARET])
def test_nonconstant_signed_bitwise_conservatively_returns_unsupported_top(
    operation: BinaryType,
) -> None:
    result = transfer_binary_interval(
        operation,
        _interval(-8, 3),
        _interval(-2, 5),
        bit_width=8,
        is_signed=True,
        is_checked=True,
    )

    assert result.interval == _interval(-128, 127)
    assert result.kind is AbstractTransferKind.TOP
    assert not result.supported


def test_unhandled_binary_operation_conservatively_returns_unsupported_top() -> None:
    result = transfer_binary_interval(
        BinaryType.LESS,
        _interval(1, 3),
        _interval(2, 4),
        bit_width=8,
        is_signed=False,
        is_checked=True,
    )

    assert result.interval == _interval(0, 255)
    assert result.kind is AbstractTransferKind.TOP
    assert not result.supported
