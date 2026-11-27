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
**Short answer:** Intrinsics are functions provided by the compiler (or by headers such as CMSIS) that map directly to specific machine instructions: `__WFI()`, `__DSB()`, `__REV()`, `__CLZ()`, `__LDREXW()`, saturating and SIMD operations. The compiler understands them, so it can still optimise around them and check types. Use intrinsics whenever one exists; use inline assembly only for instructions or sequences that have no intrinsic.

**Common Cortex-M intrinsics (CMSIS)**

| Intrinsic | Instruction | Use |
|---|---|---|
| `__enable_irq()`, `__disable_irq()` | `CPSIE i`, `CPSID i` | critical sections |
| `__get_PRIMASK()`, `__set_BASEPRI()` | `MRS`/`MSR` | interrupt masking |
| `__WFI()`, `__WFE()`, `__SEV()` | `WFI`, `WFE`, `SEV` | sleep and event signalling |
| `__DMB()`, `__DSB()`, `__ISB()` | barriers | ordering |
| `__REV()`, `__REV16()`, `__RBIT()` | byte/bit reverse | endianness, CRCs |
| `__CLZ()` | count leading zeros | priority bitmaps, log2, normalisation |
| `__LDREXW()`, `__STREXW()`, `__CLREX()` | exclusive access | lock-free atomics |
| `__SSAT()`, `__USAT()` | saturate | DSP clipping |
| `__SADD16()`, `__SMLAD()`, `__QADD()` | DSP/SIMD (Cortex-M4/M7/M33) | fixed-point filters, CMSIS-DSP |

**GCC/Clang built-ins:** `__builtin_clz`, `__builtin_ctz`, `__builtin_popcount`, `__builtin_bswap32`, `__builtin_expect` (branch hints), `__builtin_unreachable`, and `__atomic_*`/`__sync_*` for atomics. Arm's **ACLE** (`<arm_acle.h>`) and **Neon/Helium** intrinsics (`<arm_neon.h>`, `<arm_mve.h>`) give SIMD operations on Cortex-A and Cortex-M55/M85.

**Why intrinsics beat inline assembly**

- The compiler knows exactly what the instruction reads, writes and clobbers, so it allocates registers and schedules code around it.
- Portable across compilers that implement CMSIS/ACLE (GCC, Clang, Arm Compiler, IAR).
- Type-checked, readable, and they do not block optimisation of the surrounding function.

**When you still need inline assembly:** special register access with no wrapper, exact instruction sequences (context switching, fault handler entry that must read the stack pointer before the compiler touches it), and timing-critical code. Use the extended GCC syntax with correct constraints and clobbers:

```c
static inline uint32_t get_ipsr(void)
{
    uint32_t r;
    __asm volatile ("mrs %0, ipsr" : "=r" (r));   /* output in any register */
    return r;
}
```

Write whole functions that need full control (PendSV context switch) as `__attribute__((naked))` or in a separate `.S` file.

### How do you implement a delay without blocking the CPU? {M}
**Short answer:** Use a free-running time base (e.g. a 1 ms SysTick counter or a hardware timer) and compare timestamps instead of spinning in a delay loop. Record the start time, return to the main loop, and check later whether the required time has elapsed. Use unsigned arithmetic `(now - start) >= interval` so the check keeps working when the counter wraps around.

```c
#include <stdbool.h>
#include <stdint.h>

static volatile uint32_t g_ms;              /* incremented in SysTick_Handler */
void SysTick_Handler(void) { g_ms++; }

static inline uint32_t millis(void) { return g_ms; }   /* 32-bit read is atomic on Cortex-M */

typedef struct { uint32_t start, interval; } soft_timer_t;

bool timer_expired(soft_timer_t *t)
{
    if ((uint32_t)(millis() - t->start) >= t->interval) {
        t->start += t->interval;            /* keeps a fixed period without drift */
        return true;
    }
    return false;
}

/* main loop */
soft_timer_t led = { 0, 500 };
for (;;) {
    if (timer_expired(&led)) toggle_led();
    poll_uart();                            /* other work keeps running */
}
```

