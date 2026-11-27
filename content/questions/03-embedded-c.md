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
**Short answer:** No. `volatile` only stops the **compiler** from caching, merging or removing accesses. It does not make read-modify-write operations atomic, does not make multi-word accesses atomic, and does not stop the **CPU** (or other cores, caches and bus) from reordering memory accesses.

**Three ways volatile is not enough**

1. **Read-modify-write:** `volatile uint32_t count; count++;` compiles to load, add, store. An ISR that also increments `count` between the load and the store loses one increment.
2. **Multi-word data:** a 64-bit `volatile uint64_t ticks` on a 32-bit Cortex-M is read with two 32-bit loads. If the timer ISR updates it between them (e.g. when the low word wraps from `0xFFFFFFFF` to 0), the reader sees a torn value that is off by about 4 billion.
3. **Ordering between variables:** writing `data = x; ready = true;` with both volatile guarantees the compiler keeps the order, but on a multi-core system or with write buffers, another core may see `ready` before `data` without a barrier (`__DMB()`, or C11 release/acquire).

**The right tools**

| Situation | Tool |
|---|---|
| Main code ↔ ISR on a single-core MCU | short critical section (disable/mask interrupts), or a single aligned 32-bit word that only one side writes |
| Counters/flags shared between threads | C11 `<stdatomic.h>` (`atomic_fetch_add`), compiled to `LDREX`/`STREX` on Cortex-M3+ |
| Complex shared data between tasks | RTOS mutex, or message queues (do not share at all) |
| Multi-core / DMA ordering | memory barriers or acquire/release atomics, plus cache maintenance |
| Linux kernel | `atomic_t`, `READ_ONCE`/`WRITE_ONCE`, spinlocks, RCU |

**Reading a 64-bit counter safely without disabling interrupts:**

```c
uint64_t read_ticks64(void)
{
    uint32_t hi1, lo, hi2;
    do {
        hi1 = g_ticks_hi;          /* volatile, updated by the ISR */
        lo  = g_ticks_lo;
        hi2 = g_ticks_hi;
    } while (hi1 != hi2);          /* retry if the ISR changed the high word meanwhile */
    return ((uint64_t)hi1 << 32) | lo;
}
```

**Interview line:** Volatile is for observable accesses such as MMIO; atomics and locks are for concurrency. A simple ISR flag may use volatile under platform-specific atomicity and interrupt rules. For portable threaded C, volatile alone never prevents a data race.

### Can a pointer be volatile? Explain the declarations. {M}
**Short answer:** Yes; the position of `volatile` relative to `*` decides what is volatile, exactly like `const`. `volatile int *p` is a pointer to volatile data (the normal case for registers). `int *volatile p` is a volatile pointer to normal data (the pointer variable itself may be changed by an ISR). `volatile int *volatile p` makes both volatile.

| Declaration | What is volatile | Typical use |
|---|---|---|
| `volatile uint32_t *p` | the data `*p` | pointer to a hardware register or a DMA buffer |
| `uint32_t *volatile p` | the pointer `p` | a buffer pointer that an ISR swaps (double buffering) |
| `volatile uint32_t *volatile p` | both | an ISR-swapped pointer to a buffer that DMA writes |
| `volatile uint32_t *const p` | the data; the pointer is constant | fixed register address |
| `const volatile uint32_t *p` | data is volatile and read-only through `p` | read-only status register |

```c
/* fixed register: the address never changes, the contents do */
volatile uint32_t *const UART_DR = (volatile uint32_t *)0x40004404u;

/* double buffering: the ISR flips which buffer the main loop processes */
static uint8_t buf_a[64], buf_b[64];
static uint8_t *volatile ready_buf;       /* pointer written by the ISR */

void DMA_IRQHandler(void) { ready_buf = (ready_buf == buf_a) ? buf_b : buf_a; }
```

**Reading tip:** read right to left from the name. `int *volatile p`: "p is a volatile pointer to int". `volatile int *p`: "p is a pointer to an int that is volatile".

**Pointers to volatile structs:** declaring the struct members `volatile` (as CMSIS does: `__IO uint32_t CR;`) or the pointer target `volatile GPIO_TypeDef *` both make every member access volatile.

**Casting away volatile** (`(uint32_t *)p` from `volatile uint32_t *`) and then accessing the object is undefined behaviour if the object was defined volatile, and in practice lets the compiler optimise away accesses you need.

### What is an ISR and what are the rules for writing one? {E}
**Short answer:** An Interrupt Service Routine (ISR, interrupt handler) is the function the CPU runs when a hardware interrupt or exception occurs. The rules: keep it short and fast, never block, clear the interrupt source, share data safely with the rest of the program, and do heavy processing elsewhere (main loop, RTOS task, bottom half).

**The rules and the reasons**

1. **Keep it short.** While it runs, lower- or equal-priority interrupts wait, which adds latency to them. Read the data, clear the flag, put the data in a buffer, signal a task, return.
2. **Never block or wait.** No `delay()`, no busy-waiting for a peripheral that takes milliseconds, no waiting for a mutex (an ISR cannot sleep; in an RTOS it would deadlock or crash).
3. **No `printf`, `malloc` or other non-reentrant library calls.** They may hold internal locks or static buffers that the interrupted code was using.
4. **Clear the interrupt flag** (in the peripheral and, where needed, in the interrupt controller). Otherwise the interrupt fires again immediately when the ISR returns. On Cortex-M with write buffers, make sure the clearing write has completed before returning (`__DSB()` or a read-back), or the ISR can re-enter spuriously.
5. **Share data safely:** `volatile` for flags and indexes, lock-free single-producer/single-consumer ring buffers, or the RTOS's ISR-safe APIs (`xQueueSendFromISR`, `xTaskNotifyFromISR`).
6. **Be careful with floating point:** on Cortex-M4F/M7, FPU use in an ISR increases stacking (lazy stacking reduces the cost); some projects forbid FP in ISRs.
7. **No arguments and no return value** (see the next question).

**A typical UART receive ISR**

```c
#define RX_SIZE 128u                       /* power of two */
static volatile uint8_t  rx_buf[RX_SIZE];
static volatile uint16_t rx_head;          /* written only by the ISR  */
static volatile uint16_t rx_tail;          /* written only by the main loop */

void USART2_IRQHandler(void)
{
    if (USART2->SR & USART_SR_RXNE) {
        uint8_t b = (uint8_t)USART2->DR;   /* reading DR clears RXNE */
        uint16_t next = (rx_head + 1u) & (RX_SIZE - 1u);
        if (next != rx_tail) {             /* drop the byte if the buffer is full */
            rx_buf[rx_head] = b;
            rx_head = next;
        }
    }
}
```

