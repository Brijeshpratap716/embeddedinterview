---
slug: arm-architecture
title: ARM Architecture
icon: 🧩
level: Intermediate
order: 24
desc: AArch64 registers, instructions, exception levels, MMU, TLB, cache coherency, barriers, interrupts, TrustZone, virtualization and boot flow.
---
Quick ARM architecture interview revision for embedded Linux, BSP, firmware and systems engineers. Each question includes a short answer, a visual explanation and a small code example. Assembly examples target AArch64; privileged examples require the appropriate exception level and platform configuration.

### What is ARM architecture and how do Cortex-A, R and M differ? {E}
**Short answer:** Arm is a family of instruction set architectures. Cortex-A targets application processors with an MMU, Cortex-R targets real-time systems, and Cortex-M targets microcontrollers.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="Cortex-A: Linux / Android to Cortex-R: Real-time to Cortex-M: MCU / RTOS" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="108.33333333333333" y="36" font-size="13" font-weight="600" fill="#172554">Cortex-A</text><text x="108.33333333333333" y="56" font-size="11" fill="#334155">Linux / Android</text><path d="M209.66666666666666 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="231.66666666666666" y="12" width="196.66666666666666" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="330" y="36" font-size="13" font-weight="600" fill="#172554">Cortex-R</text><text x="330" y="56" font-size="11" fill="#334155">Real-time</text><path d="M431.3333333333333 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="453.3333333333333" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="551.6666666666666" y="36" font-size="13" font-weight="600" fill="#172554">Cortex-M</text><text x="551.6666666666666" y="56" font-size="11" fill="#334155">MCU / RTOS</text></svg></div>

```asm
ADD X0, X1, X2 // AArch64 example
```

### What is AArch64 versus AArch32? {E}
**Short answer:** AArch64 is the 64-bit execution state using A64 instructions. AArch32 is the 32-bit state using A32 or T32 instructions, where supported. AArch64 instructions are 32 bits wide.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="AArch32: R0–R15 to AArch64: X0–X30" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="307.5" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="163.75" y="36" font-size="13" font-weight="600" fill="#172554">AArch32</text><text x="163.75" y="56" font-size="11" fill="#334155">R0–R15</text><path d="M320.5 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="342.5" y="12" width="307.5" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="496.25" y="36" font-size="13" font-weight="600" fill="#172554">AArch64</text><text x="496.25" y="56" font-size="11" fill="#334155">X0–X30</text></svg></div>

```asm
ADD W0, W1, W2 // 32-bit operation in AArch64
ADD X0, X1, X2 // 64-bit operation
```

### Do ARM64 registers contain data or addresses? {E}
**Short answer:** Both. X0–X30 hold 64-bit values; instructions determine whether those bits represent data or an address. Writing Wn zeroes the upper 32 bits of Xn.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="X1: 0x1000 to Memory: [0x1000] = 50 to X2: 50" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="108.33333333333333" y="36" font-size="13" font-weight="600" fill="#172554">X1</text><text x="108.33333333333333" y="56" font-size="11" fill="#334155">0x1000</text><path d="M209.66666666666666 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="231.66666666666666" y="12" width="196.66666666666666" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="330" y="36" font-size="13" font-weight="600" fill="#172554">Memory</text><text x="330" y="56" font-size="11" fill="#334155">[0x1000] = 50</text><path d="M431.3333333333333 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="453.3333333333333" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="551.6666666666666" y="36" font-size="13" font-weight="600" fill="#172554">X2</text><text x="551.6666666666666" y="56" font-size="11" fill="#334155">50</text></svg></div>

```asm
MOV X1, #0x1000
LDR X2, [X1] // assuming valid readable address
ADD X3, X2, #1
```

### What are SP, PC, LR and PSTATE? {E}
**Short answer:** SP is the stack pointer, PC tracks instruction execution, X30 is the conventional link register, and PSTATE holds execution state including NZCV flags and interrupt masks. PC is not an ordinary general-purpose register in A64.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="BL: Function call to X30: Return address to RET: Return" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="108.33333333333333" y="36" font-size="13" font-weight="600" fill="#172554">BL</text><text x="108.33333333333333" y="56" font-size="11" fill="#334155">Function call</text><path d="M209.66666666666666 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="231.66666666666666" y="12" width="196.66666666666666" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="330" y="36" font-size="13" font-weight="600" fill="#172554">X30</text><text x="330" y="56" font-size="11" fill="#334155">Return address</text><path d="M431.3333333333333 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="453.3333333333333" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="551.6666666666666" y="36" font-size="13" font-weight="600" fill="#172554">RET</text><text x="551.6666666666666" y="56" font-size="11" fill="#334155">Return</text></svg></div>

