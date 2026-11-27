---
slug: microcontrollers-arm
title: Microcontrollers & ARM Cortex-M
icon: 🔌
level: Intermediate
order: 5
desc: Arm architecture (RISC, Cortex-M vs A vs R, Cortex-A53), the Cortex-M core, NVIC, faults, MPU, TrustZone, caches, clocks, GPIO, timers, ADC/DAC, DMA, low power and debug.
---
Most firmware jobs today mean Arm. These questions test whether you understand the core and the peripherals beyond the vendor HAL, plus the Cortex-A side that matters for Linux and multi-core SoCs (several are based on the topics of Arm's *Operating Systems Foundations* textbook, answered in our own words). Each answer gives the short version first, then the explanation and follow-ups.

### What is the difference between a microcontroller and a microprocessor? {E}
**Short answer:** A **microcontroller (MCU)** integrates the CPU, flash, RAM and peripherals (timers, UART, SPI, I2C, ADC, GPIO) on one chip, designed for a dedicated control task with low cost and low power; it usually runs bare metal or an RTOS. A **microprocessor** (or application processor / SoC) is built around a more powerful CPU with an MMU and caches, uses external DRAM and storage, and typically runs a full OS such as Linux or Android.

| | Microcontroller | Microprocessor / application SoC |
|---|---|---|
| Example cores | Cortex-M0+/M4/M7/M33, RISC-V RV32 | Cortex-A53/A55/A72, x86 |
| Memory | on-chip flash (KB–few MB) and SRAM (KB–1 MB) | external DRAM (hundreds of MB–GB), eMMC/UFS |
| MMU | no (MPU at most) | yes |
| Typical OS | none, FreeRTOS, Zephyr | Linux, Android, QNX |
| Clock | tens to hundreds of MHz | 1–3 GHz, multi-core |
| Power | µA in sleep, mA active | hundreds of mA to watts |
| Boot time | microseconds to milliseconds | seconds |
| Real-time behaviour | deterministic | needs special care (PREEMPT_RT) |
| Cost | cents to a few dollars | several dollars upward, plus DRAM, PMIC |

**Examples:** STM32F4 (Cortex-M4 MCU), nRF52840 (Cortex-M4 with Bluetooth), i.MX 8M (Cortex-A53 SoC), Raspberry Pi's BCM2711 (Cortex-A72).

**The line is blurring:** many SoCs combine both, e.g. i.MX 8M Plus or STM32MP1 have Cortex-A cores for Linux plus a Cortex-M core for real-time I/O, and high-end MCUs (Cortex-M7 at 600 MHz–1 GHz, Cortex-M85) approach small application processors.

**How to choose in an interview answer:** an MCU for hard real-time control, battery operation, instant start and low cost; an application processor when you need rich UI, networking stacks, large memory, Linux software and processing power.

### What is the difference between Harvard and von Neumann architecture? {E}
**Short answer:** In a **von Neumann** architecture, instructions and data share one memory and one bus, so an instruction fetch and a data access cannot happen at the same time. In a **Harvard** architecture, instructions and data have separate memories and buses, so both can happen in the same cycle. Most modern cores, including Cortex-M3/M4/M7 and Cortex-A, are **modified Harvard**: separate instruction and data buses or caches, but one unified address space.

| | Von Neumann | Harvard | Modified Harvard |
|---|---|---|---|
| Buses | one shared | separate instruction and data | separate paths/caches, single address map |
| Can execute from RAM / read constants from flash | yes | not directly (separate spaces) | yes |
| Examples | Cortex-M0/M0+ (single AHB-Lite bus), original 8086 | 8051, AVR, PIC, many DSPs | Cortex-M3/M4/M7, Cortex-A (split L1 I/D caches) |

**Cortex-M3/M4 bus details:** an **I-code** bus fetches instructions from the code region (flash), a **D-code** bus reads literal data from the code region, and a **System** bus accesses SRAM and peripherals. Code can still run from SRAM (via the System bus, typically slower) and data can still be read from flash, because all buses share one 4 GB address map.

**Practical consequences**

- On classic Harvard MCUs like AVR, a constant table in flash needs special access (`PROGMEM`, `pgm_read_byte`), because a normal pointer points into RAM. On Arm this is unnecessary: `const` data in flash is read with normal pointers.
- On Cortex-M7, putting code in ITCM and data in DTCM gives the full Harvard benefit (single-cycle, parallel access).
- Self-modifying code or loading code into RAM on a modified Harvard core with caches needs cache maintenance (clean D-cache, invalidate I-cache) because the two paths are separate.

### What is RISC, how does it differ from CISC, and why did Arm succeed? {E}
**Short answer:** **RISC** (Reduced Instruction Set Computer) uses a small set of simple, fixed-length instructions, each doing one thing, with memory accessed only by explicit load and store instructions and many general-purpose registers. **CISC** (Complex Instruction Set Computer, e.g. x86) has many variable-length instructions, some doing a lot of work and operating directly on memory. RISC makes the hardware simpler, easier to pipeline and more power-efficient, which is why Arm became dominant in phones and embedded systems.

| | RISC (Arm, RISC-V) | CISC (x86) |
|---|---|---|
| Instruction length | fixed (32-bit A64; 16/32-bit Thumb-2) | variable (1–15 bytes on x86) |
| Memory access | only load/store instructions | most instructions can use memory operands |
| Registers | many (16 in AArch32, 31 in AArch64) | fewer architectural registers historically |
| Decode | simple, cheap | complex; modern x86 decodes into internal RISC-like micro-ops |
| Code density | lower (helped by Thumb, compressed RISC-V) | higher |
| Power/area | lower | higher |

**Why it mattered for Arm:** Arm's original 1985 design (from Acorn, for the BBC Micro's successor) aimed to bring workstation-class performance to low-cost machines, often summarised as "MIPS for the masses" (MIPS here meaning millions of instructions per second). The simple RISC design needed few transistors, which turned out to make it very power efficient, almost as a side effect. When mobile and battery-powered devices took off, low power per instruction became the most valuable property, and Arm's licensing model (selling designs, not chips) let many companies build Arm SoCs.

**Modern reality:** the distinction has blurred: x86 cores internally execute RISC-like micro-operations, and Arm added complex instructions (SIMD, crypto, atomics). Energy efficiency now depends more on microarchitecture than on the instruction set label, but the clean load/store design still makes Arm cores smaller and simpler, which matters most at the low end (Cortex-M).

**Follow-up:** "What is Thumb?" A compressed instruction set with 16-bit encodings (Thumb-2 mixes 16- and 32-bit) for better code density; Cortex-M executes only Thumb.

### What are the Cortex-M profiles and how do they differ? {E}
**Short answer:** Arm's microcontroller cores range from the tiny, low-power Cortex-M0/M0+ (Armv6-M) through the mainstream Cortex-M3/M4 (Armv7-M, M4 adding DSP and an FPU) and the high-performance Cortex-M7 (caches, TCM, superscalar), to the Armv8-M cores Cortex-M23/M33 (TrustZone security) and Cortex-M55/M85 (Helium vector extension for DSP and machine learning).

| Core | Architecture | Pipeline | Notable features | Typical use |
|---|---|---|---|---|
| M0 / M0+ | Armv6-M | 3 / 2 stages | smallest, Thumb subset, no hardware divide, no unaligned access, optional MPU (M0+) | sensors, simple control, battery devices |
| M3 | Armv7-M | 3 | Thumb-2, hardware divide, bit-banding, optional MPU | general-purpose control |
| M4 | Armv7E-M | 3 | M3 + DSP/SIMD instructions, optional single-precision FPU | motor control, audio, sensor fusion |
| M7 | Armv7E-M | 6, dual-issue | I/D caches, TCM, optional double-precision FPU | high-performance control, graphics, audio |
| M23 | Armv8-M Baseline | 2 | TrustZone, stack limit (secure), small | secure IoT endpoints |
| M33 / M35P | Armv8-M Mainline | 3 | TrustZone, DSP, FPU, stack limit registers, M35P adds physical tamper resistance | secure IoT, wearables |
| M52 / M55 / M85 | Armv8.1-M | 4–7 | Helium (MVE) vector instructions, optional caches/TCM, PACBTI (M85) | ML at the edge, DSP |

**Common to all Cortex-M:** Thumb instruction set only, the NVIC, the same exception model, SysTick, a 4 GB memory map with standard regions, and C-friendly interrupt handling.

**Related families:** **Cortex-R** (R5, R52, R82) for real-time safety systems (disk/SSD controllers, automotive ECUs, 5G modems) with TCM, ECC and lock-step options; **Cortex-A** for Linux/Android application processors.

**Choosing:** the core is rarely the deciding factor alone; peripherals, memory, power modes, price, toolchain and vendor ecosystem usually decide which MCU you use.

### What are the differences between Cortex-M, Cortex-R and Cortex-A, and why can't a Cortex-M0+ run Linux? {M}
**Short answer:** **Cortex-A** cores are application processors with an MMU, caches and high clock speeds, designed to run Linux or Android. **Cortex-R** cores target real-time processing, often with an MPU and tightly coupled memory; some models also support an MMU. **Cortex-M** cores are microcontroller cores optimised for low cost, low power and simple, fast interrupt handling. A Cortex-M0+ is not a supported normal Linux target: it lacks the required architectural features and typical systems have far too little memory. Linux also has no-MMU configurations for suitable supported processors, so absence of an MMU alone does not rule out Linux on every CPU.

| | Cortex-M | Cortex-R | Cortex-A |
|---|---|---|---|
| Memory protection | MPU (optional) | MPU (R52 has two stages; R82 has an optional MMU) | MMU with virtual memory |
| Instruction sets | Thumb only | Arm + Thumb (AArch32); R82 AArch64 | AArch64 + AArch32 (A32/T32) |
| Interrupt controller | NVIC (in the core) | GIC | GIC |
| Typical clock | 10–1000 MHz | 400 MHz–1.6 GHz | 1–3+ GHz |
| Typical memory | on-chip flash/SRAM | TCM + external | external DRAM, large caches |
| Real-time | excellent, deterministic | excellent | weaker (caches, virtual memory, OS) |
| Example uses | MCUs, sensors, IoT | car brake/airbag ECUs, SSD controllers, modems | phones, gateways, infotainment, Raspberry Pi |

**Why the Cortex-M0+ is not suitable for Linux**

