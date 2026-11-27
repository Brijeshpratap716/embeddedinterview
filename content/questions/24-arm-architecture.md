---
slug: arm-architecture
title: ARM Architecture
icon: 🧩
level: Intermediate
order: 24
desc: AArch64 registers, instructions, exception levels, MMU, TLB, cache coherency, barriers, interrupts, TrustZone, virtualization and boot flow.
---
Concise Arm architecture interview notes for firmware, BSP and Linux engineers. Each answer explains the mechanism, illustrates it with a diagram and practical example, and highlights the key limitation. Privileged examples require the appropriate exception level.

### What is ARM architecture and how do Cortex-A, R and M differ? {E}
**Short answer:** Arm defines the instruction set and programmer-visible behavior; Cortex cores are implementations optimized for different jobs.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 92" width="100%" role="img" aria-label="Cortex-A / Linux, Cortex-R / Real time, Cortex-M / Firmware" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="12" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="116.66666666666667" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Cortex-A / Linux</text><rect x="235.33333333333334" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Cortex-R / Real time</text><rect x="458.6666666666667" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="563.3333333333334" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Cortex-M / Firmware</text></svg></div>

**How it works**

1. Cortex-A targets rich operating systems with virtual memory.
2. Cortex-R prioritizes predictable response and safety; some models include MMUs.
3. Cortex-M targets low-power microcontrollers and uses the M-profile exception model.

**Example:** A phone runs Android on Cortex-A; a sensor node uses Cortex-M; a real-time storage controller may use Cortex-R.

**Interview takeaway:** ISA compatibility does not imply identical cache, pipeline or peripheral design.

### What is AArch64 versus AArch32? {E}
**Short answer:** AArch64 is the 64-bit execution state using A64 instructions; AArch32 is the 32-bit state using A32 or T32 where implemented.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 92" width="100%" role="img" aria-label="AArch32: R0–R15, AArch64: X0–X30" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="12" y="12" width="321" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="172.5" y="49" font-size="12" font-weight="600" fill="#0c4a6e">AArch32: R0–R15</text><rect x="347" y="12" width="321" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="507.5" y="49" font-size="12" font-weight="600" fill="#0c4a6e">AArch64: X0–X30</text></svg></div>

**How it works**

1. A64 instructions are fixed 32-bit encodings.
2. X0–X30 are 64-bit registers; W0–W30 name their low halves.
3. Writing Wn clears the upper half of Xn.

**Example:** If X1 = 0x1234567800000001, W1 reads 1; writing W1 = 2 makes X1 = 2.

```asm
ADD W0, W1, W2
ADD X0, X1, X2
```

**Interview takeaway:** A 64-bit processor need not support AArch32, and VA/PA width need not be 64 bits.

### Do ARM64 registers contain data or addresses? {E}
**Short answer:** General-purpose ARM64 registers contain bits, not typed data or pointers. The instruction determines their interpretation.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 92" width="100%" role="img" aria-label="X1: 0x1000 then Memory[0x1000]: 50 then X2: 50" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="12" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="116.66666666666667" y="49" font-size="12" font-weight="600" fill="#0c4a6e">X1: 0x1000</text><path d="M222.33333333333334 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="235.33333333333334" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Memory[0x1000]: 50</text><path d="M445.6666666666667 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="458.6666666666667" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="563.3333333333334" y="49" font-size="12" font-weight="600" fill="#0c4a6e">X2: 50</text></svg></div>

**How it works**

1. MOV copies a value into a register.
2. LDR treats the base register as an address and reads the indicated memory.
3. ADD uses the values as arithmetic operands; STR writes a register value to memory.

**Example:** If X1 holds 0x1000 and eight readable bytes there encode 50, LDR X2,[X1] loads 50.

```asm
MOV X1, #0x1000
LDR X2, [X1]
ADD X3, X2, #1
```

**Interview takeaway:** An address must be valid and accessible; with translation enabled it is normally a virtual address.

### What are SP, PC, LR and PSTATE? {E}
**Short answer:** SP identifies the current stack, PC represents the instruction address, LR (X30) conventionally holds a return address, and PSTATE holds execution state.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 92" width="100%" role="img" aria-label="BL function then X30 = return address then RET" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="12" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="116.66666666666667" y="49" font-size="12" font-weight="600" fill="#0c4a6e">BL function</text><path d="M222.33333333333334 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="235.33333333333334" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="49" font-size="12" font-weight="600" fill="#0c4a6e">X30 = return address</text><path d="M445.6666666666667 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="458.6666666666667" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="563.3333333333334" y="49" font-size="12" font-weight="600" fill="#0c4a6e">RET</text></svg></div>