```asm
BL function
// ...
function:
    RET
```

### What is a load-store architecture? {E}
**Short answer:** Arithmetic normally uses registers; explicit loads and stores transfer data between registers and memory.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="Memory: Load to Registers: ALU operation to Memory: Store" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="108.33333333333333" y="36" font-size="13" font-weight="600" fill="#172554">Memory</text><text x="108.33333333333333" y="56" font-size="11" fill="#334155">Load</text><path d="M209.66666666666666 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="231.66666666666666" y="12" width="196.66666666666666" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="330" y="36" font-size="13" font-weight="600" fill="#172554">Registers</text><text x="330" y="56" font-size="11" fill="#334155">ALU operation</text><path d="M431.3333333333333 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="453.3333333333333" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="551.6666666666666" y="36" font-size="13" font-weight="600" fill="#172554">Memory</text><text x="551.6666666666666" y="56" font-size="11" fill="#334155">Store</text></svg></div>

```asm
LDR W0, [X1]
ADD W0, W0, #1
STR W0, [X1]
```

### What are ARM exception levels EL0 to EL3? {M}
**Short answer:** EL0 runs applications, EL1 normally runs the OS kernel, EL2 supports virtualization, and EL3 supports secure monitor functions. Availability depends on implementation.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="EL0: Application to EL1: Kernel to EL2: Hypervisor to EL3: Secure monitor" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="141.25" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="80.625" y="36" font-size="13" font-weight="600" fill="#172554">EL0</text><text x="80.625" y="56" font-size="11" fill="#334155">Application</text><path d="M154.25 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="176.25" y="12" width="141.25" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="246.875" y="36" font-size="13" font-weight="600" fill="#172554">EL1</text><text x="246.875" y="56" font-size="11" fill="#334155">Kernel</text><path d="M320.5 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="342.5" y="12" width="141.25" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="413.125" y="36" font-size="13" font-weight="600" fill="#172554">EL2</text><text x="413.125" y="56" font-size="11" fill="#334155">Hypervisor</text><path d="M486.75 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="508.75" y="12" width="141.25" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="579.375" y="36" font-size="13" font-weight="600" fill="#172554">EL3</text><text x="579.375" y="56" font-size="11" fill="#334155">Secure monitor</text></svg></div>

```asm
MRS X0, CurrentEL // privileged code
```

### How does a system call work on ARM64 Linux? {M}
**Short answer:** Userspace puts the syscall number in X8 and arguments in X0–X5, then executes SVC. The kernel handles the synchronous exception and returns a result in X0.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="EL0: SVC #0 to EL1: Syscall handler to EL0: ERET / result" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="108.33333333333333" y="36" font-size="13" font-weight="600" fill="#172554">EL0</text><text x="108.33333333333333" y="56" font-size="11" fill="#334155">SVC #0</text><path d="M209.66666666666666 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="231.66666666666666" y="12" width="196.66666666666666" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="330" y="36" font-size="13" font-weight="600" fill="#172554">EL1</text><text x="330" y="56" font-size="11" fill="#334155">Syscall handler</text><path d="M431.3333333333333 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="453.3333333333333" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="551.6666666666666" y="36" font-size="13" font-weight="600" fill="#172554">EL0</text><text x="551.6666666666666" y="56" font-size="11" fill="#334155">ERET / result</text></svg></div>

```asm
MOV X8, #172 // Linux arm64 getpid
SVC #0       // X0 = result
```

### What happens when an ARM64 exception occurs? {M}
**Short answer:** Hardware saves the return address and prior PSTATE in ELR_ELx and SPSR_ELx, selects a vector using VBAR_ELx, and transfers control. Software saves needed general registers; ERET restores the saved execution state.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="Exception: Hardware state save to Vector: VBAR_ELx to Handler: Save GPRs to ERET: Resume" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="141.25" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="80.625" y="36" font-size="13" font-weight="600" fill="#172554">Exception</text><text x="80.625" y="56" font-size="11" fill="#334155">Hardware state save</text><path d="M154.25 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="176.25" y="12" width="141.25" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="246.875" y="36" font-size="13" font-weight="600" fill="#172554">Vector</text><text x="246.875" y="56" font-size="11" fill="#334155">VBAR_ELx</text><path d="M320.5 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="342.5" y="12" width="141.25" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="413.125" y="36" font-size="13" font-weight="600" fill="#172554">Handler</text><text x="413.125" y="56" font-size="11" fill="#334155">Save GPRs</text><path d="M486.75 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="508.75" y="12" width="141.25" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="579.375" y="36" font-size="13" font-weight="600" fill="#172554">ERET</text><text x="579.375" y="56" font-size="11" fill="#334155">Resume</text></svg></div>

