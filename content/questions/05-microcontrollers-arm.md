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
A microcontroller (MCU) typically integrates CPU, program memory, RAM and peripherals for dedicated control tasks. A microprocessor (MPU) generally targets more complex computing and often relies on external DRAM and storage. Modern SoCs blur this distinction.

#### 1. Typical architecture

```text
MCU                        MPU-based system
+-------------------+      +----------------------+
| CPU | Flash | RAM |      | CPU cores | Cache    |
| Timers | UART/SPI |      | MMU | DDR controller |
| GPIO | ADC | DMA  |      +----------+-----------+
+-------------------+                 |
                              External DRAM/storage
```

#### 2. Comparison

| Feature | MCU | MPU-based system |
|---|---|---|
| Memory | Usually substantial on-chip memory | Often external DRAM |
| Software | Bare metal or RTOS common | Linux/Android common |
| Power | Often low-power control | Often higher-performance computing |
| Timing | Often designed for predictable control | Depends on caches, OS and platform |

An STM32 Cortex-M4 can run a motor-control loop directly from flash. An i.MX8 Cortex-A system can run Linux with virtual memory, graphics and multiple processes.

**Interview takeaway:** Choose based on memory, performance, timing, power and software requirements. Integration alone is not a strict distinction: some MPUs contain extensive on-chip peripherals and memory.

### What is the difference between Harvard and von Neumann architecture? {E}
Harvard architecture separates instruction and data storage or access paths. Von Neumann architecture uses a unified instruction/data memory model.

#### 1. Conceptual comparison

```text
Harvard:
Instruction memory <-- instruction bus --> CPU
Data memory        <-- data bus        --> CPU

Von Neumann:
Combined code/data memory <--> shared path <--> CPU
```

Separate paths can allow simultaneous instruction fetch and data access. A shared path may create contention, although real processors use many techniques to improve throughput.

#### 2. Modified Harvard architecture

Many modern Arm cores have separate L1 instruction and data caches but a unified address space and shared lower-level memory. They can fetch instructions and access data concurrently without having strictly separate programmer-visible memory spaces.

#### 3. Firmware example

A Cortex-M implementation may use separate instruction and data bus interfaces while exposing flash and RAM through one address map. An AArch64 application may execute instructions from memory that was previously written as data, subject to execute permissions and required instruction-cache synchronization.

**Interview takeaway:** Distinguish physical bus/cache organization from the programmer-visible memory model. Modern architectures often combine features of both models.

### What is RISC, how does it differ from CISC, and why did Arm succeed? {E}
RISC (Reduced Instruction Set Computer) emphasizes regular instruction encodings and efficient register-based operations. CISC (Complex Instruction Set Computer) supports richer instruction forms, often including operations directly on memory.

#### 1. Example

A64 typically loads operands before arithmetic:

```asm
LDR W0, [X1]
ADD W0, W0, #1
STR W0, [X1]
```

An x86 instruction can express an increment of a memory operand, though the underlying processor may decode it into multiple internal operations.

#### 2. Comparison

| Feature | Typical A64 RISC | Typical x86 CISC |
|---|---|---|
| Encoding | Fixed 32-bit instructions | Variable instruction length |
| Arithmetic | Usually register operands | Register or memory operands |
| Implementation | May be simple or superscalar | Often decoded into internal operations |

Instruction-set design does not by itself determine speed, power or complexity. Modern high-performance processors use sophisticated pipelines regardless of ISA.

#### 3. Why Arm gained adoption

Arm's licensing model, broad silicon partner ecosystem, energy-efficient implementations and scalable profiles helped it become widely used in mobile, embedded and increasingly server systems. The ecosystem and implementation choices matter as much as RISC principles.

**Interview takeaway:** RISC and CISC describe ISA design tendencies, not a universal performance ranking. A64, Thumb and x86 have different encoding and execution characteristics.

### What are the Cortex-M profiles and how do they differ? {E}
Cortex-M is Arm's microcontroller processor family. Different cores implement different M-profile architecture versions and trade performance, cost, security and deterministic control features.

#### 1. Representative cores

| Core | Typical purpose |
|---|---|
| M0/M0+ | Small, low-power control |
| M3 | General-purpose embedded control |
| M4 | DSP-oriented control; optional FPU |
| M7 | Higher performance, often cache and TCM |
| M23 | Small Armv8-M devices with optional security features |
| M33 | General Armv8-M control, optional DSP/FPU and TrustZone |
| M55/M85 | Newer high-performance DSP/ML-oriented M-profile designs |

