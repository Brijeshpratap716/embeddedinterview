---
slug: embedded-c
title: Embedded C
icon: ⚙️
level: Intermediate
order: 3
desc: volatile, ISRs, registers, critical sections, start-up code, linker scripts, AAPCS, intrinsics, bootloaders and writing firmware that survives real hardware.
---
Concise firmware interview notes with diagrams, step-by-step explanations and practical examples. Code fragments require the relevant platform headers and target-specific definitions.

### What is volatile and when must you use it? {E}
**Short answer:** Volatile marks accesses that have observable significance beyond ordinary program data flow.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="CPU read|Hardware register" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="324" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="172" y="47" fill="#0c4a6e" font-size="12">CPU read</text><rect x="346" y="8" width="324" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="508" y="47" fill="#0c4a6e" font-size="12">Hardware register</text></svg></div>

**How it works**

1. Use the target's register definitions for MMIO.
2. Read or write at the prescribed width.
3. Use volatile for platform-supported simple ISR flags where appropriate.

**Example**

```c
volatile uint32_t *reg=(volatile uint32_t *)0x40000000u;
// uint32_t status=*reg; // valid target only
```

**Interview takeaway:** Volatile is not a lock, memory barrier or cache maintenance operation.

### Does volatile make a variable thread-safe or atomic? {M}
**Short answer:** No. Volatile does not make a compound operation atomic or establish synchronization between C threads.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="Load count|Add 1|Store count" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="47" fill="#0c4a6e" font-size="12">Load count</text><rect x="234" y="8" width="212" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="47" fill="#0c4a6e" font-size="12">Add 1</text><rect x="458" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="47" fill="#0c4a6e" font-size="12">Store count</text></svg></div>

**How it works**

1. An increment typically loads, adds and stores.
2. Another context can intervene.
3. Use atomic operations or protect the critical section.

**Example**

```c
#include <stdatomic.h>
static atomic_uint count;
void increment(void){atomic_fetch_add(&count,1); }
```

**Interview takeaway:** For ISRs, confirm atomics are lock-free and supported by the platform, or use interrupt-safe primitives.

### Can a pointer be volatile? Explain the declarations. {M}
**Short answer:** The qualifier can apply to the pointed-to object, the pointer variable, or both.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="p: volatile data|q: volatile pointer|r: both" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="47" fill="#0c4a6e" font-size="12">p: volatile data</text><rect x="234" y="8" width="212" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="47" fill="#0c4a6e" font-size="12">q: volatile pointer</text><rect x="458" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="47" fill="#0c4a6e" font-size="12">r: both</text></svg></div>

**How it works**

1. Read qualifiers on each side of *.
2. A volatile pointee requires observable accesses to data.
3. A volatile pointer requires observable accesses to the pointer itself.

**Example**

```c
volatile int *p;
int *volatile q;
volatile int *volatile r;
```

**Interview takeaway:** Pointer volatility does not synchronize access to a buffer shared with another core.

### What is an ISR and what are the rules for writing one? {E}
**Short answer:** An interrupt service routine handles an asynchronous hardware event or interrupt request.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="Peripheral IRQ|ISR|Deferred worker" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="47" fill="#0c4a6e" font-size="12">Peripheral IRQ</text><rect x="234" y="8" width="212" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="47" fill="#0c4a6e" font-size="12">ISR</text><rect x="458" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="47" fill="#0c4a6e" font-size="12">Deferred worker</text></svg></div>

**How it works**

1. The CPU enters an interrupt handler.
2. Acknowledge and service the source.
3. Capture minimal data.
4. Defer expensive processing to a task.

**Example**

```c
void UART_IRQHandler(void){
    // Read status/data per hardware manual.
    // Queue received byte; notify worker using ISR-safe API.
}
```

**Interview takeaway:** Avoid blocking, long loops and ordinary mutex acquisition in an ISR.

