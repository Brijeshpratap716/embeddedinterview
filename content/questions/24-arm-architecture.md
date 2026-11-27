---
slug: arm-architecture
title: ARM Architecture
icon: 🧩
level: Intermediate
order: 24
desc: AArch64 registers, instructions, exception levels, MMU, TLB, cache coherency, barriers, interrupts, TrustZone, virtualization and boot flow.
---
Quick ARM architecture interview revision for embedded Linux, BSP, firmware and systems engineers. Each question includes a short answer, step-by-step explanations, visual diagrams, code examples and interview takeaways. Assembly examples target AArch64; privileged examples require the appropriate exception level and platform configuration.

### What is ARM architecture and how do Cortex-A, R and M differ? {E}
**Short answer:** Arm is a family of instruction set architectures. Cortex-A targets application processors with an MMU, Cortex-R targets real-time systems, and Cortex-M targets microcontrollers.

<figure style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 164" width="100%" role="img" aria-label="Three processor profiles are alternatives, not stages in a pipeline." font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="10" width="206.66666666666666" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="113.33333333333333" y="39" fill="#0c4a6e" font-size="14" font-weight="600">Cortex-A</text><rect x="236.66666666666666" y="10" width="206.66666666666666" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="39" fill="#0c4a6e" font-size="14" font-weight="600">Cortex-R</text><rect x="463.3333333333333" y="10" width="206.66666666666666" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="566.6666666666666" y="39" fill="#0c4a6e" font-size="14" font-weight="600">Cortex-M</text><rect x="10" y="82" width="206.66666666666666" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="113.33333333333333" y="111" fill="#0c4a6e" font-size="14" font-weight="600">Linux / Android</text><rect x="236.66666666666666" y="82" width="206.66666666666666" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="111" fill="#0c4a6e" font-size="14" font-weight="600">Real-time control</text><rect x="463.3333333333333" y="82" width="206.66666666666666" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="566.6666666666666" y="111" fill="#0c4a6e" font-size="14" font-weight="600">Firmware / RTOS</text></svg><figcaption>Three processor profiles are alternatives, not stages in a pipeline.</figcaption></figure>

```asm
ADD X0, X1, X2 // AArch64 example
```

**1. Architecture vs processor**

The ISA defines instructions, registers and the programmer-visible behavior. A processor implementation defines its pipeline, cache sizes and performance. Two cores implementing the same ISA may have very different hardware.

| Profile | Typical use | Example |
|---|---|---|
| Cortex-A | Linux, Android, applications | Cortex-A55 |
| Cortex-R | Predictable real-time control | Cortex-R52 |
| Cortex-M | Low-power firmware and RTOS | Cortex-M4 |

**2. Practical example:** An Android display driver typically runs on Cortex-A; a motor controller might use Cortex-M. Cortex-R often appears in safety-critical controllers. The profiles are alternatives, not sequential stages.

**Interview takeaway:** Arm architecture is the software-visible contract; Cortex is a family of processor designs.

#### How to select an ARM profile for a real product

| Example workload | Suitable profile | Reason |
|---|---|---|
| Linux graphics and networking | Cortex-A | Virtual memory, rich operating systems, application performance |
| Deadline-sensitive storage or control | Cortex-R | Real-time-oriented implementation and memory architecture |
| Small sensor and motor-control firmware | Cortex-M | Low-overhead exception model, MCU integration |

The profile describes an architectural family, not a fixed feature list. For example, Cortex-R implementations differ in MMU/MPU support, and Cortex-M implementations differ in FPU, MPU, TrustZone and cache support. Cortex-A can also run bare-metal software. The actual SoC adds interconnect, memory controllers, peripherals, power domains and interrupt hardware. Choose the processor using measured performance, worst-case latency, memory, isolation and power requirements.

### What is AArch64 versus AArch32? {E}
**Short answer:** AArch64 is the 64-bit execution state using A64 instructions. AArch32 is the 32-bit state using A32 or T32 instructions, where supported. AArch64 instructions are 32 bits wide.

<figure style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 164" width="100%" role="img" aria-label="Alternative execution states; support for AArch32 is implementation-dependent." font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="10" width="320" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="170" y="39" fill="#0c4a6e" font-size="14" font-weight="600">AArch32: A32 / T32</text><rect x="350" y="10" width="320" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="510" y="39" fill="#0c4a6e" font-size="14" font-weight="600">AArch64: A64</text><rect x="10" y="82" width="320" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="170" y="111" fill="#0c4a6e" font-size="14" font-weight="600">R0–R15 (32-bit)</text><rect x="350" y="82" width="320" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="510" y="111" fill="#0c4a6e" font-size="14" font-weight="600">X0–X30 (64-bit)</text></svg><figcaption>Alternative execution states; support for AArch32 is implementation-dependent.</figcaption></figure>

```asm
ADD W0, W1, W2 // 32-bit operation in AArch64
ADD X0, X1, X2 // 64-bit operation
```

**1. Register and instruction differences**

| Feature | AArch32 | AArch64 |
|---|---|---|
| General registers | R0–R12 plus SP, LR, PC | X0–X30 plus SP |
| Instruction sets | A32, T32 | A64 |
| Integer register width | 32 bits | 64 bits |

**2. Example:** X1 = 0x1234567800000001. Reading W1 returns 1. Writing W1 = 2 makes X1 = 2, because a W-register write clears the upper half.

**3. Compatibility:** A 64-bit CPU need not implement AArch32 at every exception level. Running 32-bit applications also requires kernel and userspace support.

**Interview takeaway:** Execution state determines the instruction set and register model; it does not by itself determine physical address width.

#### Register and instruction examples

```asm
// AArch64 (A64)
ADD X0, X1, X2
LDR W3, [X4]

// AArch32 (example A32 syntax)
ADD R0, R1, R2
LDR R3, [R4]
```

AArch64 provides 31 general-purpose X registers with 32-bit W views; AArch32 provides a different register and execution model, including R13/SP, R14/LR and R15/PC. A64 instructions are fixed 32-bit encodings even though many operands are 64 bits. Thumb instructions can use 16-bit or 32-bit encodings. An AArch64 kernel may support 32-bit userspace if the CPU and kernel configuration support AArch32 at EL0. Executable format, ABI, system-call convention and libraries must match the execution state. Do not equate 64-bit registers with a full 64-bit implemented virtual or physical address range.

### Do ARM64 registers contain data or addresses? {E}
**Short answer:** Both. X0–X30 hold 64-bit values; instructions determine whether those bits represent data or an address. Writing Wn zeroes the upper 32 bits of Xn.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="X1: 0x1000 to Memory: [0x1000] = 50 to X2: 50" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="108.33333333333333" y="36" font-size="13" font-weight="600" fill="#172554">X1</text><text x="108.33333333333333" y="56" font-size="11" fill="#334155">0x1000</text><path d="M209.66666666666666 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="231.66666666666666" y="12" width="196.66666666666666" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="330" y="36" font-size="13" font-weight="600" fill="#172554">Memory</text><text x="330" y="56" font-size="11" fill="#334155">[0x1000] = 50</text><path d="M431.3333333333333 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="453.3333333333333" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="551.6666666666666" y="36" font-size="13" font-weight="600" fill="#172554">X2</text><text x="551.6666666666666" y="56" font-size="11" fill="#334155">50</text></svg></div>

```asm
MOV X1, #0x1000
LDR X2, [X1] // assuming valid readable address
ADD X3, X2, #1
```

**1. Actual data:** MOV X1, #10 puts the number 10 directly in X1. ADD operates on register values without reading data memory.

**2. Address:** LDR X2, [X1] interprets X1 as an address and loads eight bytes. If the MMU is enabled, the address is translated before accessing memory.

```c
long a = 50;
long *p = &a;
long b = *p;
```

Conceptually X1 holds p and X2 holds b on typical ARM64 Linux.

| Instruction | Meaning |
|---|---|
| MOV X2, X1 | Copy bits |
| LDR X2, [X1] | Read pointed-to memory |
| STR X2, [X1] | Write pointed-to memory |

**Interview takeaway:** Registers are not inherently typed as pointers or integers; the instruction decides how to use their bits.

#### Trace the values through a real load and store

Assume X1 contains the valid mapped virtual address 0x1000 and an eight-byte value 50 is stored there.

```asm
LDR X2, [X1]      // X2 becomes 50
ADD X2, X2, #5   // X2 becomes 55
STR X2, [X1]      // memory at that address becomes 55
```

X1 remains 0x1000 throughout. The instruction's addressing mode determines the effective address, and its operand width determines the number of bytes read or written. LDR W2 reads four bytes and zero-extends into X2; LDRSW X2 reads a signed 32-bit value and sign-extends it. For an invalid or forbidden address, LDR may generate an exception rather than return a value. With an enabled MMU, X1 usually contains a virtual address, not a DRAM physical address. A compiler can keep a C object entirely in registers, so the C example does not guarantee actual loads and stores in optimized machine code.

### What are SP, PC, LR and PSTATE? {E}
**Short answer:** SP is the stack pointer, PC tracks instruction execution, X30 is the conventional link register, and PSTATE holds execution state including NZCV flags and interrupt masks. PC is not an ordinary general-purpose register in A64.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="BL: Function call to X30: Return address to RET: Return" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="108.33333333333333" y="36" font-size="13" font-weight="600" fill="#172554">BL</text><text x="108.33333333333333" y="56" font-size="11" fill="#334155">Function call</text><path d="M209.66666666666666 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="231.66666666666666" y="12" width="196.66666666666666" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="330" y="36" font-size="13" font-weight="600" fill="#172554">X30</text><text x="330" y="56" font-size="11" fill="#334155">Return address</text><path d="M431.3333333333333 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="453.3333333333333" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="551.6666666666666" y="36" font-size="13" font-weight="600" fill="#172554">RET</text><text x="551.6666666666666" y="56" font-size="11" fill="#334155">Return</text></svg></div>

```asm
BL function
// ...
function:
    RET
```

**1. Special register roles**

| Register | Purpose |
|---|---|
| SP | Current stack location |
| PC | Address associated with instruction execution |
| X30 / LR | Return address after BL |
| PSTATE | Flags, interrupt masks and execution state |

**2. Function call:** BL places the next instruction address in X30 and branches to the function. RET normally branches to X30. A nested call overwrites LR, so a non-leaf function generally saves it if it needs it later.

**3. Practical note:** AArch64 does not expose PC as an ordinary general-purpose register. ADR and ADRP can compute PC-relative addresses.

**Interview takeaway:** SP manages stack storage, LR supports returns, PC controls execution and PSTATE records processor state.

#### Function call versus exception return

```asm
BL  function       // X30 receives address of next instruction
// execution continues here after RET
function:
    ADD X0, X0, #1
    RET            // normally branches to X30
```

A non-leaf function generally preserves its incoming return address before executing another BL. SP points into the active stack; the normal AAPCS64 stack alignment at public interfaces is 16 bytes. PC is not a general-purpose X register, but PC-relative instructions such as ADR and ADRP construct addresses relative to instruction execution.

An exception uses a separate mechanism: hardware writes ELR_ELx and SPSR_ELx for the target exception level, and ERET restores the saved return state. X30 is not the exception return register. PSTATE contains flags and execution controls (such as NZCV and exception masks); selected fields are accessed using architectural system-register interfaces, not as one ordinary writable GPR.

### What is a load-store architecture? {E}
**Short answer:** Arithmetic normally uses registers; explicit loads and stores transfer data between registers and memory.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="Memory: Load to Registers: ALU operation to Memory: Store" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="108.33333333333333" y="36" font-size="13" font-weight="600" fill="#172554">Memory</text><text x="108.33333333333333" y="56" font-size="11" fill="#334155">Load</text><path d="M209.66666666666666 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="231.66666666666666" y="12" width="196.66666666666666" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="330" y="36" font-size="13" font-weight="600" fill="#172554">Registers</text><text x="330" y="56" font-size="11" fill="#334155">ALU operation</text><path d="M431.3333333333333 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="453.3333333333333" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="551.6666666666666" y="36" font-size="13" font-weight="600" fill="#172554">Memory</text><text x="551.6666666666666" y="56" font-size="11" fill="#334155">Store</text></svg></div>

```asm
LDR W0, [X1]
ADD W0, W0, #1
STR W0, [X1]
```

**1. How an increment works:** Assume X1 points to a 32-bit integer containing 10. LDR reads 10 into W0; ADD produces 11; STR writes 11 back. The arithmetic instruction does not directly modify RAM.

```c
(*p)++;
```

**2. Access size:** LDRB reads one byte, LDRH two bytes, LDR Wn four bytes and LDR Xn eight bytes. Stores have corresponding variants.

**3. Concurrency:** A load, add and store sequence is not atomic. Two cores can read the same old value and lose one update. Use an atomic operation when required.

**Interview takeaway:** Explicit load/store instructions move data between memory and registers, while the ALU normally operates on registers.

#### Example: increment a memory-mapped value

