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
IPC (Inter-Process Communication) provides controlled ways for independent processes to exchange data or coordinate execution.

| Mechanism | Typical use |
|---|---|
| Pipe / FIFO | Stream between processes |
| Unix-domain socket | Local bidirectional communication |
| Shared memory | High-volume shared data |
| Message queue | Structured messages |
| Signal | Asynchronous event notification |
| Semaphore | Synchronization / resource counting |

#### 1. Example: pipe

```c
int fd[2];
if (pipe(fd) == 0) {
    // fd[0] is read end; fd[1] is write end.
}
```

Close unused ends after fork and handle partial reads/writes and EOF.

#### 2. Shared memory

Processes can map the same memory using suitable mmap/shm interfaces. This avoids some copying but requires process-shared synchronization and agreed data layout. Shared memory alone does not provide message boundaries or atomicity.

**Interview takeaway:** Choose IPC based on data volume, latency, isolation, ownership and synchronization. Signals notify; shared memory shares storage; sockets and queues provide communication abstractions.

### What is a race condition, and what is a critical section? {E}
A race condition occurs when behavior depends incorrectly on the timing or interleaving of concurrent operations. A critical section is code that must execute with suitable protection against conflicting accesses.

#### 1. Lost update

```c
count++;
```

Two threads can both read the same old count, add one and store the same new value. In C, unsynchronized conflicting accesses to an ordinary object also constitute a data race and undefined behavior.

#### 2. Protect the critical section

```c
pthread_mutex_lock(&lock);
count++;
pthread_mutex_unlock(&lock);
```

All cooperating threads must use the same lock when accessing the protected state as required. A C11 atomic counter is another solution for independent increments.

#### 3. Race condition versus data race

A higher-level race can occur even when individual accesses are atomic, for example checking availability and then reserving a resource in separate atomic steps.

**Interview takeaway:** Protect the invariant, not just an individual variable. Use the synchronization mechanism appropriate to the execution context.

### What is a spinlock, and what are its advantages and disadvantages? {M}
A spinlock provides mutual exclusion by repeatedly checking a lock until it becomes available, rather than putting the waiter to sleep.

#### 1. Conceptual C11 example

```c
#include <stdatomic.h>

static atomic_flag lock = ATOMIC_FLAG_INIT;

void acquire(void)
{
    while (atomic_flag_test_and_set_explicit(
               &lock, memory_order_acquire)) {
        // Spin.
    }
}

void release(void)
{
    atomic_flag_clear_explicit(&lock,
                               memory_order_release);
}
```

This demonstrates acquire/release semantics. Production implementations use architecture and OS-specific mechanisms to reduce contention and handle scheduling/context rules.

#### 2. Advantages and disadvantages

Spinlocks can avoid sleep/wakeup overhead for very short critical sections. They waste CPU cycles under contention and may cause cache-line traffic or deadlock if the owner cannot run.

#### 3. Kernel use

Ordinary non-RT Linux spinlocks protect short non-sleeping sections. Interrupt-side locking may require local IRQ masking. PREEMPT_RT changes spinlock_t semantics; raw spinlocks retain strict spinning behavior.

**Interview takeaway:** Spin only when the owner can make progress quickly. Do not use a naive spinlock as a general-purpose mutex or block inside a non-sleeping critical section.

### What is a semaphore, and how does it differ from a mutex in POSIX? How are semaphores used for mutual exclusion and for synchronisation? {M}
A POSIX semaphore stores a nonnegative token count. sem_wait consumes a token or waits; sem_post adds a token and can wake a waiter. A pthread mutex provides ownership-based mutual exclusion.

#### 1. Mutual exclusion with a semaphore

```c
sem_t sem;
sem_init(&sem, 0, 1);

// In each cooperating thread:
if (sem_wait(&sem) == 0) {
    update_shared_state();
    sem_post(&sem);
}
```

Production code must handle EINTR and other errors, and destroy the semaphore after all users finish. A count of one can serialize access, but a mutex is generally clearer for ownership.

#### 2. Event synchronization

Initialize the semaphore to zero. A producer posts after producing an event; a consumer waits before processing it. The signaling thread need not be the thread that waited.

| Mutex | Semaphore |
|---|---|
| Lock owner releases it | No equivalent ownership requirement |
| Protect shared state | Count resources or events |
| May support priority protocols | Token-count semantics |

**Interview takeaway:** Use mutexes for ownership-based exclusion and semaphores for signaling/counting. Protect associated shared data and check API errors.

### What is a condition variable, and how do you build a thread-safe queue with one? {M}
A condition variable allows a thread to sleep while waiting for a predicate protected by a mutex. Waiting atomically releases the mutex and reacquires it before returning.

#### 1. Bounded thread-safe queue

