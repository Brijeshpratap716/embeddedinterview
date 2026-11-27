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
**Short answer:** Virtual memory gives every process its own private address space. The program uses virtual addresses, and the MMU translates each one to a physical address through page tables set up by the OS. This provides isolation between processes, lets the OS use physical memory flexibly (scattered pages, only what is used, swapping), and makes sharing and memory-mapped files easy.

**Benefits**

- **Isolation and protection:** a process cannot read or write another process's memory or the kernel's; each page has permissions (read, write, execute, user/kernel).
- **Contiguous view of scattered memory:** a 100 MB array looks contiguous to the program even though its physical pages are spread across RAM.
- **Demand paging and overcommit:** pages get physical frames only when first touched. A process can reserve a large heap and use a little of it.
- **Swapping:** rarely used pages can be moved to disk to free RAM.
- **Sharing:** shared libraries and the kernel are mapped into many processes but stored once; `fork()` uses copy-on-write.
- **Memory-mapped files and devices:** `mmap()` maps a file or device memory into the address space so it can be accessed with normal loads and stores.

**Typical 64-bit Linux process layout (low to high)**

```
0x0000...       (unmapped: catches NULL pointer accesses)
text            program code, read-only + execute
data, bss       global/static variables
heap ↑          malloc() (brk / mmap)
...             shared libraries, mmap regions
stack ↓         grows down, with a guard page
0x0000ffff...   end of user space (ARM64 with 48-bit VA)
kernel space    not accessible from user mode
```

**Address translation in one line:** virtual page number → page table lookup → physical frame number; the offset inside the page is unchanged. The **TLB** caches recent translations so most accesses do not need a table walk.

**Costs:** page table memory, TLB misses, page fault handling. Real-time systems sometimes lock memory (`mlockall()`) to avoid page faults during time-critical work.

**Embedded contrast:** a Cortex-M microcontroller has no MMU, so there is no virtual memory. All tasks share one physical address space, and an **MPU** can only restrict access to regions.

### What is paging and what is a page fault? {M}
**Short answer:** Paging splits virtual and physical memory into fixed-size blocks (pages and frames, usually 4 KB). The page table maps each virtual page to a physical frame with permission bits. A **page fault** is the exception the MMU raises when an access finds no valid mapping or not enough permission. The kernel either fixes it (allocate a page, read it from a file or swap, copy-on-write) and retries the instruction, or sends the process `SIGSEGV` if the access was invalid.

**Address split (32-bit, 4 KB pages):** `virtual address = [ 20-bit page number | 12-bit offset ]`. The page number indexes the page table; the offset (0–4095) is copied directly into the physical address.

**Kinds of page fault**

| Kind | Cause | Kernel action |
|---|---|---|
| Minor (soft) | page is in RAM but not mapped yet: first touch of anonymous memory, shared library page already in the page cache | map a zero page or existing page; no disk I/O |
| Major (hard) | page must be read from disk: swapped out, or a file-backed page not in cache | start I/O, block the process, map when done |
| Copy-on-write | write to a page shared after `fork()` | copy the page, map the copy writable |
| Invalid | address not in any mapping (NULL, freed memory), or permission violation (write to read-only, execute non-executable) | send `SIGSEGV` (or `SIGBUS`) |

**What the hardware provides:** the faulting address (`FAR_EL1` on ARM64, `CR2` on x86) and the reason (`ESR_EL1` on ARM64: translation fault, permission fault, read or write, at which level).

**Page table entries contain:** physical frame number, valid bit, read/write/execute permissions, user/kernel bit, accessed and dirty bits (used for page replacement and write-back), and memory type (normal cacheable vs device memory on ARM).

**Measuring:** `/usr/bin/time -v ./prog` (major and minor faults), `perf stat -e page-faults`, `/proc/<pid>/stat` fields `minflt`/`majflt`.

**Real-time relevance:** a major fault can block for milliseconds. Real-time Linux applications call `mlockall(MCL_CURRENT | MCL_FUTURE)` and touch their stack and heap at start-up ("prefaulting") so no faults happen in the time-critical loop.

