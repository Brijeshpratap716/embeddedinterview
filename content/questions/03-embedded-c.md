---
slug: embedded-c
title: Embedded C
icon: ⚙️
level: Intermediate
order: 3
desc: volatile, ISRs, registers, critical sections, start-up code, linker scripts, AAPCS, intrinsics, bootloaders and writing firmware that survives real hardware.
---
Embedded C is ordinary C plus the rules that come from sharing memory with hardware and interrupts. These are the questions that decide most firmware interviews. Each answer gives the short version you should say first, then the details, code, and the follow-up questions you are likely to get.

### What is volatile and when must you use it? {E}
The `volatile` qualifier tells the compiler that accesses through a volatile-qualified lvalue are observable and must be performed according to the target's volatile semantics. It is particularly important when hardware changes a value independently of the program.

#### 1. Hardware register example

```c
#include <stdint.h>
#define STATUS (*(volatile uint32_t *)0x40000000U)
#define READY  (1U << 0)

while (!(STATUS & READY)) {
    // Wait for the device.
}
```

Assume this is a documented 32-bit status register. Each evaluation reads the register again. Without volatile, an optimizer could reuse an earlier value instead of observing subsequent hardware changes.

#### 2. Interrupt-shared flag

```c
static volatile unsigned int done;

void Timer_IRQHandler(void)
{
    // Acknowledge the timer interrupt first.
    done = 1;
}

void wait_for_timer(void)
{
    while (!done) {
    }
}
```

This simple bare-metal example assumes the target supports indivisible accesses to the flag and the required ISR semantics. Real firmware should use a timeout and an ISR-safe synchronization mechanism for more complex data.

#### 3. What volatile does not do

| Property | Guaranteed? |
|---|---|
| Required volatile accesses | Yes, under implementation rules |
| Atomic increment | No |
| Thread synchronization | No |
| CPU memory ordering | No |
| DMA cache coherency | No |

In Linux drivers use readl/writel for MMIO and appropriate atomics, locks or READ_ONCE/WRITE_ONCE as part of a correct synchronization protocol.

**Interview takeaway:** Volatile controls compiler-visible accesses; it is not a general synchronization primitive.

### Does volatile make a variable thread-safe or atomic? {M}
No. `volatile` does not make an operation atomic, nor does it prevent data races between threads.

#### 1. Why an increment is unsafe

```c
volatile unsigned int count;
void increment(void)
{
    count++;
}
```

A typical increment involves a load, arithmetic and store. Consider two cores starting with count = 0.

| Step | Core A | Core B |
|---|---|---|
| 1 | Read 0 | Read 0 |
| 2 | Calculate 1 | Calculate 1 |
| 3 | Store 1 | Store 1 |

Two increments can lose an update. In C threads, conflicting unsynchronized accesses to a non-atomic object also constitute undefined behaviour; the table illustrates the hardware problem, not a guaranteed C execution.

#### 2. Correct solution using C11 atomics

```c
#include <stdatomic.h>
static atomic_uint count;

void increment(void)
{
    atomic_fetch_add_explicit(&count, 1,
                              memory_order_relaxed);
}
```

The operation atomically updates the counter. Relaxed ordering is sufficient for a standalone statistic, not for publishing related data.

#### 3. Bare-metal alternative

On a single-core Cortex-M, save the interrupt mask, disable relevant interrupts, update the shared object and restore the mask. This does not protect against other cores or DMA. Verify that an atomic implementation is lock-free and suitable for ISR use before calling it from an ISR.

**Interview takeaway:** Use volatile for hardware access; use atomics, locks or interrupt-safe critical sections for shared-state synchronization.

### Can a pointer be volatile? Explain the declarations. {M}
Yes. Volatile can qualify the pointed-to object, the pointer variable itself, or both. Read the declaration around the asterisk.

#### 1. Pointer to volatile data

```c
volatile uint32_t *p = (volatile uint32_t *)0x40000000U;
uint32_t status = *p;
```

The register access is volatile. The pointer itself may be reassigned.

#### 2. Volatile pointer to ordinary data

```c
int a = 10;
int *volatile p = &a;
```

Accesses to the pointer variable p are volatile; accesses to the int through p are not automatically volatile.

#### 3. Both pointer and data volatile

```c
volatile int *volatile p;
```

Both loading the pointer value and accessing its pointed-to int involve volatile-qualified lvalues.

| Declaration | Pointer volatile? | Pointee volatile? |
|---|---|---|
| int *p | No | No |
| volatile int *p | No | Yes |
| int *volatile p | Yes | No |
| volatile int *volatile p | Yes | Yes |

#### 4. Fixed read-only status register

```c
const volatile uint32_t *const status =
    (const volatile uint32_t *)0x40000010U;
```

The address cannot be reassigned, writes through status are forbidden, and reads observe hardware according to the target's MMIO rules.

**Interview takeaway:** Qualifiers before the asterisk apply to the pointed-to type; qualifiers after it apply to that pointer. Neither form provides automatic thread safety.

### What is an ISR and what are the rules for writing one? {E}
An ISR (Interrupt Service Routine) is a handler invoked when the processor accepts an interrupt. It services the hardware event and returns control to the interrupted context or scheduler.

#### 1. Interrupt flow

```text
Peripheral asserts IRQ
        |
Interrupt controller selects priority
        |
CPU saves exception state
        |
ISR acknowledges source / captures data
        |
Deferred task processes data
```

The exact saved registers and acknowledgement protocol depend on the architecture and peripheral.

#### 2. Example: UART receive interrupt

```c
void USART_IRQHandler(void)
{
    if (uart_rx_ready()) {
        unsigned char byte = uart_read_byte();
        rx_queue_put_from_isr(byte);
    }
}
```

These are illustrative platform-specific helpers. Reading data or explicitly clearing status must follow the UART manual. Handle queue-full conditions and acknowledge all relevant sources.

#### 3. Rules for ISR design

- Keep execution bounded; move expensive parsing to a task.
- Never wait for a mutex, sleep, or use a blocking API.
- Use ISR-safe notification/queue functions.
- Synchronize shared state and preserve required interrupt state.
- Clear or acknowledge the interrupt correctly to avoid repeated entry.

For FreeRTOS, a higher-priority task woken by an ISR may require the port-specific yield-from-ISR mechanism.

**Interview takeaway:** An ISR should capture the event and defer substantial work. Its latency and execution time both affect real-time deadlines.

### Can you pass parameters to or return a value from an ISR? {E}
A raw hardware interrupt is not an ordinary C function call. The processor enters an exception handler using the architecture's exception convention, so it does not supply arbitrary C arguments or consume a normal return value.

#### 1. Cortex-M example

```c
void TIM2_IRQHandler(void)
{
    // Check and clear the timer status.
    timer_event = 1;
}
```

The vector table contains the handler entry address. Cortex-M hardware saves a basic exception frame and uses an exception-return sequence; the exact handler declaration follows the toolchain's ABI.

#### 2. How to communicate information

The handler can read device registers, update a suitable shared flag, enqueue a message or notify a task. Use synchronization appropriate to the ISR and consumer.

#### 3. OS interrupt callbacks are different

Linux, for example, invokes registered driver handlers through its IRQ framework:

```c
static irqreturn_t my_irq(int irq, void *dev_id)
{
    struct my_device *dev = dev_id;

    if (!device_irq_pending(dev))
        return IRQ_NONE;

    device_ack_irq(dev);
    return IRQ_HANDLED;
}
```

The kernel supplies irq and dev_id and uses the returned status. This is a software callback called by the IRQ framework, not the raw architectural exception entry.

**Interview takeaway:** Raw ISR signatures follow the architecture/compiler convention; OS frameworks can supply arguments and return status through their own handler API.

### What is interrupt latency and how do you reduce it? {M}
Interrupt latency is the time from interrupt assertion to the point at which the CPU starts servicing the interrupt. Define the exact measurement points when specifying latency.

#### 1. Sources of delay

```text
IRQ asserted
     | Pending / masked / higher-priority handler
     | Interrupt-controller delivery
     | Architectural exception entry
     | Handler prologue
     v
First measured handler instruction
```

A high-priority ISR running for 20 microseconds can delay a lower-priority interrupt by a significant part of that time.

#### 2. How to reduce latency

- Keep interrupt-disabled regions short.
- Assign priorities according to actual deadlines.
- Keep higher-priority handlers bounded.
- Use DMA to reduce frequent CPU interrupts.
- Avoid long flash wait states or memory stalls in critical paths where supported.

Cortex-M features such as tail chaining can reduce exception transition overhead, but do not remove masking or contention delays.

#### 3. How to measure

Toggle a GPIO at the earliest practical ISR point, then compare that signal against the input interrupt edge using a scope or logic analyzer. Alternatively use hardware trace or a cycle counter where supported.

The measurement includes instrumentation and peripheral write delays, so document these. Measure under worst-case load, not just on an idle system.

| Metric | Meaning |
|---|---|
| Interrupt latency | Request to handler entry |
| ISR execution time | Handler entry to completion |
| Response time | Request to application-visible action |

**Interview takeaway:** Optimize worst-case latency and jitter rather than only average interrupt response.

### What is a critical section and how do you implement one on bare metal? {M}
A critical section is a region of code that must be protected from conflicting accesses. On a single-core microcontroller, a short interrupt-masked section can protect state shared with an interrupt handler.

