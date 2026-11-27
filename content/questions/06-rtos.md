---
slug: rtos
title: RTOS & Real-Time Systems
icon: ⏱️
level: Intermediate
order: 6
desc: Scheduling, task states, context switches, semaphores vs mutexes, priority inversion and inheritance, deadlock, queues, notifications, RMS and response-time analysis, stacks, timers, SMP, FreeRTOS and Zephyr internals.
---
RTOS questions check two things: whether you know the vocabulary, and whether you can reason about timing and concurrency bugs. Examples use FreeRTOS names, but the ideas apply to Zephyr, ThreadX, embOS, VxWorks and QNX. Each answer gives the one-line version first, then the explanation and the follow-ups.

### What is an RTOS and how is it different from a general-purpose OS? {E}
An RTOS (Real-Time Operating System) manages tasks, interrupts and resources with the goal of predictable timing. Correctness includes both the result and whether it is produced by the required deadline.

#### 1. Example

A motor controller must update its output every 1 ms. An RTOS can schedule a high-priority control task while lower-priority logging runs in the available time.

| RTOS | General-purpose OS |
|---|---|
| Predictability and bounded latency emphasized | Throughput, fairness and interactive performance emphasized |
| Often fixed-priority preemptive scheduling | Multiple scheduling policies |
| Small, configurable kernel common | Rich process, filesystem and networking facilities common |

Linux can also support real-time scheduling and PREEMPT_RT; an RTOS label alone does not guarantee a system meets its deadlines.

#### 2. Main services

Tasks and scheduling, queues, semaphores, mutexes, timers and interrupt-safe signaling. An RTOS is often selected when a super loop can no longer manage independent deadlines conveniently.

**Interview takeaway:** Real-time means meeting timing requirements, not simply being fast. Analyze worst-case execution, blocking and interrupt latency.

### What is the difference between hard, firm and soft real-time? {E}
Real-time systems are classified by the consequence of missing a deadline.

| Category | Missed deadline | Example |
|---|---|---|
| Hard | Violates a required timing guarantee; may be unacceptable | Safety-critical control action |
| Firm | Late result loses its value | A stale sensor frame discarded by a processing pipeline |
| Soft | Late result still has some value, but quality suffers | Interactive audio/video |

#### 1. Example timeline

```text
Release -------- required deadline -------- late completion
Hard:  timing requirement violated
Firm:  discard result
Soft:  use result if appropriate, reduced quality
```

The classification belongs to the application requirement, not automatically to a device or RTOS.

#### 2. Engineering implications

Hard real-time requires defensible worst-case timing analysis and controlled resources. Firm systems may drop expired jobs. Soft systems may use buffering and quality adaptation.

**Interview takeaway:** Classify the consequence of lateness before choosing scheduling policy, priority and recovery behavior.

### What are the states of a task? {E}
An RTOS task typically transitions between Ready, Running, Blocked and Suspended states.

<div style="max-width:650px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 196" width="100%" role="img" aria-label="Ready task scheduled to running, preempted back to ready, blocked on wait, then made ready by event">
<rect x="8" y="25" width="110" height="33" rx="5" fill="#3b82f6" fill-opacity=".13" stroke="#3b82f6"/><text x="63" y="46" text-anchor="middle" font-size="11" font-weight="600" fill="currentColor">READY</text><rect x="222" y="25" width="110" height="33" rx="5" fill="#3b82f6" fill-opacity=".13" stroke="#3b82f6"/><text x="277" y="46" text-anchor="middle" font-size="11" font-weight="600" fill="currentColor">RUNNING</text><rect x="222" y="139" width="110" height="33" rx="5" fill="#3b82f6" fill-opacity=".13" stroke="#3b82f6"/><text x="277" y="160" text-anchor="middle" font-size="11" font-weight="600" fill="currentColor">BLOCKED</text><rect x="8" y="139" width="110" height="33" rx="5" fill="#3b82f6" fill-opacity=".13" stroke="#3b82f6"/><text x="63" y="160" text-anchor="middle" font-size="11" font-weight="600" fill="currentColor">SUSPENDED</text><path d="M118 34 H222 m-5-4 5 4-5 4 M222 50 H118 m5-4 -5 4 5 4 M277 58 V139 m-4-5 4 5 4-5 M222 155 H151 V73 H63 V58 m-4 5 4-5 4 5 M45 58 V139 m-4-5 4 5 4-5 M81 139 V58 m-4 5 4-5 4 5" fill="none" stroke="currentColor"/><g fill="currentColor" font-size="10"><text x="170" y="24" text-anchor="middle">Dispatch</text><text x="170" y="66" text-anchor="middle">Preempt / yield</text><text x="286" y="99">Wait</text><text x="158" y="110">Event</text><text x="36" y="103" text-anchor="end">Suspend</text><text x="89" y="103">Resume</text></g></svg></div>

#### 1. Meaning

| State | Meaning |
|---|---|
| Running | Currently executing on a CPU |
| Ready | Eligible to execute |
| Blocked | Waiting for time or an event/resource |
| Suspended | Explicitly removed from normal scheduling |

#### 2. Example

A UART worker blocks waiting on a queue. An ISR posts a message, making the worker ready. If it has higher priority than the current task, the scheduler may dispatch it immediately.

A delayed task is blocked, not necessarily suspended. State terminology differs across kernels; in SMP more than one task can run simultaneously.

**Interview takeaway:** Ready means eligible, not currently executing. A blocked task consumes no CPU time while waiting for its condition.

### What is pre-emptive versus cooperative scheduling? {E}
Preemptive scheduling allows the scheduler to replace the currently running task when a higher-priority task becomes ready. Cooperative scheduling depends on tasks voluntarily yielding or blocking, subject to the kernel's rules.

#### 1. Example

```text
Low-priority task runs
High-priority task becomes ready

Preemptive: high-priority task runs immediately when eligible
Cooperative: low-priority task runs until a scheduling point
```

Interrupt handlers can still interrupt ordinary task execution in either model.

| Preemptive | Cooperative |
|---|---|
| Better responsiveness to urgent ready tasks | Simpler reasoning about task-to-task interleaving |
| Requires synchronization for shared data | Long tasks can delay other ready tasks |
| More possible context switches | Depends on bounded voluntary scheduling points |

#### 2. Embedded use

A high-priority control task that wakes from a timer can preempt a background logger in a preemptive RTOS. A cooperative super loop instead depends on each service returning quickly.

