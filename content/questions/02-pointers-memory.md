---
slug: pointers-memory
title: Pointers & Memory
icon: 🎯
level: Beginner
order: 2
desc: Pointer arithmetic, arrays vs pointers, the memory layout of a C program, stack vs heap, memory pools, alignment, endianness and strict aliasing.
---
Pointers are where interviewers separate people who have written C from people who have debugged it. Expect to draw memory on a whiteboard. Each answer gives the short version first, then the explanation, code, and the mistakes interviewers look for.

### What is a pointer? {E}
**Short answer:** A pointer is a variable whose value is the address of another object (or function). Its type says what kind of object is at that address, which decides how many bytes a dereference reads or writes and how far `p + 1` moves.

```c
int x = 10;
int *p = &x;     /* & gives the address of x; p now points to x */
*p = 20;         /* * dereferences: writes 20 into x */
printf("%p %d\n", (void *)p, *p);
```

**Key facts**

- **Size:** a data pointer is 4 bytes on a 32-bit MCU (Cortex-M) and 8 bytes on 64-bit Linux (ARM64, x86-64), regardless of what it points to. On some 8-bit/16-bit MCUs (AVR, 8051) there are different pointer sizes for code and data memory.
- **Type matters:** `uint8_t *` and `uint32_t *` may hold the same address, but `*p` reads 1 byte versus 4 bytes.
- **NULL:** a pointer that points to nothing. Always initialise pointers, either to an object or to `NULL`.
- **Dereferencing an invalid pointer** (NULL, freed, uninitialised, out of bounds) is undefined behaviour.

**Why pointers are essential in embedded C**

- Accessing hardware registers at fixed addresses.
- Passing large structures and buffers to functions without copying them.
- Letting functions return several results (output parameters).
- Callbacks (function pointers), linked structures, and DMA descriptors that hold addresses of buffers.

**Reading declarations:** `int *p` (pointer to int), `int **pp` (pointer to pointer to int), `int *a[4]` (array of 4 pointers), `int (*a)[4]` (pointer to an array of 4 ints), `int (*f)(void)` (pointer to a function).

### How does pointer arithmetic work? {E}
**Short answer:** Adding an integer `n` to a pointer moves it by `n * sizeof(*p)` bytes, so `p + 1` points to the **next element**, not the next byte. Subtracting two pointers into the same array gives the number of elements between them (type `ptrdiff_t`). Arithmetic is only defined within one array object (and one past its end).

```c
uint32_t buf[4] = {10, 20, 30, 40};
uint32_t *p = buf;          /* &buf[0], say address 0x20000000 */

p + 1;                      /* 0x20000004 -> buf[1] */
*(p + 2);                   /* 30, same as p[2] */
(uint8_t *)p + 1;           /* 0x20000001: one byte further */

uint32_t *end = buf + 4;    /* one past the end: valid to compute and compare, not to dereference */
ptrdiff_t n = end - p;      /* 4 elements, not 16 bytes */
```

**Equivalences:** `p[i]` is defined as `*(p + i)`, so `buf[2]`, `*(buf + 2)`, `p[2]` and even `2[buf]` are the same element.

**Rules**

- Only add/subtract integers to pointers, and subtract pointers that point into the same array. Adding two pointers is meaningless (and not allowed).
- Going beyond one-past-the-end, or before the start, is undefined behaviour even if you never dereference it.
- `void *` arithmetic is not allowed in standard C (GCC treats it like `char *` as an extension).
- Comparing pointers with `<`/`>` is only defined within one array; comparing for equality is always fine.

**Precedence with increment:** `*p++` reads `*p` then advances `p`; `(*p)++` increments the value; `*++p` advances first then reads.

**Embedded use:** walking a received byte buffer, and computing register addresses: `(volatile uint32_t *)(base + 0x14)` where `base` is a `uintptr_t`, or `&periph->CR` with a struct overlay. Be careful: if `base` is a `uint32_t *`, then `base + 0x14` moves by `0x14 * 4 = 0x50` bytes.

### What is a void pointer? {E}
**Short answer:** `void *` is a generic pointer that can hold the address of any object type. You cannot dereference it or do arithmetic on it directly in standard C; you first convert it to a pointer of the real type. In C it converts implicitly to and from any object pointer type, which is why `malloc` returns `void *` and needs no cast.

```c
void *mem = malloc(16);        /* no cast needed in C (needed in C++) */
uint8_t *bytes = mem;          /* implicit conversion */

int cmp_int(const void *a, const void *b)   /* qsort comparator */
{
    int x = *(const int *)a, y = *(const int *)b;
    return (x > y) - (x < y);
}
```

**Where it is used**

- Generic memory functions: `memcpy(void *dst, const void *src, size_t n)`, `memset`.
- Generic algorithms: `qsort`, `bsearch`.
- Callback "context" arguments, so one callback can serve many instances: `void (*cb)(void *ctx)`.
- RTOS APIs: FreeRTOS task parameters (`void *pvParameters`) and queue items.
- Opaque handles in APIs.

**Cautions**

- The compiler cannot check the type behind a `void *`; converting it back to the wrong type is a bug the compiler will not catch.
- Function pointers are **not** guaranteed to convert to `void *` (POSIX `dlsym` relies on it; on most platforms it works).
- `void *` arithmetic (`p + 1`) is a GCC extension that treats the size as 1; write `(uint8_t *)p + 1` for portable code.
- When converting `void *` to a type with stricter alignment, the address must actually be suitably aligned.

### What is a double pointer and when do you need one? {M}
**Short answer:** A double pointer (`int **pp`) is a pointer to a pointer. You need one when a function must change **which object the caller's pointer points to** (because C passes the pointer itself by value), and for arrays of pointers such as `char **argv`.

```c
#include <stdlib.h>
#include <stdint.h>

int alloc_buf(uint8_t **out, size_t n)
{
    *out = malloc(n);              /* changes the caller's pointer */
    return *out ? 0 : -1;
}

uint8_t *buf = NULL;
if (alloc_buf(&buf, 64) == 0) { /* buf now points to 64 bytes */ }
```

With a single pointer (`uint8_t *out`), assigning `out = malloc(n)` would only change the function's local copy; the caller's `buf` would still be NULL, and the memory would leak.

**Other uses**

- **Arrays of strings:** `int main(int argc, char **argv)`, where `argv[i]` is a `char *`.
- **Linked-list operations without special-casing the head:**

```c
struct node { int val; struct node *next; };

void remove_val(struct node **pp, int val)
{
    while (*pp) {
        if ((*pp)->val == val) {
            struct node *dead = *pp;
            *pp = dead->next;        /* works for the head and for inner nodes */
            free(dead);
        } else {
            pp = &(*pp)->next;
        }
    }
}
```