### Can you pass parameters to or return a value from an ISR? {E}
**Short answer:** A hardware interrupt enters using the architecture's exception convention, not an ordinary caller-supplied C argument list.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="Vector entry|Handler|Event / shared state" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="47" fill="#0c4a6e" font-size="12">Vector entry</text><rect x="234" y="8" width="212" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="47" fill="#0c4a6e" font-size="12">Handler</text><rect x="458" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="47" fill="#0c4a6e" font-size="12">Event / shared state</text></svg></div>

**How it works**

1. The vector selects an entry routine.
2. The handler reads peripheral state or uses registered context.
3. Results are communicated via memory or events.

**Example**

```c
void Timer_IRQHandler(void){
    // Clear timer interrupt and signal an event.
}
```

**Interview takeaway:** OS interrupt callbacks can accept arguments or return status because software wrappers define that interface.

### What is interrupt latency and how do you reduce it? {M}
**Short answer:** Interrupt latency is the time from interrupt assertion to the chosen handler entry milestone.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="IRQ asserted|Mask / priority delay|Handler entry" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="47" fill="#0c4a6e" font-size="12">IRQ asserted</text><rect x="234" y="8" width="212" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="47" fill="#0c4a6e" font-size="12">Mask / priority delay</text><rect x="458" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="47" fill="#0c4a6e" font-size="12">Handler entry</text></svg></div>

**How it works**

1. Account for masking, higher-priority work, hardware delivery and exception entry.
2. Minimize critical sections.
3. Measure with trace or GPIO timestamps.

**Example**

Example: if a higher-priority handler holds the CPU for 20 µs, a lower-priority request may wait at least that long.

**Interview takeaway:** Specify the measurement points and worst-case load; handler execution time is a separate metric.

### What is a critical section and how do you implement one on bare metal? {M}
**Short answer:** A critical section protects an operation that must not be interrupted by competing access.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="Save mask|Protected update|Restore mask" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="47" fill="#0c4a6e" font-size="12">Save mask</text><rect x="234" y="8" width="212" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="47" fill="#0c4a6e" font-size="12">Protected update</text><rect x="458" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="47" fill="#0c4a6e" font-size="12">Restore mask</text></svg></div>

**How it works**

1. On a single-core Cortex-M, save the interrupt mask.
2. Disable relevant interrupts.
3. Execute a short update.
4. Restore the saved mask.

**Example**

```c
uint32_t saved=__get_PRIMASK();
__disable_irq();
// update shared state
__set_PRIMASK(saved);
```

**Interview takeaway:** PRIMASK does not mask NMI or HardFault and cannot protect against another CPU or DMA.

### What is a reentrant function? {M}
**Short answer:** A reentrant function can be interrupted and invoked again before an earlier invocation completes without corrupting its state.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="Invocation A: locals|Invocation B: locals" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="324" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="172" y="47" fill="#0c4a6e" font-size="12">Invocation A: locals</text><rect x="346" y="8" width="324" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="508" y="47" fill="#0c4a6e" font-size="12">Invocation B: locals</text></svg></div>

**How it works**

1. Keep mutable state per invocation or explicitly owned by the caller.
2. Avoid unsynchronized shared state.
3. Ensure called routines have the same property.

**Example**

```c
int add(int a,int b){return a+b;} // inputs must not overflow
```

**Interview takeaway:** A mutable static scratch buffer is a common reason a function is not reentrant.

### What is the difference between reentrant and thread-safe? {H}
**Short answer:** Thread safety protects concurrent thread calls; reentrancy also permits overlapping invocation in an interrupt or nested-call situation under the relevant execution model.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="Thread-safe: mutex|Reentrant: independent state" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="324" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="172" y="47" fill="#0c4a6e" font-size="12">Thread-safe: mutex</text><rect x="346" y="8" width="324" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="508" y="47" fill="#0c4a6e" font-size="12">Reentrant: independent state</text></svg></div>

**How it works**

1. A mutex can serialize threads.
2. A nested invocation may deadlock on that mutex.
3. Per-call storage avoids that dependency.

**Example**

Example: a mutex-protected logger is thread-safe but is normally not safe to call from an ISR.

**Interview takeaway:** Neither property follows automatically from the other in every execution context.