```c
#include <pthread.h>
#define N 16

static int q[N];
static unsigned head, tail, count;
static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t not_empty = PTHREAD_COND_INITIALIZER;
static pthread_cond_t not_full  = PTHREAD_COND_INITIALIZER;

void push(int value)
{
    pthread_mutex_lock(&lock);
    while (count == N)
        pthread_cond_wait(&not_full, &lock);
    q[tail] = value;
    tail = (tail + 1) % N;
    count++;
    pthread_cond_signal(&not_empty);
    pthread_mutex_unlock(&lock);
}

int pop(void)
{
    pthread_mutex_lock(&lock);
    while (count == 0)
        pthread_cond_wait(&not_empty, &lock);
    int value = q[head];
    head = (head + 1) % N;
    count--;
    pthread_cond_signal(&not_full);
    pthread_mutex_unlock(&lock);
    return value;
}
```

This educational example assumes successful pthread calls and no cancellation/shutdown; production code needs error and lifetime handling.

#### 2. Why use while?

A wakeup can be spurious, or another thread can consume the available item before the waiter reacquires the lock. Recheck the predicate under the mutex.

**Interview takeaway:** The condition variable is a notification mechanism, not the condition itself. Protect queue state with the mutex and wait in a loop.

### Why does an OS need a scheduler, and what criteria are used to judge scheduling algorithms? {E}
An OS scheduler selects which ready task runs on each CPU. It allocates limited CPU time while respecting priorities, resource constraints and the chosen scheduling policy.

#### 1. Evaluation criteria

| Metric | Meaning |
|---|---|
| CPU utilization | Fraction of time CPU performs useful work |
| Throughput | Jobs completed per unit time |
| Turnaround | Completion time minus arrival time |
| Waiting time | Time spent ready but not running |
| Response time | Time until first service, or a defined application response |
| Deadline misses | Jobs failing their timing requirement |

#### 2. Example

A batch scheduler may emphasize throughput, an interactive scheduler responsiveness and fairness, and a real-time scheduler bounded response/deadline satisfaction.

#### 3. Trade-offs

A very short scheduling quantum can improve responsiveness but increases context-switch overhead. Giving urgent tasks priority can delay lower-priority work. SMP scheduling also balances load and cache locality.

**Interview takeaway:** There is no universally best scheduler. Evaluate it against workload objectives and worst-case timing requirements.

### Compare FCFS, SJF, SRTF and Round Robin with a worked example. {M}
FCFS, SJF, SRTF and Round Robin are classical CPU scheduling algorithms. Consider three jobs arriving at time zero, with burst lengths A=6, B=2, C=4 ms. Ignore context-switch overhead.

#### 1. Gantt charts

```text
FCFS:  0 -- A -- 6 - B - 8 -- C -- 12
SJF:   0 - B - 2 -- C -- 6 -- A -- 12
SRTF:  same as SJF here (all arrive together)
RR (2 ms):
       0 A 2 B 4 C 6 A 8 C 10 A 12
```

#### 2. Waiting time comparison

Waiting = completion − arrival − burst (for these CPU-only jobs).

| Algorithm | A | B | C | Average |
|---|---:|---:|---:|---:|
| FCFS | 0 | 6 | 8 | 4.67 ms |
| SJF / SRTF | 6 | 0 | 2 | 2.67 ms |
| Round Robin | 6 | 2 | 6 | 4.67 ms |

#### 3. Differences

FCFS uses arrival order; SJF chooses the shortest known job without preemption. SRTF is preemptive and can replace a running job when a shorter remaining job arrives. RR rotates runnable jobs using a quantum.

SJF requires knowledge or estimation of burst lengths. SRTF can starve long jobs under continuous short arrivals; RR trades waiting time and overhead for responsiveness.

**Interview takeaway:** State arrival times, tie-breaking and quantum before computing scheduling metrics. SJF and SRTF differ when new jobs arrive during execution.

### How does the Linux scheduler work (CFS and EEVDF)? {H}
Linux has multiple scheduler classes for deadline, real-time, normal fair and other policies. The normal fair scheduler has evolved from the classic CFS selection model toward EEVDF (Earliest Eligible Virtual Deadline First) in modern kernels.

#### 1. Classic CFS idea

CFS tracks weighted virtual runtime. Tasks with less accumulated virtual runtime are favored so that CPU service approaches their weighted share. Nice values influence weights rather than acting like strict real-time priorities.

#### 2. EEVDF idea

EEVDF uses virtual service accounting and eligibility based on lag relative to a task's ideal share. Among eligible tasks, it selects according to virtual deadlines. This helps balance fairness and latency for tasks with different service requests.

```text
Runnable fair tasks
    -> virtual service / lag accounting
    -> determine eligible tasks
    -> choose earliest eligible virtual deadline
```

The implementation has evolved since EEVDF entered the fair scheduler in Linux 6.6; exact data structures and heuristics depend on the kernel version.

#### 3. SMP

Each CPU has scheduling state, with load balancing, affinity and wakeup placement influencing where tasks run. Higher scheduling classes can take precedence over fair tasks.

**Interview takeaway:** CFS and EEVDF are fair-scheduling concepts, not strict deadline guarantees. Distinguish virtual deadlines in the fair scheduler from SCHED_DEADLINE's real-time scheduling interface.

