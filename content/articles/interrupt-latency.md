---
title: Interrupt Latency on Cortex-M, Explained
tag: ARM Cortex-M
desc: What contributes to interrupt latency and jitter on Cortex-M, how to measure it, and how to reduce it.
date: 2026-11-20
order: 5
---

**Interrupt latency:** Time from an interrupt request to the first ISR instruction. **Jitter:** Variation in latency. **Response time:** Time until the required action occurs.

## Cortex-M interrupt flow

Peripheral → NVIC → CPU saves R0–R3, R12, LR, PC and xPSR → Fetch ISR address → Execute ISR.

Ideal entry latency (zero memory wait states): Cortex-M0 = 16 cycles, M0+ = 15, M3/M4 = 12.

## Measure using a GPIO

Example STM32 EXTI interrupt (registers and handler depend on the MCU):

```c
void EXTI0_IRQHandler(void)
{
    GPIOA->BSRR = (1u << 5);  // GPIO high
    EXTI->PR = (1u << 0);     // Clear pending IRQ (W1C)
    GPIOA->BSRR = (1u << 21); // GPIO low
}
```

Configure the GPIO and EXTI first. On an oscilloscope, measure from the external interrupt edge to the GPIO rising edge. The GPIO write adds a small measurement overhead.

## Causes and solutions

| Cause | Solution |
|---|---|
| Disabled interrupts | Short critical sections; BASEPRI where supported |
| Higher-priority ISR | Keep ISRs short and assign priorities by deadline |
| Flash wait states / bus contention | Fast RAM or TCM |
| FPU context / sleep wake-up | Lazy stacking / suitable sleep mode |

Use DMA or hardware timers where possible; defer lengthy work to RTOS tasks.
