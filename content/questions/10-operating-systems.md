---
slug: operating-systems
title: Operating System Concepts
icon: 🧠
level: Intermediate
order: 10
desc: Processes and threads, process states, context switches, scheduling with worked examples, CFS/EEVDF, virtual memory, page tables, TLB maths, page replacement, synchronisation and I/O.
---
These questions come up for Linux, BSP and systems roles, and as warm-ups in RTOS interviews. University-style questions (scheduling Gantt charts, page-table sizes, TLB maths) are common in campus and early-career interviews, so worked examples are included. Each answer starts with the one-line version, then the explanation and the follow-ups. Linux details are given where they differ from the textbook view.

### What are the main jobs of an operating system kernel, and what is the difference between a monolithic kernel and a microkernel? {E}
An operating system kernel manages CPU scheduling, memory, interrupts, devices, filesystems and controlled access to system resources.

#### 1. Kernel architecture

```text
Monolithic: applications -> syscall -> kernel services/drivers
Microkernel: applications -> IPC -> user-space servers
                            microkernel: scheduling, IPC, low-level protection
```

Linux is a monolithic kernel with modular components. A microkernel such as seL4 keeps a smaller core and can place many services in separate protection domains.

| Monolithic | Microkernel |
|---|---|
| Many services execute in kernel space | Many services can execute outside the kernel |
| Direct internal calls common | IPC between components common |
| Driver faults may affect kernel | Isolation can contain some service faults |

#### 2. Example

A Linux read system call may proceed through VFS and a kernel driver without crossing separate user service processes. A microkernel-based design may send requests to a filesystem or device server through IPC.

**Interview takeaway:** The distinction is service placement and protection boundaries, not whether the kernel supports modules. Performance and reliability depend on the actual design.

### What is the difference between a process and a thread? {E}
A process is an execution environment with an address space and resources. A thread is a schedulable execution stream within that environment.

| Process | Thread |
|---|---|
| Usually separate virtual address space | Shares process address space |
| Resources such as file descriptors | Shares many process resources |
| Communication often uses IPC | Can communicate through shared objects |
| Own execution context | Own stack, registers and scheduling state |

#### 1. Example

Two threads in a process can access the same global variable. Each has its own stack and register state. Two ordinary processes have separate mappings, even if their virtual addresses happen to be identical.

#### 2. Linux implementation

Linux represents schedulable tasks using task_struct. Threads created with suitable clone flags share resources such as memory mappings and file tables. The thread group provides process-level identity.

**Interview takeaway:** Threads share memory, not a single execution context. Shared objects require synchronization; separate processes may also explicitly share memory.

### What are the states of a process, and how does a process move between them? {E}
A process or thread moves between execution states according to scheduling, waiting and termination.

```text
New -> Ready -> Running -> Exited
         ^       |
         |       v
         +---- Blocked (event / I/O / timeout)
Running -> Ready on preemption
```

#### 1. Typical states

Ready means eligible but not necessarily running. Running means executing on a CPU. Blocked means waiting for an event. A stopped task is paused by a control mechanism, and a terminated task may retain exit status until reaped.

#### 2. Linux example

```sh
ps -eo pid,stat,comm
```

Common state letters include R (running/runnable), S (interruptible sleep), D (uninterruptible sleep), T (stopped) and Z (zombie). These are Linux-specific reporting categories.

#### 3. Transition example

A read from an empty blocking pipe puts a thread to sleep. A writer supplies data, waking the reader; the scheduler later selects it to run.

**Interview takeaway:** Waking a task makes it eligible; it does not guarantee immediate execution. Linux R includes runnable tasks as well as currently running ones.

### What information does the OS keep about each process (the PCB / task_struct)? {M}
The process control block (PCB) holds information the OS needs to manage a task. Linux uses task_struct and related objects.

| Information | Purpose |
|---|---|
| PID and relationships | Identity, parent and thread group |
| Scheduling state | Priority, policy, runqueue information |
| CPU context | Saved architecture-specific state |
| Memory context | Address-space description (mm_struct for normal user tasks) |
| File and credential references | Open files, UID/GID and permissions |
| Signal/accounting state | Pending signals and execution statistics |

#### 1. Linux structure relationships

```text
task_struct
   -> mm_struct -> virtual memory areas / page tables
   -> files_struct -> file descriptors
   -> credentials
   -> architecture thread state / stack
```

Threads may share some referenced objects rather than duplicate them.

#### 2. Debugging

Use /proc/PID/status, /proc/PID/maps and appropriate kernel debugging tools to inspect task information. Internal structure fields are not a stable userspace ABI.

**Interview takeaway:** The PCB is task metadata and saved state, not a copy of all process memory. Linux separates shared resources into referenced objects.

### What happens during an OS context switch, and why is it expensive? {M}
A context switch changes which task executes on a CPU while preserving the outgoing task's ability to resume.

#### 1. Typical sequence

Save required registers and stack state, update scheduling/accounting data, choose the next runnable task, switch memory context if needed, restore the incoming execution state and resume it.

#### 2. Why expensive?

The direct cost includes scheduler and register-switch operations. Indirect cost can include lost cache locality, TLB misses and migration-related coherency traffic. ASIDs/PCIDs can avoid a full translation-cache flush when supported and managed correctly.

#### 3. Process versus thread switch

A switch between threads sharing the same address space may avoid changing the memory context, but still requires task-state and register handling. A context switch does not copy all pages or flush every cache automatically.

**Interview takeaway:** Context-switch cost depends on architecture, working set, CPU migration and memory context. Measure it under representative load rather than assuming one fixed cost.

### What happens during fork() and exec()? {M}
`fork()` creates a child process with a separate logical address space; `execve()` replaces the calling process's executable image.

#### 1. Example

```c
pid_t pid = fork();
if (pid == 0) {
    char *argv[] = {"/bin/echo", "hello", NULL};
    execv(argv[0], argv);
    _exit(127);
} else if (pid > 0) {
    waitpid(pid, NULL, 0);
}
```

Check fork failure in production. Successful exec does not return.

#### 2. Copy-on-write