`pp` points to "the pointer that points to the current node": either the list head or some node's `next` field. Linus Torvalds often cites this as an example of "good taste" in C.

- **Dynamically allocated 2-D arrays** as an array of row pointers (each row allocated separately), though a single block with index arithmetic is usually better for cache and fragmentation.

**Note:** `int **` is **not** compatible with a 2-D array `int m[3][4]`; that decays to `int (*)[4]`.

### What is the difference between char *s = "hello" and char s[] = "hello"? {M}
**Short answer:** `char *s = "hello";` makes `s` a **pointer** to a string literal, which usually lives in read-only memory (`.rodata`, often flash on an MCU); modifying it is undefined behaviour. `char s[] = "hello";` creates a writable **array** of 6 chars (including `'\0'`) initialised with a copy of the literal.

```c
char *p = "hello";       /* pointer (4 or 8 bytes) to a literal in .rodata */
char  a[] = "hello";     /* 6-byte array (on the stack if local, .data if global) */

a[0] = 'H';              /* fine */
p[0] = 'H';              /* undefined: may crash (Linux: SIGSEGV), or be ignored (flash) */

sizeof p;                /* 4 or 8 */
sizeof a;                /* 6 */
strlen(a);               /* 5 */

p = "world";             /* fine: point somewhere else */
a = "world";             /* error: arrays cannot be assigned */
```

**Best practice:** declare pointers to literals as `const char *p = "hello";` so the compiler rejects writes. GCC's `-Wwrite-strings` makes string literals `const char[]` to catch this. In C++, a literal already has type `const char[N]`.

**Memory layout consequences on a microcontroller**

| Declaration | Flash | RAM |
|---|---|---|
| `const char *msg = "hello";` (global) | 6 bytes (literal) | 4 bytes (the pointer, in `.data`) |
| `const char *const msg = "hello";` (global) | 6 + 4 bytes | 0 |
| `char msg[] = "hello";` (global) | 6 bytes (initial value) | 6 bytes (`.data`) |
| `static const char msg[] = "hello";` | 6 bytes | 0 |
| `char msg[] = "hello";` (local) | 6 bytes (initial value) + copy code | 6 bytes of stack each call |

For constant strings in firmware, `static const char msg[] = "..."` uses no RAM at all.

**Identical literals may share storage:** `"hello" == "hello"` may be true or false; the compiler is allowed to merge them. Compare strings with `strcmp`, never with `==`.

### What does int (*p)[10] mean versus int *p[10]? {M}
**Short answer:** `int *p[10]` is an **array of 10 pointers** to int, because `[]` binds more tightly than `*`. `int (*p)[10]` is a **single pointer to an array** of 10 ints; the parentheses make `p` a pointer first. Incrementing it moves by the size of the whole array (40 bytes with 4-byte ints).

```c
int *a[10];          /* 10 pointers: sizeof a == 10 * sizeof(int *) */
int (*b)[10];        /* 1 pointer:   sizeof b == sizeof(void *) */

int m[3][10];
b = m;               /* m decays to &m[0], type int (*)[10] */
b + 1;               /* address of m[1]: 40 bytes further */
(*b)[2] = 7;         /* m[0][2] = 7 */
b[1][2] = 8;         /* m[1][2] = 8 */
```

**How to read any C declaration (the "spiral" or "right-left" rule):** start at the name, read right (arrays `[]`, functions `()`) until a closing parenthesis, then left (`*`, qualifiers), and repeat outward.

| Declaration | Meaning |
|---|---|
| `int *p[10]` | p is an array of 10 pointers to int |
| `int (*p)[10]` | p is a pointer to an array of 10 ints |
| `int *f(int)` | f is a function taking int, returning pointer to int |
| `int (*f)(int)` | f is a pointer to a function taking int, returning int |
| `int (*f[4])(int)` | f is an array of 4 pointers to functions taking int, returning int |
| `void (*signal(int, void (*)(int)))(int)` | signal is a function taking (int, pointer to function) and returning a pointer to a function taking int |

**Use `typedef`s** for anything beyond two levels:

```c
typedef void (*handler_t)(int);
handler_t signal(int sig, handler_t h);   /* much clearer than the line above */
typedef int row_t[10];
row_t *b;                                 /* same as int (*b)[10] */
```

**Where pointer-to-array appears:** passing 2-D arrays to functions (`void f(int m[][10], size_t rows)` is `int (*m)[10]`), and walking a buffer of fixed-size records.

### What is the memory layout of a C program? {E}
**Short answer:** From low to high addresses, a typical program has **text** (code), **rodata** (constants), **data** (initialised globals/statics), **bss** (zero-initialised globals/statics), the **heap** (growing up) and the **stack** (growing down). On a microcontroller, text and rodata stay in flash, data is copied from flash to RAM at start-up, and bss, heap and stack share RAM.

**Typical layout on Linux (per process, virtual addresses)**

```
high   +-----------------------+
       | kernel space          |  not accessible from user mode
       +-----------------------+
       | stack  ↓              |  locals, return addresses; 8 MB limit by default
       |                       |
       | mmap area             |  shared libraries, large malloc, mmap'd files
       |                       |
       | heap   ↑              |  malloc (brk)
       +-----------------------+
       | .bss                  |  zero-initialised globals/statics
       | .data                 |  initialised globals/statics
       | .rodata               |  constants, string literals
       | .text                 |  code
low    +-----------------------+  (address 0 unmapped: catches NULL)
```

**Typical layout on a Cortex-M microcontroller**

```
FLASH 0x08000000: vector table | .text | .rodata | initial values of .data
RAM   0x20000000: .data | .bss | heap ↑ ... ↓ stack (top of RAM = initial MSP)
```

**What goes where**

```c
const int table[] = {1, 2, 3};   /* .rodata (flash)            */
int counter = 5;                 /* .data   (flash copy + RAM) */
int total;                       /* .bss    (RAM, zeroed)      */
static char buf[256];            /* .bss                       */

void f(void)
{
    int local;                   /* stack                      */
    static int calls;            /* .bss                       */
    char *p = malloc(32);        /* p on the stack, 32 bytes on the heap */
    const char *s = "text";      /* "text" in .rodata, s on the stack */
}
```

**Why it matters:** heap and stack growing towards each other can **collide** on an MCU without memory protection, silently corrupting data. Embedded projects size the stack carefully, often disable or limit the heap, and use the linker map file to check how much RAM each section uses. In an RTOS, each task has its own stack (allocated from the heap or statically), and the "main stack" (MSP) is used by interrupts.

