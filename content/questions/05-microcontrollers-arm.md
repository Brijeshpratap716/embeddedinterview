---
slug: microcontrollers-arm
title: Microcontrollers & ARM Cortex-M
icon: 🔌
level: Intermediate
order: 5
desc: Cortex-M architecture, NVIC, exceptions, fault handling, clocks, GPIO, timers, ADC, DMA and low-power modes.
---
Most firmware jobs today mean ARM Cortex-M. These questions test whether you understand the core and the peripherals beyond the vendor HAL.

### What is the difference between a microcontroller and a microprocessor? {E}
A **microcontroller (MCU)** puts the CPU, flash, RAM and peripherals (timers, UART, ADC, GPIO) on one chip. It is designed for a dedicated control task, low power and low cost, and usually runs bare metal or an RTOS. A **microprocessor (MPU)** is mainly a CPU, often with an MMU and caches, that relies on external DRAM and storage and typically runs a full OS such as Linux. Examples: STM32F4 (MCU, Cortex-M4) vs i.MX8 or a Qualcomm Snapdragon (MPU/SoC, Cortex-A).

### What is the difference between Harvard and von Neumann architecture? {E}
- **Von Neumann**: one memory and one bus for both instructions and data. Simpler, but instruction fetches and data accesses compete for the bus.
- **Harvard**: separate memories/buses for instructions and data, so both can happen in the same cycle.

Cortex-M3/M4 are a **modified Harvard** design: separate I-code, D-code and system buses, but a single unified address map, so code can still run from RAM and data can still be read from flash. The 8051 and AVR are classic Harvard designs with separate address spaces.

### What are the Cortex-M profiles and how do they differ? {E}
| Core | Architecture | Notable features |
|---|---|---|
| M0 / M0+ | ARMv6-M | Smallest, Thumb subset, no unaligned access, no divide instruction |
| M3 | ARMv7-M | Thumb-2, hardware divide, bit-banding, MPU optional |
| M4 | ARMv7E-M | M3 + DSP/SIMD instructions, optional single-precision FPU |
| M7 | ARMv7E-M | 6-stage superscalar, caches, TCM, optional double-precision FPU |
| M23 / M33 | ARMv8-M | TrustZone security, stack limit registers; M33 has DSP and FPU |
| M55 / M85 | ARMv8.1-M | Helium vector extension (MVE) for ML and DSP |

### What are the Cortex-M core registers? {M}
- `R0`–`R12`: general purpose (`R0`–`R3` carry arguments and return values in the AAPCS calling convention).
- `R13` (SP): stack pointer, banked as **MSP** (main) and **PSP** (process).
- `R14` (LR): link register, holds the return address or, inside an exception, an `EXC_RETURN` code.
- `R15` (PC): program counter.
- `xPSR`: flags, exception number, Thumb state.
- Special: `PRIMASK`, `FAULTMASK`, `BASEPRI` (interrupt masking) and `CONTROL` (privilege level and which stack is active).

### What are MSP and PSP and why are there two stack pointers? {M}
The **Main Stack Pointer** is used after reset, by all exception handlers and by bare-metal code. The **Process Stack Pointer** is used by threads in Thread mode when `CONTROL.SPSEL = 1`. An RTOS gives each task its own stack through PSP, while interrupts always run on the single main stack. This means each task stack does not need to reserve space for the deepest interrupt nesting, and a corrupted task stack does not break the ISR stack.

### What happens in hardware when an exception is taken on Cortex-M? {M}
1. The core pushes an 8-word **stack frame**: `R0`–`R3`, `R12`, `LR`, `PC`, `xPSR` (plus 18 words of FPU state if the FPU is active and lazy stacking is not deferring it).
2. It fetches the handler address from the vector table, in parallel with stacking.
3. `LR` is loaded with an `EXC_RETURN` value (e.g. `0xFFFFFFF9`) that encodes which stack and mode to return to.
4. The core switches to Handler mode on MSP and runs the handler.
5. When the handler does `BX LR` with an `EXC_RETURN` value, the hardware unstacks and resumes.

Because the hardware saves the caller-saved registers, ISRs can be written as normal C functions.

### What is the NVIC? {E}
The **Nested Vectored Interrupt Controller** is part of the Cortex-M core. It:

- enables/disables each external interrupt (`NVIC_EnableIRQ`),
- holds pending state (`NVIC_SetPendingIRQ`),
- assigns programmable priorities (typically 3–8 implemented bits),
- supports **nesting**: a higher-priority interrupt pre-empts a lower one,
- fetches the handler address directly from the vector table ("vectored").

It also implements **tail-chaining** and **late arrival** to cut latency.

### What are tail-chaining and late arrival? {H}
- **Tail-chaining**: if another interrupt is pending when an ISR finishes, the core skips unstacking and re-stacking and jumps straight to the next handler (6 cycles instead of about 24 on M3/M4).
- **Late arrival**: if a higher-priority interrupt arrives while the core is still stacking for a lower one, the core uses the same stack frame and runs the higher-priority handler first.