After fork, parent and child may share physical pages read-only until one writes. The kernel handles a write fault and creates a private copy when necessary. File descriptors refer to shared underlying open file descriptions as specified.

#### 3. exec behavior

The process retains its identity but receives a new program image, stack and mappings. Some resources survive, while close-on-exec descriptors are closed.

**Interview takeaway:** fork creates another process; exec replaces the current process image. Copy-on-write makes fork cheaper than eagerly copying every page.

### What is a zombie process and an orphan process? {E}
A zombie is a terminated child whose exit information has not yet been collected by its parent. An orphan is a process whose parent has exited while the process still exists.

#### 1. Zombie example

A child exits, but its parent does not call wait or waitpid. The kernel retains minimal exit/accounting information so the parent can collect it. A zombie does not execute and normally no longer owns its ordinary address space.

#### 2. Reaping

```c
int status;
pid_t child = waitpid(pid, &status, 0);
```

Handle errors and interrupted waits. A parent that creates children should arrange to reap them.

#### 3. Orphan

An orphan is reparented according to Linux namespace/subreaper rules, often to PID 1 or an eligible subreaper. It can continue running normally.

**Interview takeaway:** Killing a zombie does not reap it; it has already exited. The parent or designated reaper must collect its exit status.

### What is virtual memory and why is it used? {E}
Virtual memory gives each process an address-space abstraction independent of the exact physical locations backing it. The MMU translates addresses and checks permissions.

```text
Process A VA 0x4000 -> MMU -> physical page A
Process B VA 0x4000 -> MMU -> physical page B
```

#### 1. Benefits

Process isolation, sparse address spaces, shared libraries, mapped files, demand paging, copy-on-write and controlled access to memory.

#### 2. Example

malloc can return a virtual address before all underlying physical pages have been allocated. The kernel may establish physical backing when the process first accesses a page.

#### 3. Protection

Page-table permissions restrict read, write and execution. Invalid access may generate a fault; the kernel can resolve a valid demand fault or deliver an error such as SIGSEGV.

**Interview takeaway:** Virtual memory is not synonymous with swap. Address translation and protection remain useful even when no swap is configured.

### What is paging and what is a page fault? {M}
Paging divides virtual memory into fixed-size pages and maps them to physical page frames using translation tables. A page fault occurs when an access cannot proceed under the current translation or permissions.

#### 1. Example

For a 4 KiB page, the lowest 12 address bits are the page offset. If VA 0x40001234 maps its virtual page to physical base 0x80000000, the resulting PA is 0x80000234.

#### 2. Fault handling

```text
CPU memory access -> TLB/page-table lookup
                         |
                  invalid / permission fault
                         |
                kernel checks access and VMA
                |                           |
        establish valid mapping       signal/error
```

Demand allocation, copy-on-write and loading a file-backed page can be normal faults. An illegal access may be unrecoverable.

#### 3. TLB miss

A TLB miss can trigger a hardware table walk and refill without any page fault. It is not equivalent to a missing mapping.

**Interview takeaway:** A page fault is an exception requiring fault handling, not necessarily a bug. Distinguish translation-cache misses, demand faults and invalid accesses.

### How do multi-level page tables work? Calculate the size of the page tables. {M}
Multi-level page tables divide a virtual page number into indexes for several levels. Lower-level tables are allocated only for address ranges that need mappings.

#### 1. Worked 48-bit example

Assume 4 KiB pages and 8-byte descriptors, as in one common AArch64 configuration.

```text
VA bits: [47:39] [38:30] [29:21] [20:12] [11:0]
          L0      L1      L2      L3      offset
```

Each 9-bit index selects one of 512 entries. A full table contains 512 × 8 = 4096 bytes.

#### 2. Flat table size

A 48-bit address space with 4 KiB pages has 2^36 virtual pages. An eight-byte flat entry per page would need 2^39 bytes = 512 GiB.

#### 3. Sparse mapping

For a single isolated 4 KiB page using four levels, a new hierarchy may require one 4 KiB table per level (16 KiB), plus the mapped data page. Nearby pages reuse existing tables; large block mappings can reduce table usage.

**Interview takeaway:** Multi-level tables save memory for sparse mappings at the cost of potentially more lookup steps. Actual levels, granules and supported address widths depend on the CPU and OS configuration.

### What is a TLB, and how do you calculate the effective memory access time? {M}
A Translation Lookaside Buffer (TLB) caches address translations and associated attributes, avoiding repeated page-table walks.

#### 1. Example timing model

Assume a 10 ns TLB lookup, 100 ns memory access, a one-level page table stored in memory, no overlap, and a 95% TLB hit rate.

- Hit: 10 + 100 = 110 ns.
- Miss: 10 + 100 (table entry) + 100 (data) = 210 ns.

Effective access time = 0.95 × 110 + 0.05 × 210 = 115 ns.

#### 2. Real processors

Modern processors can overlap translation and cache lookup, cache intermediate translation-table entries and walk multiple levels. Therefore, actual timing differs from this simplified model. A miss may be resolved by a hardware walk without kernel entry.

#### 3. ASIDs and invalidation

Address-space identifiers distinguish cached translations for different processes. When mappings change, the kernel performs appropriate TLB invalidation and synchronization on affected CPUs.

**Interview takeaway:** TLB caches translations, not application data. State your timing assumptions before computing effective access time; a TLB miss is not automatically a page fault.

### Why is the page size usually 4 KB? What happens with smaller or larger pages? {M}
4 KiB is a common base page size because it balances mapping granularity, page-table overhead, memory fragmentation and TLB coverage. It is not a universal architectural requirement.

#### 1. Comparison

| Smaller pages | Larger pages |
|---|---|
| Finer protection/allocation granularity | Greater TLB coverage per entry |
| Less internal fragmentation | Fewer page-table entries |
| More mappings for the same memory range | Larger allocation/fragmentation constraints |

#### 2. Example

Mapping 2 MiB using 4 KiB pages requires 512 base-page translations. If the CPU and OS support a 2 MiB block or huge-page mapping, one larger translation may cover the entire range.

#### 3. ARM64

AArch64 supports different translation granules depending on implementation and kernel configuration, commonly 4 KiB, 16 KiB or 64 KiB. Huge/block mappings are additional possibilities.

