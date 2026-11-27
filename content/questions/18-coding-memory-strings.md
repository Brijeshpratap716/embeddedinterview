---
slug: coding-memory-strings
title: "Coding: Memory & String Functions"
icon: 🧪
level: Intermediate
order: 18
desc: Write the C library yourself: strlen, strcpy, strcmp, strcat, memcpy, memset, aligned_malloc, calloc, double-free and leak detection, slab allocators and string utilities.
---
"Implement this library function" is the most common first coding question in embedded interviews, including at NVIDIA, Qualcomm, Intel and automotive suppliers. Each answer gives compact, correct C and the points the interviewer checks: NULL and length handling, `'\0'` termination, overlap, alignment, and complexity.

### Implement strlen(). {E}
**Short answer:** Walk a pointer forward from the start of the string until it reaches the terminating `'\0'`, then return the distance between the two pointers. That distance is the number of characters before the terminator. Time is O(n) and extra space is O(1).

```c
#include <stddef.h>

size_t my_strlen(const char *s)
{
    const char *p = s;
    while (*p) p++;
    return (size_t)(p - s);          /* pointer difference = number of chars before '\0' */
}
```

**Points to mention:** returns `size_t`; does not count the terminator; undefined if `s` is NULL or not terminated (the library does not check NULL either). For a bounded version use `strnlen(s, max)`. Library implementations read a word at a time using the "has zero byte" trick after aligning the pointer.

**Step by step**

1. Save the starting address in `s` and use a second pointer `p` to scan.
2. While `*p` is not `'\0'`, advance `p`.
3. When the loop ends, `p` points at the terminator, so `p - s` is the length.

**Dry run:** for `"abc"`, `p` moves over `a`, `b`, `c` and stops at index 3 (`'\0'`); `p - s = 3`.

**Test cases to mention:** `""` → 0, `"a"` → 1, a string with spaces or non-ASCII bytes (each byte counts), a very long string (`size_t` result).

**Follow-ups interviewers ask**

- *Why `size_t` and not `int`?* Lengths can exceed `INT_MAX`, and `size_t` is what the standard uses.
- *Can you make it faster?* Align the pointer, then read 4 or 8 bytes at a time and test for a zero byte with `(w - 0x01010101) & ~w & 0x80808080`. Reading beyond the C object is not generally valid even if the address remains on the same mapped page; optimized libraries use implementation-specific guarantees.
- *What about NULL?* The standard does not require a check; in firmware you may add `if (!s) return 0;` defensively, but say that it hides bugs.
- *`sizeof` vs `strlen`:* `sizeof "abc"` is 4 (includes `'\0'`) and is compile time; `strlen` is 3 and runs at run time; `sizeof` of a `char *` gives the pointer size.

#### Bounded scan for firmware buffers

```c
size_t bounded_len(const char *s, size_t capacity)
{
    size_t n = 0;
    while (n < capacity && s[n] != '\0')
        ++n;
    return n;
}
```

If a UART receive buffer contains {'A','B','C','D'} with capacity 4, this returns 4 without reading outside the buffer. A return equal to capacity means no terminator was found. Unlike strlen, the caller can detect this malformed string safely when the supplied extent is valid.

### Implement strcpy() and a safe bounded copy. {E}
**Short answer:** `strcpy` copies characters from `src` to `dst` one at a time, including the final `'\0'`, and returns the original `dst`. It never checks the destination size, so the safe version (`strlcpy` style) takes the buffer size, copies at most `size - 1` characters, always terminates, and returns the full source length so the caller can detect truncation.

```c
#include <stddef.h>

char *my_strcpy(char *dst, const char *src)
{
    char *d = dst;
    while ((*d++ = *src++) != '\0') { }   /* copies the terminator too */
    return dst;
}

/* bounded: always terminates, returns strlen(src) so truncation can be detected (like strlcpy) */
size_t my_strlcpy(char *dst, const char *src, size_t size)
{
    size_t n = 0;
    while (src[n]) n++;
    if (size) {
        size_t c = (n >= size) ? size - 1 : n;
        for (size_t i = 0; i < c; i++) dst[i] = src[i];
        dst[c] = '\0';
    }
    return n;
}
```

**Points:** `strcpy` has no bounds check (classic overflow); overlapping buffers are undefined; return the original `dst`. Truncation happened if `my_strlcpy(...) >= size`.

**How `while ((*d++ = *src++) != '\0')` works:** the assignment copies one character and its value is then compared with `'\0'`. Because the copy happens before the test, the terminator is copied too, and then the loop stops.

**Dry run of `my_strlcpy(buf, "hello", 4)`:** `n = 5`; `size = 4` so `c = 3`; copies `h e l` and writes `'\0'` → `buf = "hel"`; returns 5. Since `5 >= 4`, the caller knows the result was truncated.

**Why not `strncpy`?** `strncpy(dst, src, n)` does **not** terminate the destination if `src` is `n` characters or longer, and it pads the rest with zeros when `src` is short (slow for big buffers). It was designed for fixed-width record fields, not safe strings.

**Points interviewers check**

- Return value is the **original** `dst` (save it before moving the pointer).
- `src` and `dst` must not overlap (undefined behaviour).
- `const char *src` because the source is not modified.
- Overflow risk: `strcpy` into a fixed buffer from external data (UART, network) is a classic security bug; use the bounded version or `snprintf`.

**Complexity:** O(n) time, O(1) space.

#### Why the terminator needs its own byte

For source "ABC", a destination of capacity 4 stores A, B, C and NUL. Capacity 3 can hold only "AB" as a valid C string. For an external input with an explicit received length, validate that length or find its terminator within the received extent before calling even a bounded destination-copy routine. Bounding the destination does not bound reads of a malformed source.

### Implement strcmp(). {E}
**Short answer:** Advance both pointers while the characters are equal and not the end of the first string. At the first difference (or when either string ends) return the difference of the two characters, compared as `unsigned char`. The result is negative if `a < b`, zero if equal, positive if `a > b`.

```c
int my_strcmp(const char *a, const char *b)
{
    while (*a && *a == *b) { a++; b++; }
    return (unsigned char)*a - (unsigned char)*b;
}
```

**Points:** the result is negative, zero or positive, not necessarily −1/0/1. Compare as `unsigned char`, as the standard requires, so bytes above 127 order correctly. The loop stops at the first difference or when `a` ends (if `b` ended first, `*b` is 0 and differs). `strncmp` adds a count limit.

**Dry run**

| a | b | loop stops at | result |
|---|---|---|---|
| `"abc"` | `"abd"` | index 2 (`c` vs `d`) | `'c' - 'd'` = −1 → a < b |
| `"abc"` | `"abc"` | index 3 (both `'\0'`) | 0 → equal |
| `"ab"` | `"abc"` | index 2 (`'\0'` vs `c`) | `0 - 'c'` < 0 → shorter string is smaller |

**Why `unsigned char`:** on platforms where `char` is signed, a byte like `0xE9` (é) would be negative and compare as smaller than `'a'`, which is wrong. The standard says comparison is done as `unsigned char`.

**Why the loop only checks `*a`:** if `*a` is not `'\0'` and `*a == *b`, then `*b` cannot be `'\0'` either, so one check is enough.

**Common mistakes**

- Returning only −1/0/1 is allowed, but callers must not assume it; always test `< 0`, `== 0`, `> 0`.
- Using `==` on two `char *` compares addresses, not contents.
- Forgetting that `strcmp` is case sensitive; a case-insensitive version applies `tolower` to both characters.

**Variant `strncmp(a, b, n)`:** add `n` to the loop condition and return 0 if `n` reaches 0 first.

**Complexity:** O(min(len a, len b)) time, O(1) space.

#### A bounded comparison

```c
int my_strncmp(const char *a, const char *b, size_t n)
{
    while (n--) {
        unsigned char x = (unsigned char)*a++;
        unsigned char y = (unsigned char)*b++;
        if (x != y) return x < y ? -1 : 1;
        if (x == 0) return 0;
    }
    return 0;
}
```

Comparing "UART0" with "UART1" for four bytes gives equality; comparing five bytes distinguishes the ports. This is lexicographical byte ordering, not numeric ordering: "10" sorts before "2".

### Implement strcat(). {E}
**Short answer:** Find the end of `dst` by scanning to its `'\0'`, then copy `src` (including its terminator) starting there, and return the original `dst`. The caller must guarantee that `dst` has room for both strings plus one byte.