**Interview extras:** mention priorities (urgent ISRs get higher priority), checking `SR` for error flags (overrun, framing), and the RTOS rule that ISRs above `configMAX_SYSCALL_INTERRUPT_PRIORITY` must not call any RTOS API.

### Can you pass parameters to or return a value from an ISR? {E}
**Short answer:** No. The hardware calls the ISR asynchronously, at an arbitrary point in the program, so there is no caller to supply arguments or to receive a return value. ISRs are declared `void handler(void)`. Data goes in and out through shared variables, buffers, queues or RTOS objects.

**Why it is impossible**

- The CPU jumps to the address in the vector table when the interrupt occurs; it does not set up argument registers.
- The interrupted code did not call the ISR and does not expect any result.
- On Cortex-M, the exception entry pushes `r0`–`r3`, `r12`, `lr`, `pc`, `xPSR` automatically and loads `LR` with an `EXC_RETURN` value; the ISR returning normally restores everything. Any value left in `r0` is discarded.

**How to get data in and out**

| Direction | Mechanism |
|---|---|
| ISR → main/tasks | `volatile` flags, ring buffers, RTOS queues/notifications/semaphores given "FromISR" |
| Main → ISR (configuration) | `volatile` variables set before enabling the interrupt |
| Context for a shared handler | a static table indexed by peripheral instance, e.g. `uart_ctx[instance]` |

**Exceptions to know**

- **SVC (supervisor call)** handlers do receive "arguments": the caller's `r0`–`r3` are in the stacked exception frame, and the handler can read them (and write a return value into the stacked `r0`). RTOS kernels and secure-call gateways use this.
- **HardFault handlers** commonly read the stacked frame to find the faulting PC; they get the stack pointer through a small assembly wrapper.
- On some other architectures (e.g. AVR with `ISR()` macros, or the `interrupt` keyword on older compilers), the compiler generates special prologue/epilogue code; still no parameters.

**Linux contrast:** a Linux interrupt handler is registered with `request_irq()` and does receive arguments (`int irq, void *dev_id`) and returns `IRQ_HANDLED`/`IRQ_NONE`, because the kernel's generic interrupt code calls it like a normal function.

### What is interrupt latency and how do you reduce it? {M}
**Short answer:** Interrupt latency is the time from the interrupt signal being asserted until the first instruction of the ISR runs. On Cortex-M3/M4 the hardware minimum is 12 clock cycles with zero-wait-state memory (Cortex-M0 is 16, M0+ 15). In real systems it is dominated by software: periods with interrupts disabled, higher-priority interrupts running, and memory wait states.

**What adds latency**

| Cause | Effect |
|---|---|
| Interrupts disabled (critical sections, `__disable_irq`) | the interrupt waits until they are re-enabled |
| A higher- or equal-priority ISR already running | waits for it to finish (or tail-chains after it) |
| Flash wait states, cache misses on the vector fetch or stacking | adds cycles |
| FPU context stacking (Cortex-M4F/M7) | up to 17 extra words; lazy stacking defers it |
| RTOS kernel critical sections | the kernel masks interrupts up to its syscall priority |
| Multi-cycle instructions (e.g. `LDM` on some cores) | may be restarted or completed first |
| Wake-up from deep sleep | clock and regulator start-up time (microseconds to milliseconds) |

**How to reduce it**

- Keep critical sections short; mask only what you must (**`BASEPRI`** to block lower priorities instead of `PRIMASK`, which blocks everything).
- Give time-critical interrupts the highest priority and keep other ISRs short.
- Put the vector table and hot ISRs in RAM or TCM (Cortex-M7: ITCM) to avoid flash wait states; enable flash prefetch/ART accelerators and caches.
- Avoid the FPU in time-critical ISRs, or keep lazy stacking enabled.
- On an RTOS, run the most time-critical interrupts **above** the RTOS's maximum syscall priority, so kernel critical sections never mask them (they then must not call RTOS APIs).
- Choose a lighter sleep mode if wake-up time matters.

**Jitter** (variation in latency) often matters more than the average for control loops; measure both by toggling a GPIO at the start of the ISR and capturing the delay from the input edge on an oscilloscope or logic analyser.

**Related Cortex-M features:** tail-chaining (6 cycles between back-to-back ISRs instead of a full exit and entry) and late arrival (a higher-priority interrupt arriving during stacking gets serviced first without re-stacking) both reduce latency automatically.

### What is a critical section and how do you implement one on bare metal? {M}
**Short answer:** A critical section is a piece of code that must not be interrupted by anything that accesses the same shared data. On a single-core MCU the simplest implementation is to disable interrupts on entry and restore the previous state on exit; saving and restoring (instead of blindly re-enabling) makes it safe to nest.

```c
#include "cmsis_compiler.h"

static inline uint32_t irq_save(void)
{
    uint32_t primask = __get_PRIMASK();   /* 1 if interrupts were already disabled */
    __disable_irq();                      /* CPSID i */
    return primask;
}

static inline void irq_restore(uint32_t primask)
{
    __set_PRIMASK(primask);               /* re-enable only if they were enabled before */
}

void counter_add(uint32_t n)
{
    uint32_t s = irq_save();
    shared_counter += n;                  /* read-modify-write is now safe from ISRs */
    irq_restore(s);
}
```

**Why save/restore:** if a function with a critical section is called from inside another critical section, a plain `__enable_irq()` at its end would enable interrupts too early, in the middle of the outer section.

**Masking only some interrupts (Cortex-M3 and later):**

```c
uint32_t old = __get_BASEPRI();
__set_BASEPRI_MAX(5u << (8u - __NVIC_PRIO_BITS));   /* block priority 5 and lower urgency */
/* ... */
__set_BASEPRI(old);
```

Interrupts more urgent than the threshold still run, so their latency is unaffected. FreeRTOS uses this for `taskENTER_CRITICAL()` on Cortex-M3+.

**Other ways to protect shared data**