**Interview takeaway:** Preemption improves responsiveness but does not eliminate blocking, interrupt masking or priority inversion. Cooperative scheduling still needs interrupt-safe sharing.

### What is time slicing / round-robin scheduling? {E}
Round-robin scheduling gives eligible tasks turns on the CPU. In a fixed-priority RTOS, time slicing commonly applies to tasks of equal priority.

#### 1. Example

```text
Time:   0     1     2     3     4 ms
Task:   | A   | B   | A   | B   |
```

Both tasks are ready at the same priority, and each time slice is 1 ms in this simplified example.

#### 2. When does the scheduler change task?

A task can yield, block or exhaust its slice. A higher-priority task becoming ready may preempt the current task before its slice finishes.

#### 3. FreeRTOS

With preemptive scheduling and time slicing enabled, equal-priority ready tasks can rotate at tick boundaries. Exact scheduling behavior depends on the kernel configuration and port; a tick is not necessarily a guaranteed uninterrupted time slice.

**Interview takeaway:** Round-robin improves sharing among peers. It does not mean every task receives equal CPU time regardless of priority or blocking behavior.

### What is a context switch and what is saved? {M}
A context switch saves enough of the outgoing execution context to resume it later and restores another task's context.

#### 1. Cortex-M example

```text
Task A runs using PSP_A
Exception entry stacks R0-R3, R12, LR, PC, xPSR
PendSV saves additional registers (typically R4-R11)
Scheduler stores A's PSP and selects B
Restore B's PSP and saved registers
Exception return resumes task B
```

The exact context depends on architecture, ABI, floating-point use and RTOS port.

#### 2. What is saved?

General registers, stack pointer, return/execution state and additional architectural state when required. A task control block records the saved stack pointer, scheduling state and metadata. An MPU-aware port may also update protection configuration.

#### 3. Cost

Switching consumes CPU time and may disrupt cache locality. Measure on the target with representative tasks and interrupt load.

**Interview takeaway:** A context switch preserves execution state, not the entire contents of memory. Hardware and software divide the saving/restoring work according to the port.

### How does an RTOS scheduler pick the next task to run? {M}
A typical fixed-priority RTOS scheduler selects the highest-priority ready task. Tasks waiting for events or delays are not eligible.

#### 1. Example

| Task | Priority (higher number = higher here) | State |
|---|---:|---|
| Control | 4 | Blocked |
| Communication | 3 | Ready |
| Logging | 1 | Ready |

Communication runs because Control is blocked. When Control becomes ready, a preemptive scheduler may switch to it.

#### 2. Scheduler mechanism

Ready queues or bitmaps track eligible tasks by priority. Event completion or timer expiry changes a task's state, and scheduling selects the next task. Equal-priority policy can be round-robin or another configured rule.

#### 3. Practical caveats

RTOS priority numbering varies: FreeRTOS task priorities use higher numbers for higher task priority, whereas Cortex-M interrupt priorities use lower numerical values for higher urgency. Do not confuse the two. Scheduler locks, interrupt masks and SMP affinity can affect dispatch.

**Interview takeaway:** Priority is considered only among eligible tasks. Blocking a high-priority task allows lower-priority ready tasks to execute.

### What is the difference between a mutex and a binary semaphore? {M}
A mutex protects a shared resource through ownership; a binary semaphore represents a zero-or-one availability/event state and is commonly used for signaling.

| Mutex | Binary semaphore |
|---|---|
| Owned by acquiring task | Usually no task ownership |
| Released by owner | Can be signaled by another permitted context |
| Often supports priority inheritance | Usually no priority inheritance |
| Protects shared resources | Signals events or availability |

#### 1. Mutex example

```c
if (xSemaphoreTake(bus_mutex, timeout) == pdTRUE) {
    i2c_transfer();
    xSemaphoreGive(bus_mutex);
}
```

The task owns the bus while performing the transfer. Use a bounded timeout and release on every relevant path.

#### 2. Binary semaphore example

A DMA completion ISR gives a binary semaphore using the appropriate FromISR API. A worker waits for it, then processes the completed buffer. A binary semaphore cannot count multiple pending events; repeated signals can merge.

**Interview takeaway:** Use a mutex for task-owned mutual exclusion and a semaphore or notification for signaling. Do not acquire a blocking mutex in an ISR.

### What is a counting semaphore? {E}
A counting semaphore stores a count representing available resources or pending events. Taking the semaphore decrements a positive count; giving it increments the count up to a configured maximum.

#### 1. Resource example

A system has three identical buffer resources. Initialize the semaphore count to 3. Each task takes one token before reserving a buffer and gives it back after releasing that buffer.

```text
Initial count: 3
Task A takes: 2
Task B takes: 1
Task C takes: 0
Task D waits
Task A gives: a waiting task can proceed
```

A separate allocator or synchronized free list identifies the actual resource; a semaphore alone does not identify which buffer is free.

#### 2. FreeRTOS API

```c
SemaphoreHandle_t sem = xSemaphoreCreateCounting(3, 3);
```

Check creation failure. Use xSemaphoreTake and xSemaphoreGive in supported task contexts; use ISR variants where permitted.

**Interview takeaway:** A binary semaphore carries at most one pending token. A counting semaphore preserves multiple tokens up to capacity, but can overflow if producers outpace consumers.

### What is priority inversion? {M}
Priority inversion occurs when a high-priority task is blocked on a resource owned by a lower-priority task. A medium-priority task can prolong the delay by preempting the resource owner.

#### 1. Example

```text
L: low-priority task locks mutex
H: high-priority task tries mutex, blocks
M: medium-priority task preempts L
H: cannot run until L gets CPU and unlocks
```

The medium-priority task indirectly delays the higher-priority task even though it does not use the mutex.

#### 2. Priority inheritance

When H blocks on L's mutex, the kernel may temporarily raise L's effective priority to H's. L completes the critical section, releases the mutex, and H can proceed. The inherited priority is removed according to the kernel's protocol.

#### 3. Limitations

Inheritance reduces interference from intermediate-priority tasks but cannot eliminate the actual time needed to release the resource. Long critical sections, nested locks and unbounded I/O can still violate deadlines.

**Interview takeaway:** Priority inversion is a resource dependency problem, not merely incorrect priority assignment. Use appropriate mutex protocols and keep critical sections bounded.

### How do priority inheritance and priority ceiling solve priority inversion? {H}
Priority inheritance and priority ceiling are synchronization protocols intended to bound priority inversion in real-time systems.

#### 1. Priority inheritance