Exact MPU, FPU, cache, security and debug capabilities depend on the implemented core configuration and SoC.

#### 2. Example selection

A low-cost button controller may need only M0+. A motor-control design may benefit from M4 DSP instructions. A signal-processing or ML workload may need a more capable core and accelerator.

#### 3. Common characteristics

Cortex-M uses Thumb instruction encodings, an NVIC-based exception model, and hardware exception stacking. It commonly runs bare-metal firmware or an RTOS.

**Interview takeaway:** Cortex-M is a processor family, not a single set of optional peripherals. Confirm capabilities from the actual core and device reference manuals.

### What are the differences between Cortex-M, Cortex-R and Cortex-A, and why can't a Cortex-M0+ run Linux? {M}
Cortex-A targets application computing, Cortex-R targets real-time and safety-oriented processing, and Cortex-M targets microcontrollers.

| Profile | Typical use | Memory protection / translation |
|---|---|---|
| Cortex-A | Linux, Android, application workloads | MMU common |
| Cortex-R | Storage, automotive, deterministic control | MPU or MMU depending on core |
| Cortex-M | Bare metal, RTOS, low-power control | MPU on supported implementations |

#### 1. Why ordinary Linux needs more than Cortex-M0+

Conventional Linux distributions expect features such as virtual memory, protected processes, sufficient RAM, a supported architecture/exception model and platform drivers. Cortex-M0+ has no full virtual-memory MMU and is designed around a different exception and memory model. Typical M0+ devices also have very limited RAM.

Linux has no-MMU configurations on supported architectures/platforms, so absence of an MMU alone does not make all Linux variants impossible. It does not mean an arbitrary Cortex-M0+ can boot standard Linux.

#### 2. Practical examples

- Cortex-A53: embedded Linux and Android.
- Cortex-R: timing-sensitive storage or control processing.
- Cortex-M4: sensor acquisition, motor control or RTOS tasks.

**Interview takeaway:** Select a profile based on workload and timing requirements. Don't equate all Cortex-M cores or all Cortex-R cores with one memory-protection configuration.

### What are the Cortex-M core registers? {M}
Cortex-M exposes general-purpose registers, stack pointers, program control registers and exception-mask registers.

#### 1. Core register groups

| Register | Purpose |
|---|---|
| R0–R12 | General-purpose values and addresses |
| R13 (SP) | Current stack pointer |
| R14 (LR) | Link register / exception-return information |
| R15 (PC) | Program counter |
| xPSR | Application flags, exception number and execution state |
| MSP / PSP | Main and Process Stack Pointer |
| CONTROL | Thread privilege and stack selection, as supported |
| PRIMASK / BASEPRI / FAULTMASK | Exception masking, depending on core |

#### 2. Function-call example

```asm
MOVS R0, #5
MOVS R1, #7
BL   add
// R0 contains result
```

AAPCS32 commonly uses R0–R3 for initial integer arguments and R0 for a simple integer return. Callee-saved registers must be preserved according to the ABI.

#### 3. Exception behavior

On standard Cortex-M exception entry, hardware stacks R0–R3, R12, LR, PC and xPSR, with additional state possible. The handler uses LR's EXC_RETURN encoding to initiate architectural exception return.

**Interview takeaway:** R0–R12 hold untyped bits; the instruction determines whether they represent data or addresses. Optional registers and features vary between Cortex-M cores.

### What are MSP and PSP and why are there two stack pointers? {M}
Cortex-M provides two stack pointers: the Main Stack Pointer (MSP) and the Process Stack Pointer (PSP). They allow firmware or an RTOS to separate handler stack usage from thread stack usage.

#### 1. Execution modes

| Mode | Stack selection |
|---|---|
| Reset / initial Thread mode | Normally MSP |
| Thread mode | MSP or PSP, selected by CONTROL.SPSEL |
| Handler mode | MSP |

#### 2. RTOS example

```text
Task A --> PSP points to task A stack
Task B --> PSP points to task B stack
Interrupt handlers --> MSP points to handler stack
```

When an interrupt occurs during a task using PSP, hardware saves the task's basic exception frame on the interrupted stack (PSP). The handler itself then executes using MSP. The scheduler may save remaining context and select another task's PSP.

#### 3. Why separate stacks?

