---
slug: operating-systems
title: Operating System Concepts
icon: 🧠
level: Intermediate
order: 10
desc: Processes and threads, scheduling, virtual memory, paging, the MMU, IPC, synchronisation and system calls.
---
These questions come up for Linux, BSP and systems roles, and as warm-ups in RTOS interviews.

### What is the difference between a process and a thread? {E}
A **process** is a running program with its own virtual address space, file descriptors and resources. A **thread** is an execution path inside a process; threads of the same process share memory and file descriptors but each has its own stack, registers and scheduling state. Creating and switching threads is cheaper, but a bug in one thread can corrupt the others. In Linux both are tasks (`task_struct`); `clone()` flags decide what is shared.

### What happens during fork() and exec()? {M}
`fork()` creates a child that is a copy of the parent. Linux uses **copy-on-write**: both share the same physical pages marked read-only, and a page is copied only when one of them writes to it. `fork` returns the child PID in the parent and 0 in the child. `exec()` (e.g. `execve`) replaces the current process image with a new program: new code, data, heap and stack, same PID and (non-close-on-exec) file descriptors. A shell runs a command with `fork` + `exec` + `wait`.

### What is a zombie process and an orphan process? {E}
A **zombie** has exited but its parent has not yet called `wait()` to collect its exit status, so it remains in the process table. An **orphan** is a process whose parent has exited; it is re-parented to `init` (or a subreaper), which reaps it when it exits. Many zombies indicate a parent that does not handle `SIGCHLD`.

### What is virtual memory and why is it used? {E}
Each process sees its own linear address space, which the MMU translates to physical memory through page tables. Benefits:

- **Isolation**: a process cannot touch another's memory.
- **Overcommit and swapping**: only pages actually used need physical frames.
- **Sharing**: libraries and copy-on-write pages are mapped into many processes once.
- **Convenience**: memory looks contiguous even if physical pages are scattered, and files can be mapped (`mmap`).

### What is paging and what is a page fault? {M}
Memory is divided into fixed-size pages (usually 4 KB; also 16/64 KB and huge pages). Page tables map virtual page numbers to physical frames with permission bits. A **page fault** is the exception raised when an access hits a page with no valid mapping or insufficient permission. The kernel then either fixes it (allocate a zero page, read from file or swap, copy-on-write) and retries the instruction, or delivers `SIGSEGV` if the access is invalid. "Minor" faults need no I/O; "major" faults do.

### What is a TLB? {M}
The Translation Lookaside Buffer is a small cache in the MMU of recent virtual-to-physical translations. A TLB hit avoids walking the multi-level page tables in memory. Context switches between processes may require flushing or tagging entries (ARM uses ASIDs so entries from different processes can coexist). Huge pages reduce TLB misses for large memory regions.

### What is the difference between an MMU and an MPU? {E}
An **MMU** translates virtual addresses to physical ones through page tables and enforces permissions per page, enabling full virtual memory and process isolation (Cortex-A, x86). An **MPU** only checks permissions and attributes for a few physical regions without translation (Cortex-M, Cortex-R). Linux needs an MMU (except the limited no-MMU configurations); RTOSes use an MPU for protection.

### What are the common IPC mechanisms? {E}
- **Pipes** and **FIFOs** (named pipes): byte streams between related or unrelated processes.
- **Message queues** (POSIX `mq_*`): discrete messages with priorities.
- **Shared memory** (`shm_open` + `mmap`): fastest, needs separate synchronisation.
- **Semaphores** (POSIX named/unnamed): synchronisation.
- **Signals**: asynchronous notifications.
- **Sockets**: Unix domain sockets locally, TCP/UDP across machines.
- Higher level: D-Bus, gRPC, and Android Binder.

### What is a race condition? {E}
A bug where the result depends on the timing of concurrent operations on shared data. The classic example is two threads doing `count++` at the same time: both read the same old value and one increment is lost. Fix it with a mutex around the access, an atomic operation, or by not sharing the data (message passing). Races are timing-dependent, so they often show up only in production; tools such as ThreadSanitizer help find them.

### What is a semaphore and how does it differ from a mutex in POSIX? {M}
A semaphore is a counter with atomic `wait` (decrement, block at zero) and `post` (increment, wake a waiter). A mutex is a lock with an owner: only the thread that locked it may unlock it, and it can support priority inheritance (`PTHREAD_PRIO_INHERIT`) and error checking. Use a mutex for mutual exclusion and a semaphore or condition variable for signalling or counting resources.

### What is a condition variable? {M}
A condition variable lets a thread sleep until a condition on shared data becomes true. It is always used with a mutex and a loop, because wake-ups can be spurious:

```c
pthread_mutex_lock(&m);
while (!data_ready)
    pthread_cond_wait(&cv, &m);   /* atomically unlocks m and sleeps */
consume();
pthread_mutex_unlock(&m);
```

The producer sets `data_ready` under the mutex and calls `pthread_cond_signal`.

### What are the CPU scheduling algorithms? {E}
- **FCFS** (first come first served): simple, poor response time.
- **SJF / SRTF**: shortest job first, optimal average waiting time, needs burst prediction.
- **Round robin**: time slices in turn, fair, good for interactive systems.
- **Priority** scheduling (pre-emptive or not), with aging to avoid starvation.
- **Multilevel feedback queues**.

Linux uses **EEVDF** (which replaced CFS in 6.6) for normal tasks, plus real-time classes `SCHED_FIFO` and `SCHED_RR` and the `SCHED_DEADLINE` class.

### What is the difference between SCHED_FIFO and SCHED_RR in Linux? {M}
Both are real-time policies with static priorities 1–99 that always pre-empt normal tasks. A `SCHED_FIFO` task runs until it blocks, yields or is pre-empted by a higher priority; equal-priority tasks wait. `SCHED_RR` adds a time slice so equal-priority tasks rotate. A runaway real-time task can lock up a CPU, which is why Linux throttles RT tasks by default (`sched_rt_runtime_us`). For lower latency, use the PREEMPT_RT patches (merged into mainline in 6.12).

### What is a system call and how does it work? {M}
A system call is the controlled entry point from user space into the kernel. The C library places the syscall number and arguments in registers and executes a trap instruction (`svc #0` on ARM64, `syscall` on x86-64). The CPU switches to kernel mode and jumps to the exception vector, the kernel looks up the handler in the syscall table, runs it, and returns the result (negative values become `errno` in libc). `strace` shows the system calls a program makes.

### What is thrashing? {E}
Thrashing happens when the working set of running processes does not fit in physical memory, so the system spends most of its time paging data in and out instead of doing useful work. Throughput collapses. Fixes are adding memory, reducing the number or size of running processes, or using the OOM killer and memory limits (cgroups).