**How it works**

1. BL writes the next instruction address into X30 and branches.
2. A non-leaf function normally saves LR before calling another function.
3. RET defaults to X30; PSTATE includes flags and interrupt masks.

**Example:** A function calling another function must preserve its original return address.

```asm
BL func
// execution resumes here
// ...
func:
    RET
```

**Interview takeaway:** PC is not a general-purpose A64 register; ADR/ADRP form PC-relative addresses.

### What is a load-store architecture? {E}
**Short answer:** Arm separates data-memory transfers from ordinary arithmetic instructions: loads and stores move data, while arithmetic uses registers.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 92" width="100%" role="img" aria-label="Load: 10 then ALU: 10 + 1 then Store: 11" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="12" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="116.66666666666667" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Load: 10</text><path d="M222.33333333333334 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="235.33333333333334" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="49" font-size="12" font-weight="600" fill="#0c4a6e">ALU: 10 + 1</text><path d="M445.6666666666667 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="458.6666666666667" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="563.3333333333334" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Store: 11</text></svg></div>

**How it works**

1. Load an integer into a register.
2. Perform an ALU operation.
3. Store the updated value if memory needs to change.

**Example:** Incrementing *p from 10 to 11 may use three instructions.

```asm
LDR W0, [X1]
ADD W0, W0, #1
STR W0, [X1]
```

**Interview takeaway:** This load/add/store sequence is not an atomic read-modify-write.

### What are ARM exception levels EL0 to EL3? {M}
**Short answer:** Exception levels define privilege in A-profile Arm. EL0 is least privileged; EL1 is normally the OS, EL2 the hypervisor and EL3 the secure monitor.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 240" width="100%" role="img" aria-label="EL3: secure monitor, EL2: hypervisor, EL1: OS kernel, EL0: application" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="130" y="8" width="420" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="36" font-size="12" font-weight="600" fill="#0c4a6e">EL3: secure monitor</text><rect x="130" y="64" width="420" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="92" font-size="12" font-weight="600" fill="#0c4a6e">EL2: hypervisor</text><rect x="130" y="120" width="420" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="148" font-size="12" font-weight="600" fill="#0c4a6e">EL1: OS kernel</text><rect x="130" y="176" width="420" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="204" font-size="12" font-weight="600" fill="#0c4a6e">EL0: application</text></svg></div>

**How it works**

1. An exception can transfer execution to its configured target level.
2. The target has privileged registers and exception vectors.
3. ERET restores the saved return state; execution need not pass through every EL.

**Example:** A normal Linux userspace system call uses SVC to enter the kernel, usually EL1.

```asm
MRS X0, CurrentEL // privileged read
```

**Interview takeaway:** EL2 and EL3 availability depends on implementation; VHE can run host kernel code at EL2.

### How does a system call work on ARM64 Linux? {M}
**Short answer:** A Linux ARM64 system call is a controlled exception from userspace into the kernel.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 92" width="100%" role="img" aria-label="EL0: SVC then Kernel: dispatch then EL0: return" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="12" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="116.66666666666667" y="49" font-size="12" font-weight="600" fill="#0c4a6e">EL0: SVC</text><path d="M222.33333333333334 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="235.33333333333334" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Kernel: dispatch</text><path d="M445.6666666666667 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="458.6666666666667" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="563.3333333333334" y="49" font-size="12" font-weight="600" fill="#0c4a6e">EL0: return</text></svg></div>

**How it works**

1. The syscall ABI uses X8 for the number and X0–X5 for arguments.
2. SVC #0 triggers a synchronous exception; entry code saves state and dispatches the syscall.
3. The return value is placed in X0 and ERET resumes userspace.

**Example:** getpid has syscall number 172 on Linux AArch64; libc normally handles this ABI.

```asm
MOV X8, #172
SVC #0
```

**Interview takeaway:** Raw failures are negative errno values; libc usually returns -1 and sets errno.

### What happens when an ARM64 exception occurs? {M}
**Short answer:** An exception redirects execution to an exception handler and saves the architectural return state.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 92" width="100%" role="img" aria-label="Exception then Vector / saved state then Handler then ERET" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="12" y="12" width="153.5" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="88.75" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Exception</text><path d="M166.5 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="179.5" y="12" width="153.5" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="256.25" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Vector / saved state</text><path d="M334 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="347" y="12" width="153.5" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="423.75" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Handler</text><path d="M501.5 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="514.5" y="12" width="153.5" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="591.25" y="49" font-size="12" font-weight="600" fill="#0c4a6e">ERET</text></svg></div>

**How it works**