- **No MMU:** mainline Linux relies on virtual memory for process isolation, `fork()`, demand paging and memory-mapped files. A no-MMU Linux (uClinux) exists, but it has been dropped or limited on many architectures and still needs megabytes of RAM.
- **Memory:** M0+ chips typically have 8–256 KB of flash and 4–64 KB of RAM. A minimal Linux needs several MB of RAM and storage.
- **Performance:** tens of MHz, no caches, no hardware divide.
- **Limited architectural features:** Armv6-M has only basic privileged/unprivileged modes and an optional, small MPU.

**What a Cortex-M0+ is good for:** simple sensor nodes, battery-powered devices (very low µA/MHz and deep-sleep currents), smart cards, power management controllers, motor drivers, as a co-processor next to a bigger CPU, and anywhere cost per unit is critical (cents per chip).

### What are the Cortex-M core registers? {M}
**Short answer:** Cortex-M has 16 core registers: `R0`–`R12` general purpose, `R13` the stack pointer (banked as MSP and PSP), `R14` the link register, `R15` the program counter, plus the program status register `xPSR` and the special registers `PRIMASK`, `FAULTMASK`, `BASEPRI` (interrupt masking) and `CONTROL` (privilege and stack selection). Cores with an FPU add `S0`–`S31` and `FPSCR`.

| Register | Role |
|---|---|
| R0–R3 | arguments and return values (AAPCS), scratch |
| R4–R11 | callee-saved variables |
| R12 | scratch (IP, intra-procedure call) |
| R13 (SP) | stack pointer: **MSP** (main) or **PSP** (process), selected by mode and `CONTROL.SPSEL` |
| R14 (LR) | return address after `BL`; inside an exception holds an `EXC_RETURN` value (e.g. `0xFFFFFFF9`) |
| R15 (PC) | program counter |
| xPSR | combined APSR (N, Z, C, V, Q flags, GE bits), IPSR (current exception number), EPSR (Thumb bit, IT/ICI state) |
| PRIMASK | 1 = mask all configurable-priority interrupts |
| FAULTMASK | 1 = also mask HardFault (not on v6-M) |
| BASEPRI | mask interrupts at or below a priority (not on v6-M) |
| CONTROL | bit 0 nPRIV (unprivileged thread mode), bit 1 SPSEL (use PSP in thread mode), bit 2 FPCA (FP context active) |
| MSPLIM, PSPLIM | stack limits (Armv8-M) |

**Reading special registers from C (CMSIS):** `__get_IPSR()`, `__get_CONTROL()`, `__set_BASEPRI()`, `__get_MSP()`, `__get_PSP()`.

**Why these matter in interviews**

- The **IPSR** tells you whether code is running in an ISR (non-zero) and which one; RTOS code uses this to choose between normal and `FromISR` APIs.
- **EXC_RETURN in LR** tells a fault handler which stack held the faulting context (bit 2: 0 = MSP, 1 = PSP).
- The **Thumb bit** (EPSR.T) must always be 1 on Cortex-M; branching to an address with bit 0 clear causes a UsageFault (INVSTATE), a classic bug with hand-built function pointers.

### What are MSP and PSP and why are there two stack pointers? {M}
**Short answer:** Cortex-M has two banked stack pointers. The **Main Stack Pointer (MSP)** is used after reset, by all exception handlers, and by bare-metal code. The **Process Stack Pointer (PSP)** can be used by code in Thread mode (when `CONTROL.SPSEL = 1`). An RTOS gives each task its own stack through PSP, while all interrupts run on the single main stack.

**Why two stacks help**

1. **Smaller task stacks:** interrupts never use a task's stack, so each task stack does not need extra space for the worst-case nesting of interrupts (which could be several hundred bytes). With 20 tasks this saves a lot of RAM.
2. **Robustness:** a task that overflows or corrupts its own stack does not break the stack that interrupts and the kernel rely on.
3. **Fast context switches:** the RTOS only saves/restores PSP and the task's registers; handler mode keeps using MSP.
4. **Privilege separation:** combined with unprivileged thread mode and the MPU, tasks cannot touch the kernel's stack.

**How the hardware uses them**

- On exception entry, the core pushes the exception frame onto whichever stack the interrupted code was using (MSP or PSP), then switches to MSP for the handler.
- `LR` gets an `EXC_RETURN` value: `0xFFFFFFF9` return to Thread mode using MSP, `0xFFFFFFFD` return to Thread mode using PSP, `0xFFFFFFF1` return to Handler mode (nested). (Values with FP context differ in bit 4: `0xFFFFFFE9`/`0xFFFFFFED`.)

**How an RTOS starts:** the scheduler sets PSP to the first task's prepared stack and then either sets `CONTROL.SPSEL` and branches, or triggers an SVC whose return uses `EXC_RETURN = 0xFFFFFFFD` to "return" into the first task on PSP.

**Bare-metal code** usually never touches PSP; everything runs on MSP. The initial MSP value comes from the first entry of the vector table.

**Debugging tip:** in a HardFault handler, test bit 2 of `LR` to know which stack holds the faulting frame:

```c
__attribute__((naked)) void HardFault_Handler(void)
{
    __asm volatile(
        "tst lr, #4      \n"
        "ite eq          \n"
        "mrseq r0, msp   \n"
        "mrsne r0, psp   \n"
        "b hard_fault_c  \n");   /* hard_fault_c(uint32_t *frame) reads frame[6] = PC */
}
```

### What happens in hardware when an exception is taken on Cortex-M? {M}
**Short answer:** The core automatically pushes an 8-word stack frame (`R0`–`R3`, `R12`, `LR`, `PC`, `xPSR`) onto the current stack, fetches the handler's address from the vector table at the same time, loads `LR` with a special `EXC_RETURN` value, switches to Handler mode using MSP, and starts the handler. When the handler returns (branching to the `EXC_RETURN` value), the hardware unstacks the registers and resumes the interrupted code. This is why ISRs can be ordinary C functions.

**Step by step**

1. **Stacking:** push `xPSR`, `PC` (return address), `LR`, `R12`, `R3`, `R2`, `R1`, `R0` onto the active stack (MSP or PSP), 8-byte aligned (an extra padding word is added if needed, recorded in xPSR bit 9). If the FPU is active, `S0`–`S15` and `FPSCR` are also stacked (18 more words), unless **lazy stacking** reserves the space and saves them only if the handler uses the FPU.
2. **Vector fetch:** read the handler address from `VTOR + 4 × exception_number`, in parallel with stacking (Harvard buses).
3. **Update registers:** `PC` = handler address, `LR` = `EXC_RETURN`, `IPSR` = exception number, switch to Handler mode (always privileged) on MSP.
4. **Handler runs.** Higher-priority exceptions can pre-empt it (nesting).
5. **Return:** `BX LR` (or `POP {..., PC}`) with an `EXC_RETURN` value tells the core to perform an exception return: unstack, restore mode and stack pointer, continue the interrupted code.

**Timing:** 12 cycles from the interrupt to the first handler instruction on Cortex-M3/M4 (zero wait states), similar on exit, and only 6 cycles between back-to-back handlers with tail-chaining.

**The stacked frame layout (lowest address first)**

| Offset | Register |
|---|---|
| 0x00 | R0 |
| 0x04 | R1 |
| 0x08 | R2 |
| 0x0C | R3 |
| 0x10 | R12 |
| 0x14 | LR (of the interrupted code) |
| 0x18 | PC (return address) |
| 0x1C | xPSR |

Fault handlers read `frame[6]` to find the instruction that faulted.

**What the hardware does not save:** `R4`–`R11` (and `S16`–`S31`). The compiler saves them in the handler if it uses them (AAPCS callee-saved), and an RTOS saves them in software during a context switch.

### What is the NVIC? {E}
**Short answer:** The **Nested Vectored Interrupt Controller** is the interrupt controller built into every Cortex-M core. It enables and disables each external interrupt, records pending interrupts, assigns programmable priorities, lets higher-priority interrupts pre-empt lower ones (nesting), and fetches the handler address directly from the vector table (vectored), with hardware optimisations such as tail-chaining and late arrival.

**What it provides**

- **Enable/disable per IRQ:** `NVIC_EnableIRQ(USART2_IRQn)`, `NVIC_DisableIRQ()` (registers `ISER`/`ICER`).
- **Pending state:** set or clear by software (`NVIC_SetPendingIRQ`, `NVIC_ClearPendingIRQ`), useful for testing or deferring work to a software-triggered interrupt.
- **Active state:** which interrupts are currently running (nesting).
- **Priorities:** 2 bits on Cortex-M0/M0+ (4 levels), typically 3–8 bits on M3/M4/M7/M33 (e.g. 16 levels on STM32), set with `NVIC_SetPriority()`.
- **Priority grouping** into pre-emption priority and sub-priority (not on v6-M).
- **Number of interrupts:** up to 32 on Armv6-M, up to 240 on Armv7-M, up to 480 on Armv8-M Mainline, depending on the chip.

**Typical set-up**

```c
NVIC_SetPriority(USART2_IRQn, 5);     /* CMSIS shifts into the implemented bits */
NVIC_ClearPendingIRQ(USART2_IRQn);    /* drop anything pending from before */
NVIC_EnableIRQ(USART2_IRQn);
USART2->CR1 |= USART_CR1_RXNEIE;      /* and enable the source inside the peripheral */
```

An interrupt reaches the CPU only if it is enabled **both** in the peripheral and in the NVIC (and not masked by `PRIMASK`/`BASEPRI`).

**Level vs pulse interrupts:** most peripheral interrupts are level-sensitive: the line stays asserted until the peripheral's flag is cleared. If the handler does not clear it, the interrupt is taken again immediately after return.

**Related:** system exceptions (SysTick, PendSV, SVC, faults) are configured in the **SCB** (`SCB->SHPR`), not the NVIC. **WIC** (wake-up interrupt controller) lets interrupts wake the core from deep sleep when the NVIC clock is stopped. Cortex-A systems use the **GIC** instead.

### What are tail-chaining and late arrival? {H}
**Short answer:** Both are hardware optimisations in the Cortex-M exception model. **Tail-chaining:** when an interrupt handler finishes and another interrupt is already pending, the core skips the unstacking and re-stacking and goes straight into the next handler (6 cycles instead of about 24 on Cortex-M3/M4). **Late arrival:** if a higher-priority interrupt arrives while the core is still stacking for a lower-priority one, the core uses the same stack frame and runs the higher-priority handler first.

**Tail-chaining timeline**

```
Without:  [ISR A] unstack (12) → stack (12) [ISR B]
With:     [ISR A] tail-chain (6) [ISR B]
```

The registers saved for the interrupted thread are still on the stack, and both handlers return to the same place, so popping and re-pushing them would be wasted work.

**Late arrival timeline**

