---
slug: bit-manipulation
title: Bit Manipulation
icon: 🔢
level: Beginner
order: 4
desc: Bitwise operators, masks, shifts, counting bits, powers of two and the classic whiteboard puzzles.
---
Bit manipulation questions are short, easy to grade, and show up in nearly every firmware interview. Know the operators cold and be ready to write each answer in one or two lines.

### What are the bitwise operators in C? {E}
| Operator | Name | Example (`a=0b1100`, `b=0b1010`) |
|---|---|---|
| `&` | AND | `0b1000` |
| &#124; | OR | `0b1110` |
| `^` | XOR | `0b0110` |
| `~` | NOT | inverts every bit |
| `<<` | left shift | `a << 1 = 0b11000` |
| `>>` | right shift | `a >> 2 = 0b0011` |

Do not confuse them with the logical operators `&&`, `||` and `!`, which produce 0 or 1 and short-circuit.

### Is right shift of a negative number arithmetic or logical? {M}
For unsigned types, `>>` is always a logical shift (fills with zeros). For a negative signed value the result is **implementation-defined**. GCC, Clang and Arm compilers perform an arithmetic shift (copying the sign bit), but portable code should not rely on it. Left-shifting a negative value, or shifting a 1 into the sign bit of a signed int, is undefined until C23 tidied some of it up. Do bit work on unsigned types.

### How do you check if a number is a power of two? {E}
```c
bool is_pow2(uint32_t x) { return x && !(x & (x - 1)); }
```

A power of two has exactly one bit set. Subtracting 1 clears that bit and sets all lower bits, so the AND is zero. The `x &&` excludes zero.

### How do you count the set bits in an integer? {M}
Brian Kernighan's method loops once per set bit, because `x & (x - 1)` clears the lowest set bit:

```c
unsigned popcount(uint32_t x)
{
    unsigned n = 0;
    while (x) { x &= x - 1; n++; }
    return n;
}
```

Constant-time SWAR version:

```c
x = x - ((x >> 1) & 0x55555555u);
x = (x & 0x33333333u) + ((x >> 2) & 0x33333333u);
x = (x + (x >> 4)) & 0x0F0F0F0Fu;
return (x * 0x01010101u) >> 24;
```

In production use `__builtin_popcount`.

### How do you swap two numbers without a temporary variable? {E}
```c
a ^= b;
b ^= a;
a ^= b;
```

It fails if `a` and `b` are the same object (both become 0), so guard with `if (&a != &b)`. In real code a temporary is clearer and just as fast; this is an interview trick.

### How do you find the position of the lowest set bit? {M}
`x & -x` (or `x & (~x + 1)`) isolates the lowest set bit. Its position is the count of trailing zeros: `__builtin_ctz(x)` (undefined for `x == 0`). On ARM, `ctz` is `RBIT` followed by `CLZ`. To find the highest set bit use `31 - __builtin_clz(x)`.

### How do you reverse the bits of a 32-bit integer? {M}
Swap progressively larger groups:

```c
uint32_t reverse_bits(uint32_t x)
{
    x = ((x >> 1) & 0x55555555u) | ((x & 0x55555555u) << 1);
    x = ((x >> 2) & 0x33333333u) | ((x & 0x33333333u) << 2);
    x = ((x >> 4) & 0x0F0F0F0Fu) | ((x & 0x0F0F0F0Fu) << 4);
    x = ((x >> 8) & 0x00FF00FFu) | ((x & 0x00FF00FFu) << 8);
    return (x >> 16) | (x << 16);
}
```

On ARMv7-M this is a single `RBIT` instruction (`__RBIT()` in CMSIS).

### How do you extract or insert a bit field? {E}
```c
#define FIELD_GET(reg, shift, width)  (((reg) >> (shift)) & ((1u << (width)) - 1u))

static inline uint32_t field_set(uint32_t reg, unsigned shift, unsigned width, uint32_t val)
{
    uint32_t mask = ((1u << width) - 1u) << shift;
    return (reg & ~mask) | ((val << shift) & mask);
}
```

