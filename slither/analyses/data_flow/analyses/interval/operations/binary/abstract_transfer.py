"""Sound non-relational interval transfer for integer binary operations."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from slither.analyses.data_flow.analyses.interval.core.tracked_variable import NumericInterval
from slither.slithir.operations.binary import BinaryType


class AbstractTransferKind(Enum):
    """Precision class of one sound abstract operation result."""

    EXACT = "exact"
    INTERVAL = "interval"
    TOP = "top"


@dataclass(frozen=True)
class AbstractTransferResult:
    """One sound interval result and the reason for its precision."""

    interval: NumericInterval
    kind: AbstractTransferKind
    may_wrap: bool = False
    supported: bool = True


def transfer_binary_interval(
    operation: BinaryType,
    left: NumericInterval,
    right: NumericInterval,
    *,
    bit_width: int,
    is_signed: bool,
    is_checked: bool,
    same_operand: bool = False,
) -> AbstractTransferResult:
    """Return a conservative interval for one Solidity integer operation."""
    type_interval = NumericInterval.type_range(bit_width, is_signed)
    if operation is BinaryType.SUBTRACTION and same_operand:
        return _exact(0)
    if operation is BinaryType.DIVISION and same_operand:
        return _exact(1)
    if operation is BinaryType.MODULO and same_operand:
        return _exact(0)
    if operation in (BinaryType.AND, BinaryType.OR) and same_operand:
        return _interval_result(left, type_interval)
    if operation is BinaryType.CARET and same_operand:
        return _exact(0)

    if operation is BinaryType.ADDITION:
        raw = NumericInterval(left.lower + right.lower, left.upper + right.upper)
        return _finish_integer_arithmetic(raw, type_interval, bit_width, is_signed, is_checked)
    if operation is BinaryType.SUBTRACTION:
        raw = NumericInterval(left.lower - right.upper, left.upper - right.lower)
        return _finish_integer_arithmetic(raw, type_interval, bit_width, is_signed, is_checked)
    if operation is BinaryType.MULTIPLICATION:
        if same_operand:
            products = (left.lower * left.lower, left.upper * left.upper)
            raw = NumericInterval(
                0 if left.lower <= 0 <= left.upper else min(products),
                max(products),
            )
            return _finish_integer_arithmetic(
                raw, type_interval, bit_width, is_signed, is_checked
            )
        products = (
            left.lower * right.lower,
            left.lower * right.upper,
            left.upper * right.lower,
            left.upper * right.upper,
        )
        raw = NumericInterval(min(products), max(products))
        return _finish_integer_arithmetic(raw, type_interval, bit_width, is_signed, is_checked)
    if operation is BinaryType.DIVISION:
        return _division(left, right, type_interval)
    if operation is BinaryType.MODULO:
        return _modulo(left, right, type_interval, is_signed)
    if operation is BinaryType.POWER:
        return _power(
            left,
            right,
            type_interval,
            bit_width=bit_width,
            is_signed=is_signed,
            is_checked=is_checked,
        )
    if operation in (BinaryType.LEFT_SHIFT, BinaryType.RIGHT_SHIFT):
        return _shift(
            operation,
            left,
            right,
            type_interval,
            bit_width=bit_width,
            is_signed=is_signed,
        )
    if operation in (BinaryType.AND, BinaryType.OR, BinaryType.CARET):
        return _bitwise(
            operation,
            left,
            right,
            type_interval,
            bit_width=bit_width,
            is_signed=is_signed,
        )
    return _top(type_interval, supported=False)


def _finish_integer_arithmetic(
    raw: NumericInterval,
    type_interval: NumericInterval,
    bit_width: int,
    is_signed: bool,
    is_checked: bool,
) -> AbstractTransferResult:
    if _contains(type_interval, raw):
        return _interval_result(raw, type_interval)
    if is_checked:
        successful = raw.intersection(type_interval)
        if successful is None:
            # The interval domain has no operation-local bottom value. The checked
            # continuation facts retain infeasibility; top is the only sound value.
            return _top(type_interval)
        return _interval_result(successful, type_interval)
    if raw.lower == raw.upper:
        return AbstractTransferResult(
            NumericInterval(
                _wrap_and_decode(raw.lower, bit_width, is_signed),
                _wrap_and_decode(raw.lower, bit_width, is_signed),
            ),
            AbstractTransferKind.EXACT,
            may_wrap=True,
        )
    # A single interval cannot in general represent modular images without
    # becoming disjunctive. Top is sound and avoids an incorrect narrow hull.
    return _top(type_interval, may_wrap=True)


def _division(
    left: NumericInterval,
    right: NumericInterval,
    type_interval: NumericInterval,
) -> AbstractTransferResult:
    divisors = _nonzero_extreme_values(right)
    if not divisors:
        return _top(type_interval)
    dividends = {left.lower, left.upper}
    if left.lower <= 0 <= left.upper:
        dividends.add(0)
    values = [_truncating_division(a, b) for a in dividends for b in divisors]
    return _interval_result(NumericInterval(min(values), max(values)), type_interval)


def _modulo(
    left: NumericInterval,
    right: NumericInterval,
    type_interval: NumericInterval,
    is_signed: bool,
) -> AbstractTransferResult:
    divisors = _nonzero_extreme_values(right)
    if not divisors:
        return _top(type_interval)
    if left.lower == left.upper and right.lower == right.upper and right.lower != 0:
        quotient = _truncating_division(left.lower, right.lower)
        return _exact(left.lower - quotient * right.lower)
    max_divisor_magnitude = max(abs(value) for value in divisors)
    max_remainder_magnitude = min(
        max(abs(left.lower), abs(left.upper)),
        max_divisor_magnitude - 1,
    )
    if not is_signed:
        raw = NumericInterval(0, min(left.upper, max_remainder_magnitude))
    elif left.lower >= 0:
        raw = NumericInterval(0, min(left.upper, max_remainder_magnitude))
    elif left.upper <= 0:
        raw = NumericInterval(max(left.lower, -max_remainder_magnitude), 0)
    else:
        raw = NumericInterval(-max_remainder_magnitude, max_remainder_magnitude)
    return _interval_result(raw, type_interval)


def _power(
    base: NumericInterval,
    exponent: NumericInterval,
    type_interval: NumericInterval,
    *,
    bit_width: int,
    is_signed: bool,
    is_checked: bool,
) -> AbstractTransferResult:
    if exponent.lower < 0:
        return _top(type_interval, supported=False)
    if base.lower == base.upper and base.lower in (-1, 0, 1):
        return _small_base_power(base.lower, exponent, type_interval)
    if exponent.lower == exponent.upper:
        if exponent.lower > 1024:
            if base.lower == base.upper and not is_checked:
                wrapped = pow(base.lower, exponent.lower, 1 << bit_width)
                return _exact(_wrap_and_decode(wrapped, bit_width, is_signed))
            return _top(type_interval, supported=False)
        raw = _fixed_exponent_interval(base, exponent.lower)
        return _finish_integer_arithmetic(raw, type_interval, bit_width, is_signed, is_checked)
    # Bounded unsigned exponentiation is monotone in the common non-negative
    # case. Cap concrete endpoint evaluation to avoid constructing enormous
    # Python integers for an unconstrained uint256 exponent.
    if base.lower >= 0 and exponent.upper <= 1024:
        bases = {base.lower, base.upper}
        powers = {exponent.lower, exponent.upper}
        if base.lower <= 1 <= base.upper:
            bases.add(1)
        if exponent.lower <= 1 <= exponent.upper:
            powers.add(1)
        values = [pow(value, power) for value in bases for power in powers]
        raw = NumericInterval(min(values), max(values))
        return _finish_integer_arithmetic(raw, type_interval, bit_width, is_signed, is_checked)
    return _top(type_interval, supported=False)


def _small_base_power(
    base: int,
    exponent: NumericInterval,
    type_interval: NumericInterval,
) -> AbstractTransferResult:
    if base == 1:
        return _exact(1)
    if base == 0:
        return _exact(0) if exponent.lower > 0 else _interval_result(NumericInterval(0, 1), type_interval)
    if exponent.lower == exponent.upper:
        return _exact(-1 if exponent.lower % 2 else 1)
    return _interval_result(NumericInterval(-1, 1), type_interval)


def _fixed_exponent_interval(base: NumericInterval, exponent: int) -> NumericInterval:
    if exponent == 0:
        return NumericInterval(1, 1)
    if exponent % 2:
        return NumericInterval(pow(base.lower, exponent), pow(base.upper, exponent))
    maximum = max(pow(abs(base.lower), exponent), pow(abs(base.upper), exponent))
    minimum = 0 if base.lower <= 0 <= base.upper else min(
        pow(abs(base.lower), exponent),
        pow(abs(base.upper), exponent),
    )
    return NumericInterval(minimum, maximum)


def _shift(
    operation: BinaryType,
    left: NumericInterval,
    right: NumericInterval,
    type_interval: NumericInterval,
    *,
    bit_width: int,
    is_signed: bool,
) -> AbstractTransferResult:
    if right.lower < 0:
        return _top(type_interval, supported=False)
    shift_values = range(right.lower, min(right.upper, bit_width - 1) + 1)
    representative_shifts = list(shift_values)
    if right.upper >= bit_width:
        representative_shifts.append(bit_width)
    results = [
        _fixed_shift(
            operation,
            left,
            shift,
            type_interval,
            bit_width=bit_width,
            is_signed=is_signed,
        )
        for shift in representative_shifts
    ]
    if not results:
        return _top(type_interval)
    if any(result.kind is AbstractTransferKind.TOP for result in results):
        return _top(type_interval, may_wrap=operation is BinaryType.LEFT_SHIFT)
    interval = results[0].interval
    for result in results[1:]:
        interval = interval.hull(result.interval)
    combined = _interval_result(interval, type_interval)
    return AbstractTransferResult(
        combined.interval,
        combined.kind,
        may_wrap=any(result.may_wrap for result in results),
    )


def _fixed_shift(
    operation: BinaryType,
    left: NumericInterval,
    shift: int,
    type_interval: NumericInterval,
    *,
    bit_width: int,
    is_signed: bool,
) -> AbstractTransferResult:
    if operation is BinaryType.RIGHT_SHIFT:
        if shift >= bit_width:
            if not is_signed:
                return _exact(0)
            values = (-1 if left.lower < 0 else 0, -1 if left.upper < 0 else 0)
            return _interval_result(NumericInterval(min(values), max(values)), type_interval)
        raw = NumericInterval(left.lower >> shift, left.upper >> shift)
        return _interval_result(raw, type_interval)
    if shift >= bit_width:
        return _exact(0)
    raw = NumericInterval(left.lower << shift, left.upper << shift)
    # Solidity shifts truncate bits even in checked scopes.
    return _finish_integer_arithmetic(raw, type_interval, bit_width, is_signed, False)


def _bitwise(
    operation: BinaryType,
    left: NumericInterval,
    right: NumericInterval,
    type_interval: NumericInterval,
    *,
    bit_width: int,
    is_signed: bool,
) -> AbstractTransferResult:
    if left.lower == left.upper and right.lower == right.upper:
        left_bits = left.lower % (1 << bit_width)
        right_bits = right.lower % (1 << bit_width)
        if operation is BinaryType.AND:
            value = left_bits & right_bits
        elif operation is BinaryType.OR:
            value = left_bits | right_bits
        else:
            value = left_bits ^ right_bits
        return _exact(_wrap_and_decode(value, bit_width, is_signed))
    zero = NumericInterval(0, 0)
    if left == zero:
        return _exact(0) if operation is BinaryType.AND else _interval_result(right, type_interval)
    if right == zero:
        return _exact(0) if operation is BinaryType.AND else _interval_result(left, type_interval)
    if not is_signed or (left.lower >= 0 and right.lower >= 0):
        if operation is BinaryType.AND:
            raw = NumericInterval(0, min(left.upper, right.upper))
        else:
            highest = max(left.upper, right.upper).bit_length()
            raw = NumericInterval(0, (1 << highest) - 1 if highest else 0)
        return _interval_result(raw, type_interval)
    return _top(type_interval, supported=False)


def _nonzero_extreme_values(interval: NumericInterval) -> set[int]:
    values = {value for value in (interval.lower, interval.upper) if value != 0}
    if interval.lower <= -1 <= interval.upper:
        values.add(-1)
    if interval.lower <= 1 <= interval.upper:
        values.add(1)
    return values


def _truncating_division(left: int, right: int) -> int:
    quotient = abs(left) // abs(right)
    return -quotient if (left < 0) != (right < 0) else quotient


def _wrap_and_decode(value: int, bit_width: int, is_signed: bool) -> int:
    modulus = 1 << bit_width
    wrapped = value % modulus
    if is_signed and wrapped >= 1 << (bit_width - 1):
        wrapped -= modulus
    return wrapped


def _contains(outer: NumericInterval, inner: NumericInterval) -> bool:
    return outer.lower <= inner.lower and inner.upper <= outer.upper


def _interval_result(
    interval: NumericInterval,
    type_interval: NumericInterval,
) -> AbstractTransferResult:
    interval = interval.intersection(type_interval) or type_interval
    kind = AbstractTransferKind.EXACT if interval.lower == interval.upper else (
        AbstractTransferKind.TOP if interval == type_interval else AbstractTransferKind.INTERVAL
    )
    return AbstractTransferResult(interval, kind)


def _exact(value: int) -> AbstractTransferResult:
    return AbstractTransferResult(NumericInterval(value, value), AbstractTransferKind.EXACT)


def _top(
    type_interval: NumericInterval,
    *,
    may_wrap: bool = False,
    supported: bool = True,
) -> AbstractTransferResult:
    return AbstractTransferResult(
        type_interval,
        AbstractTransferKind.TOP,
        may_wrap=may_wrap,
        supported=supported,
    )
