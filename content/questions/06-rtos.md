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
Deadlock, livelock and starvation are different forms of failure to make useful progress.

| Problem | Meaning | Example |
|---|---|---|
| Deadlock | Tasks wait indefinitely for each other | Circular mutex dependency |
| Livelock | Tasks actively react but make no progress | Two tasks repeatedly release and retry conflicting locks in synchrony |
| Starvation | A task is repeatedly denied CPU time or a resource | Always-ready high-priority task prevents low-priority work |

#### 1. Solutions

For deadlock, use a consistent lock order. For livelock, avoid symmetric retry behavior through ownership rules or bounded backoff. For starvation, use suitable scheduling, bounded high-priority workloads and fair resource arbitration when requirements permit.

#### 2. Embedded diagnosis

Track task progress counters, queue depths, lock owners, blocked durations and execution trace. High CPU activity does not establish that the application is progressing.

**Interview takeaway:** Deadlock is waiting without progress; livelock is activity without progress; starvation is repeated denial of progress to a particular task.

### What is a message queue and when should you use one? {E}
A message queue transfers data between tasks or between an ISR and a task through synchronized storage. It lets producers and consumers execute independently.

#### 1. Example using FreeRTOS

```c
QueueHandle_t q = xQueueCreate(8, sizeof(uint32_t));
```

After checking that creation succeeded, a producer can send a value:

```c
uint32_t sample = 123;
if (xQueueSend(q, &sample, pdMS_TO_TICKS(10)) != pdPASS)
    handle_queue_full();
```

Consumer:

```c
uint32_t value;
if (xQueueReceive(q, &value, portMAX_DELAY) == pdPASS)
    process_sample(value);
```

FreeRTOS copies the configured item size into/out of queue storage.

#### 2. Queueing pointers

For large buffers, a queue may carry a pointer or descriptor instead of copying the payload. Define who owns the buffer before and after sending, and what happens if the queue is full. Do not queue the address of an automatic object that may expire before consumption.

#### 3. Capacity

Size the queue for burst rate, service time and permitted backlog. Define whether overflow drops, blocks, overwrites or triggers recovery.

**Interview takeaway:** Queues provide synchronized data transfer and buffering. Use ISR-safe variants in interrupts and explicitly manage ownership when sending pointers.

### What are stream buffers and message buffers, and when are they better than queues? {M}
FreeRTOS stream buffers transfer a sequence of bytes. Message buffers transfer variable-length messages while preserving boundaries. A normal queue transfers fixed-size items.

| Queue | Stream buffer | Message buffer |
|---|---|---|
| Fixed-size items | Byte stream | Variable-length messages |
| Multiple producers/consumers supported under API rules | Designed for one writer and one reader | Designed for one writer and one reader |
| Good for structures and descriptors | Good for continuous UART bytes | Good for packets |

#### 1. UART stream example

```c
StreamBufferHandle_t sb =
    xStreamBufferCreate(256, 1);
```

Check the handle. A producer writes received bytes and a parser consumes available bytes. Sends may transfer fewer bytes than requested; handle partial results.

#### 2. Message buffer example

```c
MessageBufferHandle_t mb = xMessageBufferCreate(256);
```

A producer sends one message, and a consumer receives a complete message into a sufficiently large buffer. Message-length metadata consumes part of the storage.

#### 3. Concurrency restriction

Stream/message buffers assume one writer and one reader unless additional serialization is provided following the kernel documentation. Queues may be a better choice for multiple independent producers.

**Interview takeaway:** Use a stream buffer for bytes, a message buffer for variable-length records, and a queue for fixed-size messages or descriptors.

### What are event groups / event flags? {M}
An event group stores event bits that tasks can set, clear or wait for. It is useful when work depends on one or several conditions rather than a data payload.

#### 1. FreeRTOS example

```c
#define NET_READY (1U << 0)
#define CFG_READY (1U << 1)

EventBits_t bits = xEventGroupWaitBits(
    events, NET_READY | CFG_READY,
    pdFALSE, pdTRUE, pdMS_TO_TICKS(500));

if ((bits & (NET_READY | CFG_READY)) ==
    (NET_READY | CFG_READY)) {
    start_service();
}
```