#### 4. Embedded impact

Large mappings may benefit large contiguous buffers, but memory availability, alignment and isolation requirements matter. DMA/IOMMU page sizes can differ from CPU page sizes.

**Interview takeaway:** Page size trades fragmentation and mapping flexibility against translation overhead. Check the actual system with getconf PAGESIZE instead of assuming 4096.

### What are page replacement algorithms (FIFO, LRU, Clock), and what is Belady's anomaly? {M}
Page replacement chooses which resident pages to reclaim when memory is under pressure. The goal is to keep useful pages in memory and minimize expensive faults or writeback.

| Algorithm | Selection rule |
|---|---|
| FIFO | Evict oldest loaded page |
| LRU | Evict least recently used page |
| Clock | Approximate recency using reference bits and a rotating pointer |

#### 1. Belady's anomaly

With FIFO, increasing the number of page frames can sometimes increase the number of faults. A standard reference string is:

```text
1 2 3 4 1 2 5 1 2 3 4 5
FIFO with 3 frames: 9 faults
FIFO with 4 frames: 10 faults
```

Exact LRU has the stack property, so it does not suffer this anomaly.

#### 2. Real Linux

Linux reclaim is more complex than a textbook FIFO or LRU: it considers page activity, file-backed versus anonymous memory, writeback, reclaim context and kernel configuration.

**Interview takeaway:** Replacement is an approximation of future reuse. More RAM does not make every possible replacement algorithm monotonic, and real OS reclaim involves more than selecting a victim page.

### What is an inverted page table? {H}
An inverted page table organizes entries primarily by physical page frame rather than maintaining one flat entry for every virtual page of every process.

#### 1. Concept

A physical-frame entry records which virtual page/address-space identity maps to that frame, together with required attributes or associated metadata.

```text
(ASID / process identity, virtual page)
             |
       hash / lookup
             |
       physical frame entry
```

#### 2. Advantage and cost

For a system with 1 GiB physical RAM and 4 KiB frames, there are 262,144 frames. A hypothetical 16-byte entry per frame uses 4 MiB for the main array. Additional hash, alias and metadata structures can increase the cost.

A reverse organization can reduce storage for very large sparse virtual address spaces, but translation lookup, shared pages and aliases complicate implementation.

#### 3. Modern Arm

Ordinary AArch64 hardware translation uses architecture-defined hierarchical translation tables, not a generic inverted table. OS reverse-mapping structures serve related but distinct purposes.

**Interview takeaway:** Inverted tables scale primarily with physical frames, while ordinary per-address-space tables organize mappings by virtual address.

### What is the difference between an MMU and an MPU? {E}
An MMU (Memory Management Unit) translates virtual addresses and enforces memory attributes and permissions. An MPU (Memory Protection Unit) enforces access permissions and attributes for configured regions without general page-based virtual address translation.

| MMU | MPU |
|---|---|
| Virtual-to-physical mapping | Region protection |
| Page tables and TLB common | Configured regions common |
| Process address-space isolation | Task/region isolation |
| Common in Cortex-A systems | Common in Cortex-M systems |

#### 1. Example

With an MMU, two processes can use virtual address 0x4000 mapped to different physical frames. With an MPU, a task may be permitted to access only its stack and selected peripherals at their existing addresses.

#### 2. Embedded considerations

Linux usually uses an MMU on application processors; no-MMU Linux configurations exist on supported platforms. An MPU-aware RTOS can restrict unprivileged tasks. Device DMA requires its own protection/translation mechanisms where applicable.

**Interview takeaway:** An MPU protects address regions; an MMU adds address translation and protection. Neither automatically protects every independent DMA master.

### What are the common IPC mechanisms? {E}
**Short answer:** Processes communicate with **pipes and FIFOs** (byte streams), **message queues** (discrete messages), **shared memory** (fastest, but needs separate synchronisation), **semaphores** (synchronisation), **signals** (asynchronous notifications), and **sockets** (Unix domain locally, TCP/UDP over the network). Higher-level frameworks such as D-Bus, gRPC and Android Binder are built on top of these.

| Mechanism | Data | Direction | Related processes only? | Notes |
|---|---|---|---|---|
| Pipe (`pipe()`) | byte stream | one-way | yes (inherited fd) | `ls | grep` |
| FIFO (`mkfifo`) | byte stream | one-way | no (has a path name) | |
| POSIX message queue (`mq_open`) | messages with priority | either | no | `mq_notify` for async notification |
| Shared memory (`shm_open` + `mmap`) | anything | both | no | zero-copy; add a mutex/semaphore in the shared region |
| Semaphore (`sem_open`) | none (counter) | – | no | synchronisation only |
| Signal | a signal number (+ small value with `sigqueue`) | one-way | no | asynchronous, limited data |
| Unix domain socket | stream or datagram | both | no | can pass file descriptors (`SCM_RIGHTS`) and credentials |
| TCP/UDP socket | stream / datagram | both | no, across machines | |
| `eventfd`, `signalfd`, `timerfd` | counters/events as fds | – | – | integrate with `epoll` |

**How to choose**

- Large data, high rate, same machine: **shared memory** with a ring buffer and a lightweight notification (eventfd, futex, semaphore).
- Request/response between services: **Unix domain sockets** (or D-Bus/gRPC on top).
- Simple parent → child streaming: **pipe**.
- Small prioritised messages: **POSIX message queue**.
- "Wake up / stop" notifications: **signals** or eventfd.

**Embedded Linux examples:** a camera pipeline passes frame buffers between processes as **dma-buf file descriptors** over a Unix socket (zero copy). Android uses **Binder** for almost all IPC. Automotive middleware (SOME/IP, DDS) uses sockets and shared memory underneath.

**RTOS comparison:** without separate address spaces, RTOS tasks use queues, semaphores, event groups and direct-to-task notifications; "shared memory" is simply a global variable plus a mutex.

### What is a race condition, and what is a critical section? {E}
**Short answer:** A race condition is a bug where the result depends on the timing of two or more concurrent activities that access shared data, at least one of them writing. A **critical section** is the piece of code that accesses that shared data and must not be executed by more than one task at a time. Protecting critical sections (mutual exclusion) prevents races.

