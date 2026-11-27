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

### How does a memory access travel from CPU to DRAM? {M}
**Short answer:** A load uses an address in a register, translates it through the MMU, and checks caches. A cache miss can reach the coherent interconnect, memory controller and DRAM. Exact cache organization varies.

<figure style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 350" width="100%" role="img" aria-label="Load uses virtual address; TLB miss triggers page walk; cache miss reaches interconnect and possibly DRAM." font-family="system-ui,sans-serif" text-anchor="middle"><g fill="#e0f2fe" stroke="#0369a1"><rect x="210" y="10" width="260" height="40" rx="7"/><rect x="210" y="75" width="260" height="40" rx="7"/><rect x="500" y="75" width="165" height="40" rx="7"/><rect x="210" y="140" width="260" height="40" rx="7"/><rect x="10" y="140" width="165" height="40" rx="7"/><rect x="210" y="205" width="260" height="40" rx="7"/><rect x="500" y="205" width="165" height="40" rx="7"/><rect x="210" y="270" width="260" height="50" rx="7"/></g><g fill="#0c4a6e" font-size="13"><text x="340" y="35">LDR: virtual address</text><text x="340" y="100">MMU / TLB</text><text x="582" y="100">Page-table walk</text><text x="340" y="165">Cache hierarchy</text><text x="92" y="165">Hit: return bytes</text><text x="340" y="230">Coherent interconnect</text><text x="582" y="230">Peer cache may supply</text><text x="340" y="290">Memory controller</text><text x="340" y="307">DRAM if required</text></g><g stroke="#475569" stroke-width="2" fill="none"><path d="M340 50v25m-5-6 5 6 5-6 M340 115v25m-5-6 5 6 5-6 M340 180v25m-5-6 5 6 5-6 M340 245v25m-5-6 5 6 5-6 M470 95h30m-6-5 6 5-6 5 M210 160h-35m6-5-6 5 6 5 M470 225h30m-6-5 6 5-6 5"/></g><g fill="#475569" font-size="11"><text x="485" y="87">miss</text><text x="192" y="152">hit</text><text x="364" y="195">miss</text></g></svg><figcaption>Conceptual data-access flow; cache and translation lookups can overlap.</figcaption></figure>

```asm
LDR X2, [X1] // X1 = virtual address
```

**1. Instruction:** LDR computes an effective virtual address from X1 and any offset.

**2. Translation:** The MMU checks the TLB; a miss can trigger a page-table walk. Permissions and memory attributes are checked.

**3. Cache lookup:** The CPU searches its cache hierarchy. Translation and cache lookup may overlap depending on implementation.

**4. Cache miss:** The coherent interconnect can obtain data from another core or a shared cache. If no cached copy supplies it, the memory controller accesses DRAM and returns the cache line.

**5. Result:** The requested bytes are delivered to X2. For stores, a write-back cache may retain dirty data without immediately updating DRAM.

**Interview takeaway:** Not every load reaches DRAM. Registers, translation, caches, coherency fabric and memory controller all participate as needed.

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

### What are ASIDs, VMIDs and TLB shootdowns? {H}
**Short answer:** ASIDs distinguish address spaces, VMIDs distinguish virtual-machine translation contexts, and a TLB shootdown invalidates cached translations on CPUs that could still use an outdated mapping.

<figure style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 236" width="100%" role="img" aria-label="Translation tags avoid unnecessary global invalidation; they do not remove the need to invalidate changed mappings." font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="10" width="320" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="170" y="39" fill="#0c4a6e" font-size="14" font-weight="600">Process A: ASID 5</text><rect x="350" y="10" width="320" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="510" y="39" fill="#0c4a6e" font-size="14" font-weight="600">Process B: ASID 6</text><rect x="10" y="82" width="660" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="111" fill="#0c4a6e" font-size="14" font-weight="600">Same VA, different cached translations</text><rect x="10" y="154" width="660" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="183" fill="#0c4a6e" font-size="14" font-weight="600">Mapping changes: invalidate affected TLB entries</text></svg><figcaption>Translation tags avoid unnecessary global invalidation; they do not remove the need to invalidate changed mappings.</figcaption></figure>

**1. Example:** Process A and B both access VA 0x4000, but A maps it to PA 0x10000 while B maps it to PA 0x20000. Non-global translations can be tagged with different ASIDs.

**2. When a mapping changes:** The OS updates page tables and ensures affected CPUs cannot keep using obsolete entries. ARM provides TLBI instructions and shareable invalidation forms; Linux uses architecture-specific TLB flushing helpers.

**3. VMID:** A hypervisor uses a VMID to distinguish stage-2 contexts. Reusing an identifier requires appropriate invalidation.

**Interview takeaway:** ASID/VMID tags improve context switching; invalidation maintains correctness when mappings or identifiers change.

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