### How do multi-level page tables work? Calculate the size of the page tables. {M}
**Short answer:** A single flat page table for a large address space is huge and mostly empty, so the virtual page number is split into several indexes. The first index selects an entry in a top-level table, which points to a second-level table, and so on; the last level gives the physical frame. Tables for unused parts of the address space are simply not allocated, which saves most of the memory.

**Worked example: 32-bit addresses, 4 KB pages, 4-byte entries**

- Offset: 4 KB = 2¹² → **12 bits**.
- Page number: 32 − 12 = **20 bits** → 2²⁰ = 1,048,576 pages.
- **Single-level table:** 2²⁰ entries × 4 B = **4 MB per process**, even for a tiny program.
- **Two-level, 10 + 10 bits** (classic 32-bit x86 and ARMv7 short-descriptor style):
  - Level 1: 2¹⁰ = 1024 entries × 4 B = 4 KB (one page).
  - Each level-2 table: 1024 entries × 4 B = 4 KB, and it maps 1024 × 4 KB = **4 MB** of address space.
  - A process using 8 MB of code and data at the bottom plus one stack page at the top needs: 1 level-1 table + 2 level-2 tables (for 8 MB) + 1 level-2 table (for the stack) = **4 pages = 16 KB** instead of 4 MB.
- **Worst case** (every page mapped): 4 KB + 1024 × 4 KB = 4 MB + 4 KB, slightly **more** than a single-level table. Multi-level tables save space only because real address spaces are sparse.

**ARM64 with 4 KB granule and 48-bit virtual addresses**

```
47      39 38      30 29      21 20      12 11        0
[ L0 idx ][ L1 idx  ][ L2 idx  ][ L3 idx  ][ offset    ]
  9 bits    9 bits    9 bits     9 bits     12 bits
```

Each table holds 512 entries of 8 bytes = exactly 4 KB. Higher-level entries can also be **block** entries that map 1 GB (L1) or 2 MB (L2) directly ("huge pages"), skipping the lower levels.

**Cost:** each extra level adds a memory access to every TLB miss. Four levels means up to four reads before the real access, which is why TLBs and page-walk caches are essential.

**Formula to remember:** with page size 2ᵖ and entry size 2ᵉ, each table has 2^(p−e) entries, so each level resolves p − e bits. For 4 KB pages and 8-byte entries: 12 − 3 = 9 bits per level.

### What is a TLB, and how do you calculate the effective memory access time? {M}
**Short answer:** The TLB (Translation Lookaside Buffer) is a small, fast cache inside the MMU that holds recent virtual-to-physical translations. On a hit, the translation is available immediately; on a miss, the hardware (or OS) must walk the page tables in memory first. Effective access time = hit rate × (time on a hit) + miss rate × (time on a miss).

**Worked example 1**

- Memory access: 100 ns. TLB lookup: assume it overlaps with the cache access (≈ 0 ns).
- Two-level page table: a miss needs 2 extra memory reads.
- Hit rate 98%.

```
EAT = 0.98 × 100 + 0.02 × (2 × 100 + 100)
    = 98 + 6 = 104 ns       (4% slower than with no translation at all)
```

With a 4-level table, a miss costs 500 ns: `0.98 × 100 + 0.02 × 500 = 108 ns`.

**Worked example 2 (required hit rate)**

A page-table walk takes 40 times as long as a TLB lookup `t`. What hit rate keeps the average translation time at 2t?

```
h·t + (1 − h)·(t + 40t) = 2t
t + (1 − h)·40t        = 2t
(1 − h)                = 1/40  →  h = 97.5 %
```

**TLB facts worth mentioning**

- Typical sizes: an L1 data TLB of 32–64 entries and a unified L2 TLB of 512–2048 entries. Cortex-A53, for example, has small micro-TLBs per side plus a 512-entry main TLB.
- **TLB reach** = entries × page size. 1024 entries × 4 KB = 4 MB. With 2 MB huge pages, the same 1024 entries cover 2 GB. That is why databases, JVMs and VMs benefit from huge pages.
- **ASIDs** (ARM) / **PCIDs** (x86) tag entries with the process, so a context switch does not require flushing the TLB. ARM also tags with **VMID** for virtual machines.
- When the kernel changes a mapping, it must **invalidate** the stale TLB entries (`TLBI` instructions on ARM64, broadcast to other cores in the inner-shareable domain), which is called a TLB shootdown on x86.