The task waits for both bits (wait-for-all). The clear-on-exit parameter is false here, so the bits remain set. The returned bits must be checked because the wait may time out.

#### 2. Wait modes

Wait-for-any succeeds when at least one selected bit is set; wait-for-all requires every selected bit. Clear-on-exit behavior depends on the API and chosen parameters.

#### 3. Limitations

Repeated setting of the same bit does not count multiple events. Use a counting semaphore, queue or counting notification if every occurrence matters. FreeRTOS has reserved event-group bits and some ISR operations defer work through the timer service.

**Interview takeaway:** Event groups represent conditions, not message payloads or event counts. Choose the wait and clear semantics carefully.

### What are FreeRTOS task notifications? {M}
A FreeRTOS task notification is a lightweight signaling mechanism associated with a task. Notifications can act as a binary/counting semaphore, bit set or small value mailbox depending on how they are used.

#### 1. Example: DMA completion

```c
void DMA_IRQHandler(void)
{
    BaseType_t woken = pdFALSE;

    // Acknowledge the relevant device interrupt.
    vTaskNotifyGiveFromISR(worker, &woken);
    portYIELD_FROM_ISR(woken);
}
```

The worker waits:

```c
uint32_t count = ulTaskNotifyTake(pdTRUE,
                                 portMAX_DELAY);
if (count != 0)
    process_completed_work();
```

With pdTRUE, the notification count is cleared on successful take; use the returned count or other completion state if multiple events must be processed. With pdFALSE it decrements instead.

#### 2. Why notifications are lightweight

The notification state/value is attached to the task rather than a separately created queue or semaphore. Supported versions/configurations provide indexed notification arrays.

#### 3. Limitations

A notification targets a specific receiving task and is not a general multi-receiver message queue. The action selected by the sender determines whether values accumulate, overwrite or set bits.

**Interview takeaway:** Task notifications are efficient for direct task signaling. Use a queue when independent messages and payload ordering must be preserved.

### Why must you use the FromISR API variants in an interrupt? {M}
FreeRTOS provides FromISR API variants because interrupt context cannot block and must use synchronization and scheduling rules appropriate to an ISR.

#### 1. Correct queue signaling

```c
void UART_IRQHandler(void)
{
    BaseType_t woken = pdFALSE;
    uint8_t byte = uart_read_byte();

    if (xQueueSendFromISR(rx_queue, &byte, &woken)
        != pdPASS) {
        // Record dropped data using ISR-safe logic.
    }

    portYIELD_FROM_ISR(woken);
}
```

The handler acknowledges the interrupt as required by the UART. If the queue wakes a higher-priority task, the port-specific yield mechanism can request scheduling at interrupt exit.

#### 2. Why ordinary APIs are unsuitable

Task APIs may wait for a resource, manipulate scheduler state using task-context assumptions or acquire locks that are forbidden in interrupt context. FromISR variants are designed not to block.

#### 3. Priority constraints

On Cortex-M FreeRTOS ports, only interrupts within the permitted syscall-priority range may call RTOS APIs. Higher-urgency interrupts must use another handoff mechanism. Configure priority bits and grouping correctly.

**Interview takeaway:** Use only APIs documented as ISR-safe, check failure returns, and request the correct reschedule operation when a higher-priority task is woken.

### What is the tick and what is a tickless idle mode? {M}
An RTOS tick is a periodic timekeeping event used for delays, timeouts and, depending on policy, time slicing. Tickless idle suppresses unnecessary periodic tick interrupts while no work is ready.

#### 1. Tick example

A 1 kHz tick represents a nominal 1 ms tick period. A delay expressed as 10 ticks blocks the task until its calculated wake tick; wall-clock delay depends on its phase relative to tick boundaries and scheduling latency.

#### 2. Tickless idle flow

```text
No runnable work except idle
       |
Find next known kernel deadline
       |
Program wake timer, suppress periodic ticks
       |
Sleep until event / deadline
       |
Account for elapsed ticks and resume scheduling
```