If high-priority H waits for a mutex held by low-priority L, the kernel temporarily raises L's effective priority. Medium-priority M can no longer preempt L merely because L originally had lower priority. L releases the mutex and H proceeds.

#### 2. Priority ceiling

A resource is assigned a ceiling derived from the highest-priority task that can use it. Ceiling protocols impose scheduling or lock-acquisition rules based on that ceiling. In the immediate-ceiling variant, a task acquiring a resource executes at an appropriately raised effective priority while holding it.

Properly configured ceiling protocols can bound blocking and prevent certain deadlocks under their assumptions.

| Inheritance | Ceiling |
|---|---|
| Raises priority when contention occurs | Uses predefined resource ceilings |
| Adapts to actual waiters | Requires knowledge of resource users |
| May involve nested dependency chains | Can offer stronger analytical bounds |

FreeRTOS mutexes implement a simplified priority-inheritance mechanism, not a general priority-ceiling protocol. Inspect the actual kernel's behavior for nested mutexes.

**Interview takeaway:** Neither protocol removes the critical-section execution time. Choose a supported protocol and include blocking in schedulability analysis.

### What is a deadlock and how do you prevent it? {M}
Deadlock occurs when tasks wait indefinitely for resources that cannot become available because of their dependencies.

#### 1. Example

```text
Task A owns lock X, waits for Y
Task B owns lock Y, waits for X
A --> Y --> B --> X --> A
```

Neither can proceed to release its held lock.

#### 2. Four classical necessary conditions

Mutual exclusion, hold-and-wait, no forced preemption of resources, and circular wait. Removing a necessary condition prevents that class of deadlock.

#### 3. Prevention using lock ordering

```c
mutex_lock(&lock_x);
mutex_lock(&lock_y);

// Access both protected resources.

mutex_unlock(&lock_y);
mutex_unlock(&lock_x);
```

Every task needing both locks must acquire X before Y. Handle acquisition errors and release successfully acquired locks on every error path.

#### 4. Other techniques

Avoid nested locks when possible, do not hold locks across unrelated blocking operations, use a single owner task for a peripheral, and use timeout/recovery mechanisms with well-defined cleanup. A timeout can detect or break some waits but does not automatically restore consistency.

**Interview takeaway:** Draw the resource dependency graph and eliminate cycles through a consistent locking design.

### What is a livelock and what is starvation? {M}
**Short answer:** In a **livelock**, tasks keep running and changing state but make no progress, for example two tasks that detect a conflict, both back off and retry at the same moment forever. **Starvation** means a task never gets the CPU or a resource because others always win; in a fixed-priority RTOS, a high-priority task that never blocks starves every lower-priority task, including the idle task.

**Livelock examples and fixes**

- Two tasks using "try lock A then B; if B fails, release A and retry" in lock-step: add **random back-off** or a fixed lock order.
- Network devices retransmitting after collisions at the same time: Ethernet's **randomised exponential back-off** exists to avoid exactly this.
- Two tasks politely yielding to each other forever.

**Starvation examples and fixes**

| Cause | Fix |
|---|---|
| High-priority task busy-waits/polls | make it block on events; never poll in a high-priority task |
| Too much work at high priority | move work to lower priorities, reduce rates, or a faster CPU |
| Unfair locks (spinlocks, readers starving writers) | fair locks (ticket, FIFO), writer preference |
| Aging not used in priority schedulers | increase the priority of long-waiting tasks over time (general-purpose OSes) |

**Symptoms of starvation in an RTOS:** the idle task never runs (CPU load 100%), the watchdog starts resetting the system, low-priority logging or communication stops, and `vApplicationIdleHook` (where you might sleep or kick a watchdog) never executes.

**Monitoring:** measure CPU load and per-task run time (`configGENERATE_RUN_TIME_STATS`), and track the stack and execution time of high-priority tasks.

### What is a message queue and when should you use one? {E}
**Short answer:** A message queue is a thread-safe FIFO that copies fixed-size items from senders to receivers, with blocking and timeouts on both ends. Queues decouple producers and consumers, absorb bursts, and avoid shared global data and locks. In FreeRTOS, `xQueueSend` **copies** the item into the queue, so for large data send a pointer (and define who owns and frees the buffer).

```c
typedef struct { uint8_t type; int16_t value; uint32_t timestamp; } sensor_msg_t;

QueueHandle_t q = xQueueCreate(16, sizeof(sensor_msg_t));

/* producer task */
sensor_msg_t m = { .type = 1, .value = read_temp(), .timestamp = xTaskGetTickCount() };
if (xQueueSend(q, &m, pdMS_TO_TICKS(5)) != pdTRUE) { /* queue full: count/drop/handle */ }

/* consumer task */
sensor_msg_t r;
if (xQueueReceive(q, &r, portMAX_DELAY) == pdTRUE) process(&r);
```

**When to use a queue**

- One or more producers send data/commands to a task that owns a resource (e.g. all display updates go to the display task).
- Interrupts hand data to tasks (`xQueueSendFromISR`).
- You want **back-pressure**: a full queue blocks or fails the sender instead of losing data silently.

**Design points**

- **Sizing:** depth = worst-case burst rate × worst-case consumer delay, plus margin. Monitor the high-water mark (`uxQueueMessagesWaiting`).
- **Copy vs reference:** copying small items (≤ 16–32 bytes) is simple and safe; for large buffers, send pointers from a pool and pass ownership.
- **Timeouts:** always choose a timeout and handle failure.
- **Queue sets** (FreeRTOS) or `k_poll` (Zephyr) let one task wait on several queues/semaphores.

**Related FreeRTOS objects**

- **Stream buffers:** a byte stream (like a pipe) for one writer and one reader, efficient for UART data.
- **Message buffers:** variable-length messages built on stream buffers.
- **Mailbox:** a queue of length 1 that is overwritten (`xQueueOverwrite`) to always hold the latest value.

### What are stream buffers and message buffers, and when are they better than queues? {M}
**Short answer:** FreeRTOS **stream buffers** pass a continuous stream of bytes from exactly one writer to exactly one reader (like a pipe), and the reader can block until a trigger level of bytes is available. **Message buffers** are built on stream buffers and pass variable-length messages (each with a length prefix). Both are lighter than queues because they assume a single writer and single reader (no locking among multiple writers), and they copy only as many bytes as needed rather than fixed-size items.

