---
title: Intel
desc: Intel firmware and embedded interviews: C, BIOS and bootloaders, OS and RTOS, bit manipulation and coding. What candidates report and how to prepare.
roles: Firmware Engineer, Senior Firmware Engineer, Firmware Intern
hubs: Bengaluru, Folsom, Hillsboro, Haifa, Jerusalem
focus: C, BIOS/bootloader, OS/RTOS, bit manipulation, computer architecture
order: 3
---
## At a glance

| | |
|---|---|
| Typical process | Phone or online screen → several technical rounds (reports range from 2 to 5) → hiring manager and HR |
| Main focus | Embedded C, BIOS and bootloaders, OS/RTOS, locks, bit manipulation, computer architecture |
| Coding style | Implement classic C functions, string and bit problems, some LeetCode-style questions |
| Reported difficulty | Mixed: many firmware candidates describe it as average or straightforward, while some long onsite days were intense |

## How the process usually runs

Reports vary by site and level. Some candidates had a take-home coding test followed by four onsite rounds; others describe five technical rounds of straightforward embedded questions, then hiring manager and HR rounds. In Israel, candidates mention a phone interview on C and firmware followed by two long technical interviews solving coding problems on a board. One senior candidate described a full 8-hour interview day.

## Topics that come up most

- **C implementations:** `malloc`, `atoi`, swapping without a temporary → [C Programming](../../topics/c-programming/), [Pointers & Memory](../../topics/pointers-memory/)
- **BIOS, boot and firmware:** how to debug a BIOS, bootloader flow → [Embedded Linux & Boot](../../topics/embedded-linux/)
- **OS and RTOS:** types of locks, multithreading → [RTOS](../../topics/rtos/), [Operating System Concepts](../../topics/operating-systems/)
- **Architecture:** cache coherence, memory hierarchy → [Microcontrollers & ARM](../../topics/microcontrollers-arm/)
- **Bits and strings:** bit manipulation, substring search → [Bit Manipulation](../../topics/bit-manipulation/), [Arrays & Strings](../../topics/arrays-strings/)

## Questions candidates reported (paraphrased)

- Implement `malloc`; implement `atoi`.
- Swap two integers without a temporary variable.
- How would you debug a BIOS that does not boot?
- What kinds of locks exist in an OS or RTOS?
- Explain cache coherence and the memory hierarchy.
- Find a substring in a string efficiently (KMP was mentioned).
- Write an efficient routine to reach a specific memory location.

## Practice questions

These are the questions Intel candidates most often report, or close variants of them. Each links to a full answer or a coding problem with tests on this site.

1. [How would you implement a simple malloc() and free()?](../../topics/pointers-memory/how-would-you-implement-a-simple-malloc-and-free/)
2. [How do you implement atoi() and itoa() in C?](../../topics/arrays-strings/how-do-you-implement-atoi-and-itoa-in-c/)
3. [How do you swap two numbers without a temporary variable?](../../topics/bit-manipulation/how-do-you-swap-two-numbers-without-a-temporary-variable/)
4. [How do you search for a pattern in a string (naive and KMP)?](../../topics/arrays-strings/how-do-you-search-for-a-pattern-in-a-string-naive-and-kmp/)
5. [What is a bootloader and why does an embedded Linux system need one?](../../topics/embedded-linux/what-is-a-bootloader-and-why-does-an-embedded-linux-system-need-one/)
6. [What happens before main() runs on a microcontroller?](../../topics/embedded-c/what-happens-before-main-runs-on-a-microcontroller/)
7. [What is secure boot and a chain of trust?](../../topics/embedded-linux/what-is-secure-boot-and-a-chain-of-trust/)
8. [What is a spinlock, and what are its advantages and disadvantages?](../../topics/operating-systems/what-is-a-spinlock-and-what-are-its-advantages-and-disadvantages/)
9. [What is the difference between a mutex and a binary semaphore?](../../topics/rtos/what-is-the-difference-between-a-mutex-and-a-binary-semaphore/)
10. [What are the cache coherency problems with DMA?](../../topics/embedded-c/what-are-the-cache-coherency-problems-with-dma/)
11. [What is a TLB, and how do you calculate the effective memory access time?](../../topics/operating-systems/what-is-a-tlb-and-how-do-you-calculate-the-effective-memory-access-tim/)
12. [How do you count the set bits in an integer?](../../topics/bit-manipulation/how-do-you-count-the-set-bits-in-an-integer/)
13. [String to Integer with Error Checking](../../problems/atoi-overflow/) *(coding)*
14. [Fixed-Block Memory Pool](../../problems/memory-pool/) *(coding)*
15. [Implement memcpy](../../problems/implement-memcpy/) *(coding)*

## How to prepare

1. Practise writing standard library functions from scratch: [String to Integer](../../problems/atoi-overflow/), [Implement memcpy](../../problems/implement-memcpy/), [Fixed-Block Memory Pool](../../problems/memory-pool/).
2. Revise x86/UEFI boot flow if the team works on BIOS or platform firmware.
3. Know your locking primitives and when each is used.
4. Expect to explain your projects in detail and to write code without an IDE.

## Read real experiences

- [Glassdoor: Intel Firmware Engineer – take-home test and 4 onsite rounds](https://www.glassdoor.com/Interview/Intel-Corporation-Interview-E1519-RVW3998388.htm)
- [Glassdoor: Intel Firmware Engineer – implement malloc and atoi](https://www.glassdoor.com/Interview/Intel-Corporation-Interview-E1519-RVW7170079.htm)
- [Glassdoor: Intel Firmware Engineer (Bengaluru) – BIOS, bootloader, RTOS topics](https://www.glassdoor.sg/Interview/Intel-Corporation-Interview-E1519-RVW45658282.htm)
- [Glassdoor: Intel Firmware Engineer Intern – cache coherence, memory hierarchy](https://www.glassdoor.ca/Interview/Intel-Corporation-Interview-E1519-RVW81921112.htm)
- [Glassdoor: Intel Senior Firmware Engineer – locks in OS/RTOS](https://www.glassdoor.com/Interview/Intel-Corporation-Interview-E1519-RVW90206162.htm)
