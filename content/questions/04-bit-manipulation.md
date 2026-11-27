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
Use a mask containing one set bit at position n. Bit positions are zero-based: bit 0 is the least significant bit.

#### 1. Code

```c
uint32_t mask = UINT32_C(1) << n;

x |= mask;             // Set
x &= ~mask;            // Clear
x ^= mask;             // Toggle
bool bit = (x & mask) != 0; // Check
```

Here n must be in the range 0–31.

#### 2. Worked example

Take x = 0x22 (00100010) and n = 3. The mask is 00001000.

<div style="max-width:620px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 150" width="100%" role="img" aria-label="Bit 3 mask changes 00100010 to 00101010 and clearing restores the original"><text x="8" y="24" font-size="11" fill="currentColor">Original</text><rect x="96" y="5" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="109.5" y="23" text-anchor="middle" font-size="13" fill="currentColor">0</text><rect x="125" y="5" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="138.5" y="23" text-anchor="middle" font-size="13" fill="currentColor">0</text><rect x="154" y="5" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="167.5" y="23" text-anchor="middle" font-size="13" fill="currentColor">1</text><rect x="183" y="5" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="196.5" y="23" text-anchor="middle" font-size="13" fill="currentColor">0</text><rect x="212" y="5" width="27" height="27" rx="3" fill="#16a34a" fill-opacity=".15" stroke="#16a34a"/><text x="225.5" y="23" text-anchor="middle" font-size="13" fill="currentColor">0</text><rect x="241" y="5" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="254.5" y="23" text-anchor="middle" font-size="13" fill="currentColor">0</text><rect x="270" y="5" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="283.5" y="23" text-anchor="middle" font-size="13" fill="currentColor">1</text><rect x="299" y="5" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="312.5" y="23" text-anchor="middle" font-size="13" fill="currentColor">0</text><text x="8" y="59" font-size="11" fill="currentColor">Mask</text><rect x="96" y="40" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="109.5" y="58" text-anchor="middle" font-size="13" fill="currentColor">0</text><rect x="125" y="40" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="138.5" y="58" text-anchor="middle" font-size="13" fill="currentColor">0</text><rect x="154" y="40" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="167.5" y="58" text-anchor="middle" font-size="13" fill="currentColor">0</text><rect x="183" y="40" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="196.5" y="58" text-anchor="middle" font-size="13" fill="currentColor">0</text><rect x="212" y="40" width="27" height="27" rx="3" fill="#16a34a" fill-opacity=".15" stroke="#16a34a"/><text x="225.5" y="58" text-anchor="middle" font-size="13" fill="currentColor">1</text><rect x="241" y="40" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="254.5" y="58" text-anchor="middle" font-size="13" fill="currentColor">0</text><rect x="270" y="40" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="283.5" y="58" text-anchor="middle" font-size="13" fill="currentColor">0</text><rect x="299" y="40" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="312.5" y="58" text-anchor="middle" font-size="13" fill="currentColor">0</text><text x="8" y="94" font-size="11" fill="currentColor">Set: OR</text><rect x="96" y="75" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="109.5" y="93" text-anchor="middle" font-size="13" fill="currentColor">0</text><rect x="125" y="75" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="138.5" y="93" text-anchor="middle" font-size="13" fill="currentColor">0</text><rect x="154" y="75" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="167.5" y="93" text-anchor="middle" font-size="13" fill="currentColor">1</text><rect x="183" y="75" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="196.5" y="93" text-anchor="middle" font-size="13" fill="currentColor">0</text><rect x="212" y="75" width="27" height="27" rx="3" fill="#16a34a" fill-opacity=".15" stroke="#16a34a"/><text x="225.5" y="93" text-anchor="middle" font-size="13" fill="currentColor">1</text><rect x="241" y="75" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="254.5" y="93" text-anchor="middle" font-size="13" fill="currentColor">0</text><rect x="270" y="75" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="283.5" y="93" text-anchor="middle" font-size="13" fill="currentColor">1</text><rect x="299" y="75" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="312.5" y="93" text-anchor="middle" font-size="13" fill="currentColor">0</text><text x="8" y="129" font-size="11" fill="currentColor">Clear result</text><rect x="96" y="110" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="109.5" y="128" text-anchor="middle" font-size="13" fill="currentColor">0</text><rect x="125" y="110" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="138.5" y="128" text-anchor="middle" font-size="13" fill="currentColor">0</text><rect x="154" y="110" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="167.5" y="128" text-anchor="middle" font-size="13" fill="currentColor">1</text><rect x="183" y="110" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="196.5" y="128" text-anchor="middle" font-size="13" fill="currentColor">0</text><rect x="212" y="110" width="27" height="27" rx="3" fill="#16a34a" fill-opacity=".15" stroke="#16a34a"/><text x="225.5" y="128" text-anchor="middle" font-size="13" fill="currentColor">0</text><rect x="241" y="110" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="254.5" y="128" text-anchor="middle" font-size="13" fill="currentColor">0</text><rect x="270" y="110" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="283.5" y="128" text-anchor="middle" font-size="13" fill="currentColor">1</text><rect x="299" y="110" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="312.5" y="128" text-anchor="middle" font-size="13" fill="currentColor">0</text></svg></div>