#### 1. Why it is needed

```c
count++;
```

A load/add/store sequence can be interrupted between operations, causing an ISR update to be overwritten.

#### 2. Cortex-M implementation using CMSIS

```c
uint32_t saved = __get_PRIMASK();

__disable_irq();
count++;
__set_PRIMASK(saved);
```

The mask is restored to its original value, so the code also works when entered with interrupts already disabled. Use the appropriate CMSIS implementation and platform ordering requirements.

#### 3. Limitations

PRIMASK masks configurable exceptions, not NMI and HardFault. It affects only the local processor. DMA and other CPUs can continue accessing memory.

For multicore sharing, use a supported atomic operation or lock, often combined with local interrupt masking if the same lock is used from interrupt context. In an RTOS use its designated critical-section APIs and respect nesting rules.

#### 4. Practical rule

Do not call blocking functions, run long loops or perform slow I/O while interrupts are masked. Keep only the actual shared-state update inside the critical section.

**Interview takeaway:** Save and restore interrupt state rather than blindly enabling interrupts. Interrupt masking is not a universal multicore lock or DMA protection.

### What is a reentrant function? {M}
A reentrant function can be invoked again before an earlier invocation completes without corrupting the earlier invocation or shared state.

#### 1. Non-reentrant example

```c
char *format_value(int x)
{
    static char buffer[32];
    snprintf(buffer, sizeof buffer, "%d", x);
    return buffer;
}
```

Two overlapping calls use the same buffer. A nested or concurrent call can overwrite the result of the first call.

#### 2. Reentrant alternative

```c
int format_value(char *buffer, size_t size, int x)
{
    return snprintf(buffer, size, "%d", x);
}
```

Each invocation receives separate caller-owned storage. This avoids the shared buffer problem, provided the supplied buffers do not overlap and the library implementation is safe in the intended execution context.

#### 3. Rules

Use local or caller-owned state, avoid mutable shared scratch storage, avoid returning shared temporary buffers, and ensure functions called internally meet the relevant reentrancy requirements.

Being reentrant does not automatically mean a function is safe to call in a hard ISR; its operations must also be allowed and bounded in that context.

**Interview takeaway:** Reentrancy is about overlapping invocations. Separate per-call state is often the simplest solution.

### What is the difference between reentrant and thread-safe? {H}
A **thread-safe** function behaves correctly when multiple threads call it concurrently. A **reentrant** function can also tolerate an overlapping invocation, such as a nested call, without corrupting the interrupted invocation.

#### 1. Thread-safe but unsuitable for reentry

```c
void increment(void)
{
    mutex_lock(&lock);
    count++;
    mutex_unlock(&lock);
}
```

The mutex serializes threads. However, an interrupt or nested invocation that tries to acquire the same non-recursive mutex can deadlock if the first invocation holds it. A blocking mutex is generally forbidden in an ISR.

#### 2. Reentrant alternative

```c
uint32_t checksum(const uint8_t *buf, size_t n)
{
    uint32_t sum = 0;
    for (size_t i = 0; i < n; i++)
        sum += buf[i];
    return sum;
}
```

Each call owns its accumulator. Concurrent calls can share immutable input safely, provided the buffers remain valid and are not modified concurrently.

| Property | Thread-safe | Reentrant |
|---|---|---|
| Concurrent threads | Correct | Often correct with independent state |
| Nested invocation | Not necessarily safe | Must tolerate supported reentry |
| Blocking lock | May be acceptable | May defeat reentry |
| ISR suitability | Not implied | Still requires ISR-safe operations |

#### 3. Firmware use

Keep interrupt-side algorithms small, bounded and independent of mutable shared scratch buffers. A function may be safe in one execution model but unsafe in another; document the supported contexts.

**Interview takeaway:** Thread safety does not automatically imply reentrancy or interrupt safety. Design around ownership and the actual concurrency model.

### How do you set, clear, toggle and test a bit in a register? {E}
Bit manipulation uses masks to change selected bits without intentionally changing the remaining bits.

#### 1. Basic operations

```c
uint32_t reg = 0;
uint32_t mask = UINT32_C(1) << 3;

reg |= mask;              // Set bit 3
reg &= ~mask;             // Clear bit 3
reg ^= mask;              // Toggle bit 3
bool set = (reg & mask) != 0; // Test bit 3
```

The bit index must be between 0 and 31 for this mask.

<div style="max-width:600px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 120" width="100%" role="img" aria-label="Setting bit 3 in an eight-bit value changes 00100010 to 00101010">
<text x="8" y="24" font-size="11" fill="currentColor">Original</text><rect x="96" y="5" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="109.5" y="23" text-anchor="middle" font-size="13" fill="currentColor">0</text><rect x="125" y="5" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="138.5" y="23" text-anchor="middle" font-size="13" fill="currentColor">0</text><rect x="154" y="5" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="167.5" y="23" text-anchor="middle" font-size="13" fill="currentColor">1</text><rect x="183" y="5" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="196.5" y="23" text-anchor="middle" font-size="13" fill="currentColor">0</text><rect x="212" y="5" width="27" height="27" rx="3" fill="#16a34a" fill-opacity=".15" stroke="#16a34a"/><text x="225.5" y="23" text-anchor="middle" font-size="13" fill="currentColor">0</text><rect x="241" y="5" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="254.5" y="23" text-anchor="middle" font-size="13" fill="currentColor">0</text><rect x="270" y="5" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="283.5" y="23" text-anchor="middle" font-size="13" fill="currentColor">1</text><rect x="299" y="5" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="312.5" y="23" text-anchor="middle" font-size="13" fill="currentColor">0</text><text x="8" y="59" font-size="11" fill="currentColor">Mask</text><rect x="96" y="40" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="109.5" y="58" text-anchor="middle" font-size="13" fill="currentColor">0</text><rect x="125" y="40" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="138.5" y="58" text-anchor="middle" font-size="13" fill="currentColor">0</text><rect x="154" y="40" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="167.5" y="58" text-anchor="middle" font-size="13" fill="currentColor">0</text><rect x="183" y="40" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="196.5" y="58" text-anchor="middle" font-size="13" fill="currentColor">0</text><rect x="212" y="40" width="27" height="27" rx="3" fill="#16a34a" fill-opacity=".15" stroke="#16a34a"/><text x="225.5" y="58" text-anchor="middle" font-size="13" fill="currentColor">1</text><rect x="241" y="40" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="254.5" y="58" text-anchor="middle" font-size="13" fill="currentColor">0</text><rect x="270" y="40" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="283.5" y="58" text-anchor="middle" font-size="13" fill="currentColor">0</text><rect x="299" y="40" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="312.5" y="58" text-anchor="middle" font-size="13" fill="currentColor">0</text><text x="8" y="94" font-size="11" fill="currentColor">Result OR</text><rect x="96" y="75" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="109.5" y="93" text-anchor="middle" font-size="13" fill="currentColor">0</text><rect x="125" y="75" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="138.5" y="93" text-anchor="middle" font-size="13" fill="currentColor">0</text><rect x="154" y="75" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="167.5" y="93" text-anchor="middle" font-size="13" fill="currentColor">1</text><rect x="183" y="75" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="196.5" y="93" text-anchor="middle" font-size="13" fill="currentColor">0</text><rect x="212" y="75" width="27" height="27" rx="3" fill="#16a34a" fill-opacity=".15" stroke="#16a34a"/><text x="225.5" y="93" text-anchor="middle" font-size="13" fill="currentColor">1</text><rect x="241" y="75" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="254.5" y="93" text-anchor="middle" font-size="13" fill="currentColor">0</text><rect x="270" y="75" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="283.5" y="93" text-anchor="middle" font-size="13" fill="currentColor">1</text><rect x="299" y="75" width="27" height="27" rx="3" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="312.5" y="93" text-anchor="middle" font-size="13" fill="currentColor">0</text></svg></div>

#### 2. Update a multi-bit field

```c
#define MODE_MASK (UINT32_C(7) << 4)

reg = (reg & ~MODE_MASK) |
      ((UINT32_C(5) << 4) & MODE_MASK);
```

Clear bits 6:4, then insert the three-bit value 5.

#### 3. Hardware register caution

The expressions above are ordinary read-modify-write operations. For GPIO or interrupt status registers, use dedicated SET/CLEAR aliases or write-one-to-clear masks when the hardware defines them. Do not assume that every register can be read and written without side effects.

**Interview takeaway:** OR sets, AND with complement clears, XOR toggles and AND tests. Use unsigned masks of the proper width and follow register semantics.

### Why can a read-modify-write on a register be dangerous? {H}
A read-modify-write (RMW) is a sequence that reads a register, modifies a copy, then writes the result. It is dangerous if the register changes between the read and write or has special write semantics.

#### 1. Lost update

```c
REG |= (1U << 0);
```

Suppose REG initially contains zero.

| Step | Main code | Interrupt |
|---|---|---|
| 1 | Read 0 | |
| 2 | | Set bit 1; REG becomes 2 |
| 3 | Write old value OR 1 | |
| Result | REG = 1 | Bit 1 update lost |

#### 2. Write-one-to-clear (W1C)