```asm
MRS X0, ESR_EL1 // exception syndrome
MRS X1, ELR_EL1 // exception return address
```

### What is the MMU? {M}
**Short answer:** The MMU translates virtual addresses into physical addresses using translation tables and enforces access permissions and memory attributes.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="CPU: Virtual address to MMU / TLB: Translation to Memory: Physical address" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="108.33333333333333" y="36" font-size="13" font-weight="600" fill="#172554">CPU</text><text x="108.33333333333333" y="56" font-size="11" fill="#334155">Virtual address</text><path d="M209.66666666666666 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="231.66666666666666" y="12" width="196.66666666666666" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="330" y="36" font-size="13" font-weight="600" fill="#172554">MMU / TLB</text><text x="330" y="56" font-size="11" fill="#334155">Translation</text><path d="M431.3333333333333 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="453.3333333333333" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="551.6666666666666" y="36" font-size="13" font-weight="600" fill="#172554">Memory</text><text x="551.6666666666666" y="56" font-size="11" fill="#334155">Physical address</text></svg></div>

```asm
MRS X0, TTBR0_EL1 // privileged: table base
```

### What is a TLB and what happens on a TLB miss? {M}
**Short answer:** The TLB caches address translations. On a miss, hardware normally walks translation tables; a valid translation can refill the TLB. Invalid mappings or permission violations can cause a fault.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="Virtual address: TLB lookup to Miss: Table walk to Physical address: Access" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="108.33333333333333" y="36" font-size="13" font-weight="600" fill="#172554">Virtual address</text><text x="108.33333333333333" y="56" font-size="11" fill="#334155">TLB lookup</text><path d="M209.66666666666666 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="231.66666666666666" y="12" width="196.66666666666666" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="330" y="36" font-size="13" font-weight="600" fill="#172554">Miss</text><text x="330" y="56" font-size="11" fill="#334155">Table walk</text><path d="M431.3333333333333 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="453.3333333333333" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="551.6666666666666" y="36" font-size="13" font-weight="600" fill="#172554">Physical address</text><text x="551.6666666666666" y="56" font-size="11" fill="#334155">Access</text></svg></div>

```asm
LDR X0, [X1] // translation performed if needed
```

### How does a memory access travel from CPU to DRAM? {M}
**Short answer:** A load uses an address in a register, translates it through the MMU, and checks caches. A cache miss can reach the coherent interconnect, memory controller and DRAM. Exact cache organization varies.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="CPU / MMU: Address to L1 / L2: Cache lookup to Interconnect: Miss to DRAM: Memory controller" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="141.25" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="80.625" y="36" font-size="13" font-weight="600" fill="#172554">CPU / MMU</text><text x="80.625" y="56" font-size="11" fill="#334155">Address</text><path d="M154.25 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="176.25" y="12" width="141.25" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="246.875" y="36" font-size="13" font-weight="600" fill="#172554">L1 / L2</text><text x="246.875" y="56" font-size="11" fill="#334155">Cache lookup</text><path d="M320.5 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="342.5" y="12" width="141.25" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="413.125" y="36" font-size="13" font-weight="600" fill="#172554">Interconnect</text><text x="413.125" y="56" font-size="11" fill="#334155">Miss</text><path d="M486.75 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="508.75" y="12" width="141.25" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="579.375" y="36" font-size="13" font-weight="600" fill="#172554">DRAM</text><text x="579.375" y="56" font-size="11" fill="#334155">Memory controller</text></svg></div>

```asm
LDR X2, [X1] // X1 = virtual address
```

