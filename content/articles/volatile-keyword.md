---
title: The volatile Keyword in Embedded C, Explained Properly
tag: Embedded C
desc: What volatile really guarantees, common uses, and the limits of volatile.
date: 2026-11-20
order: 1
---

`volatile` tells the compiler that accesses to an object have observable side effects or its value may change unexpectedly. It must preserve required volatile reads and writes.

## 1. Without volatile: compiler can optimize loads

```c
int flag = 0;

void wait(void)
{
    while (flag == 0) { }
}
```

The compiler may load flag only once into a CPU register, then repeatedly check that register instead of reloading memory. If an ISR sets flag to 1, the loop may never exit.

## 2. With volatile: load every time

```c
volatile int flag = 0;

void ISR(void)
{
    flag = 1;             // Store
}

void wait(void)
{
    while (flag == 0) { } // Load on each iteration
}
```

On ARM, a load typically uses LDR (memory to CPU register) and a store uses STR (CPU register to memory). With volatile, the compiler must preserve each required access rather than reuse an old register value.

## 3. Load and store example

```c
volatile unsigned int x;
unsigned int read_twice(void)
{
    unsigned int a = x;   // Load x (LDR)
    unsigned int b = x;   // Load x again (LDR)
    return a + b;
}

void write_twice(void)
{
    x = 10;      // Store 10 (STR)
    x = 20;      // Store 20 (STR)
}
```

Both reads and both writes must occur. Without volatile, the compiler may combine the two reads or remove the first write if it can prove doing so preserves observable behavior. This is conceptual ARM behavior; exact instructions depend on the compiler and target.

Volatile does **not** bypass the CPU cache or guarantee every access reaches DRAM.

## 4. Why volatile is not atomic

```c
volatile int count;
void increment(void)
{
    count++; // Load -> Add -> Store
}
```

Suppose count = 5. Main loads 5; an ISR increments count to 6; main resumes, adds 1 to its old value and stores 6. One increment is lost; the expected result was 7.

For threads, use C11 atomics:

```c
#include <stdatomic.h>
atomic_int count = 0;
void increment(void)
{
    atomic_fetch_add(&count, 1);
}
```

For an ISR, use a suitable critical section or an ISR-safe lock-free atomic operation.

## 5. Memory-mapped registers

```c
#include <stdint.h>
#define UART_SR (*(volatile uint32_t *)0x40011000u)
#define UART_DR (*(volatile uint32_t *)0x40011004u)

void send(void)
{
    while (!(UART_SR & (1u << 7))) { } // Repeated load
    UART_DR = 'A';                     // Store
}
```

Example STM32 register addresses; check the actual device manual. Without volatile, the compiler may optimize required hardware accesses.

## 6. const volatile and limitations

```c
const volatile uint32_t *status;
```

The value can change externally, but this pointer cannot be used to modify it.

Volatile is useful for MMIO and simple ISR flags (when access is safe). It does not guarantee atomicity, thread safety, memory barriers or DMA cache coherency. Use atomics, locks, barriers or DMA/cache APIs as appropriate.

**Interview answer:** Volatile prevents the compiler from eliminating required loads/stores. It does not prevent CPU reordering or make read-modify-write operations atomic.