### How do you set, clear, toggle and test a bit in a register? {E}
**Short answer:** Use unsigned masks to manipulate selected bits without changing unrelated bits in an ordinary value.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="Original bits|Mask bit 5|Selected update" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="47" fill="#0c4a6e" font-size="12">Original bits</text><rect x="234" y="8" width="212" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="47" fill="#0c4a6e" font-size="12">Mask bit 5</text><rect x="458" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="47" fill="#0c4a6e" font-size="12">Selected update</text></svg></div>

**How it works**

1. Build a mask with 1u shifted by a valid bit index; OR sets, AND with complement clears, XOR toggles and AND tests.

**Example**

```c
uint32_t m=UINT32_C(1)<<5;
x |= m;
x &= ~m;
x ^= m;
bool set=(x&m)!=0;
```

**Interview takeaway:** Hardware register semantics may prohibit read-modify-write; check W1C and atomic set/clear registers.

### Why can a read-modify-write on a register be dangerous? {H}
**Short answer:** Read-modify-write can lose concurrent updates or accidentally trigger side effects on peripheral registers.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="Read old value|Concurrent update|Stale writeback" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="47" fill="#0c4a6e" font-size="12">Read old value</text><rect x="234" y="8" width="212" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="47" fill="#0c4a6e" font-size="12">Concurrent update</text><rect x="458" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="47" fill="#0c4a6e" font-size="12">Stale writeback</text></svg></div>

**How it works**

1. Read the old value.
2. Modify selected bits.
3. Write back.
4. Another writer or hardware may change other bits during the sequence.

**Example**

```c
// On a write-one-to-clear status register:
STATUS = ERROR_MASK; // not STATUS |= ERROR_MASK
```

**Interview takeaway:** Use device-specific set/clear registers, proper locking, or prescribed access patterns.

### What is bit-banding on Cortex-M? {H}
**Short answer:** Bit-banding maps individual bits in supported address regions onto word addresses in an alias region.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="Original byte / bit|Alias address|Single-bit access" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="47" fill="#0c4a6e" font-size="12">Original byte / bit</text><rect x="234" y="8" width="212" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="47" fill="#0c4a6e" font-size="12">Alias address</text><rect x="458" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="47" fill="#0c4a6e" font-size="12">Single-bit access</text></svg></div>

**How it works**

1. Calculate the byte offset from the region base.
2. Multiply by 32 and add bit index times 4.
3. Write 0 or 1 to the alias word.

**Example**

```c
// Supported classic SRAM bit-band region, byte offset 4, bit 3:
uintptr_t alias=0x22000000u+4u*32u+3u*4u;
```

**Interview takeaway:** Bit-banding is optional and absent on many Cortex-M implementations; consult the SoC manual.

### What happens before main() runs on a microcontroller? {M}
**Short answer:** Startup code establishes the C runtime environment before calling main.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="Reset handler|Initialize RAM|Runtime init|main" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="156" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="88" y="47" fill="#0c4a6e" font-size="12">Reset handler</text><rect x="178" y="8" width="156" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="256" y="47" fill="#0c4a6e" font-size="12">Initialize RAM</text><rect x="346" y="8" width="156" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="424" y="47" fill="#0c4a6e" font-size="12">Runtime init</text><rect x="514" y="8" width="156" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="592" y="47" fill="#0c4a6e" font-size="12">main</text></svg></div>

**How it works**

1. Reset selects the initial stack and reset handler.
2. Startup initializes clocks as required.
3. Copy .data and clear .bss.
4. Initialize runtime/library state and call main.

**Example**

Example: static int x=7 is copied from its load image; static int y is cleared before main.

**Interview takeaway:** Exact initialization order is platform and toolchain dependent.

### What is a linker script and what does it contain? {M}
**Short answer:** A linker script describes how input sections become output sections and where they reside in memory.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="Object sections|Linker script|Flash / RAM layout" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="47" fill="#0c4a6e" font-size="12">Object sections</text><rect x="234" y="8" width="212" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="47" fill="#0c4a6e" font-size="12">Linker script</text><rect x="458" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="47" fill="#0c4a6e" font-size="12">Flash / RAM layout</text></svg></div>

