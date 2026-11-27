---
title: The volatile Keyword in Embedded C, Explained Properly
tag: Embedded C
desc: What volatile really guarantees, common uses, and the limits of volatile.
date: 2026-11-20
order: 1
---

`volatile` tells the compiler that the value of a variable may change unexpectedly, outside the normal program flow.

It prevents the compiler from optimizing away required read and write operations on that variable.

## 1. What happens at the assembly level?

**Without volatile:**

```c
int flag = 0;

while (flag == 0);
```

The compiler may load `flag` only once and reuse its value.

ARM assembly (illustrative):

```asm
    LDR R0, [R1]
loop:
    CMP R0, #0
    BEQ loop
```

Even if hardware or an ISR changes `flag`, the loop may never exit because the CPU keeps checking R0.

**With volatile:**

```c
volatile int flag = 0;

while (flag == 0);
```

ARM assembly:

```asm
loop:
    LDR R0, [R1]
    CMP R0, #0
    BEQ loop
```

Now the compiler generates a load on every iteration, so the CPU can observe the updated value.

Similarly, for writes:

```c
volatile int x;

x = 10;
x = 20;
```

ARM assembly:

```asm
MOV R0, #10
STR R0, [R1]

MOV R0, #20
STR R0, [R1]
```

Without `volatile`, the compiler may eliminate the first store because the value is overwritten.

## 2. Where is volatile used and why?

**A. Memory-mapped hardware registers**

```c
#define STATUS (*(volatile unsigned int *)0x40000000)

while (!(STATUS & 1));
```

Hardware can update the status register independently of the CPU. Therefore, every polling iteration must perform a fresh read.

**B. Variables shared between ISR and main code**

```c
volatile int flag = 0;

void ISR(void)
{
    flag = 1;
}

int main(void)
{
    while (!flag);
    return 0;
}
```

The ISR changes `flag` asynchronously, so the compiler must not eliminate repeated reads.

**C. Hardware read-only registers**

```c
const volatile unsigned int *status =
    (const volatile unsigned int *)0x40000000;
```

- `const`: Software cannot modify the register through this pointer.
- `volatile`: Hardware can modify the register.

**D. Memory modified by DMA**

```c
volatile unsigned int dma_done;

while (!dma_done);
```

If DMA hardware updates this memory location, repeated reads are required. However, cache coherency and memory ordering must be handled separately.

## 3. What volatile does NOT guarantee

| Property | Guaranteed? |
|---|---|
| Prevent elimination of required loads (`LDR`) | Yes |
| Prevent elimination of required stores (`STR`) | Yes |
| Atomicity | No |
| Thread safety | No |
| Cache coherency | No |
| Memory barriers | No |
| Direct DRAM access | No |

For example:

```c
volatile int count = 0;
count++;
```

ARM assembly:

```asm
LDR R0, [R1]
ADD R0, R0, #1
STR R0, [R1]
```

An interrupt or another CPU core can interfere between these instructions. Therefore, `volatile` does not make an operation atomic.

## 4. What does the interviewer want to hear?

**Volatile is a compiler-level qualifier that prevents the compiler from eliminating required memory accesses or reusing a previously loaded register value instead of performing a required read. On ARM, this typically results in LDR and STR instructions for the respective reads and writes. It is primarily used for memory-mapped hardware registers, ISR-shared variables and hardware-modified memory. However, it does not guarantee atomicity, thread safety, memory ordering or cache coherency.**

**Important:** `volatile` controls compiler optimization, not CPU caching. A volatile load can still be served from the CPU cache, depending on the memory attributes.