**Follow-up: "Why is the TLB hit rate usually so high?"** Locality: programs access the same pages repeatedly (loops, stack, hot data), and one entry covers 4096 bytes of consecutive addresses.

### Why is the page size usually 4 KB? What happens with smaller or larger pages? {M}
**Short answer:** 4 KB is a compromise. Smaller pages waste less memory inside partly used pages (internal fragmentation) but need more page-table entries and more TLB entries for the same memory. Larger pages reduce page-table size and TLB misses and make disk I/O more efficient, but waste more memory and make copy-on-write and paging coarser. Modern systems keep a small base page and add huge pages where they help.

| | Smaller pages (e.g. 512 B) | Larger pages (e.g. 64 KB, 2 MB) |
|---|---|---|
| Internal fragmentation | low (average waste ½ page per region) | high |
| Page-table size | large (8× more entries than 4 KB) | small |
| TLB reach / misses | small reach, more misses | large reach, fewer misses |
| Page-fault count | more faults, each cheap | fewer faults, each costs more (zeroing/copying more data) |
| Copy-on-write after fork | fine-grained | copies a lot for a small write |
| Disk I/O for swapping | many small transfers (inefficient) | fewer large transfers |

**What real systems do**

- x86-64: 4 KB base pages, with 2 MB and 1 GB huge pages.
- ARM64: the kernel chooses a **granule** of 4 KB, 16 KB or 64 KB at build time. Apple silicon uses 16 KB pages; some server distributions use 64 KB pages to reduce TLB pressure. Software that assumes 4 KB (hard-coded `4096`, alignment of `mmap` offsets) breaks on these systems, so use `sysconf(_SC_PAGESIZE)`.
- Linux **Transparent Huge Pages (THP)** automatically uses 2 MB pages for large anonymous memory; **hugetlbfs** reserves them explicitly. Recent kernels add "large folios" / mTHP (multi-size) to use 16–64 KB blocks with 4 KB page tables.

**Numbers to show the trade-off:** a process using 1 GB of memory needs 262,144 entries with 4 KB pages, but only 512 with 2 MB pages.

**Follow-up: "When is virtual memory unnecessary?"** Small single-application systems such as microcontrollers: there is only one program, all code is trusted and linked together, and real-time predictability matters more than isolation. An MPU gives enough protection there.

### What are page replacement algorithms (FIFO, LRU, Clock), and what is Belady's anomaly? {M}
**Short answer:** When physical memory is full and a new page is needed, the OS must choose a victim page to evict. **FIFO** evicts the oldest page; **Optimal** evicts the page used furthest in the future (impossible in practice, used as a benchmark); **LRU** evicts the page unused for the longest time; **Clock (second chance)** approximates LRU cheaply with a reference bit. **Belady's anomaly** is FIFO's surprising behaviour of sometimes causing *more* faults with *more* frames.

**Worked example:** reference string `7 0 1 2 0 3 0 4`, **3 frames**.

| Algorithm | Frames after each reference (miss = *) | Faults |
|---|---|---|
| FIFO | 7* 70* 701* 201* 201 231* 230* 430* | 7 |
| LRU | 7* 70* 701* 201* 201 203* 203 403* | 6 |
| Optimal | 7* 70* 701* 201* 201 203* 203 403* | 6 |

At reference `3`, FIFO evicts `0` (the oldest) even though `0` is used next; LRU evicts `1`, which was least recently used.

**Clock algorithm (what real kernels approximate):** pages are arranged in a circle with a hand. Each page has a hardware "accessed" bit set on use. To evict, look at the page under the hand: if its bit is 1, clear it and move on (second chance); if it is 0, evict it. Pages in active use keep getting their bit set and survive.

