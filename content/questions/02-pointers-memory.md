---
slug: pointers-memory
title: Pointers & Memory
icon: 🎯
level: Beginner
order: 2
desc: Pointer arithmetic, arrays vs pointers, the memory layout of a C program, stack vs heap, alignment and endianness.
---
Pointers are where interviewers separate people who have written C from people who have debugged it. Expect to draw memory on a whiteboard.

### What is a pointer? {E}
A pointer is a variable whose value is the address of another object. Its type tells the compiler what it points to, which decides how many bytes a dereference reads and how far `p + 1` moves.

```c
int x = 10;
int *p = &x;   /* p holds the address of x */
*p = 20;       /* x is now 20 */
```

On a 32-bit MCU a data pointer is 4 bytes; on 64-bit Linux it is 8.

### How does pointer arithmetic work? {E}
Adding `n` to a pointer moves it by `n * sizeof(*p)` bytes, not `n` bytes:

```c
uint32_t buf[4];
uint32_t *p = buf;
p + 1;              /* address of buf[1], 4 bytes further */
(uint8_t *)p + 1;   /* 1 byte further */
```

Subtracting two pointers into the same array gives the number of elements between them (type `ptrdiff_t`). Arithmetic is only defined within an array and one past its end; anything else is UB.

### What is a void pointer? {E}
`void *` is a generic pointer that can hold the address of any object type. You cannot dereference it or do arithmetic on it in standard C (GCC allows arithmetic as an extension, treating the size as 1). It converts implicitly to and from any object pointer in C, which is why `malloc` returns `void *` and needs no cast in C. Use it for generic APIs such as `memcpy`, `qsort` and callback context arguments.

### What is a double pointer and when do you need one? {M}
A pointer to a pointer (`int **pp`). You need one when a function must change *which* object the caller's pointer refers to:

```c
int alloc_buf(uint8_t **out, size_t n)
{
    *out = malloc(n);
    return *out ? 0 : -1;
}

uint8_t *buf;
alloc_buf(&buf, 64);
```

Other uses: arrays of strings (`char **argv`), and linked-list insert/delete without special-casing the head.

### What is the difference between char *s = "hello" and char s[] = "hello"? {M}
- `char *s = "hello";` makes `s` point to a string literal, which normally lives in read-only memory (`.rodata`, often flash). Writing `s[0] = 'H'` is UB and may crash or silently do nothing. Declare it `const char *`.
- `char s[] = "hello";` creates a 6-byte array (including `'\0'`) initialised with a copy of the literal. You can modify it freely. `sizeof s` is 6, whereas `sizeof` the pointer version is 4 or 8.

### What does int (*p)[10] mean versus int *p[10]? {M}
- `int *p[10]` is an array of 10 pointers to int (`[]` binds tighter than `*`).
- `int (*p)[10]` is one pointer to an array of 10 ints. `p + 1` advances by 40 bytes.

Similarly `int (*fp)(int)` is a pointer to a function taking `int` and returning `int`, while `int *fp(int)` declares a function returning `int *`. Use `typedef` to keep complex declarations readable.

### What is the memory layout of a C program? {E}
From low to high addresses on a typical system:

1. **Text (.text)**: machine code, read-only.
2. **Read-only data (.rodata)**: constants and string literals.
3. **Initialised data (.data)**: globals and statics with non-zero initial values.
4. **BSS (.bss)**: zero-initialised globals and statics.
5. **Heap**: grows upward, managed by `malloc`/`free`.
6. **Stack**: grows downward, holds locals, return addresses and saved registers.

On a microcontroller `.text` and `.rodata` stay in flash, `.data` is copied from flash to RAM at start-up, and the heap and stack share the remaining RAM. See the article *Memory layout of a C program on a microcontroller*.

### What is the difference between stack and heap? {E}
| | Stack | Heap |
|---|---|---|
| Allocation | Automatic, on function entry | Explicit, `malloc`/`free` |
| Speed | One instruction (move SP) | Allocator search, can be slow |
| Lifetime | Until the function returns | Until freed |
| Size | Small, fixed per thread | Larger, but can fragment |
| Failure | Overflow, often silent corruption | `malloc` returns `NULL` |

Embedded systems prefer static and stack allocation with known bounds.

### What is a memory leak? {E}
Memory that has been allocated but can no longer be freed because the program has lost every pointer to it. In a long-running device even a few bytes per event will eventually exhaust the heap. Tools: Valgrind and AddressSanitizer on Linux; on MCUs, heap statistics from the RTOS (`xPortGetMinimumEverFreeHeapSize()` in FreeRTOS) and code review.

### What is heap fragmentation and why does it matter in embedded systems? {M}
After many allocations and frees of different sizes, free memory is split into small, non-contiguous holes. A request can fail even though the total free memory is large enough. On a device that must run for years without reboot, this is a real failure mode.

Mitigations:
- Allocate everything at start-up and never free.
- Use **fixed-size block pools** (memory pools), where any free block fits any request of that class.
- Use an RTOS allocator designed for it (FreeRTOS `heap_4` coalesces adjacent free blocks).

