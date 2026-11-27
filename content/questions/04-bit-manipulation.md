---
slug: bit-manipulation
title: Bit Manipulation
icon: 🔢
level: Beginner
order: 4
desc: Bitwise operators, masks, shifts, counting bits, powers of two and the classic whiteboard puzzles.
---
Bit manipulation questions are short, easy to grade, and show up in nearly every firmware interview. Each answer below starts with the one-line answer you would give first, then the reasoning, a worked example and the follow-up questions interviewers usually ask next. Do all bit work on **unsigned** types unless you have a reason not to.

### What are the bitwise operators in C? {E}
Bitwise operators manipulate individual bits of integer operands. They are heavily used in firmware to control registers, construct masks and process binary data.

#### 1. Basic operators

Assume a = 12 (1100) and b = 10 (1010).

| Operator | Operation | Result |
|---|---|---|
| `&` | AND | 1000 = 8 |
| `\|` | OR | 1110 = 14 |
| `^` | XOR | 0110 = 6 |
| `~` | NOT | Inverts all bits of the promoted operand |
| `<<` | Left shift | a << 1 = 24 |
| `>>` | Right shift | a >> 1 = 6 |

#### 2. Truth table

| A | B | AND | OR | XOR |
|---|---|---|---|---|
| 0 | 0 | 0 | 0 | 0 |
| 0 | 1 | 0 | 1 | 1 |
| 1 | 0 | 0 | 1 | 1 |
| 1 | 1 | 1 | 1 | 0 |

#### 3. Embedded register example

```c
uint32_t reg = 0;
reg |= UINT32_C(1) << 3; // Set bit 3
reg &= ~(UINT32_C(1) << 3); // Clear bit 3
```

For MMIO, ensure the register permits read-modify-write. C integer promotions can affect the width of complement and shift operations, especially for uint8_t and uint16_t.

**Interview takeaway:** Bitwise operators work on individual integer bits; logical operators such as && and || work on truth values and may short-circuit. Use unsigned operands and valid shift counts.

### How do you set, clear, toggle and check the nth bit? {E}
**Short answer:** Build a mask with `1u << n`, then use OR to set, AND with the inverted mask to clear, XOR to toggle and AND to test.

```c
#include <stdint.h>
#include <stdbool.h>

static inline uint32_t bit_set(uint32_t x, unsigned n)    { return x |  (1u << n); }
static inline uint32_t bit_clear(uint32_t x, unsigned n)  { return x & ~(1u << n); }
static inline uint32_t bit_toggle(uint32_t x, unsigned n) { return x ^  (1u << n); }
static inline bool     bit_test(uint32_t x, unsigned n)   { return (x >> n) & 1u; }

/* In-place versions, the style many people write first: */
void set_nth_bit(uint32_t *num, unsigned n)   { *num |=  (1u << n); }
void clear_nth_bit(uint32_t *num, unsigned n) { *num &= ~(1u << n); }
```

**Why each works**

- OR with 1 forces a bit to 1; OR with 0 leaves it unchanged. The mask has a single 1, so only bit `n` changes.
- `~(1u << n)` is all ones except bit `n`. AND with 0 forces that bit to 0 and AND with 1 keeps the others.
- XOR with 1 flips a bit; XOR with 0 keeps it.
- `x & (1u << n)` is non-zero if bit `n` is set. It is **not** 1; it is `2ⁿ`. If you need exactly 0 or 1, use `(x >> n) & 1u` or `!!(x & (1u << n))`.

**Worked example:** `x = 0b1010`, `n = 2`. Set gives `0b1110`, clear gives `0b1010` (already clear), toggle gives `0b1110`, test gives 0.

**Common mistakes**

- Using `int` and `1 << 31`: undefined behaviour. Use `uint32_t` and `1u`.
- Shifting by 32 or more: undefined for a 32-bit type. Check `n < 32` or mask `n &= 31`.
- Writing `bit = number & (1 << n)` and then comparing `bit == 1`. That is only true for `n == 0`.

**Follow-up on real hardware:** `reg |= mask` on a peripheral register is a read-modify-write. If an ISR changes the same register between the read and the write, the ISR's change is lost. Fixes: disable interrupts around it, use hardware set/clear registers (STM32 `GPIOx->BSRR`, NXP `SET`/`CLR` registers), or Cortex-M bit-banding.

### Is right shift of a negative number arithmetic or logical? {M}
**Short answer:** For unsigned types `>>` is always a logical shift (zeros come in from the left). For a negative signed value the result is **implementation-defined**; GCC, Clang and Arm compilers do an arithmetic shift that copies the sign bit, but portable code must not rely on it.

**The two kinds of right shift**

- **Logical:** fills the vacated high bits with 0. `0xF0000000u >> 4 == 0x0F000000u`.
- **Arithmetic:** fills them with copies of the sign bit, so the value stays negative. `-16 >> 2 == -4` on GCC (`0xFFFFFFF0 → 0xFFFFFFFC`).

On Arm these are two different instructions, `LSR` and `ASR`. The compiler picks `LSR` for unsigned and `ASR` for signed operands.

**Left shift is worse.** Left-shifting a negative value, or shifting a 1 into or past the sign bit of a signed int, is **undefined behaviour** in C99/C11/C17. C23 made the representation two's complement but the overflow cases are still problems. An optimiser is allowed to assume undefined behaviour never happens and can delete code that depends on it.

**Arithmetic shift is not exact division.** `-7 >> 1` gives `-4` (rounds toward minus infinity) while `-7 / 2` gives `-3` (C rounds toward zero). That is why compilers emit extra fix-up instructions when you divide a signed value by a power of two.

**Rule for interviews and production:** do bit manipulation on `uint8_t`/`uint16_t`/`uint32_t`. If you must sign-extend a field, do it explicitly:

