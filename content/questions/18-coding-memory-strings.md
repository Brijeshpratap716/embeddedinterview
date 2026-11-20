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

### Implement strcpy() and a safe bounded copy. {E}
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

### Implement strcmp(). {E}
```c
int my_strcmp(const char *a, const char *b)
{
    while (*a && *a == *b) { a++; b++; }
    return (unsigned char)*a - (unsigned char)*b;
}
```

**Points:** the result is negative, zero or positive, not necessarily −1/0/1. Compare as `unsigned char`, as the standard requires, so bytes above 127 order correctly. The loop stops at the first difference or when `a` ends (if `b` ended first, `*b` is 0 and differs). `strncmp` adds a count limit.

### Implement strcat(). {E}
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

### Implement your own memcpy(). {E}
```c
#include <stddef.h>
#include <stdint.h>

void *my_memcpy(void *restrict dst, const void *restrict src, size_t n)
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

### Implement memmove() with overlap handling. {E}
```c
#include <stddef.h>
#include <stdint.h>

void *my_memmove(void *dst, const void *src, size_t n)
{
    uint8_t *d = dst;
    const uint8_t *s = src;
    if (d == s || n == 0) return dst;
    if ((uintptr_t)d < (uintptr_t)s || (uintptr_t)d >= (uintptr_t)s + n) {
        while (n--) *d++ = *s++;          /* no harmful overlap: copy forward */
    } else {
        d += n; s += n;                   /* dst overlaps the tail of src: copy backward */
        while (n--) *--d = *--s;
    }
    return dst;
}
```

**Points:** copy backwards when the destination starts inside the source range, so source bytes are read before they are overwritten. Comparing via `uintptr_t` avoids the technically unspecified comparison of unrelated pointers.

### Implement your own memset(). {E}
```c
#include <stddef.h>
#include <stdint.h>

void *my_memset(void *dst, int c, size_t n)
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

### Implement aligned_malloc() and aligned_free(). {M}
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

### Implement calloc() on top of your allocator. {E}
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

### How do you detect a double free or an invalid free in your own allocator? {M}
```c
#include <stdint.h>
#include <stddef.h>

#define MAGIC_USED 0xA110C8EDu
#define MAGIC_FREE 0xF4EEF4EEu

typedef struct hdr { uint32_t magic; uint32_t size; } hdr_t;

extern uint8_t heap[], heap_end[];
void fault(const char *why);

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

### How do you detect memory leaks with an allocation table? {M}
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

### Implement a slab-like allocator for fixed-size objects. {H}
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

### How do you find the alignment of a variable or type? {E}
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

### How do you check whether a pointer is NULL safely? {E}
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

### Write code that shows a dangling pointer and a wild pointer, and how to fix them. {E}
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

### Count vowels and consonants in a string. {E}
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

### Find the first non-repeated character in a string. {E}
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

### Remove spaces from a string in place. {E}
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

### Convert a string to uppercase without library functions. {E}
```c
void to_upper(char *s)
{
    for (; *s; s++)
        if (*s >= 'a' && *s <= 'z')
            *s = (char)(*s - ('a' - 'A'));   /* or: *s &= ~0x20 for ASCII letters */
}
```

**Points:** only change letters; in ASCII upper and lower case differ by bit 5 (0x20), so `c & ~0x20` uppercases and `c | 0x20` lowercases a letter (do not apply it to non-letters). Use `toupper((unsigned char)c)` in real code for locale correctness.

### Count occurrences of a character in a string. {E}
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

### Remove duplicate characters from a string (keep first occurrences). {E}
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

### Compress a string with run-length encoding (aaabb → a3b2). {E}
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

### Find the longest substring without repeating characters. {M}
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

### Print all permutations of a string. {M}
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

### Find the longest palindromic substring. {M}
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