If STATUS contains pending flags in bits 0 and 1, a write of 1 clears the corresponding flag. This is incorrect:

```c
STATUS |= (1U << 0); // May clear both pending flags
```

The read obtains both set flags, and the OR writes both back as ones. Correct for a documented W1C-only register:

```c
STATUS = (1U << 0);
```

#### 3. Safer hardware mechanisms

Some MCUs provide separate atomic set/clear registers. For example, on an STM32 with a GPIO BSRR register:

```c
GPIOA->BSRR = 1U << 5;        // Set pin 5
GPIOA->BSRR = 1U << (5 + 16); // Reset pin 5
```

These direct writes avoid software RMW on the output register. Confirm the peripheral's documented layout.

A lock or interrupt masking can protect against cooperating software writers, but cannot stop independent hardware changes.

**Interview takeaway:** Volatile does not make RMW atomic. Check hardware side effects, concurrent access and dedicated set/clear mechanisms.

### What is bit-banding on Cortex-M? {H}
Bit-banding is an optional Arm Cortex-M mechanism that maps individual bits in supported SRAM or peripheral regions to word addresses in an alias region. A write to an alias word updates the corresponding bit without a software read-modify-write sequence.

#### 1. Address calculation

For the classic bit-band mapping:

```text
alias = alias_base + byte_offset * 32 + bit_number * 4
```

For the SRAM region beginning at 0x20000000, its classic alias base is 0x22000000. The bit number is 0–7 within the selected byte.

#### 2. Example

To select bit 3 of byte address 0x20000004:

```text
byte_offset = 4
alias = 0x22000000 + 4 * 32 + 3 * 4
      = 0x2200008C
```

```c
volatile uint32_t *alias =
    (volatile uint32_t *)0x2200008CU;

*alias = 1; // Set selected bit
*alias = 0; // Clear selected bit
```

Reading the alias yields the selected bit according to the implemented bit-band behavior.

#### 3. Limitations

Not every Cortex-M implementation supports bit-banding; many newer cores and SoCs do not. Only documented bit-band address ranges can be used. Do not assume bit-band writes are suitable for registers with unusual read or write side effects.

Dedicated GPIO set/clear registers and atomic software operations are alternatives, depending on the memory type and hardware.

**Interview takeaway:** Bit-banding converts a bit selection into a word-addressed access. It is a platform-specific feature, not a universal Cortex-M capability.

### What happens before main() runs on a microcontroller? {M}
On a microcontroller, startup code prepares the processor and C runtime before calling main. The exact sequence depends on the boot ROM, device and toolchain.

#### 1. Typical Cortex-M reset flow

<div style="max-width:600px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 302" width="100%" role="img" aria-label="Reset, vector fetch, startup, memory initialization and main">
<rect x="20" y="5" width="300" height="44" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="22" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">Reset</text><text x="170" y="37" text-anchor="middle" font-size="10" fill="currentColor">Hardware loads initial MSP and reset PC</text><path d="M170 49 v16 m-4-5 4 5 4-5" stroke="currentColor" fill="none"/><rect x="20" y="65" width="300" height="44" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="82" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">Reset_Handler</text><text x="170" y="97" text-anchor="middle" font-size="10" fill="currentColor">Early processor and board setup</text><path d="M170 109 v16 m-4-5 4 5 4-5" stroke="currentColor" fill="none"/><rect x="20" y="125" width="300" height="44" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="142" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">Runtime memory</text><text x="170" y="157" text-anchor="middle" font-size="10" fill="currentColor">Copy .data; clear .bss</text><path d="M170 169 v16 m-4-5 4 5 4-5" stroke="currentColor" fill="none"/><rect x="20" y="185" width="300" height="44" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="202" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">Runtime initialization</text><text x="170" y="217" text-anchor="middle" font-size="10" fill="currentColor">Library / constructors as applicable</text><path d="M170 229 v16 m-4-5 4 5 4-5" stroke="currentColor" fill="none"/><rect x="20" y="245" width="300" height="44" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="262" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">main()</text><text x="170" y="277" text-anchor="middle" font-size="10" fill="currentColor">Application begins</text></svg></div>

#### 2. Why memory initialization is required

```c
int count = 10; // .data: initial image commonly in flash
int flag;       // .bss: starts at zero
```

The linker assigns runtime and load addresses. Startup copies initialized writable data to RAM and clears zero-initialized storage.

#### 3. Illustrative startup pseudocode

```text
Reset_Handler:
    perform required early CPU/system setup
    copy initial_data_image to data_ram
    zero bss_ram
    initialize runtime
    call main
    handle unexpected return
```

Some startup implementations call SystemInit before RAM initialization; early code must not rely on uninitialized C objects. External RAM must be configured before copying data into it.

#### 4. Debugging before main

Check the vector table, initial stack address, reset PC, flash/RAM placement, clocks and fault status. Use a breakpoint in Reset_Handler and examine linker symbols.

**Interview takeaway:** main is not the processor's reset entry. Hardware and startup code establish the conditions required for valid C execution.

### What is a linker script and what does it contain? {M}
A linker script describes how object-file sections are combined and placed in the target's memory. It also defines symbols used by startup code and reserves memory for special purposes.

#### 1. Example GNU linker script fragment

```ld
MEMORY {
    FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 512K
    RAM   (rwx) : ORIGIN = 0x20000000, LENGTH = 128K
}

SECTIONS {
    .text : {
        KEEP(*(.isr_vector))
        *(.text*) *(.rodata*)
    } > FLASH

    .data : {
        _sdata = .;
        *(.data*)
        _edata = .;
    } > RAM AT> FLASH

    _sidata = LOADADDR(.data);

    .bss (NOLOAD) : {
        _sbss = .;
        *(.bss*) *(COMMON)
        _ebss = .;
    } > RAM
}
```

The addresses and sizes are illustrative. A production script also handles alignment, stack, heap, entry point, runtime sections and platform-specific requirements.

#### 2. VMA and LMA

| Term | Meaning |
|---|---|
| VMA | Address where a section resides during execution |
| LMA | Address where its initial image is loaded or stored |

For .data, the VMA is RAM and the LMA is commonly flash. Startup copies from _sidata into [_sdata, _edata).

#### 3. Inspect placement

```sh
arm-none-eabi-readelf -S firmware.elf
arm-none-eabi-size firmware.elf
```

A linker map also identifies object files, symbol addresses and memory usage.

**Interview takeaway:** The compiler creates sections; the linker script places them. Startup code and hardware memory configuration must agree with the script.

### What is the vector table? {E}
A vector table contains the information needed to enter exception and interrupt handlers. Its format depends on the architecture.

#### 1. Cortex-M vector table

<div style="max-width:600px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 199" width="100%" role="img" aria-label="Cortex-M vector table: initial MSP, reset, core exceptions and external IRQs">
<rect x="8" y="5" width="85" height="30" fill="#3b82f6" fill-opacity=".13" stroke="#3b82f6"/><text x="50" y="24" font-size="11" text-anchor="middle" fill="currentColor">0x00</text><rect x="93" y="5" width="239" height="30" fill="#16a34a" fill-opacity=".11" stroke="#16a34a"/><text x="212" y="24" font-size="11" text-anchor="middle" fill="currentColor">Initial MSP value</text><rect x="8" y="36" width="85" height="30" fill="#3b82f6" fill-opacity=".13" stroke="#3b82f6"/><text x="50" y="55" font-size="11" text-anchor="middle" fill="currentColor">0x04</text><rect x="93" y="36" width="239" height="30" fill="#16a34a" fill-opacity=".11" stroke="#16a34a"/><text x="212" y="55" font-size="11" text-anchor="middle" fill="currentColor">Reset_Handler</text><rect x="8" y="67" width="85" height="30" fill="#3b82f6" fill-opacity=".13" stroke="#3b82f6"/><text x="50" y="86" font-size="11" text-anchor="middle" fill="currentColor">0x08</text><rect x="93" y="67" width="239" height="30" fill="#16a34a" fill-opacity=".11" stroke="#16a34a"/><text x="212" y="86" font-size="11" text-anchor="middle" fill="currentColor">NMI_Handler</text><rect x="8" y="98" width="85" height="30" fill="#3b82f6" fill-opacity=".13" stroke="#3b82f6"/><text x="50" y="117" font-size="11" text-anchor="middle" fill="currentColor">0x0C</text><rect x="93" y="98" width="239" height="30" fill="#16a34a" fill-opacity=".11" stroke="#16a34a"/><text x="212" y="117" font-size="11" text-anchor="middle" fill="currentColor">HardFault_Handler</text><rect x="8" y="129" width="85" height="30" fill="#3b82f6" fill-opacity=".13" stroke="#3b82f6"/><text x="50" y="148" font-size="11" text-anchor="middle" fill="currentColor">...</text><rect x="93" y="129" width="239" height="30" fill="#16a34a" fill-opacity=".11" stroke="#16a34a"/><text x="212" y="148" font-size="11" text-anchor="middle" fill="currentColor">Other core exceptions</text><rect x="8" y="160" width="85" height="30" fill="#3b82f6" fill-opacity=".13" stroke="#3b82f6"/><text x="50" y="179" font-size="11" text-anchor="middle" fill="currentColor">0x40</text><rect x="93" y="160" width="239" height="30" fill="#16a34a" fill-opacity=".11" stroke="#16a34a"/><text x="212" y="179" font-size="11" text-anchor="middle" fill="currentColor">External IRQ 0 handler</text></svg></div>