```c
/* sign-extend the low 'bits' bits of x */
int32_t sign_extend(uint32_t x, unsigned bits)
{
    uint32_t m = 1u << (bits - 1);
    x &= (1u << bits) - 1u;          /* bits < 32 */
    return (int32_t)((x ^ m) - m);
}
```

**Follow-up:** "What does `(int8_t)0x80 >> 1` give?" The `int8_t` is promoted to `int` (-128) first, then shifted: -64 on GCC. Integer promotion happens before every shift.

### How do you check if a number is a power of two? {E}
**Short answer:** `x && !(x & (x - 1))`. A power of two has exactly one bit set, and `x & (x - 1)` clears the lowest set bit, so the result is zero only when there was a single bit.

```c
#include <stdbool.h>
#include <stdint.h>

bool is_pow2(uint32_t x)
{
    return x != 0 && (x & (x - 1)) == 0;
}
```

**Why `x - 1` works:** subtracting 1 turns the lowest set bit into 0 and every bit below it into 1. Bits above it do not change.

```
x       = 0b0100_0000   (64)
x - 1   = 0b0011_1111
x&(x-1) = 0b0000_0000   -> power of two

x       = 0b0101_0000   (80)
x - 1   = 0b0100_1111
x&(x-1) = 0b0100_0000   -> not a power of two
```

**Why `x != 0`:** for `x = 0`, `x - 1` wraps to `0xFFFFFFFF` and the AND is 0, so without the check 0 would wrongly count as a power of two.

**Alternatives:** `__builtin_popcount(x) == 1`, or C23 `stdc_has_single_bit(x)`.

**Where it is used:** checking that a ring-buffer size, DMA block size or alignment is a power of two before using `& (size - 1)` instead of `% size`.

**Follow-up:** "Check if `x` is a power of four?" It must be a power of two **and** the bit must be in an even position: `is_pow2(x) && (x & 0x55555555u)`.

### How do you clear the rightmost (lowest) set bit, and what other tricks use n & (n - 1)? {E}
**Short answer:** `n & (n - 1)` turns off the lowest set bit. It is the building block for the power-of-two test, Kernighan's bit count and several other classic tricks.

```c
uint32_t clear_lowest_set(uint32_t n)  { return n & (n - 1); }   /* 0b1011_0100 -> 0b1011_0000 */
uint32_t isolate_lowest_set(uint32_t n){ return n & (~n + 1); }  /* 0b1011_0100 -> 0b0000_0100 (n & -n) */
uint32_t set_lowest_clear(uint32_t n)  { return n | (n + 1); }   /* 0b1011_0111 -> 0b1011_1111 */
uint32_t clear_trailing_ones(uint32_t n){ return n & (n + 1); }  /* 0b1011_0111 -> 0b1011_0000 */
```

**How it works:** in binary, `n - 1` flips the lowest 1 to 0 and all the 0s below it to 1. ANDing with the original keeps the high part, removes the lowest 1 and leaves the low part zero.

**Walk-through for n = 12 (0b1100):** `n - 1 = 0b1011`, `n & (n - 1) = 0b1000` = 8. The lowest set bit (value 4) is gone.

**Uses**

1. **Power-of-two test:** `n && !(n & (n - 1))`.
2. **Counting set bits:** repeat until zero, counting the iterations (one loop per set bit).
3. **Iterating over set bits:** handle pending interrupt flags or ready tasks one at a time:
   ```c
   while (pending) {
       unsigned bit = __builtin_ctz(pending);  /* index of lowest set bit */
       handle(bit);
       pending &= pending - 1;
   }
   ```
4. **Lowest set bit as a mask:** `n & -n` is used in Fenwick trees and to pick the highest-priority ready task when priority 0 is bit 0.

**Edge case:** for `n = 0` the result is 0, which is fine. The `n & -n` form on a signed type overflows for `INT_MIN`, so use unsigned values.

### How do you count the set bits in an integer? {M}
**Short answer:** Use Brian Kernighan's loop, which runs once per set bit because `x & (x - 1)` clears the lowest set bit. In production use `__builtin_popcount` (a single `CNT`/`VCNT` or `POPCNT` instruction where the CPU has one).

```c
unsigned popcount(uint32_t x)
{
    unsigned n = 0;
    while (x) {
        x &= x - 1;   /* drop lowest set bit */
        n++;
    }
    return n;
}
```

**Three approaches compared**

| Method | Loop count | Notes |
|---|---|---|
| Test every bit: `n += x & 1; x >>= 1;` | 32 | simplest; fine for a first answer |
| Kernighan: `x &= x - 1` | number of set bits | good when few bits are set |
| SWAR (parallel add) | 0 (constant time) | best general-purpose software method |

**Simple version and its trap.** Many people write this:

```c
int a = 255, count = 0;
while (a) { count += a & 1; a >>= 1; }
```

It works for positive values, but for a **negative** `int` the arithmetic right shift keeps copying the sign bit, so `a` never becomes 0 and the loop never ends. Use `unsigned`/`uint32_t`.

**Constant-time SWAR version** (adds bits in pairs, then nibbles, then bytes):

```c
unsigned popcount_swar(uint32_t x)
{
    x = x - ((x >> 1) & 0x55555555u);                 /* 2-bit sums */
    x = (x & 0x33333333u) + ((x >> 2) & 0x33333333u); /* 4-bit sums */
    x = (x + (x >> 4)) & 0x0F0F0F0Fu;                 /* 8-bit sums */
    return (x * 0x01010101u) >> 24;                   /* add the 4 bytes */
}
```

**Lookup table:** a 256-entry table and four lookups is fast on a microcontroller without a multiplier, at the cost of 256 bytes of flash.

**Follow-ups:** "Count the bits that differ between a and b" is `popcount(a ^ b)` (the Hamming distance). "Count set bits for every number 0..n" uses `bits[i] = bits[i >> 1] + (i & 1)`.

