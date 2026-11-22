---
title: Arm
desc: Arm software and firmware interviews: C pointers, compiler optimisations, caches, TLBs, synchronisation and embedded system design. What candidates report.
roles: Software Engineer, Firmware Engineer, Embedded Software Engineer, Graduate Engineer
hubs: Cambridge, Manchester, Bengaluru, Austin, Sophia Antipolis
focus: C, compilers and optimisation, memory systems, synchronisation
order: 6
---
## At a glance

| | |
|---|---|
| Typical process | Phone interview and/or skills test → one or more technical interviews → behavioural questions |
| Main focus | C and pointers, how compilers optimise code, caches and memory systems, synchronisation, system design for embedded |
| Coding style | Reading and reasoning about short C functions; some problems written on paper |
| Reported difficulty | Software Engineer candidates on Glassdoor rate it about 3 out of 5, with around 60% positive experiences |

## How the process usually runs

Glassdoor's summary of Arm software interviews lists phone interviews, skills tests and one-to-one interviews as the most common stages. Graduate and intern candidates in Bengaluru and Austin describe basic C pointer questions and core OS and architecture concepts. More senior candidates report open discussions on memory subsystems and system design with performance trade-offs. The overall process can take several weeks.

## Topics that come up most

- **C and pointers** → [Pointers & Memory](../../topics/pointers-memory/)
- **Compilers:** which optimisations are and are not legal for a given function (aliasing, `volatile`, side effects) → [C Programming](../../topics/c-programming/), [Embedded C](../../topics/embedded-c/)
- **Memory systems:** cache coherency, TLBs → [Operating System Concepts](../../topics/operating-systems/), [Microcontrollers & ARM](../../topics/microcontrollers-arm/)
- **Synchronisation:** binary semaphore vs mutex → [RTOS](../../topics/rtos/)
- **`volatile`** → [Embedded C](../../topics/embedded-c/)

## Questions candidates reported (paraphrased)

- Given five or six short C functions, explain which compiler optimisations could and could not be applied.
- Binary semaphore vs mutex.
- What is cache coherency? What is a TLB?
- Why does `volatile` matter?
- Design an embedded software system and discuss the trade-offs.

## Practice questions

These are the questions Arm candidates most often report, or close variants of them. Each links to a full answer or a coding problem with tests on this site.

1. [Which compiler optimisations can change how your C code behaves?](../../topics/embedded-c/which-compiler-optimisations-can-change-how-your-c-code-behaves/)
2. [What is strict aliasing?](../../topics/pointers-memory/what-is-strict-aliasing/)
3. [What is volatile and when must you use it?](../../topics/embedded-c/what-is-volatile-and-when-must-you-use-it/)
4. [Does volatile make a variable thread-safe or atomic?](../../topics/embedded-c/does-volatile-make-a-variable-thread-safe-or-atomic/)
5. [What is the difference between a mutex and a binary semaphore?](../../topics/rtos/what-is-the-difference-between-a-mutex-and-a-binary-semaphore/)
6. [What are the cache coherency problems with DMA?](../../topics/embedded-c/what-are-the-cache-coherency-problems-with-dma/)
7. [How do Arm systems keep DMA and CPU caches coherent (ACP, I/O coherency)?](../../topics/microcontrollers-arm/how-do-arm-systems-keep-dma-and-cpu-caches-coherent-acp-i-o-coherency/)
8. [What is a TLB, and how do you calculate the effective memory access time?](../../topics/operating-systems/what-is-a-tlb-and-how-do-you-calculate-the-effective-memory-access-tim/)
9. [What is RISC, how does it differ from CISC, and why did Arm succeed?](../../topics/microcontrollers-arm/what-is-risc-how-does-it-differ-from-cisc-and-why-did-arm-succeed/)
10. [What does the inline assembly __asm volatile("" ::: "memory") do?](../../topics/embedded-c/what-does-the-inline-assembly-asm-volatile-memory-do/)
11. [What is a function pointer and where is it used?](../../topics/c-programming/what-is-a-function-pointer-and-where-is-it-used/)
12. [Implement memmove](../../problems/implement-memmove/) *(coding)*

## How to prepare

1. Understand what the compiler may assume: strict aliasing, undefined behaviour, `restrict`, `volatile` and side effects.
2. Revise caches, TLBs and memory ordering, ideally in the context of the Arm architecture (Cortex-A vs Cortex-M).
3. Practise writing clean C under exam-like conditions; one candidate notes that thinking before writing on paper helped.

## Read real experiences

- [Glassdoor: Arm interview – explain possible compiler optimisations](https://www.glassdoor.co.uk/Interview/Arm-Interview-E7834-RVW88739914.htm)
- [Glassdoor: Arm Firmware Engineer Intern – mutex, cache coherency, TLB, volatile](https://www.glassdoor.co.in/Interview/Arm-Interview-E7834-RVW83628137.htm)
- [Glassdoor: Arm Software Engineer interviews (Bengaluru)](https://www.glassdoor.com/Interview/Arm-Interview-E7834-RVW80120109.htm)
- [Glassdoor: Arm Software Engineer – system design for embedded](https://www.glassdoor.co.uk/Interview/Arm-Interview-E7834-RVW92184506.htm)
- [Glassdoor: Arm Software Engineer interview stages](https://www.glassdoor.co.uk/Interview/Arm-Interview-E7834-RVW1995294.htm)