1. Hardware saves the return PC and PSTATE in ELR_ELx and SPSR_ELx at the target EL.
2. The vector comes from VBAR_ELx plus the applicable offset; ESR_ELx can describe synchronous faults.
3. Software saves general registers as needed, handles the event and returns with ERET if appropriate.

**Example:** An invalid data access can raise a Data Abort; the kernel examines ESR and FAR where valid.

**Interview takeaway:** Hardware does not automatically push all AArch64 general registers onto a stack.

### What is the MMU? {M}
**Short answer:** The MMU translates virtual addresses, enforces permissions and supplies memory attributes.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 92" width="100%" role="img" aria-label="Virtual address then MMU / page tables then Physical address" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="12" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="116.66666666666667" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Virtual address</text><path d="M222.33333333333334 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="235.33333333333334" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="49" font-size="12" font-weight="600" fill="#0c4a6e">MMU / page tables</text><path d="M445.6666666666667 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="458.6666666666667" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="563.3333333333334" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Physical address</text></svg></div>

**How it works**

1. The CPU issues a virtual address; the MMU looks for a cached translation.
2. On a miss it walks translation tables when configured to do so.
3. A valid descriptor gives the physical mapping and permissions; an invalid or forbidden access raises a fault.

**Example:** VA 0x40001234 mapped to physical page 0x80000000 with 4 KiB pages becomes PA 0x80000234.

**Interview takeaway:** A page fault is not the same as a TLB miss; the mapping may be found without kernel intervention.

### What is a TLB and what happens on a TLB miss? {M}
**Short answer:** The TLB is a small translation cache that avoids repeatedly walking page tables.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 92" width="100%" role="img" aria-label="VA then TLB lookup then Hit: translate" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="12" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="116.66666666666667" y="49" font-size="12" font-weight="600" fill="#0c4a6e">VA</text><path d="M222.33333333333334 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="235.33333333333334" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="49" font-size="12" font-weight="600" fill="#0c4a6e">TLB lookup</text><path d="M445.6666666666667 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="458.6666666666667" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="563.3333333333334" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Hit: translate</text></svg></div>

**How it works**

1. Look up the virtual page and relevant address-space tag.
2. If a valid cached translation exists, use it.
3. Otherwise a hardware table walk can refill the TLB; translation or permission faults are handled separately.

**Example:** Many loads within one 4 KiB page can reuse the same translation.

**Interview takeaway:** A TLB caches translations and attributes, not the data stored in memory.

### How does a memory access travel from CPU to DRAM? {M}
**Short answer:** An ordinary load reaches DRAM only when the memory hierarchy cannot supply its data sooner.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 92" width="100%" role="img" aria-label="CPU / virtual address then MMU / TLB then Cache hierarchy then Fabric / DRAM if needed" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="12" y="12" width="153.5" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="88.75" y="49" font-size="12" font-weight="600" fill="#0c4a6e">CPU / virtual address</text><path d="M166.5 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="179.5" y="12" width="153.5" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="256.25" y="49" font-size="12" font-weight="600" fill="#0c4a6e">MMU / TLB</text><path d="M334 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="347" y="12" width="153.5" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="423.75" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Cache hierarchy</text><path d="M501.5 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="514.5" y="12" width="153.5" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="591.25" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Fabric / DRAM if needed</text></svg></div>

**How it works**

1. Decode LDR and calculate the effective virtual address.
2. Translate through the MMU/TLB and check permissions; a TLB miss may walk tables.
3. Check caches; a cache miss may be served by a shared cache or another coherent core.
4. If needed, the memory controller reads DRAM and returns the requested cache line.

**Example:** LDR X2,[X1] may be satisfied entirely by L1. A write-back store may remain dirty in cache.

```asm
LDR X2, [X1]
```

**Interview takeaway:** Translation and cache lookups may overlap; MMIO follows device-memory rules.

### What happens when malloc(4 KB) is called on ARM64 Linux? {M}
**Short answer:** malloc returns a userspace virtual address to an allocation, not necessarily a fresh physical page.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 92" width="100%" role="img" aria-label="malloc then Allocator / VA then First touch if needed then Physical page" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="12" y="12" width="153.5" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="88.75" y="49" font-size="12" font-weight="600" fill="#0c4a6e">malloc</text><path d="M166.5 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="179.5" y="12" width="153.5" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="256.25" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Allocator / VA</text><path d="M334 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="347" y="12" width="153.5" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="423.75" y="49" font-size="12" font-weight="600" fill="#0c4a6e">First touch if needed</text><path d="M501.5 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="514.5" y="12" width="153.5" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="591.25" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Physical page</text></svg></div>

**How it works**