### What is the difference between stack and heap? {E}
**Short answer:** The **stack** holds function-local data automatically: space is reserved on function entry by moving the stack pointer and released on return, so it is fast and deterministic but small and limited to the function's lifetime. The **heap** holds memory you request explicitly with `malloc` and release with `free`; it lives until freed and can be large, but allocation is slower, can fail, and can fragment.

| | Stack | Heap |
|---|---|---|
| Allocation | automatic (function entry) | explicit (`malloc`/`free`, `new`/`delete`) |
| Speed | one instruction (adjust SP) | allocator search; varies |
| Lifetime | until the function returns | until `free` |
| Size | small, fixed per thread/task (KB on MCUs, 8 MB default on Linux) | as much RAM as is available |
| Fragmentation | none | yes, over time |
| Failure mode | overflow: silent corruption or a fault | `malloc` returns NULL |
| Thread safety | each thread has its own | shared; allocator needs locking |
| Determinism | yes | generally no |

**What is on the stack:** local variables, function arguments that do not fit in registers, return addresses (LR saved by the callee), saved registers, and on Cortex-M the exception frame pushed automatically on interrupt entry (8 words, more with the FPU).

**Common bugs**

- **Returning a pointer to a local** (the stack frame is gone after return).
- **Large local arrays** (`char buf[4096];` in a task with a 2 KB stack).
- **Heap:** leaks, double free, use after free, writing past the allocated size (corrupts the allocator's metadata, crashing much later in an unrelated `malloc`).

**Embedded guidance**

- Prefer static allocation and stack allocation with known bounds; measure the worst-case stack per task (high-water marks, static analysis).
- If you need dynamic memory, allocate at start-up only, or use fixed-size **memory pools**.
- With FreeRTOS, choose the heap scheme deliberately: `heap_1` (no free), `heap_4` (coalescing first-fit), `heap_5` (multiple regions), or fully static allocation (`configSUPPORT_STATIC_ALLOCATION`).

### What is a memory leak? {E}
**Short answer:** A memory leak is memory that has been allocated but can no longer be freed because the program has lost every pointer to it (or never frees memory it no longer needs). Each leak permanently reduces available memory; in a device that runs for months, even a few bytes per event eventually exhausts the heap and causes allocation failures or a crash.

```c
void handle_msg(const uint8_t *data, size_t len)
{
    uint8_t *copy = malloc(len);
    if (copy == NULL) return;
    memcpy(copy, data, len);
    if (!valid(copy, len))
        return;                  /* LEAK: early return without free(copy) */
    process(copy, len);
    free(copy);
}
```

**Typical causes**

- Early returns and error paths that skip `free` (use a single exit path with cleanup, a `goto out;` pattern, or design ownership clearly).
- Overwriting the only pointer: `p = malloc(...)` twice, or `p = realloc(p, n)` when `realloc` fails.
- Unclear ownership: neither caller nor callee frees.
- Lost references in data structures (removing a list node without freeing it).
- Resources other than memory leak too: file descriptors, sockets, RTOS objects (queues, timers), DMA descriptors.

**Finding leaks**

- On Linux and in host-based unit tests: **Valgrind** (`valgrind --leak-check=full`), **AddressSanitizer/LeakSanitizer** (`-fsanitize=address`), heaptrack.
- On an MCU: track heap statistics over time, e.g. FreeRTOS `xPortGetFreeHeapSize()` and `xPortGetMinimumEverFreeHeapSize()`; wrap `malloc`/`free` to count allocations by call site; run long soak tests and watch the trend.
- In code review: every allocation must have a clear owner and a clear free.

**Prevention in embedded systems:** avoid run-time allocation (static allocation or pools), allocate once at start-up, and design APIs so ownership is obvious ("caller provides the buffer").

### What is heap fragmentation and why does it matter in embedded systems? {M}
**Short answer:** After many allocations and frees of different sizes, free memory is split into many small, non-adjacent holes. An allocation can then fail even though the **total** free memory is large enough, because no **single** hole is big enough. Devices that must run for years without rebooting can fail this way after days or months, which makes the bug very hard to reproduce.

**Example (a 10 KB heap)**

```
allocate A 2K, B 2K, C 2K, D 2K, E 2K   -> heap full
free B and D                            -> 4 KB free, but as two 2 KB holes
malloc(3K)                              -> FAILS: no hole is 3 KB
```

**External vs internal fragmentation**

- **External:** free memory exists but is split into pieces (the example above).
- **Internal:** memory wasted *inside* allocated blocks, e.g. a pool with 64-byte blocks used for 20-byte objects, or allocator headers and alignment padding.

**Mitigations**

1. **Allocate everything at start-up and never free.** Simple and deterministic (FreeRTOS `heap_1`).
2. **Fixed-size memory pools:** blocks of one size per pool, so any free block fits any request; no external fragmentation, O(1) allocate/free.
3. **Coalescing allocators:** merge adjacent free blocks (FreeRTOS `heap_4`, TLSF); this reduces but does not eliminate fragmentation.
4. **TLSF (Two-Level Segregated Fit):** O(1), bounded fragmentation, used in real-time systems (Zephyr offers it).
5. **Avoid mixing lifetimes:** allocate long-lived objects first, and keep short-lived ones in a separate pool or arena.
6. **Arena/region allocation:** allocate from a buffer for one operation and release the whole arena at once.

**Monitoring:** track the largest free block as well as total free memory; a shrinking largest-block size while total free memory stays constant is the signature of fragmentation.

**Safety standards** (MISRA C, IEC 61508, ISO 26262 guidance, DO-178C practice) generally forbid dynamic allocation after initialisation because of fragmentation and non-deterministic timing.

### What is a memory pool, and how do you implement a fixed-size block allocator? {M}
**Short answer:** A memory pool pre-allocates a block of memory divided into equal-sized chunks and keeps the free chunks in a linked list (the "free list"), with the link stored inside each free chunk. Allocation takes the first chunk from the list and freeing pushes it back, both in O(1) with no fragmentation, which makes pools ideal for real-time and embedded systems.

```c
#include <stddef.h>
#include <stdint.h>

#define BLOCK_SIZE  32u
#define BLOCK_COUNT 16u

typedef union block {
    union block *next;                 /* used while the block is free */
    uint8_t data[BLOCK_SIZE];          /* used while it is allocated  */
} block_t;

static block_t pool[BLOCK_COUNT];
static block_t *free_list;

void pool_init(void)
{
    for (size_t i = 0; i < BLOCK_COUNT - 1; i++)
        pool[i].next = &pool[i + 1];
    pool[BLOCK_COUNT - 1].next = NULL;
    free_list = &pool[0];
}

void *pool_alloc(void)
{
    block_t *b = free_list;            /* in an RTOS/ISR context: protect with a critical section */
    if (b) free_list = b->next;
    return b;                          /* NULL when the pool is exhausted */
}

void pool_free(void *p)
{
    if (p == NULL) return;
    block_t *b = p;
    b->next = free_list;
    free_list = b;
}
```

**Why a union:** a free block does not need its data, so its first bytes can hold the `next` pointer, costing no extra memory. The union also makes every block aligned for a pointer.

**Properties**

| | Memory pool | General `malloc` |
|---|---|---|
| Time | O(1), constant | varies with heap state |
| External fragmentation | none | possible |
| Internal fragmentation | yes, if objects are smaller than the block | small (headers, alignment) |
| Sizes | one per pool (use several pools for several sizes) | any |

**Production details**

- **Thread/ISR safety:** wrap alloc/free in a critical section, or use a lock-free stack (watch out for the ABA problem).
- **Debug checks:** fill freed blocks with a pattern, check that a freed pointer is inside the pool and on a block boundary, detect double free with a bitmap.
- **Statistics:** track the minimum number of free blocks ever (high-water mark) to size the pool.
- **Alignment:** if blocks hold types with stricter alignment (e.g. `double`, DMA buffers needing 32-byte alignment), align the pool array and round the block size up.

**Where you see pools:** RTOS memory pools (Zephyr `k_mem_slab`, ThreadX block pools, CMSIS-RTOS `osMemoryPool`), network stacks (lwIP `pbuf` pools, Linux's `kmem_cache` slab allocator), and USB/CAN message buffers.

### How would you implement a simple malloc() and free()? {H}
**Short answer:** Manage a fixed memory region as a list of blocks, each starting with a small header (size and a free flag, or a link to the next free block). `malloc` searches the free list for a block that is big enough (first fit or best fit), splits off the remainder if it is large, marks the block used and returns the address just after the header. `free` marks the block free and **coalesces** it with adjacent free neighbours to fight fragmentation.

```c
#include <stddef.h>
#include <stdint.h>

#define HEAP_SIZE 4096u
#define ALIGN8(x) (((x) + 7u) & ~(size_t)7u)

typedef struct hdr {
    size_t size;              /* payload size in bytes */
    struct hdr *next;         /* next block in address order */
    int free;
} hdr_t;

static _Alignas(8) uint8_t heap[HEAP_SIZE];
static hdr_t *head;

static void heap_init(void)
{
    head = (hdr_t *)heap;
    head->size = HEAP_SIZE - sizeof(hdr_t);
    head->next = NULL;
    head->free = 1;
}

void *my_malloc(size_t n)
{
    if (head == NULL) heap_init();
    if (n == 0) return NULL;
    n = ALIGN8(n);
    for (hdr_t *b = head; b; b = b->next) {
        if (b->free && b->size >= n) {
            if (b->size >= n + sizeof(hdr_t) + 8) {           /* split */
                hdr_t *rest = (hdr_t *)((uint8_t *)(b + 1) + n);
                rest->size = b->size - n - sizeof(hdr_t);
                rest->next = b->next;
                rest->free = 1;
                b->size = n;
                b->next = rest;
            }
            b->free = 0;
            return b + 1;                                      /* memory after the header */
        }
    }
    return NULL;                                               /* out of memory */
}

void my_free(void *p)
{
    if (p == NULL) return;
    hdr_t *b = (hdr_t *)p - 1;
    b->free = 1;
    for (hdr_t *c = head; c; c = c->next) {                   /* coalesce neighbours */
        while (c->free && c->next && c->next->free) {
            c->size += sizeof(hdr_t) + c->next->size;
            c->next = c->next->next;
        }
    }
}
```

**Design points to discuss**

- **Alignment:** every returned pointer must be suitably aligned for any type (8 bytes on Cortex-M with `double`/`uint64_t`; 16 on ARM64/x86-64). The header size must keep payloads aligned (it is 12 bytes on 32-bit here, so add padding or use `_Alignas` on the header in a real allocator).
- **Placement policy:** first fit (fast, fragments the start of the heap), best fit (less wasted space, slower search), next fit, or segregated free lists by size class (what real allocators do).
- **Coalescing:** this version scans the whole list; real allocators use **boundary tags** (a footer with the size) or doubly linked lists to merge in O(1).
- **Thread safety:** a lock around both functions (newlib's `__malloc_lock`, FreeRTOS suspends the scheduler).
- **Safety checks:** detect double free and invalid pointers, add canaries to catch overruns.
- **Determinism:** for real-time code, use TLSF or pools instead, because search time here grows with the number of blocks.

**Where real implementations come from:** newlib/newlib-nano malloc (dlmalloc-based), FreeRTOS `heap_2/4/5`, Zephyr `sys_heap`, TLSF, and the Linux kernel's buddy allocator plus slab caches.

### How do you detect a stack overflow on a microcontroller? {M}
**Short answer:** Combine several techniques: **stack painting** (fill the stack with a known pattern at boot and check how much was overwritten), a **guard region** below the stack using the MPU, **hardware stack limit registers** on Armv8-M (`MSPLIM`/`PSPLIM`), the **RTOS's overflow checks**, and **static worst-case stack analysis** at build time.

**1. Stack painting (high-water mark)**

```c
extern uint32_t _sstack, _estack;          /* from the linker script */
#define STACK_FILL 0xDEADBEEFu

void stack_paint(void)                     /* call very early, before the stack is deep */
{
    uint32_t *p = &_sstack;
    uint32_t *sp = (uint32_t *)__get_MSP();
    while (p < sp - 16) *p++ = STACK_FILL; /* leave a margin below the current SP */
}

size_t stack_unused_bytes(void)
{
    const uint32_t *p = &_sstack;
    while (p < &_estack && *p == STACK_FILL) p++;
    return (size_t)((const uint8_t *)p - (const uint8_t *)&_sstack);
}
```

Report the minimum ever over long tests; keep a safety margin (e.g. 25%).

**2. MPU guard region:** configure a small no-access region just below each stack. An overflow triggers a MemManage fault immediately, at the instruction that overflowed, instead of corrupting other data. FreeRTOS-MPU and Zephyr (`CONFIG_MPU_STACK_GUARD`) do this per thread.

**3. Stack limit registers (Cortex-M23/M33/M55/M85):** set `MSPLIM` and `PSPLIM`; any instruction that moves SP below the limit raises a UsageFault (STKOF). No MPU region needed.

**4. RTOS checks:** FreeRTOS `configCHECK_FOR_STACK_OVERFLOW` = 1 checks the stack pointer at each context switch; = 2 also checks that the last 16 bytes of the stack still contain the fill pattern; `vApplicationStackOverflowHook()` is called on detection. `uxTaskGetStackHighWaterMark()` reports the minimum free stack per task.

**5. Static analysis:** compile with `-fstack-usage` (a `.su` file per source with each function's frame size) and combine with the call graph (`-fcallgraph-info`, puncover, StackAnalyzer) to compute the worst case. Recursion and function pointers break the analysis, which is one reason they are restricted in safety code.

**6. Canaries:** `-fstack-protector-strong` puts a guard value between local buffers and the return address and checks it on return; this detects buffer overruns within a frame (a security feature, not a full overflow detector).

**Symptoms of an undetected overflow:** random variable corruption, HardFaults with nonsense addresses, crashes that depend on interrupt timing, and bugs that disappear when you add a `printf` (which changes stack usage).

### What is alignment and what happens on an unaligned access? {M}
**Short answer:** An object is **aligned** when its address is a multiple of its alignment requirement, which for basic types is usually their size (a `uint32_t` at an address divisible by 4). The compiler aligns variables and adds struct padding automatically. Unaligned accesses usually come from casting byte pointers; depending on the CPU they are slower, need extra instructions, or fault.

**Behaviour by core**

| Core | Unaligned `LDR`/`STR` (word/halfword) | Notes |
|---|---|---|
| Cortex-M0/M0+/M23 (Armv6-M/v8-M baseline) | HardFault | no unaligned support at all |
| Cortex-M3/M4/M7/M33 | supported in hardware, slower (split into two accesses) | `LDRD`/`STRD`, `LDM`/`STM` still fault; can be made to trap with `CCR.UNALIGN_TRP` |
| Cortex-A (ARMv7-A/ARMv8-A) | supported for normal memory | faults on **Device** memory (peripherals) and for exclusive/atomic instructions |
| x86 | supported, small penalty | atomics across cache lines are very slow (split locks) |

**The classic bug**

```c
void parse(const uint8_t *buf)            /* buf from a UART or network packet */
{
    uint32_t len = *(const uint32_t *)(buf + 1);   /* unaligned if buf+1 is not a multiple of 4,
                                                      and also a strict-aliasing violation */
}
```

**Correct, portable approaches**

```c
uint32_t len;
memcpy(&len, buf + 1, sizeof len);        /* compiler emits the best sequence for the target */

uint32_t len_le = (uint32_t)buf[1] | (uint32_t)buf[2] << 8 |
                  (uint32_t)buf[3] << 16 | (uint32_t)buf[4] << 24;   /* also fixes byte order */
```

**Controlling alignment**

- `_Alignas(32) uint8_t dma_buf[512];` (C11) or `__attribute__((aligned(32)))` for cache-line-aligned DMA buffers.
- `alignof(T)` (C11 `_Alignof`) gives a type's requirement.
- `aligned_alloc(align, size)` for aligned heap memory.
- Packed structs remove padding but may create unaligned members (see the C topic).

**Why alignment matters beyond correctness:** aligned data never spans two cache lines or two bus transactions; DMA controllers often require aligned buffers; and atomic operations generally require natural alignment.

### What is endianness and how do you check it in code? {E}
**Short answer:** Endianness is the order in which the bytes of a multi-byte value are stored in memory. **Little-endian** stores the least significant byte at the lowest address (x86, almost all Arm systems in practice, RISC-V). **Big-endian** stores the most significant byte first (network byte order, older PowerPC, some DSPs and Motorola parts). You can check it at run time by looking at the first byte of a known integer.

```
value 0x12345678 at address 0x100
               0x100 0x101 0x102 0x103
little-endian:  78    56    34    12
big-endian:     12    34    56    78
```

```c
#include <stdint.h>

int is_little_endian(void)
{
    uint32_t x = 1;
    return *(const uint8_t *)&x == 1;     /* lowest-addressed byte holds the LSB */
}

/* same idea with a union */
int is_little_endian_union(void)
{
    union { uint32_t u; uint8_t b[4]; } v = { .u = 1 };
    return v.b[0] == 1;
}
```

Reading an object through `char *`/`unsigned char *`/`uint8_t *` is always allowed (it does not violate strict aliasing), so the pointer version is valid C.

**Compile-time check (GCC/Clang):**

```c
#if __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__
/* little-endian target */
#endif
```

**Where endianness matters**

- **Communication:** network protocols (TCP/IP headers are big-endian), CAN signals (Intel vs Motorola byte order in DBC files), Modbus (big-endian registers), USB and Bluetooth (little-endian).
- **Files and flash data** shared between different processors.
- **Casting byte buffers to structs** or integers.

**The portable way:** never depend on the host's endianness. Build and split values from bytes explicitly with shifts, which work on any host:

```c
uint32_t get_be32(const uint8_t *b)
{
    return (uint32_t)b[0] << 24 | (uint32_t)b[1] << 16 | (uint32_t)b[2] << 8 | b[3];
}
void put_le16(uint8_t *b, uint16_t v) { b[0] = (uint8_t)v; b[1] = (uint8_t)(v >> 8); }
```

Note the casts to `uint32_t` before shifting: without them, `b[0]` is promoted to `int`, and `0x80 << 24` overflows a signed int.

**Arm detail:** Arm cores are bi-endian in architecture, but Cortex-M endianness is fixed at chip design (almost always little-endian), and Linux on Arm is almost always little-endian.

### How do you swap the endianness of a 32-bit value? {E}
**Short answer:** Move each byte to its mirrored position with shifts and masks, or use the compiler built-in `__builtin_bswap32()`, which compiles to a single `REV` instruction on Arm. For network code use `htonl()`/`ntohl()`, which swap only when the host is little-endian.

```c
#include <stdint.h>

static inline uint32_t bswap32(uint32_t x)
{
    return  (x >> 24)               |
           ((x >>  8) & 0x0000FF00u) |
           ((x <<  8) & 0x00FF0000u) |
            (x << 24);
}

static inline uint16_t bswap16(uint16_t x)
{
    return (uint16_t)((x >> 8) | (x << 8));
}
/* bswap32(0x12345678) == 0x78563412 */
```

**Use unsigned types.** A version written with `int`:

```c
int a = 0x12345678, out = 0;
out |= (a & 0x000000ff) << 24;   /* 0x78 << 24 sets the sign bit of int: overflow, UB */
out |= (a & 0xff000000) >> 24;   /* for a negative a, >> is implementation-defined */
```

works on most compilers for this particular value, but it relies on undefined and implementation-defined behaviour. With `uint32_t` every shift is well-defined.

**Other ways**

| Method | Notes |
|---|---|
| `__builtin_bswap16/32/64` | GCC/Clang; one instruction on Arm (`REV`, `REV16`), x86 (`BSWAP`) |
| `__REV()`, `__REV16()`, `__REVSH()` | CMSIS intrinsics for Cortex-M |
| `htonl`, `htons`, `ntohl`, `ntohs` | POSIX/socket APIs: host ↔ network (big-endian) |
| `htobe32`, `le32toh` (`<endian.h>`) | Linux/BSD: explicit target byte order |
| `cpu_to_be32`, `le32_to_cpu` | Linux kernel; also annotate types (`__be32`) so `sparse` can check |
| Shifts from a byte array | best for parsing buffers (also avoids alignment problems) |

**The pattern most firmware should use:** do not swap integers in place. Convert at the boundary: parse incoming bytes with `get_be32(buf)` and serialise outgoing data with `put_be32(buf, v)`. That handles byte order and alignment in one step and works unchanged on any CPU.

### What is strict aliasing? {H}
**Short answer:** The strict aliasing rule says that an object may only be accessed through an expression of its own type (or a compatible type, its signed/unsigned variant, a qualified version, an aggregate or union containing it), or through a character type (`char`, `unsigned char`). The compiler uses this rule to assume that pointers to different types do not point to the same memory, so it can keep values in registers and reorder loads and stores. Breaking the rule is undefined behaviour.

```c
#include <stdint.h>
#include <string.h>

uint32_t float_bits_bad(float f)
{
    return *(uint32_t *)&f;               /* UB: accessing a float through a uint32_t lvalue */
}

uint32_t float_bits_ok(float f)
{
    uint32_t u;
    memcpy(&u, &f, sizeof u);             /* defined; compiles to a single register move */
    return u;
}
```

**How it breaks code in practice**

```c
int foo(int *i, float *f)
{
    *i = 1;
    *f = 2.0f;           /* compiler assumes f cannot point to the same object as i */
    return *i;           /* so it returns 1 without reloading, even if i and f alias */
}
```

Code like this often works at `-O0` and silently changes behaviour at `-O2`.

**Allowed ways to reinterpret bytes**

- `memcpy` into an object of the target type (the standard, recommended way; free after optimisation).
- Reading through `unsigned char *` / `uint8_t *` (character types may alias anything).
- A union (allowed in C; undefined in C++, where `std::bit_cast` in C++20 is the tool).

**Embedded situations where it appears**

- Casting a received `uint8_t` buffer to a struct pointer (`struct hdr *h = (struct hdr *)buf;`), which is also an alignment risk. Copy into a struct with `memcpy`, or parse field by field.
- Treating a `uint32_t` array as `float` samples.
- Checksums computed by reading a struct as `uint32_t` words.

**Escape hatch:** `-fno-strict-aliasing` disables the optimisation; the Linux kernel and many embedded projects build with it. That makes such code work with GCC, but it is still non-portable C and gives up some optimisation, so prefer `memcpy` in new code. GCC's `-Wstrict-aliasing` catches some violations.

### How do you access a memory-mapped register at a fixed address? {E}
**Short answer:** Convert the register's address into a pointer to a `volatile` fixed-width integer and dereference it. The `volatile` makes the compiler perform every read and write exactly as written. Vendor headers (CMSIS) do the same with a struct that overlays a whole peripheral's registers.

```c
#include <stdint.h>

#define GPIOA_BASE  0x40020000u
#define GPIOA_MODER (*(volatile uint32_t *)(GPIOA_BASE + 0x00u))
#define GPIOA_ODR   (*(volatile uint32_t *)(GPIOA_BASE + 0x14u))

void led_on(void)
{
    GPIOA_MODER = (GPIOA_MODER & ~(3u << 10)) | (1u << 10);   /* PA5 as output */
    GPIOA_ODR |= (1u << 5);                                     /* drive PA5 high */
}
```

**The struct-overlay style (CMSIS)**

```c
typedef struct {
    volatile uint32_t MODER;    /* 0x00 */
    volatile uint32_t OTYPER;   /* 0x04 */
    volatile uint32_t OSPEEDR;  /* 0x08 */
    volatile uint32_t PUPDR;    /* 0x0C */
    volatile const uint32_t IDR;/* 0x10  read-only */
    volatile uint32_t ODR;      /* 0x14 */
    volatile uint32_t BSRR;     /* 0x18  write-only set/reset */
} GPIO_TypeDef;

#define GPIOA ((GPIO_TypeDef *)GPIOA_BASE)

GPIOA->BSRR = 1u << 5;          /* atomic set of PA5, no read-modify-write */
```

Use `_Static_assert(offsetof(GPIO_TypeDef, ODR) == 0x14, "")` to check the layout.

**Important details**

- **`volatile` is required**, or the compiler may combine, reorder or remove accesses (e.g. a polling loop reading a status register once).
- **Access width:** some peripherals require 32-bit accesses; using `uint8_t` pointers to them may fault or be ignored. Match the width the reference manual specifies.
- **Read-modify-write is not atomic.** `GPIOA->ODR |= x` can race with an ISR modifying the same register; use set/clear registers (`BSRR`), bit-banding, or a critical section.
- **Write-1-to-clear** status bits: `SR |= FLAG` would clear **every** flag that is set; write only the bit you mean: `SR = FLAG`.
- **Ordering:** `volatile` orders accesses in the compiler, but on cores with write buffers (Cortex-M7, Cortex-A) you may need `__DSB()` before relying on a write having reached the peripheral (e.g. before sleeping or after clearing an interrupt flag).
- On Linux, user space cannot use physical addresses directly; drivers use `ioremap()` + `readl()`/`writel()`, and user space can `mmap()` `/dev/mem` or a UIO device for experiments.

### Why is sizeof not a function? {E}
**Short answer:** `sizeof` is a compile-time **operator**, not a function. The compiler evaluates it from the type of its operand, so no code runs and the operand expression is **not evaluated** (except for variable-length arrays). Parentheses are required only around a type name: `sizeof(int)`; for an expression, `sizeof x` is valid.

```c
int i = 5;
size_t s = sizeof(i++);      /* s = 4, and i is still 5: i++ never executes */

int arr[10];
sizeof arr;                  /* 40 */
sizeof arr[0];               /* 4 */
sizeof(int[10]);             /* 40 */

void f(int n) { int vla[n]; sizeof vla; }   /* VLA: evaluated at run time */
```

**Facts interviewers check**

- The result type is `size_t` (unsigned). Mixing it with negative signed values in comparisons is a classic bug: `if (-1 < sizeof(int))` is false.
- `sizeof(char)` is always 1. In C, `sizeof('a')` is `sizeof(int)` because a character constant is an `int`.
- `sizeof` on a struct includes padding.
- `sizeof` on an array parameter gives the pointer size, because the parameter is really a pointer.
- `sizeof` on a function name is invalid in standard C.
- Because the result is a constant expression (except for VLAs), it can be used in `#define`s, array sizes and `_Static_assert`, but **not** in `#if` (the preprocessor runs before types exist).

**Printing it:** use `%zu`: `printf("%zu\n", sizeof arr);`.

**Good style:** `malloc(n * sizeof *p)` rather than `malloc(n * sizeof(struct foo))`; the expression form stays correct if the type of `p` changes.

### How do you find the number of elements in an array? {E}
**Short answer:** Divide the size of the whole array by the size of one element: `sizeof(a) / sizeof((a)[0])`, usually wrapped in an `ARRAY_SIZE` macro. It only works on a real array whose declaration is in scope; on a pointer (including an array passed to a function) it silently gives a wrong result.

```c
#define ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))

static const uint16_t baud_table[] = { 9600, 19200, 38400, 57600 };

for (size_t i = 0; i < ARRAY_SIZE(baud_table); i++) { /* 4 iterations */ }

void f(const uint16_t *t)
{
    size_t n = ARRAY_SIZE(t);    /* WRONG: sizeof(pointer) / sizeof(uint16_t) = 2 on 32-bit */
}
```

**Making it safe (GCC/Clang):** the Linux kernel's version fails to compile when given a pointer:

```c
#define __must_be_array(a) \
    (sizeof(struct { int : -!!(__builtin_types_compatible_p(__typeof__(a), __typeof__(&(a)[0]))); }))
#define ARRAY_SIZE_SAFE(a) (sizeof(a) / sizeof((a)[0]) + __must_be_array(a))
```

C23 and C++17 make this easier: C++ has `std::size(a)`, which refuses pointers.

**Why `(a)[0]` and not `*a`:** both work for arrays; the brackets are just a common idiom. The parentheses around `a` protect expressions passed to the macro.

**Best practice for functions:** always pass the element count with the pointer (`void send(const uint8_t *buf, size_t len)`), or pass a struct that contains both.

**Static check for tables that must match an enum:**

```c
enum mode { MODE_IDLE, MODE_RUN, MODE_COUNT };
static const char *const mode_name[] = { "idle", "run" };
_Static_assert(ARRAY_SIZE(mode_name) == MODE_COUNT, "mode_name out of sync with enum mode");
```

### What is the difference between memcpy and memmove? {E}
**Short answer:** Both copy `n` bytes from source to destination. `memcpy` assumes the two regions **do not overlap**; if they do, the behaviour is undefined. `memmove` handles overlap correctly, as if the data were first copied to a temporary buffer, usually by copying backwards when the destination is above the source.

```c
char buf[] = "abcdef";

memmove(buf + 2, buf, 4);   /* "ababcd" - correct */
memcpy(buf + 2, buf, 4);    /* undefined: may give "ababab" with a simple forward copy */
```

**Why a forward copy breaks with overlap:** copying `buf[0..3]` to `buf[2..5]` one byte at a time from the front overwrites `buf[2]` and `buf[3]` before they are read.

**How `memmove` decides direction**

```c
void *my_memmove(void *dst, const void *src, size_t n)
{
    unsigned char *d = dst;
    const unsigned char *s = src;
    if (d < s) {
        while (n--) *d++ = *s++;          /* copy forward */
    } else if (d > s) {
        d += n; s += n;
        while (n--) *--d = *--s;          /* copy backward */
    }
    return dst;
}
```

(Comparing pointers into different objects with `<` is technically unspecified in C; library implementations do it with integer addresses.)

**When to use which**

- `memcpy` when the buffers are distinct (most cases); it can be slightly faster because it may copy in any order and use the widest possible loads.
- `memmove` when shifting data inside one buffer: removing bytes from the front of a receive buffer, inserting into an array, scrolling a display buffer.

**Embedded notes**

- Neither function respects `volatile` or peripheral access widths: do not use them to copy to or from hardware registers or device memory; write an explicit loop with `volatile` accesses of the right width.
- For large copies on an MCU, a DMA memory-to-memory transfer can free the CPU.
- Compilers often replace small fixed-size `memcpy` calls with inline loads and stores, and they may also turn a hand-written copy loop into a `memcpy` call (which matters if you are writing the `memcpy` implementation itself: build it with `-fno-builtin` or `-ffreestanding`).

### What is a NULL pointer dereference on a Cortex-M and why might it not crash? {H}
**Short answer:** On most Cortex-M microcontrollers, address `0x00000000` is valid memory: flash (or an alias of it) containing the vector table. Reading through a NULL pointer therefore returns real data (the initial stack pointer value and the reset vector) instead of faulting, so the bug goes unnoticed. Writes to that area are usually ignored or cause a bus fault, depending on the part.

**Example**

```c
struct sensor *s = NULL;        /* forgot to initialise */
uint32_t v = s->value;          /* reads address 0x00000000 + offset: valid flash, no fault */
s->value = 5;                   /* write to flash: ignored, or a BusFault (imprecise on some cores) */
```

On Linux, the first page (and more) of every process is unmapped, so the same bug gives an immediate `SIGSEGV`.

**How to catch NULL dereferences on an MCU**

1. **MPU:** configure a region at address 0 (e.g. 256 bytes to a few KB) as no-access. If the vector table has been relocated to RAM or another flash address with `SCB->VTOR`, nothing legitimate reads address 0 any more, and the MPU turns a NULL access into a MemManage fault with the faulting address in `MMFAR`.
2. **Some MCUs** let you remap address 0 to non-existent memory, or have the flash at another base address with nothing at 0 (then a NULL access is a precise BusFault).
3. **Static analysis** and compiler warnings (`-Wnull-dereference`, clang analyzer, cppcheck).
4. **Unit-test the code on the host** with sanitizers, where NULL dereferences crash reliably.
5. **Defensive coding:** check pointers returned by allocation and lookup functions; initialise every pointer.

**Why it matters:** a NULL function pointer call (`cb()` where `cb == NULL`) loads the PC from address 0 — the initial stack pointer value — and the core tries to execute at an address in RAM, usually ending in a HardFault far from the cause. Knowing this pattern helps you recognise it in a fault dump: a PC equal to the initial MSP value is a strong hint.

### How do you write a function that returns multiple values? {E}
**Short answer:** C functions return only one value, so either return a **struct** containing all the results, or return a **status code** and write the results through **pointer parameters** (output parameters). Embedded APIs usually use the second form so errors are explicit.

```c
#include <stdint.h>

typedef struct { int16_t x, y, z; } accel_t;

/* 1. return a small struct by value */
accel_t accel_read(void);

/* 2. status + output parameters */
typedef enum { OK = 0, ERR_TIMEOUT, ERR_BUS } status_t;
status_t accel_read2(int16_t *x, int16_t *y, int16_t *z);

/* 3. status + output struct (common and extensible) */
status_t accel_read3(accel_t *out);

/* usage */
accel_t a;
if (accel_read3(&a) != OK) { /* handle error */ }
```

**Trade-offs**

| Approach | Pros | Cons |
|---|---|---|
| Return a struct | clean, no pointers, no aliasing issues | no separate error channel (unless the struct has a status field); large structs are copied |
| Output pointers | explicit status, caller owns the memory | callers can pass NULL; function must check |
| Output struct pointer + status | extensible (add fields without changing the signature) | slightly more code |
| Global variables | none worth mentioning | not reentrant, hidden coupling |

**Performance:** on Arm (AAPCS), a struct of up to 4 bytes is returned in `r0`; larger structs are returned through a hidden pointer to memory reserved by the caller, so returning a 6-byte `accel_t` is still cheap. On AArch64, structs up to 16 bytes come back in registers.

**Good API habits:** document whether outputs are written on failure (usually "not modified" or "undefined"), use `const` for inputs, and mark the function `[[nodiscard]]` (C23) or `__attribute__((warn_unused_result))` so callers cannot ignore the status.

### What is a flexible array member? {M}
**Short answer:** A flexible array member is an array with no size declared as the **last** member of a struct (C99). The struct describes a header followed by a variable amount of data, allocated in one block: `malloc(sizeof(struct packet) + n)`. `sizeof` the struct does not include the array.

```c
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

struct packet {
    uint16_t len;
    uint8_t  type;
    uint8_t  data[];          /* flexible array member: must be last */
};

struct packet *packet_new(uint8_t type, const uint8_t *payload, uint16_t n)
{
    struct packet *p = malloc(sizeof *p + n);   /* header + n bytes, one allocation */
    if (p == NULL) return NULL;
    p->len = n;
    p->type = type;
    memcpy(p->data, payload, n);
    return p;                                   /* one free(p) releases everything */
}
```

**Why use it**

- One allocation and one `free` instead of a header plus a separately allocated buffer.
- The data is contiguous with the header (good for cache and for sending the whole thing with one DMA or `write` call).

**Rules**

- It must be the last member, and the struct must have at least one other member.
- A struct with a flexible array member cannot be an element of an array or a member of another struct (GCC allows the latter as an extension).
- `sizeof(struct packet)` may include padding before `data`; using `offsetof(struct packet, data) + n` gives the minimum size.
- Assigning or copying such structs by value copies only the header.

**Older tricks you will see in legacy code:** `uint8_t data[1];` (the "struct hack": accessing beyond index 0 is technically undefined) and `uint8_t data[0];` (a GNU extension). Modern compilers with `-fstrict-flex-arrays` and bounds checking treat these differently, so convert them to `[]`. The Linux kernel completed this conversion and uses `__counted_by(len)` annotations so the compiler can bounds-check the array.

**Embedded note:** with static allocation, you can use the same type over a fixed buffer: `static uint8_t storage[sizeof(struct packet) + 64]` and a pointer to it, keeping the alignment of the struct in mind.

### What are offsetof and container_of? {M}
**Short answer:** `offsetof(type, member)` (from `<stddef.h>`) gives the byte offset of a member within a struct, as a compile-time constant. `container_of(ptr, type, member)` (a Linux kernel macro) uses it the other way round: given a pointer to a member, it computes the address of the struct that contains it. Together they let generic code (lists, queues, callbacks) work with embedded "hook" members.

```c
#include <stddef.h>
#include <stdint.h>

#define container_of(ptr, type, member) \
    ((type *)((char *)(ptr) - offsetof(type, member)))

struct list_node { struct list_node *next; };

struct uart_msg {
    uint8_t len;
    uint8_t data[16];
    struct list_node node;          /* hook used by a generic queue */
};

void process(struct list_node *n)
{
    struct uart_msg *m = container_of(n, struct uart_msg, node);
    /* m->len, m->data are now accessible */
}
```

**How `offsetof` can be implemented** (the classic version, technically undefined but historically common):

```c
#define my_offsetof(type, member) ((size_t)&(((type *)0)->member))
```

Modern compilers provide `__builtin_offsetof`, which `<stddef.h>` uses; always use the standard macro.

**Uses**

- **Intrusive linked lists** (Linux `list_head`, Zephyr `sys_slist`, FreeRTOS list items inside the TCB): the list code only knows about the node; `container_of` gets back to the object. No separate allocation per list entry.
- **Callbacks with embedded context:** a driver registers a `struct timer` embedded in its own state struct; the timer callback receives `struct timer *` and recovers the driver state.
- **Checking layouts:** `_Static_assert(offsetof(struct regs, CTRL) == 0x08, "")` to verify that a register struct matches the datasheet.
- **Serialisation** code that needs member positions.

**Cautions:** `container_of` is only correct if the pointer really points to that member of that type of struct; a wrong type gives a silently wrong address. The kernel's version adds a type check using `typeof` to catch mismatches at compile time.

### How do you allocate a 64-byte-aligned buffer without malloc? {M}
**Short answer:** Use the C11 alignment specifier on a fixed-size object, or a compiler/platform alignment facility.

```c
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
_Alignas(64) static unsigned char buffer[256];

bool is_aligned(const void *p, uintptr_t a)
{
    return a && !(a & (a - 1u)) &&
           !((uintptr_t)p & (a - 1u));
}
```

**Example:** 0x1000 is 64-byte aligned because its low six bits are zero; 0x1004 is not.

```text
0x1000      0x1040      0x1080      0x10C0
| 64 bytes  | 64 bytes  | 64 bytes  | 64 bytes  |
^ buffer start
```

**Why:** Alignment can be needed for SIMD, cache-line isolation and DMA buffers. Extended alignment support depends on the compiler and target. DMA mapping and cache ownership are separate requirements; alignment alone does not make the buffer DMA-safe.

**Interview takeaway:** Static aligned storage avoids heap allocation and provides the required address boundary when supported.