| | Queue | Stream buffer | Message buffer |
|---|---|---|---|
| Item | fixed size | bytes | variable-length messages |
| Writers/readers | many/many | one/one | one/one |
| Typical use | commands, events | UART/USB byte streams, audio | packets, variable-size records |
| ISR use | yes | yes (one side in an ISR) | yes |
| Overhead | higher | low | low |

```c
StreamBufferHandle_t rx = xStreamBufferCreate(256, 1);    /* size, trigger level */

void USART2_IRQHandler(void)
{
    BaseType_t woken = pdFALSE;
    uint8_t b = (uint8_t)USART2->DR;
    xStreamBufferSendFromISR(rx, &b, 1, &woken);
    portYIELD_FROM_ISR(woken);
}

void rx_task(void *p)
{
    uint8_t buf[64];
    for (;;) {
        size_t n = xStreamBufferReceive(rx, buf, sizeof buf, portMAX_DELAY);
        parse(buf, n);
    }
}
```

**Rules:** if more than one task (or ISR) writes, protect the writes with a critical section or a mutex, because the implementation assumes one writer. With message buffers, the receive buffer must be large enough for the next message, or the call returns 0 and the message stays.

**Zephyr equivalents:** `k_pipe`, `k_msgq` (fixed size), and `ring_buf` with semaphores.

### What are event groups / event flags? {M}
**Short answer:** An event group is a set of bits (flags) that tasks can set, clear and wait on with **AND** ("wait until bits 0 and 2 are both set") or **OR** ("wait until any of bits 0–3 is set") semantics, optionally clearing them on exit. They synchronise a task with several conditions at once, or several tasks at a barrier (`xEventGroupSync`). Unlike a counting semaphore, setting a bit that is already set does not count twice.

```c
#define EV_WIFI_UP   (1u << 0)
#define EV_TIME_SYNC (1u << 1)
#define EV_CERT_OK   (1u << 2)

EventGroupHandle_t sys_events = xEventGroupCreate();

/* cloud task waits until all three are ready */
EventBits_t bits = xEventGroupWaitBits(sys_events,
                                       EV_WIFI_UP | EV_TIME_SYNC | EV_CERT_OK,
                                       pdFALSE,          /* do not clear on exit */
                                       pdTRUE,           /* wait for ALL bits */
                                       pdMS_TO_TICKS(30000));
if ((bits & (EV_WIFI_UP | EV_TIME_SYNC | EV_CERT_OK)) != (EV_WIFI_UP | EV_TIME_SYNC | EV_CERT_OK)) {
    /* timeout: handle */
}
```

**Uses:** system start-up readiness (network up, time synced), state broadcasts to several tasks, barriers in multi-step pipelines, and waiting for one of several sources.

**Details and pitfalls**

- Several tasks can wait on the same group, and setting bits can unblock all of them (a broadcast), which semaphores cannot do.
- Setting bits from an ISR (`xEventGroupSetBitsFromISR`) is deferred to the timer service task in FreeRTOS, because waking an unknown number of tasks is not a bounded operation; that adds latency.
- Because bits are not counted, two events of the same type before the task runs merge into one. If you must count, use a semaphore or queue.
- The number of usable bits is limited (24 with 32-bit ticks in FreeRTOS).

**Zephyr:** `k_event` (event objects) and `k_poll` for waiting on multiple kernel objects.

### What are FreeRTOS task notifications? {M}
**Short answer:** Every FreeRTOS task has a built-in 32-bit notification value and state (an array of them since v10.4). Another task or an ISR can notify the task by incrementing the value, setting bits in it, or overwriting it, and the task can block waiting for a notification. Notifications are faster and use less RAM than semaphores, queues or event groups because no separate kernel object is needed, but only the owning task can wait on them and they cannot buffer multiple data items.

**As a lightweight binary/counting semaphore (ISR → task)**

```c
static TaskHandle_t rx_task_handle;

void DMA_IRQHandler(void)
{
    BaseType_t woken = pdFALSE;
    clear_dma_flags();
    vTaskNotifyGiveFromISR(rx_task_handle, &woken);    /* increment the notification value */
    portYIELD_FROM_ISR(woken);
}

void rx_task(void *p)
{
    for (;;) {
        uint32_t n = ulTaskNotifyTake(pdTRUE, pdMS_TO_TICKS(100));  /* pdTRUE: clear to 0 (binary) */
        if (n == 0) { /* timeout */ continue; }
        process_dma_buffer();
    }
}
```

**As event bits:** `xTaskNotify(task, BIT_X, eSetBits)` and `xTaskNotifyWait(0, ULONG_MAX, &bits, timeout)`.

**As a mailbox for a value:** `xTaskNotify(task, value, eSetValueWithOverwrite)`.

**Advantages:** about 45% faster than a binary semaphore and no extra RAM; ideal for "this ISR wakes that one handler task", which is the most common synchronisation in drivers.

**Limitations**

- Only one task (the target) can wait; you cannot broadcast to several tasks.
- One 32-bit value per index: it cannot queue several data items.
- The sender cannot block waiting for the receiver to consume a notification (no back-pressure).
- If several unrelated sources use the same notification index, they can interfere: use separate indexes or bits.

### Why must you use the FromISR API variants in an interrupt? {M}
**Short answer:** Normal RTOS API functions may block (wait for space or data), and an ISR must never block because it is not a task and cannot be suspended. The `...FromISR` variants never block, use interrupt-safe critical sections, and instead of switching context immediately, they report through a `pxHigherPriorityTaskWoken` flag that a higher-priority task became ready; the ISR then requests a context switch at its exit with `portYIELD_FROM_ISR()`.

```c
void UART_IRQHandler(void)
{
    BaseType_t woken = pdFALSE;
    uint8_t b = (uint8_t)UART->DR;
    xQueueSendFromISR(rx_queue, &b, &woken);   /* never blocks: fails if the queue is full */
    portYIELD_FROM_ISR(woken);                 /* pend PendSV if a higher-priority task was woken */
}
```

**Why the deferred switch:** the ISR may be nested inside other ISRs, and it may wake several tasks; requesting a switch once at the end (via PendSV, which runs after all ISRs) is safe and efficient. If you forget `portYIELD_FROM_ISR`, the woken task only runs at the next tick or scheduling point, adding up to one tick of latency.

**Interrupt priority rule (Cortex-M):** only interrupts with a priority **numerically greater than or equal to** `configMAX_SYSCALL_INTERRUPT_PRIORITY` (i.e. less urgent) may call FreeRTOS APIs. The kernel masks interrupts up to that level in its critical sections; a more urgent ISR could interrupt the kernel mid-update, so it must not call the API. Getting this wrong causes rare, random corruption; enable `configASSERT()`, which checks it in `vPortValidateInterruptPriority()`.