- **Disable only the one peripheral's interrupt** (`NVIC_DisableIRQ(USART2_IRQn)`) when only that ISR shares the data.
- **Atomic instructions:** `LDREX`/`STREX` (C11 atomics) on Cortex-M3+; not available on M0/M0+.
- **Lock-free design:** single-producer/single-consumer ring buffers where each index is written by only one side.
- **RTOS:** `taskENTER_CRITICAL()` from tasks, `taskENTER_CRITICAL_FROM_ISR()` in ISRs, or a mutex if the section is long and no ISR is involved.

**Rules**

- Keep it as short as possible: everything inside adds interrupt latency.
- Never call blocking functions inside it.
- On **multi-core** systems disabling interrupts on one core does not stop the other core: you need a spinlock or hardware semaphore (e.g. the HSEM on STM32H7 dual-core) as well.

### What is a reentrant function? {M}
**Short answer:** A function is reentrant if it can be interrupted partway through and safely called again (from an ISR, a signal handler or recursion) before the first call has finished, with both calls producing correct results. That requires using only its arguments and local variables, or protecting any shared state, and calling only other reentrant functions.

**Requirements**

- No modification of static or global data without protection.
- No returning pointers to static internal buffers.
- No calls to non-reentrant functions (`malloc`, `printf`, `strtok`, `rand`, `asctime`, most stdio).
- No self-modifying code, and hardware accessed in a way that tolerates interleaving.

**Non-reentrant vs reentrant**

```c
/* NOT reentrant: shared static buffer */
char *to_hex(uint8_t v)
{
    static char buf[3];
    buf[0] = "0123456789ABCDEF"[v >> 4];
    buf[1] = "0123456789ABCDEF"[v & 0xF];
    buf[2] = '\0';
    return buf;                 /* a second call (from an ISR) overwrites the first result */
}

/* reentrant: the caller provides the storage */
char *to_hex_r(uint8_t v, char out[3])
{
    out[0] = "0123456789ABCDEF"[v >> 4];
    out[1] = "0123456789ABCDEF"[v & 0xF];
    out[2] = '\0';
    return out;
}
```

**Standard library examples:** `strtok` → `strtok_r`, `rand` → `rand_r`, `localtime` → `localtime_r`, `gmtime` → `gmtime_r`. In newlib, reentrancy is handled with a per-thread `struct _reent`; RTOSes like FreeRTOS can switch it per task (`configUSE_NEWLIB_REENTRANT`).

**Why it matters in embedded systems:** any function called from both an ISR and the main loop (a logging function, a CRC routine, a driver helper) must be reentrant, otherwise the ISR can corrupt the main loop's work in progress, causing rare, timing-dependent bugs.

**Note:** reentrant is not the same as thread-safe (next question).

### What is the difference between reentrant and thread-safe? {H}
**Short answer:** A **thread-safe** function works correctly when called from several threads at the same time; it may achieve that with locks. A **reentrant** function works correctly when a call is interrupted and the **same** function is called again on the same execution context (ISR, signal handler, recursion) before the first call finishes. A function that uses a mutex is thread-safe but **not** reentrant: if an ISR interrupts it while it holds the lock and calls it again, the ISR waits forever for a lock that can only be released by the code it interrupted.

| | Reentrant | Thread-safe |
|---|---|---|
| Problem it solves | interruption and re-entry on the same core/thread | concurrent calls from different threads |
| Typical technique | no shared state; caller-provided buffers | locks around shared state, or no shared state |
| Mutex inside | breaks reentrancy (deadlock from an ISR or signal handler) | fine |
| Example | `strtok_r`, `memcpy` | `malloc` in glibc (locks), `printf` (locks the stream) |

**Examples**

```c
static uint32_t total;
static mutex_t m;

void add_threadsafe(uint32_t v)        /* thread-safe, NOT reentrant */
{
    mutex_lock(&m);
    total += v;
    mutex_unlock(&m);
}

uint32_t add_pure(uint32_t a, uint32_t b) { return a + b; }   /* both */
```

**Which functions are both:** those with no shared mutable state (pure functions of their arguments), or that update shared state with a single atomic operation that also works from interrupts (e.g. `atomic_fetch_add` on a lock-free atomic).

**Async-signal-safe** is the POSIX term for functions that may be called from a signal handler: it is a strict form of reentrancy. `write()`, `_exit()` and `sem_post()` are; `printf()` and `malloc()` are not.

**Practical rule for firmware:** functions used from ISRs must be reentrant (no locks, no static buffers). Functions used only by tasks can use RTOS mutexes for thread safety.

### How do you set, clear, toggle and test a bit in a register? {E}
**Short answer:** Build a single-bit mask with `1u << n`, then OR it to set, AND with its complement to clear, XOR to toggle, and AND to test. For multi-bit fields, clear the field with an inverted mask and OR in the new value.

```c
reg |=  (1u << n);                  /* set bit n    */
reg &= ~(1u << n);                  /* clear bit n  */
reg ^=  (1u << n);                  /* toggle bit n */
if (reg & (1u << n)) { }            /* test bit n (non-zero if set) */
bool b = (reg >> n) & 1u;           /* bit n as 0 or 1 */

/* multi-bit field: e.g. bits 5..4 = mode */
#define MODE_Pos 4u
#define MODE_Msk (3u << MODE_Pos)
reg = (reg & ~MODE_Msk) | ((mode << MODE_Pos) & MODE_Msk);
```

**Why `1u`:** `1 << 31` shifts into the sign bit of a signed `int`, which is undefined behaviour (before C23). With `1u` the shift is unsigned and well-defined.

**On real hardware, prefer hardware set/clear registers** when the peripheral has them:

```c
GPIOA->BSRR = (1u << 5);            /* set PA5 atomically (STM32)                 */
GPIOA->BSRR = (1u << (5 + 16));     /* reset PA5 atomically                       */
NRF_P0->OUTSET = (1u << 13);        /* nRF52: separate SET/CLR registers          */
```

A single write cannot be corrupted by an interrupt, unlike `|=` (read-modify-write).

**Registers that behave differently**

- **Write-1-to-clear (W1C)** status flags: clear a flag by writing a 1 **only** to that bit (`SR = FLAG;`), not `SR |= FLAG;`, which would clear every pending flag.
- **Read-to-clear** registers: reading them for a test also clears them.
- **Write-only** registers (e.g. `BSRR`): reading returns 0 or garbage, so `|=` does not work.

Always check the reference manual's access type (rw, r, w, rc_w1, rc_r).