**Why unsigned subtraction works across wrap-around:** if `start = 0xFFFFFFF0` and the counter wraps to `now = 0x00000010`, then `now - start` in 32-bit unsigned arithmetic is `0x20` = 32 ms, which is correct. The broken form `if (now >= start + 500)` fails because `start + 500` wraps to a small number and the condition becomes true immediately (or never). The difference must be compared, not the absolute times. A 32-bit millisecond counter wraps every 49.7 days, which is exactly when long-running devices fail with the broken form.

**Other non-blocking approaches**

- **Hardware timer interrupt or one-shot timer** that sets a flag or calls a callback.
- **State machines** where each state records when it was entered and moves on when a timeout passes.
- **RTOS:** `vTaskDelay()`/`vTaskDelayUntil()` block only the calling task; other tasks run (this is "blocking" for the task but not for the CPU).
- **Low power:** if nothing else needs doing, sleep (`__WFI()`) until the next timer interrupt instead of busy-polling.

**When short busy-wait delays are fine:** a few microseconds required by hardware (e.g. a 10 µs reset pulse) can use a cycle-counter loop (`DWT->CYCCNT` on Cortex-M3+), but not with a plain `for` loop, which the optimiser may delete and whose timing depends on clock speed and flash wait states.

### What is a super loop (foreground/background) architecture? {E}
**Short answer:** A super loop is the simplest firmware structure: `main()` initialises the hardware and then runs an infinite loop that calls each task function in turn. Interrupts (the **foreground**) handle time-critical events quickly and set flags or fill buffers; the loop (the **background**) does the processing. It needs no RTOS and is easy to understand, but the response time of every task depends on the total time of one pass of the loop.

```c
int main(void)
{
    clock_init();
    gpio_init();
    uart_init();
    adc_init();

    for (;;) {
        if (uart_rx_available()) handle_command();   /* each task must return quickly */
        if (adc_flag)            { adc_flag = false; filter_sample(); }
        update_display();
        kick_watchdog_if_healthy();
        __WFI();                                     /* sleep until the next interrupt */
    }
}
```

**Rules for making it work**

- Every task must be **non-blocking**: do a small amount of work and return; long operations become state machines.
- ISRs do the minimum (capture data, set flags).
- Use timestamps for periodic work instead of delay loops.
- Measure the worst-case loop time; the worst-case response time of a task is about one full loop.

**Advantages:** tiny code size, no RTOS licensing or learning curve, fully deterministic order, easy to debug, no stack-per-task overhead.

**Disadvantages and when to move on**

- A slow task (writing to flash, a long calculation) delays all others.
- Priorities are only possible through ISRs or by reordering/skipping work.
- Complex timing requirements, many independent activities, or blocking protocol stacks (TCP/IP, USB, Bluetooth) become hard to manage.

**Next steps up:** a **cooperative scheduler** (time-triggered task table, each task run at its period), event-driven frameworks (active objects with event queues, e.g. QP), or a pre-emptive **RTOS** (FreeRTOS, Zephyr).

### How do you write a state machine in C? {M}
**Short answer:** Represent the states with an `enum`. Either use a **`switch` on the current state** inside a function that receives events (clear for small machines), or a **table** indexed by state and event that gives the next state and an action function (scales well and maps directly to a state diagram). Always handle unexpected events explicitly.

**1. Switch-based**