**The classic example: `count++` is not atomic.** It is three steps: load, add, store.

```
Thread A: load count (5)
Thread B: load count (5)
Thread A: add 1, store 6
Thread B: add 1, store 6      ← one increment lost; expected 7
```

**Ways to protect a critical section**

| Technique | When |
|---|---|
| Mutex | threads/tasks; the section may block |
| Spinlock | very short sections, multi-core, cannot sleep (kernel, ISRs with IRQs disabled) |
| Disable interrupts | single-core MCU, task vs ISR, very short sections |
| Atomic operations (`stdatomic.h`, `LDREX`/`STREX`, `LDADD`) | single variables, counters, flags |
| Avoid sharing | message passing, per-thread data, single owner |

**Requirements for a correct critical-section solution:** mutual exclusion (only one inside), progress (if nobody is inside, someone waiting can enter), and bounded waiting (nobody waits forever).

**Can a task be pre-empted while inside a critical section?** Yes, if it is protected by a mutex: the task can be pre-empted, and others trying to enter will block until it resumes and unlocks. That is fine for correctness, but it can cause **priority inversion**, which is why mutexes have priority inheritance. If the critical section is protected by **disabling interrupts or pre-emption** (or a spinlock in the kernel), the task cannot be pre-empted there, so such sections must be very short.

**Finding races:** ThreadSanitizer (`-fsanitize=thread`), Helgrind, the kernel's KCSAN and lockdep, code review of every shared variable, and stress tests on multi-core hardware. Races are timing-dependent, so "it worked in testing" proves little.

### What is a spinlock, and what are its advantages and disadvantages? {M}
**Short answer:** A spinlock is a lock where a waiting thread repeatedly checks ("spins on") the lock variable in a loop instead of sleeping. It is very fast when the lock is held only briefly and the holder is running on another core, because there is no context switch. It wastes CPU time if the wait is long, and it is useless or dangerous on a single core if the holder can be pre-empted.

```c
#include <stdatomic.h>

typedef struct { atomic_flag f; } spinlock_t;
#define SPINLOCK_INIT { ATOMIC_FLAG_INIT }

static inline void spin_lock(spinlock_t *l)
{
    while (atomic_flag_test_and_set_explicit(&l->f, memory_order_acquire))
        ;   /* spin; real implementations add a pause/WFE hint here */
}

static inline void spin_unlock(spinlock_t *l)
{
    atomic_flag_clear_explicit(&l->f, memory_order_release);
}
```

The **acquire**/**release** ordering makes sure memory accesses inside the critical section cannot move outside it.

**Advantages**

- No context switch: lowest latency for very short critical sections.
- Can be used where sleeping is not allowed: interrupt handlers and other atomic contexts in the kernel.
- Simple, small.

**Disadvantages**

- Burns CPU while waiting; with many waiters it wastes a lot of cycles and memory bandwidth (cache-line bouncing).
- On a **single core** with pre-emption, a waiter spins for its whole time slice while the holder cannot run. The kernel avoids this by disabling pre-emption while a spinlock is held.
- If an interrupt handler on the same CPU tries to take a lock that the interrupted code already holds, it deadlocks: use `spin_lock_irqsave()`.
- Not fair in the simplest form (a waiter can starve); **ticket locks** and **queued spinlocks (MCS/qspinlock)** fix fairness and cache traffic.
- The holder must never sleep.

**On ARM:** the lock is built from exclusive load/store (`LDAXR`/`STXR`) or ARMv8.1 atomics (`CAS`, `SWPA`), and waiters use `WFE` (wait for event) so the core sleeps until the lock line changes, saving power.

**Rule of thumb:** spinlock if the critical section is shorter than about two context switches and cannot sleep; mutex otherwise. In user space, use a mutex: glibc's `pthread_mutex` already spins briefly before sleeping (adaptive mutexes), and user-space spinning cannot disable pre-emption.

### What is a semaphore, and how does it differ from a mutex in POSIX? How are semaphores used for mutual exclusion and for synchronisation? {M}
**Short answer:** A semaphore is an integer counter with two atomic operations: **wait** (`P`, `sem_wait`: decrement, block if it would go below zero) and **post** (`V`, `sem_post`: increment, wake a waiter). A mutex is a lock with an **owner**: only the thread that locked it may unlock it, and it can support priority inheritance and error checking. Use a mutex for mutual exclusion; use a semaphore for signalling between tasks or counting resources.

**Pattern 1: mutual exclusion** (semaphore initialised to **1**)

```c
sem_t s;
sem_init(&s, 0, 1);       /* 1 = one task may enter */

/* in each task */
sem_wait(&s);
/* critical section */
sem_post(&s);
```

**Pattern 2: synchronisation / signalling** (initialised to **0**): task B must not continue until task A has finished step 1.

```c
sem_t done;
sem_init(&done, 0, 0);    /* 0 = event has not happened yet */

/* task A */                    /* task B */
do_step1();                     sem_wait(&done);   /* blocks until A posts */
sem_post(&done);                do_step2();
```

Whatever order the scheduler runs them in (even on one CPU, even if B starts first), `do_step2()` always runs after `do_step1()`.

**Pattern 3: counting resources** (initialised to N): a pool of N buffers or connections; `sem_wait` takes one, `sem_post` returns one.

**Mutex vs semaphore**

| | Mutex | Semaphore |
|---|---|---|
| Value | locked / unlocked | 0..N |
| Ownership | yes, only the owner unlocks | no, any task may post |
| Priority inheritance | yes (`PTHREAD_PRIO_INHERIT`) | no |
| Recursive locking | optional (`PTHREAD_MUTEX_RECURSIVE`) | no |
| Can post from a signal handler/ISR | no | `sem_post` is async-signal-safe |
| Typical use | protect shared data | signal events, count resources |

**Why not use a binary semaphore as a mutex?** No owner means no priority inheritance (priority inversion risk) and no protection against another task releasing a lock it does not hold.

**POSIX details:** unnamed semaphores (`sem_init`, can be shared between processes if placed in shared memory with `pshared = 1`) and named ones (`sem_open("/name")`). The Linux implementation is built on **futexes**, so an uncontended wait/post never enters the kernel.

### What is a condition variable, and how do you build a thread-safe queue with one? {M}
**Short answer:** A condition variable lets a thread sleep until some condition on shared data becomes true, without busy-waiting. It is always used together with a mutex that protects the data, and the wait is always inside a `while` loop that re-checks the condition, because wake-ups can be spurious and another thread may get there first.

```c
#include <pthread.h>
#include <stdbool.h>

