---
title: NVIDIA
desc: NVIDIA system software and embedded interviews: Linux kernel, OS concepts, C/C++, SoC architecture and coding. What candidates report and how to prepare.
roles: System Software Engineer, Embedded Software Engineer, Firmware Engineer
hubs: Santa Clara, Pune, Bengaluru, Hyderabad, Durham, Taipei
focus: Linux kernel, OS internals, C/C++, computer architecture
order: 2
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

## How to prepare

1. Go deep on the Linux kernel: memory allocators, locking, interrupts, deferred work and the driver model.
2. Practise [Aligned Allocation](../../problems/aligned-malloc/), [Implement memmove](../../problems/implement-memmove/) and a few medium array/interval problems under time pressure.
3. Be able to draw an SoC block diagram and explain the boot flow from ROM to the kernel.
4. For GPU or Tegra/automotive teams, read up on the specific domain (display, camera, power, CUDA basics).

## Read real experiences

- [Glassdoor: NVIDIA phone screen on Linux kernel and C questions](https://www.glassdoor.ie/Interview/NVIDIA-Interview-E7633-RVW9978856.htm)
- [Glassdoor: NVIDIA System Software Engineer interviews (Pune)](https://www.glassdoor.co.uk/Interview/NVIDIA-Interview-E7633-RVW81115733.htm)
- [Glassdoor: NVIDIA Embedded Software Engineer onsite loop](https://www.glassdoor.co.in/Interview/NVIDIA-Interview-RVW23935689.htm)
- [Glassdoor: NVIDIA questions on SoC architecture and boot](https://www.glassdoor.com/Interview/NVIDIA-Interview-RVW89804534.htm)
- [Glassdoor: NVIDIA Systems Software interview (kernel memory, aligned malloc)](https://www.glassdoor.ie/Interview/NVIDIA-Interview-E7633-RVW17445377.htm)