**How it works**

1. Define flash and RAM regions.
2. Place .text, .data and .bss.
3. Expose symbols used by startup code.
4. Check the map file for fit.

**Example**

```ld
SECTIONS {
 .text : { *(.text*) } > FLASH
 .data : { *(.data*) } > RAM AT> FLASH
 .bss (NOLOAD) : { *(.bss*) *(COMMON) } > RAM
}
```

**Interview takeaway:** The MEMORY definitions and startup copy/zero symbols must match the board; fragment is illustrative.

### What is the vector table? {E}
**Short answer:** The vector table supplies exception and interrupt entry information.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="Initial MSP|Reset vector|Exception / IRQ vectors" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="47" fill="#0c4a6e" font-size="12">Initial MSP</text><rect x="234" y="8" width="212" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="47" fill="#0c4a6e" font-size="12">Reset vector</text><rect x="458" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="47" fill="#0c4a6e" font-size="12">Exception / IRQ vectors</text></svg></div>

**How it works**

1. On Cortex-M the first word supplies the initial MSP.
2. The second points to Reset_Handler.
3. Subsequent entries identify exception and IRQ handlers.

**Example**

Example: an IRQ number selects its corresponding entry after the core exception vectors.

**Interview takeaway:** VTOR availability and alignment vary; AArch64 uses exception vector code rather than this pointer-table format.

### What are weak symbols? {M}
**Short answer:** A weak symbol provides a definition that a suitable strong definition can override during linking.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="Weak default|Strong override|Selected symbol" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="47" fill="#0c4a6e" font-size="12">Weak default</text><rect x="234" y="8" width="212" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="47" fill="#0c4a6e" font-size="12">Strong override</text><rect x="458" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="47" fill="#0c4a6e" font-size="12">Selected symbol</text></svg></div>

**How it works**

1. Supply a default weak handler.
2. Implement a strong handler with the same symbol name.
3. The linker chooses the strong definition.

**Example**

```c
__attribute__((weak)) void board_init(void) {}
// In another source file, define a strong board_init().
```

**Interview takeaway:** Weak attributes and resolution rules are toolchain-specific.

### How do you place a variable or function at a specific address or section? {M}
**Short answer:** Use compiler section attributes and a linker script to control placement.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="C object|Named section|Linker region" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="47" fill="#0c4a6e" font-size="12">C object</text><rect x="234" y="8" width="212" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="47" fill="#0c4a6e" font-size="12">Named section</text><rect x="458" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="47" fill="#0c4a6e" font-size="12">Linker region</text></svg></div>

**How it works**

1. Assign an object to a named input section.
2. Map that section to the required output region.
3. Inspect the ELF and map file.

**Example**

```c
__attribute__((section(".dma_buffer"),aligned(64)))
static unsigned char buf[256];
```

**Interview takeaway:** Alignment and placement alone do not establish DMA accessibility or cache coherency.

### What is a watchdog timer and how should you use it? {E}
**Short answer:** A watchdog resets or otherwise supervises a system if software fails to service it within a configured window.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="Task health|Supervisor|Watchdog feed / reset" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="47" fill="#0c4a6e" font-size="12">Task health</text><rect x="234" y="8" width="212" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="47" fill="#0c4a6e" font-size="12">Supervisor</text><rect x="458" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="47" fill="#0c4a6e" font-size="12">Watchdog feed / reset</text></svg></div>

**How it works**

1. Configure the watchdog timeout.
2. Confirm critical tasks have made progress.
3. Service it only after health checks pass.
4. Record reset causes at boot.

**Example**

Example: supervisor feeds the watchdog only after receiving fresh heartbeat counters from communication and control tasks.

**Interview takeaway:** Feeding unconditionally in an ISR can hide a hung application.

### What is debouncing and how do you implement it? {E}
**Short answer:** Debouncing filters repeated transitions caused by mechanical switch contacts.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="Raw bouncing input|Stability filter|Clean button event" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="47" fill="#0c4a6e" font-size="12">Raw bouncing input</text><rect x="234" y="8" width="212" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="47" fill="#0c4a6e" font-size="12">Stability filter</text><rect x="458" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="47" fill="#0c4a6e" font-size="12">Clean button event</text></svg></div>

