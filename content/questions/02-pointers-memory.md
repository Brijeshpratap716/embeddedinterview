---
slug: pointers-memory
title: Pointers & Memory
icon: 🎯
level: Beginner
order: 2
desc: Pointer arithmetic, arrays vs pointers, the memory layout of a C program, stack vs heap, memory pools, alignment, endianness and strict aliasing.
---
Concise pointers and memory interview notes, with practical C examples and memory illustrations. Snippets illustrate the indicated operation and may require standard headers or surrounding function context.

### What is a pointer? {E}
**Short answer:** A pointer stores a value that identifies an object or function in memory.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 80" width="100%" role="img" aria-label="p contains an address|x contains 20" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="324" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="172" y="43" fill="#0c4a6e" font-size="12">p contains an address</text><rect x="346" y="8" width="324" height="62" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="508" y="43" fill="#0c4a6e" font-size="12">x contains 20</text></svg></div>

**How it works**

1. Declare a pointer with the pointed-to type.
2. Use & to obtain an object address.
3. Dereference with * only while the object is valid.

**Example**

```c
int x = 10;
int *p = &x;
*p = 20; // x becomes 20
```

**Interview takeaway:** A pointer is not the object itself. Its type determines the meaning of dereferencing.

### How does pointer arithmetic work? {E}
**Short answer:** Pointer arithmetic advances in units of the pointed-to type, not bytes.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 80" width="100%" role="img" aria-label="a[0]: 10|a[1]: 20|a[2]: 30" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="43" fill="#0c4a6e" font-size="12">a[0]: 10</text><rect x="234" y="8" width="212" height="62" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="43" fill="#0c4a6e" font-size="12">a[1]: 20</text><rect x="458" y="8" width="212" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="43" fill="#0c4a6e" font-size="12">a[2]: 30</text></svg></div>

**How it works**

1. For an array a, a+i points to element i.
2. Subtraction gives the number of elements between pointers into the same array.
3. One-past-end may be formed but not dereferenced.

**Example**

```c
int a[] = {10, 20, 30};
int *p = a;
int x = *(p + 1); // 20
```

**Interview takeaway:** If sizeof(int) is 4, p+1 advances 4 bytes. Arithmetic outside the array (apart from one-past) is undefined.

### What is a void pointer? {E}
**Short answer:** void * is a generic object pointer that does not specify the object type.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 80" width="100%" role="img" aria-label="int *|void *|int *" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="43" fill="#0c4a6e" font-size="12">int *</text><rect x="234" y="8" width="212" height="62" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="43" fill="#0c4a6e" font-size="12">void *</text><rect x="458" y="8" width="212" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="43" fill="#0c4a6e" font-size="12">int *</text></svg></div>

**How it works**

1. Convert an object pointer to void *.
2. Pass it through a generic interface.
3. Convert back to the appropriate type before dereferencing.

**Example**

```c
int x = 42;
void *p = &x;
int value = *(int *)p;
```

**Interview takeaway:** Standard C does not permit arithmetic or dereferencing on void *; use unsigned char * for byte access.

### What is a double pointer and when do you need one? {M}
**Short answer:** A double pointer points to another pointer, allowing a function to modify the caller's pointer.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 80" width="100%" role="img" aria-label="pp|p|object" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="43" fill="#0c4a6e" font-size="12">pp</text><rect x="234" y="8" width="212" height="62" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="43" fill="#0c4a6e" font-size="12">p</text><rect x="458" y="8" width="212" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="43" fill="#0c4a6e" font-size="12">object</text></svg></div>

**How it works**

1. Pass the address of a pointer variable.
2. Dereference once to access the pointer.
3. Dereference twice to access the object.

**Example**

```c
void set(int **p, int *value) { *p = value; }
int x = 7;
int *q = NULL;
// set(&q, &x); // q now points to x
```

**Interview takeaway:** Common uses include changing a list head, returning an allocated buffer and arrays of pointers.

### What is the difference between char *s = "hello" and char s[] = "hello"? {M}
**Short answer:** A pointer initialized with a string literal refers to literal storage; an array initialized from a literal contains a modifiable copy.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 80" width="100%" role="img" aria-label="Literal: hello|Array: Hello" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="324" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="172" y="43" fill="#0c4a6e" font-size="12">Literal: hello</text><rect x="346" y="8" width="324" height="62" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="508" y="43" fill="#0c4a6e" font-size="12">Array: Hello</text></svg></div>