#### 3. Hardware example

```c
#define UART_ENABLE (UINT32_C(1) << 3)
```

Use this mask with the documented UART control register. A dedicated set/clear register is preferable when available because ordinary read-modify-write can lose concurrent updates or mishandle special register semantics.

**Interview takeaway:** OR sets, AND with inverted mask clears, XOR toggles, AND tests. Do not shift by a negative count or a count greater than or equal to the operand width.

### Is right shift of a negative number arithmetic or logical? {M}
A logical right shift fills vacated high bits with zeros. An arithmetic right shift replicates the sign bit. In traditional C standards, right shifting a negative signed integer is implementation-defined; an unsigned right shift is logical.

#### 1. Example on a typical two's-complement 32-bit target

```c
int32_t a = -8;
uint32_t b = (uint32_t)a;

int32_t s = a >> 1;
uint32_t u = b >> 1;
```

| Operation | Typical bit pattern | Value |
|---|---|---:|
| a | 0xFFFFFFF8 | -8 |
| Arithmetic right shift | 0xFFFFFFFC | -4 |
| Logical right shift | 0x7FFFFFFC | 2147483644 |

#### 2. ARM instructions

```asm
ASR W0, W0, #1  // Arithmetic
LSR W1, W1, #1  // Logical
```

The compiler chooses an instruction according to operand type and implementation semantics.

#### 3. Why division is different

On a target using arithmetic right shift, -3 >> 1 commonly gives -2. In C99 and later, -3 / 2 gives -1 because signed integer division truncates toward zero.

**Interview takeaway:** Use unsigned types for portable logical shifts. Do not assume negative signed shifts are equivalent to division, and never use out-of-range shift counts.

### How do you check if a number is a power of two? {E}
A positive power of two contains exactly one set bit. Clearing its lowest set bit therefore produces zero.

#### 1. C implementation

```c
#include <stdint.h>
#include <stdbool.h>

bool is_power_of_two(uint32_t n)
{
    return n != 0 && (n & (n - 1)) == 0;
}
```

#### 2. Why it works

```text
n     = 00001000 (8)
n - 1 = 00000111 (7)
AND   = 00000000

n     = 00001010 (10)
n - 1 = 00001001 (9)
AND   = 00001000
```

Subtracting one clears the lowest set bit and sets every lower bit. AND removes that lowest set bit while preserving higher set bits.

#### 3. Edge cases

| n | Result |
|---:|---|
| 0 | False |
| 1 | True |
| 8 | True |
| 10 | False |

Zero must be explicitly rejected because zero AND any value is zero.

#### 4. Embedded use

Power-of-two sizes are useful for ring buffers, cache alignment and hardware resource sizes. For a nonzero power-of-two ring size N, an unsigned index can wrap using index & (N - 1).

**Interview takeaway:** The test is O(1), uses no loop and requires a nonzero unsigned input.

### How do you clear the rightmost (lowest) set bit, and what other tricks use n & (n - 1)? {E}
`n & (n - 1)` clears the least significant set bit of a nonzero unsigned integer.

#### 1. Worked example

```text
n       = 00101100 (44)
n - 1   = 00101011 (43)
AND     = 00101000 (40)
```

Subtracting one changes the lowest one into zero and changes all lower zeros into ones. AND preserves the higher bits but removes the selected one.

#### 2. C code

```c
uint32_t clear_lowest(uint32_t n)
{
    return n & (n - 1U);
}
```

For n = 0, unsigned arithmetic wraps or is converted according to the operand types, and the result is zero on normal uint32_t targets.

#### 3. Related interview tricks

| Goal | Operation |
|---|---|
| Check power of two | n != 0 && (n & (n - 1)) == 0 |
| Clear all set bits one at a time | Repeat n &= n - 1 |
| Count set bits | Count those iterations |
| Remove lowest pending flag | n &= n - 1 |

Example processing a software snapshot of pending interrupt flags:

```c
while (pending != 0) {
    unsigned bit = __builtin_ctz(pending);
    handle_event(bit);
    pending &= pending - 1U;
}
```

This assumes pending has the type expected by the builtin. The actual device interrupt must be acknowledged using its documented semantics.

**Interview takeaway:** Clearing one set bit at a time makes algorithms proportional to the number of set bits, not the entire integer width.