Offsets are relative to the vector base. At reset, Cortex-M obtains the initial main stack pointer from the first entry and the reset-handler address from the second.

#### 2. Interrupt dispatch

For a typical external interrupt number n, the exception number is 16+n. The processor uses the corresponding vector entry after accepting the exception.

#### 3. Relocation

On cores supporting VTOR, privileged firmware can select another correctly aligned vector table. A bootloader may configure VTOR for the application. Some cores instead use platform-specific remapping or other mechanisms.

#### 4. Difference from Cortex-A

AArch64 uses exception vector instruction slots at offsets from VBAR_ELx rather than a Cortex-M-style array of handler pointers.

**Interview takeaway:** The vector table is an architecture-defined interface between hardware exception entry and software handlers. Its placement, alignment and entry format must match the target.

### What are weak symbols? {M}
A weak symbol is a linker symbol that can be overridden by a suitable strong definition. It is widely used for default firmware handlers and board hooks.

#### 1. Default implementation

```c
// startup.c
void Default_Handler(void)
{
    for (;;) {}
}

void UART_IRQHandler(void)
    __attribute__((weak, alias("Default_Handler")));
```

With a supporting GNU-compatible compiler, the weak UART handler refers to Default_Handler unless a strong definition is selected.

#### 2. Application override

```c
// uart.c
void UART_IRQHandler(void)
{
    uart_service_irq();
}
```

The linker selects the strong handler instead of the weak default. The signatures and symbol names must match.

#### 3. Board customization

```c
__attribute__((weak))
void board_init(void)
{
    // Default board initialization
}
```

Another translation unit can supply a strong board_init implementation to customize the board without editing the common source.

#### 4. Important details

Weak symbols and aliases are toolchain-specific extensions. Multiple strong definitions usually produce a link error. Archive extraction and link order can affect which definitions are included; check the final ELF symbol table with nm.

**Interview takeaway:** Weak symbols provide overridable defaults, not runtime polymorphism. Verify the final linked symbol when debugging an unexpected default handler.

### How do you place a variable or function at a specific address or section? {M}
Firmware can control object placement through compiler section attributes and linker-script rules. The compiler emits the object into a named input section; the linker assigns its final address.

#### 1. Put a variable in a special section

```c
__attribute__((section(".dma_buffer"), aligned(64)))
static unsigned char rx_buf[256];
```

This GNU-compatible attribute requests a named section and 64-byte alignment.

#### 2. Linker placement

```ld
.dma_buffer (NOLOAD) : ALIGN(64) {
    KEEP(*(.dma_buffer))
} > DMA_RAM
```

DMA_RAM must be a defined MEMORY region accessible to the device. NOLOAD does not itself initialize the data; the startup code must implement any required initialization.

#### 3. Place a function in RAM

```c
__attribute__((section(".ramfunc")))
void flash_operation(void)
{
    // Device-specific operation
}
```

Arrange .ramfunc with a RAM execution address and a flash load address; copy it before execution. If flash is inaccessible during programming, called routines, constants and interrupt paths may also need relocation.

#### 4. Access an absolute hardware address

```c
#define REG (*(volatile uint32_t *)0x40000000U)
```

This accesses an existing mapped register; it does not allocate a C variable at that address.

Verify final placement with the linker map, readelf or nm. Compiler optimization and section garbage collection can remove unreferenced objects unless retained appropriately.

**Interview takeaway:** Section attributes select sections, not final addresses. The linker script determines placement; alignment, initialization and DMA access are separate requirements.

### What is a watchdog timer and how should you use it? {E}
A watchdog timer supervises software execution. If the software fails to service it within a configured time window, the watchdog triggers a reset or another defined action.

#### 1. Basic operation

```text
Configure timeout
        |
Software periodically checks system health
        |
Healthy? -- yes --> Service watchdog
        |
        no
        v
Timeout --> Reset / configured recovery
```

An independent watchdog may use a separate clock so that it can recover from some CPU or clock failures. Windowed watchdogs can detect servicing too early as well as too late.

#### 2. Good firmware design

```c
void supervisor_tick(void)
{
    if (control_task_progressed() &&
        comm_task_progressed() &&
        system_state_valid()) {
        watchdog_refresh();
    }
}
```

These functions represent system-specific health checks. Progress should be fresh since the previous check, not a flag left permanently set.

#### 3. Choosing the timeout

Account for worst-case execution time, interrupt latency, boot time and legitimate lengthy operations. The watchdog must trigger before the system's allowed recovery deadline, without resetting a healthy system under worst-case load.

#### 4. Recovery and diagnostics

Read and preserve reset-cause registers early after reboot. Record useful fault context where possible, and handle repeated failures according to system safety requirements.

**Interview takeaway:** Never blindly feed a watchdog in an interrupt or unconditional loop. It should be serviced only after confirming that essential software is progressing.

### What is debouncing and how do you implement it? {E}
Mechanical switches can produce several rapid transitions when pressed or released. Debouncing filters these transitions so software generates a single stable button event.

#### 1. Signal behavior

<div style="max-width:650px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 145" width="100%" role="img" aria-label="Raw switch signal bounces before settling; filtered signal transitions once after the stability period">
<text x="8" y="13" font-size="11" fill="currentColor">Raw switch input</text><path d="M10 54 H65 V25 H78 V54 H90 V25 H104 V54 H116 V25 H330" fill="none" stroke="#3b82f6" stroke-width="2"/>
<text x="8" y="87" font-size="11" fill="currentColor">Debounced input</text><path d="M10 127 H205 V98 H330" fill="none" stroke="#16a34a" stroke-width="2"/><path d="M116 59 V94 M205 59 V94 M116 72 H205" stroke="currentColor" stroke-dasharray="4 3" fill="none"/><text x="160" y="68" text-anchor="middle" font-size="10" fill="currentColor">Stable interval</text><text x="330" y="142" text-anchor="end" font-size="10" fill="currentColor">Time →</text></svg></div>

#### 2. Nonblocking software implementation

Call the following function every 1 ms. It accepts a transition after 20 consecutive samples that differ from the currently stable state.

```c
#include <stdbool.h>

bool debounce(bool raw)
{
    static bool stable;
    static unsigned count;

    if (raw == stable) {
        count = 0;
    } else if (++count >= 20) {
        stable = raw;
        count = 0;
        // Generate a transition event if needed.
    }
    return stable;
}
```

This is a single-button example initialized to false. Initialize state appropriately for the hardware; use a separate state structure for each button.

#### 3. Hardware alternative

An RC filter and Schmitt-trigger input can reduce bouncing, provided their electrical behavior and timing are suitable.

**Interview takeaway:** Do not insert a long blocking delay in a button ISR. Sample periodically or use a nonblocking timer and choose the debounce interval based on the switch's actual behavior.

### How do you scan a matrix keypad? {M}
A matrix keypad connects switches between rows and columns so that R rows and C columns can represent R×C keys using R+C GPIO pins.

#### 1. Example: 4×4 keypad

<div style="max-width:600px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 211" width="100%" role="img" aria-label="Four rows and four columns, highlighted key at row two column one">
<path d="M66 55 H300" stroke="#64748b" stroke-width="1"/><text x="56" y="59" text-anchor="end" font-size="11" fill="currentColor">R0</text><path d="M95 30 V185" stroke="#64748b" stroke-width="1"/><text x="95" y="20" text-anchor="middle" font-size="11" fill="currentColor">C0</text><path d="M66 95 H300" stroke="#64748b" stroke-width="1"/><text x="56" y="99" text-anchor="end" font-size="11" fill="currentColor">R1</text><path d="M150 30 V185" stroke="#16a34a" stroke-width="2"/><text x="150" y="20" text-anchor="middle" font-size="11" fill="currentColor">C1</text><path d="M66 135 H300" stroke="#16a34a" stroke-width="2"/><text x="56" y="139" text-anchor="end" font-size="11" fill="currentColor">R2</text><path d="M205 30 V185" stroke="#64748b" stroke-width="1"/><text x="205" y="20" text-anchor="middle" font-size="11" fill="currentColor">C2</text><path d="M66 175 H300" stroke="#64748b" stroke-width="1"/><text x="56" y="179" text-anchor="end" font-size="11" fill="currentColor">R3</text><path d="M260 30 V185" stroke="#64748b" stroke-width="1"/><text x="260" y="20" text-anchor="middle" font-size="11" fill="currentColor">C3</text>
<circle cx="95" cy="55" r="11" fill="#94a3b8" fill-opacity=".25" stroke="currentColor" stroke-width=".5"/><circle cx="150" cy="55" r="11" fill="#94a3b8" fill-opacity=".25" stroke="currentColor" stroke-width=".5"/><circle cx="205" cy="55" r="11" fill="#94a3b8" fill-opacity=".25" stroke="currentColor" stroke-width=".5"/><circle cx="260" cy="55" r="11" fill="#94a3b8" fill-opacity=".25" stroke="currentColor" stroke-width=".5"/><circle cx="95" cy="95" r="11" fill="#94a3b8" fill-opacity=".25" stroke="currentColor" stroke-width=".5"/><circle cx="150" cy="95" r="11" fill="#94a3b8" fill-opacity=".25" stroke="currentColor" stroke-width=".5"/><circle cx="205" cy="95" r="11" fill="#94a3b8" fill-opacity=".25" stroke="currentColor" stroke-width=".5"/><circle cx="260" cy="95" r="11" fill="#94a3b8" fill-opacity=".25" stroke="currentColor" stroke-width=".5"/><circle cx="95" cy="135" r="11" fill="#94a3b8" fill-opacity=".25" stroke="currentColor" stroke-width=".5"/><circle cx="150" cy="135" r="11" fill="#16a34a" fill-opacity=".9" stroke="currentColor" stroke-width=".5"/><circle cx="205" cy="135" r="11" fill="#94a3b8" fill-opacity=".25" stroke="currentColor" stroke-width=".5"/><circle cx="260" cy="135" r="11" fill="#94a3b8" fill-opacity=".25" stroke="currentColor" stroke-width=".5"/><circle cx="95" cy="175" r="11" fill="#94a3b8" fill-opacity=".25" stroke="currentColor" stroke-width=".5"/><circle cx="150" cy="175" r="11" fill="#94a3b8" fill-opacity=".25" stroke="currentColor" stroke-width=".5"/><circle cx="205" cy="175" r="11" fill="#94a3b8" fill-opacity=".25" stroke="currentColor" stroke-width=".5"/><circle cx="260" cy="175" r="11" fill="#94a3b8" fill-opacity=".25" stroke="currentColor" stroke-width=".5"/><text x="170" y="205" text-anchor="middle" font-size="10" fill="currentColor">Selected key: row 2, column 1 (zero-based)</text></svg></div>