```c
char *my_strcat(char *dst, const char *src)
{
    char *d = dst;
    while (*d) d++;                       /* find the end of dst */
    while ((*d++ = *src++) != '\0') { }   /* append, including '\0' */
    return dst;
}
```

**Points:** `dst` must have room for both strings plus the terminator; repeated `strcat` in a loop is O(n²) because each call rescans `dst` (keep a pointer to the end instead). Bounded alternative: `snprintf(dst + len, size - len, "%s", src)`.

**Dry run:** `char buf[16] = "Hi, "; my_strcat(buf, "Bob");` scans to index 4, copies `B o b \0` → `"Hi, Bob"`.

**Performance trap (Schlemiel the painter):** building a string with repeated `strcat` calls in a loop rescans the whole destination each time, giving O(n²). Keep a pointer to the end, or track the length:

```c
char *end = buf;
for (int i = 0; i < n; i++)
    end += sprintf(end, "%d,", vals[i]);      /* better: snprintf with remaining size */
```

**Safe bounded version (`strlcat` style):** scan at most `size` bytes for the terminator; if no terminator exists the buffer was not terminated → return; copy at most `size - len - 1` characters; terminate; return `len + strlen(src)` so truncation is visible.

**Points interviewers check:** overlapping `src`/`dst` is undefined, `dst` must already be a valid terminated string (an uninitialised buffer leads to scanning random memory), and the return value is the original `dst`.

**Complexity:** O(len(dst) + len(src)) time, O(1) space.

#### Capacity-aware concatenation

```c
bool append(char *dst, size_t cap, const char *src)
{
    size_t d = 0;
    while (d < cap && dst[d]) ++d;
    if (d == cap) return false;
    size_t n = strlen(src);
    if (n >= cap - d) return false;
    memcpy(dst + d, src, n + 1);
    return true;
}
```

This version rejects insufficient capacity without modifying the destination. It assumes a valid terminated source and nonoverlapping buffers. Track the used length in a packet or logging buffer to avoid repeatedly scanning the existing contents.

### Implement your own memcpy(). {E}
**Short answer (portable byte loop below; the word-copy example needs target-specific aliasing guarantees):** Copy `n` bytes from `src` to `dst` and return `dst`. The simple version is a byte loop. A faster version first copies single bytes until the destination is word aligned, then copies whole 32-bit words (only when source and destination have the same alignment), then copies the remaining tail bytes. Overlapping regions are not allowed; that is what `memmove` is for.

```c
#include <stddef.h>
#include <stdint.h>

void *target_specific_word_copy(void *restrict dst, const void *restrict src, size_t n)
{
    uint8_t *d = dst;
    const uint8_t *s = src;

    /* fast path: copy words when both pointers share the same alignment */
    if ((((uintptr_t)d ^ (uintptr_t)s) & (sizeof(uint32_t) - 1)) == 0) {
        while (n && ((uintptr_t)d & (sizeof(uint32_t) - 1))) { *d++ = *s++; n--; }
        uint32_t *dw = (uint32_t *)(void *)d;
        const uint32_t *sw = (const uint32_t *)(const void *)s;
        while (n >= 4) { *dw++ = *sw++; n -= 4; }
        d = (uint8_t *)dw;
        s = (const uint8_t *)sw;
    }
    while (n--) *d++ = *s++;              /* remaining bytes */
    return dst;
}
```