### How do you count the set bits in an integer? {M}
Set-bit counting (population count) returns the number of ones in an integer's binary representation.

#### 1. Basic method

```c
int count_bits(uint32_t n)
{
    int count = 0;
    while (n) {
        count += n & 1U;
        n >>= 1;
    }
    return count;
}
```

The loop examines one bit per iteration.

#### 2. Brian Kernighan's algorithm

```c
int count_bits(uint32_t n)
{
    int count = 0;
    while (n) {
        n &= n - 1U;
        count++;
    }
    return count;
}
```

Each iteration clears exactly one set bit.

<div style="max-width:620px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 142" width="100%" role="img" aria-label="Kernighan algorithm removes three set bits in three iterations"><text x="8" y="24" font-size="11" fill="currentColor">Start</text><rect x="79" y="5" width="28" height="27" rx="3" fill="#16a34a" fill-opacity=".18" stroke="#16a34a"/><text x="93" y="23" font-size="13" text-anchor="middle" fill="currentColor">1</text><rect x="110" y="5" width="28" height="27" rx="3" fill="#94a3b8" fill-opacity=".18" stroke="#94a3b8"/><text x="124" y="23" font-size="13" text-anchor="middle" fill="currentColor">0</text><rect x="141" y="5" width="28" height="27" rx="3" fill="#16a34a" fill-opacity=".18" stroke="#16a34a"/><text x="155" y="23" font-size="13" text-anchor="middle" fill="currentColor">1</text><rect x="172" y="5" width="28" height="27" rx="3" fill="#16a34a" fill-opacity=".18" stroke="#16a34a"/><text x="186" y="23" font-size="13" text-anchor="middle" fill="currentColor">1</text><rect x="203" y="5" width="28" height="27" rx="3" fill="#94a3b8" fill-opacity=".18" stroke="#94a3b8"/><text x="217" y="23" font-size="13" text-anchor="middle" fill="currentColor">0</text><rect x="234" y="5" width="28" height="27" rx="3" fill="#94a3b8" fill-opacity=".18" stroke="#94a3b8"/><text x="248" y="23" font-size="13" text-anchor="middle" fill="currentColor">0</text><rect x="265" y="5" width="28" height="27" rx="3" fill="#94a3b8" fill-opacity=".18" stroke="#94a3b8"/><text x="279" y="23" font-size="13" text-anchor="middle" fill="currentColor">0</text><rect x="296" y="5" width="28" height="27" rx="3" fill="#94a3b8" fill-opacity=".18" stroke="#94a3b8"/><text x="310" y="23" font-size="13" text-anchor="middle" fill="currentColor">0</text><text x="8" y="58" font-size="11" fill="currentColor">Step 1</text><rect x="79" y="39" width="28" height="27" rx="3" fill="#16a34a" fill-opacity=".18" stroke="#16a34a"/><text x="93" y="57" font-size="13" text-anchor="middle" fill="currentColor">1</text><rect x="110" y="39" width="28" height="27" rx="3" fill="#94a3b8" fill-opacity=".18" stroke="#94a3b8"/><text x="124" y="57" font-size="13" text-anchor="middle" fill="currentColor">0</text><rect x="141" y="39" width="28" height="27" rx="3" fill="#16a34a" fill-opacity=".18" stroke="#16a34a"/><text x="155" y="57" font-size="13" text-anchor="middle" fill="currentColor">1</text><rect x="172" y="39" width="28" height="27" rx="3" fill="#94a3b8" fill-opacity=".18" stroke="#94a3b8"/><text x="186" y="57" font-size="13" text-anchor="middle" fill="currentColor">0</text><rect x="203" y="39" width="28" height="27" rx="3" fill="#94a3b8" fill-opacity=".18" stroke="#94a3b8"/><text x="217" y="57" font-size="13" text-anchor="middle" fill="currentColor">0</text><rect x="234" y="39" width="28" height="27" rx="3" fill="#94a3b8" fill-opacity=".18" stroke="#94a3b8"/><text x="248" y="57" font-size="13" text-anchor="middle" fill="currentColor">0</text><rect x="265" y="39" width="28" height="27" rx="3" fill="#94a3b8" fill-opacity=".18" stroke="#94a3b8"/><text x="279" y="57" font-size="13" text-anchor="middle" fill="currentColor">0</text><rect x="296" y="39" width="28" height="27" rx="3" fill="#94a3b8" fill-opacity=".18" stroke="#94a3b8"/><text x="310" y="57" font-size="13" text-anchor="middle" fill="currentColor">0</text><text x="8" y="92" font-size="11" fill="currentColor">Step 2</text><rect x="79" y="73" width="28" height="27" rx="3" fill="#16a34a" fill-opacity=".18" stroke="#16a34a"/><text x="93" y="91" font-size="13" text-anchor="middle" fill="currentColor">1</text><rect x="110" y="73" width="28" height="27" rx="3" fill="#94a3b8" fill-opacity=".18" stroke="#94a3b8"/><text x="124" y="91" font-size="13" text-anchor="middle" fill="currentColor">0</text><rect x="141" y="73" width="28" height="27" rx="3" fill="#94a3b8" fill-opacity=".18" stroke="#94a3b8"/><text x="155" y="91" font-size="13" text-anchor="middle" fill="currentColor">0</text><rect x="172" y="73" width="28" height="27" rx="3" fill="#94a3b8" fill-opacity=".18" stroke="#94a3b8"/><text x="186" y="91" font-size="13" text-anchor="middle" fill="currentColor">0</text><rect x="203" y="73" width="28" height="27" rx="3" fill="#94a3b8" fill-opacity=".18" stroke="#94a3b8"/><text x="217" y="91" font-size="13" text-anchor="middle" fill="currentColor">0</text><rect x="234" y="73" width="28" height="27" rx="3" fill="#94a3b8" fill-opacity=".18" stroke="#94a3b8"/><text x="248" y="91" font-size="13" text-anchor="middle" fill="currentColor">0</text><rect x="265" y="73" width="28" height="27" rx="3" fill="#94a3b8" fill-opacity=".18" stroke="#94a3b8"/><text x="279" y="91" font-size="13" text-anchor="middle" fill="currentColor">0</text><rect x="296" y="73" width="28" height="27" rx="3" fill="#94a3b8" fill-opacity=".18" stroke="#94a3b8"/><text x="310" y="91" font-size="13" text-anchor="middle" fill="currentColor">0</text><text x="8" y="126" font-size="11" fill="currentColor">Step 3</text><rect x="79" y="107" width="28" height="27" rx="3" fill="#94a3b8" fill-opacity=".18" stroke="#94a3b8"/><text x="93" y="125" font-size="13" text-anchor="middle" fill="currentColor">0</text><rect x="110" y="107" width="28" height="27" rx="3" fill="#94a3b8" fill-opacity=".18" stroke="#94a3b8"/><text x="124" y="125" font-size="13" text-anchor="middle" fill="currentColor">0</text><rect x="141" y="107" width="28" height="27" rx="3" fill="#94a3b8" fill-opacity=".18" stroke="#94a3b8"/><text x="155" y="125" font-size="13" text-anchor="middle" fill="currentColor">0</text><rect x="172" y="107" width="28" height="27" rx="3" fill="#94a3b8" fill-opacity=".18" stroke="#94a3b8"/><text x="186" y="125" font-size="13" text-anchor="middle" fill="currentColor">0</text><rect x="203" y="107" width="28" height="27" rx="3" fill="#94a3b8" fill-opacity=".18" stroke="#94a3b8"/><text x="217" y="125" font-size="13" text-anchor="middle" fill="currentColor">0</text><rect x="234" y="107" width="28" height="27" rx="3" fill="#94a3b8" fill-opacity=".18" stroke="#94a3b8"/><text x="248" y="125" font-size="13" text-anchor="middle" fill="currentColor">0</text><rect x="265" y="107" width="28" height="27" rx="3" fill="#94a3b8" fill-opacity=".18" stroke="#94a3b8"/><text x="279" y="125" font-size="13" text-anchor="middle" fill="currentColor">0</text><rect x="296" y="107" width="28" height="27" rx="3" fill="#94a3b8" fill-opacity=".18" stroke="#94a3b8"/><text x="310" y="125" font-size="13" text-anchor="middle" fill="currentColor">0</text></svg></div>