### Why can a read-modify-write on a register be dangerous? {H}
**Short answer:** `REG |= BIT;` is three separate operations: read the register, OR in the bit, write it back. If anything changes the register between the read and the write (an ISR, another core, DMA, or the hardware itself), that change is overwritten. Read-modify-write can also clear write-1-to-clear flags you did not intend to touch, and lose data on registers that change when read.

**Three classic failures**

1. **Interrupt race:**

```c
/* main loop */                    /* ISR (runs between the read and the write) */
tmp = GPIOA->ODR;    /* reads 0x00 */
                                   GPIOA->ODR |= LED2;   /* ODR = 0x04 */
tmp |= LED1;
GPIOA->ODR = tmp;    /* writes 0x01: LED2 turned off again! */
```

2. **Write-1-to-clear flags:** a status register has `TC` (transfer complete) and `ERR` flags, both cleared by writing 1. `SR |= TC_FLAG;` reads both as 1 and writes both back as 1, clearing an error you have not handled yet. Write `SR = TC_FLAG;`.

3. **Read side effects:** some registers clear or pop on read (UART data registers, some interrupt status registers, FIFO registers). A read-modify-write consumes data.

4. **Hardware-updated bits:** a control register may contain a bit the hardware clears when an operation finishes (e.g. a "start conversion" bit). Reading it as 1 and writing it back restarts the operation.

**Solutions**

| Solution | Notes |
|---|---|
| Hardware set/clear registers (STM32 `BSRR`/`BRR`, NXP `SET`/`CLR`/`TOGGLE` aliases, nRF `OUTSET`/`OUTCLR`) | one write, atomic, best option |
| Bit-banding (Cortex-M3/M4 only) | atomic single-bit writes |
| Critical section around the RMW | simple; adds latency |
| `LDREX`/`STREX` loop | atomic for normal memory; not usable on many peripheral registers |
| Ownership | design so only one context ever writes a given register |

**Interview tip:** mention that the same issue appears with shared variables, not just registers, and that it is the main reason for driver design rules such as "configure a peripheral only from one context".

### What is bit-banding on Cortex-M? {H}
**Short answer:** On Cortex-M3 and Cortex-M4, bit-banding maps each **bit** of two 1 MB regions (the first 1 MB of SRAM at `0x20000000` and of the peripheral space at `0x40000000`) to its own 32-bit word in an **alias** region (`0x22000000` and `0x42000000`). Writing 0 or 1 to an alias word changes exactly that one bit atomically (the bus does the read-modify-write in one locked transaction); reading the alias word returns the bit's value.

**Address formula**

```
alias_address = alias_base + (byte_offset × 32) + (bit_number × 4)

SRAM:        alias_base = 0x22000000, byte_offset = address - 0x20000000
Peripheral:  alias_base = 0x42000000, byte_offset = address - 0x40000000
```

**Example:** bit 5 of the register at `0x40020014` (GPIOA ODR on an STM32F4):

```c
#define BITBAND_PERIPH(addr, bit) \
    (*(volatile uint32_t *)(0x42000000u + (((uint32_t)(addr) - 0x40000000u) * 32u) + ((bit) * 4u)))

BITBAND_PERIPH(&GPIOA->ODR, 5) = 1;   /* set PA5 atomically: 0x42000000 + 0x20014*32 + 20 = 0x42400294 */
```

**Benefits**

- Atomic set/clear of one bit without disabling interrupts.
- Faster than a software read-modify-write in some cases.
- Compact boolean flags in SRAM that can be updated from ISRs safely.

**Limitations**

- Only on **Cortex-M3 and M4** (and only if the chip vendor implemented it). Not on Cortex-M0/M0+, M7, M23, M33, M55 or M85.
- Only the two 1 MB regions.
- Still a read-modify-write at the bus level: on registers with W1C bits or read side effects, it can have the same unwanted effects as a software RMW of the whole word.

**Portable alternatives:** hardware set/clear registers, exclusive access instructions, or critical sections. Because bit-banding was removed from newer cores, new code should not depend on it.

### What happens before main() runs on a microcontroller? {M}
**Short answer:** On reset, the Cortex-M core reads the initial stack pointer from the first word of the vector table and the reset handler's address from the second word, then starts executing the reset handler. The reset handler (start-up code) typically configures clocks and the FPU (`SystemInit`), copies the `.data` section's initial values from flash to RAM, zeroes `.bss`, runs C/C++ constructors, and finally calls `main()`.

**Step by step**

1. **Hardware reset sequence:** the core loads `MSP` from address `VTOR + 0` (usually `0x00000000`, aliased to flash at `0x08000000` on STM32) and `PC` from `VTOR + 4`. Thumb mode, privileged, all interrupts enabled but no peripheral interrupts enabled yet.
2. **Reset_Handler** (in `startup_<device>.s` or a C file):
   - `SystemInit()`: set up clocks/PLL (or leave that to `main`), flash wait states, enable the FPU (`SCB->CPACR`), set `VTOR` if the image is not at the default address.
   - **Copy `.data`:** from its load address in flash (`_sidata`) to its run address in RAM (`_sdata`..`_edata`).
   - **Zero `.bss`:** `_sbss`..`_ebss`.
   - Optionally copy code into RAM/ITCM (`.ramfunc`) and initialise other memories (e.g. external SDRAM must be set up **before** any data placed there is initialised).
   - `__libc_init_array()`: runs C++ static constructors and functions marked `__attribute__((constructor))`.
   - Call `main()`; if it returns, loop forever.

```c
extern uint32_t _sidata, _sdata, _edata, _sbss, _ebss;
extern int main(void);
void SystemInit(void);
void __libc_init_array(void);

void Reset_Handler(void)
{
    SystemInit();
    for (uint32_t *s = &_sidata, *d = &_sdata; d < &_edata; ) *d++ = *s++;
    for (uint32_t *d = &_sbss; d < &_ebss; ) *d++ = 0;
    __libc_init_array();
    main();
    for (;;) { }
}
```

**Things that commonly go wrong**

- Writing the reset handler in C is fine, but it must not rely on initialised globals before they are copied, and the compiler may turn the copy loops into `memcpy`/`memset` calls (fine if those do not depend on `.data` either).
- A watchdog enabled by option bytes can reset the chip during a long `.bss` clear on large-RAM parts.
- Variables meant to survive a reset must be in a `.noinit` section, or the zeroing wipes them.
- Clock configuration done too late can make the copy loops slow on big images.

**Follow-up:** "What runs before the reset handler?" On many MCUs a **boot ROM** (system memory bootloader) runs first, reads boot pins/option bytes and decides whether to start user flash, the built-in UART/USB DFU bootloader, or SRAM.