Each task can have its own bounded stack while interrupt handlers share a separate main stack. This helps context switching and resource accounting. Correct sizing must include hardware exception stacking and possible floating-point state.

#### 4. CMSIS inspection

```c
uint32_t msp = __get_MSP();
uint32_t psp = __get_PSP();
```

These intrinsics read the respective stack pointers on supporting targets.

**Interview takeaway:** MSP is used in Handler mode; PSP is commonly used by RTOS tasks. Exception entry stacks onto the interrupted context's selected stack, not always MSP.

### What happens in hardware when an exception is taken on Cortex-M? {M}
When Cortex-M accepts an exception, hardware saves part of the interrupted context and fetches the handler address from the vector table. This reduces the amount of software required for interrupt entry.

#### 1. Basic exception stack frame

<div style="max-width:580px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 219" width="100%" role="img" aria-label="Basic Cortex-M exception frame, xPSR at high address and R0 at stack pointer">
<rect x="100" y="8" width="140" height="25" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="24" font-size="12" text-anchor="middle" fill="currentColor">xPSR</text><rect x="100" y="33" width="140" height="25" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="49" font-size="12" text-anchor="middle" fill="currentColor">PC</text><rect x="100" y="58" width="140" height="25" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="74" font-size="12" text-anchor="middle" fill="currentColor">LR</text><rect x="100" y="83" width="140" height="25" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="99" font-size="12" text-anchor="middle" fill="currentColor">R12</text><rect x="100" y="108" width="140" height="25" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="124" font-size="12" text-anchor="middle" fill="currentColor">R3</text><rect x="100" y="133" width="140" height="25" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="149" font-size="12" text-anchor="middle" fill="currentColor">R2</text><rect x="100" y="158" width="140" height="25" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="174" font-size="12" text-anchor="middle" fill="currentColor">R1</text><rect x="100" y="183" width="140" height="25" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="199" font-size="12" text-anchor="middle" fill="currentColor">R0</text><text x="90" y="20" font-size="10" text-anchor="end" fill="currentColor">High address</text><text x="90" y="198" font-size="10" text-anchor="end" fill="currentColor">SP →</text><path d="M258 10 V200 m-4-5 4 5 4-5" stroke="currentColor" fill="none"/><text x="265" y="106" font-size="10" fill="currentColor">Growth</text></svg></div>

The basic frame is eight words. Alignment padding, floating-point state and security extensions can add information.

#### 2. Entry sequence

1. Exception priority and masking determine acceptance.
2. Hardware saves the basic frame on the current selected stack.
3. It obtains the handler address from the vector table and sets exception state.
4. Handler mode executes using MSP; LR contains EXC_RETURN.
5. Exception return restores the saved context according to EXC_RETURN.

Software saves other registers when necessary, for example during an RTOS context switch.

**Interview takeaway:** Cortex-M hardware stacks a basic context automatically, not every register. EXC_RETURN encodes the return mode and stack/frame information.

### What is the NVIC? {E}
NVIC stands for Nested Vectored Interrupt Controller. It is part of the Cortex-M interrupt subsystem and controls external interrupt enabling, pending state, prioritization and delivery.

#### 1. Interrupt flow

```text
Peripheral event --> IRQ pending in NVIC
                    |
               Priority / mask check
                    |
               Cortex-M exception entry
                    |
               ISR services peripheral
```

Multiple interrupts may be pending simultaneously. The processor can preempt a lower-priority handler when a higher-urgency interrupt becomes eligible.

#### 2. CMSIS configuration example

```c
NVIC_SetPriority(USART1_IRQn, 3);
NVIC_ClearPendingIRQ(USART1_IRQn);
NVIC_EnableIRQ(USART1_IRQn);
```

Configure and clear the peripheral's interrupt condition separately before enabling the source as appropriate. Clearing NVIC pending does not necessarily clear the device's own interrupt flag.

#### 3. Priority convention

Lower numerical priority means higher urgency. Only a target-specific number of priority bits are implemented. Priority grouping, when supported, determines the preemption/subpriority split.

**Interview takeaway:** NVIC controls processor interrupt delivery, not peripheral event generation. Configure both the device and interrupt controller correctly.

### What are tail-chaining and late arrival? {H}
Tail-chaining and late arrival are Cortex-M exception mechanisms that reduce interrupt handling overhead.

#### 1. Tail-chaining

Without tail-chaining, finishing one ISR before accepting a pending interrupt could require restoring the original context and immediately stacking it again.