1. The allocator first checks reusable blocks and may request virtual memory with brk or mmap.
2. When a previously unbacked page is first written, a page fault may allocate and map physical memory.
3. The MMU and TLB translate later accesses; free returns the block to the allocator, which may retain it.

**Example:** Writing p[0] after malloc(4096) can trigger a demand fault; reused heap storage may already be mapped.

```c
#include <stdlib.h>
void demo(void) {
    unsigned char *p = malloc(4096);
    if (p) { p[0] = 42; free(p); }
}
```

**Interview takeaway:** 4 KiB allocation size does not guarantee page alignment, one page, or a syscall.

### What is cache coherency? {M}
**Short answer:** Cache coherency keeps participating cached copies of a memory location consistent.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 92" width="100%" role="img" aria-label="Core 0 writes 20 then Coherence fabric then Core 1 reads 20" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="12" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="116.66666666666667" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Core 0 writes 20</text><path d="M222.33333333333334 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="235.33333333333334" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Coherence fabric</text><path d="M445.6666666666667 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="458.6666666666667" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="563.3333333333334" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Core 1 reads 20</text></svg></div>

**How it works**

1. Both cores can initially cache a line containing 10.
2. A writer obtains permission to modify the line; other copies are invalidated or updated according to the protocol.
3. A later coherent reader obtains the current value from the appropriate cache or memory.

**Example:** Core 0 changes a from 10 to 20; after synchronization Core 1 can observe 20 even if DRAM has not been updated.

**Interview takeaway:** Coherency does not provide ordering across different locations, atomic increments or automatic coherence for every DMA device.

### What is a memory barrier? {M}
**Short answer:** A memory barrier constrains the ordering of memory operations; it does not inherently flush caches or make operations atomic.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 92" width="100%" role="img" aria-label="Producer: data → barrier → flag, Consumer: flag → barrier → data" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="12" y="12" width="321" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="172.5" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Producer: data → barrier → flag</text><rect x="347" y="12" width="321" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="507.5" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Consumer: flag → barrier → data</text></svg></div>

**How it works**

1. Without ordering, a consumer can observe a published flag before the associated data on a weakly ordered system.
2. The producer writes data, executes a write barrier and publishes the flag.
3. The consumer reads the flag, executes a read barrier and reads data.

**Example:** One-time Linux kernel publication: data and flag start at 0. If the consumer observes flag = 1 with the paired barriers, it can read the published 100.

```c
// Producer
WRITE_ONCE(data, 100);
smp_wmb();
WRITE_ONCE(flag, 1);

// Consumer
if (READ_ONCE(flag) == 1) {
    smp_rmb();
    value = READ_ONCE(data);
}
```

| ARM instruction | Purpose |
|---|---|
| DMB | Orders relevant memory accesses within its scope |
| DSB | Waits for required completion as well |
| ISB | Synchronizes subsequent instruction execution with context changes |

| Linux API | Purpose |
|---|---|
| smp_rmb() / smp_wmb() | Order reads / writes respectively |
| smp_mb() | Full SMP memory barrier |
| barrier() | Compiler barrier only |
| smp_store_release() / smp_load_acquire() | Directional publication and consumption ordering |

**Cache coherency vs barriers:** Coherency keeps copies of a cache line consistent; barriers constrain ordering between accesses. Neither substitutes for the other.

**Interview takeaway:** Use C11 atomics for portable threaded C, not racing plain variables; devices require appropriate DMA/MMIO APIs.

### What is acquire and release ordering? {M}
**Short answer:** Release publishes earlier accesses before a synchronization operation; acquire orders later accesses after it.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 92" width="100%" role="img" aria-label="Write payload then Release flag then Acquire flag then Read payload" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="12" y="12" width="153.5" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="88.75" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Write payload</text><path d="M166.5 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="179.5" y="12" width="153.5" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="256.25" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Release flag</text><path d="M334 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="347" y="12" width="153.5" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="423.75" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Acquire flag</text><path d="M501.5 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="514.5" y="12" width="153.5" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="591.25" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Read payload</text></svg></div>

**How it works**

1. Producer initializes the payload.
2. Producer performs a release store to a flag.
3. Consumer performs an acquire load; if it reads that release, preceding producer operations happen-before the consumer's subsequent operations in C11.

**Example:** A one-time initialized configuration becomes readable after an atomic ready flag is published.

```c
// C11, one producer and one-time publication
static int data;
static _Atomic int ready;
// producer: data = 100; atomic_store_explicit(&ready, 1, memory_order_release);
// consumer: if (atomic_load_explicit(&ready, memory_order_acquire)) use(data);
```

**Interview takeaway:** Acquire and release are directional; neither makes a multi-step protocol safe without ownership rules.