### How do you swap two numbers without a temporary variable? {E}
**Short answer:** Use three XORs: `a ^= b; b ^= a; a ^= b;`. It is a well-known trick, but in real code a temporary variable is clearer and just as fast.

```c
void xor_swap(int *a, int *b)
{
    if (a != b) {      /* same object would become 0 */
        *a ^= *b;
        *b ^= *a;
        *a ^= *b;
    }
}
```

**Why it works:** XOR is its own inverse (`x ^ y ^ y == x`).

| Step | a | b |
|---|---|---|
| start | A | B |
| `a ^= b` | A^B | B |
| `b ^= a` | A^B | B^(A^B) = **A** |
| `a ^= b` | (A^B)^A = **B** | A |

**Arithmetic version:** `a = a + b; b = a - b; a = a - b;` also works but can overflow on signed types, which is undefined behaviour.

**Why not use it in production**

- If `a` and `b` alias the same memory, the first XOR sets it to 0 and the value is lost. The `if (a != b)` guard fixes that.
- The three operations depend on each other, so the CPU cannot overlap them. With a temporary, the compiler often turns the swap into register renaming and generates zero instructions.
- It is less readable.

**Follow-up:** "Swap two nibbles in a byte": `(x >> 4) | (x << 4)` on a `uint8_t` (then cast back to `uint8_t`).

### How do you find the position of the lowest set bit? {M}
**Short answer:** `x & -x` isolates the lowest set bit, and its index is the number of trailing zeros: `__builtin_ctz(x)` (undefined when `x == 0`). For the highest set bit use `31 - __builtin_clz(x)`.

```c
unsigned lowest_set_index(uint32_t x)   /* x != 0 */
{
    return (unsigned)__builtin_ctz(x);
}

unsigned highest_set_index(uint32_t x)  /* x != 0 */
{
    return 31u - (unsigned)__builtin_clz(x);
}
```

**Portable loop (for an interview without builtins):**

```c
int lowest_set_index_loop(uint32_t x)
{
    if (x == 0) return -1;
    int i = 0;
    while ((x & 1u) == 0) { x >>= 1; i++; }
    return i;
}
```

**How the hardware does it on Arm:** `CLZ` (count leading zeros) exists on Arm v5 and later, including Cortex-M3/M4/M7 but **not** Cortex-M0/M0+. Count trailing zeros is `RBIT` (reverse bits) followed by `CLZ`.

**Why x & -x isolates the lowest bit:** in two's complement `-x == ~x + 1`. Inverting flips every bit, and adding 1 ripples up to the lowest original 1, so only that bit is common to `x` and `-x`.

```
x  = 0b0110_1000
-x = 0b1001_1000
x & -x = 0b0000_1000   -> bit 3
```

**Where it is used:**

- **RTOS schedulers:** FreeRTOS's port-optimised task selection keeps one bit per priority and uses `CLZ` to find the highest ready priority in one instruction.
- **Interrupt dispatch:** finding the first pending source.
- `ffs()` in POSIX returns the 1-based index (0 for no bits) and is defined for 0.

**Follow-up:** "log₂ of a power of two?" `__builtin_ctz(x)`. "Floor log₂ of any x?" `31 - __builtin_clz(x)`.

### How do you reverse the bits of a byte or an n-bit number? {E}
**Short answer:** Loop over the bits: if bit `i` is set in the input, set bit `(width - 1 - i)` in the output. The width must be the number of **bits**, not bytes.

```c
#include <stdint.h>

uint32_t reverse_n_bits(uint32_t a, unsigned width)   /* width = 1..32 */
{
    uint32_t out = 0;
    for (unsigned i = 0; i < width; i++) {
        if (a & (1u << i))
            out |= 1u << (width - 1 - i);
    }
    return out;
}

/* reverse_n_bits(15, 8)   = 0xF0  (0b00001111 -> 0b11110000) */
/* reverse_n_bits(1, 32)   = 0x80000000 */
```

**A common bug.** This version looks right but is wrong:

```c
unsigned int a = 1;
int n = sizeof(a);            /* 4 -- that is BYTES, not bits */
for (int i = 0; i < n; i++)
    if (a & (1U << i)) temp |= 1U << ((n - 1) - i);
/* prints 8 instead of 2147483648 */
```

`sizeof` returns bytes. Use `sizeof(a) * CHAR_BIT` (from `<limits.h>`), which is 32.

**Shift-in version** (no reverse index, often clearer):

```c
uint8_t reverse_byte(uint8_t b)
{
    uint8_t r = 0;
    for (int i = 0; i < 8; i++) {
        r = (uint8_t)((r << 1) | (b & 1u));  /* take LSB of b, push into r */
        b >>= 1;
    }
    return r;
}
```

**Faster options**

- 256-entry lookup table for bytes: one memory read.
- Swap halves, then quarters, then pairs: `b = (b >> 4) | (b << 4); b = ((b & 0xCC) >> 2) | ((b & 0x33) << 2); b = ((b & 0xAA) >> 1) | ((b & 0x55) << 1);`
- On Cortex-M3 and later, `__RBIT()` reverses 32 bits in one instruction; shift right by `32 - width` for narrower values.

**Where it shows up:** LSB-first vs MSB-first serial protocols, CRC implementations ("reflected" CRCs), and FFT bit-reversed addressing.

### How do you reverse the bits of a 32-bit integer? {M}
**Short answer:** Swap progressively larger groups of bits (1, 2, 4, 8, then 16) using masks. It runs in constant time with no loop. On Cortex-M3 and later it is a single `RBIT` instruction.