**How it works**

1. Sample periodically.
2. Track when a candidate state first appears.
3. Accept it only after it stays stable for the chosen interval.

**Example**

Example: at 1 ms sampling, accept a new button state after 20 consecutive matching samples.

**Interview takeaway:** Use a nonblocking timer and tune the interval to actual switch behavior.

### How do you scan a matrix keypad? {M}
**Short answer:** A matrix keypad reduces GPIO count by connecting keys between rows and columns.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="Row drive|Pressed key|Column sample" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="47" fill="#0c4a6e" font-size="12">Row drive</text><rect x="234" y="8" width="212" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="47" fill="#0c4a6e" font-size="12">Pressed key</text><rect x="458" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="47" fill="#0c4a6e" font-size="12">Column sample</text></svg></div>

**How it works**

1. Drive one row at a time while other rows are safely inactive.
2. Read pulled-up columns.
3. Identify row/column intersections and debounce.

**Example**

Example: active row 2 and low column 1 identify key (2,1) in an active-low scan.

**Interview takeaway:** Multiple simultaneous presses can cause ghosting; use diodes or limit supported combinations.

### What is polling versus interrupts versus DMA? {E}
**Short answer:** Polling repeatedly checks device state, interrupts notify the CPU, and DMA transfers data with limited CPU intervention.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="Polling: CPU checks|IRQ: device notifies|DMA: block transfer" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="47" fill="#0c4a6e" font-size="12">Polling: CPU checks</text><rect x="234" y="8" width="212" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="47" fill="#0c4a6e" font-size="12">IRQ: device notifies</text><rect x="458" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="47" fill="#0c4a6e" font-size="12">DMA: block transfer</text></svg></div>

**How it works**

1. Polling is simple for short predictable waits.
2. Interrupt handlers react to events; DMA moves blocks after setup and signals completion.

**Example**

Example: UART polling sends a boot message; RX interrupt handles occasional bytes; DMA handles a large continuous stream.

**Interview takeaway:** DMA still needs setup, ownership management and completion processing.

### What are the cache coherency problems with DMA? {H}
**Short answer:** Non-coherent DMA can access RAM while CPU caches contain newer or older copies of the same data.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="CPU cache|RAM buffer|DMA device" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="47" fill="#0c4a6e" font-size="12">CPU cache</text><rect x="234" y="8" width="212" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="47" fill="#0c4a6e" font-size="12">RAM buffer</text><rect x="458" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="47" fill="#0c4a6e" font-size="12">DMA device</text></svg></div>

**How it works**

1. Prepare TX by cleaning dirty lines as required.
2. Prepare dedicated RX cache lines before device ownership.
3. Invalidate/synchronize after completion before CPU access.

**Example**

Example: Linux uses dma_map_single and dma_unmap_single for a streaming TX buffer, with DMA_TO_DEVICE direction.

**Interview takeaway:** Use platform cache/DMA APIs, align whole cache lines where required and avoid concurrent CPU access during device ownership.

### What is a memory barrier and why would firmware need one? {H}
**Short answer:** Memory barriers constrain ordering or completion of operations so other observers and later instructions see the required behavior.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="Earlier operations|Barrier|Later operations" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="47" fill="#0c4a6e" font-size="12">Earlier operations</text><rect x="234" y="8" width="212" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="47" fill="#0c4a6e" font-size="12">Barrier</text><rect x="458" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="47" fill="#0c4a6e" font-size="12">Later operations</text></svg></div>

**How it works**

1. DMB orders relevant accesses; DSB waits for required completion; ISB synchronizes subsequent instruction execution with context changes.

**Example**

```c
// Cortex-M MPU reconfiguration pattern (follow platform sequence):
__DSB();
// update MPU configuration
__DSB();
__ISB();
```

**Interview takeaway:** Barrier scope matters; volatile is not a barrier and barriers do not automatically clean caches.