#### 2. Scanning procedure

1. Configure columns as inputs with pull-ups.
2. Drive one selected row low, leaving other rows in a safe inactive/high-impedance state.
3. Allow signals to settle and read columns.
4. A low column indicates a possible pressed key on the active row.
5. Repeat for other rows and debounce detected states.

#### 3. Illustrative code

```c
for (unsigned row = 0; row < 4; row++) {
    select_row_low(row);   // Other rows safely inactive
    wait_gpio_settle();

    for (unsigned col = 0; col < 4; col++) {
        bool pressed = !read_column(col);
        update_key_debounce(row, col, pressed);
    }
}
release_all_rows();
```

These helpers depend on the GPIO and keypad circuitry.

#### 4. Ghosting

Multiple simultaneous presses can create unintended current paths through a diode-less matrix, causing false key detections. Diodes or restricted key combinations can address this. Avoid driving conflicting row outputs against each other.

**Interview takeaway:** Matrix scanning saves GPIO pins but requires controlled row activation, settling, debouncing and a policy for simultaneous presses.

### What is polling versus interrupts versus DMA? {E}
Polling, interrupts and DMA are three ways of coordinating data transfer between the processor and peripherals.

#### 1. Polling

```c
while (!uart_tx_ready()) {
    // Wait (normally with a timeout).
}
uart_write_byte(data);
```

The CPU repeatedly checks device status. It is simple but can waste CPU cycles while waiting.

#### 2. Interrupt-driven operation

```c
void UART_IRQHandler(void)
{
    if (uart_rx_ready())
        queue_rx_byte(uart_read_byte());
}
```

The device notifies the CPU when service is required. The CPU can perform other work between interrupts.

#### 3. DMA transfer

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 158" width="100%" role="img" aria-label="CPU configures DMA; DMA moves peripheral data into RAM and interrupts CPU on completion">
<rect x="120" y="8" width="100" height="32" rx="5" fill="#3b82f6" fill-opacity=".13" stroke="#3b82f6"/><text x="170" y="28" text-anchor="middle" font-size="12" fill="currentColor">CPU</text>
<rect x="120" y="76" width="100" height="38" rx="5" fill="#eab308" fill-opacity=".15" stroke="#ca8a04"/><text x="170" y="99" text-anchor="middle" font-size="12" fill="currentColor">DMA engine</text>
<rect x="5" y="76" width="90" height="38" rx="5" fill="#16a34a" fill-opacity=".13" stroke="#16a34a"/><text x="50" y="99" text-anchor="middle" font-size="11" fill="currentColor">Peripheral</text>
<rect x="245" y="76" width="90" height="38" rx="5" fill="#16a34a" fill-opacity=".13" stroke="#16a34a"/><text x="290" y="99" text-anchor="middle" font-size="12" fill="currentColor">RAM</text>
<path d="M95 95 H120 m-5-4 5 4-5 4 M220 95 H245 m-5-4 5 4-5 4 M150 40 V76 m-4-5 4 5 4-5 M190 76 V40 m-4 5 4-5 4 5" stroke="currentColor" fill="none"/>
<text x="140" y="58" text-anchor="end" font-size="10" fill="currentColor">Configure</text><text x="199" y="58" font-size="10" fill="currentColor">Completion IRQ</text><text x="170" y="139" text-anchor="middle" font-size="10" fill="currentColor">Hardware transfers data over the system interconnect.</text></svg></div>

The CPU prepares a buffer and configures source, destination, length and direction. DMA moves the data and signals completion. The CPU handles setup, errors and ownership/cache synchronization.

| Feature | Polling | Interrupt | DMA |
|---|---|---|---|
| CPU involvement | Repeated status checks | Per event | Setup and completion |
| Good for | Short waits, boot | Sporadic events | Large/continuous transfers |
| Complexity | Low | Medium | Higher |

**Interview takeaway:** Use polling for simple bounded waits, interrupts for asynchronous events and DMA for bulk transfers. DMA is not automatically faster for very small transfers.

### What are the cache coherency problems with DMA? {H}
DMA can access memory independently of the CPU. On a non-coherent system, CPU caches may contain data that has not reached RAM, or data that is stale after DMA writes.

#### 1. Transmit: CPU to device

The CPU writes a buffer. The new value may exist only in dirty cache lines. A non-coherent DMA master could read older RAM contents. Clean or synchronize the buffer before transferring ownership to the device.

#### 2. Receive: device to CPU

DMA writes RAM while the CPU may still cache an old copy. Prepare the receive buffer before DMA, then invalidate or synchronize the appropriate cache lines after completion and before CPU access.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 184" width="100%" role="img" aria-label="Non-coherent transmit requires CPU cache clean; receive requires synchronization before CPU reads">
<text x="8" y="18" font-size="11" font-weight="600" fill="currentColor">TX: clean before device ownership</text><rect x="8" y="30" width="100" height="38" rx="5" fill="#16a34a" fill-opacity=".12" stroke="#16a34a"/><text x="58" y="53" font-size="10" text-anchor="middle" fill="currentColor">CPU cache: new</text><path d="M108 49 h12 m-4-3 4 3-4 3" stroke="currentColor" fill="none"/><rect x="120" y="30" width="100" height="38" rx="5" fill="#16a34a" fill-opacity=".12" stroke="#16a34a"/><text x="170" y="53" font-size="10" text-anchor="middle" fill="currentColor">RAM: new</text><path d="M220 49 h12 m-4-3 4 3-4 3" stroke="currentColor" fill="none"/><rect x="232" y="30" width="100" height="38" rx="5" fill="#16a34a" fill-opacity=".12" stroke="#16a34a"/><text x="282" y="53" font-size="10" text-anchor="middle" fill="currentColor">DMA reads</text><text x="8" y="108" font-size="11" font-weight="600" fill="currentColor">RX: synchronize before CPU ownership</text><rect x="8" y="120" width="100" height="38" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="58" y="143" font-size="10" text-anchor="middle" fill="currentColor">DMA writes</text><path d="M108 139 h12 m-4-3 4 3-4 3" stroke="currentColor" fill="none"/><rect x="120" y="120" width="100" height="38" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="143" font-size="10" text-anchor="middle" fill="currentColor">RAM: new</text><path d="M220 139 h12 m-4-3 4 3-4 3" stroke="currentColor" fill="none"/><rect x="232" y="120" width="100" height="38" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="282" y="143" font-size="10" text-anchor="middle" fill="currentColor">CPU reads new</text></svg></div>

#### 3. Linux streaming DMA example

```c
dma_addr_t addr = dma_map_single(dev, buf, len,
                                DMA_TO_DEVICE);
if (dma_mapping_error(dev, addr))
    return -EIO;

/* Program hardware using addr, then wait for completion. */

dma_unmap_single(dev, addr, len, DMA_TO_DEVICE);
```

The DMA API handles platform-specific mapping and cache synchronization. Use suitable DMA-mappable memory, not arbitrary stack or vmalloc addresses.

For reusable streaming mappings, dma_sync_single_for_cpu and dma_sync_single_for_device transfer access ownership as required. Do not access the buffer while the device owns it.

#### 4. Coherent systems

Coherent DMA allocations simplify visibility, but descriptor publication and ownership ordering may still require dma_wmb/dma_rmb or other documented synchronization. A CPU virtual address is not necessarily the device's DMA address.

**Interview takeaway:** Cache coherency, memory ordering and buffer ownership are different problems. Use the platform DMA API and protect full cache lines on non-coherent systems.

### What is a memory barrier and why would firmware need one? {H}
A memory barrier constrains ordering or completion of memory operations. Modern processors and compilers can reorder accesses, so communication between cores or devices requires explicit synchronization.