```c
uint32_t reverse_bits(uint32_t x)
{
    x = ((x >> 1) & 0x55555555u) | ((x & 0x55555555u) << 1);  /* swap adjacent bits   */
    x = ((x >> 2) & 0x33333333u) | ((x & 0x33333333u) << 2);  /* swap bit pairs       */
    x = ((x >> 4) & 0x0F0F0F0Fu) | ((x & 0x0F0F0F0Fu) << 4);  /* swap nibbles         */
    x = ((x >> 8) & 0x00FF00FFu) | ((x & 0x00FF00FFu) << 8);  /* swap bytes           */
    return (x >> 16) | (x << 16);                             /* swap 16-bit halves   */
}
```

**How the masks work:** `0x5` is `0101`, so `0x55555555` selects the even bits and `0xAAAAAAAA` the odd bits. `0x3` = `0011` selects the low pair in each nibble, and `0x0F` the low nibble in each byte. Each line moves the selected group up and the other group down.

**Example:** `reverse_bits(0x00000001) == 0x80000000`; `reverse_bits(0x0000000F) == 0xF0000000`.

**Cost:** 5 steps for 32 bits (log₂ 32), versus 32 iterations for the loop version.

**Using the hardware:**

```c
#include "cmsis_compiler.h"
uint32_t r = __RBIT(x);     /* Cortex-M3/M4/M7/M33 */
```

GCC also has `__builtin_bitreverse32` in recent versions (Clang has had it for longer).

**Follow-up:** "Reverse only the lower `k` bits?" `reverse_bits(x) >> (32 - k)` for `1 ≤ k ≤ 32` (handle `k == 32` without the shift, because shifting by 0 is fine but shifting by 32 is not).

### How do you swap the odd and even bits of a number? {M}
**Short answer:** Mask the odd bits with `0xAAAAAAAA` and shift them right by one, mask the even bits with `0x55555555` and shift them left by one, then OR the two halves.

```c
uint32_t swap_odd_even_bits(uint32_t n)
{
    return ((n & 0xAAAAAAAAu) >> 1) | ((n & 0x55555555u) << 1);
}
```

**Example:** `23 = 0b0001_0111`

```
n          = 0001 0111
odd bits   = 0000 0010  (n & 0xAA) -> >>1 = 0000 0001
even bits  = 0001 0101  (n & 0x55) -> <<1 = 0010 1010
result     = 0010 1011  = 43
```

Bit 0 and bit 1 swap, bit 2 and bit 3 swap, and so on.

**Why the masks:** `0xA` is `1010` (bits 1 and 3 of a nibble, the odd positions) and `0x5` is `0101` (bits 0 and 2, the even positions). Repeating them covers all 32 bits.

**Use unsigned.** With a signed `int`, `(n & 0xAAAAAAAA) >> 1` involves a value that may have the sign bit set, and shifting the even bits left can move a 1 into bit 31 of a signed int (undefined behaviour). With `uint32_t` both shifts are well-defined.

**Related tricks with the same idea:**

- Swap nibbles in a byte: `(b >> 4) | (b << 4)`.
- Swap adjacent bytes: `((x & 0xFF00FF00u) >> 8) | ((x & 0x00FF00FFu) << 8)`.
- This step is the first line of the constant-time bit-reverse algorithm.

### How do you set all bits in a range from position l to r? {M}
**Short answer:** Build a mask of ones from bit `l` to bit `r` and OR it in. With 0-based positions: `mask = ((1u << (r - l + 1)) - 1u) << l`, valid while the field is narrower than 32 bits.

```c
#include <stdint.h>

/* 0-based, inclusive: l <= r <= 31 */
uint32_t range_mask(unsigned l, unsigned r)
{
    unsigned width = r - l + 1;
    uint32_t ones = (width >= 32) ? 0xFFFFFFFFu : ((1u << width) - 1u);
    return ones << l;
}

uint32_t set_range(uint32_t x, unsigned l, unsigned r)    { return x |  range_mask(l, r); }
uint32_t clear_range(uint32_t x, unsigned l, unsigned r)  { return x & ~range_mask(l, r); }
uint32_t toggle_range(uint32_t x, unsigned l, unsigned r) { return x ^  range_mask(l, r); }
```

**Example:** `l = 3, r = 4` (0-based) → width 2 → `0b11 << 3` = `0b0001_1000` = 24.

**The XOR form (1-based positions).** A version often seen in practice:

```c
int l = 4, r = 5;                                      /* 1-based positions */
unsigned mask = ((1u << (l - 1)) - 1u) ^ ((1u << r) - 1u);
/* (1<<3)-1 = 0b00111, (1<<5)-1 = 0b11111, XOR = 0b11000 = 24 */
```

`(1 << r) - 1` is ones in positions 1..r, and `(1 << (l-1)) - 1` is ones in positions 1..l-1. XOR removes the lower ones, leaving positions l..r. It is correct, but it **breaks for r = 32** (`1u << 32` is undefined), and it is easy to confuse 1-based and 0-based positions. State which you mean before you write code.

**Kernel-style GENMASK** avoids the overflow by shifting all-ones instead:

```c
#define GENMASK(h, l) (((~0u) << (l)) & (~0u >> (31 - (h))))   /* 0-based, h >= l */
```

**Follow-up:** "Check whether all bits in the range are set": `(x & mask) == mask`. "Any bit set?": `(x & mask) != 0`.

### How do you extract or insert a bit field? {E}
**Short answer:** To read a field, shift it down and mask: `(reg >> shift) & ((1u << width) - 1)`. To write it, clear the field with the inverted mask and OR in the new value shifted into place.

```c
#define FIELD_GET(reg, shift, width)  (((reg) >> (shift)) & ((1u << (width)) - 1u))

static inline uint32_t field_set(uint32_t reg, unsigned shift, unsigned width, uint32_t val)
{
    uint32_t mask = ((1u << width) - 1u) << shift;   /* width < 32 */
    return (reg & ~mask) | ((val << shift) & mask);
}
```