**Other systems:** Zephyr uses the same functions from ISRs but requires `K_NO_WAIT` timeouts (calls with waiting fail in ISRs); CMSIS-RTOS2 functions check `__get_IPSR()` and behave accordingly; ThreadX allows certain services from ISRs with `TX_NO_WAIT`.

### What is the tick and what is a tickless idle mode? {M}
**Short answer:** The tick is a periodic timer interrupt (commonly SysTick at 1 kHz, i.e. every 1 ms) that the kernel uses to keep time, wake delayed tasks, handle timeouts, and time-slice equal-priority tasks. In **tickless idle** mode, when only the idle task is ready, the kernel stops the periodic tick, programs a timer to wake the CPU at the next scheduled event (or on any interrupt), enters a low-power mode, and corrects its tick count on wake-up. This saves a lot of power in battery devices.

**Choosing the tick rate**

| Tick | Timing resolution | Overhead |
|---|---|---|
| 100 Hz (10 ms) | coarse delays | very low |
| 1000 Hz (1 ms) | typical | moderate |
| 10 kHz | fine, but... | interrupt overhead becomes significant |

Delays are only accurate to ±1 tick: `vTaskDelay(1)` can return after anything between almost 0 and 1 tick, depending on where in the current tick it was called. For precise timing use hardware timers.

**Tickless idle details (FreeRTOS `configUSE_TICKLESS_IDLE`)**

1. The idle task sees that the next task wake-up is N ticks away (and N ≥ `configEXPECTED_IDLE_TIME_BEFORE_SLEEP`).
2. `vPortSuppressTicksAndSleep()` stops SysTick, programs it (or a low-power timer such as LPTIM/RTC that keeps running in stop mode) for N ticks, and executes `WFI`.
3. On wake-up (timer expiry or another interrupt), it computes how many ticks really elapsed and advances the tick count with `vTaskStepTick()`.

**Power impact:** a 1 kHz tick wakes the CPU 1000 times per second; for a device that is mostly idle, removing those wake-ups can cut average current from hundreds of µA to a few µA. Low-power ports use a low-power timer clocked from the 32 kHz crystal so the MCU can enter stop mode.

**Zephyr** is tickless by default (`CONFIG_TICKLESS_KERNEL`) and uses a timeout queue programmed into the system timer.

### What is the idle task and what is it used for? {E}
**Short answer:** The idle task is created by the kernel at the lowest priority and runs whenever no other task is ready. In FreeRTOS it frees the memory of deleted tasks and calls an optional **idle hook** that applications use to enter low-power sleep, do background work, or measure CPU load. It must never block or take long, because then deleted tasks are not cleaned up and the system cannot sleep.

**Uses of the idle hook (`vApplicationIdleHook`, `configUSE_IDLE_HOOK`)**

- **Power saving:** execute `__WFI()` so the CPU sleeps until the next interrupt (or use tickless idle for deeper sleep).
- **CPU load measurement:** count how often the idle loop runs, or measure time spent in idle: `load = 1 − idle_time / total_time`.
- **Low-priority background work** that must never delay real tasks (e.g. scrubbing memory, non-urgent checks). Keep it short and non-blocking.

**What it must not do:** call blocking APIs (it must always be ready), or run long jobs (a task of equal priority 0 would wait; and stuck idle means memory from deleted tasks never gets freed).

**Diagnostic value:** if the idle task never runs, some task is busy-waiting or the system is overloaded, so many teams monitor idle time as a health metric and alarm when it drops below a threshold (e.g. 20%).

**Zephyr:** has an idle thread too; power management integrates with it automatically (`CONFIG_PM`).

### How do you choose task priorities? Explain rate-monotonic scheduling. {H}
**Short answer:** For periodic tasks, **rate-monotonic scheduling (RMS)** assigns higher fixed priorities to tasks with shorter periods (higher rates). For independent periodic tasks with deadlines equal to their periods, RMS is optimal among fixed-priority policies, and a task set is guaranteed schedulable if total utilisation `U = Σ Cᵢ/Tᵢ ≤ n(2^(1/n) − 1)`, which approaches **69.3%** for large n. Above that bound a set may still be schedulable, which you check with exact **response-time analysis**.

**Liu & Layland bound values**

| n tasks | Bound |
|---|---|
| 1 | 100% |
| 2 | 82.8% |
| 3 | 78.0% |
| 4 | 75.7% |
| ∞ | 69.3% |

**Variants**

- **Deadline-monotonic (DMS):** priority by relative deadline (shorter deadline = higher priority); optimal when deadlines are shorter than periods.
- **EDF (earliest deadline first):** dynamic priorities; schedules any set with U ≤ 100% (deadline = period) but is harder to implement and behaves badly under overload (many tasks can miss). Linux `SCHED_DEADLINE` uses EDF.

**Practical priority assignment beyond the theory**

1. Interrupt handlers do minimal work and defer to tasks.
2. Hard-deadline control loops get the highest task priorities, by rate.
3. Communication handlers (with latency requirements) next.
4. User interface, logging and housekeeping lowest.
5. Tasks that only react to events get priorities based on how fast they must react (their deadline).
6. Avoid many tasks at the same priority unless they are equally important.

**Validate with measurement:** trace tools (Percepio Tracealyzer, SEGGER SystemView) show response times, CPU load and blocking, which reveals when theory and reality differ (interrupts, blocking on shared resources, cache effects).

### How do you check whether a task set is schedulable? Give a worked example. {H}
**Short answer:** First compute utilisation and compare with the RMS bound; if it is above the bound, use **response-time analysis (RTA)**: for each task, iterate `Rᵢ = Cᵢ + Bᵢ + Σⱼ∈hp(i) ⌈Rᵢ / Tⱼ⌉ · Cⱼ` (its own execution, blocking by lower-priority tasks, plus interference from every higher-priority task) until it converges. The set is schedulable if every `Rᵢ ≤ Dᵢ`.

**Example (times in ms, RMS priorities: shortest period highest)**

| Task | Period T = deadline D | WCET C | Utilisation |
|---|---|---|---|
| T1 | 10 | 3 | 0.300 |
| T2 | 15 | 4 | 0.267 |
| T3 | 40 | 10 | 0.250 |
| Total | | | **0.817** |

The RMS bound for 3 tasks is 0.780, and 0.817 is above it, so the simple test is inconclusive. Run RTA (no blocking):