**Points:** behaviour is undefined for overlapping regions (that is `memmove`'s job); `restrict` lets the compiler optimise; copy words only when both addresses are aligned (otherwise Cortex-M0 faults); return `dst`. When writing a real libc, build it with `-fno-builtin` (or `-ffreestanding`) so the compiler does not turn your loop back into a call to `memcpy` itself. Do not use it on device registers (access width and `volatile`).

**Step by step for the fast path**

1. **Check alignment compatibility:** `(d ^ s) & 3 == 0` means both addresses have the same offset within a word, so after aligning one, the other is aligned too.
2. **Head:** copy bytes one by one until `d` is a multiple of 4.
3. **Body:** copy 4 bytes per iteration as `uint32_t`.
4. **Tail:** copy the last 0–3 bytes.

**Dry run:** `dst = 0x1001`, `src = 0x2001`, `n = 10` → copy 3 head bytes (to reach 0x1004), 1 word (4 bytes), then 3 tail bytes = 10 bytes total.

**Why alignment matters on MCUs:** Cortex-M0/M0+ fault on unaligned word access; Cortex-M3/M4 allow it for normal loads/stores but it is slower, and `LDM/STM` and some instructions still require alignment.

**Points interviewers check**

- `void *` parameters, `const` source, `restrict` (no overlap), return `dst`.
- `n == 0` works (loops do nothing).
- Do not use `memcpy` on peripheral registers: it may use byte or multi-word accesses that the hardware does not accept; use `volatile` accesses of the correct width.
- Real libraries unroll loops, use `LDM/STM` (8 registers at a time), or DMA for very large copies.

**Complexity:** O(n) time, O(1) space; the word version does about n/4 iterations.

#### Portable reference implementation

```c
void *copy_bytes(void *restrict dst,
                 const void *restrict src, size_t n)
{
    unsigned char *d = dst;
    const unsigned char *s = src;
    for (size_t i = 0; i < n; ++i)
        d[i] = s[i];
    return dst;
}
```

Unsigned char can access any object's representation. An ordinary uint32_t lvalue does not have that permission for arbitrary objects, even if aligned; library fast paths rely on compiler/target-specific aliasing guarantees or special implementations. This portable version is appropriate for interview code. DMA is a separate asynchronous transfer mechanism requiring suitable buffers, cache synchronization and completion.

### Implement memmove() with overlap handling. {E}
**Short answer:** `memmove` must work even when the source and destination regions overlap. If the destination starts before the source (or the regions do not overlap), copy forwards; if the destination starts inside the source region, copy backwards from the end, so every source byte is read before it is overwritten.

```c
#include <stddef.h>
#include <stdint.h>

void *my_memmove(void *dst, const void *src, size_t n)
{
    uint8_t *d = dst;
    const uint8_t *s = src;
    if (d == s || n == 0) return dst;
    if ((uintptr_t)d < (uintptr_t)s || (uintptr_t)d - (uintptr_t)s >= n) {
        while (n--) *d++ = *s++;          /* no harmful overlap: copy forward */
    } else {
        d += n; s += n;                   /* dst overlaps the tail of src: copy backward */
        while (n--) *--d = *--s;
    }
    return dst;
}
```

**Points:** copy backwards when the destination starts inside the source range, so source bytes are read before they are overwritten. Relational comparison of unrelated C object pointers is generally undefined. The uintptr_t approach assumes a flat, monotonically addressed implementation (typical embedded targets); integer conversions are implementation-defined. The subtraction avoids wrapping s + n.

**Why direction matters (example: shift right by 2)**

```
buffer:  A B C D E _ _        memmove(buf + 2, buf, 5)
forward copy: buf[2]=A overwrites C before C is copied → A B A B A B A   (wrong)
backward copy: buf[6]=E, buf[5]=D, buf[4]=C, buf[3]=B, buf[2]=A → A B A B C D E   (correct)
```

Shifting **left** (`memmove(buf, buf + 2, 5)`) is safe forwards, because each byte is read before the write pointer reaches it.

**Decision rule used in the code**

- `d < s` → forward is safe.
- `d >= s + n` → no overlap → forward.
- otherwise (`s < d < s + n`) → backward.

**Points interviewers check**

- `n == 0` and `d == s` handled (nothing to do).
- A temporary buffer is semantically valid but often undesirable in embedded systems because it needs O(n) additional space.
- Typical uses: removing an element from an array, inserting into a buffer, compacting a ring buffer, shifting a received frame.

**Complexity:** O(n) time, O(1) extra space. A word-sized optimisation works in both directions just like `memcpy`.

#### Choosing a copy direction

| Source offsets | Destination offsets | Correct approach |
|---|---|---|
| 0–4 | 2–6 | Backward |
| 2–6 | 0–4 | Forward |
| 0–4 | 8–12 | Either |

On conventional flat-address systems, uintptr_t ordering implements the overlap test. ISO C does not generally define relational comparisons between unrelated object pointers, and pointer-to-integer address ordering is implementation-dependent. For fully portable application code use the standard memmove rather than reproducing platform-specific internals.

### Implement your own memset(). {E}
**Short answer:** Fill `n` bytes starting at `dst` with the byte value `(unsigned char)c` and return `dst`. A faster version writes single bytes until the pointer is aligned, then writes 32-bit words containing the byte repeated four times (`0x01010101 * b`), then finishes the tail bytes.

```c
#include <stddef.h>
#include <stdint.h>

void *target_specific_word_fill(void *dst, int c, size_t n)
{
    uint8_t *d = dst;
    uint8_t b = (uint8_t)c;
    while (n && ((uintptr_t)d & 3u)) { *d++ = b; n--; }      /* align */
    uint32_t w = 0x01010101u * b;                             /* replicate the byte */
    uint32_t *dw = (uint32_t *)(void *)d;
    while (n >= 4) { *dw++ = w; n -= 4; }
    d = (uint8_t *)dw;
    while (n--) *d++ = b;
    return dst;
}
```

**Points:** `c` is converted to `unsigned char`; `memset(p, 1, n)` on an `int` array does **not** set each int to 1 (it sets every byte to 0x01, giving 0x01010101). To clear secrets, the compiler may delete a `memset` before `free`/return as a "dead store": use `memset_s`, `explicit_bzero`, or a `volatile` pointer loop.

**Byte replication trick:** `0x01010101 * 0xAB = 0xABABABAB`, because each `01` byte multiplies the value into one byte lane.

**Dry run:** `memset(p, 0, 10)` at `p = 0x2003` → 1 head byte (to 0x2004), 2 words (8 bytes), 1 tail byte.

**Classic interview trap**

```c
int a[4];
memset(a, 1, sizeof a);    /* each int becomes 0x01010101 = 16843009, not 1 */
memset(a, 0, sizeof a);    /* OK: all bytes 0 → all ints 0 */
memset(a, -1, sizeof a);   /* -1 on two's-complement int targets */
```

**Other points**

- Use `sizeof a` (the array) not `sizeof p` (a pointer) when clearing through a pointer parameter — a frequent bug.
- Clearing a struct with `memset(&s, 0, sizeof s)` sets pointers to NULL and floats to 0.0 on all mainstream platforms, but `= {0}` initialisation is cleaner.
- **Secure erase:** the compiler may remove `memset(key, 0, 32)` just before `key` goes out of scope because the store is "dead". Use `explicit_bzero`, `memset_s`, or write through a `volatile` pointer so key material really disappears.
- The startup code uses the same idea to zero `.bss`.

**Complexity:** O(n) time, O(1) space.

#### Portable byte fill

```c
void *fill_bytes(void *dst, int value, size_t n)
{
    unsigned char *p = dst;
    for (size_t i = 0; i < n; ++i)
        p[i] = (unsigned char)value;
    return dst;
}
```

On an eight-bit-byte target, value 0x123 fills every byte with 0x23. For an array of integers, assign each element in a loop when the requested value is not a repeated-byte representation. Word-sized stores require both alignment and valid aliasing semantics; the byte version avoids those assumptions.

### Implement aligned_malloc() and aligned_free(). {M}
**Short answer:** Allocate more memory than requested — `size + alignment - 1 + sizeof(void *)` — so that an aligned address with room for one pointer before it always exists inside the block. Round the address up to the alignment, store the original `malloc` pointer in the word just before the aligned address, and return the aligned address. `aligned_free` reads that stored pointer and passes it to `free`.

```c
#include <stdint.h>
#include <stdlib.h>

/* alignment must be a power of two */
void *aligned_malloc(size_t size, size_t alignment)
{
    if (alignment < sizeof(void *) || (alignment & (alignment - 1)) != 0)
        return NULL;
    size_t extra = alignment - 1 + sizeof(void *);       /* room to align + store the original */
    if (size > SIZE_MAX - extra) return NULL;            /* overflow check */
    void *raw = malloc(size + extra);
    if (raw == NULL) return NULL;
    uintptr_t start = (uintptr_t)raw + sizeof(void *);
    uintptr_t aligned = (start + alignment - 1) & ~(uintptr_t)(alignment - 1);
    ((void **)aligned)[-1] = raw;                        /* store original pointer just before */
    return (void *)aligned;
}

void aligned_free(void *p)
{
    if (p) free(((void **)p)[-1]);
}
```

**What the interviewer wants to hear**

1. Allocate `size + alignment − 1 + sizeof(void*)` bytes.
2. Skip space for one pointer, then round up to the alignment with `(x + a − 1) & ~(a − 1)`.
3. Store the original `malloc` pointer in the word immediately before the aligned address.
4. `aligned_free` reads that word and frees the original block.

**Follow-ups:** why `sizeof(void *)` extra (so there is always room to store the original pointer, even if `malloc` already returned an aligned address); why power of two (the mask trick); never pass the aligned pointer to plain `free`. Standard alternatives: C11 `aligned_alloc(alignment, size)` (size must be a multiple of the alignment), POSIX `posix_memalign`. Uses: DMA buffers aligned to cache lines (32/64 bytes), SIMD data (16 bytes), page-aligned buffers (4096).

**Memory picture (alignment 64)**

```
raw (from malloc)                    aligned (returned, multiple of 64)
|<- padding ->|<- void* raw ->|<---------------- size bytes ---------------->|
```

**Dry run:** `malloc` returns `raw = 0x20000014`, alignment 64, pointer size 4.
- `start = raw + 4 = 0x20000018`
- `aligned = (0x20000018 + 63) & ~63 = 0x20000040`
- store `raw` at `0x2000003C`; return `0x20000040`.
- Total extra used: 0x2C = 44 bytes ≤ 63 + 4.

**Why each piece is needed**

- `alignment - 1` extra bytes: worst case distance to the next aligned address.
- `sizeof(void *)` extra bytes: even if `raw + 4` is already aligned, there is always room for the stored pointer.
- Power-of-two alignment: makes rounding a mask operation `(x + a - 1) & ~(a - 1)`.
- `uintptr_t`: integer arithmetic on addresses is well defined, pointer arithmetic beyond the object is not.

**Variants interviewers ask:**

- Store a 16-bit **offset** instead of a full pointer to save memory (`aligned - raw` fits when alignment ≤ 64 KB).
- What if `malloc` returns NULL? Return NULL.
- What if someone calls `free(aligned)`? Heap corruption — document that `aligned_free` is mandatory.
- Real uses: DMA buffers on cache-line boundaries (so cache maintenance doesn't affect neighbours), SIMD buffers, MMU page tables (4 KB alignment).

**Complexity:** O(1) time; overhead up to `alignment - 1 + sizeof(void *)` bytes per allocation.

#### Example: 64-byte aligned allocation

Suppose malloc returns address 0x1003 (illustrative arithmetic only), and pointer metadata needs 8 bytes. Start rounding at 0x100B, yielding 0x1040. Save the original pointer in the preceding metadata space. The returned address satisfies (address & 63) == 0.

Reserve enough storage for both the adjustment and requested payload. Require alignment at least _Alignof(void *) and check all size arithmetic; prefer the platform's aligned allocation API when available. An aligned CPU pointer is not automatically a DMA bus address or a coherent buffer.

### Implement calloc() on top of your allocator. {E}
**Short answer:** `calloc(count, size)` allocates `count * size` bytes and zeroes them. The key part is checking that the multiplication does not overflow before allocating — if `count > SIZE_MAX / size`, return NULL — and then calling `memset(p, 0, total)` on success.

```c
#include <stdint.h>
#include <string.h>

void *my_malloc(size_t n);

void *my_calloc(size_t count, size_t size)
{
    if (size != 0 && count > SIZE_MAX / size)   /* count * size would overflow */
        return NULL;
    size_t total = count * size;
    void *p = my_malloc(total);
    if (p) memset(p, 0, total);
    return p;
}
```

**Points:** the multiplication overflow check is the whole reason `calloc` exists as a separate function; without it, `calloc(0x10000, 0x10001)` on 32-bit would allocate a tiny block and lead to a heap overflow. Real allocators skip the `memset` when the memory is known to be fresh zero pages from the OS.

**Why the overflow check is critical (32-bit example)**

`count = 0x10000`, `size = 0x10001` → true product 0x1_0001_0000 needs 33 bits; in 32-bit `size_t` it wraps to `0x10000` (65,536). Without the check you get a 64 KB block, the caller believes it has 4 GB and writes far past the end — a heap overflow and a well-known class of security bugs.

**Step by step**

1. If `size != 0` and `count > SIZE_MAX / size` → return NULL.
2. `total = count * size`.
3. `p = my_malloc(total)`; if NULL, return NULL.
4. Zero the memory and return `p`.

**Alternative overflow check:** `__builtin_mul_overflow(count, size, &total)` (GCC/Clang) or C23 `ckd_mul`.

**Edge cases:** `count == 0` or `size == 0` → allocate 0 bytes (may return NULL or a unique pointer; both allowed by the standard).

**Follow-up:** "Why is `calloc` sometimes faster than `malloc + memset`?" Large allocations come from fresh OS pages that are already zero, so a real `calloc` can skip the `memset`.

**Complexity:** O(total) for the zeroing.

#### Test the overflow boundary

On a target with 32-bit size_t, SIZE_MAX is 4294967295. A request for 65536 elements of size 65536 has mathematical size 4294967296, which is unrepresentable. Reject before multiplication. A request for three four-byte elements needs 12 zeroed bytes.

Zeroed bytes are not a portable promise of null pointer or floating-point zero representations on every C implementation. Initialize typed objects explicitly when those semantic values are needed.

### How do you detect a double free or an invalid free in your own allocator? {M}
**Short answer:** Give every block a header with a **magic number** that says whether it is allocated or free. On `free`, first check that the pointer lies inside the heap, then check the magic: if it already says FREE it is a double free; if it is neither magic value the pointer is invalid or the header was overwritten. Only then mark it FREE and return it to the free list.

```c
#include <stdint.h>
#include <stddef.h>

#define MAGIC_USED 0xA110C8EDu
#define MAGIC_FREE 0xF4EEF4EEu

typedef struct hdr { uint32_t magic; uint32_t size; } hdr_t;

extern uint8_t heap[], heap_end[];
void fault(const char *why);

/* Illustrates header checks only after exact block-start validation. */
void checked_free(void *p)
{
    if (p == NULL) return;
    hdr_t *h = (hdr_t *)p - 1;
    if ((uint8_t *)h < heap || (uint8_t *)p >= heap_end) { fault("free: not a heap pointer"); return; }
    if (h->magic == MAGIC_FREE) { fault("double free"); return; }
    if (h->magic != MAGIC_USED) { fault("free: corrupted header or bad pointer"); return; }
    h->magic = MAGIC_FREE;
    /* ... return block to the free list, optionally fill with 0xDD to catch use-after-free ... */
}
```

**Techniques:** a magic number in each block header (used/free), range checks against the heap bounds, a trailing **canary** word after each block checked on free (detects overruns), poisoning freed memory with a pattern (use-after-free shows up as `0xDDDDDDDD` values), and for pools a bitmap of allocated blocks. On Linux, AddressSanitizer and glibc's own checks (`free(): double free detected in tcache 2`) do this automatically.

**Why double free is dangerous:** the same block is inserted into the free list twice, so two later `malloc` calls return the same memory to two different users, who then overwrite each other's data. Attackers use this to corrupt allocator metadata.

**Layers of protection (cheapest first)**

| Check | Catches |
|---|---|
| NULL → ignore | standard behaviour (`free(NULL)` is allowed) |
| Range check against heap bounds | freeing stack/global/random pointers |
| Alignment check (`p` must be 8-aligned) | pointers into the middle of a block |
| Magic USED/FREE in header | double free, corrupted header |
| Trailing canary (e.g. `0xDEADBEEF` after the user area) | buffer overruns into the next block |
| Fill freed memory with `0xDD` | use-after-free (reads show the pattern) |
| Allocation bitmap (pools) | exact allocated/free state per block |

**Dry run:** `p = malloc(16)` → header magic USED. `free(p)` → magic becomes FREE. `free(p)` again → magic is FREE → `fault("double free")`.

**What `fault()` should do in firmware:** log the caller address (`__builtin_return_address(0)`), the block address and size, then assert/reset in debug builds; in production at least record the event.

**Limit:** if the freed block was reused by a later allocation, its magic is USED again, so a stale double free can look valid. Quarantining freed blocks for a while (as ASan does) catches more.

#### Robust validation before header access

For a fixed pool, convert the address to the platform's integer address representation, check that it is inside the pool, check that its offset is an exact multiple of slot size, then check an allocation bitmap for that slot. Do not compute or dereference an arbitrary preceding header before verifying the pointer. For a variable-size heap, consult a trusted allocation table or walk verified allocator metadata to establish that the address is an exact live block start.

A magic number is useful corruption evidence but does not prove ownership. Synchronize validation and freeing as one operation. Stale pointers to reused addresses remain fundamentally ambiguous without generation-aware handles.

### How do you detect memory leaks with an allocation table? {M}
**Short answer:** Wrap `malloc` and `free` in debug versions that record each live allocation (pointer, size, file and line) in a table and remove the entry when it is freed. At a checkpoint — end of a test, shutdown, or periodically — print every entry still in the table: those are leaks, with the exact line that allocated them.

```c
#include <stdio.h>
#include <stdlib.h>

#define MAX_ALLOCS 256
typedef struct { void *p; size_t size; const char *file; int line; } rec_t;
static rec_t table[MAX_ALLOCS];

void *dbg_malloc(size_t n, const char *file, int line)
{
    void *p = malloc(n);
    if (p) {
        for (int i = 0; i < MAX_ALLOCS; i++)
            if (table[i].p == NULL) { table[i] = (rec_t){ p, n, file, line }; break; }
    }
    return p;
}

void dbg_free(void *p)
{
    for (int i = 0; i < MAX_ALLOCS; i++)
        if (table[i].p == p) { table[i].p = NULL; break; }
    free(p);
}

void dbg_report_leaks(void)
{
    for (int i = 0; i < MAX_ALLOCS; i++)
        if (table[i].p)
            printf("LEAK %zu bytes from %s:%d\n", table[i].size, table[i].file, table[i].line);
}

#define MALLOC(n) dbg_malloc((n), __FILE__, __LINE__)
#define FREE(p)   dbg_free(p)
```

**Points:** record every allocation with its call site, remove it on free, and dump what is left at a checkpoint (end of a test, or periodically on a device). Add a lock if used from several threads. Finding a leak "in given code" usually means spotting an early return or error path that skips `free`, or a pointer overwritten before being freed.

**How the macro captures the caller:** `#define MALLOC(n) dbg_malloc((n), __FILE__, __LINE__)` expands at each call site, so the table stores where the allocation happened, not where `dbg_malloc` is.

**Example output**

```
LEAK 64 bytes from uart.c:118
LEAK 256 bytes from parser.c:42
```

**Typical leak patterns to look for in "find the leak in this code" questions**

```c
char *buf = malloc(64);
if (read_frame(buf) < 0)
    return -1;               /* leak: early return skips free */
p = realloc(p, bigger);      /* leak if realloc fails: original p lost (use a temp) */
p = malloc(10); p = malloc(20);   /* first block lost */
free(list);                  /* leak: nodes inside the list never freed */
```

**Improvements:** hash table instead of a linear scan for speed; count of total bytes and peak usage; a lock (or disable interrupts) when called from several tasks; guard canaries; record a timestamp to find "slow leaks" that grow over days.

**Tools on a PC/Linux:** Valgrind (`--leak-check=full`), AddressSanitizer / LeakSanitizer (`-fsanitize=address`), `mtrace`, heaptrack. In embedded systems the best leak prevention is not to free at run time at all: allocate once at start-up or use fixed pools.

**Complexity:** O(MAX_ALLOCS) per call with the linear table (fine for debug builds).

#### Handle the tracking table becoming full

A debug wrapper must not silently lose allocation records. Reserve a free tracking slot first or free a newly allocated block and report allocation failure when there is no tracking space. On release, handle NULL separately and reject pointers not found in the live table before passing them to free. Protect the table and its counters with an appropriate lock in concurrent applications.

A final leak report is meaningful after worker threads stop and expected long-lived allocations are accounted for. Compare allocation count and bytes against a known baseline during repeated device open/close cycles.

### Implement a slab-like allocator for fixed-size objects. {H}
**Short answer:** A slab allocator divides one memory region into equal-sized slots for one object type and keeps the free slots in a singly linked **free list stored inside the free slots themselves**. Allocation pops the head of the list and free pushes the slot back, so both are O(1) with no fragmentation and no per-object header.

```c
#include <stddef.h>
#include <stdint.h>

typedef struct slab_cache {
    size_t obj_size;          /* rounded up to hold a pointer and keep alignment */
    void  *free_list;         /* singly linked through the free objects */
    size_t in_use, total;
} slab_cache_t;

void slab_init(slab_cache_t *c, void *mem, size_t mem_size, size_t obj_size)
{
    obj_size = (obj_size < sizeof(void *)) ? sizeof(void *) : obj_size;
    obj_size = (obj_size + 7u) & ~(size_t)7u;                   /* 8-byte alignment */
    c->obj_size = obj_size;
    c->free_list = NULL;
    c->in_use = 0;
    c->total = mem_size / obj_size;
    uint8_t *p = mem;
    for (size_t i = 0; i < c->total; i++) {                      /* thread objects onto the list */
        *(void **)(p + i * obj_size) = c->free_list;
        c->free_list = p + i * obj_size;
    }
}

void *slab_alloc(slab_cache_t *c)
{
    void *o = c->free_list;
    if (o) { c->free_list = *(void **)o; c->in_use++; }
    return o;
}

void slab_free(slab_cache_t *c, void *o)
{
    *(void **)o = c->free_list;
    c->free_list = o;
    c->in_use--;
}
```

**Points:** one cache per object type (`struct packet`, `struct timer`), O(1) allocate/free, no fragmentation, objects packed tightly. The Linux kernel's slab/SLUB allocator (`kmem_cache_create`, `kmem_cache_alloc`) works on this idea, with per-CPU caches to avoid locking and constructors to pre-initialise objects. Add a lock or per-core caches for concurrency.

**Step by step**

1. **Init:** round the object size up so that it can hold a pointer and keeps 8-byte alignment; split the memory into `total = mem_size / obj_size` slots; link every slot into the free list.
2. **Alloc:** take `free_list`, set `free_list` to the next pointer stored in that slot, return the slot.
3. **Free:** write the current `free_list` into the slot, then make the slot the new head.

**Dry run (3 slots A, B, C)**

```
init:   free_list → C → B → A → NULL
alloc → C        free_list → B → A
alloc → B        free_list → A
free(C)          free_list → C → A
alloc → C        (most recently freed slot reused first: cache friendly)
```

**Why it is popular in kernels and firmware**

- Deterministic O(1) time — suitable for ISRs (with a short critical section) and real-time code.
- No external fragmentation: all slots are the same size.
- Objects of one type are packed together: good cache behaviour.

**Improvements interviewers like:** a magic/bitmap check against double free (`slab_free` currently trusts the caller), `in_use` high-water mark for sizing, several caches for different sizes (8, 16, 32 … bytes) to build a general allocator, per-CPU caches to avoid locks, and constructors to pre-initialise objects (Linux `kmem_cache_create`).

**Complexity:** O(1) alloc/free, O(total) init, memory overhead zero per object (only rounding).

#### Fixed pool with typed storage

```c
#define POOL_N 16
struct object { int id; unsigned flags; };
static struct object objects[POOL_N];
static bool used[POOL_N];

struct object *pool_get(void)
{
    for (unsigned i = 0; i < POOL_N; ++i)
        if (!used[i]) {
            used[i] = true;
            return &objects[i];
        }
    return NULL;
}
```

This alternative uses correctly aligned typed objects and explicit allocation state. Its scan is O(POOL_N), unlike a free-index stack which gives O(1) allocation and release. Validate exact slot identity and allocation state before freeing. The original intrusive free-list variant requires appropriately aligned backing storage, sufficient stride and valid pointer-storage semantics; synchronize accesses when shared.

### How do you find the alignment of a variable or type? {E}
**Short answer:** For a **type**, use `alignof(T)` (C11 `_Alignof`), which the compiler knows at compile time. For an actual **address**, convert it to `uintptr_t`: `addr & -addr` gives the largest power of two that divides it, and `(addr & (n - 1)) == 0` tests alignment to a specific power of two `n`.

```c
#include <stdalign.h>
#include <stdint.h>
#include <stdio.h>

struct s { char c; double d; };

int main(void)
{
    printf("alignof(double)   = %zu\n", alignof(double));      /* 8 on most ABIs */
    printf("alignof(struct s) = %zu\n", alignof(struct s));
    double x;
    uintptr_t a = (uintptr_t)&x;
    printf("address alignment = %zu\n", (size_t)(a & -a));      /* largest power of two dividing the address */
    printf("is 16-aligned: %d\n", (a & 15u) == 0);
    return 0;
}
```

**Points:** `alignof`/`_Alignof` gives the type's requirement (compile time); `addr & -addr` gives the largest power of two that divides an actual address; `addr % n == 0` (or `(addr & (n−1)) == 0` for powers of two) checks a specific alignment. Without C11: `offsetof(struct { char c; T t; }, t)`. Increase alignment with `_Alignas(32)`/`alignas(32)` or `__attribute__((aligned(32)))`.

**Typical alignments (32-bit Arm EABI / x86-64)**

| Type | Arm Cortex-M | x86-64 |
|---|---|---|
| `char` | 1 | 1 |
| `short` | 2 | 2 |
| `int`, `float`, pointer | 4 | 4 (pointer 8) |
| `double`, `long long` | 8 | 8 |
| `struct { char c; double d; }` | 8 (size 16) | 8 (size 16) |

**How `addr & -addr` works:** in two's complement, `-addr` = `~addr + 1`, which keeps the lowest set bit and clears all lower bits; AND-ing leaves only that lowest set bit. Example: `0x20000038 & -0x20000038 = 0x8` → 8-byte aligned.

**Pre-C11 trick:** `offsetof(struct { char c; T t; }, t)` equals the alignment of `T`, because the compiler pads `c` up to `T`'s alignment.

**Why interviewers ask:** alignment decides struct padding (and `sizeof`), whether unaligned access faults (Cortex-M0, DMA engines), whether buffers suit DMA/cache lines (32 bytes on Cortex-M7, 64 on Cortex-A), and how to write `aligned_malloc`.

**Forcing alignment:** `_Alignas(32) uint8_t dma_buf[512];` or `__attribute__((aligned(32)))`; check it with `_Static_assert(_Alignof(...) == 32, "")`.

#### Alignment versus size

```c
struct example { char tag; uint32_t value; };
printf("%zu %zu\n", sizeof(struct example),
       _Alignof(struct example));
```

On a typical ABI with four-byte uint32_t alignment, the structure is eight bytes with alignment four; the compiler inserts padding between fields. To require a 64-byte boundary for a buffer, use _Alignas(64) where supported and verify its address with a uintptr_t mask. Alignment is not necessarily equal to object size.

### How do you check whether a pointer is NULL safely? {E}
**Short answer:** Compare the pointer with `NULL` before it is used for the first time, and return an error code instead of dereferencing it. Do the check at module boundaries (public functions, data from callbacks or other tasks), set pointers to NULL after freeing them, and remember that a NULL check cannot detect dangling or uninitialised pointers.

```c
#include <stddef.h>

int sensor_read(const struct sensor *s, int *out)
{
    if (s == NULL || out == NULL)          /* check before every dereference of external input */
        return -1;
    *out = s->value;
    return 0;
}

#define SAFE_FREE(p) do { free(p); (p) = NULL; } while (0)
```

**Points:** compare with `NULL` (or `!p`) **before** dereferencing; checking after `*p` is too late, and the compiler may even remove the later check because dereferencing NULL is undefined behaviour. Set pointers to NULL after freeing to turn use-after-free into a detectable NULL access. A NULL check cannot detect dangling or wild pointers (they are non-NULL). On Cortex-M, add an MPU region at address 0 so a missed check faults instead of silently reading flash.

**Why "after" is too late**

```c
int v = s->value;      /* undefined behaviour if s is NULL */
if (s == NULL) return; /* the compiler may delete this check: it "knows" s is not NULL */
```

Because dereferencing NULL is undefined behaviour, the optimiser is allowed to assume `s` is non-NULL after the first use and remove the later check (this has caused real Linux kernel security bugs).

**Good patterns**

- Validate arguments at the top of the function (guard clauses) and return an error code.
- `assert(p != NULL)` for internal invariants that indicate a programming error (enabled in debug builds).
- `SAFE_FREE(p)` macro: free and set to NULL in one step.
- Prefer passing objects that cannot be NULL (by value, or a statically allocated struct) where possible.

**Embedded specifics**

- On many Cortex-M parts, address 0 is the start of flash (the vector table), so a NULL read returns the initial stack pointer value instead of crashing. A NULL **function pointer** call jumps into garbage. Configure an MPU region at 0 (no access) during development to trap NULL dereferences.
- In Linux kernel code, functions often return `ERR_PTR(-ENOMEM)` instead of NULL: check with `IS_ERR()`, not just `!= NULL`.

#### Null checking is only one part of pointer safety

```c
bool read_value(const int *p, int *out)
{
    if (p == NULL || out == NULL)
        return false;
    *out = *p;
    return true;
}
```

The caller must still provide live, correctly aligned objects with the required access permissions. A dangling pointer can be non-null; checking it cannot restore lifetime. In concurrent code, protect object ownership across the entire check and use, not just at the moment of comparison.

### Write code that shows a dangling pointer and a wild pointer, and how to fix them. {E}
**Short answer:** A **dangling pointer** points to memory whose lifetime has ended — freed heap memory, a local variable of a function that returned, or a buffer that was reallocated. A **wild pointer** was never initialised, so it holds a random address. Fix them by initialising every pointer (NULL if nothing else), setting pointers to NULL after `free`, and never returning the address of a local variable.

```c
#include <stdlib.h>

int *dangling_example(void)
{
    int *p = malloc(sizeof *p);
    *p = 42;
    free(p);
    /* *p = 7;    BUG: p is dangling (points to freed memory) */
    p = NULL;     /* fix: clear the pointer after free */

    int *q;
    /* *q = 5;    BUG: q is wild (uninitialised, random address) */
    q = NULL;     /* fix: always initialise */

    int local = 3;
    return &local;  /* BUG: returns a dangling pointer to a dead stack frame */
}
```

**Dangling:** pointer to an object whose lifetime has ended (freed heap memory, a returned local, an element of a vector/array that was reallocated). **Wild:** never initialised. **Fixes:** initialise all pointers, NULL them after free, never return addresses of locals (return by value, use `static`, or let the caller pass a buffer), and use sanitizers to catch the rest.

**Three classic dangling cases**

| Case | Example | Fix |
|---|---|---|
| Use after free | `free(p); p->x = 1;` | `p = NULL` after free; clear ownership rules |
| Returning a local's address | `int *f(void){ int x; return &x; }` | return by value, `static`, or caller-provided buffer |
| Realloc moving the block | `q = p; p = realloc(p, n); *q = 1;` | refresh all aliases after `realloc` |
| Scope exit | pointer to a block-scope array used after the block | keep the object alive as long as pointers to it exist |

**Why bugs are hard to see:** freed memory often still holds the old data, so the program "works" until another allocation reuses the block. Stack memory of a returned function is overwritten by the next call.

**Detection:** `-Wall -Wreturn-local-addr` (compiler warning), `-Wuninitialized`/`-Wmaybe-uninitialized` for wild pointers, AddressSanitizer (`heap-use-after-free`, `stack-use-after-return`), Valgrind, static analysers; in firmware, filling freed blocks with a pattern (0xDD) and MPU-protected NULL page.

**Related term — memory leak:** the opposite problem: memory still allocated but no pointer refers to it any more.

#### Ownership after free

```c
int *p = malloc(sizeof *p);
if (p) {
    *p = 42;
    free(p);
    p = NULL;
}
```

If another pointer copied p before the free, clearing p does not clear the alias. Establish one owner or a reference-counted lifetime protocol, and invalidate borrowed references before releasing the object. Do not demonstrate a wild pointer by reading an uninitialized pointer or dereferencing a dangling one in executable test code.

### Count vowels and consonants in a string. {E}
**Short answer:** Walk the string once, convert each character to lower case, skip anything that is not a letter, and increment the vowel counter for `a e i o u` and the consonant counter for every other letter. Time O(n), space O(1).

```c
#include <ctype.h>

void count_vc(const char *s, int *vowels, int *consonants)
{
    *vowels = *consonants = 0;
    for (; *s; s++) {
        int c = tolower((unsigned char)*s);
        if (c < 'a' || c > 'z') continue;              /* skip digits, spaces, punctuation */
        if (c == 'a' || c == 'e' || c == 'i' || c == 'o' || c == 'u') (*vowels)++;
        else (*consonants)++;
    }
}
/* "Hello World" -> vowels 3, consonants 7 */
```

**Points:** ignore non-letters; handle upper case; cast to `unsigned char` before `tolower`.

**Dry run for `"Hello World"`**

| char | lower | letter? | vowel? |
|---|---|---|---|
| H | h | yes | no → consonant |
| e | e | yes | yes |
| l, l | l | yes | no ×2 |
| o | o | yes | yes |
| space | — | no | skipped |
| W, r, l, d | — | yes | consonants ×4 |
| o | o | yes | yes |

Result: vowels 3, consonants 7.

**Alternatives:** a lookup table `static const bool is_vowel[256]` (fast, one memory read), or `strchr("aeiouAEIOU", c)` (short code, slower).

**Points interviewers check:** non-letters such as digits and punctuation are neither vowels nor consonants; `tolower` must receive an `unsigned char` value (negative `char` values are undefined behaviour for `<ctype.h>` functions); output via pointers (or a struct) because C returns one value.

#### Classification example

"Hello, ARM 64!" contains three vowels (e, o, A) and five consonants (H, l, l, R, M). Digits, punctuation and spaces do not contribute. For ctype functions, convert a char to unsigned char before passing it; negative signed-char values other than EOF are not valid inputs. If the specification requires ASCII rather than locale-dependent letters, explicitly use ASCII ranges on ASCII-compatible targets.

### Find the first non-repeated character in a string. {E}
**Short answer:** Use two passes over the string with a 256-entry count table: the first pass counts how many times each byte appears, and the second pass walks the string in its original order and returns the first character whose count is 1. Time O(n), space O(1) (a fixed table).

```c
int first_unique_char(const char *s)
{
    int count[256] = {0};
    for (const unsigned char *p = (const unsigned char *)s; *p; p++) count[*p]++;
    for (const unsigned char *p = (const unsigned char *)s; *p; p++)
        if (count[*p] == 1) return *p;
    return -1;                                         /* none */
}
/* "swiss" -> 'w' */
```

**Points:** two passes: count, then scan in original order; O(n) time, O(1) space (fixed 256-entry table).

**Dry run for `"swiss"`:** counts s=3, w=1, i=1. Second pass: `s` (3) skip, `w` (1) → return `'w'`.

**Why two passes:** the count of a character is only known after seeing the whole string, and the second pass preserves the original order (scanning the table instead would return the alphabetically first unique character).

**Variants**

- Return the **index** instead of the character (store indices, or loop with an index).
- **Streaming version** (characters arrive one by one, e.g. from a UART): keep counts plus a queue of candidates in arrival order; pop from the front while its count > 1; the front is the answer at any time.
- Case-insensitive: count `tolower(c)`.
- Unicode (UTF-8) would need decoding first; the byte table works for ASCII and raw bytes.

**Complexity:** O(n) time, 256 ints of space (constant). A brute-force nested loop is O(n²) — mention it only as the naive baseline.

#### Why the second pass matters

For "swiss", counts are s=3, w=1, i=1. Iterating over the count table would return the lowest byte value occurring once, which is i, not the first unique character w. Scanning the original order returns w. Use a size_t frequency array if arbitrary-length inputs are supported and return an index or a status plus output byte rather than conflating a sentinel with valid data.

### Remove spaces from a string in place. {E}
**Short answer:** Use two pointers over the same buffer: a read pointer visits every character and a write pointer receives only the characters to keep. Because the write pointer never gets ahead of the read pointer, no data is lost. Terminate the string at the final write position. One pass, O(n) time, O(1) space.

```c
void remove_spaces(char *s)
{
    char *w = s;                       /* write pointer */
    for (char *r = s; *r; r++)         /* read pointer */
        if (*r != ' ') *w++ = *r;
    *w = '\0';
}
/* "a b  c" -> "abc" */
```

**Points:** two pointers, one pass, O(1) extra space; terminate at the new end. Same pattern removes any character or all whitespace (`isspace`).

**Dry run for `"a b  c"`**

| read | char | action | buffer so far |
|---|---|---|---|
| 0 | a | copy to w=0 | a |
| 1 | ' ' | skip | a |
| 2 | b | copy to w=1 | ab |
| 3, 4 | ' ' ' ' | skip | ab |
| 5 | c | copy to w=2 | abc |

Write `'\0'` at index 3 → `"abc"`.

**Generalisations of the same pattern:** remove all whitespace (`isspace`), remove a given character, collapse multiple spaces into one (copy a space only if the previous written character is not a space), trim leading/trailing spaces, and remove elements equal to a value from an integer array.

**Common mistake:** shifting the remainder of the string left every time a space is found (`memmove` per space) — correct but O(n²).

**Note:** the string must be writable; calling it on a string literal (`remove_spaces("a b")`) is undefined behaviour because literals may live in flash/read-only memory.

#### In-place invariant

At any iteration, the write index is no greater than the read index. Thus writing a retained character cannot overwrite unread input. For " a  b ", read moves over all six characters while write advances only twice; writing the final NUL produces "ab". If tabs/newlines should also be removed, use isspace((unsigned char)c) or explicitly define the desired whitespace bytes.

### Convert a string to uppercase without library functions. {E}
**Short answer:** Loop over the string and, for each character between `'a'` and `'z'`, subtract `'a' - 'A'` (32) to get the upper-case letter; leave all other characters unchanged. In ASCII the same thing is clearing bit 5 (`c & ~0x20`), but only for letters.

```c
void to_upper(char *s)
{
    for (; *s; s++)
        if (*s >= 'a' && *s <= 'z')
            *s = (char)(*s - ('a' - 'A'));   /* or: *s &= ~0x20 for ASCII letters */
}
```

**Points:** only change letters; in ASCII upper and lower case differ by bit 5 (0x20), so `c & ~0x20` uppercases and `c | 0x20` lowercases a letter (do not apply it to non-letters). Use `toupper((unsigned char)c)` in real code for locale correctness.

**ASCII facts behind it:** `'A'` = 0x41 and `'a'` = 0x61; they differ by 0x20 (bit 5). So:

| Operation | Expression (letters only) |
|---|---|
| to upper | `c & ~0x20` or `c - 32` |
| to lower | `c | 0x20` or `c + 32` |
| toggle case | `c ^ 0x20` |

**Why the range check matters:** applying `& ~0x20` to `'1'` (0x31) gives 0x11 (a control character); applying it to `'{'` gives `'['`.

**Dry run:** `"Hello, 2u!"` → `"HELLO, 2U!"` (comma, space, digit and `!` unchanged).

**Points interviewers check:** in-place modification needs a writable array; non-ASCII/locale-specific letters (é, ß) are not handled — `toupper` with a locale handles single-byte locales, full Unicode needs a library; the function is O(n) time and O(1) space.

#### Character-set assumptions

ASCII lowercase bytes run from 0x61 through 0x7A, with uppercase exactly 0x20 lower. For "aB9z", the transformation gives "AB9Z". The range/arithmetic technique is appropriate for ASCII-compatible firmware protocols; ISO C does not require every execution character set to have contiguous letters. For locale-aware text use toupper with an unsigned-char conversion. Unicode case mapping is not a one-byte transformation.

### Count occurrences of a character in a string. {E}
**Short answer:** Walk the string once and add 1 to a counter each time the current character equals the target. The comparison result (0 or 1) can be added directly, which avoids a branch. Time O(n), space O(1).

```c
#include <stddef.h>

size_t count_char(const char *s, char c)
{
    size_t n = 0;
    for (; *s; s++) n += (*s == c);
    return n;
}
```

**Points:** O(n); to count all characters at once use a 256-entry table; `strchr` in a loop is an alternative.

**Counting all characters in one pass (histogram)**

```c
#include <stdio.h>

int main(void)
{
    const char *s = "embedded";
    unsigned count[256] = {0};
    for (const unsigned char *p = (const unsigned char *)s; *p; p++) count[*p]++;
    for (int c = 0; c < 256; c++)
        if (count[c]) printf("%c=%u ", c, count[c]);    /* b=1 d=3 e=3 m=1 */
    printf("\n");
    return 0;
}
```

**When to use which:** a single target → the simple loop; many queries on the same string → build the histogram once, then each query is O(1).

**Edge cases:** counting `'\0'` (the loop never sees it; define the result as 0 or 1 explicitly), empty string → 0, case-insensitive counting with `tolower`.

**Library alternative:** `for (p = strchr(s, c); p; p = strchr(p + 1, c)) n++;` — also O(n), useful when `strchr` is optimised with word-at-a-time scanning.

#### Count over a raw receive buffer

```c
size_t count_byte(const unsigned char *buf,
                  size_t n, unsigned char target)
{
    size_t count = 0;
    for (size_t i = 0; i < n; ++i)
        count += buf[i] == target;
    return count;
}
```

Unlike a string traversal, this counts embedded zero bytes. For [0x41,0x00,0x41,0x00], count_byte with target zero returns 2. Always distinguish protocol payload length from NUL termination.

### Remove duplicate characters from a string (keep first occurrences). {E}
**Short answer:** Keep a 256-entry 'seen' table and two pointers. For each character read, if it has not been seen, mark it and copy it to the write position; otherwise skip it. Terminate at the write position. This keeps the first occurrence of each character in the original order, in one pass with O(1) extra space.

```c
#include <stdbool.h>

void remove_dup_chars(char *s)
{
    bool seen[256] = { false };
    char *w = s;
    for (char *r = s; *r; r++) {
        unsigned char c = (unsigned char)*r;
        if (!seen[c]) { seen[c] = true; *w++ = *r; }
    }
    *w = '\0';
}
/* "programming" -> "progamin" */
```

**Points:** a seen-table plus read/write pointers: O(n) time, O(1) space; keeps the order of first occurrences.

**Dry run for `"programming"`**

| char | seen before? | output |
|---|---|---|
| p r o g | no | progr… → `prog` |
| r | yes | skip |
| a | no | `proga` |
| m | no | `progam` |
| m | yes | skip |
| i n | no | `progamin` |
| g | yes | skip |

Result: `"progamin"`.

**Variants**

- Remove **adjacent** duplicates only (`"aabbca"` → `"abca"`): compare with the last written character instead of a table.
- Remove characters that appear more than once **entirely** (`"programming"` → `"poain"`): first count all characters, then keep only those with count 1.
- No extra memory allowed: for each character, scan the output so far (O(n²)), or sort first (loses order).
- Lower-case letters only: a 32-bit mask (`seen |= 1u << (c - 'a')`) replaces the table.

**Complexity:** O(n) time, O(1) space (fixed table).

#### Memory-constrained variant

For an eight-bit-byte system, a 256-bit bitmap needs only 32 bytes instead of a 256-byte Boolean table. The byte index is c >> 3, and its mask is 1U << (c & 7). Test the bit before copying and set it after accepting the character. For "banana", first occurrences produce "ban". Preserve original order by scanning the source once and maintaining a write index.

### Compress a string with run-length encoding (aaabb → a3b2). {E}
**Short answer:** Scan the input in runs of identical characters. For each run, write the character followed by the run length, then continue after the run. Always check the remaining output space, because counts can have several digits and the 'compressed' string can be longer than the input.

```c
#include <stdio.h>
#include <string.h>

/* returns 0 on success, -1 if out is too small */
int rle_compress(const char *in, char *out, size_t out_size)
{
    size_t w = 0;
    for (size_t i = 0; in[i]; ) {
        size_t j = i;
        while (in[j] == in[i]) j++;                     /* run [i, j) */
        int n = snprintf(out + w, out_size - w, "%c%zu", in[i], j - i);
        if (n < 0 || (size_t)n >= out_size - w) return -1;
        w += (size_t)n;
        i = j;
    }
    if (w >= out_size) return -1;
    out[w] = '\0';
    return 0;
}
/* "aaabbc" -> "a3b2c1" */
```

**Points:** walk runs, append character + count; check the output buffer size (counts can be several digits); the "compressed" string can be longer than the input (`"abc"` → `"a1b1c1"`), so many versions return the original when compression does not help.

**Dry run for `"aaabbc"`**

| run | char | length | output |
|---|---|---|---|
| [0,3) | a | 3 | `a3` |
| [3,5) | b | 2 | `a3b2` |
| [5,6) | c | 1 | `a3b2c1` |

**Output size planning:** the worst case is a string with no repeats: each character becomes character + `"1"`, so the output needs `2n + 1` bytes; long runs need more digits (`a` × 1000 → `a1000`).

**Common variants**

- "Return the original if compression does not make it shorter" (classic interview version).
- **In-place** compression (LeetCode 443): write pointer behind the read pointer; digits written with a small loop instead of `snprintf`.
- **Decompression:** read a character, parse the number, write the character that many times (check output bounds).
- Binary RLE used in embedded systems: encode `(count, byte)` pairs with a maximum count of 255, e.g. for display images and fonts stored in flash.

**Complexity:** O(n) time; output space depends on the input pattern.

#### Encoding can increase the output size

"abcd" becomes "a1b1c1d1": eight bytes plus NUL, compared with four input bytes. For this text format, reserve at least 2n+1 bytes as a conservative bound when arithmetic is representable, or calculate required space. Runs containing decimal digit characters make this simple representation ambiguous to decode; use an explicit binary (value,count) format or escaping when arbitrary input is required. Source and destination must not overlap.

### Find the longest substring without repeating characters. {M}
**Short answer:** Use a sliding window `[start, i]` that never contains a repeated character, plus a table storing the last index where each character was seen. For each new character, if its last occurrence is inside the window, move `start` to just after that occurrence; then record the new index and update the best length. Every character is processed once: O(n) time, O(1) space.

```c
#include <stddef.h>

size_t longest_unique_substring(const char *s)
{
    int last[256];
    for (int i = 0; i < 256; i++) last[i] = -1;       /* last index each char was seen */
    size_t best = 0;
    int start = 0;                                     /* left edge of the window */
    for (int i = 0; s[i]; i++) {
        unsigned char c = (unsigned char)s[i];
        if (last[c] >= start) start = last[c] + 1;     /* repeat inside window: jump past it */
        last[c] = i;
        if ((size_t)(i - start + 1) > best) best = (size_t)(i - start + 1);
    }
    return best;
}
/* "abcabcbb" -> 3 ("abc"), "pwwkew" -> 3 ("wke") */
```

**Points:** sliding window: extend the right edge each step, move the left edge past the previous occurrence of a repeated character; each character processed once → O(n), O(1) space with a 256-entry table.

**Dry run for `"abcabcbb"`**

| i | char | last[char] | start | window | best |
|---|---|---|---|---|---|
| 0 | a | −1 | 0 | a | 1 |
| 1 | b | −1 | 0 | ab | 2 |
| 2 | c | −1 | 0 | abc | 3 |
| 3 | a | 0 (≥ start) | 1 | bca | 3 |
| 4 | b | 1 | 2 | cab | 3 |
| 5 | c | 2 | 3 | abc | 3 |
| 6 | b | 4 | 5 | cb | 3 |
| 7 | b | 6 | 7 | b | 3 |

Answer: 3.

**Why `last[c] >= start` and not just `last[c] != -1`:** an old occurrence that is already to the left of the window must not move `start` backwards (e.g. `"abba"`: at the final `a`, its last index 0 is outside the window starting at 2).

**Return the substring too:** store `best_start = start` whenever `best` improves.

**Related sliding-window problems:** longest substring with at most k distinct characters, minimum window containing all target characters, longest run of 1s with at most k flips — all O(n) with two pointers.

**Brute force for comparison:** check every substring for uniqueness — O(n³) or O(n²) with a set; mention it, then give the O(n) answer.

#### Sliding-window trace: "abba"

| Index | Byte | Window start | Window | Best |
|---|---|---:|---|---:|
| 0 | a | 0 | a | 1 |
| 1 | b | 0 | ab | 2 |
| 2 | b | 2 | b | 2 |
| 3 | a | 2 | ba | 2 |

When a previously seen byte is already outside the current window, do not move the start backward. For very long inputs use size_t positions with a sentinel or a last-position-plus-one representation rather than int indices. This algorithm operates on bytes, not Unicode code points.

### Print all permutations of a string. {M}
**Short answer:** Use backtracking: for position `l`, swap each character from `l` to the end into position `l`, recursively permute the rest of the string (`l + 1`), and swap back to restore the original order before trying the next character. When `l` reaches the last index, the current arrangement is one permutation. There are n! permutations, so the work is O(n · n!).

```c
#include <stdio.h>
#include <string.h>

static void swap(char *a, char *b) { char t = *a; *a = *b; *b = t; }

void permute(char *s, int l, int r)
{
    if (l == r) { puts(s); return; }
    for (int i = l; i <= r; i++) {
        int dup = 0;                                  /* skip repeated letters at this position */
        for (int k = l; k < i; k++) if (s[k] == s[i]) { dup = 1; break; }
        if (dup) continue;
        swap(&s[l], &s[i]);
        permute(s, l + 1, r);
        swap(&s[l], &s[i]);                           /* backtrack */
    }
}
/* char str[] = "abc"; permute(str, 0, 2);  -> abc acb bac bca cba cab */
```

**Points:** fix one position at a time by swapping each remaining character into it, recurse, then swap back (backtracking). There are n! permutations, so time is O(n · n!); recursion depth is n. The duplicate check avoids printing the same permutation twice for inputs like "aab". The string must be writable (an array, not a literal).

**Recursion tree for `"abc"`**

```
permute(abc, 0)
├─ swap(0,0) abc → permute(·,1) → abc, acb
├─ swap(0,1) bac → permute(·,1) → bac, bca
└─ swap(0,2) cba → permute(·,1) → cba, cab
```

**Why the swap back:** each level must return the string to the state its caller expects, otherwise later branches start from a changed arrangement and produce duplicates or miss permutations.

**Duplicates:** for `"aab"` the plain algorithm prints 6 lines but only 3 are distinct; the check "skip `s[i]` if the same character was already placed at position `l` in this loop" removes the duplicates without a set.

**Alternatives**

- **Next permutation** (iterative, lexicographic order, no recursion — better for embedded stack limits): find the rightmost `i` with `s[i] < s[i+1]`, swap `s[i]` with the rightmost larger character, reverse the suffix. Sort first to start from the smallest.
- Heap's algorithm generates each permutation with a single swap.

**Limits:** 10 characters give 3,628,800 permutations; mention that the output size, not the algorithm, is the problem. Recursion depth is n, so stack use is small.

#### Why backtracking restores the string

At recursion depth l, positions before l are fixed. Choose one character for position l, recurse over the remaining suffix, then undo the swap so the next choice starts from the same state. For "aab", skipping duplicate choices at each depth yields aab, aba and baa. The number of unique permutations is n! divided by the factorial of each character multiplicity. Recursion depth is O(n), and printing each result costs O(n). Handle the empty string as one empty permutation if required.

### Find the longest palindromic substring. {M}
**Short answer:** Every palindrome mirrors around a centre, which is either a character (odd length) or the gap between two characters (even length). For each of the 2n − 1 centres, expand outwards while the characters on both sides match, and keep the longest span found. Time O(n²), space O(1).

```c
#include <string.h>

/* returns length; *start receives the starting index */
size_t longest_palindrome(const char *s, size_t *start)
{
    size_t n = strlen(s), best = n ? 1 : 0;
    *start = 0;
    for (size_t c = 0; c < n; c++) {
        for (int odd = 1; odd >= 0; odd--) {           /* odd and even length centres */
            long lo = (long)c, hi = (long)c + (odd ? 0 : 1);
            while (lo >= 0 && hi < (long)n && s[lo] == s[hi]) { lo--; hi++; }
            size_t len = (size_t)(hi - lo - 1);
            if (len > best) { best = len; *start = (size_t)(lo + 1); }
        }
    }
    return best;
}
/* "babad" -> 3 ("bab"), "cbbd" -> 2 ("bb") */
```

**Points:** expand around every centre (2n − 1 centres: characters and gaps between them); O(n²) time, O(1) space, simple enough for an interview. Manacher's algorithm does it in O(n) if asked.

**Dry run for `"babad"`**

| centre | expansion | palindrome |
|---|---|---|
| b (0) | — | b |
| a (1) | b = b | bab (length 3) |
| b (2) | a = a | aba (length 3) |
| gap a\|b etc. | no match | — |

Answer: length 3, starting at 0 (`"bab"`; `"aba"` is equally valid).

**Why both centre types:** `"cbbd"` has the even palindrome `"bb"`, which no single-character centre finds.

**Index details:** after the loop stops, `lo` and `hi` point one step **beyond** the palindrome, so its length is `hi - lo - 1` and it starts at `lo + 1`. Using signed `long` for `lo` avoids unsigned underflow when it goes below 0.

**Other approaches**

| Method | Time | Space |
|---|---|---|
| Check every substring | O(n³) | O(1) |
| Dynamic programming table `P[i][j]` | O(n²) | O(n²) — too much RAM for MCUs |
| Expand around centre (above) | O(n²) | O(1) |
| Manacher's algorithm | O(n) | O(n) |

**Related:** "is the whole string a palindrome" (two pointers from the ends, O(n)), "longest palindromic subsequence" (DP, characters need not be contiguous).

#### Odd and even centres

"racecar" expands from its middle e; "abba" expands from the gap between the two b characters. There are 2n−1 candidate centres for nonempty strings. For "cbbd", expanding the centre between b and b first matches both, then fails on c versus d, producing start 1, length 2. Use size_t-safe boundary checks when inputs can exceed LONG_MAX; Manacher's algorithm reduces worst-case time to O(n) at the cost of extra state.