#### 1. Without ordering

```text
Core 0                  Core 1
data = 100              if (flag == 1)
flag = 1                    read data
```

On a weakly ordered architecture, the consumer may observe the flag before the data. Ordinary racing C variables are also undefined in threaded C; this is a conceptual hardware example.

#### 2. Linux publication example

```c
// Producer (one-time publication)
WRITE_ONCE(data, 100);
smp_wmb();
WRITE_ONCE(flag, 1);

// Consumer
if (READ_ONCE(flag) == 1) {
    smp_rmb();
    value = READ_ONCE(data);
}
```

The paired barriers enforce required ordering when the consumer observes the published flag. A release store and acquire load are often clearer for this pattern.

#### 3. ARM barrier types

| Barrier | Purpose |
|---|---|
| DMB | Orders specified memory accesses within its scope |
| DSB | Waits for required completion of specified operations |
| ISB | Synchronizes later instruction execution with context changes |

For example, updating certain system registers may require an ISB after the architecture-specified sequence. DMA and MMIO may need barriers with a different scope than SMP shared memory.

#### 4. Compiler barrier vs CPU barrier

```c
__asm__ volatile("" ::: "memory"); // Compiler barrier
__DMB();                          // CMSIS CPU barrier
```

The empty assembly does not emit a CPU ordering instruction. Follow the compiler/architecture interface for the required semantics.

**Interview takeaway:** A barrier does not automatically make an operation atomic, clean caches or provide a complete synchronization protocol. In portable C threads use C11 atomic acquire/release operations or locks.

### What is the Arm calling convention (AAPCS), and why does it matter in embedded work? {M}
AAPCS (Arm Architecture Procedure Call Standard) specifies how functions exchange arguments and return values, preserve registers and align the stack. It lets separately compiled code and assembly work together.

#### 1. AAPCS32 vs AAPCS64

| Feature | AAPCS32 | AAPCS64 |
|---|---|---|
| Common integer argument registers | R0–R3 | X0–X7 |
| Common integer return | R0 (R1 may also be used) | X0 (X1 may also be used) |
| Link register | R14 | X30 |
| Public-interface stack alignment | 8 bytes | 16 bytes |

Floating-point arguments, structures and special platform registers follow additional rules.

#### 2. AArch64 example

```c
long add(long a, long b)
{
    return a + b;
}
```

Typical AArch64 LP64 code:

```asm
add:
    ADD X0, X0, X1
    RET
```

The caller supplies a and b in X0 and X1; X0 contains the return value.

#### 3. Caller-saved vs callee-saved

For AAPCS64, X19–X29 are callee-saved; SP is preserved, and X18 is platform-specific. A non-leaf function typically saves LR if another call would overwrite it. Other general registers commonly hold arguments or temporary values.

#### 4. Embedded relevance

Startup code, interrupt wrappers, bootloader transitions, RTOS context switching and handwritten assembly must obey the applicable ABI or explicitly document a different interface. An exception frame is not the same as an ordinary function call frame.

**Interview takeaway:** AAPCS is a software interface contract, not merely a list of registers. Incorrect stack alignment or register preservation can break otherwise correct C code.

### What are compiler intrinsics, and when should you use them instead of inline assembly? {M}
Compiler intrinsics are compiler-recognized functions or built-ins that expose architecture-specific operations or optimization information. They often translate directly into special instructions.

#### 1. Example: count leading zeros

```c
unsigned leading_zeros(unsigned int x)
{
    return x ? __builtin_clz(x) : sizeof(x) * CHAR_BIT;
}
```

GCC and Clang can use an appropriate CPU instruction, such as CLZ on Arm. The zero check matters because the traditional __builtin_clz is undefined for zero.

#### 2. CMSIS intrinsics

```c
__disable_irq();
__DMB();
// Protected operation as appropriate
__enable_irq();
```

These illustrate processor-control intrinsics. In reusable critical sections save and restore the previous interrupt mask rather than blindly enabling interrupts.

#### 3. Intrinsics vs inline assembly

| Intrinsic | Inline assembly |
|---|---|
| Compiler understands its documented semantics | Compiler relies on explicit operands and clobbers |
| Easier register allocation | More control over instruction sequence |
| Usually simpler to maintain | Requires precise constraints and target expertise |

Use inline assembly for operations not exposed by a suitable intrinsic, or when a carefully specified instruction sequence is essential.

**Interview takeaway:** Prefer documented intrinsics where possible. Check their target requirements, edge cases and ordering semantics; an intrinsic does not automatically imply a memory barrier.

### How do you implement a delay without blocking the CPU? {M}
A nonblocking delay allows the CPU to perform other work while waiting for a deadline. Instead of spinning, record the starting time and check elapsed time from a periodic service function.

#### 1. Blocking approach

```c
delay_ms(100);
toggle_led();
```

The caller cannot service other foreground work during a busy-wait delay.

#### 2. Nonblocking approach

```c
#include <stdint.h>

void led_service(void)
{
    static uint32_t last;
    uint32_t now = millis();

    if ((uint32_t)(now - last) >= 100U) {
        last = now;
        toggle_led();
    }
}
```

Call led_service repeatedly from the main loop. The unsigned subtraction handles ordinary counter wraparound, provided the elapsed interval is observed within the counter's wrap period.

#### 3. Main-loop example

```c
for (;;) {
    led_service();
    uart_service();
    button_service();
}
```

Each service function performs short bounded work and returns promptly. Updating last to now skips missed periods; adding the period to last instead maintains a periodic schedule but requires an explicit missed-deadline policy.

#### 4. RTOS alternative

A task may block using an RTOS delay or wait for a timer event, allowing other ready tasks to run. Blocking the current task is different from busy-waiting the CPU.

**Interview takeaway:** Use elapsed-time checks, hardware timers or RTOS waits rather than spin delays for long waits. Time resolution and scheduling jitter determine actual timing accuracy.

### What is a super loop (foreground/background) architecture? {E}
A super loop is a cooperative firmware architecture in which the main function repeatedly calls short service routines. Interrupts handle asynchronous hardware events.

#### 1. Basic implementation

```c
int main(void)
{
    board_init();

    for (;;) {
        button_service();
        uart_service();
        control_service();
        watchdog_service();
    }
}
```

Each service routine checks whether work is pending, performs a bounded amount of work and returns.

#### 2. Foreground/background communication

```text
Hardware IRQ --> ISR --> queue / event
                              |
                              v
main loop --> input --> process --> output
     ^                                  |
     +----------------------------------+
```

The ISR captures events quickly. Foreground code performs parsing and application-level processing. Shared data needs an appropriate synchronization protocol.

#### 3. Advantages and limitations

| Advantage | Limitation |
|---|---|
| Simple control flow | No preemptive task scheduling |
| Low memory overhead | One slow service delays all others |
| Easy on small MCUs | Complex timing becomes difficult |

Use nonblocking drivers, explicit state machines and event-driven processing. If multiple independent deadlines become difficult to satisfy, an RTOS may be a better fit.

**Interview takeaway:** A super loop is cooperative: every service must return promptly. Interrupts alone do not guarantee the foreground loop meets deadlines.

### How do you write a state machine in C? {M}
A finite state machine (FSM) models behavior using a finite set of states and explicit transitions triggered by events. It avoids scattered flags and makes nonblocking control flow easier to test.

#### 1. Example: device startup

<div style="max-width:620px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 168" width="100%" role="img" aria-label="Idle transitions to starting on start, starting to running on ready, and starting or running to fault on error">
<rect x="8" y="15" width="94" height="32" rx="5" fill="#3b82f6" fill-opacity=".13" stroke="#3b82f6"/><text x="55" y="35" font-size="11" font-weight="600" text-anchor="middle" fill="currentColor">IDLE</text><rect x="123" y="15" width="94" height="32" rx="5" fill="#3b82f6" fill-opacity=".13" stroke="#3b82f6"/><text x="170" y="35" font-size="11" font-weight="600" text-anchor="middle" fill="currentColor">STARTING</text><rect x="238" y="15" width="94" height="32" rx="5" fill="#3b82f6" fill-opacity=".13" stroke="#3b82f6"/><text x="285" y="35" font-size="11" font-weight="600" text-anchor="middle" fill="currentColor">RUNNING</text><rect x="123" y="124" width="94" height="32" rx="5" fill="#dc2626" fill-opacity=".13" stroke="#dc2626"/><text x="170" y="144" font-size="11" font-weight="600" text-anchor="middle" fill="currentColor">FAULT</text><path d="M102 31 H123 m-4-3 4 3-4 3 M217 31 H238 m-4-3 4 3-4 3 M170 47 V124 m-4-5 4 5 4-5 M285 47 V140 H217 m5-4 -5 4 5 4" stroke="currentColor" fill="none"/><text x="112" y="11" text-anchor="middle" font-size="9" fill="currentColor">START</text><text x="227" y="11" text-anchor="middle" font-size="9" fill="currentColor">READY</text><text x="176" y="88" font-size="10" fill="currentColor">ERROR</text><text x="291" y="87" font-size="10" fill="currentColor">ERROR</text></svg></div>

#### 2. Implementation