Both are automatic; they are why Cortex-M interrupt overhead is low.

### How do interrupt priorities work on Cortex-M? Lower number means? {M}
A **lower number is a higher priority**. Reset (-3), NMI (-2) and HardFault (-1) have fixed, highest priorities. The priority byte can be split into a **group (pre-emption) priority** and a **sub-priority** with `NVIC_SetPriorityGrouping`. Only the group priority decides pre-emption; the sub-priority only orders pending interrupts of equal group priority. Implemented bits are the top bits of the byte, so on a part with 4 bits, priority 5 is written as `5 << 4`. CMSIS `NVIC_SetPriority` handles the shift.

### What is the difference between PRIMASK, FAULTMASK and BASEPRI? {H}
- `PRIMASK = 1` masks all configurable-priority exceptions (everything except NMI and HardFault). `__disable_irq()` sets it.
- `FAULTMASK = 1` also masks HardFault. Only usable by fault handlers, and cleared automatically on exception return.
- `BASEPRI = n` masks only exceptions whose priority value is ≥ `n`, so more urgent interrupts still run. FreeRTOS uses it for critical sections (`configMAX_SYSCALL_INTERRUPT_PRIORITY`).

`BASEPRI` does not exist on ARMv6-M (Cortex-M0/M0+).

### What causes a HardFault and how do you debug one? {M}
Common causes: invalid memory access (NULL or wild pointer), stack overflow, unaligned `LDM`/`STRD`, executing from a non-executable address, calling a function pointer without the Thumb bit set, divide by zero (if trapping is enabled), or an escalated MemManage/BusFault/UsageFault.

Debugging steps:
1. Write a HardFault handler that captures the stacked frame (check bit 2 of `LR` to pick MSP or PSP).
2. Read the stacked **PC** (the faulting instruction) and **LR** (the caller) and look them up in the `.map` file or with `addr2line`.
3. Read `SCB->CFSR` (which fault and why), `HFSR`, and `MMFAR`/`BFAR` (the faulting address, if valid).
4. Note **imprecise** bus faults: the stacked PC is after the faulting instruction. Temporarily set `DISDEFWBUF` in `ACTLR` to make them precise.

See the coding problem *HardFault handler that captures the stack frame*.

### What are SVC and PendSV used for? {H}
- **SVC** (supervisor call): a software-triggered exception from the `SVC #n` instruction. Unprivileged code uses it to request privileged services, and RTOSes use it to start the first task.
- **PendSV**: a pendable exception set by writing `SCB->ICSR`. It is configured at the **lowest priority**, so it runs only after all other ISRs have finished. RTOSes do the **context switch** in PendSV so a switch never happens in the middle of a nested ISR.
- **SysTick** generates the RTOS tick and typically pends PendSV when a switch is needed.

### What is the MPU and how is it used? {M}
The Memory Protection Unit defines a small number of regions (8 or 16 typically) with access permissions (read/write/execute, privileged/unprivileged) and memory attributes (cacheable, shareable). A violation raises a MemManage fault. Uses:

- Catch stack overflows with a guard region.
- Mark RAM non-executable (stops code injection) and flash read-only.
- Isolate RTOS tasks (FreeRTOS-MPU, Zephyr userspace).
- Mark DMA buffers non-cacheable on Cortex-M7.

On ARMv7-M, region sizes must be a power of two and aligned to their size; ARMv8-M uses base/limit pairs with 32-byte granularity.

### What is TrustZone for Cortex-M? {H}
ARMv8-M TrustZone splits the system into **Secure** and **Non-secure** worlds. Memory regions, peripherals and interrupts are assigned to one world via the SAU/IDAU. Non-secure code can call into secure code only through **non-secure callable** entry points (`SG` instruction), and the core keeps separate stack pointers, MPU and SysTick per world. It is used to protect keys, secure boot and trusted firmware (TF-M) from bugs in application code.

### How is the system clock configured on an MCU? {M}
Typical sources: an internal RC oscillator (HSI, fast startup but less accurate), an external crystal (HSE, accurate), and a low-speed 32.768 kHz crystal for the RTC. A **PLL** multiplies a source to the core frequency, and prescalers divide it for the AHB/APB buses and peripherals.

Sequence: enable the source and wait for ready, configure flash wait states for the target frequency **before** switching up, configure and lock the PLL, switch the system clock mux, then set bus prescalers. Getting the flash wait states wrong causes random crashes.

### What are the GPIO modes? {E}
- **Input**: floating, pull-up or pull-down.
- **Output**: push-pull (drives both high and low) or open-drain (drives low only, needs a pull-up; used for I2C and wired-OR lines).
- **Alternate function**: the pin is controlled by a peripheral (UART TX, SPI SCK, timer PWM).
- **Analog**: digital buffer disabled, for ADC/DAC; also the lowest-power state for unused pins.

Most parts also configure output **speed/slew rate**. Higher speed increases EMI and power.