```
t0: low-priority IRQ L arrives → core starts stacking
t1: high-priority IRQ H arrives during stacking
t2: stacking completes → core fetches H's vector instead of L's and runs H
t3: H returns → tail-chains into L
```

The higher-priority interrupt gets almost the minimum latency, and no extra stacking is needed.

**Related optimisation: pop pre-emption.** If a new interrupt arrives while the core is unstacking after a handler, the unstacking is abandoned and the new handler starts (via tail-chaining).

**Why it matters:** these features make Cortex-M interrupt overhead low and predictable without any software effort, which is one reason ISRs can be plain C functions. They also mean a burst of interrupts is handled efficiently, and they explain why measured "exit + entry" time between two ISRs is shorter than you might calculate.

**Lazy FP stacking** works with these: if the handlers do not use the FPU, the FP registers are never actually saved.

### How do interrupt priorities work on Cortex-M? Lower number means? {M}
**Short answer:** On Cortex-M a **lower priority number means higher urgency**. Reset (−3), NMI (−2) and HardFault (−1) have fixed negative priorities and are the most urgent; configurable exceptions and interrupts have priorities from 0 (most urgent) upward. A higher-priority (lower-number) interrupt can pre-empt a running lower-priority handler; equal priorities never pre-empt each other.

**Implemented bits:** the priority field is 8 bits, but chips implement only the **top** few bits (e.g. 4 bits on STM32 → 16 levels, written as `level << 4`). CMSIS `NVIC_SetPriority(IRQn, 5)` does the shift for you using `__NVIC_PRIO_BITS`; writing raw registers you must shift yourself. Unimplemented low bits read as zero.

**Priority grouping (Armv7-M and Armv8-M Mainline)**

The priority value can be split into **group (pre-emption) priority** and **sub-priority** with `NVIC_SetPriorityGrouping()` (the `PRIGROUP` field in `SCB->AIRCR`):

- Only the **group** priority decides whether one interrupt can pre-empt another.
- The **sub-priority** only decides the order in which **pending** interrupts with the same group priority are serviced.
- If both are equal, the lower exception number goes first.

Example with 4 implemented bits and grouping "2 bits group, 2 bits sub": priorities 0x40 and 0x50 have the same group (1) and different sub-priorities, so neither pre-empts the other.

**Practical guidance**

- Give the most time-critical, short ISRs the highest priority (lowest numbers).
- With FreeRTOS, ISRs that call RTOS APIs must have a numeric priority **≥** `configMAX_SYSCALL_INTERRUPT_PRIORITY` (i.e. *less* urgent); more urgent ISRs must never call RTOS functions. This trips up many people because of the inverted numbering.
- PendSV should be the lowest priority (largest number), SysTick usually low as well.
- Keep the grouping simple (all bits as pre-emption priority is common, and what FreeRTOS recommends).

**Armv6-M (M0/M0+):** only 2 implemented bits (4 levels), no grouping, no BASEPRI.

### What is the difference between PRIMASK, FAULTMASK and BASEPRI? {H}
**Short answer:** All three are special registers that mask (block) exceptions. **PRIMASK** = 1 blocks every exception with configurable priority, leaving only NMI and HardFault; `__disable_irq()` sets it. **FAULTMASK** = 1 also blocks HardFault (only NMI remains); it is meant for fault handlers and is cleared automatically on exception return. **BASEPRI** = n blocks only exceptions whose priority value is ≥ n, so more urgent interrupts still run.

| Register | Blocks | Available on | Typical use |
|---|---|---|---|
| PRIMASK | all configurable-priority exceptions | all Cortex-M | short critical sections, `__disable_irq()` |
| FAULTMASK | the above + HardFault | Armv7-M, Armv8-M Mainline | fault handlers that must not be interrupted; running at priority −1 |
| BASEPRI | priorities numerically ≥ BASEPRI (0 = no masking) | Armv7-M, Armv8-M Mainline | RTOS critical sections that leave high-priority interrupts running |

```c
/* RTOS-style critical section that leaves priorities 0-4 running */
uint32_t old = __get_BASEPRI();
__set_BASEPRI(5u << (8u - __NVIC_PRIO_BITS));   /* mask priority values >= 5 */
/* ... critical work ... */
__set_BASEPRI(old);
```

`__set_BASEPRI_MAX()` (the `BASEPRI_MAX` alias) only raises the masking level, never lowers it, which makes nested use safe.

**Why BASEPRI matters:** with `PRIMASK`, every critical section adds latency to every interrupt. With `BASEPRI`, the kernel's critical sections do not delay the most time-critical interrupts at all (e.g. a motor-control PWM interrupt), as long as those interrupts do not call kernel APIs.

**Armv6-M (Cortex-M0/M0+)** has only PRIMASK, so RTOS critical sections there disable all interrupts.

**Other notes**

- Masking also delays the exception, it does not lose it: pending interrupts are taken when the mask is lifted.
- On Armv8-M with TrustZone, each security state has its own PRIMASK/FAULTMASK/BASEPRI, and Secure code can optionally deprioritise Non-secure interrupts.

### What causes a HardFault and how do you debug one? {M}
**Short answer:** A HardFault is the catch-all fault on Cortex-M. Common causes: accessing an invalid address (NULL or wild pointer, freed memory), stack overflow, executing from a non-executable or invalid address, branching to an address without the Thumb bit, unaligned multi-word accesses, divide by zero (if trapping is enabled), undefined instructions, and MemManage/BusFault/UsageFault faults escalated because their handlers are disabled. Debug it by capturing the stacked registers to find the faulting PC, then reading the fault status registers.

**Debugging steps**

1. **Capture the stack frame** in a handler (assembly wrapper chooses MSP or PSP from bit 2 of `LR`, as shown in the MSP/PSP question).

```c
void hard_fault_c(uint32_t *frame)
{
    volatile uint32_t pc   = frame[6];          /* faulting instruction (or next, if imprecise) */
    volatile uint32_t lr   = frame[5];          /* caller */
    volatile uint32_t cfsr = SCB->CFSR;         /* which fault and why */
    volatile uint32_t hfsr = SCB->HFSR;
    volatile uint32_t mmfar = SCB->MMFAR, bfar = SCB->BFAR;
    (void)pc; (void)lr; (void)cfsr; (void)hfsr; (void)mmfar; (void)bfar;
    __BKPT(0);                                  /* stop here in the debugger */
    for (;;) { }
}
```

2. **Find the code:** `arm-none-eabi-addr2line -e fw.elf 0x08001234` or look up PC and LR in the map file/disassembly.
3. **Decode `CFSR`** (Configurable Fault Status Register):
   - **MMFSR** (MemManage): `IACCVIOL`, `DACCVIOL`, `MSTKERR` (stacking error, often stack overflow), `MMARVALID` → address in `MMFAR`.
   - **BFSR** (BusFault): `PRECISERR` (address in `BFAR`), `IMPRECISERR` (write buffered, PC is later than the fault), `STKERR`, `IBUSERR`.
   - **UFSR** (UsageFault): `UNDEFINSTR`, `INVSTATE` (Thumb bit clear: bad function pointer), `INVPC`, `NOCP` (FPU used but not enabled), `UNALIGNED`, `DIVBYZERO`, `STKOF` (Armv8-M stack limit).
4. **`HFSR.FORCED`** = 1 means a configurable fault was escalated to HardFault (enable the separate handlers in `SCB->SHCSR` to get more specific faults).
5. **Imprecise BusFault:** the stacked PC is after the real culprit, because the write was buffered. Temporarily set `DISDEFWBUF` in `SCnSCB->ACTLR` (Cortex-M3/M4) to make bus faults precise while debugging.

**Recognisable patterns**

- PC = `0xFFFFFFFE` or a RAM address equal to the initial stack pointer: a NULL or erased-flash function pointer was called.
- `INVSTATE`: function pointer without bit 0 set.
- `NOCP`: floating point used before `SCB->CPACR` enabled the FPU (often in start-up code or an early `printf("%f")`).
- `MSTKERR`/`STKERR` or random faults that change with code changes: stack overflow.

**In production:** save the frame and status registers into a `.noinit` area, reset, and report them on the next boot. Tools like SEGGER Ozone, STM32CubeIDE's fault analyser and Memfault automate the decoding.

### What are SVC and PendSV used for? {H}
**Short answer:** **SVC** (Supervisor Call) is a synchronous exception triggered by the `SVC #n` instruction; unprivileged code uses it to request privileged services, and RTOSes use it to start the first task. **PendSV** (Pendable Service) is an asynchronous exception triggered by software setting a bit in `SCB->ICSR`; it is given the **lowest** priority, so it runs only after all other interrupts have finished, which makes it the right place for an RTOS to perform context switches.

**SVC**

- Executes immediately (synchronously) at the `SVC` instruction; it cannot be pended.
- The handler can read the SVC number from the instruction (`((uint8_t *)frame[6])[-2]`) and arguments from the stacked `R0`–`R3`, and return a result in the stacked `R0`.
- Uses: system calls from unprivileged tasks (with the MPU), starting the scheduler (FreeRTOS `vPortSVCHandler` restores the first task), secure/non-secure gateways in some designs.
- Calling SVC from a handler with equal or higher priority (or with interrupts masked) causes a HardFault, because a synchronous exception cannot wait.

**PendSV**

- Set pending with `SCB->ICSR = SCB_ICSR_PENDSVSET_Msk;`.
- Configured to the lowest priority: if an ISR wakes a higher-priority task, it pends PendSV; the switch happens only when all ISRs (including nested ones) have completed, so the switch never interrupts an ISR and needs to save only task context.
- The handler saves `R4`–`R11` (and `S16`–`S31` if the task used the FPU) onto the current task's stack (PSP), stores PSP in the task's TCB, picks the next task, restores its registers and PSP, and returns with `EXC_RETURN` = thread mode/PSP.

**SysTick** provides the RTOS tick: its handler updates time, wakes delayed tasks, and pends PendSV if a higher-priority task became ready or a time slice ended.

**Why not switch context directly in SysTick or in the ISR?** If an ISR pre-empted another ISR, switching tasks there would return to a different task while the first ISR is still unfinished, corrupting the stack. Deferring to the lowest-priority PendSV avoids this and also coalesces several switch requests into one.

### What is the MPU and how is it used? {M}
**Short answer:** The Memory Protection Unit lets software define a small number of memory regions (typically 8 or 16) with access permissions (privileged/unprivileged read, write, execute-never) and memory attributes (cacheable, bufferable, shareable, device). An access that violates the rules raises a MemManage fault instead of silently corrupting memory. It does not translate addresses (no virtual memory).