### What is a linker script and what does it contain? {M}
**Short answer:** A linker script tells the linker what memory the target has and where each output section (code, constants, initialised data, zeroed data, stack, heap) goes. It defines `MEMORY` regions (start address, size, permissions) and a `SECTIONS` command mapping input sections to output sections and regions, and it exports symbols (such as `_sdata`, `_ebss`, `_estack`) that the start-up code uses.

```ld
MEMORY
{
  FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 512K
  RAM   (rwx) : ORIGIN = 0x20000000, LENGTH = 128K
}

_estack = ORIGIN(RAM) + LENGTH(RAM);       /* initial stack pointer: top of RAM */

SECTIONS
{
  .isr_vector : { KEEP(*(.isr_vector)) } > FLASH       /* KEEP: never garbage-collect */

  .text : { *(.text*) *(.rodata*) . = ALIGN(4); } > FLASH

  _sidata = LOADADDR(.data);
  .data : { _sdata = .; *(.data*) . = ALIGN(4); _edata = .; } > RAM AT> FLASH

  .bss (NOLOAD) : { _sbss = .; *(.bss*) *(COMMON) . = ALIGN(4); _ebss = .; } > RAM

  .noinit (NOLOAD) : { *(.noinit*) } > RAM             /* not zeroed at start-up */

  ._user_heap_stack : { . = ALIGN(8); . += 0x1000; . += 0x800; } > RAM   /* reserve heap + stack, fail link if no room */
}
```

**Key concepts**

- **VMA vs LMA:** `.data` has a run address (VMA) in RAM and a load address (LMA) in flash (`> RAM AT> FLASH`). The start-up code copies from LMA to VMA.
- **`KEEP`** stops `--gc-sections` from removing sections nothing references explicitly (vector table, init arrays).
- **`NOLOAD`** sections take no space in the output image.
- **Symbols** defined in the script have an address but no storage; in C you use `&_sdata`.
- The linker fails with "region `RAM' overflowed" if things do not fit, which is better than finding out at run time.

**Common reasons to edit a linker script**

- Leave room for a **bootloader** (application starts at `0x08008000`), or for configuration/calibration data in a reserved flash sector.
- Place time-critical code in RAM or ITCM, and DMA buffers in a specific (non-cacheable or DMA-reachable) RAM bank.
- Add a `.noinit` area for crash logs or a bootloader-to-application mailbox.
- Use external memory (QSPI flash for graphics, SDRAM for frame buffers).
- Insert a firmware header (version, CRC, size) at a fixed offset.

**Check the result** in the map file (`-Wl,-Map=fw.map`) and with `arm-none-eabi-size -A fw.elf`.

### What is the vector table? {E}
**Short answer:** The vector table is an array of addresses that the CPU uses to find handlers for exceptions and interrupts. On Cortex-M it is at address 0 by default (relocatable with `SCB->VTOR`): entry 0 is the initial main stack pointer, entry 1 is the reset handler, then the system exception handlers (NMI, HardFault, MemManage, BusFault, UsageFault, SVCall, DebugMonitor, PendSV, SysTick), followed by one entry per peripheral interrupt (IRQ0, IRQ1, ...).

| Offset | Entry | Exception number |
|---|---|---|
| 0x00 | Initial MSP value | – |
| 0x04 | Reset | 1 |
| 0x08 | NMI | 2 |
| 0x0C | HardFault | 3 |
| 0x10–0x18 | MemManage, BusFault, UsageFault (not on M0/M0+) | 4–6 |
| 0x1C–0x28 | SecureFault (v8-M) / reserved | 7–10 |
| 0x2C | SVCall | 11 |
| 0x30 | DebugMonitor | 12 |
| 0x38 | PendSV | 14 |
| 0x3C | SysTick | 15 |
| 0x40 + 4·n | IRQn (peripheral interrupts) | 16 + n |

**In C (GCC):**

```c
extern uint32_t _estack;
void Reset_Handler(void);
void Default_Handler(void) { for (;;) { } }
void NMI_Handler(void)       __attribute__((weak, alias("Default_Handler")));
void HardFault_Handler(void) __attribute__((weak, alias("Default_Handler")));
void USART2_IRQHandler(void) __attribute__((weak, alias("Default_Handler")));

__attribute__((section(".isr_vector"), used))
void (*const vector_table[])(void) = {
    (void (*)(void))&_estack,
    Reset_Handler,
    NMI_Handler,
    HardFault_Handler,
    /* ... */
};
```

**Details**

- Handler addresses have bit 0 set (Thumb state); the compiler/linker does this automatically for function addresses.
- `VTOR` alignment: the table must be aligned to a power of two at least as large as the table (e.g. 512 bytes for up to 128 entries); check the core's rules.
- Relocating the table to RAM lets you change handlers at run time and is needed by bootloaders (the application sets `VTOR` to its own table).
- Cortex-A uses a different scheme: a table of **instructions** (branches) per exception type, located via `VBAR_ELx`, and a separate interrupt controller (GIC) provides the interrupt number.

### What are weak symbols? {M}
**Short answer:** A weak symbol is a definition that the linker uses only if no normal (strong) definition with the same name exists. Start-up files define every interrupt handler as a weak alias of a default handler, so when you write a function with the exact same name in your code, your strong definition replaces it, without editing the start-up file.

```c
/* startup.c */
void Default_Handler(void) { for (;;) { } }
void USART1_IRQHandler(void) __attribute__((weak, alias("Default_Handler")));

/* uart.c: this strong definition overrides the weak one */
void USART1_IRQHandler(void)
{
    /* real handler */
}
```

**Other uses**

- **Hooks with default implementations:** a library defines `__attribute__((weak)) void app_error_hook(int code) { }` and calls it; the application may override it.
- **Platform overrides:** HAL libraries define weak callbacks (`HAL_UART_RxCpltCallback`) that you implement in your code.
- **Optional features:** `if (optional_fn) optional_fn();` with a weak **declaration** (`extern void optional_fn(void) __attribute__((weak));`), which is NULL if no one defines it.

**Pitfalls**