```asm
LDR W0, [X1]       // load 32-bit value into register
ADD W0, W0, #1    // arithmetic on register
STR W0, [X1]       // store 32-bit result
```

The ADD does not access the addressed memory; it uses register operands. This design keeps common arithmetic separate from data-transfer instructions. Instructions such as LDP/STP transfer pairs, and atomic memory instructions are additional architectural operations rather than evidence that all arithmetic directly accesses memory.

The three-instruction increment is not atomic. Two cores could load the same old value before either stores a result. For shared RAM use suitable atomics or a lock. For MMIO, an apparently simple load/add/store can be wrong if a register has read-to-clear or write-one-to-clear semantics. Use documented register operations and OS accessors.

### What are ARM exception levels EL0 to EL3? {M}
**Short answer:** EL0 runs applications, EL1 normally runs the OS kernel, EL2 supports virtualization, and EL3 supports secure monitor functions. Availability depends on implementation.

<figure style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 308" width="100%" role="img" aria-label="Privilege hierarchy. An exception is routed to its configured target; it need not traverse every level." font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="10" width="660" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="39" fill="#0c4a6e" font-size="14" font-weight="600">EL3 — secure monitor (if present)</text><rect x="10" y="82" width="660" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="111" fill="#0c4a6e" font-size="14" font-weight="600">EL2 — hypervisor (if present)</text><rect x="10" y="154" width="660" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="183" fill="#0c4a6e" font-size="14" font-weight="600">EL1 — OS kernel</text><rect x="10" y="226" width="660" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="255" fill="#0c4a6e" font-size="14" font-weight="600">EL0 — application</text></svg><figcaption>Privilege hierarchy. An exception is routed to its configured target; it need not traverse every level.</figcaption></figure>

```asm
MRS X0, CurrentEL // privileged code
```

**1. Privilege levels**

| Level | Typical software |
|---|---|
| EL0 | Application |
| EL1 | Linux kernel and drivers |
| EL2 | Hypervisor |
| EL3 | Secure monitor |

**2. Transition example:** A userspace syscall executes SVC, normally entering EL1. The kernel validates arguments, performs work and returns with ERET. A guest may encounter traps routed to EL2.

**3. Why isolation matters:** EL0 cannot freely program privileged system registers or access kernel-only mappings. An illegal operation can cause an exception.

**Interview takeaway:** Exception levels provide privilege separation. Higher ELs are not stages that every instruction passes through; routing depends on configuration.

#### Example: a Linux guest under an ARM hypervisor

```text
Guest application (EL0) -- SVC --> guest kernel (EL1)
Guest kernel -- selected trap / stage-2 fault --> hypervisor (EL2)
Hypervisor -- ERET --> guest execution
Secure monitor (EL3), when present, handles defined secure transitions
```

The ordinary guest syscall need not exit to EL2. Hypervisor control registers determine which operations trap. The guest's stage-1 tables manage guest virtual addresses, while the hypervisor's stage-2 tables restrict access to host physical memory.

A conventional non-VHE host kernel runs at EL1, but with VHE the host kernel can execute at EL2. Not every CPU implements every exception level or security extension. EL0 cannot directly modify privileged translation registers; entry through the configured exception mechanism is required. Exception level describes privilege within an execution context, whereas Secure/Non-secure state concerns security attribution.

### How does a system call work on ARM64 Linux? {M}
**Short answer:** Userspace puts the syscall number in X8 and arguments in X0–X5, then executes SVC. The kernel handles the synchronous exception and returns a result in X0.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="EL0: SVC #0 to EL1: Syscall handler to EL0: ERET / result" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="108.33333333333333" y="36" font-size="13" font-weight="600" fill="#172554">EL0</text><text x="108.33333333333333" y="56" font-size="11" fill="#334155">SVC #0</text><path d="M209.66666666666666 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="231.66666666666666" y="12" width="196.66666666666666" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="330" y="36" font-size="13" font-weight="600" fill="#172554">EL1</text><text x="330" y="56" font-size="11" fill="#334155">Syscall handler</text><path d="M431.3333333333333 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="453.3333333333333" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="551.6666666666666" y="36" font-size="13" font-weight="600" fill="#172554">EL0</text><text x="551.6666666666666" y="56" font-size="11" fill="#334155">ERET / result</text></svg></div>

```asm
MOV X8, #172 // Linux arm64 getpid
SVC #0       // X0 = result
```

**1. Userspace preparation:** libc follows the Linux AArch64 syscall ABI: X8 contains the syscall number, X0–X5 contain up to six arguments.

**2. Kernel entry:** SVC raises a synchronous exception. Hardware saves return state; the kernel entry code saves registers and dispatches the syscall.

**3. Return:** The kernel places a result in X0 and restores userspace execution. Raw Linux syscall failures are negative error numbers; libc typically converts these into -1 and sets errno.

```c
#include <unistd.h>
pid_t pid = getpid();
```

**Interview takeaway:** A syscall is a controlled privilege transition, not an ordinary function call into kernel memory.

#### Complete example: write(fd, buf, len)

For a raw AArch64 Linux write syscall (number 64 in the standard arm64 ABI):

```asm
// X0 = fd, X1 = user buffer address, X2 = byte count
MOV X8, #64
SVC #0
// X0 = bytes written or raw negative errno
```

At a typical EL0-to-EL1 entry, the CPU selects the lower-EL AArch64 synchronous exception vector. Linux entry code saves the userspace register state, checks the syscall number and invokes the relevant implementation. For write, the VFS resolves the file descriptor to a file and dispatches through the appropriate file operations. The kernel validates user-provided ranges and uses appropriate user-access helpers when copying data. A syscall can block and the scheduler may run another task before it returns. It can return fewer bytes than requested, so userspace handles partial writes.

A raw negative errno is not the same as the libc return convention. The C library generally returns -1 and sets thread-local errno for this interface. Exact Linux function names and entry paths vary by kernel release.

### What happens when an ARM64 exception occurs? {M}
**Short answer:** Hardware saves the return address and prior PSTATE in ELR_ELx and SPSR_ELx, selects a vector using VBAR_ELx, and transfers control. Software saves needed general registers; ERET restores the saved execution state.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="Exception: Hardware state save to Vector: VBAR_ELx to Handler: Save GPRs to ERET: Resume" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="141.25" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="80.625" y="36" font-size="13" font-weight="600" fill="#172554">Exception</text><text x="80.625" y="56" font-size="11" fill="#334155">Hardware state save</text><path d="M154.25 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="176.25" y="12" width="141.25" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="246.875" y="36" font-size="13" font-weight="600" fill="#172554">Vector</text><text x="246.875" y="56" font-size="11" fill="#334155">VBAR_ELx</text><path d="M320.5 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="342.5" y="12" width="141.25" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="413.125" y="36" font-size="13" font-weight="600" fill="#172554">Handler</text><text x="413.125" y="56" font-size="11" fill="#334155">Save GPRs</text><path d="M486.75 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="508.75" y="12" width="141.25" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="579.375" y="36" font-size="13" font-weight="600" fill="#172554">ERET</text><text x="579.375" y="56" font-size="11" fill="#334155">Resume</text></svg></div>

```asm
MRS X0, ESR_EL1 // exception syndrome
MRS X1, ELR_EL1 // exception return address
```

**1. Exception types:** Synchronous exceptions include system calls and faults. IRQ and FIQ are interrupt classes; SError reports certain asynchronous errors.

**2. Hardware entry:** The target EL's ELR and SPSR save return address and prior processor state. VBAR identifies the vector table, with the slot determined by exception type and origin.

**3. Software handler:** Kernel entry code saves general registers as required. ESR describes synchronous fault causes; FAR may contain the faulting address when valid.

**4. Return:** ERET restores execution state using ELR and SPSR. Depending on the cause, software may retry, resume elsewhere or terminate the process.

**Interview takeaway:** Hardware saves essential exception state, but software is responsible for preserving general-purpose registers as needed.

#### Vector-table selection and saved registers

AArch64 vector tables have 16 slots, each 128 bytes, grouped by exception origin (current EL with SP0, current EL with SPx, lower EL in AArch64, lower EL in AArch32) and type (synchronous, IRQ, FIQ, SError). The table base is aligned as required by the architecture.

For a normal AArch64 EL0 synchronous fault handled at EL1, the vector starts at VBAR_EL1+0x400. A data abort can provide an exception class and syndrome in ESR_EL1, and the faulting virtual address in FAR_EL1 when valid. ELR_EL1 identifies the architectural return address. Linux examines the cause and decides whether to repair the mapping, send a signal or report a kernel fault.

An asynchronous IRQ follows a different vector slot and uses the interrupt-controller interface to identify/acknowledge the source. Unlike Cortex-M's basic automatic register stack frame, AArch64 exception-entry software explicitly saves the general registers needed for the handler and return.

### What is the MMU? {M}
**Short answer:** The MMU translates virtual addresses into physical addresses using translation tables and enforces access permissions and memory attributes.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="CPU: Virtual address to MMU / TLB: Translation to Memory: Physical address" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="108.33333333333333" y="36" font-size="13" font-weight="600" fill="#172554">CPU</text><text x="108.33333333333333" y="56" font-size="11" fill="#334155">Virtual address</text><path d="M209.66666666666666 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="231.66666666666666" y="12" width="196.66666666666666" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="330" y="36" font-size="13" font-weight="600" fill="#172554">MMU / TLB</text><text x="330" y="56" font-size="11" fill="#334155">Translation</text><path d="M431.3333333333333 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="453.3333333333333" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="551.6666666666666" y="36" font-size="13" font-weight="600" fill="#172554">Memory</text><text x="551.6666666666666" y="56" font-size="11" fill="#334155">Physical address</text></svg></div>

```asm
MRS X0, TTBR0_EL1 // privileged: table base
```

**1. Why translation is needed:** Two processes can use the same virtual address while mapping to different physical pages. The MMU also enforces user/kernel access, read/write and execute permissions.

**2. Example:** With a 4 KiB page, virtual address 0x1234 has offset 0x234. If its virtual page maps to physical base 0x8000, the resulting physical address is 0x8234.

| System register | Role at EL1 |
|---|---|
| TTBR0_EL1 / TTBR1_EL1 | Translation table bases |
| TCR_EL1 | Translation configuration |
| MAIR_EL1 | Memory attribute encodings |
| SCTLR_EL1 | Controls including MMU enable |

**3. Failure:** An invalid mapping or permission violation raises a fault. Linux may resolve a valid demand-page fault or signal the process.

**Interview takeaway:** The MMU provides translation, isolation and memory attributes; the TLB accelerates translation.

#### Worked four-level page-table example

Assume 48-bit virtual addressing, 4 KiB granules and eight-byte translation descriptors.

```text
VA [47:39] [38:30] [29:21] [20:12] [11:0]
       L0      L1      L2      L3     offset
```

Each level uses a nine-bit index (512 entries). TTBR0_EL1 or TTBR1_EL1 selects the applicable root. A table descriptor supplies the base of the next table; a valid terminal page descriptor supplies the physical page base and attributes. Supported block descriptors can terminate the walk at a higher level. The low 12-bit offset is combined with the page base for a 4 KiB page.

Attributes control read/write privilege, executable permission, cacheability and shareability. An invalid descriptor can cause a translation fault; a valid mapping with insufficient permission can cause a permission fault. TLB entries cache the result, so the hardware need not repeat the complete walk for each load. The granule and address width determine the actual table layout; 4 KiB and four levels are examples, not universal ARM64 requirements.

### What is a TLB and what happens on a TLB miss? {M}
**Short answer:** The TLB caches address translations. On a miss, hardware normally walks translation tables; a valid translation can refill the TLB. Invalid mappings or permission violations can cause a fault.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="Virtual address: TLB lookup to Miss: Table walk to Physical address: Access" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="108.33333333333333" y="36" font-size="13" font-weight="600" fill="#172554">Virtual address</text><text x="108.33333333333333" y="56" font-size="11" fill="#334155">TLB lookup</text><path d="M209.66666666666666 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="231.66666666666666" y="12" width="196.66666666666666" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="330" y="36" font-size="13" font-weight="600" fill="#172554">Miss</text><text x="330" y="56" font-size="11" fill="#334155">Table walk</text><path d="M431.3333333333333 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="453.3333333333333" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="551.6666666666666" y="36" font-size="13" font-weight="600" fill="#172554">Physical address</text><text x="551.6666666666666" y="56" font-size="11" fill="#334155">Access</text></svg></div>

```asm
LDR X0, [X1] // translation performed if needed
```

**1. TLB hit:** The CPU finds a cached translation and permissions, avoiding a page-table walk.

**2. TLB miss:** The hardware walks translation tables in memory. If a valid entry is found, it can cache the translation and proceed. A TLB miss alone is not a page fault.

**3. Page fault:** A missing or forbidden mapping can trigger a synchronous exception. Linux handles legitimate demand paging or rejects illegal access.

| TLB | CPU data cache |
|---|---|
| Stores address translations | Stores memory contents |
| Avoids table walks | Avoids slower data accesses |