### What happens when malloc(4 KB) is called on ARM64 Linux? {M}
**Short answer:** The allocator may reuse a free chunk or obtain virtual memory via brk/mmap. A first write to an unbacked anonymous page can fault, causing Linux to allocate a physical page and update the mapping. Allocation is not necessarily page-aligned.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="malloc: Allocator to brk / mmap: If needed to Page fault: If unbacked to Physical page: Retry" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="141.25" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="80.625" y="36" font-size="13" font-weight="600" fill="#172554">malloc</text><text x="80.625" y="56" font-size="11" fill="#334155">Allocator</text><path d="M154.25 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="176.25" y="12" width="141.25" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="246.875" y="36" font-size="13" font-weight="600" fill="#172554">brk / mmap</text><text x="246.875" y="56" font-size="11" fill="#334155">If needed</text><path d="M320.5 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="342.5" y="12" width="141.25" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="413.125" y="36" font-size="13" font-weight="600" fill="#172554">Page fault</text><text x="413.125" y="56" font-size="11" fill="#334155">If unbacked</text><path d="M486.75 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="508.75" y="12" width="141.25" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="579.375" y="36" font-size="13" font-weight="600" fill="#172554">Physical page</text><text x="579.375" y="56" font-size="11" fill="#334155">Retry</text></svg></div>

```c
char *p = malloc(4096);
if (p) { p[0] = 'A'; free(p); }
```

### What is cache coherency? {M}
**Short answer:** Hardware keeps coherent copies of a cache line consistent across cores. A writer typically obtains ownership and invalidates other copies; a later coherent reader obtains the updated value. DRAM need not be updated immediately.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="Core 0: a = 20 to Coherency fabric: Invalidate to Core 1: Reload = 20" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="108.33333333333333" y="36" font-size="13" font-weight="600" fill="#172554">Core 0</text><text x="108.33333333333333" y="56" font-size="11" fill="#334155">a = 20</text><path d="M209.66666666666666 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="231.66666666666666" y="12" width="196.66666666666666" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="330" y="36" font-size="13" font-weight="600" fill="#172554">Coherency fabric</text><text x="330" y="56" font-size="11" fill="#334155">Invalidate</text><path d="M431.3333333333333 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="453.3333333333333" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="551.6666666666666" y="36" font-size="13" font-weight="600" fill="#172554">Core 1</text><text x="551.6666666666666" y="56" font-size="11" fill="#334155">Reload = 20</text></svg></div>

```c
/* Use proper synchronization for shared data. */
smp_store_release(&flag, 1);
/* Other CPU: smp_load_acquire(&flag) */
```

### What is a memory barrier? {M}
**Short answer:** A barrier constrains memory ordering. On ARM, DMB orders relevant accesses, DSB also waits for required completion, and ISB synchronizes instruction execution after context changes.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="Write data: 100 to DMB: Ordering to Write flag: 1" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="108.33333333333333" y="36" font-size="13" font-weight="600" fill="#172554">Write data</text><text x="108.33333333333333" y="56" font-size="11" fill="#334155">100</text><path d="M209.66666666666666 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="231.66666666666666" y="12" width="196.66666666666666" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="330" y="36" font-size="13" font-weight="600" fill="#172554">DMB</text><text x="330" y="56" font-size="11" fill="#334155">Ordering</text><path d="M431.3333333333333 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="453.3333333333333" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="551.6666666666666" y="36" font-size="13" font-weight="600" fill="#172554">Write flag</text><text x="551.6666666666666" y="56" font-size="11" fill="#334155">1</text></svg></div>

```asm
STR W0, [X1]
DMB ISHST
STR W2, [X3]
```

### What is acquire and release ordering? {M}
**Short answer:** Release orders earlier accesses before publication; acquire orders later accesses after observing publication. Together they support safe producer-consumer communication.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="Producer: Write data to Release / Acquire: Publish flag to Consumer: Read data" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="108.33333333333333" y="36" font-size="13" font-weight="600" fill="#172554">Producer</text><text x="108.33333333333333" y="56" font-size="11" fill="#334155">Write data</text><path d="M209.66666666666666 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="231.66666666666666" y="12" width="196.66666666666666" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="330" y="36" font-size="13" font-weight="600" fill="#172554">Release / Acquire</text><text x="330" y="56" font-size="11" fill="#334155">Publish flag</text><path d="M431.3333333333333 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="453.3333333333333" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="551.6666666666666" y="36" font-size="13" font-weight="600" fill="#172554">Consumer</text><text x="551.6666666666666" y="56" font-size="11" fill="#334155">Read data</text></svg></div>

