---
title: Interrupt Latency on Cortex-M, Explained
tag: ARM Cortex-M
desc: What contributes to interrupt latency and jitter on Cortex-M, how to measure it, and how to reduce it.
date: 2026-11-20
order: 5
---
"What is interrupt latency and how would you reduce it?" sounds simple, but good answers distinguish **latency** from **jitter** and know where the cycles actually go.

## Definitions

- **Interrupt latency**: the time from the interrupt request being asserted to the first instruction of the ISR executing.
- **Response time**: latency plus the time the ISR takes to do the useful part of its work (for example, toggling an output).
- **Jitter**: the variation in latency from one interrupt to the next. In control systems, jitter is often worse than a constant delay.

## Where the cycles go on Cortex-M

With zero-wait-state memory and nothing else happening, Cortex-M3/M4 take **12 cycles** from request to the first ISR instruction (Cortex-M0 takes 16, M0+ 15). In those cycles the core:

1. finishes or abandons the current instruction (multi-cycle instructions like `LDM` can be interrupted and resumed),
2. pushes the 8-word stack frame (`R0`–`R3`, `R12`, `LR`, `PC`, `xPSR`),
3. fetches the vector in parallel and refills the pipeline.

Real systems add more:

| Source | Typical cost |
|---|---|
| Flash wait states on vector and code fetch | Several cycles per fetch at high clock rates (reduced by ART/caches) |
| FPU context (Cortex-M4F/M7) | Extra 17 words if not deferred by lazy stacking |
| Higher-priority ISR running | Its whole remaining duration |
| Interrupts disabled in a critical section | Up to the longest critical section in the system |
| Bus contention with DMA | A few cycles |
| Exit from a low-power mode | Microseconds (clock and regulator restart) |
| RTOS overhead before the "real" handler | Often 0 for the ISR itself; matters for the handler task |

## How to measure it

The simplest reliable method uses a GPIO and an oscilloscope or logic analyser:

1. Trigger the interrupt from an external signal (or another timer output).
2. In the first line of the ISR, set a GPIO high using an atomic set register (e.g. `GPIOx->BSRR`).
3. Measure the time between the trigger edge and the GPIO edge on the scope. Use persistence mode to see the jitter.

Alternatively, use the **DWT cycle counter** (`DWT->CYCCNT`) and timer input capture to timestamp the event and the ISR entry with cycle accuracy.

## How to reduce latency and jitter

**Keep critical sections short.** The worst-case latency of every interrupt includes the longest section with interrupts disabled. Audit `__disable_irq()` calls and RTOS critical sections.

**Mask selectively.** Use `BASEPRI` to block only interrupts that share data with the critical section. FreeRTOS does this: interrupts above `configMAX_SYSCALL_INTERRUPT_PRIORITY` (numerically below it) are never masked by the kernel, so they are not delayed by it. Such interrupts must not call RTOS APIs.

**Get priorities right.** Give the most time-critical interrupt the highest priority (lowest number) and keep everything at that level short. Put long work in lower-priority ISRs or tasks.

**Keep ISRs short.** A long low-priority ISR does not delay higher-priority ones (they pre-empt it), but it delays everything at its own level and below.

**Run from fast memory.** Place the vector table and critical ISRs in RAM, ITCM or a cached region, and enable the flash accelerator. On Cortex-M7, use TCM to avoid cache-miss jitter.

**Avoid FPU context in the hot ISR.** If the ISR does not use floating point, lazy stacking means it does not pay the FPU stacking cost. Be aware that compilers can use FPU registers for unexpected things, such as `memcpy`.

**Do not sleep too deeply.** If the deadline is shorter than the wake-up time of a deep-sleep mode, use a lighter sleep mode.

**Use hardware instead.** The best latency is no interrupt at all: timers can toggle outputs, DMA can move data, and peripheral interconnects (STM32 timers triggering ADCs, nRF PPI/DPPI) link events directly in hardware with zero jitter.

## A model interview answer

> "Interrupt latency is the delay from the request to the first ISR instruction. On a Cortex-M4 the hardware minimum is 12 cycles for stacking and vector fetch, but in practice flash wait states, higher-priority ISRs and, most of all, code that disables interrupts add to it, and they also cause jitter. I measure it with a GPIO toggle at ISR entry on a scope. To reduce it, I keep critical sections short and use BASEPRI instead of global disables, assign priorities by deadline, keep ISRs short and defer work, place hot handlers in RAM or TCM, and where possible let hardware like DMA or timer triggers do the job."
