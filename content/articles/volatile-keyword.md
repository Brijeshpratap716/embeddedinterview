---
title: The volatile Keyword in Embedded C, Explained Properly
tag: Embedded C
desc: What volatile really guarantees, common uses, and the limits of volatile.
date: 2026-11-20
order: 1
---

`volatile` tells the compiler that an access has observable side effects or that a value may change unexpectedly. It prevents required volatile accesses from being eliminated or cached in a register across accesses.

## 1. Flag shared with an ISR

```c
volatile int ready;

void ISR(void)
{
    ready = 1;
}

int main(void)
{
    while (!ready) { }
}
```

Without volatile, the compiler may read ready once and turn the loop into an infinite loop. This example assumes a platform where the flag access is safe and atomic with respect to the ISR.

## 2. Memory-mapped registers

```c
#include <stdint.h>
#define UART_SR (*(volatile uint32_t *)0x40011000u)
#define UART_DR (*(volatile uint32_t *)0x40011004u)
#define TXE (1u << 7)

void send(char c)
{
    while (!(UART_SR & TXE)) { }
    UART_DR = (uint8_t)c;
}
```

Example STM32 register layout; check the actual hardware manual. Volatile ensures each status read and data write occurs as required.

## 3. What volatile does not guarantee

| Limitation | Solution |
|---|---|
| Atomic read-modify-write (counter++) | Critical section or atomics |
| Safe concurrent thread access | Atomics or locks |
| Ordering of ordinary memory operations | Appropriate synchronization/barriers |
| DMA or multicore cache coherency | DMA APIs, cache maintenance and barriers as required |

Volatile is not a substitute for synchronization. It does not itself emit CPU barriers or make DMA buffers coherent. On Linux use MMIO accessors (readl/writel), synchronization and DMA APIs as appropriate.

## 4. const volatile

```c
const volatile uint32_t *status;
```

The pointed-to value may change externally, but this pointer cannot be used to write it. Useful for read-only hardware registers.

**Interview answer:** Volatile preserves required accesses to objects such as MMIO registers and simple ISR flags. It does not provide atomicity, thread safety or hardware memory ordering.