**How it works**

1. The literal includes a terminating zero.
2. The array has its own elements.
3. Changing a literal has undefined behavior.

**Example**

```c
const char *p = "hello";
char s[] = "hello";
s[0] = 'H';
```

**Interview takeaway:** Prefer const char * for literals. sizeof(s) is 6; sizeof(p) is the pointer size.

### What does int (*p)[10] mean versus int *p[10]? {M}
**Short answer:** Parentheses change the declarator: int (*p)[10] is a pointer to a ten-int array; int *p[10] is an array of ten int pointers.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 80" width="100%" role="img" aria-label="p: one pointer to row|q: ten pointer slots" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="324" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="172" y="43" fill="#0c4a6e" font-size="12">p: one pointer to row</text><rect x="346" y="8" width="324" height="62" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="508" y="43" fill="#0c4a6e" font-size="12">q: ten pointer slots</text></svg></div>

**How it works**

1. Read the declarator outward from its name.
2. Parentheses bind first.
3. Array indexing binds more tightly than the pointer declarator.

**Example**

```c
int a[2][10] = {{0}};
int (*p)[10] = a;
int *q[10] = {0};
```

**Interview takeaway:** p+1 advances one whole row, not one int.

### What is the memory layout of a C program? {E}
**Short answer:** A typical executable uses code, read-only data, initialized data, zero-initialized data, heap and stacks.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 80" width="100%" role="img" aria-label="Text / rodata|Data / BSS|Heap / stacks" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="43" fill="#0c4a6e" font-size="12">Text / rodata</text><rect x="234" y="8" width="212" height="62" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="43" fill="#0c4a6e" font-size="12">Data / BSS</text><rect x="458" y="8" width="212" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="43" fill="#0c4a6e" font-size="12">Heap / stacks</text></svg></div>

**How it works**

1. The linker assigns sections.
2. The loader or startup code initializes storage.
3. Automatic objects normally use registers/stack and dynamic allocation uses allocator-managed memory.

**Example**

```c
static int initialized = 5; // usually .data
static int zeroed;          // usually .bss
const char msg[] = "OK";    // placement depends on scope/compiler
```

**Interview takeaway:** This is a conceptual layout. Actual addresses and section placement depend on linker script, OS and target.

### What is the difference between stack and heap? {E}
**Short answer:** Stack storage typically follows function or task lifetime; heap storage is explicitly managed by an allocator.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 80" width="100%" role="img" aria-label="Stack: frames|Heap: allocations" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="324" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="172" y="43" fill="#0c4a6e" font-size="12">Stack: frames</text><rect x="346" y="8" width="324" height="62" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="508" y="43" fill="#0c4a6e" font-size="12">Heap: allocations</text></svg></div>

**How it works**

1. A call may reserve a stack frame.
2. Returning releases that frame.
3. Malloc/free manage independently lived blocks.

**Example**

```c
void f(void) {
    int local[8];
    int *p = malloc(8 * sizeof *p);
    if (p) free(p);
}
```

**Interview takeaway:** Stack size is bounded, especially in RTOS tasks. Heap allocations can fail or fragment.

### What is a memory leak? {E}
**Short answer:** A memory leak occurs when allocated storage is no longer reachable or is never released when no longer needed.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 80" width="100%" role="img" aria-label="Allocate|Use|Free" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="43" fill="#0c4a6e" font-size="12">Allocate</text><rect x="234" y="8" width="212" height="62" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="43" fill="#0c4a6e" font-size="12">Use</text><rect x="458" y="8" width="212" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="43" fill="#0c4a6e" font-size="12">Free</text></svg></div>

**How it works**

1. Allocate a block.
2. Retain ownership.
3. Release it on every relevant success/error path.

**Example**

```c
void f(void) {
    char *p = malloc(64);
    if (!p) return;
    // use p
    free(p);
}
```

**Interview takeaway:** Overwriting the sole pointer before free leaks the block. Use Valgrind or sanitizers on supported targets.