- **Misspelled handler name:** `void USART1_IRQHandle(void)` (missing `r`) compiles and links fine; the weak default stays in the vector table, and when the interrupt fires the system hangs in `Default_Handler`. When debugging a hang there, check which interrupt is active (`SCB->ICSR` `VECTACTIVE` field).
- **C++ name mangling:** a handler defined in a `.cpp` file must be `extern "C"`, or its name will not match.
- **Static libraries:** the linker only pulls an object file out of a `.a` archive to satisfy an **undefined** reference; it does not search archives to replace a weak definition. A strong override inside a library may therefore be silently ignored unless something else pulls in that object (use `--whole-archive` or put the override in a directly linked object).
- **LTO and weak symbols** have had compiler bugs; check the map file to see which definition was used.

### How do you place a variable or function at a specific address or section? {M}
**Short answer:** Put it in a named section with `__attribute__((section(".name")))` and map that section to the right memory region (or address) in the linker script. For a fixed absolute address, define the section at that address in the script, or (for read-only/hardware addresses) use a pointer to that address instead of a variable.

```c
/* code that must run from RAM, e.g. while flash is being erased */
__attribute__((section(".ramfunc"), noinline, long_call))
void flash_erase_sector(uint32_t sector) { /* ... */ }

/* data kept across a warm reset (not zeroed at start-up) */
__attribute__((section(".noinit"))) uint32_t reset_count;

/* firmware header at a fixed offset, read by the bootloader */
__attribute__((section(".fw_header"), used))
const struct fw_header hdr = { .magic = 0x46574844u, .version = 0x010200u };

/* DMA buffer in a non-cacheable, DMA-reachable SRAM bank, cache-line aligned */
__attribute__((section(".dma_buf"), aligned(32))) uint8_t adc_buf[1024];
```

```ld
.ramfunc : { _sramfunc = .; *(.ramfunc*) _eramfunc = .; } > RAM AT> FLASH   /* copied at start-up */
.noinit (NOLOAD) : { *(.noinit*) } > RAM
.fw_header 0x08008200 : { KEEP(*(.fw_header)) } > FLASH
.dma_buf (NOLOAD) : { *(.dma_buf*) } > SRAM_D2
```

**Why code runs from RAM:** on most MCUs you cannot read (execute from) a flash bank while it is being erased or programmed; the CPU stalls or faults. Placing the flash-programming routine (and everything it calls, and the interrupt handlers that may run) in RAM avoids this. `long_call` makes calls between RAM and flash work when they are further apart than a branch instruction can reach.

**Other mechanisms**

- `used` / `KEEP()` stop the compiler and linker from removing data nothing references.
- IAR uses `@` placement (`int x @ 0x20001000;`) and `#pragma location`; Keil has `__attribute__((at(addr)))` in older versions.
- For hardware registers, never declare a variable; use a pointer constant: `#define REG (*(volatile uint32_t *)0x40021000u)`.

**Verify** in the map file that the symbol landed where you expected.

### What is a watchdog timer and how should you use it? {E}
**Short answer:** A watchdog is an independent hardware timer that resets the microcontroller unless software "kicks" (refreshes) it before it expires. It recovers the system from software hangs, infinite loops, deadlocks and runaway code. To be effective, the kick must prove that the **whole** system is healthy, not just that one timer interrupt is still running.

**Types**

- **Independent watchdog** (e.g. STM32 IWDG): runs from its own low-speed oscillator, so it works even if the main clock fails; often cannot be stopped once started.
- **Window watchdog** (WWDG): a refresh that comes **too early** also triggers a reset, catching code that runs too fast or loops around the kick.
- **External watchdog ICs:** a separate chip, required in some safety designs, can also monitor supply voltage.

**Good practice**

1. **Kick from one place, after checking that every critical task has checked in.** Each task sets its bit in a "alive" mask; a supervisor (main loop or low-priority task) kicks only when all bits are set, then clears them.

```c
static volatile uint32_t alive;
#define TASK_COMMS  (1u << 0)
#define TASK_CTRL   (1u << 1)
#define ALL_TASKS   (TASK_COMMS | TASK_CTRL)

void task_checkin(uint32_t bit) { __atomic_fetch_or(&alive, bit, __ATOMIC_RELAXED); }

void supervisor_tick(void)                 /* every 100 ms */
{
    if ((alive & ALL_TASKS) == ALL_TASKS) {
        IWDG->KR = 0xAAAAu;                /* refresh */
        alive = 0;
    }                                      /* else: let the watchdog reset the chip */
}
```

2. **Never kick from a timer ISR alone:** the ISR keeps running when the main loop is stuck, so the watchdog never fires.
3. **Record the reset cause** at boot (`RCC->CSR` flags on STM32) and log or report watchdog resets; they are evidence of field bugs.
4. **Choose the timeout** longer than the worst-case loop time (including flash erase and slow operations), but short enough to recover quickly; disable or extend it carefully during long operations instead of kicking in many places.
5. **Low-power modes:** decide whether the watchdog should run (and wake the device) in stop/sleep modes.
6. **Debugging:** freeze the watchdog when the core is halted by the debugger (`DBGMCU` freeze bits), or you get resets while stepping.
7. **After a watchdog reset:** consider a safe mode if resets repeat (count them in a `.noinit` variable), instead of an endless reset loop.

### What is debouncing and how do you implement it? {E}
**Short answer:** Mechanical switches and buttons "bounce": the contacts open and close several times for a few milliseconds (typically 1–10 ms, sometimes more) when pressed or released. Debouncing means accepting a new state only after the input has been stable for a period. Do it in software by sampling periodically, or in hardware with an RC filter and a Schmitt-trigger input.

**Software: shift-register (integrating) debounce, called every 1 ms**

```c
#include <stdbool.h>
#include <stdint.h>

static bool pressed;

void button_poll_1ms(void)
{
    static uint8_t history;
    history = (uint8_t)((history << 1) | (read_pin() ? 1u : 0u));
    if (history == 0xFFu)      pressed = true;    /* 8 consecutive samples high */
    else if (history == 0x00u) pressed = false;   /* 8 consecutive samples low  */
    /* mixed samples: keep the previous state */
}
```

**Counter-based debounce for several buttons at once** (vertical counters) is a common efficient variant: process up to 8 or 32 buttons in parallel with bitwise operations.

**Edge detection after debouncing:**

```c
bool now = pressed;
if (now && !last) on_press();      /* rising edge of the debounced state */
last = now;
```

**Interrupt-based approach:** an edge interrupt starts a timer (and disables the pin interrupt); when the timer expires (e.g. 20 ms later), read the pin and re-enable the interrupt. This keeps the CPU asleep when nothing happens, which matters for battery devices.

