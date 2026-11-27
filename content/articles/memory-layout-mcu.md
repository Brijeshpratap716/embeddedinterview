---
title: Memory Layout of a C Program on a Microcontroller
tag: Memory
desc: Where .text, .data, .bss, heap and stack live on a Cortex-M, how they get there at boot, and how to read a map file.
date: 2026-11-20
order: 2
---

A microcontroller typically stores code and constants in **flash**, and writable variables in **SRAM**.

## Memory sections

| Section | Contents | Runtime location |
|---|---|---|
| .isr_vector | Interrupt vector table | Usually flash |
| .text | Program code | Usually flash |
| .rodata | Constants and string literals | Usually flash |
| .data | Initialised writable globals/statics | RAM (initial values in flash) |
| .bss | Zero-initialised globals/statics | RAM |
| Heap | Dynamic allocation | RAM |
| Stack | Function frames, saved registers, locals | RAM |

```c
const int table[] = {1, 2};  // usually .rodata
int count = 10;             // .data
int buffer[100];            // .bss

void f(void)
{
    static int calls;       // .bss
    int local = 5;          // stack or register
}
```

## Reset to main()

1. CPU loads the initial stack pointer and reset-handler address from the vector table.
2. Startup code initializes hardware and C runtime: copies .data from flash into RAM and clears .bss.
3. Runs constructors if required, then calls main(). Exact ordering of SystemInit() is platform-dependent.

## Linker script

```ld
MEMORY
{
    FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 512K
    RAM   (rwx) : ORIGIN = 0x20000000, LENGTH = 128K
}
.data : {
    _sdata = .;
    *(.data*)
    _edata = .;
} > RAM AT> FLASH
_sidata = LOADADDR(.data);
```

Example STM32 addresses; actual addresses and sizes depend on the device.

## Heap, stack and memory usage

The heap often grows upward and the stack downward. A collision may corrupt memory. Detect overflow using stack high-water marks, MPU guards or stack-limit registers. RTOS tasks normally have separate stacks.

```sh
arm-none-eabi-size firmware.elf
# Linker option: -Wl,-Map=firmware.map
```

Typically flash usage is approximately text + data, and static RAM usage is data + bss. Include extra sections, reserved memory, heap and stacks when calculating actual usage.

**Interview point:** .data needs an initial-value copy from flash; .bss needs zeroing, not stored initial values.