### What is heap fragmentation and why does it matter in embedded systems? {M}
**Short answer:** Fragmentation reduces the allocator's ability to satisfy requests despite free memory.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 80" width="100%" role="img" aria-label="Used 32|Free 16|Used 32|Free 16" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="156" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="88" y="43" fill="#0c4a6e" font-size="12">Used 32</text><rect x="178" y="8" width="156" height="62" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="256" y="43" fill="#0c4a6e" font-size="12">Free 16</text><rect x="346" y="8" width="156" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="424" y="43" fill="#0c4a6e" font-size="12">Used 32</text><rect x="514" y="8" width="156" height="62" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="592" y="43" fill="#0c4a6e" font-size="12">Free 16</text></svg></div>

**How it works**

1. Variable-size allocations leave gaps after frees.
2. Adjacent free blocks may coalesce.
3. A large request needs a sufficiently large usable block.

**Example**

Example: [used 32][free 16][used 32][free 16]. Total free is 32 bytes but a contiguous 24-byte request cannot fit either gap.

**Interview takeaway:** Fixed-size pools reduce external fragmentation; rounding allocations up can introduce internal fragmentation.

### What is a memory pool, and how do you implement a fixed-size block allocator? {M}
**Short answer:** A fixed-block pool preallocates equal-size slots and tracks which are available, giving bounded allocation work.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 80" width="100%" role="img" aria-label="Free slot|Allocated slot|Free slot" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="43" fill="#0c4a6e" font-size="12">Free slot</text><rect x="234" y="8" width="212" height="62" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="43" fill="#0c4a6e" font-size="12">Allocated slot</text><rect x="458" y="8" width="212" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="43" fill="#0c4a6e" font-size="12">Free slot</text></svg></div>

**How it works**

1. Initialize the free-slot bitmap.
2. Allocate an unused slot.
3. Return its index on release after validating ownership.

**Example**

```c
#include <stdbool.h>
#include <stddef.h>
#include <stdalign.h>
static max_align_t slots[8];
static bool used[8];
void *pool_alloc(void) {
    for (unsigned i=0;i<8;i++) if (!used[i]) {
        used[i]=true; return &slots[i];
    }
    return NULL;
}
bool pool_free(void *p) {
    for (unsigned i=0;i<8;i++) if (p == &slots[i] && used[i]) {
        used[i]=false; return true;
    }
    return false;
}
```

**Interview takeaway:** This simple single-threaded pool supports objects fitting max_align_t; synchronize concurrent access. A free list can make allocation O(1).

### How would you implement a simple malloc() and free()? {H}
**Short answer:** A simple heap allocator manages a region using metadata recording block size and allocation status.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 80" width="100%" role="img" aria-label="Header + used payload|Header + free payload|Header + free payload" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="43" fill="#0c4a6e" font-size="12">Header + used payload</text><rect x="234" y="8" width="212" height="62" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="43" fill="#0c4a6e" font-size="12">Header + free payload</text><rect x="458" y="8" width="212" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="43" fill="#0c4a6e" font-size="12">Header + free payload</text></svg></div>

**How it works**

1. Align the request and check overflow.
2. Find a free block large enough.
3. Split if useful.
4. On free mark unused and coalesce adjacent free blocks.

**Example**

Pseudocode: alloc(n): round_up(n); find_fit(n); split(block); mark_used(block); return payload. free(p): validate(p); mark_free(block); merge_neighbors(block).

**Interview takeaway:** Metadata, alignment, bounds, invalid frees and locking are essential. This is the algorithm, not a production malloc replacement.

### How do you detect a stack overflow on a microcontroller? {M}
**Short answer:** A stack overflow happens when stack usage exceeds reserved storage and may corrupt nearby data.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 80" width="100%" role="img" aria-label="Stack top|Used stack|Watermark / guard" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="43" fill="#0c4a6e" font-size="12">Stack top</text><rect x="234" y="8" width="212" height="62" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="43" fill="#0c4a6e" font-size="12">Used stack</text><rect x="458" y="8" width="212" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="43" fill="#0c4a6e" font-size="12">Watermark / guard</text></svg></div>

**How it works**