### What is the Arm calling convention (AAPCS), and why does it matter in embedded work? {M}
**Short answer:** AAPCS defines function-call rules, argument passing, return values and register preservation for Arm targets.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="Caller arguments|Function|Return registers" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="47" fill="#0c4a6e" font-size="12">Caller arguments</text><rect x="234" y="8" width="212" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="47" fill="#0c4a6e" font-size="12">Function</text><rect x="458" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="47" fill="#0c4a6e" font-size="12">Return registers</text></svg></div>

**How it works**

1. AAPCS32 commonly passes initial integer arguments in R0–R3; AAPCS64 uses X0–X7.
2. Callees preserve designated registers and maintain required stack alignment.

**Example**

Example: a two-integer AArch64 add function receives X0 and X1 and returns the result in X0.

**Interview takeaway:** Floating-point, aggregate and platform-specific conventions have additional rules.

### What are compiler intrinsics, and when should you use them instead of inline assembly? {M}
**Short answer:** Compiler intrinsics expose architecture-specific operations through compiler-recognized functions.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="C intrinsic|Compiler|Machine instruction" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="47" fill="#0c4a6e" font-size="12">C intrinsic</text><rect x="234" y="8" width="212" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="47" fill="#0c4a6e" font-size="12">Compiler</text><rect x="458" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="47" fill="#0c4a6e" font-size="12">Machine instruction</text></svg></div>

**How it works**

1. Use an intrinsic when available.
2. Let the compiler understand operand constraints and scheduling.
3. Use inline assembly only when necessary.

**Example**

```c
// CMSIS example:
__DMB();
__WFI();
```

**Interview takeaway:** Check intrinsic availability, semantics and target feature support.

### How do you implement a delay without blocking the CPU? {M}
**Short answer:** A nonblocking delay schedules work for a future time instead of spinning until it expires.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="Start time|Other work|Deadline event" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="47" fill="#0c4a6e" font-size="12">Start time</text><rect x="234" y="8" width="212" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="47" fill="#0c4a6e" font-size="12">Other work</text><rect x="458" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="47" fill="#0c4a6e" font-size="12">Deadline event</text></svg></div>

**How it works**

1. Record the start tick.
2. Periodically compare unsigned elapsed time to the duration.
3. Run other work until the deadline.

**Example**

```c
uint32_t start=now_ms();
// In a periodic loop:
if ((uint32_t)(now_ms()-start)>=100u) {
    // Perform scheduled work once.
}
```

**Interview takeaway:** Unsigned subtraction handles counter wrap within the supported interval; prevent repeated firing.

### What is a super loop (foreground/background) architecture? {E}
**Short answer:** A super loop is a foreground loop that cooperatively services tasks, often with interrupts handling asynchronous events.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="Initialize|Service tasks repeatedly|Interrupt events" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="47" fill="#0c4a6e" font-size="12">Initialize</text><rect x="234" y="8" width="212" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="47" fill="#0c4a6e" font-size="12">Service tasks repeatedly</text><rect x="458" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="47" fill="#0c4a6e" font-size="12">Interrupt events</text></svg></div>

**How it works**

1. Initialize hardware.
2. Iterate through short nonblocking service routines.
3. Let IRQ handlers capture events and wake the loop when applicable.

**Example**

```c
for (;;) {
    poll_buttons();
    service_uart();
    update_control();
}
```

**Interview takeaway:** One long blocking task delays every other foreground service.

### How do you write a state machine in C? {M}
**Short answer:** A finite state machine represents behavior as states, events and transitions.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="IDLE|RUN|FAULT" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="47" fill="#0c4a6e" font-size="12">IDLE</text><rect x="234" y="8" width="212" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="47" fill="#0c4a6e" font-size="12">RUN</text><rect x="458" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="47" fill="#0c4a6e" font-size="12">FAULT</text></svg></div>

**How it works**

1. Define states.
2. Handle each event according to the current state.
3. Perform actions and transition explicitly.
4. Handle errors.

**Example**