#define QSIZE 16

typedef struct {
    int buf[QSIZE];
    unsigned head, tail, count;
    pthread_mutex_t m;
    pthread_cond_t not_empty, not_full;
} queue_t;

void q_init(queue_t *q)
{
    q->head = q->tail = q->count = 0;
    pthread_mutex_init(&q->m, NULL);
    pthread_cond_init(&q->not_empty, NULL);
    pthread_cond_init(&q->not_full, NULL);
}

void q_put(queue_t *q, int v)
{
    pthread_mutex_lock(&q->m);
    while (q->count == QSIZE)                       /* re-check after every wake-up */
        pthread_cond_wait(&q->not_full, &q->m);     /* unlocks m, sleeps, re-locks m */
    q->buf[q->tail] = v;
    q->tail = (q->tail + 1) % QSIZE;
    q->count++;
    pthread_cond_signal(&q->not_empty);
    pthread_mutex_unlock(&q->m);
}

int q_get(queue_t *q)
{
    pthread_mutex_lock(&q->m);
    while (q->count == 0)
        pthread_cond_wait(&q->not_empty, &q->m);
    int v = q->buf[q->head];
    q->head = (q->head + 1) % QSIZE;
    q->count--;
    pthread_cond_signal(&q->not_full);
    pthread_mutex_unlock(&q->m);
    return v;
}
```

**Why `pthread_cond_wait` takes the mutex:** it releases the mutex and goes to sleep **atomically**. If you unlocked first and then slept, the producer could add an item and signal in between, and the wake-up would be lost.

**Why a `while` and not an `if`:**

- POSIX allows **spurious wake-ups**.
- With several consumers, another consumer may take the item between the signal and this thread re-acquiring the mutex.

**`signal` vs `broadcast`:** `pthread_cond_signal` wakes at least one waiter; `pthread_cond_broadcast` wakes all (use when the state change may let several waiters proceed, or when waiters wait for different conditions on the same variable).

**Common mistakes:** changing the shared state without holding the mutex, waiting without a predicate (a signal sent before the wait is lost forever, since condition variables have no memory), and holding the mutex while doing slow work.

**C11 / C++ equivalents:** `cnd_wait`/`mtx_t` in `<threads.h>`, `std::condition_variable` in C++. In an RTOS, the same producer/consumer is usually a **message queue**, which bundles the buffer, the lock and the blocking.

### Why does an OS need a scheduler, and what criteria are used to judge scheduling algorithms? {E}
**Short answer:** There are usually more runnable tasks than CPUs, and tasks often wait for I/O. The scheduler decides which ready task runs on each CPU and for how long, so that the CPU is kept busy while some tasks wait, interactive tasks respond quickly, and real-time tasks meet their deadlines. Algorithms are judged on CPU utilisation, throughput, turnaround time, waiting time, response time, fairness and, for real-time systems, deadline misses and predictability.

**Criteria**

| Criterion | Definition | Goal |
|---|---|---|
| CPU utilisation | fraction of time the CPU does useful work | maximise |
| Throughput | jobs completed per unit time | maximise |
| Turnaround time | completion time − arrival time | minimise |
| Waiting time | time spent in the ready queue (turnaround − burst, for CPU-only jobs) | minimise |
| Response time | arrival → first time it runs (or first output) | minimise (interactive) |
| Fairness | each task gets a fair share; no starvation | ensure |
| Deadlines / jitter | real-time tasks finish on time with low variation | guarantee |

These conflict: short time slices improve response time but add context-switch overhead and reduce throughput; favouring short jobs minimises average waiting time but can starve long ones.

**How scheduling relates to the process life cycle:** the scheduler only chooses among **Ready** tasks. It runs when the current task blocks (Running → Blocked), exits, or is pre-empted (timer tick, or a higher-priority task becomes Ready because an interrupt or another task woke it).

**Pre-emptive vs non-pre-emptive:** in a non-pre-emptive (cooperative) scheduler, a task keeps the CPU until it blocks or yields; in a pre-emptive one the OS can take the CPU away at any time. All general-purpose OSes and most RTOSes are pre-emptive.

**System calls and scheduling:** a system call is a natural scheduling point. Blocking calls (`read` on an empty socket, `sleep`, `pthread_mutex_lock` on a held lock) move the task to Blocked and invoke the scheduler; on return from any system call or interrupt, the kernel checks whether a reschedule is needed.

### Compare FCFS, SJF, SRTF and Round Robin with a worked example. {M}
**Short answer:** **FCFS** runs jobs in arrival order (simple, but short jobs wait behind long ones). **SJF** picks the shortest next CPU burst (optimal average waiting time if bursts are known, non-pre-emptive). **SRTF** is the pre-emptive version: a newly arrived job pre-empts the current one if its burst is shorter than the remaining time. **Round Robin** gives each job a fixed time slice in turn (fair, good response time; performance depends on the quantum).

**Example processes (times in ms)**

| Process | Arrival | Burst |
|---|---|---|
| P1 | 0 | 8 |
| P2 | 1 | 4 |
| P3 | 2 | 9 |
| P4 | 3 | 5 |

Waiting time = finish − arrival − burst.

**FCFS**

```
| P1 0-8 | P2 8-12 | P3 12-21 | P4 21-26 |
```

Waiting: P1 0, P2 7, P3 10, P4 18 → **average 8.75 ms**.

**SJF (non-pre-emptive):** at t = 0 only P1 is there, so it runs to completion. At t = 8 the shortest is P2 (4), then P4 (5), then P3 (9).

```
| P1 0-8 | P2 8-12 | P4 12-17 | P3 17-26 |
```

Waiting: P1 0, P2 7, P4 9, P3 15 → **average 7.75 ms**.

**SRTF (pre-emptive SJF):** at t = 1, P2 (4) is shorter than P1's remaining 7, so P2 pre-empts.

```
| P1 0-1 | P2 1-5 | P4 5-10 | P1 10-17 | P3 17-26 |
```

Waiting: P1 17−0−8 = 9, P2 0, P3 15, P4 2 → **average 6.5 ms** (the best of the four).

**Round Robin, quantum 4 ms** (new arrivals join the queue before a pre-empted job is re-queued)

```
| P1 0-4 | P2 4-8 | P3 8-12 | P4 12-16 | P1 16-20 | P3 20-24 | P4 24-25 | P3 25-26 |
```

Finish: P1 20, P2 8, P3 26, P4 25. Waiting: P1 12, P2 3, P3 15, P4 17 → **average 11.75 ms**, worse average waiting, but every job got the CPU within 12 ms of arriving (best worst-case response).

**Comparison**

| Algorithm | Pre-emptive | Avg waiting | Starvation? | Notes |
|---|---|---|---|---|
| FCFS | no | poor (convoy effect) | no | simplest |
| SJF | no | optimal among non-pre-emptive | yes, for long jobs | needs burst prediction |
| SRTF | yes | optimal | yes | more context switches |
| RR | yes | often worse | no | response time bounded by (n−1) × quantum |
| Priority | either | depends | yes, fixed by **aging** | RTOS default |

**Predicting bursts:** real schedulers do not know burst lengths, so SJF uses an exponential average of previous bursts: `τ(n+1) = α·t(n) + (1−α)·τ(n)`.

**Related: SETF (shortest elapsed time first)** picks the job that has run the *least* so far. It needs no prediction and favours new and short jobs, the idea behind multilevel feedback queues: new jobs start at high priority and sink as they use CPU time.

**Quantum choice for RR:** too small → overhead dominates; too large → becomes FCFS. A rule of thumb: 80% of CPU bursts should be shorter than the quantum.

### How does the Linux scheduler work (CFS and EEVDF)? {H}
**Short answer:** For normal tasks, Linux tries to give each runnable task a fair share of CPU time weighted by its nice value. **CFS** (Completely Fair Scheduler, 2.6.23 to 6.5) tracked each task's **virtual runtime** (actual runtime scaled by its weight), kept runnable tasks in a **red-black tree** sorted by vruntime, and always ran the task with the smallest vruntime (the leftmost node). Since Linux 6.6, **EEVDF** (Earliest Eligible Virtual Deadline First) replaced CFS's picking rule: it still uses weighted virtual time, but among tasks that are "eligible" (not ahead of their fair share) it picks the one with the earliest **virtual deadline**, which gives better latency control.

**Weights and nice values**

- Nice ranges from −20 (highest priority) to +19 (lowest). Nice 0 has weight **1024**; each nice step changes the weight by about **1.25×**, so a task one nice level higher gets about 10% more CPU than its neighbour.
- `vruntime += actual_runtime × 1024 / weight`. A high-weight task's vruntime grows slowly, so it gets picked more often.

**Example:** two CPU-bound tasks, one at nice 0 (weight 1024) and one at nice 5 (weight 335). CPU shares are 1024 / (1024 + 335) ≈ **75%** and ≈ **25%**.

**Why a red-black tree:** insert and delete are O(log n), and the leftmost node (smallest vruntime) is cached, so picking the next task is O(1). A task that blocked for a long time is placed relative to the current minimum vruntime when it wakes, so it gets a quick turn without being able to monopolise the CPU.

**EEVDF in one paragraph:** each task has a **lag** (how much service it is owed). A task is *eligible* if its lag is ≥ 0. Its virtual deadline is roughly its eligible time plus `slice / weight`. The scheduler picks the eligible task with the earliest virtual deadline. Tasks can request shorter slices (latency-sensitive work) without getting more total CPU.

**Scheduling classes (checked in priority order)**

| Class | Policies | Use |
|---|---|---|
| stop | – | internal (CPU hotplug, migration) |
| deadline | `SCHED_DEADLINE` | runtime/period/deadline reservations (EDF + CBS) |
| real-time | `SCHED_FIFO`, `SCHED_RR` (priority 1–99) | soft real-time, control loops |
| fair | `SCHED_NORMAL` (`SCHED_OTHER`), `SCHED_BATCH` | everything else |
| idle | `SCHED_IDLE` | lowest-priority background work |

**Multi-core:** each CPU has its own runqueue; the load balancer migrates tasks between CPUs considering cache topology and, on big.LITTLE/DynamIQ systems, **energy-aware scheduling** (place small tasks on efficient cores).

**Tools:** `nice`, `renice`, `chrt` (real-time policy), `taskset` (affinity), `/proc/<pid>/sched`, `perf sched`, and `sched_ext` (6.12+) for BPF-based custom schedulers.

### What is the difference between SCHED_FIFO, SCHED_RR and SCHED_DEADLINE in Linux? {M}
**Short answer:** All three are real-time policies that always pre-empt normal tasks. **SCHED_FIFO** runs the highest-priority task until it blocks, yields or is pre-empted by a higher priority; tasks of equal priority wait their turn. **SCHED_RR** is the same but adds a time slice so equal-priority tasks rotate. **SCHED_DEADLINE** schedules by deadlines (EDF) using a declared runtime, deadline and period, and the kernel admits a task only if the total load is feasible.

| | SCHED_FIFO | SCHED_RR | SCHED_DEADLINE |
|---|---|---|---|
| Priority | static 1–99 | static 1–99 | not priority-based; earliest deadline first |
| Equal priority | runs until it blocks/yields | time slice (default 100 ms), then rotates | – |
| Parameters | priority | priority | runtime, deadline, period |
| Admission control | no | no | yes (rejects overload) |
| Protection from overrun | no | no | yes: throttled when it exceeds its runtime |

```bash
chrt -f 80 ./control_loop            # SCHED_FIFO priority 80
chrt -r 50 ./worker                  # SCHED_RR priority 50
chrt -d --sched-runtime 2000000 --sched-deadline 5000000 --sched-period 10000000 0 ./task
```

**Dangers and safeguards**

- A runaway `SCHED_FIFO` task at a high priority starves everything else on its CPU, including shells you would use to fix it. Linux reserves 5% of CPU for non-RT tasks by default (`/proc/sys/kernel/sched_rt_runtime_us` = 950000 out of 1000000), which keeps the system usable but adds latency to RT tasks when it kicks in.
- RT priority does not help if the task blocks on a page fault, a lock held by a normal task, or slow I/O: lock memory with `mlockall()`, use priority-inheritance mutexes, and pre-allocate.

**Soft vs hard real time on Linux:** standard Linux gives soft real-time behaviour: worst-case latencies of hundreds of µs to ms are possible. **PREEMPT_RT** (fully merged into mainline in 6.12) makes almost all kernel code pre-emptible, runs interrupt handlers in threads and turns spinlocks into sleeping, priority-inheriting locks, giving worst-case latencies of tens of µs on good hardware. Measure with `cyclictest`. For hard real time with guaranteed deadlines, many products still use an MCU or a separate core running an RTOS next to Linux.

### What is processor affinity, and when should you control it? {M}
**Short answer:** Processor (CPU) affinity is the set of CPU cores a thread is allowed to run on. By default the scheduler may move a thread to any core; pinning it to one core or a group keeps its caches warm, avoids migration costs, and isolates time-critical work from the rest of the system.

```bash
taskset -c 2 ./control_loop        # run on CPU 2 only
taskset -pc 0-1 1234               # change affinity of PID 1234
```

```c
#define _GNU_SOURCE
#include <sched.h>