### How do you detect a stack overflow on a microcontroller? {M}
- **Stack painting**: fill the stack with a pattern (e.g. `0xDEADBEEF`) at boot and check later how much is untouched (the "high-water mark").
- **Guard region**: place an MPU no-access region below the stack so overflow causes a MemManage fault.
- **Stack limit registers**: ARMv8-M (Cortex-M23/M33) has `MSPLIM`/`PSPLIM` that fault on overflow.
- **RTOS checks**: FreeRTOS `configCHECK_FOR_STACK_OVERFLOW` checks the stack pointer and a canary on each context switch.
- **Static analysis**: `-fstack-usage` and a call-graph tool give the worst case at build time.

### What is alignment and what happens on an unaligned access? {M}
An object is aligned if its address is a multiple of its alignment requirement (usually its size for primitive types). Effects of unaligned access vary by core:

- Cortex-M3/M4/M7 handle unaligned `LDR`/`STR` in hardware with a time penalty, but `LDRD`, `LDM` and `STM` still fault.
- Cortex-M0/M0+ raise a HardFault on any unaligned access.
- x86 handles it, usually with a small penalty.

Casting a `uint8_t *` buffer to `uint32_t *` and dereferencing it is the usual cause. Use `memcpy` into a local variable instead; compilers turn it into the best instruction sequence.

### What is endianness and how do you check it in code? {E}
Endianness is the byte order of multi-byte values in memory. **Little-endian** stores the least significant byte at the lowest address (x86, most ARM configurations). **Big-endian** stores the most significant byte first (network byte order, some PowerPC).

```c
int is_little_endian(void)
{
    uint16_t x = 1;
    return *(uint8_t *)&x == 1;
}
```

For protocols, build values from bytes explicitly: `v = (uint32_t)b[0] << 24 | b[1] << 16 | b[2] << 8 | b[3];`, which works on any host.

### How do you swap the endianness of a 32-bit value? {E}
```c
static inline uint32_t bswap32(uint32_t x)
{
    return  (x >> 24) |
           ((x >> 8) & 0x0000FF00u) |
           ((x << 8) & 0x00FF0000u) |
            (x << 24);
}
```

In practice use `__builtin_bswap32()`, which compiles to a single `REV` instruction on ARM, or `htonl`/`ntohl` for network code.

### What is strict aliasing? {H}
The strict aliasing rule says an object may only be accessed through an lvalue of its own type (or a compatible, signed/unsigned or qualified version of it), or through a character type. The compiler uses this to assume that an `int *` and a `float *` never point to the same memory.

```c
uint32_t f2u(float f) { return *(uint32_t *)&f; }   /* UB */
uint32_t f2u_ok(float f) { uint32_t u; memcpy(&u, &f, sizeof u); return u; }
```

Violations often work at `-O0` and break at `-O2`. Use `memcpy`, a union (fine in C), or `-fno-strict-aliasing` (the Linux kernel builds with it).

### How do you access a memory-mapped register at a fixed address? {E}
Cast the address to a pointer to a `volatile` fixed-width type and dereference it:

```c
#define GPIOA_ODR (*(volatile uint32_t *)0x40020014u)

GPIOA_ODR |= (1u << 5);   /* drive PA5 high */
```

Vendor headers (CMSIS) do the same thing with a struct overlay: `GPIOA->ODR |= 1u << 5;`, where `GPIOA` is `((GPIO_TypeDef *)0x40020000u)` and each struct member is declared `volatile`.

### Why is sizeof not a function? {E}
`sizeof` is a compile-time operator. For everything except variable-length arrays it is evaluated by the compiler and its operand is **not executed**: `sizeof(i++)` does not increment `i`. Parentheses are only required around a type name (`sizeof(int)`); for an expression `sizeof x` is valid.

### How do you find the number of elements in an array? {E}
```c
#define ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))
```

This only works on a real array in scope. Passed to a function, the array has decayed to a pointer and the macro silently gives the wrong answer. The Linux kernel's `ARRAY_SIZE` adds a compile-time check that the argument is an array.

### What is the difference between memcpy and memmove? {E}
Both copy `n` bytes. `memcpy` assumes the regions do not overlap and may copy in any order. `memmove` handles overlap correctly, as if the data were copied through a temporary buffer, typically by copying backwards when the destination is above the source. Use `memmove` whenever overlap is possible, for example when shifting data inside one buffer.

### What is a NULL pointer dereference on a Cortex-M and why might it not crash? {H}
On many Cortex-M parts, address `0x00000000` is mapped to flash (aliased to the vector table). Reading through a NULL pointer returns the initial stack pointer value instead of faulting, and the bug goes unnoticed. Writes to flash are usually ignored or cause a bus fault depending on the part. To catch NULL dereferences, configure the MPU to make the first few hundred bytes no-access (after the vector table has been relocated with `VTOR`) or rely on static analysis.

### How do you write a function that returns multiple values? {E}
Either return a struct, or pass pointers to output parameters:

```c
typedef struct { int16_t x, y, z; } accel_t;
accel_t read_accel(void);                        /* returns a small struct */
int read_accel2(int16_t *x, int16_t *y, int16_t *z);   /* returns status */
```

Embedded APIs usually return a status code and write results through pointers, so errors are explicit.

### What is a flexible array member? {M}
A struct whose last member is an array of unspecified size, used for variable-length records:

```c
struct packet {
    uint16_t len;
    uint8_t  data[];     /* C99 flexible array member */
};

struct packet *p = malloc(sizeof *p + n);
p->len = n;
```

`sizeof(struct packet)` excludes the array. The older trick `uint8_t data[1];` or `data[0]` (GNU) is technically UB or non-standard.