```c
enum state {IDLE,RUN,FAULT};
// Example transition: IDLE + START -> RUN
// RUN + ERROR -> FAULT
```

**Interview takeaway:** Define recovery and unexpected-event handling rather than relying on implicit state.

### How do you design error handling in firmware? {M}
**Short answer:** Firmware error handling detects failures, preserves safe behavior and makes root causes diagnosable.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="Detect|Diagnose|Recover / safe state" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="47" fill="#0c4a6e" font-size="12">Detect</text><rect x="234" y="8" width="212" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="47" fill="#0c4a6e" font-size="12">Diagnose</text><rect x="458" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="47" fill="#0c4a6e" font-size="12">Recover / safe state</text></svg></div>

**How it works**

1. Validate inputs and return values.
2. Use bounded retries/timeouts.
3. Record useful diagnostics.
4. Recover or enter a safe state according to requirements.

**Example**

Example: after repeated I2C timeouts, mark the sensor unavailable and notify the supervisor instead of blocking forever.

**Interview takeaway:** Safety-critical recovery policies depend on system hazards and requirements.

### What does the inline assembly __asm volatile("" ::: "memory") do? {H}
**Short answer:** An empty GNU inline assembly statement with a memory clobber acts as a compiler memory barrier.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="Compiler before|Memory clobber|Compiler after" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="47" fill="#0c4a6e" font-size="12">Compiler before</text><rect x="234" y="8" width="212" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="47" fill="#0c4a6e" font-size="12">Memory clobber</text><rect x="458" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="47" fill="#0c4a6e" font-size="12">Compiler after</text></svg></div>

**How it works**

1. The compiler must account for possible memory changes at that point.
2. It cannot freely move affected memory accesses across it.
3. No CPU barrier instruction is implied.

**Example**

```c
__asm__ __volatile__("" ::: "memory");
```

**Interview takeaway:** This does not enforce inter-core ordering, device completion or cache maintenance.

### How do you make a firmware image position independent or relocatable? {H}
**Short answer:** Relocatable firmware can execute at a different address using position-independent references or runtime relocation.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="Linked image|Relocation / PIC|New execution address" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="47" fill="#0c4a6e" font-size="12">Linked image</text><rect x="234" y="8" width="212" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="47" fill="#0c4a6e" font-size="12">Relocation / PIC</text><rect x="458" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="47" fill="#0c4a6e" font-size="12">New execution address</text></svg></div>

**How it works**

1. Generate suitable position-independent code.
2. Resolve or relocate address-dependent data.
3. Arrange linker/startup support for the target.

**Example**

Example: PC-relative branches can remain valid when the entire image moves together; absolute pointers may need relocation.

**Interview takeaway:** Interrupt vectors, MMIO addresses, GOT and absolute references need separate consideration.

### How does a bootloader jump to the application on Cortex-M? {H}
**Short answer:** A Cortex-M bootloader transfers control by adopting the application's vector table and initial stack, then branching to its reset handler.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="Bootloader|Validate application vectors|Application reset handler" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="47" fill="#0c4a6e" font-size="12">Bootloader</text><rect x="234" y="8" width="212" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="47" fill="#0c4a6e" font-size="12">Validate application vectors</text><rect x="458" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="47" fill="#0c4a6e" font-size="12">Application reset handler</text></svg></div>

**How it works**

1. Validate image and vectors.
2. Quiesce interrupts and peripherals as required.
3. Configure the vector base where supported.
4. Perform a carefully implemented final stack switch and branch.

**Example**

```c
// Conceptual: vector[0] = application MSP; vector[1] = reset entry.
// Final handoff must avoid compiler-generated stack use after MSP changes.
```

**Interview takeaway:** Check Thumb entry bit, address ranges, privilege state and VTOR support. Use target-specific assembly or a proven handoff routine.

### What is MISRA C? {E}
**Short answer:** MISRA C is a coding guideline framework intended to improve reliability, safety and portability of C programs.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="Coding rules|Analysis / review|Documented compliance" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="47" fill="#0c4a6e" font-size="12">Coding rules</text><rect x="234" y="8" width="212" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="47" fill="#0c4a6e" font-size="12">Analysis / review</text><rect x="458" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="47" fill="#0c4a6e" font-size="12">Documented compliance</text></svg></div>

