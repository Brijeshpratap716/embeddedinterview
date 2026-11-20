---
slug: embedded-c
title: Embedded C
icon: ⚙️
level: Intermediate
order: 3
desc: volatile, ISRs, registers, critical sections, start-up code, linker scripts and writing firmware that survives real hardware.
---
Embedded C is ordinary C plus the rules that come from sharing memory with hardware and interrupts. These are the questions that decide most firmware interviews.

### What is volatile and when must you use it? {E}
`volatile` tells the compiler that a variable can change, or that accessing it has side effects, in ways the compiler cannot see. Every read and write in the source must then actually be performed, in program order relative to other volatile accesses.

Use it for:
1. **Memory-mapped peripheral registers**.
2. **Variables shared between an ISR and main code**.
3. **Variables shared between threads** on systems without proper atomics (and only together with other measures).
4. Variables modified by DMA, or locals that must survive a `longjmp`.

```c
volatile bool g_rx_ready;          /* set in ISR */

while (!g_rx_ready) { }            /* without volatile this can become while(1) */
```

### Does volatile make a variable thread-safe or atomic? {M}
No. `volatile` only stops the compiler caching or removing accesses. It does not:

- make a read-modify-write such as `count++` atomic (that is a load, add and store),
- make a 64-bit access atomic on a 32-bit CPU,
- stop the CPU or other cores reordering memory accesses (no memory barrier).

For data shared with an ISR you need a critical section or atomic instructions. For threads, use C11 `<stdatomic.h>`, RTOS primitives, or kernel locks.

### Can a pointer be volatile? Explain the declarations. {M}
- `volatile int *p`: pointer to a volatile int. The **pointed-to data** changes unexpectedly. This is the normal case for registers.
- `int *volatile p`: volatile pointer to a normal int. The **pointer itself** may be changed by an ISR.
- `volatile int *volatile p`: both.

### What is an ISR and what are the rules for writing one? {E}
An Interrupt Service Routine is the function the CPU runs when an interrupt fires. Rules:

- Keep it **short**: acknowledge the source, move data, set a flag or give a semaphore, and return. Do the heavy work in a task or main loop.
- **No blocking**: no `delay`, no waiting on a mutex, no `printf` (non-reentrant, slow).
- **No `malloc`/`free`**: not reentrant, not deterministic.
- **Clear the interrupt flag**, or it will fire again immediately.
- Share data through `volatile` variables protected by critical sections, or lock-free queues.
- An ISR takes no arguments and returns nothing.
- Floating-point in an ISR costs extra stacking time on Cortex-M4F (lazy stacking helps).

### Can you pass parameters to or return a value from an ISR? {E}
No. The hardware calls the ISR asynchronously; there is no caller to supply arguments or receive a return value. Data is exchanged through shared global or static variables, queues or ring buffers. On Cortex-M, ISRs are ordinary `void f(void)` C functions because the hardware stacks the caller-saved registers automatically.

### What is interrupt latency and how do you reduce it? {M}
Interrupt latency is the time from the interrupt signal being asserted to the first instruction of the ISR executing. On Cortex-M3/M4 the hardware minimum is 12 cycles with zero-wait-state memory.

What makes it worse:
- Code running with interrupts globally disabled (long critical sections).
- A higher-priority ISR already running.
- Flash wait states and cache misses on the vector fetch.
- Saving FPU context.

Reduce it by keeping critical sections short, using priority masking (`BASEPRI`) instead of disabling everything, placing hot ISRs and the vector table in RAM or TCM, and assigning correct priorities. See the article *Interrupt latency explained*.

### What is a critical section and how do you implement one on bare metal? {M}
A critical section is a piece of code that must run without being interrupted by anything that touches the same data.

```c
static inline uint32_t irq_save(void)
{
    uint32_t primask = __get_PRIMASK();
    __disable_irq();
    return primask;
}
static inline void irq_restore(uint32_t primask) { __set_PRIMASK(primask); }

uint32_t s = irq_save();
shared_counter++;
irq_restore(s);
```

