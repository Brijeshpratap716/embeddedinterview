---
title: Boeing
desc: Boeing embedded software interviews: HireVue behavioural questions, a coding challenge, RTOS and resume-based technical questions. What candidates report.
roles: Embedded Software Engineer, Software Engineer
hubs: Seattle/Everett, Hazelwood (St. Louis), Huntington Beach, Bengaluru
focus: Behavioural (STAR), coding challenge, RTOS, resume deep-dive
order: 9
sources: Glassdoor|https://www.glassdoor.co.uk/Interview/Boeing-Interview-E102-RVW103357468.htm ; Glassdoor|https://www.glassdoor.com/Interview/Boeing-Interview-E102-RVW103967925.htm ; Glassdoor|https://www.glassdoor.co.uk/Interview/Boeing-Interview-E102-RVW104324582.htm ; Glassdoor|https://www.glassdoor.co.uk/Interview/Boeing-Interview-E102-RVW80307774.htm ; Glassdoor|https://www.glassdoor.co.uk/Interview/Boeing-Interview-E102-RVW99415559.htm
---
## At a glance

| | |
|---|---|
| Typical process | Online application → recorded HireVue interview (behavioural + coding) → technical/behavioural interview with the team |
| Main focus | STAR behavioural questions, a coding challenge, RTOS and embedded basics, your resume |
| Coding style | One algorithmic challenge (a message-decoding problem is reported repeatedly) |
| Reported difficulty | Embedded Software Engineer candidates on Glassdoor rate it about 2.6 out of 5, with just over half reporting a positive experience |

## How the process usually runs

Recent candidates describe a first round on HireVue, where you record answers to a camera: two behavioural STAR questions and a coding challenge, reportedly taken from an old programming competition. Later rounds are with the team and lean on behavioural questions plus technical questions drawn from your resume. Some candidates had only one technical question in the final round; others describe an in-person round on core theory.

Because much of Boeing's work is safety-critical avionics, expect interest in process, documentation and how you handle unfamiliar technology.

## Topics that come up most

- **Behavioural (STAR):** teamwork, learning new technology, why Boeing
- **Coding:** string and message decoding → [Arrays & Strings](../../topics/arrays-strings/)
- **RTOS:** what an RTOS is and when to use one → [RTOS](../../topics/rtos/)
- **Hardware/software co-design** and embedded basics → [Embedded C](../../topics/embedded-c/), [Microcontrollers & ARM](../../topics/microcontrollers-arm/)

## Questions candidates reported (paraphrased)

- Introduce yourself, your background, and why Boeing.
- A message-decoding coding challenge.
- Explain an RTOS in detail and its use cases.
- What would you do when you have to work with a technology you don't know?
- Have you done hardware/software co-design?

## Practice questions

These are the questions Boeing candidates most often report, or close variants of them. Each links to a full answer or a coding problem with tests on this site.

1. [What is an RTOS and how is it different from a general-purpose OS?](../../topics/rtos/what-is-an-rtos-and-how-is-it-different-from-a-general-purpose-os/)
2. [What is priority inversion?](../../topics/rtos/what-is-priority-inversion/)
3. [What is a deadlock and how do you prevent it?](../../topics/rtos/what-is-a-deadlock-and-how-do-you-prevent-it/)
4. [What is MISRA C?](../../topics/embedded-c/what-is-misra-c/)
5. [What is a watchdog timer and how should you use it?](../../topics/embedded-c/what-is-a-watchdog-timer-and-how-should-you-use-it/)
6. [What are a HAL and a BSP, and how do they differ?](../../topics/embedded-c/what-are-a-hal-and-a-bsp-and-how-do-they-differ/)
7. [Compare UART, SPI and I2C.](../../topics/communication-protocols/compare-uart-spi-and-i2c/)
8. [How do you reverse the order of words in a string?](../../topics/arrays-strings/how-do-you-reverse-the-order-of-words-in-a-string/)
9. [UART Packet Parser State Machine](../../problems/frame-parser/) *(coding)*
10. [Validate an NMEA Sentence](../../problems/nmea-checksum/) *(coding)*
11. [CRC-16/CCITT-FALSE](../../problems/crc16-ccitt/) *(coding)*

## How to prepare

1. Prepare 5–6 STAR stories (conflict, failure, learning fast, ownership, a technical challenge) and practise recording yourself, since HireVue has no live interviewer.
2. Practise string-parsing problems under time pressure: [UART Packet Parser](../../problems/frame-parser/), [NMEA Checksum](../../problems/nmea-checksum/).
3. Revise RTOS fundamentals and be ready to discuss safety-critical practices (MISRA C, DO-178C awareness for avionics roles).