### How do LDAXR and STLXR implement atomic operations? {H}
**Short answer:** LDAXR and STLXR form an acquire/release exclusive-access loop for atomic read-modify-write operations.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 92" width="100%" role="img" aria-label="LDAXR then ADD then STLXR then Retry if failed" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="12" y="12" width="153.5" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="88.75" y="49" font-size="12" font-weight="600" fill="#0c4a6e">LDAXR</text><path d="M166.5 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="179.5" y="12" width="153.5" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="256.25" y="49" font-size="12" font-weight="600" fill="#0c4a6e">ADD</text><path d="M334 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="347" y="12" width="153.5" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="423.75" y="49" font-size="12" font-weight="600" fill="#0c4a6e">STLXR</text><path d="M501.5 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="514.5" y="12" width="153.5" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="591.25" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Retry if failed</text></svg></div>

**How it works**

1. LDAXR reads a value and establishes an exclusive reservation.
2. Compute the new value and attempt STLXR.
3. STLXR reports success (0) or failure; retry if the reservation was lost.

**Example:** An atomic increment retries rather than overwriting a concurrent update.

```asm
1: LDAXR W0, [X1]
   ADD W0, W0, #1
   STLXR W2, W0, [X1]
   CBNZ W2, 1b
```

**Interview takeaway:** Use properly aligned supported memory; LSE atomics may replace exclusive loops on supporting CPUs.

### What is the difference between normal and device memory? {M}
**Short answer:** Normal memory is intended for ordinary data and may be cached/speculated; Device memory is for registers with side effects and has stricter access rules.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 92" width="100%" role="img" aria-label="Normal: RAM / cacheable, Device: MMIO / side effects" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="12" y="12" width="321" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="172.5" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Normal: RAM / cacheable</text><rect x="347" y="12" width="321" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="507.5" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Device: MMIO / side effects</text></svg></div>

**How it works**

1. A page-table descriptor selects an attribute encoding from MAIR.
2. Normal memory may use write-back caches and speculative reads.
3. Device memory subtypes restrict gathering, reordering and early acknowledgement according to their attributes.

**Example:** DRAM holding an array is normal memory; a UART status register is mapped as Device memory.

**Interview takeaway:** Device mappings alone do not replace required barriers and accessor APIs.

### How does DMA interact with CPU caches? {M}
**Short answer:** DMA transfers data without the CPU copying each byte. A non-coherent DMA master may not see dirty CPU cache lines, and the CPU may see stale cached receive data.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 92" width="100%" role="img" aria-label="CPU cache then DMA API / ownership then Device / RAM" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="12" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="116.66666666666667" y="49" font-size="12" font-weight="600" fill="#0c4a6e">CPU cache</text><path d="M222.33333333333334 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="235.33333333333334" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="49" font-size="12" font-weight="600" fill="#0c4a6e">DMA API / ownership</text><path d="M445.6666666666667 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="458.6666666666667" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="563.3333333333334" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Device / RAM</text></svg></div>

**How it works**

1. For TX, prepare/map the buffer before transferring ownership to hardware.
2. For RX, prepare the buffer before DMA and synchronize/unmap after completion before reading.
3. Use the DMA API to obtain a device-visible address and manage ownership and cache maintenance.

**Example:** Linux maps a TX packet with dma_map_single, checks the mapping, programs the device and unmaps after completion.

```c
dma_addr_t a = dma_map_single(dev, buf, len, DMA_TO_DEVICE);
if (dma_mapping_error(dev, a)) return -EIO;
/* Start DMA using a; wait for device completion. */
dma_unmap_single(dev, a, len, DMA_TO_DEVICE);
```

**Interview takeaway:** Coherent allocations still need ordering for descriptor ownership; never assume a CPU pointer is a DMA address.

### What is ARM GIC? {M}
**Short answer:** The Generic Interrupt Controller routes and prioritizes interrupts for Arm A-profile systems.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 92" width="100%" role="img" aria-label="Peripheral IRQ then GIC routing then CPU handler then EOI / deactivate" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="12" y="12" width="153.5" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="88.75" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Peripheral IRQ</text><path d="M166.5 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="179.5" y="12" width="153.5" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="256.25" y="49" font-size="12" font-weight="600" fill="#0c4a6e">GIC routing</text><path d="M334 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="347" y="12" width="153.5" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="423.75" y="49" font-size="12" font-weight="600" fill="#0c4a6e">CPU handler</text><path d="M501.5 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="514.5" y="12" width="153.5" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="591.25" y="49" font-size="12" font-weight="600" fill="#0c4a6e">EOI / deactivate</text></svg></div>

**How it works**