Result: 3.

#### 3. Complexity and alternatives

| Method | Iterations |
|---|---|
| Shift method | Up to word width |
| Kernighan | Exactly number of set bits |
| Compiler builtin | Target-dependent optimized implementation |

GCC/Clang provide __builtin_popcount for unsigned int and width variants for larger types. The compiler may select a hardware instruction or optimized software sequence.

**Interview takeaway:** Kernighan is particularly effective for sparse masks. For production code, a suitable population-count builtin is usually clearer and lets the compiler choose the best implementation.

### How do you swap two numbers without a temporary variable? {E}
Two integer values can be swapped without an explicit temporary variable using XOR. This is an interview exercise rather than a preferred production pattern.

#### 1. XOR swap

```c
void swap(unsigned int *a, unsigned int *b)
{
    if (a == b)
        return;

    *a ^= *b;
    *b ^= *a;
    *a ^= *b;
}
```

Both pointers must refer to valid unsigned int objects.

#### 2. Example

| Step | a | b |
|---|---:|---:|
| Initial | 5 | 3 |
| a = a XOR b | 6 | 3 |
| b = b XOR a | 6 | 5 |
| a = a XOR b | 3 | 5 |

The identity x XOR x = 0 and x XOR 0 = x makes this work. If both pointers refer to the same object, the unguarded algorithm would clear it.

