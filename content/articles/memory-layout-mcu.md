---
title: Memory Layout of a C Program on a Microcontroller
tag: Memory
desc: Where .text, .data, .bss, heap and stack live on a Cortex-M, how they get there at boot, and how to read a map file.
date: 2026-11-20
order: 2
---
"Draw the memory layout of a C program" is a standard question. On a desktop the textbook picture is enough. On a microcontroller, interviewers expect you to explain flash versus RAM and what happens before `main()`.

## Two kinds of memory

A typical Cortex-M has **flash** (non-volatile, executable, slow to write, e.g. at `0x08000000` on STM32) and **SRAM** (volatile, read/write, e.g. at `0x20000000`). The linker script describes both:

```ld
MEMORY
{
    FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 512K
    RAM   (rwx) : ORIGIN = 0x20000000, LENGTH = 128K
}
```

## The sections and where they go

| Section | Contents | Stored in | Lives at run time in |
|---|---|---|---|
| `.isr_vector` | Vector table | Flash | Flash |
| `.text` | Code | Flash | Flash |
| `.rodata` | `const` data, string literals | Flash | Flash |
| `.data` | Initialised globals and statics | Flash (initial values) | RAM |
| `.bss` | Zero / uninitialised globals and statics | Nothing (just a size) | RAM |
| Heap | `malloc` memory | – | RAM, above `.bss` |
| Stack | Locals, return addresses | – | RAM, top end, grows down |

Take this code:

```c
const uint16_t table[4] = { 1, 2, 3, 4 };   /* .rodata  (flash)          */
uint32_t counter = 10;                       /* .data    (flash + RAM)    */
uint8_t  rx_buf[256];                        /* .bss     (RAM only)       */

void f(void)
{
    static int calls;                        /* .bss                      */
    int local = 5;                           /* stack                     */
    char *msg = "hi";                        /* msg on stack, "hi" in .rodata */
}
```

The interesting one is `counter`. Its initial value 10 must survive power-off, so it is stored in flash, but the variable must be writable, so it lives in RAM. That needs a copy at boot.

## What happens between reset and main()

1. The core reads the **initial stack pointer** from address 0 of the vector table and the **reset handler** address from address 4.
2. The reset handler copies `.data` from its load address in flash (`_sidata`) to its run address in RAM (`_sdata` to `_edata`).
3. It zeroes `.bss` (`_sbss` to `_ebss`).
4. It calls `SystemInit()` (clocks, FPU), runs C++ constructors if any, then calls `main()`.

The linker script tells the linker about the split load and run addresses with `> RAM AT> FLASH`:

```ld
.data :
{
    _sdata = .;
    *(.data*)
    _edata = .;
} > RAM AT> FLASH
_sidata = LOADADDR(.data);
```

You can practise writing this loop in the coding problem *Write the Reset Handler*.

## Heap and stack sharing RAM

After `.data` and `.bss`, the rest of RAM is shared. The heap usually starts at `_end` (the end of `.bss`) and grows up; the main stack starts at `_estack` (the top of RAM) and grows down. Nothing stops them colliding. On an MCU without memory protection, a stack overflow silently overwrites the heap or `.bss` and the bug appears somewhere unrelated.

Defences: reserve a fixed stack size in the linker script and check it at link time, paint the stack and check the high-water mark, put an MPU guard region at the bottom of the stack, or use the stack-limit registers on ARMv8-M.

With an RTOS, each task gets its own stack (usually allocated from the RTOS heap or statically), and interrupts use the main stack.

## Reading the map file

Pass `-Wl,-Map=firmware.map` to the linker. The map file shows every section, its address and size, and which object file contributed each part. Two quick questions it answers:

- **"Why is my flash full?"** Look for the largest `.text` and `.rodata` contributions. Floating-point `printf` and big vendor HAL functions are common culprits.
- **"Why is my RAM full?"** Look at `.bss` and `.data`. A forgotten `const` moves a table from flash into RAM.

`arm-none-eabi-size firmware.elf` gives the summary:

```
   text    data     bss     dec     hex filename
  42816    1120    9344   53280    d020 firmware.elf
```

Flash used is `text + data`; RAM used (excluding heap and stack) is `data + bss`.

## Interview tips

- Say "flash" and "RAM" explicitly; the desktop diagram alone is not enough for a firmware role.
- Mention that `.bss` takes no space in the image, which is why zero-initialising a big buffer is cheaper than initialising it to a non-zero value.
- Explain that string literals are in `.rodata`, which is why writing to them is undefined behaviour and often has no effect on an MCU.
- Mention the stack-heap collision risk and how you would detect it.
