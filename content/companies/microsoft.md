---
title: Microsoft
desc: Microsoft firmware interviews (Surface, Xbox, Azure hardware): C, RTOS, HAL/BSP, BIOS/UEFI, Linux boot, debugging and coding rounds. What candidates report.
roles: Firmware Engineer, Embedded Firmware Engineer, Senior Firmware Engineer
hubs: Redmond, Hyderabad, Bengaluru, Noida, Taipei
focus: C, RTOS, HAL/BSP, BIOS/UEFI, boot, debugging
order: 8
sources: Glassdoor|https://www.glassdoor.co.uk/Interview/Microsoft-Interview-E1651-RVW100005836.htm ; Glassdoor|https://clear.glassdoor.nl/Interview/Microsoft-Interview-E1651-RVW33908451.htm ; Glassdoor|https://www.glassdoor.com.au/Interview/Microsoft-Interview-E1651-RVW103685699.htm ; Glassdoor|https://www.glassdoor.com.au/Interview/Microsoft-Interview-E1651-RVW100005836.htm ; Glassdoor|https://www.glassdoor.co.uk/Interview/Microsoft-Interview-E1651-RVW2363400.htm
---
## At a glance

| | |
|---|---|
| Typical process | Recruiter or referral → phone/video screen → 3–5 technical rounds mixing coding and embedded questions |
| Main focus | C, RTOS, HAL and BSP design, BIOS/UEFI, Linux boot, debugging, data structures |
| Coding style | Data-structure problems (palindromes and similar), sometimes completing half-written code |
| Reported difficulty | Often described as difficult, but many candidates still report a positive experience |

## How the process usually runs

One candidate who accepted an offer described four rounds: a phone or video screen, then three technical rounds of coding and embedded-systems questions. Others describe a deep dive into C, RTOS and debugging skills, including walking the team through how they solved a tricky memory leak. Campus candidates for hardware teams sometimes got circuit-design questions instead of pure firmware ones, depending on the team (Xbox, Surface and others).

## Topics that come up most

- **C:** `volatile` and `static` → [C Programming](../../topics/c-programming/), [Embedded C](../../topics/embedded-c/)
- **Firmware structure:** HAL, BSP → [Embedded C](../../topics/embedded-c/), [Driver coding](../../topics/coding-embedded-drivers/)
- **Boot:** how a Linux system boots; BIOS questions → [Embedded Linux & Boot](../../topics/embedded-linux/)
- **RTOS and debugging:** memory leaks, debugging approach → [RTOS](../../topics/rtos/), [Debugging & Tools](../../topics/debugging-testing/)
- **Data structures and coding** → [Data Structures](../../topics/data-structures/), [Arrays & Strings](../../topics/arrays-strings/)

## Questions candidates reported (paraphrased)

- Explain `volatile` and `static`.
- Walk through how a Linux system boots.
- BIOS questions plus data structures.
- Describe a memory leak you tracked down and how you found it.
- A palindrome problem; completing partially written code.

## Practice questions

These are the questions Microsoft candidates most often report, or close variants of them. Each links to a full answer or a coding problem with tests on this site.

1. [What are a HAL and a BSP, and how do they differ?](../../topics/embedded-c/what-are-a-hal-and-a-bsp-and-how-do-they-differ/)
2. [What is the volatile keyword?](../../topics/c-programming/what-is-the-volatile-keyword/)
3. [What does the static keyword do in different contexts?](../../topics/c-programming/what-does-the-static-keyword-do-in-different-contexts/)
4. [Walk through the complete boot process of an embedded Linux system, from power-on to the login prompt.](../../topics/embedded-linux/walk-through-the-complete-boot-process-of-an-embedded-linux-system-fro/)
5. [What happens inside U-Boot from reset until it boots the kernel?](../../topics/embedded-linux/what-happens-inside-u-boot-from-reset-until-it-boots-the-kernel/)
6. [What is secure boot and a chain of trust?](../../topics/embedded-linux/what-is-secure-boot-and-a-chain-of-trust/)
7. [What is an RTOS and how is it different from a general-purpose OS?](../../topics/rtos/what-is-an-rtos-and-how-is-it-different-from-a-general-purpose-os/)
8. [What is the difference between a breakpoint and a watchpoint?](../../topics/debugging-testing/what-is-the-difference-between-a-breakpoint-and-a-watchpoint/)
9. [What are ITM, SWO, ETM and RTT, and when do you use trace?](../../topics/debugging-testing/what-are-itm-swo-etm-and-rtt-and-when-do-you-use-trace/)
10. [Check whether a linked list is a palindrome.](../../topics/coding-lists-stacks-queues/check-whether-a-linked-list-is-a-palindrome/)
11. [Find the longest palindromic substring.](../../topics/coding-memory-strings/find-the-longest-palindromic-substring/)
12. [HardFault Handler that Captures the Stack Frame](../../problems/hardfault-handler/) *(coding)*
13. [Fixed-Block Memory Pool](../../problems/memory-pool/) *(coding)*

## How to prepare

1. Have one or two detailed debugging stories ready, with the tools you used and what you measured.
2. Revise the boot chain end to end: ROM, bootloader or UEFI, kernel, init.
3. Practise standard coding questions in C, since rounds often mix coding and embedded topics.
4. Be ready to explain how you structured a HAL or BSP on a past project.