An external interrupt may wake the processor before the programmed deadline. The port must update timekeeping appropriately.

#### 3. Trade-offs

A faster tick improves nominal delay granularity but increases periodic interrupt overhead. Tickless operation can reduce idle power and wakeups, but needs reliable timers, wake latency handling and platform power-management integration.

**Interview takeaway:** A tick is a kernel time base, not a guarantee of exact execution time. Tickless idle saves energy by suppressing unnecessary ticks, not by stopping time.

### What is the idle task and what is it used for? {E}
The idle task runs when no other eligible task can execute. It gives the RTOS a defined lowest-priority execution context.

#### 1. Common uses

- Enter a platform-supported low-power state.
- Run an optional idle hook.
- Perform kernel-specific housekeeping.

In FreeRTOS, the idle task also participates in cleanup of resources for tasks that delete themselves, depending on configuration and execution path.

#### 2. Idle hook

```c
void vApplicationIdleHook(void)
{
    // Short, nonblocking idle work only.
}
```

Enable the applicable FreeRTOS configuration. A real power-management implementation must coordinate wake sources and scheduler/timer state; do not blindly enter a deep sleep mode in the hook.

#### 3. CPU load estimate

If the idle task executes for 30% of an observation interval, non-idle task activity is approximately 70%, assuming the measurement accounts appropriately for interrupts and other untracked runtime.

**Interview takeaway:** Never block the idle task or place essential deadline-sensitive work solely in an idle hook. It may receive little CPU time under heavy load.

### How do you choose task priorities? Explain rate-monotonic scheduling. {H}
Task priorities should reflect deadlines, execution times, dependencies and blocking, not simply how important a task sounds.

#### 1. Rate-monotonic scheduling (RMS)

For independent periodic tasks on one CPU, with deadlines equal to periods and fixed-priority preemptive scheduling, RMS gives shorter-period tasks higher priorities.

| Task | Period | Worst-case execution | RMS priority |
|---|---:|---:|---|
| Control | 5 ms | 1 ms | Highest |
| Sampling | 10 ms | 2 ms | Middle |
| Logging | 50 ms | 4 ms | Lowest |

The control task runs most frequently, so it receives the highest fixed priority under the RMS assumptions.

#### 2. Priority selection in real firmware

Measure worst-case execution, identify deadlines, account for resource blocking, interrupt overhead and release jitter, then assign priorities and validate response times. Aperiodic and sporadic jobs need additional analysis.

#### 3. Avoid starvation

High-priority tasks should block when idle. An always-ready high-priority polling loop can prevent all lower-priority tasks from running.

**Interview takeaway:** RMS is optimal among fixed-priority assignments under its classical assumptions. It is not a universal priority rule for arbitrary deadlines, dependencies or multicore systems.

### How do you check whether a task set is schedulable? Give a worked example. {H}
Schedulability analysis determines whether all tasks can finish by their deadlines under a stated scheduling model. Consider independent periodic tasks, one CPU, fixed-priority preemption, deadlines equal to periods, and negligible blocking/overhead.

#### 1. Worked example

| Task | Worst-case execution C | Period T | Utilization C/T |
|---|---:|---:|---:|
| A | 1 ms | 4 ms | 0.25 |
| B | 2 ms | 5 ms | 0.40 |
| Total | | | 0.65 |

For two tasks, the classical RMS sufficient utilization bound is 2(√2−1), approximately 0.828. Since 0.65 is below the bound, the task set is schedulable under the stated assumptions.

#### 2. Response-time analysis

For task i, iterate:

```text
R_i(next) = C_i + B_i
          + sum over higher-priority tasks j:
              ceil(R_i(current) / T_j) * C_j
```

B_i is a suitable bound on blocking. Here A has highest priority and R_A = 1 ms. For B, start R_B = 2:

```text
2 + ceil(2/4)*1 = 3
2 + ceil(3/4)*1 = 3 (converged)
```

R_B = 3 ms, below its 5 ms deadline.