**Hardware debouncing:** an RC low-pass filter (e.g. 10 kΩ and 100 nF, time constant 1 ms) smooths the bounce; a Schmitt-trigger input (most MCU GPIOs have hysteresis) turns the slow edge into a clean transition. Dedicated debouncer ICs exist too.

**Why not just use an edge interrupt on a raw switch?** Each bounce triggers an interrupt, so one press produces a burst of 5–50 interrupts, and the press may be counted many times.

**Interview follow-ups:** long press vs short press (count how long the debounced state stays pressed), and scanning a matrix keypad (see the next question).

### How do you scan a matrix keypad? {M}
**Short answer:** A matrix keypad connects keys at the crossings of rows and columns, so a 4×4 keypad needs 8 pins instead of 16. Configure the columns as inputs with pull-ups and the rows as outputs. Drive one row low at a time, read the columns: a column reading low means the key at that row and column is pressed. Repeat for each row every few milliseconds and debounce the result.

```c
#include <stdint.h>

#define ROWS 4
#define COLS 4
static const char keymap[ROWS][COLS] = {
    {'1','2','3','A'}, {'4','5','6','B'}, {'7','8','9','C'}, {'*','0','#','D'},
};

void row_drive(int r, int level);      /* board-specific GPIO helpers */
int  col_read(int c);                  /* returns 0 when pressed (pulled up) */
void delay_us(unsigned us);

/* returns the pressed key, or 0 if none; call every 5-10 ms and debounce */
char keypad_scan(void)
{
    for (int r = 0; r < ROWS; r++) {
        for (int i = 0; i < ROWS; i++) row_drive(i, 1);   /* all rows high (inactive) */
        row_drive(r, 0);                                   /* select one row */
        delay_us(5);                                       /* let the lines settle */
        for (int c = 0; c < COLS; c++)
            if (col_read(c) == 0)
                return keymap[r][c];
    }
    return 0;
}
```

**Design points to mention**

- **Settling time:** after changing a row, wait a few microseconds before reading; line capacitance and the pull-up resistors make the column take time to change.
- **Inactive rows:** drive them high or switch them to inputs (high-impedance). Using open-drain outputs avoids short circuits when two keys in the same column are pressed.
- **Debouncing:** require the same key in two or three consecutive scans.
- **Ghosting and masking:** pressing three keys at the corners of a rectangle makes a fourth key appear pressed, because current flows through the pressed keys. Diodes in series with each key prevent this (needed for keyboards with n-key rollover).
- **Low power:** instead of scanning continuously, drive all rows low and enable a pin-change interrupt on the columns; any key press wakes the MCU, which then scans.

**Related "classic peripherals" questions:** driving a multiplexed **seven-segment display** uses the same idea in reverse: enable one digit at a time, output its segment pattern, and cycle fast enough (more than 60 Hz per digit) that persistence of vision makes all digits appear lit; the segment current must be higher to keep brightness when each digit is on only 1/N of the time.

### What is polling versus interrupts versus DMA? {E}
**Short answer:** With **polling**, the CPU repeatedly checks a status flag and handles the peripheral when it is ready: simple and predictable, but it wastes CPU time and power. With **interrupts**, the peripheral signals the CPU when something happens, so the CPU can do other work or sleep: efficient for sporadic events, but each event costs an ISR entry and exit. With **DMA**, a DMA controller moves data between the peripheral and memory without the CPU, interrupting only when a block is done: best for high-throughput streams.

| | Polling | Interrupts | DMA |
|---|---|---|---|
| CPU load | high (busy waiting) | per event/byte | per block |
| Latency | lowest if the CPU is already polling | interrupt latency + ISR | hardware speed after set-up |
| Power | poor (cannot sleep) | good | best |
| Complexity | lowest | moderate (shared data, priorities) | highest (descriptors, buffers, cache) |
| Good for | very short waits, simple boot code, very fast devices | buttons, low-rate UART, timers, events | ADC streaming, audio (I2S), SPI displays, UART at high baud, memory copies |

**Example: receiving UART data at 1 Mbaud**

- Polling: the CPU can do nothing else.
- Interrupt per byte: 100,000 interrupts per second; at ~50 cycles each, a large fraction of a slow MCU's time.
- DMA into a circular buffer with "half complete", "complete" and **UART idle line** interrupts: a few interrupts per message.

**Combining them is normal:** DMA for the data, an interrupt at the end of each block, and polling for very short waits (e.g. waiting a few cycles for a flag after starting a conversion).

**DMA traps:** cache coherency on Cortex-M7 and Cortex-A (next question), buffers that must stay valid until the transfer finishes (never a local variable of a function that returns), bus matrix restrictions (some DMA controllers cannot access certain RAM banks or TCM), and handling errors and overruns.

### What are the cache coherency problems with DMA? {H}
**Short answer:** On CPUs with a data cache (Cortex-M7, Cortex-A, some Cortex-M55/M85 systems), the CPU reads and writes through its cache, but most DMA controllers on MCUs access main memory directly. The two can see different data: DMA may transmit stale data still waiting in the cache, and the CPU may read stale cached data after the DMA has written new data to memory. You must **clean** dirty cache lines before DMA reads memory. For DMA writes, prepare dedicated cache-line-aligned buffers before handing them to the device and invalidate stale lines after completion, following the platform's DMA and cache rules.

**The two cases**

| Direction | Problem | Fix |
|---|---|---|
| CPU writes buffer → DMA sends it (TX) | new data is in the (write-back) cache, not yet in RAM | **clean** (write back) the buffer's lines before starting DMA |
| DMA writes buffer → CPU reads it (RX) | the CPU's cache holds old data for those addresses | **invalidate** the lines after DMA completes (and also before starting, if the CPU might write-back dirty lines over the DMA data) |

```c
/* Cortex-M7 with CMSIS */
SCB_CleanDCache_by_Addr((uint32_t *)tx_buf, sizeof tx_buf);
start_dma_tx(tx_buf, sizeof tx_buf);

/* Before RX: dedicate whole cache lines; clean/invalidate as required. */
SCB_CleanInvalidateDCache_by_Addr((uint32_t *)rx_buf, sizeof rx_buf);
start_dma_rx(rx_buf, sizeof rx_buf);
/* ... RX complete interrupt; device has stopped writing ... */
SCB_InvalidateDCache_by_Addr((uint32_t *)rx_buf, sizeof rx_buf);
process(rx_buf);
```