cpu_set_t set;
CPU_ZERO(&set);
CPU_SET(2, &set);
sched_setaffinity(0, sizeof(set), &set);     /* 0 = calling thread */
/* or pthread_setaffinity_np(pthread_self(), sizeof(set), &set); */
```

**Benefits**

- **Cache locality:** the thread's data stays in that core's L1/L2.
- **Predictable latency for real-time work:** combine with `isolcpus=` or cpusets so no other tasks run on that core, `nohz_full=` to stop the scheduler tick there, and move interrupts away (`/proc/irq/<n>/smp_affinity`).
- **NUMA:** keep threads near the memory they use (`numactl`).
- **Heterogeneous CPUs:** keep a heavy task on a big core, or background work on LITTLE cores.

**Risks:** pinning can leave cores idle while others are overloaded, because the load balancer cannot move pinned tasks. Only pin when you have measured a benefit.

**Interrupt affinity** is the related idea for IRQs: steer a network card's interrupts to specific cores (often matched with the threads that process the packets: RSS/RPS).

**Parallel programs:** for data-parallel work (OpenMP, a thread pool), pinning one worker per core avoids threads bouncing between cores; OpenMP has `OMP_PROC_BIND` and `OMP_PLACES` for this.

### What are the ways a CPU can communicate with an I/O device (polling, interrupts, DMA)? {E}
**Short answer:** With **polling** the CPU repeatedly reads a status register until the device is ready (simple, lowest latency for very fast devices, but wastes CPU time). With **interrupts** the device signals the CPU when it needs attention, and the CPU does other work meanwhile. With **DMA** a DMA controller copies whole blocks of data between the device and memory without the CPU, interrupting only when the transfer is done. Device registers are accessed through memory-mapped I/O (ARM) or a separate I/O port space (x86 `in`/`out`).

| | Polling | Interrupt-driven | DMA |
|---|---|---|---|
| CPU cost per byte | high (busy loop) | one interrupt per event/byte | almost none (one interrupt per block) |
| Latency | lowest if the CPU is already looping | interrupt entry latency (µs) | setup cost, then hardware speed |
| Complexity | trivial | ISR, shared data protection | buffer management, cache coherency, descriptors |
| Good for | very short waits, boot code, very high rates (NAPI busy polling) | keyboards, UART at low rates, buttons, timers | disks, network, audio, displays, high-rate ADC/SPI |

**Interrupt handling basics:** the device asserts an IRQ line → interrupt controller (GIC, NVIC, APIC) → CPU saves state and jumps to the vector → the handler acknowledges the device and does minimal work → defers the rest (bottom half, tasklet, workqueue, threaded IRQ, or an RTOS task) → returns.

**Hybrid approaches:** Linux network drivers use **NAPI**: the first packet raises an interrupt, then the driver disables the interrupt and polls while traffic is heavy, switching back to interrupts when it is quiet. This avoids an "interrupt storm" at high packet rates.

**DMA caveats:** on CPUs without hardware cache coherency for DMA (many Cortex-A/M7 systems), the driver must clean the cache before a device reads memory and invalidate it before the CPU reads what a device wrote. Linux's DMA API (`dma_map_single`, `dma_alloc_coherent`) handles this.

**Watching interrupts on Linux:** `/proc/interrupts` shows per-CPU counts for every IRQ. Sampling it over a minute and dividing by 60 gives a stable per-second rate, smoothing out bursts that a one-second sample would exaggerate or miss.

### What is a system call and how does it work? {M}
**Short answer:** A system call is the controlled entry point from a user program into the kernel, used whenever the program needs something only the kernel may do (I/O, memory, creating processes). The C library puts the syscall number and arguments in registers and executes a trap instruction (`svc #0` on ARM64, `syscall` on x86-64). The CPU switches to kernel mode at a fixed entry point; the kernel checks the arguments, runs the handler from the syscall table and returns the result. Negative return values become `errno` in libc.

