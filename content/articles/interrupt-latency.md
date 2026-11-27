---
title: Interrupt Latency on Cortex-M, Explained
tag: ARM Cortex-M
desc: What contributes to interrupt latency and jitter on Cortex-M, how to measure it, and how to reduce it.
date: 2026-11-20
order: 5
---

**Interrupt latency** is the time from an interrupt request to the first ISR instruction. **Response time** includes the time needed to perform the required action. **Jitter** is the variation in latency.

## Cortex-M interrupt flow

```text
Peripheral IRQ → NVIC → CPU stacks registers
→ Fetch ISR address from vector table → Execute ISR
```

Ideal minimum entry latency with zero-wait-state memory: Cortex-M0 = 16 cycles, M0+ = 15, M3/M4 = 12.

The hardware stacks R0–R3, R12, LR, PC and xPSR. FPU context, if needed, adds overhead; lazy stacking can defer it.

## What increases latency?

- Disabled interrupts or higher-priority ISRs.
- Flash wait states, cache misses and DMA bus contention.
- FPU context stacking and low-power wake-up delays.

## How to measure

Trigger an interrupt using an external signal and toggle a GPIO at ISR entry. Measure the time between edges on an oscilloscope. Repeated measurements show jitter. Where supported, use the DWT cycle counter with an event timestamp.

## How to reduce latency

- Keep ISRs and critical sections short; defer long work to tasks.
- Assign priorities according to deadlines (lower number means higher priority).
- Use BASEPRI on supported cores instead of global masking. FreeRTOS ISRs above the syscall-priority threshold must not call RTOS APIs.
- Place critical code in fast RAM or TCM; use lazy FPU stacking where supported.
- Use timers or DMA for time-critical actions instead of software interrupts.

**Interview answer:** Cortex-M4 has an ideal entry latency of 12 cycles, but masking, preemption, memory delays and wake-up time increase real latency. Measure it using GPIO and minimise critical sections.