1. Fill unused stack with a pattern and check the remaining watermark.
2. Place a guard/canary at the boundary.
3. Enable an MPU guard or RTOS overflow hook when available.

**Example**

Example: an RTOS task has a 1024-byte stack but its worst observed use is 900 bytes, leaving only 124 bytes of measured margin.

**Interview takeaway:** Watermarks are measurements, not proofs of worst-case depth. Interrupt nesting and recursion can increase consumption.

### What is alignment and what happens on an unaligned access? {M}
**Short answer:** Alignment requires an address to be a multiple of the object's or hardware's alignment boundary.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 80" width="100%" role="img" aria-label="0x1000: aligned|0x1004: not 16-byte aligned" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="324" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="172" y="43" fill="#0c4a6e" font-size="12">0x1000: aligned</text><rect x="346" y="8" width="324" height="62" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="508" y="43" fill="#0c4a6e" font-size="12">0x1004: not 16-byte aligned</text></svg></div>

**How it works**

1. The compiler aligns ordinary objects.
2. A linker or allocator can request stronger alignment.
3. Unaligned accesses may be slower, split, or fault depending on architecture and memory type.

**Example**

```c
#include <stdint.h>
#include <stdbool.h>
bool aligned16(const void *p) {
    return ((uintptr_t)p & 15u) == 0;
}
```

**Interview takeaway:** A misaligned typed C access can be undefined even when the CPU tolerates it. Use memcpy for unaligned byte data.

### What is endianness and how do you check it in code? {E}
**Short answer:** Endianness describes the order of bytes in a multi-byte object.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 80" width="100%" role="img" aria-label="Little: 02 01|Big: 01 02" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="324" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="172" y="43" fill="#0c4a6e" font-size="12">Little: 02 01</text><rect x="346" y="8" width="324" height="62" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="508" y="43" fill="#0c4a6e" font-size="12">Big: 01 02</text></svg></div>

**How it works**

1. Little-endian places the least significant byte at the lowest address.
2. Big-endian places the most significant byte there.
3. Inspect the object through unsigned char.

**Example**

```c
#include <stdint.h>
uint16_t n = 0x0102;
// ((const unsigned char *)&n)[0] is 2 on little-endian (8-bit bytes).
```

**Interview takeaway:** Endian conversion is needed for protocols and device formats; it is unrelated to register bit numbering.

### How do you swap the endianness of a 32-bit value? {E}
**Short answer:** A byte swap reverses the four byte positions of a 32-bit value.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 80" width="100%" role="img" aria-label="12 34 56 78|78 56 34 12" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="324" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="172" y="43" fill="#0c4a6e" font-size="12">12 34 56 78</text><rect x="346" y="8" width="324" height="62" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="508" y="43" fill="#0c4a6e" font-size="12">78 56 34 12</text></svg></div>

**How it works**

1. Mask each byte.
2. Shift it to the opposite position; OR all four fields.

**Example**

```c
#include <stdint.h>
uint32_t swap32(uint32_t x) {
    return (x>>24) | ((x>>8)&0xff00u) |
           ((x<<8)&0xff0000u) | (x<<24);
}
```

**Interview takeaway:** Use unsigned operands. A compiler builtin or architecture instruction can generate the same result.

### What is strict aliasing? {H}
**Short answer:** Strict aliasing limits the types through which an object may be accessed, allowing the compiler to optimize memory operations.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 80" width="100%" role="img" aria-label="float object|memcpy bytes|integer representation" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="43" fill="#0c4a6e" font-size="12">float object</text><rect x="234" y="8" width="212" height="62" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="43" fill="#0c4a6e" font-size="12">memcpy bytes</text><rect x="458" y="8" width="212" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="43" fill="#0c4a6e" font-size="12">integer representation</text></svg></div>

**How it works**

1. Access through compatible types or a permitted exception.
2. Character types can inspect object representation.
3. Use memcpy to copy representations without incompatible typed dereferences.

**Example**

```c
float f = 1.0f;
uint32_t bits;
// Assuming equal sizes:
memcpy(&bits, &f, sizeof bits);
```

**Interview takeaway:** A cast does not make incompatible dereferencing legal. Do not assume all float representations are IEEE 754.