**ARM64 example (what `write(1, "hi\n", 3)` becomes)**

```asm
mov  x8, #64          // __NR_write on arm64
mov  x0, #1           // fd
adr  x1, msg          // buffer
mov  x2, #3           // count
svc  #0               // trap to EL1
// x0 now holds the result (bytes written, or -errno)
```

**Inside the kernel (ARM64):** the `SVC` exception goes to the EL1 vector `el0_sync` → `el0_svc` → `invoke_syscall()`, which indexes `sys_call_table[x8]` and calls, e.g., `__arm64_sys_write()`. User pointers are never dereferenced directly: the kernel uses `copy_from_user()`/`copy_to_user()`, which handle faults safely.

**Why system calls exist (the rationale):**

- **Protection:** user code runs at EL0 / ring 3 and cannot touch hardware or other processes' memory. The only way in is through checked entry points.
- **Abstraction:** programs call `read()` on any file, pipe, socket or device; the kernel handles the details.
- **Resource management:** the kernel arbitrates between programs (scheduling, quotas, permissions).

**Effect on scheduling:** a system call is a point where the kernel may switch tasks: blocking calls put the caller to sleep and run another task; on the way out, if a higher-priority task became ready, the kernel reschedules before returning.

**Cost and how Linux avoids it**

- A syscall costs on the order of 100 ns to a few µs (mode switch, mitigations).
- **vDSO:** `clock_gettime()` and `gettimeofday()` run entirely in user space by reading kernel-maintained data.
- Batching interfaces: `readv`/`writev`, `sendmmsg`, `io_uring` (submission/completion rings with few or no syscalls).