1. A peripheral asserts an interrupt; the distributor handles shared peripheral interrupts.
2. A GICv3 redistributor handles per-CPU interrupt state and the CPU interface signals an eligible core.
3. The handler acknowledges the interrupt, services/clears the device and signals completion; deactivation depends on configuration.

**Example:** A UART IRQ can be routed to a chosen CPU and masked by interrupt priority.

**Interview takeaway:** GIC versions differ; SGIs are software-generated, PPIs private and SPIs shared peripheral interrupts.

### What is TrustZone? {M}
**Short answer:** TrustZone separates security states so sensitive code and resources can be isolated from normal-world software.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 92" width="100%" role="img" aria-label="Normal world then Secure monitor then Secure world" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="12" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="116.66666666666667" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Normal world</text><path d="M222.33333333333334 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="235.33333333333334" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Secure monitor</text><path d="M445.6666666666667 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="458.6666666666667" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="563.3333333333334" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Secure world</text></svg></div>

**How it works**

1. Hardware security attributes and platform controllers protect memory and peripherals.
2. A secure monitor can mediate world transitions; a trusted OS may run trusted applications.
3. Normal-world software uses a defined interface, often SMC-based, to request a secure service.

**Example:** A normal-world client requests a key operation without reading the protected key.

**Interview takeaway:** Secure state and exception level are separate concepts; security depends on correct platform configuration.

### What is ARM virtualization at EL2? {H}
**Short answer:** EL2 supports hypervisors through trap controls, stage-2 translation and virtual interrupt/timer facilities.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 92" width="100%" role="img" aria-label="Guest VA then Stage 1: IPA then Stage 2: PA" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="12" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="116.66666666666667" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Guest VA</text><path d="M222.33333333333334 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="235.33333333333334" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Stage 1: IPA</text><path d="M445.6666666666667 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="458.6666666666667" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="563.3333333333334" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Stage 2: PA</text></svg></div>

**How it works**

1. Guest EL0/EL1 addresses undergo stage-1 translation to IPA.
2. Stage-2 translation maps IPA to host physical addresses and enforces VM isolation.
3. Configured operations trap to EL2; the hypervisor handles them and resumes the guest.

**Example:** An emulated device access may generate a stage-2 fault that KVM/QEMU handles.

**Interview takeaway:** Not every guest instruction traps; hardware virtualization runs compatible guest instructions directly.

### What is the ARM64 calling convention? {M}
**Short answer:** AAPCS64 defines how compiled functions pass arguments, return values and preserve registers.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 92" width="100%" role="img" aria-label="Caller: X0/X1 then Function: ADD then Return: X0" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="12" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="116.66666666666667" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Caller: X0/X1</text><path d="M222.33333333333334 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="235.33333333333334" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Function: ADD</text><path d="M445.6666666666667 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="458.6666666666667" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="563.3333333333334" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Return: X0</text></svg></div>

**How it works**

1. X0–X7 carry integer/pointer arguments and common return values.
2. X19–X29 and SP are callee-preserved; X30 holds the return address and X18 is platform-specific.
3. SP must satisfy 16-byte alignment at public interfaces; SIMD/FP registers have their own rules.

**Example:** add(a,b) can receive a in X0, b in X1 and return the sum in X0.

```asm
add:
    ADD X0, X0, X1
    RET
```

**Interview takeaway:** Aggregates, floating point and indirect results have additional ABI rules.

### What is a stack frame in ARM64? {M}
**Short answer:** A stack frame is temporary stack storage used by a function for saved registers, local objects and other call-related data.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 240" width="100%" role="img" aria-label="Higher address: caller, Saved X29 / X30, Locals / spills, SP: lower address" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="130" y="8" width="420" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="36" font-size="12" font-weight="600" fill="#0c4a6e">Higher address: caller</text><rect x="130" y="64" width="420" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="92" font-size="12" font-weight="600" fill="#0c4a6e">Saved X29 / X30</text><rect x="130" y="120" width="420" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="148" font-size="12" font-weight="600" fill="#0c4a6e">Locals / spills</text><rect x="130" y="176" width="420" height="48" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="204" font-size="12" font-weight="600" fill="#0c4a6e">SP: lower address</text></svg></div>

**How it works**

1. A function may decrement SP to reserve aligned space.
2. It may save frame pointer X29 and LR X30 and establish a frame record.
3. On return it restores registers and SP before RET.

**Example:** A function that calls another function can save LR so the nested BL cannot destroy its return address.

```asm
STP X29, X30, [SP, #-16]!
MOV X29, SP
BL helper
LDP X29, X30, [SP], #16
RET
```