**How it works**

1. Select the applicable edition and project rules.
2. Use static analysis and reviews.
3. Document justified deviations and verify compliance.

**Example**

Example: explicitly check conversions and array bounds instead of relying on implementation assumptions.

**Interview takeaway:** MISRA compliance alone does not establish functional safety or prove absence of bugs.

### What are a HAL and a BSP, and how do they differ? {M}
**Short answer:** A HAL abstracts hardware operations; a BSP integrates the software needed to run on a particular board.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="Application|HAL / drivers|Board configuration / hardware" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="47" fill="#0c4a6e" font-size="12">Application</text><rect x="234" y="8" width="212" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="47" fill="#0c4a6e" font-size="12">HAL / drivers</text><rect x="458" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="47" fill="#0c4a6e" font-size="12">Board configuration / hardware</text></svg></div>

**How it works**

1. HAL supplies peripheral-level interfaces; BSP selects clocks, pins, memory map, startup and board-specific drivers.
2. Applications use the provided interfaces.

**Example**

Example: a GPIO HAL sets a pin; the BSP identifies which pin drives the board LED.

**Interview takeaway:** Terminology and layering vary across vendors and operating systems.

### What is AUTOSAR and what are its main layers? {M}
**Short answer:** AUTOSAR standardizes automotive software architecture and interfaces; Classic and Adaptive target different environments.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="Application components|RTE|BSW / MCAL" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="47" fill="#0c4a6e" font-size="12">Application components</text><rect x="234" y="8" width="212" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="47" fill="#0c4a6e" font-size="12">RTE</text><rect x="458" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="47" fill="#0c4a6e" font-size="12">BSW / MCAL</text></svg></div>

**How it works**

1. Classic separates application software components, RTE and basic software including MCAL; Adaptive uses service-oriented interfaces on higher-performance platforms.

**Example**

Example: a Classic sensor application communicates through the RTE and basic software rather than directly accessing MCU registers.

**Interview takeaway:** Adaptive AUTOSAR is not simply the Classic layered stack running on a faster CPU.

### What does a typical SoC look like inside? {M}
**Short answer:** An SoC integrates processor cores, memory interfaces, interconnects and peripherals on one chip.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="CPU / cache|Interconnect|DRAM / peripherals / DMA" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="47" fill="#0c4a6e" font-size="12">CPU / cache</text><rect x="234" y="8" width="212" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="47" fill="#0c4a6e" font-size="12">Interconnect</text><rect x="458" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="47" fill="#0c4a6e" font-size="12">DRAM / peripherals / DMA</text></svg></div>

**How it works**

1. CPU cores execute software.
2. The interconnect routes memory and MMIO requests.
3. Controllers manage DRAM, interrupts, DMA and external interfaces.

**Example**

Example: a display engine reads framebuffer data through the interconnect while the CPU handles control registers.

**Interview takeaway:** Address maps, clocks, resets and coherency domains are SoC-specific.

### Which compiler optimisations can change how your C code behaves? {H}
**Short answer:** Optimizers transform code while preserving defined observable behavior under the language and implementation rules.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 88" width="100%" role="img" aria-label="C source|Optimizer|Machine code" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="47" fill="#0c4a6e" font-size="12">C source</text><rect x="234" y="8" width="212" height="70" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="47" fill="#0c4a6e" font-size="12">Optimizer</text><rect x="458" y="8" width="212" height="70" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="47" fill="#0c4a6e" font-size="12">Machine code</text></svg></div>

**How it works**

1. Dead-code elimination removes unused computations.
2. Common-subexpression elimination reuses results.
3. Inlining and reordering improve performance.
4. Undefined behavior invalidates assumptions.

**Example**

Example: a loop polling an ordinary variable modified externally may not reload it as expected; use the appropriate volatile or synchronization interface.

**Interview takeaway:** Do not use -O0 as a correctness fix; inspect generated code and fix invalid assumptions.