**Example:** a clock prescaler in bits 6..4 of a register.

```c
uint32_t cfg = 0x1234;
unsigned psc = FIELD_GET(cfg, 4, 3);     /* (0x1234 >> 4) & 0x7 = 0x123 & 7 = 3 */
cfg = field_set(cfg, 4, 3, 5);           /* clears bits 6..4, writes 101 -> 0x1254 */
```

**Why mask the new value too:** `& mask` after shifting stops a too-large `val` from spilling into neighbouring fields. Writing 9 into a 3-bit field without it would corrupt bit 7.

**Real registers: read-modify-write.** On a peripheral register:

```c
uint32_t v = PERIPH->CR;          /* read once */
v &= ~PSC_Msk;
v |= (psc << PSC_Pos) & PSC_Msk;
PERIPH->CR = v;                   /* write once */
```

Reading into a local and writing once avoids two separate bus writes that would put a half-updated value into the hardware in between.

**Traps**

- `width == 32`: `1u << 32` is undefined; use `GENMASK`-style macros.
- Do not use C bit-fields (`struct { unsigned psc:3; }`) for hardware registers: the bit order, padding and access width are implementation-defined, and the compiler may use byte accesses on a register that only accepts 32-bit accesses.

**Linux:** `FIELD_GET(MASK, reg)` and `FIELD_PREP(MASK, val)` from `<linux/bitfield.h>`, with `GENMASK(h, l)` for the mask. CMSIS headers give `_Pos` and `_Msk` macros for each field.

### How do you check if two integers have opposite signs? {E}
**Short answer:** `(a ^ b) < 0`. XOR of two numbers has its sign bit set only when the two sign bits differ, so the result is negative exactly when the signs are opposite.

```c
#include <stdbool.h>

bool opposite_signs(int a, int b)
{
    return (a ^ b) < 0;
}
```

**Example**

```
a =  5  -> 0000...0101
b = -3  -> 1111...1101
a ^ b   -> 1111...1000  (sign bit 1, negative) -> opposite signs

a = -5, b = -3 -> sign bits both 1 -> XOR sign bit 0 -> same sign
```

**Edge cases**

- Zero counts as positive, so `opposite_signs(0, -1)` is true and `opposite_signs(0, 5)` is false. Say this out loud in an interview.
- No overflow is possible: XOR never overflows, unlike `a * b < 0`, which can overflow for large values (undefined behaviour for signed types).

**Readable alternative:** `(a < 0) != (b < 0)`. Modern compilers generate the same code, so this is preferable in production.

**Where it is used:** detecting a zero crossing in a signal (consecutive samples with opposite signs), and overflow checks: for `s = a + b`, overflow happened if `a` and `b` have the same sign and `s` has a different sign: `((a ^ s) & (b ^ s)) < 0`. Compute `s` with unsigned arithmetic so the addition itself is not undefined.

### How do you check if a number is even or odd using bitwise operators? {E}
**Short answer:** Test the lowest bit: `(n & 1) == 0` means even and `(n & 1) == 1` means odd. Every odd number has bit 0 set, because all other bits contribute even values.

```c
#include <stdbool.h>

bool is_even(unsigned n) { return (n & 1u) == 0; }
bool is_odd(unsigned n)  { return (n & 1u) != 0; }
```

**Why:** a binary number is `b0·1 + b1·2 + b2·4 + ...`. Everything except `b0` is a multiple of 2, so `b0` alone decides odd or even.

**Negative numbers:** in two's complement (all modern CPUs, and required by C23), `-3` is `...11101`, so `-3 & 1 == 1` and the test still works. Compare with `%`: `-3 % 2 == -1` in C, so `n % 2 == 1` is **false** for negative odd numbers. That is a real bug. Write `n % 2 != 0` if you use `%`.

**Speed:** compilers turn `n % 2 == 0` into a single AND, so there is no performance reason to prefer the bitwise form. Use whichever reads better.

**Related one-liners**

- Multiple of 4: `(n & 3) == 0`.
- Multiple of 2ᵏ: `(n & ((1u << k) - 1)) == 0`.
- Round down to even: `n & ~1u`.

### How do you find the absolute value without branching? {M}
**Short answer:** Make a mask that is all ones for negative numbers and zero otherwise (`mask = x >> 31`), then compute `(x + mask) ^ mask`. It relies on an arithmetic right shift and fails for `INT32_MIN`.

```c
#include <stdint.h>

int32_t abs_branchless(int32_t x)
{
    int32_t mask = x >> 31;        /* 0 if x >= 0, -1 (all ones) if x < 0 */
    return (x + mask) ^ mask;
}
```

**Walk-through for x = -5**

- `mask = -1` (0xFFFFFFFF)
- `x + mask = -6` (0xFFFFFFFA)
- `-6 ^ -1 = ~(-6) = 5`

For `x = 5`, the mask is 0 and `(5 + 0) ^ 0 = 5`.

**Why it works:** for negative x, `(x - 1)` inverted is `-(x - 1) - 1 = -x`. Two's complement negation is "invert and add one"; this does "subtract one and invert", which is the same thing.

**Limitations**

1. `x >> 31` on a negative signed value is implementation-defined (arithmetic on GCC/Clang/Arm, but not guaranteed by the standard).
2. `abs(INT32_MIN)` cannot be represented; the result is `INT32_MIN` again, and with the plain `-x` form it is undefined behaviour.

**Why branchless was used:** on older CPUs a mispredicted branch was expensive, and in cryptographic code a branch on secret data leaks timing information.

**In practice:** write `x < 0 ? -x : x` or `abs(x)`. GCC and Clang already generate branchless code for it (on Arm, `CMP` plus a conditional negate or `CSNEG` on AArch64). Branchless tricks are worth knowing for interviews and constant-time code, not for everyday firmware.

