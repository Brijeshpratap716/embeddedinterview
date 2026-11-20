---
slug: rtos
title: RTOS & Real-Time Systems
icon: ⏱️
level: Intermediate
order: 6
desc: Scheduling, tasks, semaphores vs mutexes, priority inversion, deadlock, queues, FreeRTOS and Zephyr internals.
---
RTOS questions check two things: whether you know the vocabulary, and whether you can reason about timing and concurrency bugs. Examples use FreeRTOS names, but the ideas apply to Zephyr, ThreadX and others.

### What is an RTOS and how is it different from a general-purpose OS? {E}
A Real-Time Operating System guarantees that tasks respond within bounded, predictable time. The goal is **determinism**, not average throughput. Compared with Linux or Windows, an RTOS has:

- a small, often fully pre-emptive priority-based scheduler,
- bounded interrupt and context-switch latency,
- tiny footprint (a few KB of flash),
- usually no MMU-based process isolation, and tasks share one address space.

Examples: FreeRTOS, Zephyr, ThreadX (Eclipse ThreadX), VxWorks, QNX, embOS.

### What is the difference between hard, firm and soft real-time? {E}
- **Hard**: missing a deadline is a system failure (airbag deployment, motor commutation, pacemaker).
- **Firm**: a late result is useless but not catastrophic; occasional misses are tolerated (video frame decoding).
- **Soft**: late results still have reduced value (UI responsiveness, audio buffering with retries).

Real-time does not mean fast; it means *on time, every time*.

### What are the states of a task? {E}
In FreeRTOS terms:

- **Running**: currently executing (one per core).
- **Ready**: able to run, waiting for the CPU.
- **Blocked**: waiting for an event (delay, semaphore, queue) with an optional timeout.
- **Suspended**: explicitly removed from scheduling with `vTaskSuspend` until resumed.

A deleted task waits for the idle task to free its memory.

### What is pre-emptive versus cooperative scheduling? {E}
In **pre-emptive** scheduling, the kernel switches tasks whenever a higher-priority task becomes ready (from an ISR or another task), even mid-function. In **cooperative** scheduling, a task runs until it voluntarily yields or blocks. Pre-emptive gives better worst-case response for high-priority work; cooperative needs fewer locks but one misbehaving task stalls everything. FreeRTOS supports both (`configUSE_PREEMPTION`).

### What is time slicing / round-robin scheduling? {E}
When several ready tasks share the highest priority, the scheduler gives each one a time slice (one tick in FreeRTOS) and rotates between them. Tasks of different priorities are never time-sliced against each other: the higher one always runs. Enabled by `configUSE_TIME_SLICING`.

### What is a context switch and what is saved? {M}
A context switch saves the state of the running task and restores another. On Cortex-M:

1. Hardware stacks `R0`–`R3`, `R12`, `LR`, `PC`, `xPSR` when PendSV is entered.
2. The PendSV handler pushes `R4`–`R11` (and `S16`–`S31` if the task used the FPU) onto the task's stack, saves the PSP into the task control block (TCB),
3. selects the next task, loads its PSP from its TCB, pops `R4`–`R11`, and
4. returns with `EXC_RETURN`, so hardware pops the rest.

Cost is typically well under a microsecond on a 100+ MHz Cortex-M.

### What is the difference between a mutex and a binary semaphore? {M}
| | Mutex | Binary semaphore |
|---|---|---|
| Purpose | Mutual exclusion around a resource | Signalling / synchronisation |
| Ownership | Has an owner; only the owner can release it | No owner; anyone can give it |
| Priority inheritance | Yes (in FreeRTOS, Zephyr) | No |
| Use from ISR | No | Yes (`xSemaphoreGiveFromISR`) |
| Recursive version | Yes | No |

Use a mutex to protect a shared bus or data structure. Use a semaphore (or better, a direct task notification) for "ISR tells task data is ready".

### What is a counting semaphore? {E}
A semaphore with a count greater than one. Two uses:

1. **Resource counting**: initialise to N for N identical resources (buffers, DMA channels); each `take` decrements, each `give` increments, `take` blocks at zero.
2. **Event counting**: an ISR gives once per event so the task does not lose events that arrive faster than it processes them.

### What is priority inversion? {M}
A high-priority task is blocked waiting for a resource held by a low-priority task, while a **medium-priority** task (which does not need the resource) pre-empts the low-priority one. The high-priority task now effectively waits for the medium one, which breaks the priority scheme and can be unbounded.

The famous example is the Mars Pathfinder resets in 1997, fixed by turning on priority inheritance for a VxWorks mutex.

### How do priority inheritance and priority ceiling solve priority inversion? {H}
- **Priority inheritance**: while a low-priority task holds a mutex that a higher-priority task is waiting for, the holder temporarily runs at the waiter's priority. It cannot be pre-empted by medium tasks, so it finishes quickly and releases the mutex. FreeRTOS mutexes do this automatically.
- **Priority ceiling protocol**: each mutex has a ceiling equal to the highest priority of any task that uses it; a task that takes the mutex immediately runs at the ceiling. It also prevents deadlocks between mutexes and bounds blocking to one critical section, at the cost of configuring ceilings.

Neither helps if a task holds a lock for too long; keep critical sections short.

### What is a deadlock and how do you prevent it? {M}
A deadlock is when two or more tasks each wait for a resource the other holds, so none can proceed. It requires all four Coffman conditions: mutual exclusion, hold and wait, no pre-emption, and circular wait.

Prevention:
- **Lock ordering**: always acquire mutexes in the same global order (breaks circular wait).
- Take all needed locks at once, or none.
- Use timeouts on `take` and handle failure.
- Minimise nested locking; prefer message passing to shared data.

### What is a livelock and what is starvation? {M}
- **Livelock**: tasks keep running but make no progress, for example two tasks that both back off and retry in lock-step forever.
- **Starvation**: a task never gets the CPU or the resource because higher-priority tasks always win. In a fixed-priority RTOS, a high-priority task that never blocks starves everything below it, including the idle task.

### What is a message queue and when should you use one? {E}
A thread-safe FIFO that copies fixed-size items from sender to receiver, with blocking and timeouts on both ends. Queues decouple producers and consumers, buffer bursts and avoid shared global data. In FreeRTOS, `xQueueSend` copies the item by value, so send a pointer if the data is large (and manage its ownership carefully). An ISR uses `xQueueSendFromISR`.

### What are event groups / event flags? {M}
A set of bits that tasks can wait on with AND or OR semantics: "wake me when bits 0 and 2 are both set" or "when any of bits 0–3 is set". Useful for synchronising one task with several conditions, or several tasks at a barrier (`xEventGroupSync`). Unlike a queue, setting a bit that is already set loses the second event.

### What are FreeRTOS task notifications? {M}
Each task has a built-in 32-bit notification value (an array of them since FreeRTOS 10.4). Another task or an ISR can increment it, set bits, or overwrite it, and the task can block on it. They are faster and use less RAM than a semaphore or queue because there is no separate kernel object, but only one task (the owner) can wait, and they cannot buffer multiple data items. They are the recommended way for an ISR to wake a single handler task.

### Why must you use the FromISR API variants in an interrupt? {M}
Normal API functions may block, and an ISR must never block. The `...FromISR` versions never block, and instead of switching context immediately they report through `pxHigherPriorityTaskWoken` that a higher-priority task became ready:

```c
void UART_IRQHandler(void)
{
    BaseType_t woken = pdFALSE;
    vTaskNotifyGiveFromISR(rx_task, &woken);
    portYIELD_FROM_ISR(woken);   /* switch on ISR exit if needed */
}
```

Also, only interrupts at or below `configMAX_SYSCALL_INTERRUPT_PRIORITY` (numerically ≥ on Cortex-M) may call any FreeRTOS API.

### What is the tick and what is a tickless idle mode? {M}
The tick is a periodic interrupt (often SysTick at 1 kHz) that the kernel uses to track time, expire delays and time-slice. In **tickless idle** mode (`configUSE_TICKLESS_IDLE`), when only the idle task is ready, the kernel stops the periodic tick, programs a timer to wake at the next scheduled event, enters a low-power mode, and corrects the tick count on wake-up. It saves significant power for battery devices.