#### 3. Real-world analysis

Include interrupt interference, scheduling/context-switch costs, blocking, release jitter, and the actual deadline model. Utilization greater than the RMS sufficient bound does not automatically prove failure; exact analysis may still find a feasible schedule.

**Interview takeaway:** Average CPU utilization alone cannot prove deadlines. Use an appropriate worst-case response-time analysis and validate on the target.

### How much stack does a task need and how do you size it? {M}
An RTOS task stack must accommodate its maximum active call chain, saved registers, local objects and any exception context stored on that stack.

#### 1. Estimate the size

1. Analyze function call depth and stack usage.
2. Include library calls, context-switch state and FPU state if used.
3. Account for interrupt/exception frames according to the architecture.
4. Add a margin for observed and analyzed worst-case usage.

Avoid large automatic buffers and unbounded recursion on small task stacks.

#### 2. FreeRTOS watermark

```c
UBaseType_t unused =
    uxTaskGetStackHighWaterMark(task);
```

This returns the minimum observed unused stack depth, in stack units. For a port with four-byte StackType_t, a watermark of 32 units corresponds to 128 bytes. Confirm the API and port units rather than assuming bytes.

#### 3. Example

If a task has a 1024-byte stack and testing shows a minimum of 128 unused bytes, the observed maximum usage is 896 bytes. This is not proof that all future call paths fit.

#### 4. Protection

Use configured RTOS stack-overflow checking, MPU guards where available, compiler stack-usage reports and representative stress tests.

**Interview takeaway:** Size stacks using worst-case analysis plus measured margins. Hardware exception stacking and task stack units are common sources of sizing mistakes.

### What are software timers in an RTOS? {E}
An RTOS software timer tracks a timeout or periodic interval in software and invokes a callback or posts an event when it expires. It uses a kernel time base rather than dedicating a physical timer to every timeout.

#### 1. FreeRTOS example

```c
static void timer_cb(TimerHandle_t timer)
{
    xTaskNotifyGive(worker);
}

TimerHandle_t t = xTimerCreate(
    "periodic", pdMS_TO_TICKS(100),
    pdTRUE, NULL, timer_cb);

if (t != NULL)
    xTimerStart(t, 0);
```

Check the start result in production. pdTRUE selects auto-reload. The callback runs in the timer service task, not a hardware ISR.

#### 2. One-shot vs periodic

A one-shot timer expires once unless restarted. A periodic timer automatically reloads according to the kernel's timer semantics.

#### 3. Callback rules

Keep callbacks short and nonblocking. A slow callback can delay other software timers because they share the timer service context. Send lengthy work to a worker task.

#### 4. Hardware timer distinction

Hardware timers are preferable for precise signal generation, capture or timing requirements beyond the kernel's tick resolution. Software timer expiration and callback execution are not necessarily simultaneous.

**Interview takeaway:** Software timers simplify application timeouts but their callback latency depends on scheduler and timer-service load.

### What is the difference between vTaskDelay and vTaskDelayUntil? {M}
`vTaskDelay` blocks for a relative number of ticks. `vTaskDelayUntil` (and the status-returning xTaskDelayUntil API) supports periodic execution relative to a maintained previous wake time.

#### 1. Relative delay

```c
for (;;) {
    process();
    vTaskDelay(pdMS_TO_TICKS(100));
}
```

If processing takes 20 ms, the interval between starts is approximately 120 ms plus timing variations. Execution time contributes to drift.

#### 2. Periodic scheduling

```c
TickType_t last = xTaskGetTickCount();

for (;;) {
    process();
    vTaskDelayUntil(&last, pdMS_TO_TICKS(100));
}
```

The wake schedule is advanced by the requested period, rather than measuring each delay from the end of processing. This is useful for sampling and control.

```text
Relative: work 20 | wait 100 | work 20 | wait 100
Periodic: work 20 | wait 80  | work 20 | wait 80
```

The diagram assumes an ideal tick phase and no interference.

#### 3. Deadline miss