**Uses**

- **Stack overflow detection:** a no-access guard region just below each stack.
- **NULL pointer detection:** a no-access region at address 0 (after relocating the vector table).
- **Execute-never RAM** and read-only flash, which stops many code-injection and accidental-overwrite bugs.
- **Task isolation:** unprivileged tasks can access only their own stack/data and the peripherals they need (FreeRTOS-MPU, Zephyr user mode, safety RTOSes).
- **Cache control on Cortex-M7:** make DMA buffers non-cacheable or write-through, and mark external memory and peripheral regions correctly.

**Region rules**

| | Armv7-M (M3/M4/M7) | Armv8-M (M23/M33/M55/M85) |
|---|---|---|
| Region definition | base + size | base + limit |
| Size | power of two, 32 B to 4 GB, base aligned to size | any multiple of 32 bytes |
| Subregions | 8 subregions per region can be disabled | none |
| Overlap | allowed; higher region number wins | not allowed |
| Attributes | TEX/C/B/S bits | index into `MAIR` attribute registers |

**Example (Armv7-M): make a 32-byte guard at the bottom of a task stack**

```c
MPU->RNR  = 7;                                   /* region 7 */
MPU->RBAR = (uint32_t)task_stack;                /* must be 32-byte aligned */
MPU->RASR = (0u << MPU_RASR_AP_Pos)              /* no access */
          | MPU_RASR_XN_Msk
          | (4u << MPU_RASR_SIZE_Pos)            /* size = 2^(4+1) = 32 bytes */
          | MPU_RASR_ENABLE_Msk;
MPU->CTRL = MPU_CTRL_ENABLE_Msk | MPU_CTRL_PRIVDEFENA_Msk;  /* default map for privileged code */
__DSB();
__ISB();
```

**PRIVDEFENA** keeps the default memory map for privileged code, so you only need regions for what you want to restrict.

**Limitations:** few regions (an RTOS reprograms some on every context switch), the v7-M alignment rules waste memory, and MPU programming is easy to get subtly wrong, so test violations deliberately.

### What is TrustZone for Cortex-M? {H}
**Short answer:** TrustZone for Armv8-M (Cortex-M23/M33/M35P/M55/M85) splits the system into a **Secure** world and a **Non-secure** world on the same core. Memory, peripherals and interrupts are assigned to one world; Non-secure code cannot access Secure resources, and can call Secure code only through defined entry points. It protects keys, secure boot, cryptographic services and firmware update logic from bugs or attacks in the application.

**How it works**

- **SAU** (Security Attribution Unit, programmed by secure code) and **IDAU** (fixed by the chip designer) mark each address as Secure, Non-secure, or **Non-secure Callable (NSC)**.
- **Entry from Non-secure to Secure** only at NSC addresses that start with the `SG` (secure gateway) instruction; the compiler generates these veneers for functions marked `__attribute__((cmse_nonsecure_entry))`.
- **Calls from Secure to Non-secure** use `BLXNS`, with registers cleared so secrets do not leak.
- **Banked resources:** separate stack pointers (MSP_S/PSP_S, MSP_NS/PSP_NS), stack limits, MPUs, SysTick timers, VTORs, and interrupt masks per world. Each interrupt is assigned to one world (`NVIC->ITNS`).
- **Peripheral and memory protection** outside the core by the chip's security controllers (e.g. TZC, MPC/PPC), so even DMA from the Non-secure side cannot read Secure memory.
- Faults from security violations go to the **SecureFault** handler.

**Software stack:** the Secure side typically runs **Trusted Firmware-M (TF-M)**, which provides PSA services (crypto, secure storage, attestation, firmware update), and the Non-secure side runs the RTOS and application (Zephyr, FreeRTOS).

**Compared with TrustZone for Cortex-A:** the same idea, but Cortex-A switches worlds through EL3 secure monitor calls (`SMC`) and runs a full secure OS (OP-TEE). Cortex-M switching is a fast function call, designed for microcontrollers.

**Design rules:** keep the Secure world small, validate every pointer and length passed from the Non-secure side (it may point into Secure memory: use `cmse_check_address_range`), and lock the configuration (SAU, debug access) before starting Non-secure code.

### What is the Cortex-A53, and what are its key architectural features? {M}
**Short answer:** The Cortex-A53 is Arm's most widely used 64-bit (Armv8-A) application core: an in-order, dual-issue, 8-stage pipeline core optimised for efficiency, used in the Raspberry Pi 3, many i.MX 8, Rockchip, Allwinner and Qualcomm SoCs, and as the LITTLE core in big.LITTLE designs. It runs both AArch64 and AArch32 code, has four exception levels (EL0–EL3) with virtualization and TrustZone, a Neon SIMD and floating-point unit, separate L1 instruction and data caches per core, a shared L2 cache, and an MMU with a two-level TLB.

**Execution states and privilege**

- **AArch64** (A64 instruction set, 31 × 64-bit registers) and **AArch32** (A32/T32, compatible with Armv7-A) at each exception level, with the restriction that a lower level cannot be 64-bit if the level above is 32-bit.
- **EL0** applications, **EL1** OS kernel, **EL2** hypervisor, **EL3** secure monitor; **Secure** and **Non-secure** states (TrustZone). In AArch32, the older processor modes (User, FIQ, IRQ, Supervisor, Abort, Undefined, System, Hyp, Monitor) map onto these levels.

**Floating point and SIMD (Neon / Advanced SIMD)**

- IEEE 754 single and double precision floating point is mandatory in AArch64.
- Thirty-two 128-bit vector registers (`V0`–`V31`), each viewed as 16×8-bit, 8×16-bit, 4×32-bit or 2×64-bit lanes, for media, DSP and ML workloads.
- Optional **Cryptography Extension**: AES and SHA-1/SHA-256 instructions, a big speed-up for TLS and disk encryption.

**Caches and TLBs (typical configuration)**

| | Size / organisation |
|---|---|
| L1 instruction cache | 8–64 KB per core, 2-way set associative, 64-byte lines |
| L1 data cache | 8–64 KB per core, 4-way set associative, 64-byte lines, write-back |
| L2 cache | shared, 128 KB–2 MB, 16-way, optional |
| L1 TLBs | micro-TLBs (10 entries each for instructions and data) |
| Main TLB | 512 entries, 4-way, per core |
| Page-walk cache / IPA cache | caches intermediate translation results |

Data coherency between cores is kept by the **SCU** (snoop control unit) using a MOESI-style protocol; DMA masters can use the **ACP** (Accelerator Coherency Port) to access memory coherently through the L2.

**Other features:** 1–4 cores per cluster, generic timer, GICv3/v4 CPU interface, ECC/parity options on caches, and hardware virtualization (stage-2 translation, but **no VHE**, which arrived in Armv8.1).

**Interview angle:** knowing A53 details helps explain performance (in-order core: code scheduling and cache behaviour matter), Linux boot (EL2/EL3 handover), and why Neon intrinsics speed up image and audio processing on embedded Linux devices.

### What is a CPU cache, and how do you write cache-friendly code? {M}
**Short answer:** A cache is a small, fast memory close to the CPU that keeps copies of recently used memory in fixed-size blocks called **cache lines** (32 bytes on Cortex-M7, 64 bytes on most Cortex-A). Accesses that hit in the cache take a few cycles; misses go to slower memory (tens to hundreds of cycles). Code is cache-friendly when it uses data that is close together (spatial locality) and reuses data soon (temporal locality), and when hot data structures are small and laid out in the order they are accessed.

**Key terms**

| Term | Meaning |
|---|---|
| Line | unit of transfer (e.g. 64 bytes) |
| Set associativity | each address can go in N places (ways) within its set; 1-way = direct-mapped |
| Hit / miss | data found / not found |
| Write-back vs write-through | write-back updates memory only on eviction (faster); write-through writes memory every time |
| Write-allocate | on a write miss, load the line into the cache |
| Compulsory, capacity, conflict misses | first use; working set too big; addresses competing for the same set |
| Coherency | keeping caches of several cores (and DMA) consistent |

**Example: loop order over a 2-D array**

```c
#define N 1024
static float m[N][N];

float sum_rows(void)            /* row-major traversal: consecutive addresses, ~1 miss per 16 floats */
{
    float s = 0;
    for (int i = 0; i < N; i++)
        for (int j = 0; j < N; j++)
            s += m[i][j];
    return s;
}

float sum_cols(void)            /* column-major: each access 4 KB apart, a miss almost every time */
{
    float s = 0;
    for (int j = 0; j < N; j++)
        for (int i = 0; i < N; i++)
            s += m[i][j];
    return s;
}
```

The second version can be several times slower with exactly the same arithmetic.

**Techniques**

- Traverse arrays in memory order; prefer arrays to linked lists for hot data.
- **Structure of arrays** vs array of structures: if a loop uses one field of many objects, store that field contiguously.
- Keep hot fields together and cold fields elsewhere; align heavily shared structures to cache lines.
- **Blocking/tiling** large computations (matrix multiply, image filters) so each block fits in the cache.
- Avoid **false sharing** on multi-core systems: two cores writing different variables in the same line make the line bounce between caches; pad per-core data to a full line.
- Prefetch (`__builtin_prefetch`) for predictable access patterns the hardware prefetcher misses.