### How do you access a memory-mapped register at a fixed address? {E}
**Short answer:** A memory-mapped peripheral register occupies an address in the processor's address map.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 80" width="100%" role="img" aria-label="CPU load/store|MMIO address|Peripheral" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="43" fill="#0c4a6e" font-size="12">CPU load/store</text><rect x="234" y="8" width="212" height="62" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="43" fill="#0c4a6e" font-size="12">MMIO address</text><rect x="458" y="8" width="212" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="43" fill="#0c4a6e" font-size="12">Peripheral</text></svg></div>

**How it works**

1. Obtain the register address from the hardware manual.
2. Use the required access width.
3. Read or write through an appropriate volatile-qualified pointer in bare-metal code.

**Example**

```c
#include <stdint.h>
#define REG (*(volatile uint32_t *)0x40000000u)
// REG = 1; // only if this address and write are valid on the target
```

**Interview takeaway:** Linux drivers use ioremap and readl/writel. Volatile does not provide general ordering or safe register read-modify-write.

### Why is sizeof not a function? {E}
**Short answer:** sizeof is a C operator that yields the storage size of a type or expression in bytes, as size_t.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 80" width="100%" role="img" aria-label="Type / expression|Compiler|Size in bytes" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="43" fill="#0c4a6e" font-size="12">Type / expression</text><rect x="234" y="8" width="212" height="62" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="43" fill="#0c4a6e" font-size="12">Compiler</text><rect x="458" y="8" width="212" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="43" fill="#0c4a6e" font-size="12">Size in bytes</text></svg></div>

**How it works**

1. The operand is normally not evaluated.
2. The result includes padding.
3. Variable-length array types can require runtime evaluation.

**Example**

```c
int a[10];
size_t n = sizeof a; // 10 * sizeof(int)
size_t m = sizeof(int);
```

**Interview takeaway:** A C byte is CHAR_BIT bits, not necessarily 8. sizeof does not discover the allocated length behind a pointer.

### How do you find the number of elements in an array? {E}
**Short answer:** An actual array's size divided by one element's size gives its element count.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 80" width="100%" role="img" aria-label="Array: 4 elements|sizeof a / sizeof a[0]" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="324" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="172" y="43" fill="#0c4a6e" font-size="12">Array: 4 elements</text><rect x="346" y="8" width="324" height="62" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="508" y="43" fill="#0c4a6e" font-size="12">sizeof a / sizeof a[0]</text></svg></div>

**How it works**

1. Apply sizeof before array-to-pointer decay.
2. Divide by sizeof array[0].
3. Pass the count explicitly when calling a function.

**Example**

```c
int a[] = {1,2,3,4};
size_t n = sizeof a / sizeof a[0]; // 4
```

**Interview takeaway:** An array parameter is adjusted to a pointer; the formula cannot recover its original length there.

### What is the difference between memcpy and memmove? {E}
**Short answer:** memcpy copies non-overlapping byte regions; memmove also supports overlapping regions.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 80" width="100%" role="img" aria-label="Before: A B C D E _ _|After: A B A B C D E" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="324" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="172" y="43" fill="#0c4a6e" font-size="12">Before: A B C D E _ _</text><rect x="346" y="8" width="324" height="62" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="508" y="43" fill="#0c4a6e" font-size="12">After: A B A B C D E</text></svg></div>

**How it works**

1. If destination overlaps the source at a higher address, a typical memmove copies backward.
2. Otherwise it can copy forward.
3. Both functions return destination.

**Example**

```c
char b[8] = "ABCDE";
memmove(b+2, b, 5); // ABABCDE plus existing terminator
```

**Interview takeaway:** Overlapping memcpy is undefined. Both functions require valid ranges; neither automatically adds a string terminator.

### What is a NULL pointer dereference on a Cortex-M and why might it not crash? {H}
**Short answer:** Dereferencing NULL is undefined behavior in C, regardless of whether hardware faults.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 80" width="100%" role="img" aria-label="NULL access|Mapped address or fault" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="324" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="172" y="43" fill="#0c4a6e" font-size="12">NULL access</text><rect x="346" y="8" width="324" height="62" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="508" y="43" fill="#0c4a6e" font-size="12">Mapped address or fault</text></svg></div>

**How it works**