Watch out for `width == 32`: `1u << 32` is undefined. The Linux kernel provides `FIELD_GET()`/`FIELD_PREP()` with `GENMASK()` for this.

### How do you check if two integers have opposite signs? {E}
```c
bool opposite = (a ^ b) < 0;
```

XOR of the sign bits is 1 only if they differ, which makes the result negative.

### How do you find the absolute value without branching? {M}
```c
int32_t mask = x >> 31;           /* 0 or -1 (arithmetic shift) */
int32_t abs_x = (x + mask) ^ mask;
```

This relies on arithmetic right shift (implementation-defined) and fails for `INT32_MIN`. Compilers already generate branchless code for `x < 0 ? -x : x`, so prefer the readable form.

### How do you round up to the next power of two? {M}
```c
uint32_t next_pow2(uint32_t x)
{
    x--;
    x |= x >> 1;  x |= x >> 2;  x |= x >> 4;
    x |= x >> 8;  x |= x >> 16;
    return x + 1;
}
```

Smearing the highest bit to every lower position gives `2^k - 1`; adding 1 gives the power of two. Returns 0 for `x == 0` and for values above `2^31`.

### How do you align a value up or down to a power-of-two boundary? {E}
```c
#define ALIGN_DOWN(x, a) ((x) & ~((a) - 1))
#define ALIGN_UP(x, a)   (((x) + (a) - 1) & ~((a) - 1))
```

`ALIGN_UP(13, 8)` is 16. This is used constantly for buffer sizes, DMA and cache lines, and page addresses.

### How do you compute x % 8 or x / 8 using bit operations? {E}
For unsigned `x` and a power-of-two divisor: `x % 8 == x & 7` and `x / 8 == x >> 3`. Compilers already do this for unsigned values. For signed values the rounding differs for negatives, which is why the compiler adds fix-up instructions.

### How do you find the single number that appears once when all others appear twice? {E}
XOR everything together. Pairs cancel (`a ^ a = 0`) and `0 ^ x = x`:

```c
int single(const int *a, size_t n)
{
    int r = 0;
    for (size_t i = 0; i < n; i++) r ^= a[i];
    return r;
}
```

O(n) time and O(1) memory.

### How do you check whether bit n is the same in two registers? {E}
`(((a ^ b) >> n) & 1u) == 0`. XOR marks every differing bit.

### How do you detect if a value has a zero byte? {H}
This trick, used in fast `strlen` implementations, tests four bytes at once:

```c
#define HAS_ZERO(v) (((v) - 0x01010101u) & ~(v) & 0x80808080u)
```

Subtracting 1 from a zero byte borrows and sets its high bit; `~v` filters out bytes whose high bit was already set. A non-zero result means at least one byte is zero.

### What is a bit mask and how is GENMASK built? {M}
A mask is a constant whose 1-bits select the bits you want to operate on. A contiguous mask from bit `l` to bit `h` inclusive:

```c
#define GENMASK(h, l) (((~0u) << (l)) & (~0u >> (31 - (h))))
/* GENMASK(7, 4) == 0x000000F0 */
```

Building masks this way avoids the `(1u << 32)` overflow when the field is the full width.

### How do you rotate bits left and right? {M}
```c
static inline uint32_t rotl(uint32_t x, unsigned n) { n &= 31; return (x << n) | (x >> ((32 - n) & 31)); }
static inline uint32_t rotr(uint32_t x, unsigned n) { n &= 31; return (x >> n) | (x << ((32 - n) & 31)); }
```

Masking the shift counts avoids undefined behaviour when `n` is 0. Compilers recognise the pattern and emit a single `ROR` on ARM.

### How do you find the parity of a number? {M}
Fold the word onto itself with XOR until one bit remains:

```c
bool parity(uint32_t x)
{
    x ^= x >> 16; x ^= x >> 8; x ^= x >> 4; x ^= x >> 2; x ^= x >> 1;
    return x & 1u;   /* 1 = odd number of set bits */
}
```

Or `__builtin_parity(x)`. Parity is used in UART frames and simple error detection.