**4. Context switches:** Address Space Identifiers (ASIDs) help distinguish translations belonging to different processes. Kernel mapping changes may require TLB invalidation.

**Interview takeaway:** TLB miss means translation is not cached; page fault means the access cannot proceed with the current translation state.

#### A TLB miss with a valid mapping versus a page fault

Consider two successive accesses to VA 0x40001234 with a 4 KiB page. On the first access the TLB may lack a matching translation. Hardware walks the tables, finds the physical page base 0x80000000, checks attributes and proceeds to PA 0x80000234. The second access can reuse the translation. A page-table walk can itself hit CPU caches or dedicated walk caches rather than reading DRAM for every descriptor.

If the terminal descriptor is invalid, the CPU reports a translation fault; Linux checks whether the address belongs to a valid VMA and can install a mapping. If the address is outside a permitted region, a userspace access may instead result in SIGSEGV. Permission faults can also implement legitimate copy-on-write.

For a TLB with 64 entries, 4 KiB pages cover 256 KiB of distinct base-page mappings; larger mappings can increase reach. This simplified calculation ignores multiple TLB levels and replacement behavior.

### How does a memory access travel from CPU to DRAM? {M}
When a user-space process accesses memory, the CPU generates a **virtual address**, which is translated into a **physical address** by the MMU. The CPU then checks the cache hierarchy before accessing DRAM.

#### 1. Complete memory access flow

<figure style="max-width:480px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 530" width="100%" role="img" aria-label="Memory access flow" font-family="system-ui,sans-serif"><defs><marker id="dram-arrow" markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto"><path d="M0 0 L6 3 L0 6Z" fill="#64748b"/></marker></defs><rect x="20" y="8" width="226" height="46" rx="7" fill="#e0f2fe" stroke="#64748b"/><text x="133" y="26" font-size="12" font-weight="600" fill="#0f172a" text-anchor="middle">User-space process</text><text x="133" y="42" font-size="10" fill="#334155" text-anchor="middle">int x = *ptr;</text><path d="M133 54 V67" stroke="#64748b" fill="none" marker-end="url(#dram-arrow)"/><rect x="20" y="69" width="226" height="46" rx="7" fill="#e0f2fe" stroke="#64748b"/><text x="133" y="87" font-size="12" font-weight="600" fill="#0f172a" text-anchor="middle">CPU / Load Store Unit</text><text x="133" y="103" font-size="10" fill="#334155" text-anchor="middle">Generates virtual address</text><path d="M133 115 V128" stroke="#64748b" fill="none" marker-end="url(#dram-arrow)"/><rect x="20" y="130" width="226" height="46" rx="7" fill="#e0f2fe" stroke="#64748b"/><text x="133" y="148" font-size="12" font-weight="600" fill="#0f172a" text-anchor="middle">MMU / TLB</text><text x="133" y="164" font-size="10" fill="#334155" text-anchor="middle">Virtual → Physical address</text><path d="M133 176 V189" stroke="#64748b" fill="none" marker-end="url(#dram-arrow)"/><rect x="20" y="191" width="226" height="46" rx="7" fill="#e0f2fe" stroke="#64748b"/><text x="133" y="209" font-size="12" font-weight="600" fill="#0f172a" text-anchor="middle">L1 Data Cache</text><text x="133" y="225" font-size="10" fill="#334155" text-anchor="middle">Fastest data cache</text><path d="M133 237 V250" stroke="#64748b" fill="none" marker-end="url(#dram-arrow)"/><rect x="20" y="252" width="226" height="46" rx="7" fill="#e0f2fe" stroke="#64748b"/><text x="133" y="270" font-size="12" font-weight="600" fill="#0f172a" text-anchor="middle">L2 Cache</text><text x="133" y="286" font-size="10" fill="#334155" text-anchor="middle">Larger, slower cache</text><path d="M133 298 V311" stroke="#64748b" fill="none" marker-end="url(#dram-arrow)"/><rect x="20" y="313" width="226" height="46" rx="7" fill="#e0f2fe" stroke="#64748b"/><text x="133" y="331" font-size="12" font-weight="600" fill="#0f172a" text-anchor="middle">L3 / Last Level Cache</text><text x="133" y="347" font-size="10" fill="#334155" text-anchor="middle">Often shared across cores</text><path d="M133 359 V372" stroke="#64748b" fill="none" marker-end="url(#dram-arrow)"/><rect x="20" y="374" width="226" height="46" rx="7" fill="#e0f2fe" stroke="#64748b"/><text x="133" y="392" font-size="12" font-weight="600" fill="#0f172a" text-anchor="middle">Memory Controller</text><text x="133" y="408" font-size="10" fill="#334155" text-anchor="middle">Schedules DRAM commands</text><path d="M133 420 V443" stroke="#64748b" fill="none" marker-end="url(#dram-arrow)"/><rect x="20" y="445" width="226" height="46" rx="7" fill="#dcfce7" stroke="#16a34a"/><text x="133" y="463" font-size="12" font-weight="600" fill="#0f172a" text-anchor="middle">DRAM / DDR RAM</text><text x="133" y="479" font-size="9" fill="#334155" text-anchor="middle">Channel → Rank → Bank → Row → Column</text><path d="M246 153 H264 V181 H246" stroke="#d97706" fill="none" stroke-dasharray="4 2" marker-end="url(#dram-arrow)"/><g font-size="10" fill="#b45309"><text x="270" y="150">TLB miss</text><text x="270" y="163">Page table</text><text x="270" y="176">walk</text></g><g font-size="9" fill="#64748b"><text x="143" y="247">Miss</text><text x="143" y="308">Miss</text><text x="143" y="369">Miss</text></g><path d="M20 468 H8 V92 H18" stroke="#16a34a" stroke-width="1.5" fill="none" marker-end="url(#dram-arrow)"/><text x="133" y="514" text-anchor="middle" font-size="11" fill="#15803d">Requested data returns to CPU</text></svg><figcaption>Simplified read path for a typical modern CPU. Address translation and cache lookup may overlap.</figcaption></figure>

#### 2. Step-by-step explanation

**Step 1: User process generates a memory request**

```c
int a = 10;
int *ptr = &a;
int x = *ptr;
```

Assuming the compiler generates an actual load instruction, the CPU executes it to read memory.

For ARM64:

```asm
LDR W0, [X1]
```

Here, `X1` contains the virtual address.

**Step 2: MMU checks the TLB**

The Memory Management Unit (MMU) checks the Translation Lookaside Buffer (TLB).

- **TLB hit:** Physical page address is obtained directly.
- **TLB miss:** Hardware performs a page table walk on modern ARM64 and x86 processors.

The TLB caches address translations, not actual application data.

**Step 3: Page table walk**

For a typical Linux ARM64 system using four-level page tables:

```text
PGD → PUD → PMD → PTE
```

The MMU uses the page table base register (`TTBR0_EL1` on ARM64 for user-space addresses) to locate the page tables.

The page table entry contains information such as the physical page frame, access permissions and memory attributes.

**Step 4: Virtual-to-physical address translation**

For a 4 KB page:

<figure style="max-width:480px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 138" width="100%" role="img" aria-label="Virtual to physical address translation" font-family="system-ui,sans-serif" text-anchor="middle"><g fill="#dbeafe" stroke="#3b82f6"><rect x="4" y="5" width="208" height="37" rx="4"/><rect x="4" y="90" width="208" height="37" rx="4"/></g><g fill="#dcfce7" stroke="#16a34a"><rect x="214" y="5" width="102" height="37" rx="4"/><rect x="214" y="90" width="102" height="37" rx="4"/></g><g fill="#0f172a" font-size="11"><text x="108" y="20">Virtual page number</text><text x="108" y="34">0x12345</text><text x="265" y="20">Page offset</text><text x="265" y="34">0x678</text><text x="108" y="105">Physical page number</text><text x="108" y="119">0xABCDE</text><text x="265" y="105">Same offset</text><text x="265" y="119">0x678</text></g><path d="M108 42 V87" stroke="#3b82f6" stroke-width="1.5"/><path d="M103 81 L108 88 L113 81" fill="#3b82f6"/><rect x="56" y="52" width="104" height="24" rx="4" fill="#64748b"/><text x="108" y="68" font-size="11" fill="white">MMU translation</text><path d="M265 42 V88" stroke="#16a34a" stroke-dasharray="3 2"/></svg><figcaption>Virtual address — example</figcaption></figure>

Virtual address: `0x12345678`

Physical address: `0xABCDE678`

The page number changes, but the page offset remains the same.

**Step 5: Page fault handling (if required)**

If the page is not mapped or access permissions are violated, the CPU generates a synchronous exception.

The Linux kernel page fault handler may allocate a physical page, load data from a file or swap, update the page table and retry the instruction.

If the access is invalid and cannot be resolved, Linux typically sends `SIGSEGV` to the process.

**Step 6: CPU checks the cache hierarchy**

Once the address translation and permission checks are resolved, the CPU obtains data through the cache hierarchy.

| Memory level | Approximate latency |
|---|---:|
| L1 cache | 1 ns |
| L2 cache | 3–5 ns |
| L3 cache | 10–30 ns |
| DRAM | 60–120 ns |

These are illustrative values and vary by processor.

If data is available in a cache, DRAM access is unnecessary. Data may also be obtained from another CPU core's cache through the cache-coherency mechanism.

**Step 7: SoC interconnect and memory controller**

If the cache hierarchy cannot supply the data, the request travels through the system interconnect to the memory controller.

On ARM-based SoCs, this may involve an AXI or coherent interconnect.

The memory controller translates the system physical address into DRAM-specific addressing:

- Channel
- Rank
- Bank
- Row
- Column

**Step 8: DRAM access**

The memory controller issues DDR commands:

| Command | Purpose |
|---|---|
| `ACTIVATE` | Opens a row into the row buffer |
| `READ` | Reads the requested column data |
| `WRITE` | Writes data into the selected location |
| `PRECHARGE` | Closes the active row |

If the required row is already open, the controller can avoid another activation.

**Step 9: Data returns to CPU**

The requested data returns through the memory controller and interconnect. It typically fills the appropriate caches as a cache line (commonly 64 bytes), and the requested value is delivered to the CPU register.

The instruction completes.

#### 3. What happens during a memory write?

For a typical write-back, write-allocate cache:

```c
*ptr = 20;
```

```text
CPU → Store Buffer → L1 Cache
                         ↓
                    Dirty cache line
                         ↓
                 Eventual write-back
                         ↓
                  Memory Controller
                         ↓
                        DRAM
```

A CPU write does not necessarily update DRAM immediately.

#### 4. Important interview follow-up questions

| Question | Answer |
|---|---|
| Does every memory access enter kernel mode? | No, only when an exception or another kernel entry is required. |
| Does every TLB miss cause a page fault? | No, a valid page table entry can resolve it. |
| Does every cache miss access DRAM? | No, another cache level or core may supply data. |
| Where are page tables stored? | Physical memory; their entries can also be cached. |
| Who configures page tables? | The OS kernel. |
| Who translates virtual addresses? | MMU hardware. |
| Who manages DDR timing? | Memory controller. |
| Does `volatile` bypass CPU cache? | No. |

**Interview-ready answer:** A user-space memory access generates a virtual address. The MMU translates it using the TLB or a page table walk and verifies access permissions. The CPU checks its cache hierarchy. If the data cannot be supplied by caches, the request travels through the system interconnect to the memory controller, which issues DDR commands to retrieve data from DRAM. The data returns to the CPU, completing the instruction.


### What happens when malloc(4 KB) is called on ARM64 Linux? {M}
**Short answer:** The allocator may reuse a free chunk or obtain virtual memory via brk/mmap. A first write to an unbacked anonymous page can fault, causing Linux to allocate a physical page and update the mapping. Allocation is not necessarily page-aligned.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="malloc: Allocator to brk / mmap: If needed to Page fault: If unbacked to Physical page: Retry" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="141.25" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="80.625" y="36" font-size="13" font-weight="600" fill="#172554">malloc</text><text x="80.625" y="56" font-size="11" fill="#334155">Allocator</text><path d="M154.25 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="176.25" y="12" width="141.25" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="246.875" y="36" font-size="13" font-weight="600" fill="#172554">brk / mmap</text><text x="246.875" y="56" font-size="11" fill="#334155">If needed</text><path d="M320.5 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="342.5" y="12" width="141.25" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="413.125" y="36" font-size="13" font-weight="600" fill="#172554">Page fault</text><text x="413.125" y="56" font-size="11" fill="#334155">If unbacked</text><path d="M486.75 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="508.75" y="12" width="141.25" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="579.375" y="36" font-size="13" font-weight="600" fill="#172554">Physical page</text><text x="579.375" y="56" font-size="11" fill="#334155">Retry</text></svg></div>

```c
char *p = malloc(4096);
if (p) { p[0] = 'A'; free(p); }
```

**1. Allocator:** malloc is a libc function, not a syscall. It checks existing free chunks and may return a pointer without entering the kernel.

**2. Virtual memory:** If needed, glibc obtains more space through brk or mmap. The kernel creates or extends virtual mappings.