**Interview takeaway:** Optimized leaf functions may omit a frame; layout is compiler/ABI dependent.

### What is WFI versus WFE? {M}
**Short answer:** WFI is a wait-for-interrupt hint; WFE waits for an event or another allowed wake condition. SEV sends an event.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 92" width="100%" role="img" aria-label="WFI: interrupt, WFE: event / wake condition" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="12" y="12" width="321" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="172.5" y="49" font-size="12" font-weight="600" fill="#0c4a6e">WFI: interrupt</text><rect x="347" y="12" width="321" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="507.5" y="49" font-size="12" font-weight="600" fill="#0c4a6e">WFE: event / wake condition</text></svg></div>

**How it works**

1. WFI is commonly used in idle paths.
2. WFE may consume an already recorded event and return immediately.
3. A waiting loop must recheck its condition after waking.

**Example:** A CPU can use WFE while waiting for a lock-related event; ordering and the lock protocol are separate.

```asm
WFI
// separate event-based wait example:
WFE
SEV
```

**Interview takeaway:** Neither instruction guarantees a sleep duration or supplies memory synchronization on its own.

### What is the difference between a cache clean and invalidate? {M}
**Short answer:** Cleaning writes dirty cache data toward the specified point; invalidating discards a cached copy.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 92" width="100%" role="img" aria-label="Clean: cache → memory, Invalidate: discard cached copy" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="12" y="12" width="321" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="172.5" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Clean: cache → memory</text><rect x="347" y="12" width="321" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="507.5" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Invalidate: discard cached copy</text></svg></div>

**How it works**

1. Clean when another non-coherent observer must see CPU-written data.
2. Invalidate stale lines after a device writes memory, after proper ownership transfer.
3. For receive buffers prepare full cache lines before DMA as required by the platform.

**Example:** TX DMA may read old RAM until cache cleaning; RX CPU reads may hit old cache contents unless synchronized.

**Interview takeaway:** Invalidating dirty lines can lose data; use the OS DMA API and honor cache-line boundaries.

### What is endianness in ARM? {E}
**Short answer:** Endianness defines byte order for multi-byte objects in memory, not the order of bits inside a register.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 92" width="100%" role="img" aria-label="Little: 78 56 34 12, Big: 12 34 56 78" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="12" y="12" width="321" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="172.5" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Little: 78 56 34 12</text><rect x="347" y="12" width="321" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="507.5" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Big: 12 34 56 78</text></svg></div>

**How it works**

1. Little-endian stores the least significant byte at the lowest address.
2. Big-endian stores the most significant byte at the lowest address.
3. AArch64 Linux commonly uses little-endian; hardware and device formats may differ.

**Example:** 0x12345678 is stored as 78 56 34 12 in little-endian and 12 34 56 78 in big-endian.

```asm
REV W0, W0 // reverse bytes of 32-bit value
```

**Interview takeaway:** Network and peripheral formats may require explicit conversion; do not infer byte order from a pointer cast.

### What are NZCV condition flags? {E}
**Short answer:** NZCV are the integer condition flags: Negative, Zero, Carry and Overflow.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 92" width="100%" role="img" aria-label="N: negative, Z: zero, C: carry, V: overflow" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="12" y="12" width="153.5" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="88.75" y="49" font-size="12" font-weight="600" fill="#0c4a6e">N: negative</text><rect x="179.5" y="12" width="153.5" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="256.25" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Z: zero</text><rect x="347" y="12" width="153.5" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="423.75" y="49" font-size="12" font-weight="600" fill="#0c4a6e">C: carry</text><rect x="514.5" y="12" width="153.5" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="591.25" y="49" font-size="12" font-weight="600" fill="#0c4a6e">V: overflow</text></svg></div>

**How it works**

1. N records the result sign bit; Z indicates zero.
2. C describes carry for addition or no borrow for subtraction.
3. V indicates signed overflow; conditional branches and selects test these flags.

**Example:** CMP X0,#0 sets flags as if subtracting zero; B.EQ branches if Z is set.

```asm
CMP X0, #0
B.EQ zero_case
```

**Interview takeaway:** C and V differ: carry is unsigned, overflow is signed.

### What is the ARM64 boot flow? {M}
**Short answer:** ARM64 boot initializes a platform and transfers control to a kernel using the boot protocol; exact firmware stages vary.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 92" width="100%" role="img" aria-label="ROM / firmware then Bootloader then Linux kernel then PID 1" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="12" y="12" width="153.5" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="88.75" y="49" font-size="12" font-weight="600" fill="#0c4a6e">ROM / firmware</text><path d="M166.5 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="179.5" y="12" width="153.5" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="256.25" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Bootloader</text><path d="M334 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="347" y="12" width="153.5" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="423.75" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Linux kernel</text><path d="M501.5 45h12m-5-4 5 4-5 4" fill="none" stroke="#475569" stroke-width="1.5"/><rect x="514.5" y="12" width="153.5" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="591.25" y="49" font-size="12" font-weight="600" fill="#0c4a6e">PID 1</text></svg></div>