### What is the idle task and what is it used for? {E}
The idle task runs at the lowest priority whenever no other task is ready. It frees memory of deleted tasks and runs the idle hook, which applications use to enter low-power sleep (`__WFI()`), kick a watchdog after checks, or measure CPU load (time spent in idle vs total). It must never block.

### How do you choose task priorities? Explain rate-monotonic scheduling. {H}
**Rate-monotonic scheduling (RMS)** assigns higher fixed priority to tasks with shorter periods. For n independent periodic tasks with deadlines equal to periods, RMS is optimal among fixed-priority schemes and the set is guaranteed schedulable if total CPU utilisation U = Σ(Cᵢ/Tᵢ) ≤ n(2^(1/n) − 1), which tends to about 69% for large n. Above that bound a set may still be schedulable; check with response-time analysis.

**Deadline-monotonic** uses relative deadline instead of period. **EDF (earliest deadline first)** is a dynamic-priority scheme that can schedule up to 100% utilisation but is harder to analyse under overload.

### How much stack does a task need and how do you size it? {M}
Start from the worst-case call depth of the task's code (locals, saved registers, arguments) plus the context frame (16 words, plus 34 more if it uses the FPU). Interrupts run on the main stack on Cortex-M, so they are not included. Then measure: run the system under worst-case conditions and check `uxTaskGetStackHighWaterMark()`, keeping a safety margin of 20–30%. Enable `configCHECK_FOR_STACK_OVERFLOW` during development. Avoid large local arrays and `printf`-family functions in small tasks.

### What are software timers in an RTOS? {E}
Callbacks run by the kernel after a delay, once or periodically, without a dedicated task per timer. In FreeRTOS they all execute in the **timer service (daemon) task**, so callbacks must be short and must not block, or every other timer is delayed. Commands to start or stop timers go through a queue to that task.

### What is the difference between vTaskDelay and vTaskDelayUntil? {M}
- `vTaskDelay(n)` blocks for n ticks **from now**. If the task's own work takes variable time, its period drifts.
- `vTaskDelayUntil(&last, period)` (or `xTaskDelayUntil`) blocks until an **absolute** time `last + period` and updates `last`, giving a fixed-frequency loop with no drift.

Use `vTaskDelayUntil` for periodic control loops and sampling.

### How do you protect a shared resource between a task and an ISR? {M}
A mutex cannot be used from an ISR. Options:

- Disable interrupts (or raise `BASEPRI`) around the task's short access: `taskENTER_CRITICAL()` / `taskEXIT_CRITICAL()`. In the ISR, use `taskENTER_CRITICAL_FROM_ISR()` if a higher-priority ISR can also touch it.
- Make the ISR the only writer and use a lock-free single-producer/single-consumer ring buffer.
- Pass data through a queue or stream buffer and let only the task own the resource.

### What are common RTOS design mistakes? {M}
- Too many tasks; each one costs a stack and adds context switches.
- Busy-wait loops in tasks, which starve lower priorities.
- Calling blocking APIs or `printf` from ISRs.
- Holding mutexes while doing slow I/O, or taking several mutexes in different orders.
- Using global variables between tasks without protection.
- Getting the interrupt priority vs `configMAX_SYSCALL_INTERRUPT_PRIORITY` relationship wrong, causing random corruption.
- Not checking API return values (queue full, timeout).

### How does Zephyr differ from FreeRTOS? {M}
FreeRTOS is a small kernel (scheduler, queues, semaphores, timers) with optional libraries; you bring your own drivers, usually from the silicon vendor. **Zephyr** is a complete RTOS project under the Linux Foundation: it uses **Kconfig** and **devicetree** (like Linux) for configuration, has a unified driver model, networking (IPv4/v6, Bluetooth LE, Thread), file systems, a shell, user-mode thread isolation with the MPU, and builds with CMake and the `west` tool. Zephyr has a steeper learning curve but much more built in.