**3. First write:** A store to an unbacked anonymous page can trigger a page fault. Linux checks the VMA, allocates and zeroes physical memory as needed, updates page tables and retries the instruction.

```asm
MOV X0, #4096
BL malloc
CBZ X0, failed
MOV W1, #65
STRB W1, [X0]
failed:
```

**4. Important details:** ARM64 Linux may use 4, 16 or 64 KiB base pages. A 4096-byte allocation need not be page-aligned, and allocator metadata can touch pages before the application does. free may retain memory in the allocator.

**Interview takeaway:** Virtual allocation and physical backing are separate; demand paging often defers physical allocation until access.

#### Why a 4096-byte allocation does not equal one physical page

Suppose malloc returns virtual address 0x40001020. The requested interval of 4096 bytes ends just before 0x40002020. With 4 KiB pages, it spans two pages because the starting offset is 0x20. The allocator may already have mapped and touched either page. An initial write can generate a minor fault for anonymous demand allocation; later accesses usually reuse the established mapping.

On a Linux system, compare virtual versus resident usage using /proc/PID/maps and /proc/PID/smaps or smaps_rollup. Use getconf PAGESIZE to check the configured page size. The allocator can reuse freed chunks without returning them to the kernel immediately; a large mapping may instead be unmapped, depending on allocator behavior.

Virtual memory overcommit means a successful allocation does not universally guarantee that every future page touch can be backed under memory pressure. Also, physically contiguous backing is not guaranteed. For DMA in a Linux driver, allocate/map using the kernel DMA API, rather than treating a malloc pointer as a bus address.

### What is cache coherency? {M}
**Short answer:** Hardware keeps coherent copies of a cache line consistent across cores. A writer typically obtains ownership and invalidates other copies; a later coherent reader obtains the updated value. DRAM need not be updated immediately.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="Core 0: a = 20 to Coherency fabric: Invalidate to Core 1: Reload = 20" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="108.33333333333333" y="36" font-size="13" font-weight="600" fill="#172554">Core 0</text><text x="108.33333333333333" y="56" font-size="11" fill="#334155">a = 20</text><path d="M209.66666666666666 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="231.66666666666666" y="12" width="196.66666666666666" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="330" y="36" font-size="13" font-weight="600" fill="#172554">Coherency fabric</text><text x="330" y="56" font-size="11" fill="#334155">Invalidate</text><path d="M431.3333333333333 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="453.3333333333333" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="551.6666666666666" y="36" font-size="13" font-weight="600" fill="#172554">Core 1</text><text x="551.6666666666666" y="56" font-size="11" fill="#334155">Reload = 20</text></svg></div>

```c
/* Use proper synchronization for shared data. */
smp_store_release(&flag, 1);
/* Other CPU: smp_load_acquire(&flag) */
```

**1. Without coherency:** Core 0 and Core 1 both cache a = 10. Core 0 writes 20; without coordination, Core 1 could keep reading stale 10.

**2. With coherency:** Core 0 requests write ownership, other copies are invalidated, and a later coherent read obtains 20 from the appropriate cache or memory. This works at cache-line granularity.

| MESI state | Meaning |
|---|---|
| M | Modified, dirty and exclusive |
| E | Exclusive and clean |
| S | Shared and clean |
| I | Invalid |

MESI is an illustrative protocol; real Arm implementations vary.

**3. CPU vs DMA:** Non-coherent DMA may require cleaning before a device reads CPU-written buffers and invalidating stale CPU copies before reading device-written data. Linux DMA APIs manage these transitions.

**4. Limitation:** Coherency does not make a++ atomic or enforce ordering between different addresses.

**Interview takeaway:** Coherency keeps cached copies consistent; synchronization and memory barriers solve separate ordering and atomicity problems.

#### Cache-line ownership: practical multicore example

Assume an illustrative 64-byte cache line contains two variables. Initially both cores cache the line in shared state. Core 0 writes one variable; the coherency protocol obtains exclusive write ownership and invalidates other copies. Core 1's next read of a variable on that line requests a valid copy. The line may be supplied directly by another cache even while DRAM still contains the old value.

If the cores continuously update different variables in the same cache line, ownership can repeatedly move between cores: this is false sharing. Separating hot per-core variables into different cache lines can improve throughput, at the cost of extra memory. Verify actual line size and measure the effect.

Coherence of a location does not impose every desired ordering relationship across locations. Publishing a flag and associated data still requires release/acquire or another synchronization protocol. A C data race remains undefined even on coherent hardware. Non-coherent devices require a separate DMA ownership/cache-maintenance strategy.

### What is a memory barrier? {M}
**Short answer:** A barrier constrains memory ordering. On ARM, DMB orders relevant accesses, DSB also waits for required completion, and ISB synchronizes instruction execution after context changes.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="Write data: 100 to DMB: Ordering to Write flag: 1" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="108.33333333333333" y="36" font-size="13" font-weight="600" fill="#172554">Write data</text><text x="108.33333333333333" y="56" font-size="11" fill="#334155">100</text><path d="M209.66666666666666 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="231.66666666666666" y="12" width="196.66666666666666" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="330" y="36" font-size="13" font-weight="600" fill="#172554">DMB</text><text x="330" y="56" font-size="11" fill="#334155">Ordering</text><path d="M431.3333333333333 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="453.3333333333333" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="551.6666666666666" y="36" font-size="13" font-weight="600" fill="#172554">Write flag</text><text x="551.6666666666666" y="56" font-size="11" fill="#334155">1</text></svg></div>

```asm
STR W0, [X1]
DMB ISHST
STR W2, [X3]
```

**1. Without a memory barrier**

Consider two CPU cores sharing data and flag, initially zero. The following is conceptual pseudocode, not safe portable C concurrency:

```c
// CPU Core 0
data = 100;
flag = 1;

// CPU Core 1
if (flag == 1)
    value = data;
```

On weakly ordered ARM systems, Core 1 may observe flag = 1 before data = 100 and obtain the old value 0.

**2. With a memory barrier (Linux kernel)**

```c
// CPU Core 0
WRITE_ONCE(data, 100);
smp_wmb();
WRITE_ONCE(flag, 1);

// CPU Core 1
if (READ_ONCE(flag) == 1) {
    smp_rmb();
    value = READ_ONCE(data);
}
```

<div style="max-width:600px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 260" width="100%" role="img" aria-label="Producer writes data then write barrier then flag. Consumer reads flag then read barrier then data." font-family="system-ui,sans-serif" text-anchor="middle"><g fill="#dbeafe" stroke="#2563eb"><rect x="15" y="10" width="260" height="35" rx="6"/><rect x="325" y="10" width="260" height="35" rx="6"/></g><g fill="#172554" font-size="15" font-weight="600"><text x="145" y="33">CPU Core 0</text><text x="455" y="33">CPU Core 1</text></g><g fill="#dcfce7" stroke="#15803d"><rect x="15" y="60" width="260" height="40" rx="6"/><rect x="325" y="60" width="260" height="40" rx="6"/><rect x="15" y="190" width="260" height="40" rx="6"/><rect x="325" y="190" width="260" height="40" rx="6"/></g><g fill="#fef3c7" stroke="#a16207"><rect x="15" y="125" width="260" height="40" rx="6"/><rect x="325" y="125" width="260" height="40" rx="6"/></g><g fill="#172554" font-size="14"><text x="145" y="85">Write data = 100</text><text x="455" y="85">Read flag = 1</text><text x="145" y="150">Write barrier</text><text x="455" y="150">Read barrier</text><text x="145" y="215">Write flag = 1</text><text x="455" y="215">Read data = 100</text></g><g stroke="#64748b" stroke-width="2" fill="none"><path d="M145 100v25m-5-6 5 6 5-6 M145 165v25m-5-6 5 6 5-6 M455 100v25m-5-6 5 6 5-6 M455 165v25m-5-6 5 6 5-6"/></g></svg></div>

When the consumer observes the published flag, the paired barriers ensure it can read the earlier data in this one-time publication example.

**3. ARM barrier instructions**

| Instruction | Purpose |
|---|---|
| DMB | Orders relevant memory accesses |
| DSB | Also waits for required completion |
| ISB | Synchronizes subsequent instruction execution after context changes |

**4. Linux kernel APIs**

| API | Purpose |
|---|---|
| smp_rmb() | Orders reads |
| smp_wmb() | Orders writes |
| smp_mb() | Orders reads and writes |
| barrier() | Compiler ordering only |
| smp_store_release() | Store with release ordering |
| smp_load_acquire() | Load with acquire ordering |

**5. Coherency vs barrier**

| Cache coherency | Memory barrier |
|---|---|
| Consistency of cached copies | Ordering across memory accesses |
| Usually hardware-managed | Explicit ordering where needed |

**6. Simpler Linux publication pattern**

```c
// Producer: one-time publication
WRITE_ONCE(data, 100);
smp_store_release(&flag, 1);

// Consumer
if (smp_load_acquire(&flag))
    value = READ_ONCE(data);
```

Release orders prior accesses before publication; acquire orders later accesses after observing it. Use C11 atomics in portable userspace code. A device ownership flag instead needs the DMA API and appropriate DMA/MMIO barriers.