#### 3. Why not addition and subtraction?

The pattern a = a + b; b = a - b; a = a - b may overflow signed integers, causing undefined behavior. Unsigned modular arithmetic can be used, but the approach has similar readability and aliasing drawbacks.

#### 4. Preferred solution

```c
unsigned int tmp = *a;
*a = *b;
*b = tmp;
```

Compilers normally allocate a temporary register or optimize the swap efficiently. The XOR version introduces dependent operations and is not inherently faster.

**Interview takeaway:** Know the XOR identity and same-address corner case, but use a temporary variable for clear, maintainable C.

### How do you find the position of the lowest set bit? {M}
The lowest set bit is the first one encountered when scanning an integer from its least significant end. Its index is also the number of trailing zeros.

#### 1. Simple implementation

```c
int lowest_set_bit(uint32_t n)
{
    if (n == 0)
        return -1;

    int position = 0;
    while ((n & 1U) == 0) {
        n >>= 1;
        position++;
    }
    return position;
}
```

For n = 40 (00101000), the result is 3.

#### 2. Isolate the lowest set bit

```c
uint32_t mask = n & (uint32_t)(0U - n);
```

On a conventional unsigned 32-bit target, n = 40 gives mask = 8. The mask is a value, not the bit index.

#### 3. Compiler builtin

```c
int pos = n ? __builtin_ctz((unsigned int)n) : -1;
```

This variant assumes unsigned int can represent all uint32_t values. The traditional builtin is undefined for zero. AArch64 can implement trailing-zero counting using RBIT followed by CLZ, or a dedicated instruction on supporting architectures.

#### 4. Use in firmware

A software scheduler or interrupt dispatcher may keep pending events in a bitmap. Finding the lowest set bit selects one pending event without scanning all positions.

**Interview takeaway:** CTZ gives the zero-based index; n & -n isolates a one-bit mask for unsigned n. Handle zero explicitly.

### How do you reverse the bits of a byte or an n-bit number? {E}
Bit reversal changes the order of individual bits, not the order of bytes. An n-bit value is reversed by moving its least significant bit into the most significant position of the result.

#### 1. Reverse an eight-bit value

```c
#include <stdint.h>

uint8_t reverse8(uint8_t x)
{
    uint8_t out = 0;

    for (unsigned i = 0; i < 8; i++) {
        out = (uint8_t)((out << 1) | (x & 1U));
        x >>= 1;
    }
    return out;
}
```

For input 00010110 (0x16), the output is 01101000 (0x68).

#### 2. General n-bit reversal

```c
uint32_t reverse_n(uint32_t x, unsigned n)
{
    uint32_t out = 0;
    if (n > 32)
        return 0; // Invalid width

    for (unsigned i = 0; i < n; i++) {
        out = (out << 1) | (x & 1U);
        x >>= 1;
    }
    return out;
}
```

This reverses only the lowest n bits and returns them in the lowest n positions. For n = 0, the result is zero.

#### 3. Example of one iteration

Read the rightmost input bit using x & 1, shift the output left to make space, append that bit, then shift the input right.

This is useful for bit-oriented protocols, some CRC implementations and bit-order conversion when hardware requires it.

**Interview takeaway:** A byte swap preserves the bits within each byte. Bit reversal reverses every selected bit; a fixed width must be specified.

### How do you reverse the bits of a 32-bit integer? {M}
A 32-bit bit reversal maps bit i to bit 31-i. It can be implemented with a loop or a fixed sequence of mask-and-shift operations.

#### 1. Simple loop

```c
uint32_t reverse32(uint32_t n)
{
    uint32_t out = 0;
    for (unsigned i = 0; i < 32; i++) {
        out = (out << 1) | (n & 1U);
        n >>= 1;
    }
    return out;
}
```

For input 0x00000001, the result is 0x80000000.

#### 2. Parallel bit reversal

```c
uint32_t reverse32_fast(uint32_t x)
{
    x = ((x & 0x55555555U) << 1) |
        ((x >> 1) & 0x55555555U);
    x = ((x & 0x33333333U) << 2) |
        ((x >> 2) & 0x33333333U);
    x = ((x & 0x0F0F0F0FU) << 4) |
        ((x >> 4) & 0x0F0F0F0FU);
    x = ((x & 0x00FF00FFU) << 8) |
        ((x >> 8) & 0x00FF00FFU);
    return (x << 16) | (x >> 16);
}
```

Each stage swaps neighboring groups of 1, 2, 4, 8 and 16 bits. After all five stages every bit has moved to its reversed position.