**How it works**

1. Reset enters platform firmware or Boot ROM; early code loads trusted firmware and initializes clocks/DRAM as needed.
2. A bootloader loads the kernel, DTB and optional initramfs; it establishes the required CPU state.
3. The kernel entry code establishes its own translation state, initializes subsystems and starts PID 1.

**Example:** On a typical embedded system: ROM → platform firmware/SPL → U-Boot → Linux → init.

**Interview takeaway:** For Linux arm64 the boot protocol specifies MMU off at entry, x0 as DTB address for DT boot, and required cache/interrupt state; UEFI paths differ.

### What are TTBR0_EL1, TTBR1_EL1, TCR_EL1 and MAIR_EL1? {H}
**Short answer:** These system registers configure stage-1 translation at EL1/EL0.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 92" width="100%" role="img" aria-label="TTBR: table roots, TCR: translation rules, MAIR: memory type" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="12" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="116.66666666666667" y="49" font-size="12" font-weight="600" fill="#0c4a6e">TTBR: table roots</text><rect x="235.33333333333334" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="49" font-size="12" font-weight="600" fill="#0c4a6e">TCR: translation rules</text><rect x="458.6666666666667" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="563.3333333333334" y="49" font-size="12" font-weight="600" fill="#0c4a6e">MAIR: memory type</text></svg></div>

**How it works**

1. TTBR0_EL1 and TTBR1_EL1 specify translation-table roots and associated ASID fields, subject to configuration.
2. TCR_EL1 controls address sizes, granules and walk attributes.
3. MAIR_EL1 defines memory attributes selected by page-descriptor AttrIndx; SCTLR_EL1 controls translation/cache enablement.

**Example:** Linux typically separates user and kernel VA ranges using TTBR0 and TTBR1.

```asm
MRS X0, TTBR0_EL1
MRS X1, TCR_EL1
MRS X2, MAIR_EL1
```

**Interview takeaway:** Changing translation configuration requires architecture-defined barriers and TLB maintenance.

### What are ASIDs, VMIDs and TLB shootdowns? {H}
**Short answer:** ASIDs distinguish address spaces, VMIDs distinguish VM translation contexts, and shootdowns invalidate stale translations on affected CPUs.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 92" width="100%" role="img" aria-label="ASID A: VA → PA A, ASID B: VA → PA B" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="12" y="12" width="321" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="172.5" y="49" font-size="12" font-weight="600" fill="#0c4a6e">ASID A: VA → PA A</text><rect x="347" y="12" width="321" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="507.5" y="49" font-size="12" font-weight="600" fill="#0c4a6e">ASID B: VA → PA B</text></svg></div>

**How it works**

1. Non-global TLB entries can be tagged with ASIDs so switching processes need not flush everything.
2. VMIDs distinguish stage-2 translation contexts.
3. After changing mappings or recycling tags, software performs appropriate invalidation and synchronization.

**Example:** Process A and B can both map VA 0x4000 to different physical pages without sharing the same cached translation.

**Interview takeaway:** Tags do not eliminate the need to invalidate changed mappings; use kernel TLB APIs.

### What is the ARM SMMU and how does it differ from the CPU MMU? {H}
**Short answer:** The SMMU is Arm's IOMMU architecture. It translates and checks device DMA transactions, independently of CPU virtual address translation.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 92" width="100%" role="img" aria-label="CPU VA → CPU MMU, Device IOVA → SMMU, Physical memory" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="12" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="116.66666666666667" y="49" font-size="12" font-weight="600" fill="#0c4a6e">CPU VA → CPU MMU</text><rect x="235.33333333333334" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Device IOVA → SMMU</text><rect x="458.6666666666667" y="12" width="209.33333333333334" height="66" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="563.3333333333334" y="49" font-size="12" font-weight="600" fill="#0c4a6e">Physical memory</text></svg></div>

**How it works**

1. The driver maps memory with the DMA API.
2. The device issues a DMA address (possibly an IOVA); the SMMU translates it to physical memory.
3. Permissions isolate devices and mappings are removed when no longer required.

**Example:** A display engine can scan out a framebuffer using a device-visible address that differs from the CPU virtual address.

**Interview takeaway:** An SMMU does not itself guarantee cache coherency; mappings may alternatively use direct addresses or bounce buffers.