```c
typedef enum { ST_IDLE, ST_CONNECTING, ST_CONNECTED } state_t;
typedef enum { EV_START, EV_OK, EV_FAIL, EV_TIMEOUT } event_t;

static state_t state = ST_IDLE;

void fsm_dispatch(event_t ev)
{
    switch (state) {
    case ST_IDLE:
        if (ev == EV_START) { start_link(); state = ST_CONNECTING; }
        break;
    case ST_CONNECTING:
        if (ev == EV_OK)                          { notify_up(); state = ST_CONNECTED; }
        else if (ev == EV_FAIL || ev == EV_TIMEOUT) { log_fail();  state = ST_IDLE; }
        break;
    case ST_CONNECTED:
        if (ev == EV_FAIL) { notify_down(); state = ST_IDLE; }
        break;
    default:
        state = ST_IDLE;                          /* corrupted state: recover */
        break;
    }
}
```

**2. Table-driven**

```c
typedef struct { bool valid; state_t next; void (*action)(void); } trans_t;

static const trans_t table[3][4] = {                 /* [state][event] */
    [ST_IDLE]       = { [EV_START]   = { true, ST_CONNECTING, start_link } },
    [ST_CONNECTING] = { [EV_OK]      = { true, ST_CONNECTED, notify_up },
                        [EV_FAIL]    = { true, ST_IDLE, log_fail },
                        [EV_TIMEOUT] = { true, ST_IDLE, log_fail } },
    [ST_CONNECTED]  = { [EV_FAIL]    = { true, ST_IDLE, notify_down } },
};

void fsm_dispatch_table(event_t ev)
{
    const trans_t *t = &table[state][ev];
    if (!t->valid) {
        log_unexpected(state, ev);                   /* unhandled pair: log, ignore or fault */
        return;
    }
    if (t->action) t->action();
    state = t->next;
}
```

Entries not listed are zero-initialised, so `valid` is `false` for every unhandled (state, event) pair.

**3. State functions:** each state is a function returning the next state function; compact, and each state's logic is together.

**Good practice**

- Keep the table `const` (it lives in flash and cannot be corrupted).
- Events come from ISRs through a queue; the state machine runs in the main loop or a task, never inside the ISR.
- Use entry/exit actions for things like starting and stopping timers.
- Log state transitions; it makes field debugging much easier.
- For complex behaviour, use hierarchical state machines (UML statecharts; QP/C, or code generation from a diagram).

**Embedded examples:** protocol parsers (byte-by-byte frame decoding), connection managers, button handling (idle/pressed/long-press), power management, bootloader update flows.

### How do you design error handling in firmware? {M}
**Short answer:** Combine several layers: functions return explicit status codes that callers must check; `assert`-style checks catch programming errors during development; peripherals and communication have timeouts and retries; hardware faults (HardFault, bus errors) are caught by fault handlers that record diagnostic data; and the system has a defined recovery strategy (retry, degrade, safe state, reset) plus a watchdog as the last line of defence. Errors are logged so field failures can be analysed.

**1. Status codes**

```c
typedef enum {
    ERR_OK = 0, ERR_TIMEOUT, ERR_BUSY, ERR_CRC, ERR_PARAM, ERR_NO_MEM, ERR_HW
} err_t;

err_t sensor_read(int16_t *out) __attribute__((warn_unused_result));

err_t e = sensor_read(&t);
if (e != ERR_OK) { log_error(MOD_SENSOR, e); return e; }   /* propagate */
```

**2. Classify errors and choose a response**

| Class | Example | Response |
|---|---|---|
| Transient | I2C NACK, CRC error on a message | retry with a limit and back-off |
| Recoverable hardware | sensor not responding | re-initialise the peripheral, bus recovery, mark data invalid |
| Persistent | sensor dead, flash wear-out | degrade: use a default, disable the feature, report it |
| Programming error | NULL argument, impossible state | `assert` → fault handler → safe state/reset (do not continue with corrupted logic) |
| Fatal | stack overflow, HardFault | record context in `.noinit`, enter safe state, reset |

**3. Fault handlers:** implement `HardFault_Handler` (and MemManage/Bus/Usage faults) to save the stacked PC, LR, fault status registers (`CFSR`, `HFSR`, `MMFAR`, `BFAR`) into a `.noinit` area, put outputs into a safe state (motors off, valves closed), then reset. After reboot, read and report the record.