If processing exceeds the period, the delay-until operation may return without blocking. Detect overruns and choose whether to skip missed releases, resynchronize or report an error.

**Interview takeaway:** Delay is relative; delay-until maintains a periodic release schedule. Neither guarantees the task actually executes exactly at the wake tick.

### How do you protect a shared resource between a task and an ISR? {M}
A shared resource between a task and an ISR requires synchronization that does not block in interrupt context.

#### 1. Event and data transfer

Prefer an ISR-safe queue or notification when the ISR produces work for a task.

```c
void IRQ_Handler(void)
{
    BaseType_t woken = pdFALSE;
    uint32_t value = read_and_ack_device();

    xQueueSendFromISR(queue, &value, &woken);
    portYIELD_FROM_ISR(woken);
}
```

Handle queue-full errors and follow the interrupt-priority restrictions.

#### 2. Shared counter or short update

Use a supported lock-free atomic operation or an appropriate RTOS critical-section API. On a single-core system, masking the relevant interrupt can protect the task's short update, provided the ISR is within the masked set. Save/restore mask state when required.

#### 3. What not to do

Do not take a blocking mutex from an ISR. Do not rely solely on volatile for multi-step updates. Local interrupt masking does not stop DMA or other CPUs.

#### 4. Ownership example

For a DMA receive buffer, the ISR signals completion and transfers ownership according to the driver protocol. The task accesses the completed buffer only after the required cache and ordering synchronization.

**Interview takeaway:** Use a handoff instead of sharing mutable state wherever practical. Select synchronization according to ISR priority, CPU count and device ownership.

### How do you measure task execution time and CPU load in an RTOS? {M}
Task execution time measures how much CPU time a task consumes; CPU load measures the fraction of time the processor is busy over a defined interval.

#### 1. Measure elapsed time with a cycle counter

On Cortex-M implementations supporting an enabled DWT cycle counter:

```c
uint32_t start = DWT->CYCCNT;
work();
uint32_t elapsed = DWT->CYCCNT - start;
```

Unsigned subtraction handles wrap for intervals shorter than the counter period. Divide cycles by the applicable CPU clock to estimate elapsed time. Interrupts and preemption can contribute to this elapsed measurement.

#### 2. Measure per-task CPU time

An RTOS trace hook or runtime-statistics facility can accumulate time between context switches. FreeRTOS supports runtime statistics when the relevant timer and configuration are provided. Ensure the statistics timer has sufficient resolution and understand whether interrupt time is attributed to tasks.

#### 3. CPU load example

If a single CPU is idle for 25 ms during a 100 ms observation window, estimated non-idle load is 75%, subject to the accounting method.

#### 4. Real-time profiling

Measure worst-case latency, execution time, queue backlog and deadline misses with representative workloads. A GPIO and scope or a hardware trace interface may help when software instrumentation perturbs timing.

**Interview takeaway:** Elapsed time, CPU execution time and response time are distinct. Measure the correct metric and account for interrupts, frequency changes and counter wrap.

### How is memory allocated in an RTOS, and why prefer static allocation? {M}
RTOS objects such as tasks, stacks, queues and semaphores may use statically supplied storage or dynamically allocated memory, depending on kernel configuration.

#### 1. Dynamic task creation

```c
BaseType_t ret = xTaskCreate(worker, "worker", 256,
                            NULL, 2, &handle);
```

Check ret for failure. The FreeRTOS stack-depth argument is in stack units, not necessarily bytes.

#### 2. Static task creation

```c
static StaticTask_t tcb;
static StackType_t stack[256];

TaskHandle_t handle = xTaskCreateStatic(
    worker, "worker", 256, NULL, 2, stack, &tcb);
```

Enable the appropriate static-allocation configuration. The supplied objects must remain valid for the task's lifetime.

| Static allocation | Dynamic allocation |
|---|---|
| Capacity known in advance | Flexible runtime object creation |
| Avoids allocation failure for reserved objects | Creation may fail |
| Easier resource accounting | Allocator timing/fragmentation matters |

FreeRTOS supplies several heap implementations with different allocation, freeing and coalescing behavior. Do not assume they all support free.