### How do you round up to the next power of two? {M}
**Short answer:** Subtract one, copy the highest set bit into every lower position with shifts and ORs, then add one. The smearing turns any value into `2ᵏ - 1`, and adding one gives `2ᵏ`.

```c
uint32_t next_pow2(uint32_t x)
{
    x--;
    x |= x >> 1;
    x |= x >> 2;
    x |= x >> 4;
    x |= x >> 8;
    x |= x >> 16;
    return x + 1;
}
```

**Walk-through for x = 37 (0b100101)**

```
x - 1      = 0b100100
|= >>1     = 0b110110
|= >>2     = 0b111111   (already all ones below the top bit)
...        = 0b111111   (63)
+ 1        = 0b1000000  (64)
```

**Why subtract one first:** so that an exact power of two maps to itself. Without it, `next_pow2(64)` would give 128.

**Edge cases**

- `x = 0` → `x - 1` wraps to `0xFFFFFFFF`, smearing changes nothing, and `+ 1` wraps to 0. Decide what 0 should return and handle it explicitly.
- `x > 2³¹` → the answer does not fit in 32 bits and the result wraps to 0.

**With CLZ (one instruction on Cortex-M3+):**

```c
uint32_t next_pow2_clz(uint32_t x)   /* 2 <= x <= 2^31 */
{
    return 1u << (32 - __builtin_clz(x - 1));
}
```

**Where it is used:** sizing ring buffers and hash tables so you can wrap indices with `& (size - 1)`, choosing a DMA or MPU region size (the classic Arm v7-M MPU requires power-of-two region sizes aligned to their size), and memory allocators that use power-of-two size classes (buddy allocator).

### How do you align a value up or down to a power-of-two boundary? {E}
**Short answer:** Align down with `x & ~(a - 1)`; align up with `(x + a - 1) & ~(a - 1)`. Both require `a` to be a power of two.

```c
#define ALIGN_DOWN(x, a)  ((x) & ~((a) - 1))
#define ALIGN_UP(x, a)    (((x) + (a) - 1) & ~((a) - 1))
#define IS_ALIGNED(x, a)  (((x) & ((a) - 1)) == 0)
```

**Examples with a = 8 (mask `~7` = ...11111000)**

| x | ALIGN_DOWN | ALIGN_UP |
|---|---|---|
| 13 | 8 | 16 |
| 16 | 16 | 16 |
| 1 | 0 | 8 |

**Why it works:** `a - 1` is a mask of the low bits (7 = `0b111`). Clearing them rounds down to a multiple of `a`. Adding `a - 1` first pushes any value that is not already aligned past the next boundary, so the clear then rounds up.

**Where you use it in embedded work**

- **DMA buffers and caches:** on a Cortex-M7 with D-cache, a DMA buffer should start and end on a 32-byte cache-line boundary so that cache clean/invalidate does not touch neighbouring variables.
- **Memory allocators:** returning 8-byte aligned blocks so `double` and `uint64_t` work.
- **Page arithmetic:** `ALIGN_DOWN(addr, 4096)` gives the page base address.
- **Stack pointers:** the AAPCS requires 8-byte stack alignment at public function calls.

**Pitfalls**

- With a pointer, cast to `uintptr_t` first: `ALIGN_UP((uintptr_t)p, 32)`.
- Types must match: if `x` is 64-bit and `a` is an `unsigned int`, `~(a - 1)` is a 32-bit mask and clears the upper 32 bits of `x`. Cast `a` to the type of `x`.
- `ALIGN_UP` can overflow near the top of the address range.

For non-power-of-two alignment, use `((x + a - 1) / a) * a`.

### How do you compute x % 8 or x / 8 using bit operations? {E}
**Short answer:** For an unsigned `x` and a power-of-two divisor 2ᵏ, `x / 2ᵏ == x >> k` and `x % 2ᵏ == x & (2ᵏ - 1)`. So `x / 8 == x >> 3` and `x % 8 == x & 7`.

```c
uint32_t div8(uint32_t x) { return x >> 3; }
uint32_t mod8(uint32_t x) { return x & 7u; }
```

**Why:** dividing by 8 drops the last three binary digits (like dividing by 1000 drops three decimal digits), and those three dropped bits are exactly the remainder.

**Example:** `x = 29 = 0b11101` → `x >> 3 = 0b11 = 3`, `x & 7 = 0b101 = 5`, and `3 * 8 + 5 = 29`.

**Signed values are different.** C rounds integer division toward zero, so `-9 / 8 == -1` and `-9 % 8 == -1`. But `-9 >> 3 == -2` (arithmetic shift rounds toward minus infinity) and `-9 & 7 == 7`. That is why for `int x` the compiler emits a few extra instructions to correct the result. If the value is never negative, make it `unsigned` and you get the single instruction.

**You rarely need to write the shift yourself.** Any optimising compiler turns `x / 8` into a shift for unsigned operands. Write the arithmetic that expresses your intent.

**Where the mask form is important: ring buffers.**

```c
#define BUF_SIZE 64u                       /* must be a power of two */
head = (head + 1u) & (BUF_SIZE - 1u);      /* wraps 63 -> 0, no division */
```

On a Cortex-M0/M0+ there is no hardware divide instruction at all, so avoiding `%` with a non-constant divisor saves a call to a slow library routine.

### How do you find the single number that appears once when all others appear twice? {E}
**Short answer:** XOR all the elements together. Every number that appears twice cancels itself (`a ^ a = 0`), and `0 ^ x = x`, so only the unique value remains. O(n) time, O(1) memory.

```c
#include <stddef.h>

int find_unique(const int *arr, size_t n)
{
    int result = 0;
    for (size_t i = 0; i < n; i++)
        result ^= arr[i];
    return result;
}
/* {4, 1, 2, 1, 2} -> 4 */
```