**4. Timeouts everywhere:** no `while (!(SR & FLAG));` without an escape; a missing hardware response should not hang the system.

**5. Safe state:** define what "safe" means for the product (e.g. heater off, actuators de-energised), and make sure every fatal path goes there quickly.

**6. Watchdog** for errors you did not anticipate, plus a reset counter to detect boot loops and switch to a recovery/safe mode.

**7. Logging and telemetry:** a small ring buffer of error codes with timestamps, kept in RAM (`.noinit`) or flash, readable over a debug interface or sent to the cloud.

**8. Defensive input handling:** validate all external input (message lengths, ranges, enum values); never trust data from the outside.

**What interviewers want to hear:** errors are expected and handled by design, not ignored; programming errors fail fast and loud in development; production devices recover on their own and leave evidence behind.

### What does the inline assembly __asm volatile("" ::: "memory") do? {H}
**Short answer:** It is a **compiler barrier**. The empty assembly statement with a `"memory"` clobber tells the compiler that the (empty) code might read or write any memory, so it must not move memory accesses across this point, must write out values it is holding in registers before it, and must reload values from memory after it. It emits **no instruction**, so it does not stop the CPU or the bus from reordering anything.

```c
#define compiler_barrier() __asm volatile ("" ::: "memory")

flag_data = compute();
compiler_barrier();        /* the store to flag_data is emitted before the store to ready */
ready = 1;
```

**What each part means**

- `__asm volatile`: do not delete or move this statement (volatile asm).
- `""`: no instructions.
- `::: "memory"`: the clobber list says "memory may have changed", which forces the compiler to forget cached values.

**Where it is used**

- The Linux kernel's `barrier()` is exactly this.
- Inside lock and critical-section macros, so that accesses to protected data are not moved outside the lock by the compiler (CMSIS `__disable_irq()` includes a memory clobber for the same reason).
- Benchmarking, to stop the compiler from optimising away or reordering the code being measured.
- Preventing the compiler from merging or removing memory accesses in tight polling loops on non-volatile data (better: use `volatile` or atomics).

**Compiler barrier vs hardware barrier**

| | Compiler barrier | Hardware barrier (`DMB`/`DSB`) |
|---|---|---|
| Prevents compiler reordering | yes | yes (CMSIS versions include a memory clobber) |
| Prevents CPU/bus reordering | no | yes |
| Instructions emitted | none | one |
| Enough for | single-core code vs interrupts, when the CPU itself does not reorder visibly | multi-core, DMA, write buffers, device memory |

**C11 equivalents:** `atomic_signal_fence(memory_order_seq_cst)` is a compiler-only fence (for code vs signal handlers/ISRs on the same core); `atomic_thread_fence()` is a full fence that also emits a hardware barrier.

