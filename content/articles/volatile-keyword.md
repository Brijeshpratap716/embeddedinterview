---
title: The volatile Keyword in Embedded C, Explained Properly
tag: Embedded C
desc: What volatile really guarantees, the three places you must use it, and the four things it does not do.
date: 2026-11-20
order: 1
---
`volatile` is the most-asked embedded C keyword and the most misunderstood. Most candidates can say "it stops the compiler optimising the variable". Interviewers then ask what that means and when it is *not* enough. This article gives you both halves.

## What the compiler is allowed to do without volatile

The C standard describes an abstract machine. The compiler only has to produce the same *observable behaviour*, and ordinary memory reads and writes are not observable. So it may:

- keep a variable in a register and never reload it from memory,
- delete a write if it can prove nobody reads the value,
- merge two writes into one, or reorder independent accesses.

Here is the classic failure:

```c
bool data_ready;               /* set by an ISR */

void wait_for_data(void)
{
    while (!data_ready) { }    /* at -O2 this can become: if (!data_ready) for(;;); */
}
```

Nothing inside the loop changes `data_ready`, and the compiler cannot see the ISR, so it reads the flag once. The program hangs only in release builds, which is why this bug survives testing.

## What volatile guarantees

Accessing a `volatile` object is treated as observable behaviour. The compiler must:

1. perform **every read and write** written in the source,
2. perform them **in program order** relative to other volatile accesses,
3. use the access width the type implies, as far as the hardware allows.

Adding `volatile bool data_ready;` fixes the loop: the flag is re-read on every iteration.

## The three places you must use it

**1. Memory-mapped peripheral registers.** Writing the same value twice to a UART data register sends two bytes; reading a status register twice can return two different values. Both are side effects the compiler cannot know about.

```c
#define UART_SR (*(volatile uint32_t *)0x40011000u)
#define UART_DR (*(volatile uint32_t *)0x40011004u)

while (!(UART_SR & TXE)) { }
UART_DR = 'A';
```

**2. Variables shared between an interrupt and the main code.** Flags, counters and ring-buffer indexes all fall into this group.

**3. Memory changed by another bus master.** DMA buffers and shared memory with another core. Here `volatile` is necessary but rarely sufficient, as the next section explains.

A fourth, rarer case: local variables modified between `setjmp` and `longjmp` must be `volatile` to have defined values afterwards.

## What volatile does NOT do

This is where interviews are decided.

**It does not make operations atomic.** `counter++` on a volatile variable is still a load, an add and a store. If an ISR increments the same variable between the load and the store, one increment is lost. Protect it with a critical section, or use an atomic instruction.

**It does not make wide accesses atomic.** A 64-bit volatile on a 32-bit MCU is read with two instructions. An ISR can update it in between, and you read half old, half new.

**It does not order non-volatile accesses.** The compiler may still move ordinary memory operations across a volatile access. If you fill a normal buffer and then set a volatile "ready" flag, the buffer writes can legally be moved after the flag write. Make the buffer volatile too, or add a compiler barrier:

```c
fill(buffer);
__asm volatile("" ::: "memory");   /* compiler barrier */
ready = true;
```

**It does not emit hardware memory barriers.** On cores that reorder memory operations (Cortex-A, Cortex-M7 with its write buffer, any multi-core system), the CPU itself can reorder accesses. You need `__DMB()`/`__DSB()` on ARM, C11 atomics with acquire/release ordering, or the Linux kernel's `smp_wmb()`/`smp_rmb()`.

## volatile and threads

In hosted C and C++, `volatile` is **not** a synchronisation tool between threads. Use `<stdatomic.h>` or `std::atomic`, mutexes, or your RTOS primitives. They provide atomicity and ordering, and the compiler understands them. The Linux kernel discourages `volatile` in driver code for the same reason (see `Documentation/process/volatile-considered-harmful.rst`): proper locking or `READ_ONCE()`/`WRITE_ONCE()` say what you mean.

## const volatile

Both qualifiers together are legal and useful. `const` says *this code* may not write the object; `volatile` says it may change anyway. A read-only status register or a value written by DMA that the CPU only reads are typical examples.

## A model interview answer

> "`volatile` tells the compiler that an object can change, or that accessing it has side effects, outside what it can see, so every access in the source must really happen, in order. I use it for hardware registers, for flags shared with ISRs, and for memory touched by DMA. It does not make read-modify-write operations atomic and it does not add memory barriers, so for shared counters I add a critical section, and on multi-core or cached systems I use atomics or explicit barriers."

That answer covers the definition, the use cases and the limits in under 30 seconds. It is usually enough to move the interviewer on to the next question.
