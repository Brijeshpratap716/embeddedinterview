---
title: AMD
desc: AMD firmware and embedded interviews: C, bit manipulation, pointers, structure padding, interrupts, Linux drivers and live coding. What candidates report.
roles: Firmware Engineer, Embedded Software Engineer, Firmware Intern
hubs: Austin, Santa Clara, Markham, Hyderabad, Bengaluru
focus: Embedded C, bit manipulation, pointers, interrupts, Linux drivers
order: 5
---
## At a glance

| | |
|---|---|
| Typical process | Hiring manager round → 2–3 technical rounds, often split between questions and live coding |
| Main focus | Embedded C, bit manipulation, pointers and memory, interrupts, structure padding, Linux kernel drivers for some teams |
| Coding style | Live coding (CoderPad mentioned), "what does this code print / what is wrong with it" snippets |
| Reported difficulty | Varies by team: many describe easy-to-average questions, while some firmware roles were rated difficult |

## How the process usually runs

Several candidates describe a hiring-manager round focused on resume and projects, followed by two or three technical rounds. One candidate's interviews were an hour each, split evenly between technical questions and live coding. Intern interviews were sometimes a single hour: 15 minutes on projects and three short coding questions. Some firmware roles close to hardware also asked Verilog questions.

## Topics that come up most

- **Bit manipulation:** set/clear/toggle, masks, extracting fields, endianness, counting set bits → [Bit Manipulation](../../topics/bit-manipulation/)
- **C and memory:** pointers, structure padding, `volatile`, the heap → [Pointers & Memory](../../topics/pointers-memory/), [C Programming](../../topics/c-programming/)
- **Interrupts and embedded basics** → [Embedded C](../../topics/embedded-c/)
- **Data structures:** linked lists and arrays → [Data Structures](../../topics/data-structures/)
- **Linux:** basics, then kernel driver programming for driver roles → [Linux Kernel & Device Drivers](../../topics/linux-device-drivers/)
- **Architecture:** RISC vs CISC → [Microcontrollers & ARM](../../topics/microcontrollers-arm/)

## Questions candidates reported (paraphrased)

- Count the set bits in a number.
- Structure padding, `volatile` and interrupt questions.
- What is wrong with this C snippet, and what does it print?
- What is the heap used for?
- Difference between RISC and CISC.
- Parallel processing and semaphores (for a GPU-adjacent firmware role).

## How to prepare

1. Drill bit manipulation until it is automatic: [Set, Clear, Toggle](../../problems/set-clear-toggle-bits/), [Register Field](../../problems/register-field/), [Swap Byte Order](../../problems/swap-nibbles-endian/), [Count Set Bits](../../problems/count-set-bits/).
2. Practise reading C snippets for undefined behaviour, padding and pointer mistakes.
3. For driver teams, revise kernel module structure, interrupts and locking.

## Read real experiences

- [Glassdoor: AMD Firmware Intern – bit manipulation, padding, volatile, interrupts](https://www.glassdoor.co.in/Interview/AMD-Interview-E15-RVW101245307.htm)
- [Glassdoor: AMD interview – technical questions plus live coding](https://www.glassdoor.com/Interview/AMD-Interview-E15-RVW103894912.htm)
- [Glassdoor: AMD Firmware Engineer (Austin) – bit masking, pointers, endianness](https://www.glassdoor.com/Interview/AMD-Interview-E15-RVW39576196.htm)
- [Glassdoor: AMD Embedded Software Engineer – C, Linux and kernel drivers](https://www.glassdoor.co.in/Interview/AMD-Interview-E15-RVW88491756.htm)
- [Glassdoor: AMD Firmware Engineer Intern – "what's wrong with this code" questions](https://www.glassdoor.ca/Interview/AMD-Interview-E15-RVW100081675.htm)