- **T1:** R = 3 (no higher-priority tasks) ≤ 10 ✓
- **T2:** R₀ = 4 → R = 4 + ⌈4/10⌉·3 = 7 → R = 4 + ⌈7/10⌉·3 = 7 (converged) ≤ 15 ✓
- **T3:** R₀ = 10
  - R = 10 + ⌈10/10⌉·3 + ⌈10/15⌉·4 = 10 + 3 + 4 = 17
  - R = 10 + ⌈17/10⌉·3 + ⌈17/15⌉·4 = 10 + 6 + 8 = 24
  - R = 10 + ⌈24/10⌉·3 + ⌈24/15⌉·4 = 10 + 9 + 8 = 27
  - R = 10 + ⌈27/10⌉·3 + ⌈27/15⌉·4 = 10 + 9 + 8 = 27 (converged) ≤ 40 ✓

All tasks meet their deadlines even though utilisation is above the bound.

**Adding reality**

- **Blocking time `Bᵢ`:** the longest time a lower-priority task can hold a resource that task i needs (with priority inheritance/ceiling, typically one critical section).
- **ISR load:** treat interrupts as the highest-priority "tasks" with their own C and minimum inter-arrival time.
- **Kernel overhead:** add context switch time to each C (twice per job: switch in and out).
- **Jitter:** release jitter adds to the interference terms.

**Interview tip:** even if you do not remember the formula exactly, explain the idea: "a task's worst-case response is its own work plus the work of every higher-priority job released during that window plus blocking; iterate until stable and compare with the deadline."

### How much stack does a task need and how do you size it? {M}
**Short answer:** Estimate it from the worst-case call depth of the task's code (local variables, saved registers, function arguments, padding) plus the context-switch frame (16 words on Cortex-M, plus 18 more for FP context if the task uses the FPU, and on some ports a little more). Then **measure** under worst-case conditions with the high-water mark and add a safety margin (20–50%). Interrupts use the main stack on Cortex-M, so they do not need to be included in task stacks.

**Step by step**

1. **Static analysis:** compile with `-fstack-usage` to get each function's frame size, and combine with the call graph (`-fcallgraph-info`, puncover, or commercial tools) to get the worst path. Recursion and function pointers need manual bounds.
2. **Add** the context frame and any library calls that are stack-hungry (`printf`/`snprintf` with floating point can use 500 bytes to 1 KB or more).
3. **Measure:** run stress tests that exercise every path, then check `uxTaskGetStackHighWaterMark(handle)` (minimum free stack ever, in words). FreeRTOS fills stacks with `0xA5` to measure this.
4. **Margin:** keep 25% or more free in the worst measured case, since tests rarely hit the true worst case.

**Protection during development and in the field**

- `configCHECK_FOR_STACK_OVERFLOW = 2` (check pattern at each switch) and `vApplicationStackOverflowHook()`.
- MPU guard regions (FreeRTOS-MPU, Zephyr `CONFIG_HW_STACK_PROTECTION`) or Armv8-M PSPLIM for immediate faults.
- Log the minimum free stack per task in diagnostics.

**Reducing stack needs**

- Move large buffers out of local variables into static memory or pools.
- Avoid `printf`-family functions in small tasks; use a logging task.
- Avoid deep call chains and recursion; avoid variable-length arrays and `alloca`.
- Watch for large structs passed by value.

**Typical values:** simple tasks 128–256 words (512 B–1 KB) on Cortex-M; tasks using TLS, filesystems or networking several KB.

### What are software timers in an RTOS? {E}
**Short answer:** Software timers run a callback function after a delay, either once (one-shot) or repeatedly (auto-reload), without needing a dedicated task per timer. In FreeRTOS all timer callbacks execute in a single **timer service (daemon) task**, so callbacks must be short and must never block, otherwise every other timer is delayed.

```c
static void led_timer_cb(TimerHandle_t t) { (void)t; toggle_led(); }

TimerHandle_t led_timer = xTimerCreate("led", pdMS_TO_TICKS(500), pdTRUE /* auto-reload */,
                                       NULL, led_timer_cb);
xTimerStart(led_timer, 0);
```

**How it works**

- API calls (`xTimerStart`, `xTimerStop`, `xTimerChangePeriod`, `xTimerReset`) send commands through the **timer command queue** to the daemon task, so they can fail if the queue is full; check the return value and use a block time.
- The daemon task keeps active timers in a list sorted by expiry and blocks until the next one expires.
- Its priority (`configTIMER_TASK_PRIORITY`) decides how promptly callbacks run relative to other tasks; set it appropriately (often high, with very short callbacks).

**Good uses:** LED blinking, timeouts for protocols (e.g. "no response in 2 s"), debouncing, periodic housekeeping, retry back-off, watchdog supervision.

**Avoid:** heavy processing or blocking calls in callbacks (send an event to a worker task instead), and using software timers for precise, jitter-free timing (use a hardware timer interrupt for that).

**Resolution:** limited to the tick period.

**Zephyr:** `k_timer` runs its expiry function in the system timer **interrupt** context (so it must be ISR-safe and very short); use `k_work_delayable` for work that should run in a thread.

### What is the difference between vTaskDelay and vTaskDelayUntil? {M}
**Short answer:** `vTaskDelay(n)` blocks the task for `n` ticks counted **from the moment it is called**, so if the task's own work takes variable time, its period drifts. `vTaskDelayUntil(&last_wake, period)` (or `xTaskDelayUntil`) blocks until an **absolute** time `last_wake + period` and then updates `last_wake`, giving a fixed-frequency loop with no drift.

```c
/* drifts: period = 10 ms + execution time (variable) */
for (;;) {
    control_step();
    vTaskDelay(pdMS_TO_TICKS(10));
}

/* fixed 10 ms period, independent of execution time */
TickType_t last = xTaskGetTickCount();
for (;;) {
    vTaskDelayUntil(&last, pdMS_TO_TICKS(10));
    control_step();
}
```

**Timeline (control step takes 2–4 ms)**

```
vTaskDelay:       run(3) wait(10) run(2) wait(10) run(4) wait(10)  → wake times 13, 25, 39 ...
vTaskDelayUntil:  wake at 10, 20, 30, 40 ... regardless of run time
```

**Details**