```text
Ordinary transition:
ISR A -> unstack -> stack -> ISR B

Tail-chained transition:
ISR A -> ISR B (reuse existing stacked context)
```

If another eligible exception can be serviced at exception return, hardware can transition directly without unnecessary stack-frame restoration and recreation.

#### 2. Late arrival

If a higher-urgency interrupt arrives while hardware is entering a lower-urgency exception, the processor may service the higher-urgency interrupt first. The lower-priority request remains pending for later service, subject to the architectural rules.

#### 3. Why useful?

Both mechanisms reduce unnecessary entry/exit overhead and improve interrupt responsiveness. Exact cycle counts depend on the core, memory wait states, bus conditions and exception configuration; they are not universal.

**Interview takeaway:** Tail-chaining optimizes ISR-to-ISR transitions. Late arrival allows a higher-priority request to take precedence during exception entry.

### How do interrupt priorities work on Cortex-M? Lower number means? {M}
On Cortex-M, a lower numerical interrupt-priority value represents higher urgency. Priority determines which eligible interrupt is serviced first and which handlers can preempt others.

#### 1. Example

| Interrupt | Configured priority | Urgency |
|---|---:|---|
| Timer | 1 | Highest of these |
| UART | 3 | Medium |
| GPIO | 5 | Lowest of these |

If GPIO is running and Timer becomes pending, Timer can preempt it if their preemption priorities differ and masking permits it.

#### 2. Priority grouping

On implementations supporting priority grouping, priority bits may be split into preemption priority and subpriority. Preemption priority determines nesting; subpriority helps select between pending exceptions that have equal preemption priority.

#### 3. CMSIS usage

```c
NVIC_SetPriority(TIM2_IRQn, 1);
NVIC_SetPriority(USART1_IRQn, 3);
NVIC_EnableIRQ(TIM2_IRQn);
NVIC_EnableIRQ(USART1_IRQn);
```

These values assume the device implements enough priority levels. CMSIS handles the priority-bit positioning; do not manually shift values passed to NVIC_SetPriority.

#### 4. RTOS requirement

FreeRTOS ports may prohibit high-urgency interrupts from using RTOS APIs above a configured syscall priority threshold. Follow the port's priority encoding and configuration rules.

**Interview takeaway:** Lower number means higher urgency, but preemption grouping, interrupt masks and RTOS constraints determine whether an interrupt can actually preempt another.

### What is the difference between PRIMASK, FAULTMASK and BASEPRI? {H}
PRIMASK, BASEPRI and FAULTMASK are Cortex-M special registers that control exception masking. Their availability varies by architecture; BASEPRI and FAULTMASK are absent on Cortex-M0/M0+.

| Register | Effect |
|---|---|
| PRIMASK = 1 | Masks configurable-priority exceptions |
| BASEPRI nonzero | Masks configurable exceptions at or below the specified urgency threshold |
| FAULTMASK = 1 | Masks all exceptions except NMI |

NMI and HardFault are not masked by PRIMASK or BASEPRI. BASEPRI = 0 disables BASEPRI-based masking.

#### 1. PRIMASK example

```c
uint32_t saved = __get_PRIMASK();
__disable_irq();
// Short shared-state update
__set_PRIMASK(saved);
```

This restores the prior state rather than enabling interrupts unconditionally.

#### 2. BASEPRI use

An RTOS may mask lower-urgency interrupts while allowing time-critical higher-urgency interrupts to execute. The hardware threshold uses the implemented priority field encoding, not necessarily the unshifted logical number passed to NVIC_SetPriority.

#### 3. FAULTMASK use

FAULTMASK is a specialized mechanism for carefully controlled fault-handling or recovery paths. It is not an ordinary critical-section mechanism and can prevent normal fault handling.

**Interview takeaway:** PRIMASK masks most configurable interrupts, BASEPRI selectively masks by urgency, and FAULTMASK masks nearly all exceptions. Use the platform's established synchronization APIs.

### What causes a HardFault and how do you debug one? {M}
HardFault is a Cortex-M exception that can indicate an escalation of another fault or a processor fault that cannot be handled by an enabled configurable fault handler.

#### 1. Common causes

- Invalid or forbidden memory access.
- Invalid instruction, execution state or exception return.
- Fault during exception entry or stacking.
- Stack corruption or invalid function pointer.
- Escalated MemManage, BusFault or UsageFault, where supported.

#### 2. Debugging workflow