#### 3. ARM alternative

```asm
RBIT W0, W0
```

AArch64 provides RBIT. Some Cortex-M implementations also support bit reversal directly; use a documented intrinsic if available.

**Interview takeaway:** Bit reversal is not a byte swap. The loop is simple, the mask-based version has fixed operation count, and hardware can provide an even more efficient implementation.

### How do you swap the odd and even bits of a number? {M}
Swapping odd and even bits means exchanging bit 0 with bit 1, bit 2 with bit 3, and so on.

#### 1. Masks

For a 32-bit value, 0xAAAAAAAA selects odd-numbered bit positions and 0x55555555 selects even-numbered positions (zero-based).

```c
uint32_t swap_adjacent(uint32_t x)
{
    return ((x & 0xAAAAAAAAU) >> 1) |
           ((x & 0x55555555U) << 1);
}
```

#### 2. Example

```text
x       = 1001 0110 (0x96)
odd     = 1000 0010
odd >>1 = 0100 0001
even    = 0001 0100
even<<1 = 0010 1000
OR      = 0110 1001 (0x69)
```

Odd bits move one position right; even bits move one position left. The two fields do not overlap after shifting.

#### 3. Applications

Adjacent-bit swaps are a building block for parallel bit reversal and certain protocol or hardware-lane transformations. Only use the transformation when the actual data format requires it.

**Interview takeaway:** Separate disjoint bit groups, shift each to its destination and OR the results. This swap is its own inverse.

### How do you set all bits in a range from position l to r? {M}
To set all bits in an inclusive range l through r, construct a mask with ones in those positions and OR it into the original value.

#### 1. 32-bit mask construction

```c
#include <stdint.h>
#include <stdbool.h>

bool set_range(uint32_t *x, unsigned l, unsigned r)
{
    if (!x || l > r || r >= 32)
        return false;

    uint32_t mask = (UINT32_MAX << l) &
                    (UINT32_MAX >> (31U - r));
    *x |= mask;
    return true;
}
```

Positions are zero-based. The first mask retains bits 31:l; the second retains bits r:0. Their AND selects exactly bits r:l. Valid shifts are always between 0 and 31.

#### 2. Worked example

Set bits 3 through 5 in x = 0x02.

```text
x       = 00000010
mask    = 00111000
x|mask  = 00111010 (0x3A)
```

With one-based positions 4 through 6, convert the bounds to zero-based positions 3 through 5 before applying the function.

#### 3. Other operations on the range

```c
x |= mask;   // Set range
x &= ~mask;  // Clear range
x ^= mask;   // Toggle range
```

These operate on ordinary unsigned values. Hardware registers may prohibit read-modify-write.

**Interview takeaway:** Validate bit indices and avoid a shift by the full width. This mask formula handles the complete range 0–31 without evaluating 1U << 32.

### How do you extract or insert a bit field? {E}
A bit field is a group of adjacent bits that represents a numeric value, such as a peripheral's mode selection. Extract it by shifting and masking; insert it by clearing the old field and combining the new field.

#### 1. Example: bits 6:4

```c
#define MODE_SHIFT 4U
#define MODE_MASK  (UINT32_C(7) << MODE_SHIFT)

uint32_t mode = (reg & MODE_MASK) >> MODE_SHIFT;

reg = (reg & ~MODE_MASK) |
      ((UINT32_C(5) << MODE_SHIFT) & MODE_MASK);
```

The extraction produces a value from 0 to 7. The insertion sets the field to 5 and preserves other bits.