**Why order does not matter:** XOR is commutative and associative, so `4 ^ 1 ^ 2 ^ 1 ^ 2` can be regrouped as `4 ^ (1 ^ 1) ^ (2 ^ 2) = 4 ^ 0 ^ 0 = 4`.

**Comparison with other approaches**

| Approach | Time | Extra memory |
|---|---|---|
| Two nested loops | O(n²) | O(1) |
| Sort, then scan pairs | O(n log n) | O(1) or O(n) |
| Hash/count table | O(n) | O(n) |
| **XOR** | **O(n)** | **O(1)** |

**Follow-ups interviewers ask**

1. **Two unique numbers, all others twice:** XOR everything to get `x = a ^ b`. Pick any set bit of `x` (`x & -x`); `a` and `b` differ there. Split the array into two groups by that bit and XOR each group separately.
2. **One number once, all others three times:** count each bit position modulo 3, or use the `ones`/`twos` bitmask method.
3. **Find the missing number 1..n:** XOR all indices 1..n with all elements; the missing one remains. This avoids the overflow risk of the sum formula `n(n+1)/2`.

### How do you check whether bit n is the same in two registers? {E}
**Short answer:** XOR the two values; a 1 marks every bit that differs. Bit `n` is the same in both when `((a ^ b) >> n) & 1u` is 0.

```c
#include <stdbool.h>
#include <stdint.h>

bool same_bit(uint32_t a, uint32_t b, unsigned n)
{
    return (((a ^ b) >> n) & 1u) == 0;
}
```

**Example:** `a = 0b1010`, `b = 0b1001`, `a ^ b = 0b0011`. Bits 0 and 1 differ; bits 2 and 3 are the same.

**Practical uses of "a ^ b"**

- **Change detection:** read the GPIO input register, XOR it with the previous reading, and the result shows which pins changed. `changed & new_state` gives rising edges and `changed & ~new_state` gives falling edges.
  ```c
  uint32_t now = GPIOA->IDR;
  uint32_t changed = now ^ last;
  uint32_t rising  = changed & now;
  uint32_t falling = changed & ~now;
  last = now;
  ```
- **Comparing a register with an expected value under a mask:** `((reg ^ expected) & mask) == 0` checks only the bits you care about.
- **Hamming distance:** `__builtin_popcount(a ^ b)` counts differing bits, used in error-correction and checksums.

**Follow-up:** "Check whether all bits in a mask are the same": `((a ^ b) & mask) == 0`.

### How do you detect if a value has a zero byte? {H}
**Short answer:** `((v - 0x01010101) & ~v & 0x80808080) != 0` tests all four bytes of a 32-bit word at once. It is the trick behind fast word-at-a-time `strlen` and `memchr`.

```c
#include <stdint.h>
#define HAS_ZERO(v)  (((v) - 0x01010101u) & ~(v) & 0x80808080u)
```

**How it works, byte by byte**

1. `v - 0x01010101` subtracts 1 from every byte. A byte that was `0x00` becomes `0xFF` (and borrows from the next byte up), so its high bit becomes 1.
2. Bytes that were `0x81`–`0xFF` also have the high bit set after subtracting. `& ~v` removes those, because their original high bit was already 1.
3. `& 0x80808080` keeps only the high bit of each byte.

If anything is left, at least one byte was zero.

**Example**

```
v               = 0x61 62 00 63
v - 0x01010101  = 0x60 60 FF 62   (the 00 byte became FF and borrowed from 0x62)
~v              = 0x9E 9D FF 9C
(v-..) & ~v     = 0x00 00 FF 00
& 0x80808080    = 0x00 00 80 00   -> non-zero, a zero byte exists
```

The borrow can corrupt bytes **above** the zero byte, which may produce a false high bit there. That is fine for "is there a zero?" but you must find the exact byte with a byte-by-byte check, or by using `__builtin_ctz` on a little-endian machine (lowest set marker = first zero byte in memory order).

**Find a specific byte value `c`:** XOR with a repeated pattern first: `HAS_ZERO(v ^ (0x01010101u * c))`.

**Practical notes**

- Word-at-a-time reads must be aligned, or you can read past the end of a buffer into an unmapped page. Library implementations align the pointer first.
- glibc and newlib `strlen`/`memchr` use this idea; Arm's optimized routines use NEON or `UADD8`/`SEL` instead.

### What is a bit mask and how is GENMASK built? {M}
**Short answer:** A mask is a constant whose 1 bits select the bits you want to read or change. `GENMASK(h, l)` builds a contiguous run of ones from bit `l` to bit `h` (inclusive) by shifting all-ones, which avoids the undefined `1u << 32`.

```c
#define GENMASK(h, l)  (((~0u) << (l)) & (~0u >> (31 - (h))))
/* GENMASK(7, 4)  == 0x000000F0 */
/* GENMASK(31, 0) == 0xFFFFFFFF  (no overflow) */
```

**How it is built**

- `~0u << l` gives ones from bit `l` upward: for `l = 4`, `0xFFFFFFF0`.
- `~0u >> (31 - h)` gives ones from bit `h` downward: for `h = 7`, `0x000000FF`.
- AND keeps the overlap: bits 7..4, `0x000000F0`.

**Why not `((1u << (h - l + 1)) - 1) << l`?** For a full 32-bit field, `h - l + 1 == 32`, and `1u << 32` is undefined behaviour. With GENMASK every shift amount stays in the range 0..31.

**Using masks**

| Operation | Code |
|---|---|
| set the bits | `x |= MASK` |
| clear the bits | `x &= ~MASK` |
| toggle | `x ^= MASK` |
| all set? | `(x & MASK) == MASK` |
| any set? | `(x & MASK) != 0` |
| read field | `(x & MASK) >> l` |