1. Halt in HardFault_Handler using a debugger.
2. Determine which stack and frame type EXC_RETURN describes.
3. Inspect the saved PC, LR and xPSR.
4. Examine HFSR and, where implemented, CFSR and valid fault address registers.
5. Resolve the faulting instruction using the ELF and disassembly.

```sh
arm-none-eabi-addr2line -e firmware.elf -f 0x08001234
```

The address is an illustrative saved PC. Some bus faults are imprecise, so the stacked PC may not identify the exact faulting instruction.

#### 3. Basic handler strategy

Capture the fault registers and stack-frame information into a dedicated diagnostic area, if safe. Avoid ordinary logging routines that might depend on damaged stack, locks or hardware. Recover or reset according to the system's defined policy.

**Interview takeaway:** Do not simply clear HardFault and resume. Inspect the architectural fault evidence, the saved context and memory map; available registers differ across Cortex-M profiles.

### What are SVC and PendSV used for? {H}
SVC (Supervisor Call) and PendSV (Pendable Service Call) are Cortex-M exceptions commonly used by operating systems.

#### 1. SVC

```asm
SVC #0
```

SVC requests a synchronous exception. An RTOS can use it to enter a privileged service or start the first task. The handler interprets the request according to the RTOS's ABI and validates any untrusted arguments.

#### 2. PendSV

PendSV is a software-pended exception. An RTOS commonly gives it the lowest configurable urgency so that a requested context switch occurs after higher-urgency interrupt work.

```c
SCB->ICSR = SCB_ICSR_PENDSVSET_Msk;
```

Use the architecture-appropriate register and barriers through the RTOS port.

#### 3. Typical context switch

```text
SysTick / ISR / task requests reschedule
                 |
              PendSV
                 |
Save remaining outgoing task registers
Save PSP; select next task; restore PSP
                 |
Restore incoming context and exception return
```

Hardware already saves the basic exception frame. The port handles other registers, floating-point state and security requirements when applicable.

**Interview takeaway:** SVC is synchronous service entry; PendSV is deferred exception processing commonly used for task switching. SysTick may trigger scheduling but need not perform the entire switch itself.

### What is the MPU and how is it used? {M}
An MPU (Memory Protection Unit) enforces access permissions and memory attributes for configured address regions. Unlike a conventional MMU, an MPU does not provide general virtual-to-physical page translation.

#### 1. Example region configuration

| Region | Typical permissions |
|---|---|
| Firmware flash | Read/execute |
| RAM data | Read/write, execute-never |
| Peripheral MMIO | Device memory, appropriate access |
| Task stack guard | No access |

Actual regions depend on the MPU version, alignment/granularity rules and privileged background mapping configuration.

#### 2. How it works

When the CPU fetches an instruction or accesses data, the MPU checks the relevant region attributes and permissions. A prohibited access generates a fault according to the processor configuration. Correctly configured execute-never regions can prevent execution from data buffers.

#### 3. RTOS application

An MPU-aware RTOS may reprogram task-specific regions during a context switch, restricting unprivileged tasks to their own stack, buffers and approved peripherals. The OS must validate requests to privileged services.

#### 4. MPU vs MMU

| MPU | MMU |
|---|---|
| Region-based protection | Page-based translation and protection common |
| No general address translation | Virtual-to-physical mapping |
| Common in MCU systems | Common in rich OS systems |

**Interview takeaway:** An MPU can improve isolation and fault detection, but its protection is only as good as the configured regions and privilege model. It does not automatically isolate DMA masters.

### What is TrustZone for Cortex-M? {H}
Arm TrustZone for Cortex-M, introduced with Armv8-M security extensions, divides execution and resources into Secure and Non-secure security states on supporting implementations.

#### 1. Architecture

```text
Non-secure application
        |
Non-secure callable gateway (SG)
        |
Secure service --> protected memory / peripherals
        |
Return to non-secure caller
```

The Security Attribution Unit (SAU), implementation-defined attribution and platform security controllers determine which address regions and resources belong to each security state.

#### 2. Example

A non-secure application requests an operation using a protected cryptographic key. A secure service validates the request, performs the operation and returns the result without exposing the key.

#### 3. Secure gateway

Non-secure code enters approved Secure services through correctly defined Non-secure Callable regions and gateway veneers. Secure software must validate non-secure pointers, sizes and permissions before accessing caller-supplied buffers.

#### 4. Difference from Cortex-A