```c
enum State { IDLE, STARTING, RUNNING, FAULT };
enum Event { START, READY, ERROR };

static enum State state = IDLE;

void handle_event(enum Event event)
{
    switch (state) {
    case IDLE:
        if (event == START) {
            begin_startup();
            state = STARTING;
        }
        break;
    case STARTING:
        if (event == READY)
            state = RUNNING;
        else if (event == ERROR)
            state = FAULT;
        break;
    case RUNNING:
        if (event == ERROR)
            state = FAULT;
        break;
    case FAULT:
        break;
    }
}
```

The example assumes a single event-processing context and nonblocking startup. A real implementation adds timeouts, shutdown/recovery actions and handling of unexpected events.

#### 3. Testing

Build a state/event transition table and test each defined transition, error path and invalid event. A queue can serialize events produced by interrupts or other tasks.

**Interview takeaway:** Keep state transitions explicit and actions bounded. State machines make asynchronous firmware easier to reason about than implicit combinations of flags.

### How do you design error handling in firmware? {M}
Firmware error handling must detect failures, keep the system in a defined state and provide useful diagnostic information. The recovery strategy depends on the device's functional and safety requirements.

#### 1. Detect and propagate errors

```c
int read_sensor(int *value)
{
    if (!value)
        return -EINVAL;

    int ret = bus_read_sensor(value);

    if (ret < 0)
        return ret;

    return 0;
}
```

This illustrates an errno-style interface; actual return values depend on the platform. Specify whether output values are valid on failure.

#### 2. Use bounded retries

```c
int ret;
for (unsigned i = 0; i < 3; i++) {
    ret = read_sensor(&value);
    if (ret == 0)
        break;
    if (!is_retryable(ret))
        break;
}

if (ret < 0)
    handle_sensor_failure(ret);
```

Retries should have a deadline and must not repeat operations that are unsafe to repeat. Backoff and bus recovery may be necessary.

#### 3. Recovery levels

| Failure | Possible response |
|---|---|
| Transient communication error | Limited retry |
| Peripheral stuck | Controlled reinitialization |
| Invalid input | Reject and report |
| Critical subsystem fault | Enter system-defined safe state |

Record relevant state, error codes, counters and reset causes. Avoid flooding logs or blocking a critical path.

**Interview takeaway:** Never ignore error returns or wait forever on unreliable hardware. Recovery must be bounded, observable and consistent with the system's safety requirements.

### What does the inline assembly __asm volatile("" ::: "memory") do? {H}
The GNU C expression `__asm__ volatile("" ::: "memory")` is an empty inline assembly statement with a memory clobber. It acts as a **compiler memory barrier**.

#### 1. Meaning of each part

```c
__asm__ volatile("" ::: "memory");
```

- Empty instruction string: emits no actual CPU instruction.
- volatile: the compiler retains the assembly operation under its documented rules.
- memory clobber: tells the compiler that memory may have been read or changed by the assembly.

The compiler must account for those possible effects when optimizing memory accesses across the statement.

#### 2. Why it is not a CPU barrier

```text
C source --> compiler memory barrier --> machine code
                                      (no fence instruction)
CPU execution --> architecture memory model still applies
```

The CPU can still reorder accesses permitted by the architecture. The compiler may also move computations that do not depend on affected memory.

#### 3. Compare with Arm barriers

```c
__asm__ volatile("" ::: "memory"); // Compiler barrier
__DMB();                         // CMSIS memory-ordering barrier
```

The CMSIS intrinsic has platform-specific semantics and emits the appropriate barrier instruction. Use Linux barrier APIs in kernel code.

**Interview takeaway:** A compiler barrier limits compiler transformations; it does not provide CPU ordering, atomicity, cache maintenance or C11 inter-thread synchronization.

### How do you make a firmware image position independent or relocatable? {H}
Position-independent code (PIC) can execute without assuming a fixed load address for its instruction references. Relocatable firmware can be moved by applying the required address fixups before execution.

#### 1. Why ordinary firmware may fail after moving

```text
Image linked for 0x08000000
    absolute pointer = 0x08001000

Image copied to 0x20000000
    absolute pointer still refers to old address
```

PC-relative branches often remain valid if the whole image moves together; absolute data pointers or addresses may not.

#### 2. Common approaches

- Compile with target-appropriate PIC options when supported.
- Use PC-relative references and a global offset table where required.
- Retain relocation records and apply them in a loader.
- Link separate images for different execution addresses if relocation is unnecessary.

For example, ELF relocations can describe locations that need adjustment when an image's load bias changes. The exact fixup calculation depends on relocation type and architecture.

#### 3. Firmware-specific requirements

Interrupt vectors, absolute peripheral addresses, data initialization, stack placement, exception tables and startup assembly may need separate handling. MMIO addresses usually must remain fixed even when code moves.

Inspect the image using:

```sh
readelf -r firmware.elf
objdump -d firmware.elf
```

A compiler option such as -fPIC alone is not enough to make a bare-metal firmware image relocatable.

**Interview takeaway:** PIC avoids certain fixed-address assumptions; relocation repairs address-dependent references. The entire startup and memory layout must support the chosen scheme.

### How does a bootloader jump to the application on Cortex-M? {H}
A Cortex-M bootloader hands control to an application by validating its image and establishing the application's expected reset-entry state. A simple C function call to the application's entry address is generally insufficient.

#### 1. Application vector table

```text
APP_BASE + 0 : Initial MSP value
APP_BASE + 4 : Reset_Handler address (Thumb bit set)
APP_BASE + 8 : NMI vector
...
```

The bootloader validates the initial stack against allowed RAM ranges and the reset vector against executable application memory. If secure boot is required, authenticate the image before execution.

#### 2. Handoff sequence

1. Stop or quiesce relevant peripherals, timers and DMA.
2. Disable interrupts and clear pending sources as required.
3. Configure the application's vector table base where VTOR is supported, and perform required barriers.
4. Establish the documented privilege, stack and interrupt-mask state.
5. Load the application's MSP and branch to its reset handler using a safe final assembly handoff.

#### 3. Illustrative final handoff (Thumb assembly)

```asm
// r0 = validated initial MSP; r1 = validated reset vector
// Preconditions: required privileged Thread-mode state,
// correct vector base and platform handoff preparation.
MSR MSP, r0
BX  r1
```

This fragment deliberately avoids compiler-generated stack accesses after MSP changes. It is not a complete bootloader implementation. Handle CONTROL, PSP, PRIMASK, BASEPRI, cache and security-state requirements as applicable. An application must know whether it must explicitly enable interrupts after the handoff.

#### 4. Alternative

Some systems request a hardware reset after recording the desired boot slot, allowing normal reset initialization to establish a cleaner environment.

**Interview takeaway:** The final branch is only one step. Correct image validation, vector configuration, interrupt/peripheral cleanup and stack/processor state are essential.

### What is MISRA C? {E}
MISRA C is a set of coding guidelines for developing reliable, maintainable and portable C software, especially in safety-related embedded applications. It restricts or controls language constructs that are difficult to analyze or prone to errors.

#### 1. Why MISRA C is used

C allows unchecked pointers, implicit conversions and operations with undefined or implementation-defined behavior. These are particularly problematic in automotive, industrial and other safety-related firmware.

#### 2. Example: explicit range checking

```c
bool store_value(int32_t input, uint8_t *out)
{
    if ((out == NULL) || (input < 0) || (input > 255)) {
        return false;
    }

    *out = (uint8_t)input;
    return true;
}
```

The code makes its range assumptions explicit before narrowing. It illustrates the reasoning behind safer coding guidelines, not a claim of complete MISRA compliance.

#### 3. How compliance is established

1. Identify the applicable MISRA C edition and project requirements.
2. Configure compiler warnings and static analysis.
3. Review findings, including rules that require manual examination.
4. Document justified deviations using the project's approved process.
5. Verify compliance as code changes.

#### 4. MISRA vs functional safety

MISRA guides source-code practices. Functional safety standards such as ISO 26262 address broader lifecycle activities, hazard analysis and safety verification. Passing a MISRA checker is not proof that software is safe or bug-free.

**Interview takeaway:** MISRA C reduces language-related risks through defined coding rules and a documented compliance process; it is not a compiler mode or a substitute for testing.

### What are a HAL and a BSP, and how do they differ? {M}
A Hardware Abstraction Layer (HAL) provides interfaces for operating hardware peripherals. A Board Support Package (BSP) contains the board-specific software and configuration needed to run firmware or an operating system on a particular board.

#### 1. HAL example

```c
HAL_GPIO_WritePin(GPIOA, GPIO_PIN_5, GPIO_PIN_SET);
```

On STM32 targets using the relevant HAL, this invokes the GPIO abstraction instead of manually programming the output register.

#### 2. BSP example

```c
void board_led_on(void)
{
    HAL_GPIO_WritePin(LED_PORT, LED_PIN, GPIO_PIN_SET);
}
```

LED_PORT and LED_PIN are selected by board configuration. A different board can provide another implementation without changing the application interface.