**Linux:** uses active and inactive LRU lists (and the newer **multi-generational LRU**, MGLRU), driven by the accessed bits in page table entries. Clean file pages are cheap to drop (re-read from the file later); dirty or anonymous pages must be written to the file or swap first.

**Belady's anomaly:** with FIFO and the string `1 2 3 4 1 2 5 1 2 3 4 5`, 3 frames give 9 faults but 4 frames give 10. LRU and Optimal are "stack algorithms" and never show this anomaly.

**Related:** **thrashing** happens when the working set does not fit no matter which algorithm you use.

### What is an inverted page table? {H}
**Short answer:** A normal page table has one entry per **virtual page** of each process. An inverted page table has one entry per **physical frame**, recording which process (address-space ID) and which virtual page currently occupy it. Its size depends only on physical memory, not on the number of processes or the size of their address spaces. The drawback is lookup: you have to search for the entry that matches (ASID, virtual page), so a hash table is used to make it fast.

**Comparison**

| | Per-process page tables | Inverted page table |
|---|---|---|
| Entries | one per virtual page (per process) | one per physical frame (system-wide) |
| Size | grows with address space × processes | fixed: frames × entry size |
| Lookup | direct indexing (fast) | search by (ASID, VPN): needs hashing |
| Sharing pages between processes | easy (two entries point to the same frame) | hard (one frame has one owner entry) |

**Example:** 4 GB of RAM with 4 KB frames has 1,048,576 frames. With 16-byte entries the inverted table is 16 MB **in total**, regardless of whether there are 10 or 10,000 processes.

**Why software-only inverted tables are slow:** a TLB is content-addressable hardware that compares all entries at once. In software, searching every entry on each TLB miss would be O(number of frames). The fix is a **hashed** inverted page table: hash (ASID, VPN) to a bucket and follow a short chain. This was used by IBM POWER and PowerPC (hashed page table) and Intel Itanium.

**Where it is used today:** mostly historical in general-purpose CPUs; ARM and x86 use multi-level per-process tables, which work well with sparse 64-bit address spaces and make sharing easy. The idea remains in TLBs, in some hypervisor and accelerator designs, and in exam questions.

### What is the difference between an MMU and an MPU? {E}
**Short answer:** An **MMU** translates virtual addresses to physical addresses using page tables and enforces permissions per page, which gives each process its own address space (Cortex-A, x86, RISC-V with Sv39/Sv48). An **MPU** does no translation: it only checks permissions and memory attributes for a small number of physical address regions (typically 8 or 16), giving basic protection with predictable timing (Cortex-M, Cortex-R).

| | MMU | MPU |
|---|---|---|
| Address translation | yes (virtual → physical) | no (addresses are physical) |
| Granularity | pages (4 KB, 16 KB, 64 KB, huge pages) | regions (on Armv7-M: power-of-two size ≥ 32 B, aligned; on Armv8-M: any 32-byte-aligned base and limit) |
| Number of mappings | millions (tables in RAM) | 8–16 regions (registers) |
| Per-process address spaces | yes | no, one shared address space |
| Timing | TLB misses add variable latency | deterministic |
| OS | Linux, Windows, Android | FreeRTOS-MPU, Zephyr userspace, SafeRTOS, PikeOS on Cortex-R |

**What an MPU is used for on a microcontroller**

- Stack overflow detection: a no-access region just below each task's stack.
- Making flash or code regions read-only/execute-only and RAM execute-never (stops many code-injection attacks).
- Isolating unprivileged tasks so they can only touch their own data and the peripherals they need.
- Setting memory attributes: device memory for peripheral regions, non-cacheable regions for DMA buffers (Cortex-M7).

**Linux without an MMU:** the kernel can be built for no-MMU targets (`!CONFIG_MMU`), but there is no `fork()` (use `vfork`/`posix_spawn`), no memory protection between processes, and memory fragmentation becomes a problem. It is rare now that small Cortex-A parts are cheap.

**Interview follow-up:** "Cortex-R52 has two MPU stages, one for the OS and one for a hypervisor" — so even without an MMU, ARMv8-R can run a hypervisor with spatial isolation between guests.

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