M-profile uses its own security state and exception architecture. Cortex-A systems commonly use a secure monitor and different exception levels; do not assume EL3 or the A-profile SMC flow exists on Cortex-M.

**Interview takeaway:** TrustZone provides hardware security attribution and controlled transitions. It is not encryption by itself and does not eliminate the need for secure firmware, validation and correct peripheral configuration.

### What is the Cortex-A53, and what are its key architectural features? {M}
Cortex-A53 is a 64-bit-capable Arm application processor implementing Armv8-A. It is designed for power-efficient application workloads and is widely used in embedded Linux SoCs.

#### 1. Key features

- Supports AArch64 and AArch32 execution states.
- In-order, dual-issue-oriented microarchitecture.
- MMU, TLB and instruction/data caches.
- Multicore configurations with cache coherency support.
- Architectural support for virtualization and security extensions, subject to implementation and platform configuration.

#### 2. Example: i.MX8 system

```text
Cortex-A53 cores
   | L1 caches
   | Shared cache / coherent interconnect
   | DDR controller --> DRAM
   | MMIO peripherals
```

Linux uses the MMU for process address spaces, exception levels for privilege, and interrupt/timer facilities for scheduling. Device DMA may use a separate IOMMU depending on the SoC.

#### 3. Contrast with Cortex-M

Cortex-A53 supports virtual memory and rich OS workloads. Cortex-M processors commonly prioritize low-cost, low-power deterministic embedded control with a different exception model.

**Interview takeaway:** Cortex-A53 is a particular Armv8-A core implementation, not the architecture itself. Cache sizes, memory interfaces and optional platform features depend on the actual SoC.

### What is a CPU cache, and how do you write cache-friendly code? {M}
A CPU cache is fast memory that stores copies of recently accessed or nearby instructions/data. It reduces accesses to slower memory by exploiting temporal and spatial locality.

#### 1. Typical hierarchy

```text
CPU --> L1 cache --> L2 / shared cache --> DRAM
         fastest        larger           slower
```

Data is commonly transferred in cache lines, not individual bytes. A miss may be satisfied by another cache or by memory.

#### 2. Cache-friendly array traversal

For a conventional C row-major array:

```c
for (size_t r = 0; r < rows; r++)
    for (size_t c = 0; c < cols; c++)
        sum += matrix[r][c];
```

Adjacent columns are contiguous in memory. Reversing the loop order can create large strides and reduce locality, especially for large matrices.

#### 3. Practical optimizations

Use contiguous data where appropriate, avoid unnecessary pointer chasing, reuse working data before eviction, and consider loop blocking for large matrices. Separate frequently modified per-core counters to avoid false sharing when measurements justify the extra padding.

#### 4. Firmware caveat

Cache sizes, line sizes and policies vary. MMIO and DMA buffers need appropriate memory attributes and cache/ownership handling; ordinary cache-friendly code does not solve device coherency.

**Interview takeaway:** Optimize memory locality and measure cache misses. The cache is transparent for ordinary coherent CPU memory but is not automatically transparent to every DMA device.

### What is the Arm memory map, and what are "DRAM holes"? {H}
The Arm system memory map describes which physical address ranges correspond to RAM, peripheral registers, ROM or other resources. The architecture defines certain address and memory-type rules; the SoC supplies the actual physical map.

#### 1. Illustrative system map

```text
0x00000000 ... boot ROM / platform regions
0x40000000 ... MMIO peripheral window
0x80000000 ... DRAM bank 0
               reserved gap / inaccessible range
               DRAM bank 1
```

These addresses are examples, not an i.MX8 or universal Arm memory map.

#### 2. What is a DRAM hole?

A DRAM hole is an address interval not usable as ordinary RAM between or within described memory banks. Causes include peripheral address windows, reserved firmware memory, secure regions, memory-controller layout and hardware address decoding.

A reserved region may physically contain DRAM but still be unavailable to the normal OS allocator.

#### 3. Linux representation

The device tree's memory nodes describe usable physical memory banks. Reserved-memory nodes describe carveouts such as firmware, secure buffers or device-specific regions. The kernel also discovers and reserves memory through its platform boot mechanisms.

```sh
cat /proc/iomem
```

This can show RAM and reserved/resource ranges, subject to permissions and kernel configuration.

**Interview takeaway:** Physical addresses are not necessarily a contiguous range of installed DRAM. Drivers must use OS-managed resources and DMA mappings instead of inventing addresses.

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