**MCU specifics:** Cortex-M0–M4 usually have no data cache (but vendors add flash accelerators such as ST's ART); Cortex-M7 and M55/M85 have L1 caches, which must be enabled (`SCB_EnableICache()`, `SCB_EnableDCache()`) and handled carefully with DMA. TCM (tightly coupled memory) gives single-cycle, deterministic access without cache unpredictability, which is often better for real-time code.

### What is the Arm memory map, and what are "DRAM holes"? {H}
**Short answer:** Arm systems follow a recommended physical address map so that software and SoC designs are consistent: low addresses for boot ROM/flash and on-chip memory, a region for peripherals, and DRAM above that. Because the 32-bit address space (4 GB) is shared with peripherals, a system with lots of DRAM cannot place it all below 4 GB; the parts of the DRAM that would collide with peripheral space are remapped to higher addresses (above 4 GB, in the 36-bit and 40-bit extensions of the map). The gaps this leaves in the DRAM address ranges are the "DRAM holes".

**Cortex-M fixed memory map (Armv7-M/v8-M)**

| Range | Region | Typical content |
|---|---|---|
| `0x0000_0000`–`0x1FFF_FFFF` | Code | flash, boot ROM, ITCM |
| `0x2000_0000`–`0x3FFF_FFFF` | SRAM | on-chip RAM (bit-band region on M3/M4) |
| `0x4000_0000`–`0x5FFF_FFFF` | Peripheral | on-chip peripherals |
| `0x6000_0000`–`0x9FFF_FFFF` | External RAM | FMC/SDRAM |
| `0xA000_0000`–`0xDFFF_FFFF` | External device | |
| `0xE000_0000`–`0xFFFF_FFFF` | System | NVIC, SCB, SysTick, MPU, debug (PPB) |

Because the map is fixed, every Cortex-M part has the NVIC at `0xE000E100`, the same SysTick address, and default memory attributes (e.g. the peripheral region is Device memory, execute-never).

**Cortex-A systems (Arm's "Principles of Arm Memory Maps")**

- The first 4 GB (32-bit) contains boot ROM, on-chip RAM, peripherals and the first 2 GB of DRAM (often from `0x8000_0000`).
- The 36-bit and 40-bit maps repeat the same structure, with large DRAM windows above 4 GB (e.g. starting at `0x8_8000_0000`) and peripheral space reserved in each region.
- A system with, say, 8 GB of DRAM therefore sees it as several non-contiguous ranges: 2 GB low and the remaining 6 GB high. The ranges reserved for peripherals and future use inside the DRAM windows are the holes.

**Why a common map helps**

- The same kernel and firmware work across SoCs with different memory sizes; devices are found from the device tree or ACPI, but DRAM placement follows predictable rules.
- 32-bit software (and 32-bit DMA masters) can still reach the low 2 GB of DRAM.
- Moving from 32-bit to 36/40-bit physical addresses (LPAE on Armv7, Armv8-A) does not force a redesign of where peripherals sit.

**Practical consequences on Linux:** the device tree `/memory` node lists several banks; DMA from 32-bit-only devices needs buffers in the low region (`ZONE_DMA32`) or an IOMMU/SMMU; and the kernel's memory zones reflect the holes.

### How do Arm systems keep DMA and CPU caches coherent (ACP, I/O coherency)? {H}
**Short answer:** If a DMA master accesses main memory directly while the CPUs work through write-back caches, the two can see different data. There are two solutions. **Software coherency:** the driver cleans and invalidates cache lines around each transfer (what Cortex-M7 firmware and many Linux drivers do via the DMA API). **Hardware (I/O) coherency:** the DMA master is connected so that its accesses are checked against the CPU caches, either through the **Accelerator Coherency Port (ACP)** on the CPU cluster, or through a coherent interconnect (CCI, CCN, CMN) using the ACE-Lite protocol.

**ACP (Accelerator Coherency Port)**

- An AXI slave port on clusters such as Cortex-A53/A9/A72 that lets an external master (DMA engine, accelerator, FPGA logic) read and write memory **through** the cluster's coherency logic (SCU and L2).
- A read via ACP returns the latest data even if it is dirty in a CPU's L1; a write via ACP updates or invalidates the cached copies.
- Accesses may also allocate into the L2, so an accelerator and the CPUs can share data with low latency (useful for small, frequent transfers).
- Limitations: limited bandwidth (it shares the cluster's ports), only certain access sizes and types, and heavy use pollutes the L2.

**Coherent interconnects:** in larger SoCs, the CCI/CMN snoops the CPU caches for I/O masters that use **ACE-Lite**, so DMA from a network controller or GPU is coherent without software maintenance. Linux learns this from the device tree property `dma-coherent`, and the DMA API then skips cache maintenance.

**Choosing between them**

| | Software maintenance | ACP / coherent interconnect |
|---|---|---|
| Hardware cost | none | needs the port/interconnect |
| CPU overhead | clean/invalidate per buffer (expensive for many small buffers) | none |
| Bugs | easy to forget a maintenance call or misalign a buffer | fewer software bugs |
| Large streaming transfers | fine | may thrash the L2 |

**Interview follow-up:** "What happens if a buffer is not cache-line aligned in the software approach?" Invalidating the buffer also invalidates neighbouring data in the same line, losing recent CPU writes, which is why DMA buffers must be aligned and padded to whole lines.

### What are memory types and shareability domains in the Arm architecture? {H}
**Short answer:** Arm classifies memory into **Normal** memory (RAM, ROM: accesses may be cached, merged, reordered and speculated) and **Device** memory (peripherals: accesses must not be speculated or merged and keep order, with sub-types `nGnRnE`, `nGnRE`, `nGRE`, `GRE` describing what is allowed). **Shareability** describes which observers (cores, DMA masters) must see a coherent view of a Normal memory location: **Non-shareable** (one core only), **Inner Shareable** (typically all cores in the cluster/system that run the same OS), and **Outer Shareable** (also other masters such as GPUs or DMA on a coherent interconnect). Barriers and cache maintenance instructions take a shareability domain argument.

**Memory types**

| Type | Caching | Reordering / merging / speculation | Use |
|---|---|---|---|
| Normal, write-back cacheable | yes | allowed | RAM for code and data |
| Normal, non-cacheable | no | reordering and merging allowed | DMA buffers without coherency, frame buffers |
| Device-nGnRnE | no | none (no Gathering, no Reordering, no Early write ack) | strongly ordered registers |
| Device-nGnRE | no | early write acknowledgement allowed | most peripheral registers (Linux `ioremap()`) |
| Device-GRE | no | gathering and reordering allowed | rarely: e.g. some write-combining buffers |

Attributes are set in page-table entries via `MAIR_ELx` indexes (Cortex-A) or MPU attributes (Cortex-M/R).

**Shareability domains in practice**

- On a 4-core Cortex-A53 cluster running Linux, all normal memory is mapped **Inner Shareable**, and the SCU keeps the cores' caches coherent automatically.
- A barrier such as `DMB ISH` orders accesses as seen by all cores in the inner shareable domain; `DMB OSH` extends to the outer domain (e.g. for coherent DMA masters); `DMB SY` is the full system.
- TLB invalidation `TLBI ...IS` broadcasts to all cores in the inner shareable domain.
- Linux maps its `smp_mb()` to `DMB ISH`, while `mb()`/`dma_mb()` use `DMB SY`/`OSH` variants because they must also order accesses with devices.

**Why it exists:** making every operation globally coherent and ordered would be slow. Shareability lets software request coherency and ordering only as far as needed: a core-private variable needs nothing, shared data between cores needs inner shareable, and data shared with devices needs outer or full-system scope.

**Interview angle:** "Why does your DMA buffer work only with `dma_alloc_coherent`?" Because that maps it non-cacheable (or uses hardware coherency), while a normal cacheable mapping requires explicit maintenance before the device sees it.

### How do Arm multi-core processors support parallel programming? {M}
**Short answer:** Arm multi-core clusters provide **hardware cache coherency** between cores (snoop control unit, coherent interconnects), **atomic and exclusive-access instructions** for locks and lock-free data structures (`LDXR`/`STXR`, and Armv8.1 LSE atomics like `LDADD`, `CAS`, `SWP`), **memory barriers** (`DMB`, `DSB`, `ISB`, and load-acquire/store-release `LDAR`/`STLR`) because the memory model is weakly ordered, **event signalling** (`WFE`/`SEV`) for power-efficient spinning, **inter-processor interrupts** via the GIC (SGIs), and SIMD (Neon/SVE) inside each core. Heterogeneous designs (big.LITTLE, DynamIQ) add cores with different performance and power.

**Building blocks**

| Feature | Purpose |
|---|---|
| Cache coherency (MOESI, SCU/CCI/CMN) | every core sees the latest value of shared data without software flushes |
| `LDXR`/`STXR` (exclusive monitor) | atomic read-modify-write by retry loop (Armv8.0) |
| LSE atomics (`LDADD`, `CAS`, `SWP`) | single-instruction atomics that scale better under contention (Armv8.1+) |
| Barriers and acquire/release | enforce ordering on a weakly ordered memory model |
| `WFE`/`SEV` | a waiting core sleeps until another core signals (spinlocks) |
| GIC SGIs | one core interrupts another (scheduler IPIs, TLB shootdown, function calls on other CPUs) |
| Generic timer per core | per-core scheduling ticks with a common time base |
| big.LITTLE / DynamIQ | run demanding threads on big cores, background work on LITTLE cores |

**Weak memory ordering example (message passing):**

```c
#include <stdatomic.h>

int data;
atomic_int ready;

void producer(void) { data = 42; atomic_store_explicit(&ready, 1, memory_order_release); }   /* STLR */
int consumer(void)
{
    while (!atomic_load_explicit(&ready, memory_order_acquire)) { }                           /* LDAR */
    return data;   /* guaranteed to see 42 */
}
```

Without acquire/release, a core could observe `ready == 1` before the write to `data` becomes visible.

**Software side:** POSIX threads, OpenMP, and data-parallel frameworks (OpenCL, Vulkan compute) on the GPU. **Processor affinity** pins threads to cores to keep caches warm or isolate real-time work.

**Scalability limits:** contention on shared locks and cache lines (false sharing), memory bandwidth, and Amdahl's law: if 10% of a program is serial, the speed-up can never exceed 10×.

**Follow-up example: merge sort.** With unlimited processors, the sorting of halves can run in parallel, and with a parallel merge the depth is O(log² n) (O(n) if the merge itself is sequential at the top level); with p processors, the time is roughly O((n log n)/p + n) for the simple version where the final merge is sequential.

### How is the system clock configured on an MCU? {M}
**Short answer:** An MCU has several clock sources: a fast internal RC oscillator (starts quickly, less accurate), an external crystal or oscillator (accurate, needed for USB, CAN, precise UART baud rates), and a 32.768 kHz low-speed crystal for the RTC. A **PLL** multiplies a source up to the core frequency, and prescalers divide it for the buses and peripherals. When raising the frequency, increase the flash wait states (and the voltage scale, if applicable) **before** switching to the faster clock.

**Typical sequence (STM32-style)**

1. Enable the external oscillator (HSE) and wait for its ready flag (with a timeout and a fallback to the internal oscillator).
2. Set the regulator voltage scale for the target frequency if the chip requires it.
3. Configure **flash wait states** (latency) and enable prefetch/caches for the new frequency.
4. Configure the PLL (input divider, multiplier, output dividers), enable it, wait for lock.
5. Set AHB/APB prescalers so buses stay within their maximum frequencies.
6. Switch the system clock multiplexer to the PLL and wait until the switch is confirmed.
7. Update `SystemCoreClock` so SysTick, delays and UART baud calculations use the right value.

**Example numbers:** 8 MHz HSE ÷ 8 = 1 MHz × 336 = 336 MHz VCO ÷ 2 = 168 MHz SYSCLK (STM32F4), APB1 = 42 MHz, APB2 = 84 MHz.

**Why wait states matter:** flash access time is fixed (e.g. ~30 ns). At 168 MHz a cycle is 6 ns, so the CPU must wait several cycles per flash read. Too few wait states → the CPU reads garbage → random HardFaults that appear only at high speed or high temperature.

**Other points**

- **Clock security system (CSS):** detects a failed external crystal and switches to the internal oscillator, raising an NMI.
- **Peripheral clocks** must be enabled individually (`RCC->AHB1ENR |= ...`) before accessing peripheral registers, or writes are ignored and reads return 0: a very common bring-up bug.
- **Low power:** run slower or from the internal oscillator when possible; power scales roughly with frequency.
- **Accuracy:** UART needs roughly ±2% total baud error, USB full-speed ±0.25% (internal RC oscillators often need clock recovery/trim to meet it), CAN about ±0.5% or tighter.

### How does dynamic voltage and frequency scaling (DVFS) save power? {M}
**Short answer:** The dynamic power of CMOS logic is roughly **P = C · V² · f** (switched capacitance × voltage squared × frequency). DVFS lowers the clock frequency when full performance is not needed and, because a lower frequency allows a lower supply voltage, lowers the voltage too. Since power depends on V², reducing voltage gives a large saving. The OS (or firmware) picks an **operating performance point** (OPP: a frequency/voltage pair) based on the current load.

**Example:** going from 1.2 GHz at 1.1 V to 600 MHz at 0.9 V:

```
P2 / P1 = (0.9² × 0.6) / (1.1² × 1.2) = 0.486 / 1.452 ≈ 0.33
```

Half the speed for about one third of the dynamic power, so the energy per operation also drops (~0.67×).

**Rules when switching**

- **Raising performance:** increase the voltage first, wait for it to settle, then increase the frequency.
- **Lowering:** decrease the frequency first, then the voltage.
- Flash wait states (MCU) or memory timings must also be valid for the new frequency.

**In Linux:** the **cpufreq** framework with governors (`schedutil`, `ondemand`, `performance`, `powersave`), OPP tables in the device tree, a clock driver and a regulator (PMIC) driver; on Arm servers and newer SoCs, firmware (SCMI) performs the change. Check with `cpupower frequency-info` or `/sys/devices/system/cpu/cpu0/cpufreq/`.

**On MCUs:** switch between run modes or PLL settings (e.g. STM32L4 range 1/range 2), run from a slower clock when idle, and use voltage scaling registers.

**DVFS vs "race to idle":** sometimes it is better to run at full speed, finish quickly and go into a deep sleep state, because static (leakage) power and the rest of the system (memory, radio) keep consuming power while the CPU works slowly. The right choice depends on how much the sleep states save; measure.

**Related techniques:** clock gating (stop clocks to unused blocks), power gating (switch off domains), big.LITTLE task placement, and thermal throttling (reducing the OPP when the chip gets too hot).

### What are the GPIO modes, and what are drive strength and slew rate? {E}
**Short answer:** A GPIO pin can be configured as an **input** (floating, with pull-up, or with pull-down), an **output** (push-pull or open-drain), an **alternate function** (controlled by a peripheral such as UART TX or a timer PWM output), or **analog** (digital buffer disconnected, for ADC/DAC). Outputs also have configurable **drive strength** (how much current the pin can source or sink while keeping valid logic levels) and **slew rate/speed** (how fast the edges are).

| Mode | Use | Notes |
|---|---|---|
| Input floating | signals driven by another device | never leave unconnected inputs floating (noise, extra current) |
| Input pull-up / pull-down | buttons, open-drain signals, defined default state | internal pulls are weak (typically 20–50 kΩ) |
| Output push-pull | LEDs, chip selects, enables | drives high and low actively |
| Output open-drain | I2C, shared interrupt lines, level shifting with an external pull-up | only drives low |
| Alternate function | UART, SPI, I2C, timers, USB | the peripheral controls the pin; select the AF number in the pin mux |
| Analog | ADC inputs, DAC outputs, unused pins | lowest leakage; no Schmitt trigger input current |

**Drive strength**

- Rated in mA (e.g. 4, 8, 20 mA per pin) and limited per port and per chip. Exceeding it drops the output voltage below valid levels and can damage the pin.
- An LED needs a series resistor sized for the pin's capability; larger loads (relays, motors, LED strips) need a transistor or MOSFET driver.

**Slew rate / speed setting**

- Faster edges are needed for high-frequency signals (SPI at 50 MHz, SDIO, Ethernet RMII).
- Faster edges also cause more ringing, crosstalk, EMI and higher switching current. Use the **slowest setting that meets timing**, especially for long traces or cables.

**Other configuration details**

- **Schmitt trigger** inputs (hysteresis) reject noise on slow edges.
- **Interrupts on edges** (EXTI) for wake-up and events.
- **Lock registers** on some MCUs prevent accidental reconfiguration of critical pins.
- **Reset state:** most pins are inputs (often floating or analog) after reset; outputs that control hardware (motor enables, power switches) need external pull resistors so they are safe before firmware configures them.

**Power tip:** configure unused pins as analog (or output low) to minimise current; a single floating input can add tens or hundreds of µA in sleep.

### What is the difference between open-drain and push-pull outputs? {E}
**Short answer:** A **push-pull** output has two transistors (one to the supply, one to ground) and actively drives the line both high and low, giving strong, fast edges. An **open-drain** (open-collector for bipolar transistors) output has only the transistor to ground: it can pull the line low or release it; a pull-up resistor makes the line high when released. Open-drain lets several devices share one line safely and lets the line be pulled up to a different voltage.

```
Push-pull                     Open-drain
  VDD                           VDD (or another voltage)
   |                             |
  [P-MOS]                       [R pull-up]
   |---- output                  |---- line
  [N-MOS]                       [N-MOS]
   |                             |
  GND                           GND
```

| | Push-pull | Open-drain |
|---|---|---|
| Drives high | actively | via pull-up resistor (passive) |
| Rise time | fast | depends on R × C of the line |
| Several outputs on one line | short circuit if one drives high and another low | safe: any device can pull low ("wired-AND") |
| High level voltage | the chip's supply | whatever the pull-up connects to (within the pin's tolerance) |
| Power | no static current | current flows through the pull-up while low |
| Typical uses | LEDs, SPI, UART TX, chip select | I2C SDA/SCL, shared interrupt/reset lines, 1-Wire, level shifting |

**Why I2C needs open-drain:** several devices (controller and targets) drive SDA, and clock stretching and arbitration require that any device can hold the line low while others release it. With push-pull outputs, two devices driving opposite levels would short the supply.

**Choosing the pull-up value:** a smaller resistor gives faster rising edges but more current when the line is low. For I2C, typical values are 2.2–10 kΩ, calculated from the bus capacitance and speed (see the Communication Protocols topic).

**Level shifting trick:** a 3.3 V MCU can drive an open-drain line pulled up to 5 V **only if the pin is 5 V tolerant** (marked "FT" on STM32). Otherwise use a level shifter.

### How do timers generate PWM? {M}
**Short answer:** A timer counts from 0 up to an auto-reload value (ARR) and then restarts, which sets the PWM period. In PWM mode, each channel compares the counter with a compare register (CCR): the output is active while the counter is below CCR and inactive after it, which sets the duty cycle. Changing CCR changes the duty cycle; changing ARR (or the prescaler) changes the frequency.

**Formulas (up-counting, STM32-style)**

```
f_PWM = f_timer / ((PSC + 1) × (ARR + 1))
duty  = CCR / (ARR + 1)
resolution = ARR + 1 steps (log2(ARR + 1) bits)
```

**Example:** 72 MHz timer clock, PSC = 71 → 1 MHz counter (1 µs per tick); ARR = 999 → period 1000 µs = 1 kHz; CCR = 250 → 25% duty.

**Trade-off:** for a given timer clock, higher PWM frequency means fewer counts per period, so less duty-cycle resolution. 72 MHz with ARR = 71 gives 1 MHz PWM but only 72 steps (≈6 bits).

**Set-up steps**

1. Enable the timer clock and configure the GPIO pin as the timer's alternate function.
2. Set PSC and ARR; enable **ARR preload** (ARPE).
3. Configure the channel in PWM mode 1 with **CCR preload** enabled, set polarity, enable the channel output (and on advanced timers the main output enable, MOE).
4. Generate an update event to load the shadow registers, then start the counter.

**Why preload (shadow) registers:** new ARR/CCR values are transferred at the next update event (end of period), so changing the duty cycle mid-period cannot create a glitch (an extra short or long pulse).

**Modes and features**

- **Edge-aligned** (counts up, sawtooth) vs **center-aligned** (counts up and down, triangle): center-aligned gives symmetric pulses, and the switching of different phases is spread out, which reduces current ripple and EMI in motor control.
- **Complementary outputs with dead time** (advanced timers): drive the high- and low-side transistors of a half bridge without both being on at the same time (shoot-through).
- **Break input:** hardware disables outputs immediately on a fault signal.
- **DMA bursts** to update CCR every period (LED strips like WS2812, sine generation).

**Uses:** LED dimming, motor speed control, servo control (50 Hz, 1–2 ms pulses), switching power supplies, generating analogue voltages through an RC filter, buzzers.

### What is input capture and how do you measure a frequency with it? {M}
**Short answer:** In input capture mode, a timer copies (latches) its counter value into a capture register when a selected edge occurs on an input pin, and can raise an interrupt or DMA request. Capturing two consecutive rising edges gives the period in timer ticks: `period = c2 − c1` (computed with unsigned arithmetic so one counter wrap is handled automatically). Frequency = timer clock ÷ period.

```c
static volatile uint16_t last;
static volatile uint32_t period_ticks;

void TIM3_IRQHandler(void)
{
    if (TIM3->SR & TIM_SR_CC1IF) {
        uint16_t now = (uint16_t)TIM3->CCR1;        /* reading CCR1 clears CC1IF */
        period_ticks = (uint16_t)(now - last);      /* 16-bit wrap-safe difference */
        last = now;
    }
}

/* f = timer_clk / period_ticks, e.g. 1 MHz / 2500 = 400 Hz */
```

**Handling long periods:** if the period can exceed one counter cycle (65,536 ticks for a 16-bit timer), count overflows in the update interrupt and add `overflows × 65536`, being careful when an overflow and a capture happen close together. Or use a 32-bit timer, or a larger prescaler (less resolution).

**Measuring duty cycle (PWM input mode):** map one input to two capture channels, one capturing on rising and one on falling edges, with the timer reset on each rising edge (slave reset mode). Then CCR1 = period and CCR2 = high time.

**Choosing a method by frequency**

| Signal | Best method | Why |
|---|---|---|
| Low frequency (Hz–kHz) | input capture (period measurement) | high resolution from many timer ticks per period |
| High frequency (100 kHz–MHz) | counting edges in a fixed gate time (timer in external clock mode) | many edges per gate → good accuracy |
| Very short pulses | capture with input filter disabled and a fast timer clock | resolution = 1 timer tick |

**Accuracy:** ±1 tick quantisation error per measurement; average several periods for better precision. Input filters (digital filters on the capture input) reject glitches.

**Uses:** reading encoder or hall-sensor speed, ultrasonic distance sensors (echo pulse width), RC receiver pulse widths, IR remote decoding, measuring a crystal's frequency against a reference.

### How does an ADC work and what are its key parameters? {M}
**Short answer:** Most MCU ADCs are **successive approximation (SAR)** converters: a sample-and-hold capacitor captures the input voltage, then an internal DAC and comparator perform a binary search, deciding one bit per step from the most significant bit down. Key parameters are resolution, sampling time, conversion rate, the reference voltage, and accuracy figures (offset, gain error, INL/DNL, ENOB).

**Conversion:** `code = Vin / Vref × (2^N − 1)` (approximately `Vin / Vref × 2^N`). A 12-bit ADC with Vref = 3.3 V has an LSB of 3.3 / 4096 ≈ 0.81 mV. Reading 2048 means about 1.65 V.

**Key parameters**

| Parameter | What to know |
|---|---|
| Resolution | 10, 12, 16 bits; number of output codes |
| Sampling time | time to charge the sampling capacitor; too short with a high source impedance gives readings that are too low |
| Conversion rate | samples per second (e.g. 1–5 Msps on STM32) |
| Reference voltage | accuracy and noise of Vref directly limit accuracy; use a separate filtered VREF+ pin or an external reference for precision |
| Offset and gain error | constant and proportional errors, removable by calibration |
| INL / DNL | non-linearity; DNL > 1 LSB means missing codes |
| ENOB | effective number of bits after noise and distortion; often 1–2 bits below nominal |

**Sampling techniques**

- **Timer-triggered conversions** give an exact, jitter-free sample rate (required for signal processing); software-triggered sampling in a loop does not.
- **Scan mode + DMA:** convert several channels in sequence into a buffer with no CPU work; circular DMA with half/full interrupts gives continuous double-buffered streaming.
- **Injected/priority channels:** sample critical signals (motor current) at precise moments in the PWM cycle.
- **Oversampling and averaging:** averaging 4^k samples adds k bits of effective resolution for slow signals, if there is some noise (dither) present. Many MCUs have hardware oversampling.
- **Anti-aliasing:** filter the input (RC low-pass) below half the sample rate (Nyquist), or high-frequency noise folds into the measurement.

**Driving the input:** the sampling capacitor (a few pF) must charge through the source impedance within the sampling time. A high-impedance sensor (e.g. a 100 kΩ divider) needs a longer sampling time, a buffer op-amp, or a capacitor at the pin (which acts as a charge reservoir).

**Other ADC types:** sigma-delta (high resolution, slower: weigh scales, audio, energy metering), pipelined and flash (very fast).

### How does a DAC work, and how do you generate a waveform with it? {M}
**Short answer:** A DAC (digital-to-analogue converter) turns a digital code into a voltage: `Vout = code / (2^N) × Vref` (for an N-bit DAC). MCU DACs are typically 8–12 bits with a few hundred kHz to a few MHz update rate. To generate a waveform, store one period of samples in a table and have a **timer trigger** the DAC update while **DMA** feeds samples from the table in circular mode, so the output frequency is exact and the CPU is not involved.

```c
#include <math.h>
#include <stdint.h>

#define N_SAMPLES 64
static uint16_t sine_table[N_SAMPLES];

void make_sine_table(void)                       /* 12-bit DAC, mid-scale offset */
{
    for (int i = 0; i < N_SAMPLES; i++)
        sine_table[i] = (uint16_t)(2048 + 2047 * sinf(2.0f * 3.14159265f * i / N_SAMPLES));
}
/* Configure: timer update event at f_out * N_SAMPLES (e.g. 1 kHz * 64 = 64 kHz),
   DAC trigger = timer TRGO, DMA circular from sine_table to the DAC data register. */
```

`f_out = f_trigger / N_SAMPLES`. More samples per period give a cleaner waveform but require a higher update rate.

**Key parameters:** resolution, settling time (how long the output takes to reach the new value), output impedance and drive capability (many MCU DACs need the internal output buffer enabled or an external op-amp to drive a load), and reference accuracy.

**Cleaning up the output:** a DAC produces a staircase; a **reconstruction low-pass filter** after it removes the step frequency (images around the update rate). The sinc roll-off of a zero-order hold also attenuates higher output frequencies slightly.

**DAC types:** resistor string, R-2R ladder (common on MCUs), sigma-delta (audio codecs), and **PWM + RC filter** as a cheap "DAC" when no DAC is available: duty cycle sets the average voltage, at the cost of ripple and slow response.

**Uses:** audio tones and alerts, generating reference or bias voltages, test signals, setting analogue control inputs (e.g. a laser driver or a motor controller reference), and the internal DAC that sets comparator thresholds.

### What is DMA and how is it configured? {M}
**Short answer:** A Direct Memory Access controller transfers data between peripherals and memory (or memory and memory) without the CPU copying each word. You configure the source and destination addresses, the number of items and their width, whether each address increments, the direction, the trigger (which peripheral request starts each transfer), priority, and normal or circular mode; interrupts signal half-transfer, transfer-complete and errors.

**Typical channel configuration (UART receive into a buffer)**

| Setting | Value |
|---|---|
| Source | `&USART2->DR` (peripheral, fixed address: no increment) |
| Destination | `rx_buf` (memory, increment after each item) |
| Item size | 8 bits both sides |
| Count | `sizeof rx_buf` |
| Request/stream | USART2_RX (via the DMA request mux on newer parts) |
| Mode | circular |
| Interrupts | half-transfer, transfer-complete, transfer-error |

Then enable the peripheral's DMA request (`USART2->CR3 |= USART_CR3_DMAR`) and the stream.

**Circular mode + half/complete interrupts = double buffering:** while DMA fills the second half of the buffer, the CPU processes the first half, and vice versa. For variable-length messages over UART, combine circular DMA with the **IDLE line** interrupt and read the DMA's remaining-count register (`NDTR`) to know how many bytes arrived.

**Other features**

- **Memory-to-memory** transfers (fast `memcpy` that frees the CPU).
- **Scatter-gather / linked-list descriptors** (on more advanced controllers and on application processors): a chain of transfers to non-contiguous buffers without CPU intervention.
- **FIFO and burst modes** to use the bus efficiently and pack bytes into words.
- **Priority levels** when several streams compete.

**Common pitfalls**

- **Buffer lifetime:** never use a local (stack) buffer for a DMA transfer that outlives the function.
- **Cache coherency** on Cortex-M7/A (clean/invalidate, alignment).
- **Bus access restrictions:** some DMA controllers cannot reach certain memories (e.g. DTCM on STM32H7) — the transfer fails silently or with an error flag.
- **Volatile:** the CPU reading a buffer that DMA writes must not be optimised into reading stale values; use `volatile` access or a barrier after the completion interrupt.
- **Error handling:** check transfer-error flags (bus errors from bad addresses).

### What low-power modes do MCUs have? {M}
**Short answer:** Names differ by vendor, but there are usually three levels. **Sleep**: the CPU clock stops (`WFI`/`WFE`), peripherals keep running, and any interrupt wakes it within a few cycles. **Stop/deep sleep**: most clocks and the PLL stop, RAM and registers are kept, wake-up comes from external interrupts, the RTC or a few low-power peripherals in microseconds, and clocks must be reconfigured afterwards. **Standby/shutdown**: almost everything is powered off, RAM is lost (except a small backup domain), wake-up is from a few pins or the RTC, and the MCU restarts through reset.

| Mode | CPU | Clocks | RAM | Wake sources | Wake time | Typical current |
|---|---|---|---|---|---|---|
| Run | on | all | kept | – | – | mA (e.g. 100 µA/MHz) |
| Sleep | off | peripherals on | kept | any interrupt | ~cycles | ~half of run |
| Stop / deep sleep | off | HF clocks off, LSE/LSI on | kept | EXTI, RTC, LPUART, LPTIM, comparators | µs | µA |
| Standby / shutdown | off | almost all off | lost (backup regs kept) | wake-up pins, RTC, reset | ms (reboot) | < 1 µA |

**Entering sleep on Cortex-M**

```c
SCB->SCR &= ~SCB_SCR_SLEEPDEEP_Msk;   /* light sleep */
__DSB();
__WFI();

SCB->SCR |= SCB_SCR_SLEEPDEEP_Msk;    /* deep sleep (vendor registers select Stop vs Standby) */
__DSB();
__WFI();
```

**SLEEPONEXIT:** set `SCB_SCR_SLEEPONEXIT_Msk` in fully interrupt-driven designs: the core goes back to sleep automatically after each ISR, without returning to the main loop.

**Getting really low current**

- Configure unused pins as analog or output low; disconnect pull resistors that conduct.
- Disable peripheral clocks and power-hungry analogue blocks (ADC, comparators, voltage reference) when not used.
- Lower the core voltage/frequency when awake (run modes).
- Turn off external components (sensors, radios, LEDs) via load switches.
- Make sure the debugger is disconnected: debug logic keeps clocks running (`DBGMCU` settings).
- Measure with a power analyser or a current probe over a full duty cycle (Nordic PPK2, Otii, Joulescope), not a multimeter.

**Battery life estimate:** average current = (active current × active time + sleep current × sleep time) / period. A device that wakes for 5 ms every second at 5 mA and sleeps at 2 µA averages ~27 µA, so a 220 mAh coin cell lasts roughly 8,000 hours (about 11 months), before self-discharge and peak-current limits.

### What is the difference between WFI and WFE? {H}
**Short answer:** `WFI` (Wait For Interrupt) puts the core to sleep until an interrupt (or debug request or reset) arrives. `WFE` (Wait For Event) sleeps until an **event**: an interrupt, an event signalled by another core with `SEV`, an external event input, or a pending event that is already latched. If the event register is already set when `WFE` executes, it clears it and continues immediately without sleeping.

| | WFI | WFE |
|---|---|---|
| Wakes on | interrupts (even if masked by PRIMASK, the core still wakes) | events: interrupts (with `SEVONPEND`, even disabled ones), `SEV` from another core, external event line |
| Event register | not used | if set, `WFE` clears it and does not sleep |
| Typical use | idle loops, low-power waiting for an interrupt | multi-core spinlocks, waiting for another core, low-overhead polling |

**Why the event register exists:** to avoid a race. If core B executes `SEV` just **before** core A executes `WFE`, the event is latched, so A does not miss it and sleep forever.

**Spinlock usage on Arm (multi-core)**

```asm
retry:
    LDAXR   w1, [x0]        // load-acquire exclusive
    CBNZ    w1, wait        // lock held by someone else
    STXR    w2, w3, [x0]    // try to take it
    CBNZ    w2, retry
    RET
wait:
    WFE                     // sleep until the holder releases and signals
    B       retry
```

The unlock is a store-release; clearing the exclusive monitor of a waiting core generates an event automatically on Armv8 (older code used an explicit `SEV`).

**Masked interrupts and WFI:** a common idiom for race-free sleep is `__disable_irq(); if (!work_pending) __WFI(); __enable_irq();`. The core still wakes on the interrupt (it is pending), and the ISR runs after `__enable_irq()`, so a wake-up between the check and the sleep is not lost.

**SEVONPEND** (`SCB->SCR`): makes any newly pending interrupt, even a disabled one, generate an event for `WFE`. Useful to wake on a peripheral flag without running an ISR.

**Practical rule:** use `WFI` for "sleep until something needs attention" in idle loops (RTOS idle hooks use it); use `WFE` for synchronisation between cores and in lock implementations.

### What is the difference between flash and EEPROM, and what is wear levelling? {M}
**Short answer:** Both are non-volatile memories. **Flash** is erased in large blocks (sectors or pages, typically 1–128 KB on MCUs) and programming can only change bits from 1 to 0; to change a 0 back to 1 you must erase the whole block. **EEPROM** can usually be erased and written byte by byte. Both wear out after a limited number of erase/write cycles (typically 10,000 for MCU flash, 100,000 to 1,000,000 for EEPROM). **Wear levelling** spreads writes across many locations so no single block reaches its limit early.

| | Flash (MCU embedded) | EEPROM |
|---|---|---|
| Erase unit | sector/page (KBs) | byte or word |
| Write unit | word/double-word/row (bits 1 → 0 only) | byte |
| Endurance | ~10k cycles (some 100k) | 100k–1M cycles |
| Retention | 10–20 years | 10–100 years |
| Speed | erase ms (sector: up to seconds), program µs | write ~3–5 ms per byte/page |
| Density / cost | high / low | low / higher |
| Reads while writing | usually blocks reads of the same bank | independent (external EEPROM) |

**Emulated EEPROM on flash (common technique)**

- Use two (or more) flash pages. Store records as (ID, value) pairs appended sequentially.
- To update a value, append a new record; the newest record for an ID is valid.
- When a page fills, copy the latest value of each ID to the other page, then erase the old page.
- Each erase now covers many updates, multiplying the effective endurance.

**Wear levelling in general:** log-structured storage, rotating sectors, keeping erase counts per block. Filesystems like **LittleFS** (MCU), UBIFS and F2FS (Linux) do this; managed flash (eMMC, SD) has a controller that does it internally.

**Power-loss safety:** a write or erase interrupted by power failure leaves a half-programmed area. Use sequence numbers and CRCs per record, write the new copy before invalidating the old, and validate at boot.

**Endurance calculation example:** writing a 32-byte record every minute to a 2 KB page pair with 10k cycles: each page holds 64 records → one erase per 64 minutes per page, alternating → each page erased about every 2 hours → 10k cycles last ~2.3 years. Using 8 pages instead extends it ~4×. Interviewers like to see this kind of estimate.

### What is an RTC and how is backup domain power used? {E}
**Short answer:** A Real-Time Clock is a low-power timer that keeps the calendar time (seconds, minutes, hours, date), usually driven by a 32.768 kHz crystal. It sits in a **backup domain** that can be powered from a separate `VBAT` pin (coin cell, supercapacitor) so it keeps running, along with a few backup registers, when the main supply is off. It also provides alarms and periodic wake-ups from low-power modes.

**Why 32.768 kHz:** 32,768 = 2¹⁵, so a 15-stage binary divider produces exactly 1 Hz. The crystals are small, cheap and consume very little power (the oscillator uses well under 1 µA).

**Features**

- Calendar in BCD or a binary second counter (sub-second resolution on many parts).
- **Alarms** that wake the MCU from stop or standby.
- **Periodic wake-up timer** for duty-cycled devices (e.g. measure every 10 minutes).
- **Tamper detection** inputs and timestamping (security products).
- **Backup registers or backup SRAM:** small storage kept on VBAT, useful for boot flags, reset counters, or the last known state.
- **Smooth calibration:** adjusts for crystal error in ppm.

**Accuracy:** a typical crystal is ±20 ppm, which is about ±1.7 seconds per day (≈ 52 s per month). Temperature changes make it worse (tuning-fork crystals drift quadratically away from 25 °C). Improve it with calibration against a reference, temperature compensation, or synchronising from GPS/NTP/cellular network time.

**Design points**

- Write-protect: RTC registers are usually locked; you must unlock the backup domain (e.g. `PWR->CR1 |= PWR_CR1_DBP` on STM32) to change them.
- The first time power is applied, detect that the RTC is not initialised (a magic value in a backup register) and set it.
- Use UTC internally and apply time zones in the application.
- If there is no battery, the time is lost on power loss; plan to get it from the network.

**External RTC chips** (DS3231, PCF85063, RV-3028) are used when the MCU lacks a good RTC or for very low backup current and temperature-compensated accuracy.

### What is JTAG and SWD? {E}
**Short answer:** Both are hardware debug interfaces that let a debug probe halt the CPU, set breakpoints, read and write memory and registers, and program flash. **JTAG** (IEEE 1149.1) uses 4 or 5 pins (TCK, TMS, TDI, TDO, optional nTRST), supports chaining several chips on one interface, and also provides **boundary scan** for testing board connections. **SWD** (Serial Wire Debug) is Arm's 2-pin alternative (SWDIO, SWCLK) with the same debug access to Cortex cores, which is why it is standard on Cortex-M boards.

| | JTAG | SWD |
|---|---|---|
| Pins | TCK, TMS, TDI, TDO (+ nTRST) | SWDIO, SWCLK (+ optional SWO) |
| Multiple devices | daisy chain | one target per interface (multi-drop SWD exists in SWD v2) |
| Boundary scan | yes | no |
| Arm Cortex debug access | yes | yes (same CoreSight debug port) |
| Typical use | FPGAs, CPLDs, Cortex-A SoCs, board test | Cortex-M microcontrollers |

**Related signals and features**

- **SWO** (Serial Wire Output): a one-pin trace output for **ITM** (`printf`-style logging via `ITM_SendChar`, very fast and non-intrusive), data watchpoint trace and PC sampling for profiling.
- **ETM/ETB/ETR** (Embedded Trace Macrocell): full instruction trace, captured by expensive probes or on-chip buffers.
- **RTT** (SEGGER Real-Time Transfer): uses the debug port to read a ring buffer in RAM, giving fast logging without extra pins.
- **nRESET** is usually wired to the debug connector so the probe can reset the target ("connect under reset" to recover a chip whose firmware disables SWD pins or goes into deep sleep immediately).

**Probes and tools:** ST-LINK, SEGGER J-Link, CMSIS-DAP (DAPLink, Raspberry Pi Debug Probe), Lauterbach TRACE32; software such as OpenOCD, pyOCD, GDB, and IDEs (STM32CubeIDE, Keil, IAR, VS Code + Cortex-Debug).

**Security:** production devices should disable or lock the debug port (read-out protection levels, debug authentication, TrustZone debug restrictions), otherwise anyone with a probe can read the firmware and secrets. Locking is usually irreversible or erases the chip.

### Do ARM64 registers X0, X1 and X2 contain data or memory addresses? {E}
**Short answer:** Both. AArch64 has 31 general-purpose registers (X0–X30), each 64 bits wide. Their W-register aliases access the lower 32 bits. A register holds bits; the instruction determines whether they represent an integer, an address, or something else.

```asm
MOV X1, #10
MOV X2, #20
ADD X3, X1, X2       // X3 = 30; no data-memory access
```

Now assume virtual address 0x1000 is valid, readable and contains the 64-bit value 50:

```asm
MOV X1, #0x1000
LDR X2, [X1]         // X2 = 50
STR X2, [X1]         // write 50 back to that address
```

```text
X1 = 0x1000 ----> Memory[0x1000] = 50
X2 = 50     <---- LDR reads the value
```

With the MMU enabled, the load/store address is translated and checked; data may come from cache rather than DRAM. MOV copies a value, LDR loads from memory, and STR stores to memory. In C, a pointer holds an address while dereferencing it accesses the object at that address.

### What is cache coherency in a multicore ARM system? {M}
**Short answer:** Cache coherency ensures that cores accessing the same coherent memory location do not continue using stale cached copies after a write becomes visible.

Suppose Core 0 and Core 1 both cache a shared variable a = 10. Core 0 writes a = 20. Without coherency, Core 1 might still read 10.

In a typical write-invalidate protocol:

1. Core 0 requests exclusive ownership of the cache line.
2. The coherent interconnect invalidates other cached copies.
3. Core 0 modifies the line.
4. A subsequent coherent read by Core 1 obtains the latest value, potentially from another cache rather than DRAM.

| MESI state | Meaning |
|---|---|
| Modified | Dirty line held exclusively; backing memory may be stale. |
| Exclusive | Clean line held exclusively. |
| Shared | Clean line may be held in multiple caches. |
| Invalid | Line cannot be used. |

MESI is an illustrative protocol; implementations may use other state machines. Arm coherent systems may use CCI or CMN interconnects and ACE or CHI protocols.

**CPU and DMA:** On a non-coherent DMA system, CPU-written dirty data may need cleaning before the device reads it, and stale CPU cache lines may need invalidating before the CPU reads device-written data. Linux drivers should use the DMA API (dma_map_single, dma_sync_single_for_cpu, dma_sync_single_for_device, dma_unmap_single, or dma_alloc_coherent as appropriate) rather than assuming direct physical addresses or manually managing caches.

**Interview trap:** Coherency operates on cache lines and does not guarantee ordering between different locations or make a++ atomic. Use proper synchronization and memory barriers.
