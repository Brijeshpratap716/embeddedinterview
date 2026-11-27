---
title: Memory Layout of a C Program on a Microcontroller
tag: Memory
desc: Where .text, .data, .bss, heap and stack live on a Cortex-M, how they get there at boot, and how to read a map file.
date: 2026-11-20
order: 2
---

A microcontroller stores code and constants in flash and writable data in RAM.

## Memory sections

| Section | Content | Location |
|---|---|---|
| .text | Program instructions | Flash |
| .rodata | Read-only data | Flash |
| .data | Initialized writable globals/statics | RAM; initial values in flash |
| .bss | Zero-initialized globals/statics | RAM |
| Heap | Dynamic allocation | RAM |
| Stack | Function frames and local variables | RAM |

```c
#include <stdlib.h>

const int table[] = {1, 2}; // Usually .rodata
int count = 10;             // .data
int buffer[100];            // .bss

void example(void)
{
    static int calls;       // .bss
    int local = 5;          // Stack or register
    int *p = malloc(sizeof *p); // Heap allocation
    free(p);
}
```

## Before main()

CPU loads SP and reset handler from the vector table. Startup code initializes the C runtime by copying .data from flash to RAM and zeroing .bss.

Illustrative C startup loops (symbols supplied by the linker):

```c
#include <stdint.h>
extern uint32_t _sidata, _sdata, _edata, _sbss, _ebss;

void init_memory(void)
{
    uint32_t *src = &_sidata;
    for (uint32_t *dst = &_sdata; dst < &_edata;)
        *dst++ = *src++;

    for (uint32_t *dst = &_sbss; dst < &_ebss;)
        *dst++ = 0;
}
```

Hardware initialization and constructors run as required before main(); exact order is platform-dependent.

Heap often grows up and stack down; overflow may corrupt RAM. Use stack guards and high-water marks. Check section sizes with arm-none-eabi-size and the linker map.