**Tools:** `strace -f ./prog` lists every syscall with arguments and results; `strace -c` gives counts and times; `ltrace` shows library calls.

### What is thrashing? {E}
**Short answer:** Thrashing is when the combined working sets of the running processes do not fit in physical memory, so the system spends most of its time moving pages between RAM and swap (or re-reading evicted file pages) instead of doing useful work. CPU utilisation drops, disk I/O is saturated, and everything becomes extremely slow.

**The feedback loop that makes it worse:** low CPU utilisation (everyone is waiting for page-ins) can trick a naive OS or administrator into starting more work, which increases memory pressure further.

**Symptoms on Linux**

- `vmstat 1`: high `si`/`so` (swap in/out) and `wa` (I/O wait), low `us`/`sy`.
- `/proc/pressure/memory` (PSI): high "some" and "full" percentages.
- Major page faults rising in `sar -B` or `perf stat`.

**Working set:** the set of pages a process has used recently. If the sum of all working sets is larger than RAM, thrashing follows no matter how good the replacement algorithm is.

**Fixes**

- Add RAM, or reduce memory use (fewer processes, smaller caches, fix leaks).
- Limit memory per service with **cgroups** (`memory.max`, `memory.high`) so one runaway process cannot drag the system down.
- Let the **OOM killer** or a user-space early-OOM daemon (`systemd-oomd`, `earlyoom`) kill a process before the system becomes unresponsive.
- **zram** (compressed swap in RAM) on embedded devices without disk swap, as Android and ChromeOS do.
- Avoid swap entirely on real-time systems and use `mlockall()` for time-critical processes.

**Embedded note:** most embedded Linux devices have no swap, so instead of thrashing on swap they thrash on **file-backed pages**: code pages of running programs are evicted and re-read from flash over and over, which also wears the flash. Watch memory headroom in testing.

### Walk through what happens when malloc(4 KB) is called on ARM64 Linux. {M}
**Short answer:** malloc(4096) is a user-space allocator request. The allocator may reuse existing space, or obtain virtual memory through brk or mmap. Physical pages are often allocated on demand when accessed.

```c
char *ptr = malloc(4096);
if (ptr) {
    ptr[0] = 'A';
    free(ptr);
}
```

**Typical flow (glibc, anonymous memory, 4 KiB base pages assumed)**

1. malloc checks allocator-managed free chunks and arenas.
2. If more space is needed, the allocator may call brk or mmap. On ARM64, the SVC instruction enters the kernel from EL0 (normally EL1).
3. The kernel establishes or extends a virtual memory area (VMA). Not every page needs physical backing yet.
4. malloc returns a virtual address; allocator bookkeeping may already have touched some pages.
5. A subsequent store uses the MMU and TLB. On a TLB miss, hardware walks the page tables.
6. If a valid anonymous mapping has no writable physical page, a page fault enters the kernel. Linux checks permissions, allocates and zeroes a page as necessary, and updates the page tables.
7. The instruction is retried; the write may initially update only the CPU cache.

```asm
MOV X0, #4096
BL  malloc
CBZ X0, failed
MOV W1, #65
STRB W1, [X0]
failed:
```

A representative Linux fault path is do_mem_abort -> do_page_fault -> handle_mm_fault -> __handle_mm_fault -> handle_pte_fault, with anonymous-page handling such as do_anonymous_page. Exact paths depend on the kernel and mapping.

**Follow-ups:** malloc is not a syscall; not every allocation causes a fault; 4096 bytes need not be page-aligned and may span pages; ARM64 Linux may use other base page sizes. free does not necessarily release memory to the kernel immediately.

### What is a memory barrier, and why is it needed on ARM? {M}
**Short answer:** A memory barrier constrains compiler and/or hardware reordering of memory operations. Cache coherency alone does not guarantee ordering between different addresses.

Suppose a producer writes data = 100 and then flag = 1. On a weakly ordered architecture, without proper synchronization a consumer may see the flag before the data is visible.

Linux kernel example (initially data and flag are zero; one producer publishes once):

```c
/* Producer */
WRITE_ONCE(data, 100);
smp_wmb();
WRITE_ONCE(flag, 1);

/* Consumer */
if (READ_ONCE(flag) == 1) {
    smp_rmb();
    value = READ_ONCE(data);
}
```

Alternatively, use smp_store_release(&flag, 1) and smp_load_acquire(&flag) for this publication pattern.

| ARM instruction | Purpose |
|---|---|
| DMB | Orders relevant memory accesses across the barrier. |
| DSB | Also waits for relevant preceding operations to complete as required by its scope and type. |
| ISB | Synchronizes subsequent instruction execution with context changes. |

| Linux API | Purpose |
|---|---|
| smp_rmb() | Orders reads across the barrier. |
| smp_wmb() | Orders writes across the barrier. |
| smp_mb() | Orders reads and writes across the barrier. |
| barrier() | Compiler barrier only. |

**Interview trap:** Barriers do not make read-modify-write operations atomic, and do not necessarily flush caches to DRAM. SMP barriers are for CPU-to-CPU ordering; device drivers must use the appropriate MMIO accessors and DMA barriers for device communication. In portable user-space C, use C11 atomics with release/acquire ordering instead of plain shared variables.