**Interview takeaway:** Static allocation is often preferred for fixed real-time resources. It does not guarantee stack sizing or eliminate every runtime failure, but makes memory availability easier to analyze.

### How does an RTOS work on a multi-core (SMP) processor? {H}
An SMP (Symmetric Multiprocessing) RTOS schedules work on multiple processors that share memory. More than one task may execute simultaneously.

#### 1. Architecture

```text
Core 0: task A          Core 1: task B
       |                       |
       +-- shared kernel / ready queues --+
                   shared RAM
```

The scheduler selects tasks according to priority, affinity and the port's policy. Interprocessor notifications can request rescheduling on another core.

#### 2. Synchronization changes

Disabling interrupts on core 0 does not prevent core 1 from accessing the same object. SMP kernels use suitable locks, atomic operations and memory-ordering primitives to protect kernel and application state.

#### 3. Example

Two worker tasks can concurrently increment an atomic counter. If they instead update an ordinary shared counter without synchronization, a lost update or a C data race can occur.

#### 4. Performance concerns

Lock contention, cache false sharing, affinity restrictions and cross-core communication may limit scalability. Assign affinity only when latency, peripheral ownership or cache locality requires it, and test under concurrent load.

**Interview takeaway:** SMP adds true simultaneous execution. A single-core critical-section design must be revisited; local interrupt masking alone is not multicore synchronization.

### What are common RTOS design mistakes? {M}
Common RTOS design failures arise from incorrect assumptions about timing, ownership and execution context.

| Mistake | Better approach |
|---|---|
| Blocking API in ISR | Use documented ISR-safe signaling |
| Highest-priority task never blocks | Wait for events or periodic releases |
| Unbounded critical section | Keep protected work short and bounded |
| Inconsistent lock order | Define and enforce resource order |
| Undersized stack | Analyze stack usage and measure watermarks |
| Ignored queue-full result | Specify overflow policy and monitor drops |
| Volatile used as a lock | Use atomics, locks or safe handoff |
| Blind watchdog feeding | Verify essential task progress |

#### 1. Example failure

A high-priority UART task spins waiting for a byte. A lower-priority parser never executes even though there is no data to process. A blocking queue receive or interrupt notification allows the UART task to sleep until work is available.

#### 2. Verification

Stress burst traffic, nested interrupts, timeouts, queue saturation, stack margins and deadline misses. Test error recovery, not just the normal path.

**Interview takeaway:** RTOS correctness requires a resource and timing design. Creating tasks and assigning priorities alone does not make firmware real-time.

### How does Zephyr differ from FreeRTOS? {M}
Zephyr and FreeRTOS are both RTOS ecosystems, but they have different architectural scope and integration models.

| Zephyr | FreeRTOS |
|---|---|
| Integrated configurable OS | Lightweight real-time kernel with libraries |
| Devicetree and Kconfig commonly describe hardware/configuration | Hardware configuration often provided by vendor SDK |
| Standardized driver model and subsystems | Drivers commonly supplied by MCU vendor or application |
| Integrated networking, Bluetooth, power-management facilities | Networking/security libraries available as separate components |
| Typically CMake/west build workflows | Build workflow depends on integration |

#### 1. Zephyr example

```c
void worker(void)
{
    for (;;) {
        do_work();
        k_msleep(100);
    }
}
```

#### 2. FreeRTOS example

```c
void worker(void *arg)
{
    for (;;) {
        do_work();
        vTaskDelay(pdMS_TO_TICKS(100));
    }
}
```

Both delay the current execution context rather than busy-waiting the CPU. The examples assume suitable thread/task setup.

#### 3. Choosing a kernel

Use Zephyr when an integrated driver, devicetree, networking and board ecosystem fits the project. FreeRTOS is attractive when a small kernel with a vendor-specific HAL/SDK is sufficient. Compare target support, footprint, real-time constraints, qualification needs and team experience.

**Interview takeaway:** Compare complete product configurations, not just kernel names. Both can support preemptive real-time workloads; timing guarantees depend on system design.