- If the task overruns (work takes longer than the period), `vTaskDelayUntil` returns immediately and the task runs late; `xTaskDelayUntil` returns `pdFALSE` in that case, so you can detect overruns.
- Neither gives better than ±1 tick precision, and higher-priority tasks or interrupts can delay the actual start (jitter). For tight timing (e.g. a 1 kHz control loop with low jitter), trigger the task from a hardware timer interrupt with a notification.
- `vTaskDelay(0)` just yields.

**Zephyr equivalents:** `k_sleep()` / `k_msleep()` (relative) and `k_sleep(K_TIMEOUT_ABS_MS(...))` or periodic `k_timer` + `k_timer_status_sync()` for absolute timing.

### How do you protect a shared resource between a task and an ISR? {M}
**Short answer:** A mutex cannot be used, because an ISR cannot block or own a mutex. Instead: protect the task's short access with a **critical section** that masks the interrupt (`taskENTER_CRITICAL()` / `taskEXIT_CRITICAL()`, which raises `BASEPRI` on Cortex-M3+); design the data flow so each variable has a **single writer** (lock-free ring buffer); or pass data through an RTOS **queue/stream buffer** and let only the task own the resource.

**Options**

1. **Critical section in the task**

```c
/* task side */
taskENTER_CRITICAL();
uint32_t count = shared_count;    /* read-modify-write that the ISR also does */
shared_count = 0;
taskEXIT_CRITICAL();

/* ISR side: if a higher-priority ISR can also touch it */
UBaseType_t s = taskENTER_CRITICAL_FROM_ISR();
shared_count++;
taskEXIT_CRITICAL_FROM_ISR(s);
```

Keep it a few instructions long; it delays all interrupts at or below the masked priority.

2. **Disable only that interrupt** (`NVIC_DisableIRQ` / `NVIC_EnableIRQ`) around the access, when only one ISR is involved and you do not want to affect other interrupts.

3. **Lock-free single-producer/single-consumer structures:** the ISR writes the head, the task writes the tail; no locks needed on a single core (add barriers on Cortex-M7/multi-core).

4. **Message passing:** the ISR sends the event/data to a queue, stream buffer or task notification; the task is the only one that touches the resource. This is usually the cleanest design.

5. **Atomic operations** for single variables (C11 atomics on Cortex-M3+).

**Do not:** take a mutex in an ISR, call blocking APIs from it, or rely on `volatile` alone for read-modify-write operations.

**Interrupt priority check:** if the ISR calls `...FromISR` APIs, its priority must be at or below `configMAX_SYSCALL_INTERRUPT_PRIORITY` (numerically ≥).

### How do you measure task execution time and CPU load in an RTOS? {M}
**Short answer:** Use the RTOS's run-time statistics (FreeRTOS `configGENERATE_RUN_TIME_STATS` with a fast timer, then `vTaskGetRunTimeStats()`), measure idle time to compute CPU load (`load = 1 − idle time / total time`), toggle GPIOs at task entry/exit and watch them on a logic analyser, or use trace tools (Percepio Tracealyzer, SEGGER SystemView) that record every context switch and interrupt with timestamps.

**FreeRTOS run-time stats**

```c
/* FreeRTOSConfig.h */
#define configGENERATE_RUN_TIME_STATS 1
#define portCONFIGURE_TIMER_FOR_RUN_TIME_STATS() dwt_init()      /* e.g. DWT cycle counter */
#define portGET_RUN_TIME_COUNTER_VALUE()         (DWT->CYCCNT)

/* somewhere in a debug command */
char buf[512];
vTaskGetRunTimeStats(buf);   /* "Task  AbsTime  %Time" per task, including IDLE */
```

The counter should run 10–100× faster than the tick for useful resolution.

**Measuring a single function's WCET**

```c
uint32_t t0 = DWT->CYCCNT;
filter_update();
uint32_t cycles = DWT->CYCCNT - t0;
if (cycles > max_cycles) max_cycles = cycles;      /* keep the worst seen */
```

Run it under worst-case conditions (all interrupts active, caches cold) and record the maximum, not the average.

**GPIO method:** set a pin high at task start, low at the end; an oscilloscope or logic analyser shows execution time, period and jitter for several tasks at once, with no software overhead to speak of. Great for checking real-time behaviour and interrupt latency.

**Trace tools** show the whole timeline: which task ran when, blocking reasons, response times and missed deadlines. They are the fastest way to understand priority problems.

**CPU load target:** keep peak load below about 70–80% to leave headroom for worst-case bursts and future features, and alarm in diagnostics if idle time falls below a threshold.

### How is memory allocated in an RTOS, and why prefer static allocation? {M}
**Short answer:** RTOS objects (task stacks and control blocks, queues, semaphores, timers) can be allocated **dynamically** from an RTOS heap or **statically** from memory you provide. Safety-critical and long-running systems prefer static allocation (or allocation only at start-up) because it cannot fail at run time, cannot fragment, is deterministic, and makes RAM usage visible at link time.

**FreeRTOS heap schemes**

| Scheme | Free? | Coalescing | Notes |
|---|---|---|---|
| `heap_1` | no | – | allocate only; simplest and deterministic; good for "create everything at start-up" |
| `heap_2` | yes | no | legacy; fragments; avoid |
| `heap_3` | yes | depends | wraps the C library `malloc`/`free` with scheduler suspension |
| `heap_4` | yes | yes | first-fit with merging of adjacent blocks; most common |
| `heap_5` | yes | yes | like heap_4 but spans several non-contiguous RAM regions |

**Static allocation**

```c
static StackType_t  sensor_stack[256];
static StaticTask_t sensor_tcb;
TaskHandle_t h = xTaskCreateStatic(sensor_task, "sensor", 256, NULL, 3, sensor_stack, &sensor_tcb);

static uint8_t       q_storage[16 * sizeof(msg_t)];
static StaticQueue_t q_struct;
QueueHandle_t q = xQueueCreateStatic(16, sizeof(msg_t), q_storage, &q_struct);
```

Enable with `configSUPPORT_STATIC_ALLOCATION` (and optionally disable dynamic allocation entirely with `configSUPPORT_DYNAMIC_ALLOCATION 0`).

**Guidelines**

- Create all tasks and kernel objects during initialisation; never create/delete them repeatedly at run time.
- For variable-size application data, use fixed-size **memory pools** (Zephyr `k_mem_slab`, ThreadX block pools) instead of a general heap.
- Monitor the heap (`xPortGetMinimumEverFreeHeapSize()`) and define `vApplicationMallocFailedHook()` if any dynamic allocation remains.
- Make sure the C library's `malloc` (used by `printf`, some drivers) is either thread-safe (newlib locks via `__malloc_lock`) or not used from multiple tasks.