Saving and restoring `PRIMASK` (instead of always re-enabling) makes the section safe to nest. On Cortex-M3+ you can mask only lower-priority interrupts with `BASEPRI`, so urgent interrupts still run.

### What is a reentrant function? {M}
A function is reentrant if it can be interrupted partway and safely called again (from an ISR or another thread) before the first call finishes. Requirements:

- No modification of static or global data without protection.
- No returning pointers to static buffers.
- Only calls other reentrant functions.
- Works only on its arguments and local variables.

`strtok`, classic `rand` and most `printf` implementations are not reentrant. `strtok_r` is the reentrant version.

### What is the difference between reentrant and thread-safe? {H}
A **thread-safe** function can be called from multiple threads at once, which it may achieve with a mutex. A **reentrant** function can be interrupted and re-entered *on the same thread*, such as from a signal handler or ISR. A function using a mutex is thread-safe but not reentrant: if an ISR interrupts it while the mutex is held and calls it again, it deadlocks. Reentrant functions are usually thread-safe too, provided they do not share data.

### How do you set, clear, toggle and test a bit in a register? {E}
```c
reg |=  (1u << n);          /* set   */
reg &= ~(1u << n);          /* clear */
reg ^=  (1u << n);          /* toggle */
if (reg & (1u << n)) { }    /* test  */
```

Use `1u`, not `1`, so that `1 << 31` is not signed overflow. For multi-bit fields: `reg = (reg & ~MASK) | ((val << SHIFT) & MASK);`.

### Why can a read-modify-write on a register be dangerous? {H}
`REG |= BIT;` is three steps: read, OR, write. Problems:

1. **Interrupt race**: an ISR that modifies the same register between the read and the write has its change overwritten.
2. **Write-1-to-clear bits**: if the register has status bits cleared by writing 1, reading them as 1 and writing back clears flags you did not mean to clear.
3. **Read side effects**: some registers clear on read (such as a UART data register), so the read itself loses data.

Solutions: use the hardware's atomic set/reset registers (STM32 `GPIOx->BSRR`, `BRR`), Cortex-M3/M4 bit-banding, a critical section, or `LDREX/STREX`.

### What is bit-banding on Cortex-M? {H}
On Cortex-M3 and M4, bit-banding maps every bit of the first 1 MB of SRAM (`0x20000000`) and of the peripheral region (`0x40000000`) to its own 32-bit word in an alias region. Writing 0 or 1 to the alias word changes exactly that one bit, atomically, in a single bus transaction.

```
alias = alias_base + (byte_offset * 32) + (bit_number * 4)
```

It is not present on Cortex-M0/M0+, M7 or M33, so portable code avoids relying on it.

### What happens before main() runs on a microcontroller? {M}
1. On reset the core loads the **initial stack pointer** from vector table entry 0 and the **reset handler** address from entry 1.
2. The reset handler (in start-up assembly or C) runs:
   - optionally `SystemInit()` to configure clocks, flash wait states and the FPU,
   - copies `.data` initial values from flash to RAM,
   - zeroes `.bss`,
   - runs C++ static constructors / `__libc_init_array` if used,
   - calls `main()`.
3. If `main` returns, the handler usually loops forever.

See the coding problem *Write the reset handler*.

### What is a linker script and what does it contain? {M}
A linker script tells the linker where memory is and where each section goes. A minimal one has:

- `MEMORY` regions: e.g. `FLASH (rx) : ORIGIN = 0x08000000, LENGTH = 512K` and `RAM (rwx) : ORIGIN = 0x20000000, LENGTH = 128K`.
- `SECTIONS`: `.isr_vector` and `.text`/`.rodata` into FLASH; `.data` into RAM with a load address in FLASH (`> RAM AT> FLASH`); `.bss` into RAM.
- Symbols used by start-up code: `_sidata`, `_sdata`, `_edata`, `_sbss`, `_ebss`, `_estack`.

You edit it to place code in RAM, reserve a no-init region that survives reset, put a bootloader at the start of flash, or move the application.