```asm
STLR W0, [X1] // release store
LDAR W2, [X1] // acquire load
```

### How do LDAXR and STLXR implement atomic operations? {H}
**Short answer:** An exclusive load establishes a reservation. An exclusive store succeeds only if the reservation remains valid; otherwise retry. Acquire/release forms provide ordering.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="LDAXR: Read / reserve to ADD: Modify to STLXR: Try store to Retry: On failure" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="141.25" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="80.625" y="36" font-size="13" font-weight="600" fill="#172554">LDAXR</text><text x="80.625" y="56" font-size="11" fill="#334155">Read / reserve</text><path d="M154.25 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="176.25" y="12" width="141.25" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="246.875" y="36" font-size="13" font-weight="600" fill="#172554">ADD</text><text x="246.875" y="56" font-size="11" fill="#334155">Modify</text><path d="M320.5 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="342.5" y="12" width="141.25" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="413.125" y="36" font-size="13" font-weight="600" fill="#172554">STLXR</text><text x="413.125" y="56" font-size="11" fill="#334155">Try store</text><path d="M486.75 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="508.75" y="12" width="141.25" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="579.375" y="36" font-size="13" font-weight="600" fill="#172554">Retry</text><text x="579.375" y="56" font-size="11" fill="#334155">On failure</text></svg></div>

```asm
1: LDAXR W0, [X1]
   ADD W0, W0, #1
   STLXR W2, W0, [X1]
   CBNZ W2, 1b
```

### What is the difference between normal and device memory? {M}
**Short answer:** Normal memory is suitable for RAM and may be cacheable. Device memory has stricter access attributes suitable for MMIO registers. Linux drivers use ioremap and appropriate I/O accessors.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="Normal: RAM / cache to Device: MMIO / peripheral" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="307.5" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="163.75" y="36" font-size="13" font-weight="600" fill="#172554">Normal</text><text x="163.75" y="56" font-size="11" fill="#334155">RAM / cache</text><path d="M320.5 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="342.5" y="12" width="307.5" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="496.25" y="36" font-size="13" font-weight="600" fill="#172554">Device</text><text x="496.25" y="56" font-size="11" fill="#334155">MMIO / peripheral</text></svg></div>

```c
void __iomem *base = ioremap(phys, size);
/* After checking base: */
writel(1, base);
```

### How does DMA interact with CPU caches? {M}
**Short answer:** A coherent device can participate in hardware coherency. Non-coherent DMA requires cache maintenance and ownership transitions; use Linux DMA mapping APIs to handle this.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="CPU cache: DMA mapping to RAM: DMA buffer to Device: DMA engine" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="108.33333333333333" y="36" font-size="13" font-weight="600" fill="#172554">CPU cache</text><text x="108.33333333333333" y="56" font-size="11" fill="#334155">DMA mapping</text><path d="M209.66666666666666 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="231.66666666666666" y="12" width="196.66666666666666" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="330" y="36" font-size="13" font-weight="600" fill="#172554">RAM</text><text x="330" y="56" font-size="11" fill="#334155">DMA buffer</text><path d="M431.3333333333333 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="453.3333333333333" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="551.6666666666666" y="36" font-size="13" font-weight="600" fill="#172554">Device</text><text x="551.6666666666666" y="56" font-size="11" fill="#334155">DMA engine</text></svg></div>

```c
dma_addr_t a = dma_map_single(dev, buf, len, DMA_TO_DEVICE);
/* Check dma_mapping_error; unmap after DMA completes. */
```

### What is ARM GIC? {M}
**Short answer:** The Generic Interrupt Controller routes and prioritizes interrupts. GICv3 uses a distributor, redistributors and CPU interfaces; an interrupt handler acknowledges and completes interrupts.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="Peripheral: IRQ to GIC: Route / priority to CPU: Exception handler" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="108.33333333333333" y="36" font-size="13" font-weight="600" fill="#172554">Peripheral</text><text x="108.33333333333333" y="56" font-size="11" fill="#334155">IRQ</text><path d="M209.66666666666666 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="231.66666666666666" y="12" width="196.66666666666666" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="330" y="36" font-size="13" font-weight="600" fill="#172554">GIC</text><text x="330" y="56" font-size="11" fill="#334155">Route / priority</text><path d="M431.3333333333333 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="453.3333333333333" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="551.6666666666666" y="36" font-size="13" font-weight="600" fill="#172554">CPU</text><text x="551.6666666666666" y="56" font-size="11" fill="#334155">Exception handler</text></svg></div>