<div style="max-width:620px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 111" width="100%" role="img" aria-label="Eight-bit register with bits 6 through 4 selected as a three-bit mode field">
<text x="30" y="16" font-size="10" text-anchor="middle" fill="currentColor">7</text><rect x="10" y="24" width="40" height="35" fill="#94a3b8" fill-opacity=".17" stroke="#94a3b8"/><text x="30" y="46" font-size="13" text-anchor="middle" fill="currentColor">0</text><text x="70" y="16" font-size="10" text-anchor="middle" fill="currentColor">6</text><rect x="50" y="24" width="40" height="35" fill="#16a34a" fill-opacity=".17" stroke="#16a34a"/><text x="70" y="46" font-size="13" text-anchor="middle" fill="currentColor">1</text><text x="110" y="16" font-size="10" text-anchor="middle" fill="currentColor">5</text><rect x="90" y="24" width="40" height="35" fill="#16a34a" fill-opacity=".17" stroke="#16a34a"/><text x="110" y="46" font-size="13" text-anchor="middle" fill="currentColor">0</text><text x="150" y="16" font-size="10" text-anchor="middle" fill="currentColor">4</text><rect x="130" y="24" width="40" height="35" fill="#16a34a" fill-opacity=".17" stroke="#16a34a"/><text x="150" y="46" font-size="13" text-anchor="middle" fill="currentColor">1</text><text x="190" y="16" font-size="10" text-anchor="middle" fill="currentColor">3</text><rect x="170" y="24" width="40" height="35" fill="#94a3b8" fill-opacity=".17" stroke="#94a3b8"/><text x="190" y="46" font-size="13" text-anchor="middle" fill="currentColor">0</text><text x="230" y="16" font-size="10" text-anchor="middle" fill="currentColor">2</text><rect x="210" y="24" width="40" height="35" fill="#94a3b8" fill-opacity=".17" stroke="#94a3b8"/><text x="230" y="46" font-size="13" text-anchor="middle" fill="currentColor">0</text><text x="270" y="16" font-size="10" text-anchor="middle" fill="currentColor">1</text><rect x="250" y="24" width="40" height="35" fill="#94a3b8" fill-opacity=".17" stroke="#94a3b8"/><text x="270" y="46" font-size="13" text-anchor="middle" fill="currentColor">0</text><text x="310" y="16" font-size="10" text-anchor="middle" fill="currentColor">0</text><rect x="290" y="24" width="40" height="35" fill="#94a3b8" fill-opacity=".17" stroke="#94a3b8"/><text x="310" y="46" font-size="13" text-anchor="middle" fill="currentColor">0</text><path d="M50 65 V72 H170 V65" stroke="#16a34a" fill="none"/><text x="110" y="86" font-size="11" text-anchor="middle" fill="currentColor">Mode = 101 (5)</text><text x="170" y="104" font-size="10" text-anchor="middle" fill="currentColor">Shift right by 4 after masking.</text></svg></div>

#### 2. Validate the field value

If the caller provides a value, reject values larger than the field can represent when truncation would be incorrect. A mask silently discards excess bits.

#### 3. Linux driver helpers

Linux provides FIELD_GET and FIELD_PREP for suitably defined contiguous masks, and GENMASK for constructing a range. Register writes still need the appropriate MMIO API and hardware semantics.

**Interview takeaway:** Extract with mask then shift; insert with clear then OR. Do not alter reserved bits or blindly use RMW on special registers.

### How do you check if two integers have opposite signs? {E}
Two integers have opposite signs when exactly one is negative. Zero is nonnegative in this test.

#### 1. Portable C implementation

```c
#include <stdbool.h>

bool opposite_sign(int a, int b)
{
    return (a < 0) != (b < 0);
}
```

This avoids arithmetic overflow and does not depend on integer representation.

#### 2. Bitwise alternative

On a conventional two's-complement system:

```c
bool opposite = (a ^ b) < 0;
```

XOR makes the sign bit one when the two sign bits differ. The comparison form above is clearer and portable across C implementations.

| a | b | Result |
|---:|---:|---|
| -5 | 3 | True |
| 5 | 3 | False |
| -5 | -3 | False |
| -5 | 0 | True (negative vs nonnegative) |

If the requirement is strictly positive versus strictly negative, explicitly reject zero.

#### 3. Why not multiply?

Testing a*b < 0 can overflow signed integers and gives different zero semantics.

**Interview takeaway:** Compare sign conditions directly. Do not multiply values just to determine their signs.

### How do you check if a number is even or odd using bitwise operators? {E}
The least significant bit of a binary integer indicates whether its value is even or odd.

#### 1. C implementation

```c
bool is_odd(unsigned int n)
{
    return (n & 1U) != 0;
}
```

The mask 1 preserves only bit 0.

#### 2. Example

```text
6 = 0110;  0110 & 0001 = 0 (even)
7 = 0111;  0111 & 0001 = 1 (odd)
```

For signed values, casting to unsigned before testing the lowest bit gives the same mathematical parity, including negative numbers:

```c
bool odd = ((unsigned int)value & 1U) != 0;
```

#### 3. Modulo comparison

```c
bool odd = (value % 2) != 0;
```

This also works with negative values. A compiler normally optimizes a parity test without needing manual division.

**Interview takeaway:** Test bit zero for parity. Use unsigned operands for bit operations and do not confuse odd/even parity with the parity of the number of set bits.

### How do you find the absolute value without branching? {M}
A branchless absolute-value algorithm can use an unsigned sign mask. Returning an unsigned magnitude avoids the signed overflow problem for INT_MIN.

#### 1. Safe unsigned magnitude

```c
unsigned int magnitude(int n)
{
    unsigned int u = (unsigned int)n;
    unsigned int mask = 0U - (unsigned int)(n < 0);
    return (u ^ mask) - mask;
}
```

For nonnegative n, mask is zero. For negative n, mask is UINT_MAX, so the expression computes the unsigned modular negation of u.

#### 2. Example using eight-bit illustrations