### What is the vector table? {E}
An array of addresses at a known location (address 0 on Cortex-M by default, movable with `SCB->VTOR`). Entry 0 is the initial main stack pointer, entry 1 the reset handler, then the system exceptions (NMI, HardFault, MemManage, BusFault, UsageFault, SVCall, PendSV, SysTick) and then one entry per peripheral interrupt. Weak default handlers let you override any of them by defining a function with the same name.

### What are weak symbols? {M}
A weak symbol is a definition that the linker uses only if no strong definition with the same name exists:

```c
void __attribute__((weak)) USART1_IRQHandler(void) { Default_Handler(); }
```

Start-up files define every ISR as a weak alias of a default handler. When you write `void USART1_IRQHandler(void)` in your code, yours wins. A common bug is misspelling the handler name: the weak default stays, and the board hangs in `Default_Handler` when the interrupt fires.

### How do you place a variable or function at a specific address or section? {M}
Use a section attribute and map that section in the linker script:

```c
__attribute__((section(".ramfunc"))) void flash_erase(void) { /* runs from RAM */ }
__attribute__((section(".noinit")))  uint32_t reset_reason;
```

Code that erases or programs flash often has to run from RAM because flash cannot be read while it is being written. A `.noinit` section is excluded from start-up zeroing so values survive a warm reset.

### What is a watchdog timer and how should you use it? {E}
A watchdog is a hardware timer that resets the MCU unless software "kicks" it before it expires. It recovers the system from hangs and runaway code.

Good practice:
- Kick it from one place, after checking that all critical tasks have reported they are alive, not blindly from a timer ISR (which keeps running even when the main loop is stuck).
- Use a windowed watchdog where a kick that is too early also counts as a failure.
- Record the reset cause at boot so field failures are visible.
- Make sure it keeps running in low-power modes if needed.

### What is debouncing and how do you implement it? {E}
Mechanical switches bounce, producing several transitions over a few milliseconds. Software debouncing accepts a new state only once it has been stable for a period:

```c
/* call every 1 ms */
void button_poll(void)
{
    static uint8_t history;
    history = (uint8_t)(history << 1) | read_pin();
    if (history == 0xFF) pressed = true;     /* stable high for 8 ms */
    else if (history == 0x00) pressed = false;
}
```

Hardware alternatives: an RC filter with a Schmitt-trigger input. Avoid edge interrupts for raw switches without filtering; the bounce generates bursts of interrupts.

### What is polling versus interrupts versus DMA? {E}
- **Polling**: the CPU repeatedly checks a status flag. Simple and predictable, wastes CPU and power.
- **Interrupts**: the peripheral signals the CPU when something happens. Efficient for sporadic events, but each byte costs an ISR entry at high data rates.
- **DMA**: a DMA controller moves data between peripheral and memory without the CPU, interrupting only at half/full transfer. Best for high-throughput streams like ADC sampling, audio, SPI displays and UART receive.

### What are the cache coherency problems with DMA? {H}
On cores with a data cache (Cortex-M7, Cortex-A), the CPU and DMA can see different data:

- **CPU writes, DMA reads (TX)**: data may still be in the cache. **Clean** (write back) the buffer's cache lines before starting DMA.
- **DMA writes, CPU reads (RX)**: the cache may hold stale data. **Invalidate** the lines after the transfer completes, before reading.
- Buffers must be aligned to and sized in multiples of the cache line (32 bytes on M7), otherwise invalidation can destroy neighbouring data.

Alternatives: put DMA buffers in a non-cacheable MPU region or DTCM. Linux drivers use the DMA API (`dma_map_single`, `dma_alloc_coherent`) for the same reason.

### What is a memory barrier and why would firmware need one? {H}
A barrier forces ordering of memory operations that the CPU or bus would otherwise reorder. On ARM:

- `DMB` (data memory barrier): earlier memory accesses complete before later ones.
- `DSB` (data synchronisation barrier): all accesses complete before *any* later instruction runs.
- `ISB` (instruction synchronisation barrier): flushes the pipeline so later instructions see the new context.