```asm
MRS X0, ICC_IAR1_EL1 // acknowledge Group 1
// handle valid interrupt
MSR ICC_EOIR1_EL1, X0 // end priority
```

### What is TrustZone? {M}
**Short answer:** TrustZone provides hardware-backed security state separation. A typical system has a normal world and a secure world, with controlled transitions and protected resources.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="Normal world: Linux / Android to Secure monitor: SMC to Secure world: Trusted OS" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="108.33333333333333" y="36" font-size="13" font-weight="600" fill="#172554">Normal world</text><text x="108.33333333333333" y="56" font-size="11" fill="#334155">Linux / Android</text><path d="M209.66666666666666 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="231.66666666666666" y="12" width="196.66666666666666" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="330" y="36" font-size="13" font-weight="600" fill="#172554">Secure monitor</text><text x="330" y="56" font-size="11" fill="#334155">SMC</text><path d="M431.3333333333333 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="453.3333333333333" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="551.6666666666666" y="36" font-size="13" font-weight="600" fill="#172554">Secure world</text><text x="551.6666666666666" y="56" font-size="11" fill="#334155">Trusted OS</text></svg></div>

```asm
SMC #0 // monitor call, where permitted
```

### What is ARM virtualization at EL2? {H}
**Short answer:** EL2 lets a hypervisor control guest execution and traps. Stage-1 translation maps guest VA to IPA; stage-2 maps IPA to host PA.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="Guest VA: Stage 1 to IPA: Stage 2 to Host PA: Memory" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="108.33333333333333" y="36" font-size="13" font-weight="600" fill="#172554">Guest VA</text><text x="108.33333333333333" y="56" font-size="11" fill="#334155">Stage 1</text><path d="M209.66666666666666 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="231.66666666666666" y="12" width="196.66666666666666" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="330" y="36" font-size="13" font-weight="600" fill="#172554">IPA</text><text x="330" y="56" font-size="11" fill="#334155">Stage 2</text><path d="M431.3333333333333 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="453.3333333333333" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="551.6666666666666" y="36" font-size="13" font-weight="600" fill="#172554">Host PA</text><text x="551.6666666666666" y="56" font-size="11" fill="#334155">Memory</text></svg></div>

```asm
MRS X0, VTTBR_EL2 // stage-2 table base
```

### What is the ARM64 calling convention? {M}
**Short answer:** AAPCS64 passes ordinary integer/pointer arguments in X0–X7 and returns simple integer results in X0. X19–X28 are callee-saved; SP must be 16-byte aligned at public interfaces.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="Caller: X0–X7 arguments to Function: Compute to Return: X0 result" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="108.33333333333333" y="36" font-size="13" font-weight="600" fill="#172554">Caller</text><text x="108.33333333333333" y="56" font-size="11" fill="#334155">X0–X7 arguments</text><path d="M209.66666666666666 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="231.66666666666666" y="12" width="196.66666666666666" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="330" y="36" font-size="13" font-weight="600" fill="#172554">Function</text><text x="330" y="56" font-size="11" fill="#334155">Compute</text><path d="M431.3333333333333 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="453.3333333333333" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="551.6666666666666" y="36" font-size="13" font-weight="600" fill="#172554">Return</text><text x="551.6666666666666" y="56" font-size="11" fill="#334155">X0 result</text></svg></div>

```asm
add_two:
    ADD X0, X0, X1
    RET
```

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

### What is WFI versus WFE? {M}
**Short answer:** WFI waits for an interrupt or another permitted wake condition. WFE waits for an event or other permitted wake condition; SEV sends an event. Neither is a synchronization primitive by itself.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="WFI: Interrupt to WFE: Event to SEV: Signal event" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="108.33333333333333" y="36" font-size="13" font-weight="600" fill="#172554">WFI</text><text x="108.33333333333333" y="56" font-size="11" fill="#334155">Interrupt</text><path d="M209.66666666666666 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="231.66666666666666" y="12" width="196.66666666666666" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="330" y="36" font-size="13" font-weight="600" fill="#172554">WFE</text><text x="330" y="56" font-size="11" fill="#334155">Event</text><path d="M431.3333333333333 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="453.3333333333333" y="12" width="196.66666666666666" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="551.6666666666666" y="36" font-size="13" font-weight="600" fill="#172554">SEV</text><text x="551.6666666666666" y="56" font-size="11" fill="#334155">Signal event</text></svg></div>