<div style="max-width:620px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 244" width="100%" role="img" aria-label="Application calls board interface, which uses HAL or drivers to access hardware">
<rect x="20" y="5" width="300" height="44" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="22" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">Application</text><text x="170" y="37" text-anchor="middle" font-size="10" fill="currentColor">board_led_on()</text><path d="M170 49 v16 m-4-5 4 5 4-5" stroke="currentColor" fill="none"/><rect x="20" y="65" width="300" height="44" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="82" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">BSP / board configuration</text><text x="170" y="97" text-anchor="middle" font-size="10" fill="currentColor">Select pin, clocks and board resources</text><path d="M170 109 v16 m-4-5 4 5 4-5" stroke="currentColor" fill="none"/><rect x="20" y="125" width="300" height="44" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="142" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">HAL / peripheral driver</text><text x="170" y="157" text-anchor="middle" font-size="10" fill="currentColor">Configure and operate GPIO</text><path d="M170 169 v16 m-4-5 4 5 4-5" stroke="currentColor" fill="none"/><rect x="20" y="185" width="300" height="44" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="202" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">Hardware</text><text x="170" y="217" text-anchor="middle" font-size="10" fill="currentColor">GPIO controller and LED</text></svg></div>

#### 3. Linux BSP

An embedded Linux BSP may contain bootloader configuration, kernel drivers, device trees, firmware, board-specific patches and build metadata. It integrates the software stack for the target board.

| HAL | BSP |
|---|---|
| Abstracts hardware operations | Integrates board-specific resources |
| Often reusable across a chip family | Usually customized for a board |
| GPIO, UART, SPI interfaces | Pin configuration, memory, boot and drivers |

Terminology and layering differ between vendors; a BSP can include a HAL.

**Interview takeaway:** HAL abstracts how peripherals operate; BSP describes and enables the specific board on which they operate.

### What is AUTOSAR and what are its main layers? {M}
AUTOSAR (AUTomotive Open System ARchitecture) defines standardized automotive software architecture and interfaces. It helps separate application functionality from ECU hardware and software infrastructure.

#### 1. Classic AUTOSAR

<div style="max-width:620px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 242" width="100%" role="img" aria-label="Simplified Classic AUTOSAR layers: application software components, RTE, basic software including MCAL, and MCU">
<rect x="20" y="5" width="300" height="44" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="22" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">Application SWCs</text><text x="170" y="37" text-anchor="middle" font-size="10" fill="currentColor">Control and application functions</text><path d="M170 49 v16 m-4-5 4 5 4-5" stroke="currentColor" fill="none"/><rect x="20" y="65" width="300" height="44" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="82" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">RTE</text><text x="170" y="97" text-anchor="middle" font-size="10" fill="currentColor">Runtime Environment: communication interfaces</text><path d="M170 109 v16 m-4-5 4 5 4-5" stroke="currentColor" fill="none"/><rect x="20" y="125" width="300" height="44" rx="5" fill="#16a34a" fill-opacity=".12" stroke="#16a34a"/><text x="170" y="142" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">Basic Software (BSW)</text><text x="170" y="157" text-anchor="middle" font-size="10" fill="currentColor">Services, ECU abstraction and MCAL</text><path d="M170 169 v16 m-4-5 4 5 4-5" stroke="currentColor" fill="none"/><rect x="20" y="185" width="300" height="44" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="202" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">Microcontroller</text><text x="170" y="217" text-anchor="middle" font-size="10" fill="currentColor">CPU, CAN, ADC, GPIO and peripherals</text></svg></div>

- Application software components implement vehicle functions.
- The RTE connects software components and basic software through configured interfaces.
- BSW provides OS, communication, diagnostics, memory services and hardware abstraction.
- MCAL contains standardized low-level microcontroller drivers.

Complex drivers may use specialized interfaces where ordinary abstraction is insufficient.

#### 2. Example

A sensor-processing application receives a value through an RTE interface. The underlying basic software and configured driver access the ADC or communication bus. The application need not directly program hardware registers.

#### 3. Classic vs Adaptive

| Classic | Adaptive |
|---|---|
| Typically resource-constrained MCUs | Higher-performance computing platforms |
| Statically configured components | Service-oriented applications |
| Real-time control ECUs | Complex computing and connected functions |

Adaptive uses its own architecture and is not simply the Classic RTE/MCAL stack on a faster processor.

**Interview takeaway:** AUTOSAR standardizes interfaces to make automotive software integration and reuse easier. Classic focuses on traditional ECU control; Adaptive targets more complex computing workloads.

### What does a typical SoC look like inside? {M}
A System on Chip (SoC) integrates processors, memory interfaces, interconnects and hardware accelerators/peripherals on one integrated circuit.

#### 1. Typical SoC architecture

<div style="max-width:720px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 244" width="100%" role="img" aria-label="CPU caches, DMA and accelerators connect through SoC interconnect to DDR controller and peripherals">
<rect x="5" y="5" width="105" height="47" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="57.5" y="23" text-anchor="middle" font-size="11" font-weight="600" fill="currentColor">CPU cluster</text><text x="57.5" y="38" text-anchor="middle" font-size="10" fill="currentColor">L1 / L2 cache</text><rect x="117" y="5" width="105" height="47" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="169.5" y="23" text-anchor="middle" font-size="11" font-weight="600" fill="currentColor">DMA engine</text><text x="169.5" y="38" text-anchor="middle" font-size="10" fill="currentColor">Transfers</text><rect x="229" y="5" width="105" height="47" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="281.5" y="23" text-anchor="middle" font-size="11" font-weight="600" fill="currentColor">Accelerators</text><text x="281.5" y="38" text-anchor="middle" font-size="10" fill="currentColor">GPU / display</text><rect x="5" y="154" width="105" height="47" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="57.5" y="172" text-anchor="middle" font-size="11" font-weight="600" fill="currentColor">DDR controller</text><text x="57.5" y="187" text-anchor="middle" font-size="10" fill="currentColor">External DRAM</text><rect x="117" y="154" width="105" height="47" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="169.5" y="172" text-anchor="middle" font-size="11" font-weight="600" fill="currentColor">Peripheral bus</text><text x="169.5" y="187" text-anchor="middle" font-size="10" fill="currentColor">UART / I2C / SPI</text><rect x="229" y="154" width="105" height="47" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="281.5" y="172" text-anchor="middle" font-size="11" font-weight="600" fill="currentColor">On-chip SRAM</text><text x="281.5" y="187" text-anchor="middle" font-size="10" fill="currentColor">ROM / SRAM</text><rect x="5" y="85" width="329" height="38" rx="5" fill="#eab308" fill-opacity=".13" stroke="#ca8a04"/><text x="170" y="108" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">System interconnect / address routing</text><path d="M57.5 52 V85 M57.5 123 V154" stroke="currentColor" fill="none"/><path d="M169.5 52 V85 M169.5 123 V154" stroke="currentColor" fill="none"/><path d="M281.5 52 V85 M281.5 123 V154" stroke="currentColor" fill="none"/><text x="170" y="222" font-size="10" text-anchor="middle" fill="currentColor">Interrupt, clock, reset, power and security controllers</text></svg></div>

#### 2. Example: display controller reads a framebuffer

1. CPU or GPU prepares pixel data in memory.
2. The display controller issues memory transactions over the interconnect.
3. The memory controller or coherent hierarchy supplies data.
4. The display engine processes pixels and sends them toward the panel.

If an IOMMU is present, device-visible addresses may require translation. Cache synchronization and memory ordering depend on the coherency architecture.

#### 3. Important software interfaces

- MMIO address ranges for device registers.
- Interrupt routing and priorities.
- Clocks, reset lines, regulators and power domains.
- CPU and device address translation and coherency domains.

Firmware or an OS BSP describes and initializes these resources.

**Interview takeaway:** An SoC is a collection of cooperating hardware masters and slaves, not just a CPU. Drivers must understand the device's memory, clock, interrupt and power dependencies.

### Which compiler optimisations can change how your C code behaves? {H}
Compiler optimizations transform a program while preserving its defined observable behavior under the language and implementation rules. Firmware bugs can become visible when optimization exposes incorrect assumptions.

#### 1. Common optimizations

| Optimization | Effect |
|---|---|
| Dead-code elimination | Removes unused computations |
| Inlining | Replaces a call with its body where suitable |
| Constant propagation | Uses known values during compilation |
| Loop transformations | Changes iteration or instruction structure |
| Load/store optimization | Reuses or reorders accesses when permitted |

#### 2. Example: polling a hardware register

```c
uint32_t *status = (uint32_t *)0x40000000U;
while ((*status & 1U) == 0) {}
```

Ordinary C accesses do not communicate the register's external hardware changes. A compiler may transform the loop in a way that does not poll the device as intended.

Use the appropriate MMIO access:

```c
volatile uint32_t *status =
    (volatile uint32_t *)0x40000000U;

while ((*status & 1U) == 0) {
    // Add a timeout in production.
}
```

This assumes a valid bare-metal register mapping and width.

#### 3. Undefined behavior and optimization

```c
int test(int x)
{
    return x + 1 > x;
}
```

A compiler may return 1 unconditionally because signed overflow is undefined. It need not preserve a wraparound assumption for INT_MAX.

#### 4. Debugging optimized firmware

Compare generated assembly, enable warnings and static analysis, use sanitizers on supported targets, and check volatile usage, aliasing, alignment, lifetime and synchronization. Debug builds and release builds may differ in timing and register allocation.

**Interview takeaway:** Optimization does not make invalid C correct. Fix the language or hardware-interface violation rather than permanently disabling optimization.