1. On some Cortex-M maps address zero aliases vector table or flash.
2. An access might read real memory; MPU permissions or bus faults can instead trap it.

**Example**

Example: reading address zero via a null pointer is invalid C even if the processor happens to return a vector-table word.

**Interview takeaway:** Enable protection when supported; never use absence of a HardFault as evidence of valid C.

### How do you write a function that returns multiple values? {E}
**Short answer:** C returns one value directly, but output pointers or a returned structure can carry multiple results.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 80" width="100%" role="img" aria-label="Input a,b|Function|Result: two fields" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="43" fill="#0c4a6e" font-size="12">Input a,b</text><rect x="234" y="8" width="212" height="62" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="43" fill="#0c4a6e" font-size="12">Function</text><rect x="458" y="8" width="212" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="43" fill="#0c4a6e" font-size="12">Result: two fields</text></svg></div>

**How it works**

1. Define output types.
2. Pass addresses of caller objects or return a structure.
3. Document failure and validity rules.

**Example**

```c
struct result { int quotient, remainder; };
struct result divide(int a, int b) {
    return (struct result){a/b, a%b};
}
```

**Interview takeaway:** Caller must ensure b != 0 and avoid signed division overflow (INT_MIN / -1).

### What is a flexible array member? {M}
**Short answer:** A flexible array member is an unsized last member of a structure used for variable-size trailing data.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 80" width="100%" role="img" aria-label="Header: len|Trailing data bytes" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="324" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="172" y="43" fill="#0c4a6e" font-size="12">Header: len</text><rect x="346" y="8" width="324" height="62" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="508" y="43" fill="#0c4a6e" font-size="12">Trailing data bytes</text></svg></div>

**How it works**

1. Allocate the fixed header plus payload.
2. Check addition overflow and allocation failure.
3. Store the length and access only allocated elements.

**Example**

```c
struct packet { size_t len; unsigned char data[]; };
// after checking n <= SIZE_MAX - sizeof(struct packet):
struct packet *p = malloc(sizeof *p + n);
if (p) p->len = n;
```

**Interview takeaway:** sizeof excludes the flexible array elements; free the whole allocation once.

### What are offsetof and container_of? {M}
**Short answer:** offsetof returns a member's byte offset within a structure; container_of recovers the enclosing object from a valid member pointer.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 80" width="100%" role="img" aria-label="Object base|Member offset|Member pointer" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="43" fill="#0c4a6e" font-size="12">Object base</text><rect x="234" y="8" width="212" height="62" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="43" fill="#0c4a6e" font-size="12">Member offset</text><rect x="458" y="8" width="212" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="43" fill="#0c4a6e" font-size="12">Member pointer</text></svg></div>

**How it works**

1. Compute the member offset at compile time.
2. Subtract it from the member address.
3. Interpret the result as the original structure type.

**Example**

```c
#include <stddef.h>
struct node { int id; int link; };
struct node n = {1,0};
// Typical flat-address implementation, e.g. Linux:
struct node *owner = (struct node *)((char *)&n.link - offsetof(struct node, link));
```

**Interview takeaway:** Use the kernel's container_of macro in Linux. The pointer must belong to the actual enclosing object; strict portability has additional constraints.

### How do you allocate a 64-byte-aligned buffer without malloc? {M}
**Short answer:** Use an explicit alignment specifier on statically or automatically allocated storage instead of heap allocation.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 80" width="100%" role="img" aria-label="0x1000: start|0x1040: next boundary|0x1080: next boundary" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="43" fill="#0c4a6e" font-size="12">0x1000: start</text><rect x="234" y="8" width="212" height="62" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="43" fill="#0c4a6e" font-size="12">0x1040: next boundary</text><rect x="458" y="8" width="212" height="62" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="43" fill="#0c4a6e" font-size="12">0x1080: next boundary</text></svg></div>

**How it works**

1. Choose a supported power-of-two alignment.
2. Declare the buffer with _Alignas.
3. Verify address alignment with an unsigned mask.

**Example**

```c
#include <stdint.h>
_Alignas(64) static unsigned char buffer[256];
// ((uintptr_t)buffer & 63u) == 0
```

**Interview takeaway:** Extended alignment is implementation-dependent; DMA also requires mapping and ownership rules.