### How do you make a firmware image position independent or relocatable? {H}
**Short answer:** Compile with position-independent options (`-fPIC`/`-fpie`, or on Cortex-M `-fropi`/`-frwpi` with Arm Compiler, or GCC's `-msingle-pic-base -mpic-register=r9 -mno-pic-data-is-text-relative` for separate data), so code uses PC-relative addressing and data is reached through a base register or a global offset table (GOT) that is fixed up at load time. In practice most MCU firmware is linked at a **fixed address**, and bootloaders support multiple images with fixed slots or by **swapping** images rather than relocating them.

**Why it is hard on MCUs**

- Function pointers, the vector table and any initialised pointer in `.data` contain absolute addresses that must be patched if the image moves.
- Without an MMU there is no virtual address trick to make the image appear at its link address.
- Position-independent code is slightly larger and slower (extra indirections through the GOT).

**Common strategies for firmware updates**

| Strategy | How | Trade-off |
|---|---|---|
| Fixed single slot + recovery bootloader | bootloader overwrites the app in place | no rollback if the update fails mid-way, unless the bootloader can always re-download |
| Two slots, image linked for slot A only, **swap** | MCUboot copies/swaps the new image from slot B into slot A (using a scratch area), with revert support | needs time and flash wear for the swap |
| Two slots, two builds | build the same firmware twice, linked for each slot; the bootloader runs whichever is valid | the update server must deliver the right build for the inactive slot |
| Execute-in-place from external flash with **address remapping** | some MCUs (e.g. with OTFDEC/remap registers, or nRF/ESP32 flash mapping/MMU) map either slot to the same execution address | needs hardware support |
| Real PIC | `-fpie` + loader fix-ups (as in Zephyr's LLEXT, or loadable modules) | complexity and size |

**What the bootloader must do for any non-default location:** set `SCB->VTOR` to the application's vector table, which must be suitably aligned, before jumping (next question).

### How does a bootloader jump to the application on Cortex-M? {H}
**Short answer:** The bootloader validates the application image (magic number, size, CRC or signature), puts the system back into a reset-like state (de-initialise peripherals and clocks it changed, disable and clear all interrupts, stop SysTick), sets `SCB->VTOR` to the application's vector table, loads the main stack pointer from the first word of that table, and branches to the reset handler whose address is in the second word.

```c
#include <stdint.h>
#include "stm32f4xx.h"              /* or the CMSIS header for your MCU */

#define APP_BASE 0x08008000u

static void jump_to_app(void) __attribute__((noreturn));
static void jump_to_app(void)
{
    const uint32_t *vt = (const uint32_t *)APP_BASE;
    uint32_t app_sp    = vt[0];
    uint32_t app_reset = vt[1];

    __disable_irq();
    SysTick->CTRL = 0;                               /* stop SysTick */
    for (unsigned i = 0; i < 8; i++) {               /* disable and clear every NVIC interrupt */
        NVIC->ICER[i] = 0xFFFFFFFFu;
        NVIC->ICPR[i] = 0xFFFFFFFFu;
    }
    /* HAL_RCC_DeInit(); deinit peripherals the bootloader used (UART, USB, DMA) */

    SCB->VTOR = APP_BASE;                            /* application's vector table */
    __DSB();
    __ISB();

    __set_MSP(app_sp);                               /* from here on, no stack use in C */
    __enable_irq();                                  /* the app expects interrupts enabled after reset (PRIMASK = 0) */
    ((void (*)(void))app_reset)();                   /* bit 0 of the address is already set (Thumb) */
    for (;;) { }
}
```

**Validation before jumping**

- Check that `app_sp` points into RAM and `app_reset` points into the application's flash region; an erased flash reads `0xFFFFFFFF`.
- Verify a CRC or a cryptographic signature over the image (secure boot).

**Details that cause real-world bugs**

- **Setting MSP from C:** after `__set_MSP`, any local variable stored on the old stack is invalid. Load the reset address into a register first (as above, it is computed before), or do the last steps in a small assembly function.
- **Interrupts left enabled or pending** from the bootloader fire in the application before it has set up their handlers.
- **Peripherals left running** (DMA writing into RAM the application now uses, a USB stack still attached) cause random corruption.
- **Clock configuration:** the application's `SystemInit` may assume reset clock settings; either restore them or make the application tolerant.
- **Privilege and stack selection:** if the bootloader used the PSP or unprivileged mode, restore `CONTROL` to 0.
- **VTOR alignment:** the application's vector table must be aligned as the core requires (e.g. 512 bytes on many parts).
- **Application linker script** must start at `APP_BASE`, not at the start of flash.

**A cleaner alternative** used by some bootloaders: write a "boot application" flag to a `.noinit` RAM location or backup register, trigger a system reset (`NVIC_SystemReset()`), and have the bootloader jump immediately at the start of its reset handler before initialising anything. Then the application starts from a true reset state.

### What is MISRA C? {E}
**Short answer:** MISRA C is a set of coding guidelines for writing safe, secure, portable and reliable C in critical systems. It was created for the automotive industry by the Motor Industry Software Reliability Association, and is now used in aerospace, medical, railway and industrial devices. Rules restrict language features that commonly cause undefined behaviour or bugs, such as unchecked dynamic memory, recursion, unrestricted `goto`, implicit conversions between "essential types", and unions used for type punning. Compliance is checked with static analysis tools.

**Structure**

- **Directives** (process-level, partly not checkable by tools, e.g. "all code shall be traceable to requirements") and **rules** (checkable on the source).
- Each is **Mandatory** (no deviations allowed), **Required** (deviations need a documented, approved justification), or **Advisory**.
- **Decidable** vs **undecidable** rules: some can always be checked by a tool, others only partly.

**Example rules (paraphrased)**

- No dynamic memory allocation from the heap (Rule 21.3).
- Functions shall not call themselves, directly or indirectly (Rule 17.2).
- The value of an expression shall not be assigned to an object with a narrower essential type (Rule 10.3).
- A `switch` statement shall have a `default` label (Rule 16.4).
- The return value of a non-void function shall be used (Rule 17.7).
- No implicit conversion of a signed value to unsigned in arithmetic (essential type model).
- Octal constants shall not be used (`010` is 8, a common mistake).

**Editions:** MISRA C:1998, :2004, :2012 (with amendments adding security rules and C11 support), and the consolidated **MISRA C:2023** (adds C11/C18 coverage, including threads and atomics). **MISRA C++:2023** covers modern C++.

**Tools:** PC-lint Plus, Polyspace, Coverity, Parasoft C/C++test, Helix QAC, LDRA, Klocwork, cppcheck's MISRA addon (partial), and compiler-integrated checkers (IAR C-STAT, Arm, Green Hills).

**How it is used in practice:** projects agree a "compliance plan" (which rules apply), integrate the checker into CI, document deviations with justifications, and record compliance evidence for standards such as **ISO 26262** (automotive), **IEC 61508** (industrial), **IEC 62304** (medical) and **DO-178C** (avionics). Related standards: **CERT C** (security-focused) and **AUTOSAR C++14** guidelines.

### What are a HAL and a BSP, and how do they differ? {M}
Both are layers that keep application code independent of the hardware, but at different levels.

- A **HAL (hardware abstraction layer)** gives a uniform API for a *type* of peripheral (`uart_write()`, `gpio_set()`, `spi_transfer()`), hiding the registers of one chip family. Vendor examples are STM32 HAL/LL, NXP MCUXpresso SDK drivers and TI DriverLib; CMSIS-Driver standardises the API across vendors.
- A **BSP (board support package)** adapts software to a *specific board*: which pins connect to which device, clock and memory setup, external chips (PMIC, flash, sensors), and the start-up code. In embedded Linux, the BSP is the bootloader, kernel configuration and device tree for that board.

| | HAL | BSP |
|---|---|---|
| Abstracts | A peripheral or chip family | A whole board |
| Changes when | You switch MCU family | You change the board design |
| Example | `uart_init(&cfg)` | "Debug UART is USART2 on PA2/PA3; sensor on I2C1 at 0x48" |

A good layering is: application → services/middleware → BSP → HAL → registers. Interviewers often follow up with how you would port firmware to a new MCU: you rewrite or replace the HAL and update the BSP, and the application should not change.

### What is AUTOSAR and what are its main layers? {M}
AUTOSAR (AUTomotive Open System ARchitecture) is a standard software architecture for automotive ECUs, so software components can be reused across suppliers and hardware. **Classic Platform** targets deeply embedded ECUs on microcontrollers with static configuration; **Adaptive Platform** targets high-performance ECUs running POSIX operating systems with service-oriented communication.

The Classic Platform layers, from top to bottom:

1. **Application layer:** software components (SWCs) containing the vehicle functions, with ports for data and services.
2. **RTE (Runtime Environment):** generated middleware that connects SWCs to each other and to the basic software, so components never call hardware directly.
3. **BSW (Basic Software):**
   - **Services layer:** OS (OSEK-based AUTOSAR OS), communication stack (COM, PduR, CanIf), diagnostics (DCM, DEM), memory services (NvM), watchdog manager.
   - **ECU abstraction layer:** makes on-board devices accessible regardless of how they connect to the MCU.
   - **MCAL (Microcontroller Abstraction Layer):** drivers for on-chip peripherals: CAN, ADC, DIO, PWM, SPI, flash, GPT.
   - **Complex device drivers:** an escape path for timing-critical hardware access that doesn't fit the layers.

Everything is configured with tools (ARXML files) and code is largely generated. Interview follow-ups usually cover how a CAN signal travels from the bus to an application SWC (CAN driver → CanIf → PduR → COM → RTE → SWC) and how diagnostics (UDS over DCM) work.

### What does a typical SoC look like inside? {M}
A system-on-chip puts a complete computer on one die. A typical application-processor SoC (phone, automotive, IoT gateway) contains:

- **CPU cluster(s):** several Arm Cortex-A cores, often in big.LITTLE groups, with private L1 caches and a shared L2/L3.
- **Accelerators:** GPU, DSP, NPU for machine learning, video encoder and decoder, ISP for cameras, display controller.
- **Microcontroller cores:** Cortex-M or Cortex-R cores for power management, security, sensors or real-time control.
- **Memory system:** DDR/LPDDR controller, on-chip SRAM, boot ROM, and an MMU/SMMU (IOMMU) so devices can use virtual addresses.
- **Interconnect:** a bus fabric (AMBA AXI/ACE/CHI, with AHB/APB for slow peripherals) linking everything, with cache coherency between CPUs and some devices.
- **Peripherals:** UART, SPI, I2C, GPIO, timers, USB, PCIe, Ethernet, SD/eMMC/UFS, MIPI DSI and CSI.
- **System control:** clock and reset controllers, power domains, PMIC interface, interrupt controller (GIC), watchdog, thermal sensors.
- **Security:** crypto engines, true random number generator, secure enclave or TrustZone, eFuses for keys and secure boot.

Interviewers usually ask you to draw this and then trace one flow, for example how a camera frame reaches the display, or what happens from power-on to the kernel running.

### Which compiler optimisations can change how your C code behaves? {H}
An optimiser may transform code in any way that keeps the *observable behaviour* defined by the C standard. Code that relies on undefined behaviour, or that forgets to tell the compiler about hardware, can change behaviour between `-O0` and `-O2`. The common ones:

- **Caching values in registers / removing loads:** a polled flag or register read once and never again. Fix with `volatile`.
- **Dead-store elimination:** writes the compiler thinks nobody reads are removed, such as clearing a key buffer before `free` or writing a register twice. Fix with `volatile` or `explicit_bzero`/`memset_s`.
- **Reordering:** independent loads and stores may be moved, including across a write to a "data ready" flag. Fix with barriers or atomics.
- **Assuming no undefined behaviour:** signed overflow cannot happen (so `x + 1 > x` becomes `true`), a dereferenced pointer cannot be NULL (so a later NULL check is deleted), shifts are smaller than the type width.
- **Strict aliasing:** the compiler assumes an `int *` and a `float *` never point to the same memory, so type-punning through pointer casts can read stale values.
- **Loop transformations:** empty delay loops are removed entirely; loops become `memcpy`/`memset` calls (a problem inside your own `memcpy` or before `.data` is initialised).
- **Inlining and constant folding:** can change timing and stack usage, and hide functions from the debugger.

The interview point is that the optimiser is not buggy; the code relied on something the language does not promise. Use `volatile` for hardware, atomics and barriers for concurrency, `memcpy` for type punning, and compiler warnings and sanitizers (`-Wall -Wextra`, UBSan) to find undefined behaviour.
