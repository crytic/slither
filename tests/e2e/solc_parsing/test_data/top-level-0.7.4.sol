uint constant EXPONENT = 10;
uint constant MULTIPLIER = 2**EXPONENT;

struct Fixed { uint value; }

function toFixed(uint x) pure returns (Fixed memory ret) {
    ret.value = x * MULTIPLIER;
}