### How does an RTOS work on a multi-core (SMP) processor? {H}
**Short answer:** In **SMP** (symmetric multiprocessing) mode, one RTOS kernel schedules tasks across several cores sharing memory: on each core it runs the highest-priority ready task that is allowed to run there. This adds new concerns: kernel data structures need spinlocks instead of only disabling interrupts, tasks of different priorities can run **at the same time**, core affinity can pin tasks to cores, and caches and memory ordering must be handled. In **AMP** (asymmetric) mode, each core runs its own independent OS or bare-metal code and they communicate through shared memory and inter-core interrupts.

**SMP (FreeRTOS SMP since v11, Zephyr SMP, ThreadX SMP)**

- **Locks:** a task-level critical section on one core does not stop the other core, so the kernel uses spinlocks (with interrupt masking) for its data.
- **Priority assumptions break:** in single-core code, "a high-priority task never runs at the same time as a low-priority task" was often relied on to avoid locks. On SMP both can run in parallel, so shared data needs real protection.
- **Affinity:** `vTaskCoreAffinitySet()` (FreeRTOS) or `k_thread_cpu_mask_*` (Zephyr) restricts tasks to cores, e.g. dedicate one core to a time-critical control loop.
- **Inter-processor interrupts:** used to ask another core to reschedule.
- **Caches:** cores need coherent caches (or uncached shared memory) and atomics with proper barriers.

**AMP (common on heterogeneous SoCs)**

- e.g. Cortex-M7 + Cortex-M4 in STM32H7 dual-core, Cortex-A + Cortex-M in i.MX 8M / STM32MP1, or two Cortex-R cores in lock-step pairs.
- Each core runs its own RTOS (or Linux on one, RTOS on the other).
- Communication via **OpenAMP/RPMsg** (shared-memory ring buffers + mailbox interrupts), hardware semaphores (HSEM) for shared peripherals.
- Simpler isolation and certification, but load cannot be balanced automatically.

**Lock-step** (Cortex-R5/R52 in safety MCUs) is different again: two cores execute the same code in parallel and hardware compares results to detect faults; it is one logical CPU for software.

### What are common RTOS design mistakes? {M}
**Short answer:** The usual mistakes are: too many tasks; busy-waiting instead of blocking; blocking or slow calls in ISRs; wrong interrupt priorities relative to the kernel's syscall priority; holding mutexes during slow I/O or taking them in inconsistent orders; sharing globals without protection; undersized stacks; ignoring API return values and timeouts; and creating/deleting tasks and objects at run time.

| Mistake | Consequence | Better approach |
|---|---|---|
| A task per small job | wasted stacks, more switches and sharing | group related work; use event-driven tasks |
| Polling loops (`while (!flag);`) | starves lower priorities, burns power | block on notifications/queues |
| `printf`, `malloc`, blocking APIs in ISRs | crashes, deadlocks, latency | defer to tasks; use `FromISR` APIs |
| ISR priority above `configMAX_SYSCALL_INTERRUPT_PRIORITY` calling the API | rare random corruption | follow the priority rule; enable `configASSERT` |
| Holding a mutex during flash writes or network calls | priority inversion, latency for others | copy data, release, then do slow work; single-owner tasks |
| Inconsistent lock order | deadlock | global lock ordering; message passing |
| Unprotected shared globals | race conditions | mutex, critical section, or atomics |
| Stack sizes guessed once | random crashes later | measure high-water marks, overflow checks |
| `portMAX_DELAY` everywhere | silent hangs | finite timeouts and error handling |
| Ignoring return values (`xQueueSend` failed) | lost data | check and count failures |
| Dynamic creation/deletion at run time | fragmentation, leaks | create at init; static allocation |
| Using `vTaskDelay` for periodic loops | drift | `vTaskDelayUntil` or timer-driven tasks |
| Not watching CPU load / idle time | unnoticed overload | run-time stats, trace, watchdog supervision |

**Interview tip:** pick two or three from your own experience and describe how you found them (trace tools, high-water marks, `configASSERT`) — that is more convincing than reciting the list.

### How does Zephyr differ from FreeRTOS? {M}
**Short answer:** **FreeRTOS** is a small, portable kernel (scheduler, queues, semaphores, timers, event groups) with optional add-on libraries; drivers usually come from the silicon vendor's SDK, and configuration is a header file. **Zephyr** is a full RTOS platform under the Linux Foundation: it uses **Kconfig** and **devicetree** (like Linux) for configuration, has a unified driver model and many in-tree drivers, networking (IPv4/IPv6, Bluetooth LE, Thread/Matter), file systems, a shell, logging, power management, MCUboot integration and optional user-mode isolation, built with CMake and the `west` tool. Zephyr does more out of the box but is larger and has a steeper learning curve.

| | FreeRTOS | Zephyr |
|---|---|---|
| Scope | kernel + optional libraries | complete OS platform |
| Configuration | `FreeRTOSConfig.h` | Kconfig (`prj.conf`) + devicetree + board definitions |
| Drivers | vendor SDK/HAL, or your own | in-tree, generic APIs (`gpio_pin_set_dt`, `i2c_write_read_dt`) |
| Build | any (Make, CMake, IDE projects) | CMake + `west` meta-tool |
| Networking / BLE | separate (FreeRTOS+TCP, vendor stacks, lwIP) | integrated IP stack, Bluetooth host/controller, OpenThread |
| Memory protection | FreeRTOS-MPU port | user mode threads with MPU/MMU (`CONFIG_USERSPACE`) |
| Footprint | very small (≈ 5–10 KB kernel) | larger, but highly configurable (minimal builds of ~10 KB are possible) |
| Licensing | MIT | Apache 2.0 |
| Learning curve | gentle | steep (devicetree, Kconfig, west) |
| Governance | maintained by Amazon (AWS) | Linux Foundation project with many vendors |

**When to choose which:** FreeRTOS for small, simple products, existing vendor SDK-based projects, or teams that want minimal abstraction. Zephyr for connected products (BLE, Thread, Matter, IP), portability across many boards, a Linux-like development model, and long-term vendor-neutral support (Nordic's nRF Connect SDK is built on Zephyr).

**Others worth knowing:** Eclipse ThreadX (formerly Azure RTOS, with safety certifications), NuttX (POSIX-compatible, used by PX4 drones), RIOT (IoT), Mbed OS (end of life), and commercial safety RTOSes (SafeRTOS, VxWorks, QNX, INTEGRITY).