**Interview takeaway:** Barriers enforce memory ordering, not atomicity or automatic cache writeback. The barrier scope and memory type matter. [Linux memory barriers](https://docs.kernel.org/core-api/wrappers/memory-barriers.html).

#### Choosing the correct barrier for a concrete situation

| Situation | Relevant mechanism |
|---|---|
| Publish normal-memory data between CPU cores | Release/acquire or paired SMP barriers |
| Publish a DMA descriptor before ownership | DMA ordering primitives plus required mapping/sync |
| Complete specified cache maintenance before proceeding | Architecture-required DSB scope |
| Change a system register affecting instruction execution | Required context synchronization, often ISB |

The barrier domain matters: DMB ISH orders specified accesses for the inner-shareable domain, DMB ISHST restricts the ordering to the appropriate store class, and other scopes/variants serve different observers. DSB is not a universal instruction that flushes all caches or waits for every peripheral's internal operation; it waits for the operations required by its architectural type and scope. ISB synchronizes the instruction stream with context changes; it is not a substitute for data-memory ordering.

A typical one-time Linux publication can also be written more directly:

```c
// Producer
WRITE_ONCE(data, 100);
smp_store_release(&flag, 1);

// Consumer
if (smp_load_acquire(&flag) == 1)
    value = READ_ONCE(data);
```

Both sides must participate in the synchronization protocol; a producer barrier alone does not solve every consumer ordering issue. Use portable C11 atomic operations for userspace threads and Linux SMP/DMA/MMIO APIs for kernel code. Do not insert raw barriers blindly or rely on volatile for ordering.

### What is acquire and release ordering? {M}
**Short answer:** Release orders earlier accesses before publication; acquire orders later accesses after observing publication. Together they support safe producer-consumer communication.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="Producer: Write data to Release / Acquire: Publish flag to Consumer: Read data" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="108.33333333333333" y="36" font-size="13" font-weight="600" fill="#172554">Producer</text><text x="108.33333333333333" y="56" font-size="11" fill="#334155">Write data</text><path d="M209.66666666666666 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="231.66666666666666" y="12" width="196.66666666666666" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="330" y="36" font-size="13" font-weight="600" fill="#172554">Release / Acquire</text><text x="330" y="56" font-size="11" fill="#334155">Publish flag</text><path d="M431.3333333333333 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="453.3333333333333" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="551.6666666666666" y="36" font-size="13" font-weight="600" fill="#172554">Consumer</text><text x="551.6666666666666" y="56" font-size="11" fill="#334155">Read data</text></svg></div>

```asm
STLR W0, [X1] // release store
LDAR W2, [X1] // acquire load
```

**1. Producer:** Write the payload first, then publish the flag with release ordering.

**2. Consumer:** Load the flag with acquire ordering. If it observes the release publication, subsequent reads can safely access the payload in this one-time publication pattern.

```c
// Linux kernel; initially flag = 0
WRITE_ONCE(data, 100);
smp_store_release(&flag, 1);

// Other CPU
if (smp_load_acquire(&flag))
    value = READ_ONCE(data);
```

**3. Difference from full barriers:** Release primarily orders preceding accesses before publication; acquire orders following accesses after observation. A full barrier is stronger in other ordering directions.

**Interview takeaway:** Acquire/release is a common efficient building block for locks, queues and producer-consumer synchronization.

#### C11 example and ARM64 lowering

```c
#include <stdatomic.h>
static int payload;
static atomic_int published;

void send_once(void)
{
    payload = 42;
    atomic_store_explicit(&published, 1, memory_order_release);
}

int receive(void)
{
    if (atomic_load_explicit(&published, memory_order_acquire))
        return payload;
    return -1;
}
```

When the acquire load reads the release publication, the payload write happens-before the consumer's payload read. On AArch64, a suitable compiler may implement the release store with STLR and the acquire load with LDAR or an equivalent instruction sequence.

For a standalone statistics counter, relaxed atomics can be sufficient because no other data is published. For a lock, acquisition uses acquire semantics and unlock uses release so protected writes become visible to the next owner. Sequentially consistent atomics impose additional ordering requirements. Acquire/release is directional rather than a full fence in both directions. The example is one-time publication: reuse of payload requires acknowledgment or another ownership protocol.

### How do LDAXR and STLXR implement atomic operations? {H}
**Short answer:** An exclusive load establishes a reservation. An exclusive store succeeds only if the reservation remains valid; otherwise retry. Acquire/release forms provide ordering.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="LDAXR: Read / reserve to ADD: Modify to STLXR: Try store to Retry: On failure" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="141.25" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="80.625" y="36" font-size="13" font-weight="600" fill="#172554">LDAXR</text><text x="80.625" y="56" font-size="11" fill="#334155">Read / reserve</text><path d="M154.25 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="176.25" y="12" width="141.25" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="246.875" y="36" font-size="13" font-weight="600" fill="#172554">ADD</text><text x="246.875" y="56" font-size="11" fill="#334155">Modify</text><path d="M320.5 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="342.5" y="12" width="141.25" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="413.125" y="36" font-size="13" font-weight="600" fill="#172554">STLXR</text><text x="413.125" y="56" font-size="11" fill="#334155">Try store</text><path d="M486.75 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="508.75" y="12" width="141.25" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="579.375" y="36" font-size="13" font-weight="600" fill="#172554">Retry</text><text x="579.375" y="56" font-size="11" fill="#334155">On failure</text></svg></div>

```asm
1: LDAXR W0, [X1]
   ADD W0, W0, #1
   STLXR W2, W0, [X1]
   CBNZ W2, 1b
```

**1. Why normal increment fails:** Two cores can both load 10, add 1 and store 11, losing an increment.

**2. Exclusive sequence:** LDAXR reads and establishes an exclusive reservation. STLXR attempts the write and returns zero on success or nonzero on failure. Interference or other events can invalidate the reservation.

**3. Retry:** CBNZ repeats the sequence until a store succeeds. LDAXR has acquire semantics and STLXR release semantics.

```c
// Linux kernel alternative
atomic_inc(&counter);
```

**4. Modern ARM:** LSE-capable cores also support single-instruction atomic read-modify-write operations, such as LDADD.

**Interview takeaway:** Exclusives make the update conditional on reservation validity; ordering semantics and atomicity are distinct.

#### Two-core exclusive retry trace

| Step | Core 0 | Core 1 |
|---|---|---|
| Initial | counter=10 | counter=10 |
| Load-exclusive | reads 10, reserves | reads 10, reserves |
| Add | computes 11 | computes 11 |
| Store-exclusive | succeeds, status 0 | fails if reservation invalidated |
| Retry | done | reloads 11, computes 12, stores successfully |

The exclusive monitor tracks the relevant reservation granule; interference, context changes and other permitted conditions can cause failure, not just an explicit write to the exact C object. Code must handle failure by retrying. A store-exclusive status value is not the stored data. Use the architecture's width, alignment and memory-type restrictions, and keep the exclusive sequence short.

For pure counter increments, LDXR/STXR can provide relaxed atomicity; LDAXR/STLXR add ordering. LSE instructions such as LDADD and ordering variants can avoid an explicit software retry loop when supported. In C or Linux, prefer compiler atomic or kernel atomic APIs to handwritten inline assembly unless the low-level implementation itself is the subject. A retry loop is not a bounded-time guarantee under contention.

### What is the difference between normal and device memory? {M}
**Short answer:** Normal memory is suitable for RAM and may be cacheable. Device memory has stricter access attributes suitable for MMIO registers. Linux drivers use ioremap and appropriate I/O accessors.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="Normal: RAM / cache to Device: MMIO / peripheral" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="307.5" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="163.75" y="36" font-size="13" font-weight="600" fill="#172554">Normal</text><text x="163.75" y="56" font-size="11" fill="#334155">RAM / cache</text><path d="M320.5 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="342.5" y="12" width="307.5" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="496.25" y="36" font-size="13" font-weight="600" fill="#172554">Device</text><text x="496.25" y="56" font-size="11" fill="#334155">MMIO / peripheral</text></svg></div>

```c
void __iomem *base = ioremap(phys, size);
/* After checking base: */
writel(1, base);
```

**1. Normal memory:** Used for program code, heap and buffers. Depending on attributes, it can be cached, speculatively accessed and reordered.

**2. Device memory:** Used for registers whose reads or writes can have side effects. Device attributes restrict gathering, reordering and early acknowledgement to varying degrees.

| Normal | Device |
|---|---|
| RAM | Peripheral MMIO |
| Often cacheable | Not ordinary cacheable RAM |
| Speculation allowed as appropriate | Restricted access behavior |

**3. Linux driver:** Use ioremap or managed resource mapping, then readl/writel. Check mapping errors and release unmanaged mappings. Do not treat MMIO as an ordinary pointer or assume volatile supplies hardware ordering.

**Interview takeaway:** Memory attributes tell the CPU how accesses may behave; driver accessors enforce the appropriate semantics.

#### Device-memory attribute subtypes

AArch64 defines Device-nGnRnE, Device-nGnRE, Device-nGRE and Device-GRE. The letters describe permitted Gathering, Reordering and Early write acknowledgement. The n prefix disables that behavior. For example, nGnRnE provides the strictest of these device attributes, while nGnRE permits early write acknowledgement. Device memory is not ordinary cacheable RAM.

Consider a UART receive-data register. Each read may consume a byte from its FIFO. Speculatively reading it or merging two reads would change device behavior. A correctly mapped device register and appropriate accessor preserve the required access semantics.

Normal non-cacheable memory is not identical to Device memory: its permitted speculation and access behavior differ. Linux chooses mapping attributes through ioremap, resource helpers and platform configuration. A posted device write can require a documented readback to ensure it has reached the relevant device before a subsequent action. Do not use memcpy on an arbitrary MMIO register range; use suitable I/O accessors and the device's documented widths.

### How does DMA interact with CPU caches? {M}
**Short answer:** A coherent device can participate in hardware coherency. Non-coherent DMA requires cache maintenance and ownership transitions; use Linux DMA mapping APIs to handle this.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="CPU cache: DMA mapping to RAM: DMA buffer to Device: DMA engine" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="108.33333333333333" y="36" font-size="13" font-weight="600" fill="#172554">CPU cache</text><text x="108.33333333333333" y="56" font-size="11" fill="#334155">DMA mapping</text><path d="M209.66666666666666 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="231.66666666666666" y="12" width="196.66666666666666" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="330" y="36" font-size="13" font-weight="600" fill="#172554">RAM</text><text x="330" y="56" font-size="11" fill="#334155">DMA buffer</text><path d="M431.3333333333333 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="453.3333333333333" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="551.6666666666666" y="36" font-size="13" font-weight="600" fill="#172554">Device</text><text x="551.6666666666666" y="56" font-size="11" fill="#334155">DMA engine</text></svg></div>

```c
dma_addr_t a = dma_map_single(dev, buf, len, DMA_TO_DEVICE);
/* Check dma_mapping_error; unmap after DMA completes. */
```

**1. CPU to device:** CPU writes a buffer. On a non-coherent system, dirty cache lines may hold newer bytes than RAM. Mapping or syncing for the device performs required maintenance.

**2. Device to CPU:** DMA writes memory. The CPU may retain stale cached bytes, so syncing for CPU access or unmapping is necessary before reading.

| Linux API | Use |
|---|---|
| dma_alloc_coherent | Coherent allocation |
| dma_map_single | Streaming mapping |
| dma_sync_single_for_cpu | Return ownership to CPU |
| dma_sync_single_for_device | Return ownership to device |
| dma_unmap_single | End streaming mapping |

**3. Important:** Check dma_mapping_error, obey DMA direction and ownership, and use the returned DMA address, not a cast CPU pointer. Coherent allocation still needs ordering where appropriate.

**Interview takeaway:** The DMA API abstracts cache maintenance and address mapping, including IOMMUs.

#### Walk through both DMA directions

CPU-to-device example: the CPU fills a transmit buffer with new data, but a non-coherent device might otherwise see old RAM contents because dirty cache lines have not been written back. The DMA mapping or sync-for-device operation establishes the required visibility before the driver hands ownership to hardware.

Device-to-CPU example: hardware receives a packet into memory. Before the CPU reads it, the driver waits for completion and uses the DMA API to return ownership to the CPU. This handles stale cache lines and any platform-required maintenance.

```c
dma_addr_t dma = dma_map_single(dev, buf, len, DMA_FROM_DEVICE);
if (dma_mapping_error(dev, dma))
    return -EIO;

/* Submit DMA and wait for completion or quiesce on error. */

dma_unmap_single(dev, dma, len, DMA_FROM_DEVICE);
/* Now CPU may consume the received data. */
```

For persistent streaming mappings, dma_sync_single_for_cpu and dma_sync_single_for_device bracket ownership changes instead of unmapping each time. Do not let independent objects share cache lines inappropriately with DMA buffers on a non-coherent target. For coherent descriptors, publish fields before the device ownership flag with an appropriate barrier; coherence does not itself guarantee ordering or safe simultaneous modification.

### What is ARM GIC? {M}
**Short answer:** The Generic Interrupt Controller routes and prioritizes interrupts. GICv3 uses a distributor, redistributors and CPU interfaces; an interrupt handler acknowledges and completes interrupts.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="Peripheral: IRQ to GIC: Route / priority to CPU: Exception handler" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="108.33333333333333" y="36" font-size="13" font-weight="600" fill="#172554">Peripheral</text><text x="108.33333333333333" y="56" font-size="11" fill="#334155">IRQ</text><path d="M209.66666666666666 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="231.66666666666666" y="12" width="196.66666666666666" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="330" y="36" font-size="13" font-weight="600" fill="#172554">GIC</text><text x="330" y="56" font-size="11" fill="#334155">Route / priority</text><path d="M431.3333333333333 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="453.3333333333333" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="551.6666666666666" y="36" font-size="13" font-weight="600" fill="#172554">CPU</text><text x="551.6666666666666" y="56" font-size="11" fill="#334155">Exception handler</text></svg></div>

```asm
MRS X0, ICC_IAR1_EL1 // acknowledge Group 1
// handle valid interrupt
MSR ICC_EOIR1_EL1, X0 // end priority
```

**1. Interrupt path:** A peripheral asserts an interrupt. The GIC decides its priority and target CPU. The CPU receives an IRQ exception if permitted.

**2. GICv3 components**

| Component | Role |
|---|---|
| Distributor | Configures shared peripheral interrupts |
| Redistributor | Per-core interrupt configuration |
| CPU interface | Acknowledge, prioritize and signal completion |

**3. Interrupt classes:** SGIs support interprocessor signaling; PPIs are private to a CPU; SPIs are shared peripheral interrupts.

**4. Handler:** Acknowledge the interrupt, service its source, then signal end of interrupt. Depending on configuration, a separate deactivate operation is required. Linux normally handles these details via its IRQ subsystem.

**Interview takeaway:** The GIC routes and prioritizes interrupts; the device driver handles the interrupt source.

#### End-to-end interrupt flow in Linux

Assume an I2C-connected touch controller asserts a GPIO interrupt. The GPIO controller may route or cascade that interrupt through a parent interrupt controller; the GIC presents the relevant interrupt to the CPU.

```text
Peripheral IRQ -> GPIO / interrupt routing -> GIC
    -> CPU exception vector -> Linux IRQ subsystem
    -> device driver's registered handler
    -> acknowledge device and complete interrupt
```

GICv3's distributor handles shared interrupt configuration, redistributors hold per-processor SGI/PPI configuration and related state, and CPU system-register interfaces handle acknowledgement and priority operations. For MSI-based devices, an ITS can translate device/event identifiers to LPIs when that facility is implemented.

A level-triggered device interrupt generally requires its source to be serviced or deasserted before it is allowed to retrigger. Otherwise, repeated interrupts may occur even after end-of-interrupt at the GIC. Read /proc/interrupts to examine interrupt counts and CPU distribution, and inspect the device's own status registers when diagnosing missing or repeated interrupts.

The raw assembly illustration assumes a valid acknowledged interrupt and a suitable GIC configuration; spurious INTIDs and split EOI/deactivate mode require their documented handling. Ordinary Linux device drivers use request_irq or request_threaded_irq instead of manipulating the GIC directly.

### What is TrustZone? {M}
**Short answer:** TrustZone provides hardware-backed security state separation. A typical system has a normal world and a secure world, with controlled transitions and protected resources.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="Normal world: Linux / Android to Secure monitor: SMC to Secure world: Trusted OS" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="108.33333333333333" y="36" font-size="13" font-weight="600" fill="#172554">Normal world</text><text x="108.33333333333333" y="56" font-size="11" fill="#334155">Linux / Android</text><path d="M209.66666666666666 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="231.66666666666666" y="12" width="196.66666666666666" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="330" y="36" font-size="13" font-weight="600" fill="#172554">Secure monitor</text><text x="330" y="56" font-size="11" fill="#334155">SMC</text><path d="M431.3333333333333 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="453.3333333333333" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="551.6666666666666" y="36" font-size="13" font-weight="600" fill="#172554">Secure world</text><text x="551.6666666666666" y="56" font-size="11" fill="#334155">Trusted OS</text></svg></div>

```asm
SMC #0 // monitor call, where permitted
```

**1. Normal world:** Runs the ordinary OS and applications, with access limited to non-secure resources.

**2. Secure world:** Runs trusted firmware or a trusted OS and can protect keys or sensitive services through platform security controls.

**3. Transition:** An SMC may enter the secure monitor (depending on routing/configuration), which validates the request and coordinates world switching. Memory controllers and peripheral firewalls enforce resource separation.

| TrustZone | Virtualization |
|---|---|
| Security state separation | Guest isolation and resource control |
| Secure monitor typically EL3 | Hypervisor typically EL2 |

**Interview takeaway:** TrustZone is hardware-assisted isolation, not automatic security for every application; secure firmware and platform configuration matter.

#### Example: trusted service from a normal-world application

```text
Normal-world application
    -> kernel TEE driver
    -> SMC / platform call
    -> secure monitor
    -> trusted OS / trusted application
    -> validated result returned to normal world
```

For example, a normal-world client requests a cryptographic operation using a protected key. The trusted service performs the operation without exposing that key to the caller. Shared-memory arguments must be checked for valid address ranges, size, permissions and lifetime. The normal-world kernel may be untrusted by the secure service's threat model.

TrustZone requires the SoC's memory and peripheral security controllers to enforce the intended resource attribution. The secure monitor, trusted OS, secure boot chain and trusted applications must also be correctly implemented. TrustZone does not itself encrypt all memory or prove the correctness of trusted code. On Cortex-M, TrustZone uses a different exception and gateway model from the Cortex-A SMC/EL3 architecture. Newer Arm systems can provide additional security states and isolation facilities, so consult the implemented architecture.

### What is ARM virtualization at EL2? {H}
**Short answer:** EL2 lets a hypervisor control guest execution and traps. Stage-1 translation maps guest VA to IPA; stage-2 maps IPA to host PA.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="Guest VA: Stage 1 to IPA: Stage 2 to Host PA: Memory" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="108.33333333333333" y="36" font-size="13" font-weight="600" fill="#172554">Guest VA</text><text x="108.33333333333333" y="56" font-size="11" fill="#334155">Stage 1</text><path d="M209.66666666666666 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="231.66666666666666" y="12" width="196.66666666666666" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="330" y="36" font-size="13" font-weight="600" fill="#172554">IPA</text><text x="330" y="56" font-size="11" fill="#334155">Stage 2</text><path d="M431.3333333333333 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="453.3333333333333" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="551.6666666666666" y="36" font-size="13" font-weight="600" fill="#172554">Host PA</text><text x="551.6666666666666" y="56" font-size="11" fill="#334155">Memory</text></svg></div>

```asm
MRS X0, VTTBR_EL2 // stage-2 table base
```

**1. Guest stage 1:** Guest Linux translates its virtual address using its own page tables to an intermediate physical address (IPA).

**2. Hypervisor stage 2:** EL2 controls translation from IPA to host physical address. This allows a hypervisor to restrict guest memory without modifying guest page tables.

**3. Traps:** Selected privileged operations, device accesses or faults can trap to EL2 for handling. Hardware virtualization allows many guest instructions to execute directly.

**4. Linux example:** KVM on an ARM64 host uses EL2 facilities; QEMU can provide userspace device emulation. An x86 host cannot directly execute ARM guest instructions with KVM and typically needs QEMU TCG for cross-ISA emulation.

**Interview takeaway:** Stage-2 translation and configurable traps let EL2 isolate and manage guests.

#### Worked translation and trap example

Guest Linux maps VA 0x40001234 through its stage-1 tables to IPA 0x80000234. The hypervisor maps IPA page 0x80000000 to host physical page 0xA0000000. The resulting host PA is 0xA0000234, assuming 4 KiB pages and permitted accesses.

| EL2 register | Role |
|---|---|
| HCR_EL2 | Virtualization controls and selected trap routing |
| VTTBR_EL2 | Stage-2 translation root and VMID, as configured |
| VTCR_EL2 | Stage-2 translation parameters |
| ELR_EL2 / SPSR_EL2 | Exception return state |
| ESR_EL2 | Exception syndrome where applicable |

If the guest accesses an emulated peripheral that is not backed by ordinary stage-2 RAM, the hypervisor can handle the resulting fault and emulate the register operation. In Linux KVM, some exits are handled in the kernel; selected events such as emulated MMIO can return to QEMU through KVM_RUN. QEMU services the device model and re-enters guest execution.

A combined translation can be cached in the TLB, so two-stage translation does not require two complete walks for every instruction. Guest DMA needs its own device isolation/mapping mechanism. KVM accelerates compatible-ISA guests; TCG dynamically translates guest instructions on a different host architecture.

### What is the ARM64 calling convention? {M}
**Short answer:** AAPCS64 passes ordinary integer/pointer arguments in X0–X7 and returns simple integer results in X0. X19–X28 are callee-saved; SP must be 16-byte aligned at public interfaces.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="Caller: X0–X7 arguments to Function: Compute to Return: X0 result" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="108.33333333333333" y="36" font-size="13" font-weight="600" fill="#172554">Caller</text><text x="108.33333333333333" y="56" font-size="11" fill="#334155">X0–X7 arguments</text><path d="M209.66666666666666 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="231.66666666666666" y="12" width="196.66666666666666" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="330" y="36" font-size="13" font-weight="600" fill="#172554">Function</text><text x="330" y="56" font-size="11" fill="#334155">Compute</text><path d="M431.3333333333333 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="453.3333333333333" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="551.6666666666666" y="36" font-size="13" font-weight="600" fill="#172554">Return</text><text x="551.6666666666666" y="56" font-size="11" fill="#334155">X0 result</text></svg></div>

```asm
add_two:
    ADD X0, X0, X1
    RET
```

**1. Register rules (AAPCS64)**

| Registers | Role |
|---|---|
| X0–X7 | Ordinary integer/pointer arguments |
| X0 | Typical scalar result |
| X19–X28 | Callee-saved |
| X29 / X30 | Frame pointer convention / link register |
| SP | 16-byte aligned at public interfaces |

**2. Example:** Calling add_two(10, 20) passes 10 in X0 and 20 in X1. ADD leaves 30 in X0 and RET returns to the caller.

**3. Extra arguments:** Additional ordinary arguments may be passed on the stack. Floating-point and aggregate arguments follow additional ABI rules. X18 is platform-specific.

**Interview takeaway:** The ABI lets independently compiled functions agree on arguments, results and register preservation.

#### Caller-saved and callee-saved example

```asm
// long wrapper(long x) { return helper(x) + 1; }
wrapper:
    STP X29, X30, [SP, #-16]!
    MOV X29, SP
    BL helper
    ADD X0, X0, #1
    LDP X29, X30, [SP], #16
    RET
```

BL overwrites X30, so this non-leaf function preserves its original return address. Ordinary integer arguments and temporary values in caller-saved registers may be overwritten by helper. If wrapper needs a value after the call, it must save it or use a callee-saved register while preserving that register's incoming value.

AAPCS64 also defines X8 for certain indirect result locations, X16/X17 as intra-procedure-call temporaries, and X18 as platform-specific. X29 is a callee-saved register conventionally used as frame pointer. Floating-point and SIMD arguments/results typically use V0–V7, and parts of V8–V15 have preservation requirements. Aggregates and variadic functions have additional rules.

Do not confuse the C function-call ABI with the Linux syscall ABI, which uses X8 for the syscall number and X0–X5 for its arguments.

### What is a stack frame in ARM64? {M}
**Short answer:** A function may save its frame pointer X29 and link register X30 on the stack. Leaf functions may not require a frame.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="SP before: Caller to Stack frame: Saved X29 / X30 to SP after: Restore" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="108.33333333333333" y="36" font-size="13" font-weight="600" fill="#172554">SP before</text><text x="108.33333333333333" y="56" font-size="11" fill="#334155">Caller</text><path d="M209.66666666666666 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="231.66666666666666" y="12" width="196.66666666666666" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="330" y="36" font-size="13" font-weight="600" fill="#172554">Stack frame</text><text x="330" y="56" font-size="11" fill="#334155">Saved X29 / X30</text><path d="M431.3333333333333 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="453.3333333333333" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="551.6666666666666" y="36" font-size="13" font-weight="600" fill="#172554">SP after</text><text x="551.6666666666666" y="56" font-size="11" fill="#334155">Restore</text></svg></div>

```asm
STP X29, X30, [SP, #-16]!
MOV X29, SP
// function body
LDP X29, X30, [SP], #16
RET
```

**1. Entry:** STP with pre-index addressing subtracts 16 from SP and stores X29 and X30. MOV sets the frame pointer to the new SP.

**2. Body:** A function may reserve more aligned stack space for local variables, saved registers or outgoing arguments.

**3. Exit:** LDP restores the saved registers and increments SP by 16. RET branches to the saved return address.

| Before frame | After allocation |
|---|---|
| SP points to caller stack top | SP points to saved X29 |
| LR contains return address | Saved X30 is at SP + 8 |

**4. Optimization:** Leaf functions may omit stack frames and some platforms permit frame-pointer omission.

**Interview takeaway:** The stack frame preserves call state and local storage; the stack grows toward lower addresses in the usual AArch64 ABI.

#### Numerical stack-frame trace

Assume SP starts at 0x8000 and the function executes the following prologue:

```asm
STP X29, X30, [SP, #-16]!
MOV X29, SP
SUB SP, SP, #32
```

SP first becomes 0x7FF0. Saved X29 is at 0x7FF0 and saved X30 at 0x7FF8. X29 points to the frame record. After reserving 32 bytes, SP becomes 0x7FD0, leaving aligned local storage below the saved registers.

```text
Higher addresses
0x8000  caller's original SP
0x7FF8  saved X30 (return address)
0x7FF0  saved X29  <- frame pointer
        local storage (32 bytes)
0x7FD0  current SP
Lower addresses
```

Before returning, reverse the local allocation and restore the saved pair with LDP. The compiler may instead omit a frame pointer, combine allocations, or use different spill offsets; the ABI and unwind metadata govern the valid layout. A stack frame is not necessarily the same size as a function's C local variables, since alignment, register spills and outgoing arguments also matter.

### What is WFI versus WFE? {M}
**Short answer:** WFI waits for an interrupt or another permitted wake condition. WFE waits for an event or other permitted wake condition; SEV sends an event. Neither is a synchronization primitive by itself.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="WFI: Interrupt to WFE: Event to SEV: Signal event" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="108.33333333333333" y="36" font-size="13" font-weight="600" fill="#172554">WFI</text><text x="108.33333333333333" y="56" font-size="11" fill="#334155">Interrupt</text><path d="M209.66666666666666 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="231.66666666666666" y="12" width="196.66666666666666" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="330" y="36" font-size="13" font-weight="600" fill="#172554">WFE</text><text x="330" y="56" font-size="11" fill="#334155">Event</text><path d="M431.3333333333333 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="453.3333333333333" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="551.6666666666666" y="36" font-size="13" font-weight="600" fill="#172554">SEV</text><text x="551.6666666666666" y="56" font-size="11" fill="#334155">Signal event</text></svg></div>

```asm
WFI // idle hint
WFE // event wait hint
SEV // send event
```

**1. WFI:** A CPU idle loop may use Wait For Interrupt so the processor can reduce activity until a wake condition occurs.

**2. WFE:** Wait For Event can be used in a waiting loop. SEV sends an event; a previously recorded event may make WFE return immediately.

**3. Practical pattern:** Always recheck the shared condition after waking. Wakeups can be unrelated to the expected event, and ordering must be supplied separately.

| WFI | WFE |
|---|---|
| Common in idle paths | Common in event-based wait loops |
| Interrupt-related wakeup | Event or other allowed wakeup |

**Interview takeaway:** These are architectural hints, not locks or guarantees that the core sleeps for a particular duration.

#### Event waiting and lost-wakeup considerations

AArch64 maintains an event mechanism used by WFE. An event may already be recorded when WFE executes, in which case the instruction can return immediately. SEV signals an event; SEVL is a local event-setting instruction. WFI and WFE may also be treated as hints or trap under virtualization controls, depending on the architecture and configuration.

A conceptual event-based lock waiter must repeatedly check the lock with the required atomic ordering. The unlock path publishes the released state and follows the matching notification protocol. A plain load followed by WFE without a correct event protocol can miss a state change. Use the OS or architecture's established synchronization primitives rather than inventing a wait loop.

For low-power idle, configure appropriate wake sources and account for pending work, clock/power-domain behavior and wake latency. Neither WFI nor WFE specifies the SoC's eventual power state or guarantees that a particular interrupt has been serviced when execution resumes.

### What is the difference between a cache clean and invalidate? {M}
**Short answer:** Cleaning writes dirty data toward the required coherency point; invalidation discards cached copies. Incorrect invalidation can lose dirty data. Use platform APIs for DMA.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="Clean: Cache → coherency point to Invalidate: Discard stale line" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="307.5" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="163.75" y="36" font-size="13" font-weight="600" fill="#172554">Clean</text><text x="163.75" y="56" font-size="11" fill="#334155">Cache → coherency point</text><path d="M320.5 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="342.5" y="12" width="307.5" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="496.25" y="36" font-size="13" font-weight="600" fill="#172554">Invalidate</text><text x="496.25" y="56" font-size="11" fill="#334155">Discard stale line</text></svg></div>

```asm
DC CVAC, X0 // clean by VA to PoC
DSB SY      // wait for completion; illustrative
```

**1. Clean:** A dirty cache line is written toward the specified coherency point, allowing required observers to obtain updated contents.

**2. Invalidate:** A cached copy is discarded so later access must obtain a valid copy again. Discarding dirty data without correct handling may lose updates.

| Operation | Typical ARM instruction |
|---|---|
| Clean by VA to PoC | DC CVAC |
| Invalidate by VA to PoC | DC IVAC |
| Clean and invalidate by VA to PoC | DC CIVAC |

**3. Practical notes:** Maintenance applies to cache lines; alignment, scope and barriers matter. PoC is the point of coherency, not necessarily DRAM. Privilege and cache configuration affect permitted instructions.

**Interview takeaway:** Clean makes dirty data available as required; invalidate removes cached copies. Prefer Linux DMA APIs in drivers.

#### Worked cache-line maintenance example

Assume a 64-byte cache line and a CPU buffer starting at 0x1020 with length 80 bytes. The range touches two complete cache lines: 0x1000–0x103F and 0x1040–0x107F. A raw per-line maintenance operation affects the whole corresponding line, not just the requested bytes. Inappropriate invalidation can discard dirty data belonging to a neighboring object. This is one reason non-coherent DMA buffers need suitable allocation/alignment and ownership rules.

Clean is useful before a non-coherent device reads data produced by the CPU; invalidate or the platform's prescribed synchronization is needed before the CPU reads data produced by a device. The DMA API may perform maintenance at mapping, synchronization and unmapping as required by the platform and direction.

PoC (point of coherency) is the point at which relevant observers are guaranteed to see a coherent copy; PoU (point of unification) concerns the point where relevant instruction and data accesses see a unified copy. Executable-code modification may require data-cache cleaning to PoU, instruction-cache invalidation and prescribed DSB/ISB operations. Use architecture-specific helpers rather than treating a data-cache invalidate as a general instruction-cache synchronization operation.

### What is endianness in ARM? {E}
**Short answer:** Endianness determines the byte order of multi-byte values in memory. AArch64 supports little-endian data and implementation-dependent big-endian support; Linux commonly uses little-endian.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="Value: 0x12345678 to Low → high: 78 56 34 12" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="307.5" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="163.75" y="36" font-size="13" font-weight="600" fill="#172554">Value</text><text x="163.75" y="56" font-size="11" fill="#334155">0x12345678</text><path d="M320.5 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="342.5" y="12" width="307.5" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="496.25" y="36" font-size="13" font-weight="600" fill="#172554">Low → high</text><text x="496.25" y="56" font-size="11" fill="#334155">78 56 34 12</text></svg></div>

```asm
REV W0, W1 // reverse byte order
```

**1. Example:** Store 0x12345678 at address 0x1000.

| Address | Little endian | Big endian |
|---|---|---|
| 0x1000 | 78 | 12 |
| 0x1001 | 56 | 34 |
| 0x1002 | 34 | 56 |
| 0x1003 | 12 | 78 |

**2. C example**

```c
uint32_t x = 1;
bool little = *(unsigned char *)&x == 1;
```

**3. Drivers:** Protocols and device registers may define their own byte order. Use conversions such as cpu_to_le32 or be32_to_cpu where appropriate.

**Interview takeaway:** Endianness changes byte layout in memory, not the numerical meaning of an integer held in a register.

#### Byte order at a protocol boundary

Suppose an I2C device returns bytes 0x12 and 0x34 for a 16-bit big-endian register value.

```c
uint16_t decode_be16(const uint8_t b[2])
{
    return (uint16_t)(((uint16_t)b[0] << 8) | b[1]);
}
```

The result is 0x1234 regardless of the host CPU's byte order. Directly casting b to a uint16_t pointer can cause alignment, aliasing and endian problems. Explicit decoding or suitable OS helpers handles the protocol representation.

REV reverses all bytes of the selected register width; REV16 swaps bytes within each 16-bit group; RBIT reverses individual bits rather than bytes. These operations are distinct from the bit transmission order of a serial protocol.

A device's MMIO registers can specify their own endianness; Linux provides appropriate endian-specific accessors. Do not assume every peripheral uses the CPU's native byte order. A64 instruction encodings themselves use the architecture's fixed little-endian instruction representation, independently of supported data endianness.

### What are NZCV condition flags? {E}
**Short answer:** N is negative, Z is zero, C is carry (or no borrow for subtraction), and V is signed overflow. Flag-setting instructions and conditional branches use them.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="CMP: Set NZCV to B.EQ: Branch if Z=1" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="307.5" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="163.75" y="36" font-size="13" font-weight="600" fill="#172554">CMP</text><text x="163.75" y="56" font-size="11" fill="#334155">Set NZCV</text><path d="M320.5 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="342.5" y="12" width="307.5" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="496.25" y="36" font-size="13" font-weight="600" fill="#172554">B.EQ</text><text x="496.25" y="56" font-size="11" fill="#334155">Branch if Z=1</text></svg></div>

```asm
CMP X0, #0
B.EQ is_zero
```

**1. Flags**

| Flag | Meaning |
|---|---|
| N | Result sign bit |
| Z | Result is zero |
| C | Unsigned carry / no borrow |
| V | Signed overflow |

**2. Example:** CMP X0, #0 performs a subtraction for flags without storing the result. If X0 is zero, Z becomes 1 and B.EQ branches.

**3. Signed vs unsigned:** B.LT checks signed less-than (N differs from V); B.LO checks unsigned lower (C is clear). Choosing the wrong condition causes bugs.

```asm
CMP X0, X1
B.LO unsigned_lower
B.LT signed_lower
```

**Interview takeaway:** NZCV records arithmetic conditions and supports conditional execution and branching.

#### Signed overflow versus unsigned carry

For a 32-bit ADD instruction that updates flags:

```asm
// W0 = 0x7FFFFFFF, W1 = 1
ADDS W2, W0, W1
// W2 = 0x80000000: N=1, Z=0, C=0, V=1
```

The signed mathematical result exceeds INT32_MAX, so V is set. There is no unsigned carry out of bit 31.

If W0=0xFFFFFFFF and W1=1, the result is zero with N=0, Z=1, C=1 and V=0. Unsigned addition wraps while signed -1+1 is representable.

| Condition | Flag test | Interpretation after CMP |
|---|---|---|
| EQ | Z=1 | Equal |
| NE | Z=0 | Not equal |
| LO / CC | C=0 | Unsigned lower |
| HS / CS | C=1 | Unsigned higher or same |
| LT | N≠V | Signed less than |
| GE | N=V | Signed greater or equal |

CMP is an alias of a flag-setting subtraction whose result is discarded. Ordinary ADD does not update NZCV; ADDS does. CSEL can select one of two register values using a condition without an explicit branch. The compiler chooses such instructions when appropriate.

### What is the ARM64 boot flow? {M}
**Short answer:** Platform firmware initializes hardware and loads the next stage. A typical Linux flow is Boot ROM, platform firmware/bootloader, kernel entry, MMU setup and userspace init. Exact stages vary by SoC.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="Boot ROM: Firmware to Bootloader: Kernel + DTB to Linux kernel: MMU / drivers to Userspace: PID 1" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="141.25" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="80.625" y="36" font-size="13" font-weight="600" fill="#172554">Boot ROM</text><text x="80.625" y="56" font-size="11" fill="#334155">Firmware</text><path d="M154.25 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="176.25" y="12" width="141.25" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="246.875" y="36" font-size="13" font-weight="600" fill="#172554">Bootloader</text><text x="246.875" y="56" font-size="11" fill="#334155">Kernel + DTB</text><path d="M320.5 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="342.5" y="12" width="141.25" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="413.125" y="36" font-size="13" font-weight="600" fill="#172554">Linux kernel</text><text x="413.125" y="56" font-size="11" fill="#334155">MMU / drivers</text><path d="M486.75 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="508.75" y="12" width="141.25" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="579.375" y="36" font-size="13" font-weight="600" fill="#172554">Userspace</text><text x="579.375" y="56" font-size="11" fill="#334155">PID 1</text></svg></div>

```asm
// Linux arm64 boot protocol: X0 = DTB physical address
// X1–X3 = 0 at kernel entry
```

**1. Boot ROM:** Executes platform-defined immutable startup code and locates the next boot stage.

**2. Firmware / bootloader:** Initializes required clocks, DDR and devices, configures security state, and loads the kernel and DTB. Some platforms use TF-A, U-Boot SPL or U-Boot proper.

**3. Kernel entry:** Bootloader passes the DTB physical address in X0 according to the ARM64 Linux boot protocol. Linux performs early architecture setup, builds translation tables, enables the MMU and initializes drivers.

**4. Userspace:** The kernel mounts or prepares the root filesystem and executes the initial userspace program, typically systemd, /sbin/init or Android /init.

**Interview takeaway:** Boot flow progresses from platform firmware to kernel initialization to PID 1. Exact stages, exception levels and DDR initialization vary by SoC.

#### Detailed boot flow with typical firmware stages

```text
Reset -> Boot ROM
      -> early platform firmware / SPL
      -> DRAM and security initialization
      -> trusted firmware / bootloader, as configured
      -> Linux Image + DTB + optional initramfs
      -> early ARM64 kernel entry
      -> start_kernel()
      -> rest_init() / kernel_init()
      -> execute PID 1 userspace program
```

Boot ROM locates and verifies the next image according to platform policy, often using on-chip RAM before external DDR is available. Early firmware prepares clocks, power and DRAM. A platform may use TF-A BL31 at EL3 and a non-secure bootloader at a supported exception level. The exact chain differs by SoC; for example, i.MX8QM/QXP configurations may use system-controller firmware and platform-specific boot containers rather than the same SPL sequence as an i.MX8M board.

For direct ARM64 Linux DT boot, load the kernel image and DTB in suitable memory, supply the DTB physical address in X0, set X1–X3 to zero, establish required exception-level/interrupt/cache state, and enter with the MMU off as specified by the arm64 boot protocol. Linux then establishes its early mappings and initializes its own MMU configuration.

Early kernel assembly and architecture setup lead into start_kernel, which initializes core subsystems; initcalls initialize built-in drivers and related services. The kernel's init path prepares the root filesystem and executes an initial userspace init program. Function names and ordering details vary by kernel release.

For debugging, isolate the last successful stage using serial logs, bootloader image/address checks, earlycon, device-tree validation, initcall diagnostics and root-filesystem checks.

### What are TTBR0_EL1, TTBR1_EL1, TCR_EL1 and MAIR_EL1? {H}
**Short answer:** These registers configure stage-1 address translation for EL1 and EL0. TTBRs select translation-table roots, TCR controls translation parameters, and MAIR describes memory attribute encodings.

<figure style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 236" width="100%" role="img" aria-label="Translation tables select the physical mapping; the attribute index selects memory properties." font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="10" width="660" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="39" fill="#0c4a6e" font-size="14" font-weight="600">Virtual address</text><rect x="10" y="82" width="320" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="170" y="111" fill="#0c4a6e" font-size="14" font-weight="600">TTBR0 / TTBR1: table root</text><rect x="350" y="82" width="320" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="510" y="111" fill="#0c4a6e" font-size="14" font-weight="600">TCR: address size and granule</text><rect x="10" y="154" width="320" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="170" y="183" fill="#0c4a6e" font-size="14" font-weight="600">Page descriptor: AttrIndx</text><rect x="350" y="154" width="320" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="510" y="183" fill="#0c4a6e" font-size="14" font-weight="600">MAIR: memory type</text></svg><figcaption>Translation tables select the physical mapping; the attribute index selects memory properties.</figcaption></figure>

| Register | Role |
|---|---|
| TTBR0_EL1 / TTBR1_EL1 | Root table address and ASID field, subject to configuration |
| TCR_EL1 | VA size, granule, table-walk cacheability and shareability |
| MAIR_EL1 | Normal or Device memory attributes selected by descriptor AttrIndx |
| SCTLR_EL1 | Controls MMU and cache enablement among other settings |

**Example:** A Linux user VA typically uses the TTBR0 range; a kernel VA uses TTBR1. A page descriptor can map normal cacheable RAM or device MMIO using different attribute indices.

```asm
MRS X0, TTBR0_EL1 // privileged diagnostic read
MRS X1, TCR_EL1
MRS X2, MAIR_EL1
```

**Interview takeaway:** Page tables alone are insufficient; the translation configuration and attributes determine how the mapping behaves. Changing them requires the architecture-defined synchronization and invalidation sequence.

#### Concrete 4 KiB translation configuration

For a typical 48-bit VA setup, TCR_EL1.T0SZ and T1SZ may be 16, since 64−16=48 address bits for the respective ranges. TG0 and TG1 select the translation granules using their architecture-defined encodings; their encodings are not necessarily identical. TCR also describes table-walk cacheability/shareability, physical address size and other translation controls.

TTBR0_EL1 commonly serves the lower virtual-address range (userspace), while TTBR1_EL1 commonly serves the upper range (kernel). TTBR fields and ASID selection depend on the active translation configuration.

MAIR_EL1 contains eight eight-bit attribute slots in the conventional setup. A page descriptor's AttrIndx selects one of those slots. For example, an attribute byte of 0xFF denotes a common Normal write-back cacheable encoding, and 0x00 denotes Device-nGnRnE. Other descriptor bits supply permissions, execute-never and shareability information. These encodings are examples, not a claim that Linux uses a particular index on every system.

SCTLR_EL1.M controls stage-1 MMU enablement for the applicable regime. A valid table structure is not sufficient if the root address, granule, VA range or memory attributes are wrong. Updating live mappings must follow the architecture's break-before-make rules where applicable, TLB invalidation and required synchronization. Use kernel architecture helpers rather than arbitrary MSR sequences.

### What are ASIDs, VMIDs and TLB shootdowns? {H}
**Short answer:** ASIDs distinguish address spaces, VMIDs distinguish virtual-machine translation contexts, and a TLB shootdown invalidates cached translations on CPUs that could still use an outdated mapping.

<figure style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 236" width="100%" role="img" aria-label="Translation tags avoid unnecessary global invalidation; they do not remove the need to invalidate changed mappings." font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="10" width="320" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="170" y="39" fill="#0c4a6e" font-size="14" font-weight="600">Process A: ASID 5</text><rect x="350" y="10" width="320" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="510" y="39" fill="#0c4a6e" font-size="14" font-weight="600">Process B: ASID 6</text><rect x="10" y="82" width="660" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="111" fill="#0c4a6e" font-size="14" font-weight="600">Same VA, different cached translations</text><rect x="10" y="154" width="660" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="183" fill="#0c4a6e" font-size="14" font-weight="600">Mapping changes: invalidate affected TLB entries</text></svg><figcaption>Translation tags avoid unnecessary global invalidation; they do not remove the need to invalidate changed mappings.</figcaption></figure>

**1. Example:** Process A and B both access VA 0x4000, but A maps it to PA 0x10000 while B maps it to PA 0x20000. Non-global translations can be tagged with different ASIDs.

**2. When a mapping changes:** The OS updates page tables and ensures affected CPUs cannot keep using obsolete entries. ARM provides TLBI instructions and shareable invalidation forms; Linux uses architecture-specific TLB flushing helpers.

**3. VMID:** A hypervisor uses a VMID to distinguish stage-2 contexts. Reusing an identifier requires appropriate invalidation.

**Interview takeaway:** ASID/VMID tags improve context switching; invalidation maintains correctness when mappings or identifiers change.

#### Why identifiers reduce context-switch overhead

```text
TLB entry A: VA 0x4000 + ASID 7 -> PA 0x10000
TLB entry B: VA 0x4000 + ASID 8 -> PA 0x20000
```

With distinct valid ASIDs, a switch from process A to B need not discard every cached non-global translation. Global mappings follow their own matching rules. ASID space is finite, so the kernel manages reuse and invalidation, often with generation-based allocation.

VMIDs similarly distinguish guest stage-2 contexts. When a hypervisor reuses a VMID or changes a guest mapping, it must invalidate relevant cached translations according to architectural rules. Combined stage-1/stage-2 entries may be affected.

A shootdown is needed, for example, when one core unmaps a page that another core may still have cached. The OS updates translation structures, ensures descriptor writes are visible as required, invalidates the affected translations, and waits for the necessary completion before reusing physical memory. ARM shareable TLBI operations can target relevant cores without necessarily requiring a separate IPI to each one. A representative architectural pattern involves ordering table writes before TLBI, then waiting for invalidation completion and performing required context synchronization; exact instructions and scope depend on the mapping change. Use Linux's TLB flush interfaces and never free backing pages while another CPU can still access an obsolete mapping.

### What is the ARM SMMU and how does it differ from the CPU MMU? {H}
**Short answer:** A CPU MMU translates CPU virtual addresses; an SMMU (Arm's IOMMU architecture) translates and checks device DMA transactions. It can provide device isolation and an I/O virtual address space.

<figure style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 236" width="100%" role="img" aria-label="The CPU and device can use different addresses for the same physical buffer." font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="10" width="320" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="170" y="39" fill="#0c4a6e" font-size="14" font-weight="600">CPU virtual address</text><rect x="350" y="10" width="320" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="510" y="39" fill="#0c4a6e" font-size="14" font-weight="600">Device DMA address (IOVA)</text><rect x="10" y="82" width="320" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="170" y="111" fill="#0c4a6e" font-size="14" font-weight="600">CPU MMU</text><rect x="350" y="82" width="320" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="510" y="111" fill="#0c4a6e" font-size="14" font-weight="600">SMMU / IOMMU</text><rect x="10" y="154" width="660" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="183" fill="#0c4a6e" font-size="14" font-weight="600">Physical memory</text></svg><figcaption>The CPU and device can use different addresses for the same physical buffer.</figcaption></figure>

**1. Example:** A display controller reads a framebuffer through an IOVA. The SMMU translates it to the underlying physical pages and enforces access permissions.

**2. Linux flow:** allocate or obtain a suitable buffer, map it with the DMA API, check the result, program the device with the returned DMA address, then unmap after completion if streaming.

```c
dma_addr_t addr = dma_map_single(dev, buf, len, DMA_TO_DEVICE);
if (dma_mapping_error(dev, addr))
    return -EIO;
/* Program DMA address, wait for completion, then unmap. */
dma_unmap_single(dev, addr, len, DMA_TO_DEVICE);
```

**3. Important:** An SMMU does not automatically make a non-coherent device coherent. DMA addresses are not CPU pointers; a system may also use direct mapping or bounce buffers.

**Interview takeaway:** The SMMU is for device address translation and isolation; use Linux DMA APIs rather than assuming a physical address equals a DMA address.

#### Device DMA example with noncontiguous physical pages

A display framebuffer may occupy two physical pages at 0x90000000 and 0xA0000000. With a suitable SMMU mapping, the device can receive a contiguous IOVA range such as 0x40000000–0x40001FFF even though physical pages are noncontiguous. The CPU accesses the framebuffer through its own virtual mappings, while device transactions use the IOVA.

```text
CPU virtual address -> CPU MMU -> physical RAM
Display DMA IOVA    -> SMMU    -> same physical RAM
```

The SMMU selects translation context using device stream information and platform configuration. For an SMMUv3 implementation, stream-table entries identify relevant translation settings; context descriptors can supply stage-1 settings, and stage-2 translation can also be supported. Its translation caches require suitable invalidation when mappings change.

In Linux, dma_map_sg may map a scatter-gather list and return the number of DMA segments the device should use; that number can differ from the input entry count. Use each mapped segment's DMA address/length and unmap with the original entry count according to the API. Handle mapping errors, address-width constraints and device ownership.

An SMMU fault can indicate an unmapped IOVA, incorrect stream configuration, insufficient access permission or a DMA access after unmapping. Check the driver's mapping lifetime, device descriptors, DMA mask, IOMMU configuration and fault logs. Translation and isolation do not guarantee cache coherency; those are separate properties of the device's hardware path and software protocol.

### Explain complete interrupt flow in very brief for ARM. {M}

#### ARM Interrupt Flow (ARM Cortex-A)

An interrupt is a hardware or software event that temporarily stops normal CPU execution and transfers control to an Interrupt Service Routine (ISR).

In ARM Cortex-A processors, the **GIC (Generic Interrupt Controller)** manages hardware interrupts.

#### 1. Complete interrupt flow

```text
Peripheral (UART / GPIO / Timer)
Generates an interrupt
        ↓
GIC Distributor
Checks enable status, priority and CPU routing
        ↓
GIC CPU Interface
Signals an IRQ or FIQ to the CPU
        ↓
ARM CPU
Accepts interrupt and saves exception return state
        ↓
Exception Vector Table
Branches to IRQ exception handler
        ↓
Interrupt Handler
Saves registers and reads interrupt ID from GIC
        ↓
Device ISR
Services peripheral and clears interrupt source
        ↓
End of Interrupt (EOI)
Notifies GIC that interrupt handling is complete
        ↓
ERET
Restores execution of interrupted program
```

#### 2. Explanation of each step

**Step 1: Peripheral generates interrupt**

For example, UART receives data and sets an interrupt status bit. It asserts an interrupt signal to the GIC.

**Step 2: GIC processes interrupt**

The GIC checks:

- Whether the interrupt is enabled.
- Interrupt priority.
- Target CPU core.
- Priority masking and interrupt routing.

If eligible, it signals the CPU.

**Step 3: CPU saves execution state**

Assuming an ARM64 interrupt targeting EL1, the CPU automatically:

- Saves the return address in `ELR_EL1`.
- Saves processor state in `SPSR_EL1`.
- Masks further IRQ interrupts.
- Transfers execution to the exception vector.

General-purpose registers are saved by the software exception handler, not automatically by the CPU.

**Step 4: Exception vector table**

`VBAR_EL1` contains the base address of the exception vector table.

The CPU jumps to the appropriate IRQ vector based on the current exception level and execution state.

**Step 5: Identify interrupt**

The interrupt handler reads the GIC Interrupt Acknowledge Register.

```c
irq_id = read_sysreg(ICC_IAR1_EL1);
```

For GICv3, this returns the interrupt ID and acknowledges the interrupt.

**Step 6: Execute ISR**

The corresponding device ISR is executed.

```c
void uart_isr(void)
{
    data = UART_RX_REG;
    UART_INT_CLEAR = RX_INTERRUPT;
}
```

The ISR processes received data and clears the peripheral interrupt condition as required by the hardware.

**Step 7: End of interrupt**

The handler informs the GIC that interrupt processing is complete.

```c
write_sysreg(irq_id, ICC_EOIR1_EL1);
```

Depending on the GIC configuration, a separate deactivation operation may also be required.

**Step 8: Return from interrupt**

The software restores general-purpose registers and executes:

```asm
ERET
```

The CPU restores the processor state from `SPSR_EL1` and resumes execution using `ELR_EL1`.

#### 3. ARM Linux kernel interrupt flow

In a typical ARM64 Linux system with GICv3:

```text
Hardware interrupt
        ↓
GIC
        ↓
ARM64 exception vector
        ↓
el1h_64_irq_handler()  (example: interrupted EL1)
        ↓
gic_handle_irq()
        ↓
generic_handle_domain_irq()
        ↓
Linux IRQ flow handler
        ↓
Registered device ISR
        ↓
EOI / interrupt deactivation
        ↓
Restore context
        ↓
ERET
```

A Linux device driver registers its ISR using:

```c
request_irq(irq, uart_isr, 0, "uart", dev);
```

Exact internal function names and EOI placement depend on the kernel version and GIC configuration.

#### 4. Types of interrupts in ARM GIC

| Type | Full form | Example |
|---|---|---|
| SGI | Software Generated Interrupt | Inter-processor communication |
| PPI | Private Peripheral Interrupt | Per-core timer |
| SPI | Shared Peripheral Interrupt | UART, GPIO, I2C |
| LPI | Locality-specific Peripheral Interrupt | PCIe MSI |

**Interview summary:** Peripheral generates an interrupt → GIC routes it to the CPU → CPU saves exception state → exception vector handler identifies the interrupt → ISR executes → peripheral interrupt condition is cleared → GIC interrupt handling completes → CPU restores context and resumes execution.

Note: ARM Cortex-M uses an NVIC instead of a GIC and has a different hardware context-saving mechanism.

### What are L1, L2 and L3 caches? {M}

They are cache hierarchy levels, typically progressing from smaller and faster to larger and slower; sharing depends on the processor.


### What is a cache line? {M}

The fixed-size unit of cache allocation and coherence, commonly 64 bytes on modern CPUs.


### What is false sharing? {M}

Independent variables on the same cache line cause unnecessary coherence traffic when different cores write them.


### What is the MESI protocol? {M}

A coherence protocol with Modified, Exclusive, Shared and Invalid cache-line states.


### What is write-back versus write-through caching? {M}

Write-back delays lower-level writes until eviction or cleaning; write-through propagates writes to the next level promptly.


### What is cache eviction? {M}

Replacing a cached line to make space for another; dirty lines may require writeback.


### What are spatial and temporal locality? {M}

Spatial locality means accessing nearby addresses; temporal locality means reusing recently accessed data.

