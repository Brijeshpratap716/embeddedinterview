---
title: Embedded Interview Roadmap
desc: A step-by-step study plan for embedded software, firmware and Linux driver interviews.
---
Follow the phases in order. Each phase links to the topic pages, practice problems and articles you need. Mark questions as done as you go, and the topic cards on the home page will show your progress.

> **Short on time?** Do Phase 1 and Phase 2 completely, the protocol comparison in Phase 4, and then jump to the phase that matches the job description.

## Phase 1 — C foundations (week 1)
- [C Programming](../topics/c-programming/): storage classes, macros, undefined behaviour, integer promotion.
- [Pointers & Memory](../topics/pointers-memory/): pointer arithmetic, memory layout, alignment, endianness.
- [Bit Manipulation](../topics/bit-manipulation/): masks, shifts, counting bits.
- Practice: [Set, Clear, Toggle a Bit](../problems/set-clear-toggle-bits/), [Count Set Bits](../problems/count-set-bits/), [Safe String Copy](../problems/safe-string-copy/), [Implement memmove](../problems/implement-memmove/).
- Read: [Memory Layout of a C Program on a Microcontroller](../articles/memory-layout-mcu/).

## Phase 2 — Embedded C and the microcontroller (week 2)
- [Embedded C](../topics/embedded-c/): volatile, ISRs, critical sections, start-up code, linker scripts.
- [Microcontrollers & ARM Cortex-M](../topics/microcontrollers-arm/): NVIC, exceptions, faults, timers, ADC, DMA, low power.
- Practice: [Register Field](../problems/register-field/), [Wrap-Safe Timeout](../problems/wrap-safe-timeout/), [Debounce](../problems/debounce-button/), [Reset Handler](../problems/reset-handler/), [HardFault Handler](../problems/hardfault-handler/).
- Read: [The volatile Keyword](../articles/volatile-keyword/), [Interrupt Latency](../articles/interrupt-latency/).

## Phase 3 — Concurrency and real time (week 3)
- [RTOS & Real-Time Systems](../topics/rtos/): scheduling, mutexes vs semaphores, priority inversion, deadlock.
- [Operating System Concepts](../topics/operating-systems/): processes, threads, virtual memory, IPC.
- Practice: [Lock-Free Ring Buffer](../problems/ring-buffer/), [Fixed-Block Memory Pool](../problems/memory-pool/).

## Phase 4 — Interfaces and hardware (week 4)
- [Communication Protocols](../topics/communication-protocols/): UART, SPI, I2C, CAN, USB, Ethernet.
- [Electronics & Hardware Basics](../topics/electronics-hardware/): pull-ups, level shifting, filters, power.
- Practice: [Bit-Banged SPI](../problems/bitbang-spi/), [CRC-16](../problems/crc16-ccitt/), [UART Packet Parser](../problems/frame-parser/), [NMEA Checksum](../problems/nmea-checksum/).
- Read: [UART vs SPI vs I2C vs CAN](../articles/uart-spi-i2c-can/).

## Phase 5 — Linux kernel and embedded Linux (week 5, for BSP/driver roles)
- [Linux Kernel & Device Drivers](../topics/linux-device-drivers/): modules, char drivers, device model, device tree, locking, DMA, DRM.
- [Embedded Linux & Boot](../topics/embedded-linux/): U-Boot, Yocto/Buildroot, filesystems, OTA, secure boot.
- Read: [Writing Your First Linux Character Driver](../articles/linux-char-driver/).

## Phase 6 — Polish (week 6)
- [Data Structures & Algorithms](../topics/data-structures/) and [C++ for Embedded](../topics/cpp-embedded/).
- [Debugging, Testing & Tools](../topics/debugging-testing/): prepare two real bug stories.
- Finish every [practice problem](../problems/) without looking at the solution, then take the [quiz](../quiz/) until you score 8/10 in every category.
- Read: [How to Prepare for an Embedded Software Interview](../articles/embedded-interview-roadmap/).