**Naming conventions in real code**

- CMSIS: `USART_CR1_UE_Pos` (bit position) and `USART_CR1_UE_Msk` (mask).
- Linux: `GENMASK()`, `BIT(n)`, `FIELD_PREP()`, `FIELD_GET()`, and `GENMASK_ULL()` for 64-bit.

**Follow-up:** "Why `~0u` and not `~0`?" `~0` is `-1` as a signed int, and shifting a negative value left is undefined. `~0u` is unsigned.

### How do you rotate bits left and right? {M}
**Short answer:** Combine two shifts with OR: rotate left is `(x << n) | (x >> (32 - n))`. Mask the shift amounts with `& 31` so that `n = 0` does not produce a shift by 32, which is undefined.

```c
#include <stdint.h>

static inline uint32_t rotl32(uint32_t x, unsigned n)
{
    n &= 31;
    return (x << n) | (x >> ((32 - n) & 31));
}

static inline uint32_t rotr32(uint32_t x, unsigned n)
{
    n &= 31;
    return (x >> n) | (x << ((32 - n) & 31));
}
```

**Rotate vs shift:** a shift throws away the bits that fall off one end and fills with zeros. A rotate puts the bits that fall off one end back in at the other end, so no information is lost.

```
x          = 0x80000001
x << 1     = 0x00000002   (top bit lost)
rotl(x, 1) = 0x00000003   (top bit wrapped to bit 0)
```

**Why the `& 31`:** for `n = 0`, the naive `x >> (32 - 0)` is a shift by 32, which is undefined in C. On Arm the `LSR` by 32 gives 0, but on x86 the shift count is masked to 5 bits and gives `x`. Undefined behaviour means the optimiser may assume it never happens.

**The compiler recognises this pattern** and emits one instruction: `ROR` on Arm (there is no rotate-left; it uses `ROR` by `32 - n`), `ROL`/`ROR` on x86. C23 adds `stdc_rotate_left`/`stdc_rotate_right` to `<stdbit.h>`.

**Uses:** hash functions and CRC/crypto (SHA-256, ChaCha20 are built from rotates), circular LED patterns, and rotating a bitmap of round-robin slots.

**Rotate other widths:** for a `uint8_t`, use 7 and 8 instead of 31 and 32, and cast the result back to `uint8_t`, because the operands are promoted to `int` before shifting.

### How do you find the parity of a number? {M}
**Short answer:** Parity is whether the number of set bits is odd or even. Fold the word onto itself with XOR (`x ^= x >> 16; x ^= x >> 8; ...`) until one bit is left; that bit is 1 for odd parity. Or use `__builtin_parity(x)`.

```c
#include <stdbool.h>
#include <stdint.h>

bool parity_odd(uint32_t x)
{
    x ^= x >> 16;
    x ^= x >> 8;
    x ^= x >> 4;
    x ^= x >> 2;
    x ^= x >> 1;
    return x & 1u;          /* 1 = odd number of set bits */
}
```

**Why folding works:** XOR of two bits is their sum modulo 2. Each step adds the top half of the remaining bits to the bottom half (mod 2), so after five steps bit 0 holds the XOR of all 32 bits, which is the parity.

**Simple loop version:**

```c
bool parity_loop(uint32_t x)
{
    bool p = 0;
    while (x) { p = !p; x &= x - 1; }   /* flip once per set bit */
    return p;
}
```

**Even vs odd parity in protocols**

- **Even parity:** the transmitter sets the parity bit so the total number of 1s (data + parity) is even. The parity bit equals `parity_odd(data)`.
- **Odd parity:** the total must be odd, so the parity bit is the inverse.

A UART set to 8E1 sends 8 data bits, an even-parity bit and 1 stop bit. The receiver recomputes parity and flags a parity error if it does not match.

**What parity can and cannot do:** it detects any **odd** number of flipped bits but misses every even number (two flipped bits cancel). For better detection use a CRC; for correction use Hamming or ECC codes, which are built from several overlapping parity bits.

**Faster on a microcontroller:** a 16-entry nibble table, or `__builtin_parity`, which GCC lowers to an efficient sequence.

### How do you swap the two nibbles of a byte? {E}
A byte has two 4-bit nibbles. Shift the low nibble up, shift the high nibble down, and combine:

```c
uint8_t swap_nibbles(uint8_t x)
{
    return (uint8_t)((x << 4) | (x >> 4));
}
/* 0x5A -> 0xA5, 0x12 -> 0x21 */
```

Because `x` is promoted to `int` before shifting, `x << 4` can be up to 12 bits wide; the cast back to `uint8_t` discards the extra bits. The equivalent with explicit masks is `((x & 0x0F) << 4) | ((x & 0xF0) >> 4)`.

Uses: converting between packed BCD digit orders, some display and LCD controllers that expect nibble-swapped data, and as the first stage of reversing bits. Interviewers often extend it to swapping adjacent bits (masks `0x55`/`0xAA`) or reversing all bits of a byte.

### How do you check whether a number has alternating bits? {E}
**Short answer:** XOR the number with itself shifted right by one. For alternating bits, the result contains consecutive ones from the least significant bit through its highest set bit.

```c
#include <stdint.h>
#include <stdbool.h>
bool alternating(uint32_t n)
{
    uint32_t x = n ^ (n >> 1);
    return n != 0 && (x & (x + 1u)) == 0;
}
```

**Example (significant bits):**

```text
n       101010
n >> 1  010101
XOR     111111
x + 1  1000000
AND    0000000
```

**Complexity:** O(1) for a fixed-width integer. Leading zeros are ignored; zero is excluded by definition here. Unsigned wraparound is intentional.

**Interview takeaway:** XOR detects adjacent bit differences; the all-ones mask test validates the result.