### What is the difference between SCHED_FIFO, SCHED_RR and SCHED_DEADLINE in Linux? {M}
Linux provides real-time scheduling policies for workloads needing different execution guarantees or priority behavior.

| Policy | Selection behavior |
|---|---|
| SCHED_FIFO | Highest-priority runnable RT task; no ordinary time slice among equals |
| SCHED_RR | Similar fixed-priority rules, with round-robin quantum among equals |
| SCHED_DEADLINE | Deadline-based scheduling with runtime budget and admission control |

#### 1. FIFO versus RR

A FIFO task continues until it blocks, yields, is preempted by higher-priority work or is otherwise constrained by kernel policy. RR rotates equal-priority runnable tasks at quantum expiration.

#### 2. Deadline parameters

SCHED_DEADLINE uses runtime, deadline and period parameters. For example, a task may request a runtime budget of 2 ms in every 10 ms period, with a 10 ms relative deadline. The kernel enforces its budget and applies admission rules.

#### 3. Practical constraints

Setting these policies may require privileges or resource limits. An uncontrolled high-priority task can starve ordinary tasks; kernel throttling and other system constraints may affect behavior.

**Interview takeaway:** FIFO/RR are priority-based RT policies; DEADLINE uses explicit timing budgets and deadline scheduling. A policy alone does not prove end-to-end real-time correctness.

### What is processor affinity, and when should you control it? {M}
Processor affinity restricts the CPUs on which a task is eligible to run. It can improve cache locality or help isolate latency-sensitive workloads.

#### 1. Linux example

```c
#define _GNU_SOURCE
#include <sched.h>

cpu_set_t set;
CPU_ZERO(&set);
CPU_SET(2, &set);

if (sched_setaffinity(0, sizeof set, &set) < 0) {
    // Handle error: CPU may not be available/allowed.
}
```

PID 0 applies to the calling thread. CPU numbering and permitted masks depend on the system and cgroup/cpuset configuration.

#### 2. Command-line example

```sh
taskset -c 2 ./app
```

#### 3. When useful

Pin a periodic control task to a selected CPU, keep a producer/consumer close to shared cache, or separate workloads when testing latency. IRQ affinity is a separate control.

#### 4. Trade-offs

Pinning may reduce load-balancing flexibility and overload one CPU. Isolation also requires considering IRQs, kernel housekeeping and shared hardware contention.

**Interview takeaway:** Affinity restricts placement; it does not reserve a CPU exclusively or guarantee latency. Measure whether pinning improves the actual workload.

### What are the ways a CPU can communicate with an I/O device (polling, interrupts, DMA)? {E}
The CPU can communicate with peripherals through polling, interrupts or DMA, depending on the device and workload.

| Mechanism | CPU role | Example |
|---|---|---|
| Polling | Repeatedly read status | Wait for UART TX readiness |
| Interrupt | Service hardware notification | Handle incoming GPIO event |
| DMA | Configure transfer and handle completion | Receive a block of audio samples |

#### 1. Data flow

```text
Polling: CPU -> read device status -> repeat
Interrupt: device -> interrupt controller -> CPU ISR
DMA: device <--> DMA engine / interconnect <--> memory
     CPU configures and receives completion
```

#### 2. Linux use

Drivers map registers using MMIO APIs, register IRQ handlers and use DMA mapping APIs. For high-rate networking, a hybrid interrupt/polling mechanism such as NAPI can reduce per-packet interrupt overhead.

#### 3. Trade-offs

Polling wastes cycles during long waits but can be simple and predictable for short bounded waits. Interrupts reduce idle checking but add scheduling/service overhead. DMA improves bulk transfer efficiency but adds mapping and ownership requirements.

**Interview takeaway:** Choose based on transfer size, latency, event frequency and CPU overhead. DMA does not eliminate synchronization or error handling.

### What is a system call and how does it work? {M}
A system call is a controlled interface through which a userspace program requests a kernel service, such as reading a file, mapping memory or creating a process.

#### 1. ARM64 Linux example

```asm
MOV X8, #172 // Linux AArch64 getpid syscall
SVC #0
// X0 contains the return value
```

The AArch64 Linux syscall ABI uses X8 for the syscall number and X0–X5 for up to six arguments. Applications normally call a libc wrapper rather than writing assembly.

#### 2. Execution flow

```text
User function -> syscall ABI -> SVC exception
    -> kernel entry saves state
    -> syscall dispatch and argument validation
    -> subsystem operation
    -> return result, restore state, ERET
```

On a normal non-VHE arrangement, SVC from EL0 enters the kernel at EL1. Host virtualization arrangements can differ.

#### 3. Error handling

Raw Linux syscall errors commonly use negative errno values. libc wrappers typically translate these to -1 and set errno, according to the function's interface.

**Interview takeaway:** A syscall crosses a privilege boundary through an architecture-defined exception. It is not an ordinary C function call into arbitrary kernel code.

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