Examples: a `DSB` after clearing an interrupt flag at the end of an ISR so the write lands before the ISR returns (otherwise the interrupt can re-trigger); `DSB` + `ISB` after changing `VTOR`, MPU settings or `CONTROL`. `volatile` does not emit barriers.

### How do you implement a delay without blocking the CPU? {M}
Use a free-running tick (SysTick at 1 ms, for example) and compare timestamps, keeping the arithmetic unsigned so wrap-around works:

```c
uint32_t start = g_ticks;
/* later, in the main loop */
if ((uint32_t)(g_ticks - start) >= 500u) {
    start += 500u;
    toggle_led();
}
```

Subtracting unsigned values gives the correct elapsed time even after `g_ticks` overflows. Never compare `g_ticks >= start + 500`, which breaks at wrap-around.

### What is a super loop (foreground/background) architecture? {E}
The simplest firmware structure: `main()` initialises hardware and then runs an infinite loop that calls each task function in turn. Interrupts (the foreground) capture time-critical events and set flags; the loop (background) processes them. It is easy to reason about and needs no RTOS, but the response time of any task depends on the total time of the whole loop. Once timing requirements or task count grow, move to a scheduler or RTOS.

### How do you write a state machine in C? {M}
The two common approaches:

1. **switch on state** inside a function called with each event. Clear for small machines.
2. **Table-driven**: a 2-D table indexed by `[state][event]` holding the next state and an action function pointer. Scales well, easy to review against a diagram.

```c
typedef enum { IDLE, CONNECTING, CONNECTED, ST_COUNT } state_t;
typedef enum { EV_START, EV_OK, EV_FAIL, EV_COUNT } event_t;
typedef struct { state_t next; void (*action)(void); } trans_t;

static const trans_t table[ST_COUNT][EV_COUNT] = {
    [IDLE]       = { [EV_START] = { CONNECTING, start_link } },
    [CONNECTING] = { [EV_OK] = { CONNECTED, notify_up }, [EV_FAIL] = { IDLE, log_fail } },
};
```

Handle "impossible" event/state pairs explicitly instead of ignoring them.

### What does the inline assembly __asm volatile("" ::: "memory") do? {H}
It is a **compiler barrier**: the empty assembly with a `"memory"` clobber tells the compiler that memory may have changed, so it must not move memory accesses across this point and must reload values afterwards. It emits no instruction, so it does not stop the CPU reordering. The Linux kernel's `barrier()` is exactly this. Use a real barrier (`__DMB()`) when hardware ordering matters.

### How do you make a firmware image position independent or relocatable? {H}
Compile with `-fPIC`/`-fpie` (or ARM `-mpic-data-is-text-relative`) so code uses PC-relative addressing, and have the loader fix the global offset table at run time. Most MCU firmware instead links at a fixed address. Bootloader designs usually reserve two fixed slots, link one image per slot or use a "swap" scheme (as MCUboot does), and set `VTOR` to the application's vector table before jumping to it.

### How does a bootloader jump to the application on Cortex-M? {H}
1. Check the application is valid (magic value, CRC or signature).
2. De-initialise peripherals and disable interrupts, including SysTick; clear pending IRQs.
3. Set `SCB->VTOR` to the application's vector table address.
4. Load the main stack pointer from the first word of that table (`__set_MSP`).
5. Jump to the address in the second word (the application's reset handler).

```c
uint32_t *app = (uint32_t *)APP_BASE;
SCB->VTOR = APP_BASE;
__set_MSP(app[0]);
((void (*)(void))app[1])();
```

### What is MISRA C? {E}
MISRA C is a set of coding guidelines for safety- and security-critical C, first written for the automotive industry. Rules forbid or restrict things like dynamic memory, recursion, `goto`, implicit conversions between essential types, and unions for type punning. Compliance is checked with static analysis tools (such as PC-lint, Polyspace, Coverity, cppcheck's MISRA addon) and deviations must be documented. The current edition is MISRA C:2023.