```asm
WFI // idle hint
WFE // event wait hint
SEV // send event
```

### What is the difference between a cache clean and invalidate? {M}
**Short answer:** Cleaning writes dirty data toward the required coherency point; invalidation discards cached copies. Incorrect invalidation can lose dirty data. Use platform APIs for DMA.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="Clean: Cache → coherency point to Invalidate: Discard stale line" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="307.5" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="163.75" y="36" font-size="13" font-weight="600" fill="#172554">Clean</text><text x="163.75" y="56" font-size="11" fill="#334155">Cache → coherency point</text><path d="M320.5 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="342.5" y="12" width="307.5" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="496.25" y="36" font-size="13" font-weight="600" fill="#172554">Invalidate</text><text x="496.25" y="56" font-size="11" fill="#334155">Discard stale line</text></svg></div>

```asm
DC CVAC, X0 // clean by VA to PoC
DSB SY      // wait for completion; illustrative
```

### What is endianness in ARM? {E}
**Short answer:** Endianness determines the byte order of multi-byte values in memory. AArch64 supports little-endian data and implementation-dependent big-endian support; Linux commonly uses little-endian.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="Value: 0x12345678 to Low → high: 78 56 34 12" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="307.5" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="163.75" y="36" font-size="13" font-weight="600" fill="#172554">Value</text><text x="163.75" y="56" font-size="11" fill="#334155">0x12345678</text><path d="M320.5 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="342.5" y="12" width="307.5" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="496.25" y="36" font-size="13" font-weight="600" fill="#172554">Low → high</text><text x="496.25" y="56" font-size="11" fill="#334155">78 56 34 12</text></svg></div>

```asm
REV W0, W1 // reverse byte order
```

### What are NZCV condition flags? {E}
**Short answer:** N is negative, Z is zero, C is carry (or no borrow for subtraction), and V is signed overflow. Flag-setting instructions and conditional branches use them.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="CMP: Set NZCV to B.EQ: Branch if Z=1" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="307.5" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="163.75" y="36" font-size="13" font-weight="600" fill="#172554">CMP</text><text x="163.75" y="56" font-size="11" fill="#334155">Set NZCV</text><path d="M320.5 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="342.5" y="12" width="307.5" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="496.25" y="36" font-size="13" font-weight="600" fill="#172554">B.EQ</text><text x="496.25" y="56" font-size="11" fill="#334155">Branch if Z=1</text></svg></div>

```asm
CMP X0, #0
B.EQ is_zero
```

### What is the ARM64 boot flow? {M}
**Short answer:** Platform firmware initializes hardware and loads the next stage. A typical Linux flow is Boot ROM, platform firmware/bootloader, kernel entry, MMU setup and userspace init. Exact stages vary by SoC.

<div style="max-width:660px;margin:12px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 100" width="100%" role="img" aria-label="Boot ROM: Firmware to Bootloader: Kernel + DTB to Linux kernel: MMU / drivers to Userspace: PID 1" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="12" width="141.25" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="80.625" y="36" font-size="13" font-weight="600" fill="#172554">Boot ROM</text><text x="80.625" y="56" font-size="11" fill="#334155">Firmware</text><path d="M154.25 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="176.25" y="12" width="141.25" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="246.875" y="36" font-size="13" font-weight="600" fill="#172554">Bootloader</text><text x="246.875" y="56" font-size="11" fill="#334155">Kernel + DTB</text><path d="M320.5 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="342.5" y="12" width="141.25" height="68" rx="9" fill="#dbeafe" stroke="#2563eb"/><text x="413.125" y="36" font-size="13" font-weight="600" fill="#172554">Linux kernel</text><text x="413.125" y="56" font-size="11" fill="#334155">MMU / drivers</text><path d="M486.75 46 h18 m-6 -5 l6 5 -6 5" fill="none" stroke="#64748b" stroke-width="2"/><rect x="508.75" y="12" width="141.25" height="68" rx="9" fill="#dcfce7" stroke="#15803d"/><text x="579.375" y="36" font-size="13" font-weight="600" fill="#172554">Userspace</text><text x="579.375" y="56" font-size="11" fill="#334155">PID 1</text></svg></div>

```asm
// Linux arm64 boot protocol: X0 = DTB physical address
// X1–X3 = 0 at kernel entry
```