**Alignment rule:** cache operations work on whole lines (32 bytes on Cortex-M7, 64 bytes on most Cortex-A). If a DMA buffer shares a cache line with another variable, invalidating the buffer also discards recent writes to that variable, and cleaning it writes stale data over DMA results. Align DMA buffers to the cache line size and round their size up to a multiple of it:

```c
__attribute__((aligned(32))) static uint8_t rx_buf[ALIGN_UP(RX_LEN, 32)];
```

**Alternatives**

- **Non-cacheable region:** use the MPU to make a RAM area non-cacheable (or write-through for TX-only buffers) and put DMA buffers there.
- **TCM memory** (DTCM on Cortex-M7) is not cached; check that the DMA controller can access it (on STM32H7, some DMAs cannot reach DTCM).
- **Hardware coherency:** Cortex-A systems with an ACP or CCI/CMN interconnect can make some DMA masters cache-coherent.

**Linux:** drivers never do this manually; the DMA API does it: `dma_map_single()`/`dma_unmap_single()` (streaming, does the clean/invalidate), and `dma_alloc_coherent()` (memory that is uncached or hardware-coherent).

**Symptom:** "DMA works with the cache disabled but returns old/corrupted data with the cache enabled" is a strong clue to investigate cache maintenance, buffer ownership and DMA addressability.

### What is a memory barrier and why would firmware need one? {H}
**Short answer:** A memory barrier forces an ordering between memory operations that the CPU, its write buffers or the bus would otherwise be allowed to reorder or delay. Arm has three barrier instructions: **`DMB`** (memory accesses before it are observed before those after it), **`DSB`** (waits for required completion of relevant preceding operations within the specified scope before subsequent instructions execute), and **`ISB`** (flush the pipeline so later instructions are fetched and decoded with the new context).

| Barrier | Guarantees | Typical use |
|---|---|---|
| `DMB` | ordering of memory accesses | multi-core shared data, DMA descriptor updates (descriptor written before the "go" bit), lock implementations |
| `DSB` | completion of memory accesses before continuing | before `WFI` (enter sleep), after clearing an interrupt flag at the end of an ISR, before an operation that depends on a write having reached a peripheral, after cache maintenance |
| `ISB` | pipeline refetch | after writing `CONTROL` (switching stack or privilege), after changing `VTOR`, MPU, or enabling the FPU, after self-modifying code (with cache maintenance) |

**Embedded examples**

```c
/* end of an ISR on a core with write buffers (Cortex-M7, or bus-bridged peripherals) */
TIM2->SR = ~TIM_SR_UIF;    /* clear the update flag */
__DSB();                   /* make sure the write reached the timer before returning,
                              otherwise the still-pending interrupt re-triggers the ISR */

/* changing privilege/stack */
__set_CONTROL(__get_CONTROL() | CONTROL_SPSEL_Msk);
__ISB();

/* MPU reconfiguration */
MPU->CTRL = MPU_CTRL_ENABLE_Msk | MPU_CTRL_PRIVDEFENA_Msk;
__DSB();
__ISB();
```

**Single-core Cortex-M:** most cores (M0/M3/M4) do not reorder memory accesses much, so barriers are rarely needed for plain data. Arm still recommends them in the architectural cases above (CONTROL, MPU, VTOR, before sleep), and they matter on Cortex-M7 (write buffers, caches) and for accesses to peripherals behind bus bridges.

**Multi-core and Cortex-A:** reordering is common. Use C11 atomics with acquire/release ordering (`atomic_store_explicit(&ready, 1, memory_order_release)`), which emit the right barriers, or the kernel's `smp_mb()`, `smp_wmb()`, `dma_wmb()`.

**Compiler vs CPU barriers:** `volatile` and `__asm volatile("" ::: "memory")` only constrain the **compiler**; they emit no instruction. CMSIS `__DMB()`/`__DSB()`/`__ISB()` include a compiler barrier **and** the hardware instruction.

### What is the Arm calling convention (AAPCS), and why does it matter in embedded work? {M}
**Short answer:** The AAPCS (Procedure Call Standard for the Arm Architecture) defines how functions pass arguments and return values and which registers they must preserve. On 32-bit Arm: the first four arguments go in `r0`–`r3`, the rest on the stack; results come back in `r0` (and `r1` for 64-bit values); `r0`–`r3` and `r12` are caller-saved (scratch); `r4`–`r11` are callee-saved; `r13` is SP, `r14` is LR (return address), `r15` is PC; and the stack must be 8-byte aligned at public function boundaries.

| Register | Role | Preserved across calls? |
|---|---|---|
| r0–r3 | arguments, return value, scratch | no (caller-saved) |
| r4–r11 | local variables | yes (callee-saved) |
| r12 (IP) | intra-procedure scratch | no |
| r13 (SP) | stack pointer | yes |
| r14 (LR) | return address | saved by callee if it makes calls |
| r15 (PC) | program counter | – |
| s0–s15 / d0–d7 (FPU) | FP arguments/results (hard-float), scratch | no |
| s16–s31 | FP callee-saved | yes |

AArch64 is similar with more registers: `x0`–`x7` for arguments and results, `x19`–`x28` callee-saved, `x29` frame pointer, `x30` link register, 16-byte stack alignment.

**Why it matters**

- **Cortex-M interrupts are plain C functions** because the hardware automatically stacks exactly the caller-saved registers (`r0`–`r3`, `r12`, `lr`, `pc`, `xPSR`). The compiler-generated code saves `r4`–`r11` only if the ISR uses them. That is a deliberate fit with the AAPCS.
- **Writing assembly** that is called from C (or calls C): you must preserve `r4`–`r11` and keep SP aligned, or C code breaks in subtle ways.
- **Performance:** functions with four or fewer integer arguments pass everything in registers; a fifth argument goes on the stack. Passing a pointer to a struct instead of many arguments is cheaper.
- **Struct returns:** small structs (≤ 4 bytes on AArch32) come back in `r0`; larger ones through memory the caller provides.
- **Float ABI:** `-mfloat-abi=hard` passes floats in FPU registers; `softfp` uses FPU instructions but passes floats in integer registers; mixing objects built with `hard` and `soft`/`softfp` fails to link.
- **Context switches:** an RTOS on Cortex-M saves `r4`–`r11` (and `s16`–`s31` if the FPU is used) in software in PendSV, because the hardware already saved the rest.
- **Debugging:** in a crash dump, `lr` and the stacked frame let you reconstruct the call chain.

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