### What is the difference between open-drain and push-pull outputs? {E}
A **push-pull** output has two transistors and actively drives the line both high and low, giving fast edges. An **open-drain** output can only pull the line low; when "off" the line floats and an external pull-up resistor brings it high. Open-drain lets several devices share one line without short circuits (I2C, interrupt lines) and lets a device drive a line to a different voltage than its own supply.

### How do timers generate PWM? {M}
A timer counts from 0 to the auto-reload value (ARR) and then restarts. In PWM mode, the output is high while the counter is below the compare value (CCR) and low afterwards.

- Frequency = timer clock / ((PSC + 1) × (ARR + 1))
- Duty cycle = CCR / (ARR + 1)

Example: 72 MHz clock, PSC = 71 gives 1 MHz ticks; ARR = 999 gives 1 kHz PWM; CCR = 250 gives 25% duty. Center-aligned mode counts up and down for symmetric PWM in motor control. Use the preload (shadow) registers so changes take effect at the next period without glitches.

### What is input capture and how do you measure a frequency with it? {M}
Input capture latches the timer counter value into a register on an edge of an input pin. Capture two consecutive rising edges; the period in ticks is `(c2 - c1)` using unsigned arithmetic (handles a single counter wrap). Frequency = timer clock / period. For low frequencies, count overflows too; for high frequencies, use the external clock (counter) mode and count edges in a fixed gate time.

### How does an ADC work and what are its key parameters? {M}
Most MCU ADCs are **successive approximation (SAR)** converters: a sample-and-hold capacitor captures the input, then a DAC and comparator perform a binary search, one bit per clock.

Key parameters:
- **Resolution** (12 bits gives 4096 steps; LSB = Vref / 4096).
- **Sampling time**: must be long enough to charge the sampling capacitor through the source impedance, or readings are low.
- **Conversion rate**, **reference voltage** and its noise.
- **INL/DNL**, offset and gain error, ENOB.

For several channels use scan mode with DMA. Oversampling and averaging improve effective resolution for slow signals.

### What is DMA and how is it configured? {M}
A Direct Memory Access controller moves data between peripherals and memory without the CPU. Configuration: source and destination addresses, transfer size and width, increment mode for each side, direction, priority, normal or **circular** mode, and the request line (which peripheral triggers each transfer). Interrupts fire at half-transfer, transfer-complete and error.

Circular mode with half/complete interrupts gives **double buffering**: the CPU processes one half while DMA fills the other. Watch out for cache coherency on Cortex-M7 and for buffers that go out of scope while DMA is still writing.

### What low-power modes do MCUs have? {M}
Names vary by vendor, but generally:

- **Sleep**: CPU clock stopped (`WFI`/`WFE`), peripherals run, any interrupt wakes it. Fast wake-up.
- **Stop / Deep sleep**: most clocks stopped, RAM and registers retained, wake from EXTI, RTC or some peripherals. Microsecond wake-up; clocks must be reconfigured afterwards.
- **Standby / Shutdown**: almost everything off, RAM lost (except backup domain), wake from a few pins or the RTC, and the MCU restarts from reset.

Tips: put unused pins in analog mode, disable peripheral clocks, use `SLEEPONEXIT` for interrupt-driven designs, and measure with a power analyser, since one floating pin can cost more than the core.

### What is the difference between WFI and WFE? {H}
- `WFI` (wait for interrupt) sleeps until an interrupt (or debug event) occurs.
- `WFE` (wait for event) sleeps until an **event**: an interrupt, an `SEV` instruction from another core, or a pending event latch that was already set. If the event latch is already set, `WFE` clears it and returns immediately.

`WFE` is used in spinlocks on multi-core systems and with `SEVONPEND`. `WFI` is the usual choice for idle loops.

### What is the difference between flash and EEPROM, and what is wear levelling? {M}
Flash is erased in large **sectors/pages** (KBs) and can only change bits from 1 to 0 when writing; you must erase a whole sector to set bits back to 1. EEPROM can usually be written byte by byte. Both have limited **endurance** (typically 10k cycles for MCU flash, 100k–1M for EEPROM).

**Wear levelling** spreads writes over many locations, for example by writing records sequentially through a log and erasing only when a sector is full, so no single cell wears out first. Many MCUs emulate EEPROM in two flash sectors this way.

### What is an RTC and how is backup domain power used? {E}
A Real-Time Clock counts seconds from a 32.768 kHz crystal (2^15 Hz, so a 15-bit divider gives exactly 1 Hz). It sits in a backup domain powered from `VBAT` (coin cell or supercap) so it keeps time when main power is off, along with a few backup registers. It also provides alarms and periodic wake-ups from low-power modes.

### What is JTAG and SWD? {E}
Both are debug interfaces. **JTAG** (IEEE 1149.1) uses 4–5 pins (TCK, TMS, TDI, TDO, optional TRST), supports daisy-chaining several devices and boundary scan for board test. **SWD** (Serial Wire Debug) is ARM's 2-pin alternative (SWDIO, SWCLK) with the same debug access to the core and memory. **SWO** adds a trace output pin for ITM `printf` and profiling. Probes: ST-LINK, J-Link, CMSIS-DAP.