```text
n = -5
u    = 11111011
mask = 11111111
XOR  = 00000100
subtract mask modulo 256 = 00000101 (5)
```

Actual unsigned int width is target-dependent.

#### 3. INT_MIN corner case

On a typical 32-bit two's-complement machine, INT_MIN is -2147483648, whose magnitude 2147483648 cannot fit in int but fits in unsigned int.

Calling abs(INT_MIN) is undefined when its magnitude cannot be represented by int. The unsigned approach represents that magnitude.

#### 4. Is it always branchless?

The C source has no conditional branch statement, but the compiler decides which machine instructions to generate. A normal conditional expression can also compile to branchless instructions.

**Interview takeaway:** Handle the minimum signed value explicitly. Prefer correct unsigned arithmetic over tricks relying on signed shifts or overflow.

### How do you round up to the next power of two? {M}
To round a positive unsigned integer up to the next power of two (including itself), spread its highest set bit to all lower positions, then add one.

#### 1. 32-bit implementation

```c
uint32_t next_pow2(uint32_t n)
{
    if (n <= 1)
        return 1;
    if (n > UINT32_C(0x80000000))
        return 0; // Overflow: no representable power

    n--;
    n |= n >> 1;
    n |= n >> 2;
    n |= n >> 4;
    n |= n >> 8;
    n |= n >> 16;
    return n + 1U;
}
```

Subtracting first ensures exact powers of two remain unchanged.

#### 2. Example: n = 10

```text
n-1           = 00001001
OR with >> 1  = 00001101
OR with >> 2  = 00001111
Remaining shifts leave the mask unchanged.
Add one       = 00010000 (16)
```

| Input | Result |
|---:|---:|
| 0 | 1 (chosen convention) |
| 1 | 1 |
| 8 | 8 |
| 10 | 16 |

#### 3. Embedded use

Power-of-two buffers allow wrapping an unsigned index with a mask. Increasing capacity may waste memory; check available RAM and multiplication overflow before allocating.

**Interview takeaway:** Handle zero, exact powers and overflow before bit spreading. This implementation returns zero as an explicit overflow sentinel.

### How do you align a value up or down to a power-of-two boundary? {E}
For a power-of-two alignment A, aligned values have their lowest log2(A) bits cleared.

#### 1. Align down

```c
uintptr_t down = value & ~(A - 1);
```

Assume A is a nonzero power-of-two uintptr_t. For value = 0x1035 and A = 16, down is 0x1030.

#### 2. Align up

```c
uintptr_t up = (value + A - 1) & ~(A - 1);
```

For the same example, up is 0x1040. Adding A-1 allows rounding to the next boundary before clearing the low bits.

#### 3. Safe implementation

```c
bool align_up(uintptr_t v, uintptr_t a, uintptr_t *out)
{
    if (!out || !a || (a & (a - 1)))
        return false;

    uintptr_t mask = a - 1;
    if (v > UINTPTR_MAX - mask)
        return false;

    *out = (v + mask) & ~mask;
    return true;
}
```

This conservatively rejects overflow of the intermediate sum.

#### 4. Embedded use

DMA buffers, cache lines and memory regions may require alignment. Rounding a pointer value is valid only when the resulting address is accessible and belongs to the appropriate allocated storage; reserve extra space when manually aligning buffers.

**Interview takeaway:** Mask-based rounding requires a nonzero power-of-two alignment. Validate the input, check overflow and respect allocation bounds.

### How do you compute x % 8 or x / 8 using bit operations? {E}
For unsigned integers, division and remainder by a power of two can be calculated using shifts and masks. Since 8 = 2³, shift by three bits to divide and keep the lowest three bits to obtain the remainder.

#### 1. Implementation

```c
uint32_t quotient  = x >> 3;
uint32_t remainder = x & 7U;
```

For x = 29:

```text
29 = 00011101
29 >> 3 = 00000011 = 3
29 & 7  = 00000101 = 5

29 = 3 * 8 + 5
```

#### 2. General case

For an unsigned value and valid k smaller than the operand width:

```c
uint32_t q = x >> k;
uint32_t r = x & ((UINT32_C(1) << k) - 1);
```

The divisor is 2 to the power k. The remainder ranges from zero through divisor minus one.

#### 3. Signed-number caveat

On a machine using arithmetic right shift, -9 >> 3 typically produces -2, whereas -9 / 8 in modern C produces -1. A bit mask also does not reproduce C's negative remainder in general.

#### 4. Embedded application

Power-of-two ring buffer sizes allow unsigned indices to wrap with a mask instead of a division operation. A compiler normally optimizes constant unsigned divisions by powers of two automatically.

**Interview takeaway:** Use shifts and masks for unsigned powers of two. Do not blindly substitute them for signed division and modulo.

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
