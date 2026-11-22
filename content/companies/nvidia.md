---
title: NVIDIA
desc: NVIDIA system software and embedded interviews: Linux kernel, OS concepts, C/C++, SoC architecture and coding. What candidates report and how to prepare.
roles: System Software Engineer, Embedded Software Engineer, Firmware Engineer
hubs: Santa Clara, Pune, Bengaluru, Hyderabad, Durham, Taipei
focus: Linux kernel, OS internals, C/C++, computer architecture
order: 2
sources: Glassdoor|https://www.glassdoor.ie/Interview/NVIDIA-Interview-E7633-RVW9978856.htm ; Glassdoor|https://www.glassdoor.co.uk/Interview/NVIDIA-Interview-E7633-RVW81115733.htm ; Glassdoor|https://www.glassdoor.co.in/Interview/NVIDIA-Interview-RVW23935689.htm ; Glassdoor|https://www.glassdoor.com/Interview/NVIDIA-Interview-RVW89804534.htm ; Glassdoor|https://www.glassdoor.ie/Interview/NVIDIA-Interview-E7633-RVW17445377.htm ; GeeksforGeeks|https://www.geeksforgeeks.org/companies/nvidia/articles/
---
## At a glance

| | |
|---|---|
| Typical process | Recruiter → 1–2 technical phone/video screens → onsite or virtual loop (some candidates report 6–7 rounds in one day) |
| Main focus | Linux kernel internals, OS concepts, C and C++, computer architecture, coding |
| Coding style | Algorithm and data-structure problems plus C/C++ programs, sometimes a longer timed coding question |
| Reported difficulty | System Software Engineer candidates on Glassdoor rate it about 3.5 out of 5, with roughly half reporting a positive experience |

## How the process usually runs

Candidates usually describe a first phone screen of about an hour. One report split it into roughly 10 minutes on the resume, 30 minutes on Linux kernel questions and 10 minutes of C questions, many of them quick but tricky. Further screens add coding and computer architecture. Some candidates were then invited to a full-day onsite loop of 6–7 interviews mixing coding, architecture, Linux and protocol questions.

## Topics that come up most

- **Linux kernel:** memory allocation, threads, ISR top and bottom halves, system calls → [Linux Kernel & Device Drivers](../../topics/linux-device-drivers/)
- **OS concepts:** process vs thread, virtual memory, mutex vs semaphore, concurrency vs parallelism → [Operating System Concepts](../../topics/operating-systems/)
- **C basics:** `volatile` and `static`, aligned allocation → [Embedded C](../../topics/embedded-c/)
- **Architecture:** SoC breakdown, what happens when an embedded system boots, caches → [Microcontrollers & ARM](../../topics/microcontrollers-arm/), [Embedded Linux & Boot](../../topics/embedded-linux/)
- **Debugging:** hardware vs software breakpoints → [Debugging & Tools](../../topics/debugging-testing/)
- **Algorithms:** intervals, linked lists, typical medium coding problems → [Data Structures](../../topics/data-structures/)

## Questions candidates reported (paraphrased)

- Walk through a typical SoC architecture.
- What happens, step by step, when an embedded system boots?
- How does virtual memory work? Process vs thread? Mutex vs semaphore?
- Linux kernel memory allocation methods; write `aligned_malloc` and `aligned_free`.
- Top half vs bottom half of an interrupt handler.
- Hardware vs software breakpoints.
- Given a stream of (start, end) intervals, find the busiest hour.

## Practice questions

These are the questions NVIDIA candidates most often report, or close variants of them. Each links to a full answer or a coding problem with tests on this site.

1. [What does a typical SoC look like inside?](../../topics/embedded-c/what-does-a-typical-soc-look-like-inside/)
2. [How does the kernel boot on an ARM64 system?](../../topics/linux-device-drivers/how-does-the-kernel-boot-on-an-arm64-system/)
3. [Walk through the complete boot process of an embedded Linux system, from power-on to the login prompt.](../../topics/embedded-linux/walk-through-the-complete-boot-process-of-an-embedded-linux-system-fro/)
4. [What is the difference between a process and a thread?](../../topics/operating-systems/what-is-the-difference-between-a-process-and-a-thread/)
5. [What is virtual memory and why is it used?](../../topics/operating-systems/what-is-virtual-memory-and-why-is-it-used/)
6. [What is a semaphore, and how does it differ from a mutex in POSIX? How are semaphores used for mutual exclusion and for synchronisation?](../../topics/operating-systems/what-is-a-semaphore-and-how-does-it-differ-from-a-mutex-in-posix-how-a/)
7. [What is the difference between kmalloc, vmalloc and kzalloc?](../../topics/linux-device-drivers/what-is-the-difference-between-kmalloc-vmalloc-and-kzalloc/)
8. [What are top halves and bottom halves?](../../topics/linux-device-drivers/what-are-top-halves-and-bottom-halves/)
9. [What is the difference between a spinlock and a mutex in the kernel?](../../topics/linux-device-drivers/what-is-the-difference-between-a-spinlock-and-a-mutex-in-the-kernel/)
10. [What is the difference between a breakpoint and a watchpoint?](../../topics/debugging-testing/what-is-the-difference-between-a-breakpoint-and-a-watchpoint/)
11. [What is the volatile keyword?](../../topics/c-programming/what-is-the-volatile-keyword/)
12. [What does the static keyword do in different contexts?](../../topics/c-programming/what-does-the-static-keyword-do-in-different-contexts/)
13. [What is a system call and how does it work?](../../topics/operating-systems/what-is-a-system-call-and-how-does-it-work/)
14. [What is the difference between a structure and a union?](../../topics/c-programming/what-is-the-difference-between-a-structure-and-a-union/)
15. [Implement aligned_malloc() and aligned_free().](../../topics/coding-memory-strings/implement-aligned-malloc-and-aligned-free/)
16. [Merge overlapping intervals.](../../topics/coding-sorting-arrays/merge-overlapping-intervals/)
17. [Aligned Allocation](../../problems/aligned-malloc/) *(coding)*

## How to prepare

1. Go deep on the Linux kernel: memory allocators, locking, interrupts, deferred work and the driver model.
2. Practise [Aligned Allocation](../../problems/aligned-malloc/), [Implement memmove](../../problems/implement-memmove/) and a few medium array/interval problems under time pressure.
3. Be able to draw an SoC block diagram and explain the boot flow from ROM to the kernel.
4. For GPU or Tegra/automotive teams, read up on the specific domain (display, camera, power, CUDA basics).
