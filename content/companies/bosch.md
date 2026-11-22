---
title: Bosch
desc: Bosch embedded and automotive software interviews: CAN, AUTOSAR layers, Embedded C, RTOS, MISRA, HIL testing and project deep dives. What candidates report.
roles: Embedded Software Engineer, Embedded Developer, AUTOSAR Engineer
hubs: Bengaluru, Coimbatore, Stuttgart, Budapest, Ho Chi Minh City
focus: CAN, AUTOSAR, Embedded C, RTOS, automotive testing
order: 12
sources: Glassdoor|https://www.glassdoor.com.au/Interview/Robert-Bosch-Interview-E3353-RVW8430885.htm ; Glassdoor|https://www.glassdoor.com/Interview/Robert-Bosch-Interview-E3353-RVW13938744.htm ; Glassdoor|https://static.glassdoor.com.br/Interview/Robert-Bosch-Embedded-Developer-Interview-Questions-EI_IE3353.0,12_KO13,31.htm ; Glassdoor|https://www.glassdoor.ca/Interview/Robert-Bosch-Interview-E3353-RVW82453143.htm ; Glassdoor|https://www.glassdoor.com/Interview/Bosch-Interview-RVW5567201.htm ; AmbitionBox|https://www.ambitionbox.com/interviews/bosch-interview-questions/embedded-software-engineer
---
## At a glance

| | |
|---|---|
| Typical process | Hiring manager or phone screen → 1–2 technical rounds → senior manager → HR (often completed within a month) |
| Main focus | CAN in depth, AUTOSAR architecture, Embedded C and C++, RTOS, MISRA, testing (HIL) |
| Coding style | C and data-structure questions (linked lists, pointers) rather than long algorithm problems |
| Reported difficulty | Embedded Software Engineer candidates on Glassdoor rate it about 3.3 out of 5, with about three-quarters reporting a positive experience |

## How the process usually runs

Candidates in India describe a technical phone round of about an hour focused on CAN and Embedded C, followed by a face-to-face technical round on their current work, then a senior manager discussion and HR. Other reports describe three rounds: a high-level hiring-manager conversation, a technical interview with the team, and HR. Interviewers tend to go deep into each project on your CV.

## Topics that come up most

- **CAN:** frame fields, error management, voltage levels → [Communication Protocols](../../topics/communication-protocols/)
- **AUTOSAR:** the layered architecture (application, RTE, BSW, MCAL) → [Embedded C](../../topics/embedded-c/)
- **Embedded C and C++:** pointers, arrays, OOP basics, memory types (RAM, flash, EEPROM) → [C Programming](../../topics/c-programming/), [C++ for Embedded](../../topics/cpp-embedded/)
- **RTOS and synchronisation:** mutexes, semaphores → [RTOS](../../topics/rtos/)
- **Drivers:** I2C drivers, integrating a sensor → [Driver coding](../../topics/coding-embedded-drivers/)
- **Quality and testing:** MISRA C, hardware-in-the-loop testing → [Debugging & Testing](../../topics/debugging-testing/)

## Questions candidates reported (paraphrased)

- Explain each field of a CAN frame and how CAN handles errors.
- What voltage levels does CAN use?
- Describe the AUTOSAR layered architecture.
- How would you integrate a temperature sensor and build the RTOS application around it?
- Linked-list programs in C; mutex vs semaphore.
- Polymorphism and OOP examples in C++.
- Why do you want to work at Bosch?

## Practice questions

These are the questions Bosch candidates most often report, or close variants of them. Each links to a full answer or a coding problem with tests on this site.

1. [How does a CAN frame look?](../../topics/communication-protocols/how-does-a-can-frame-look/)
2. [How does CAN arbitration work?](../../topics/communication-protocols/how-does-can-arbitration-work/)
3. [How does CAN handle errors?](../../topics/communication-protocols/how-does-can-handle-errors/)
4. [Why does a CAN bus need 120 Ω termination?](../../topics/communication-protocols/why-does-a-can-bus-need-120-termination/)
5. [What is AUTOSAR and what are its main layers?](../../topics/embedded-c/what-is-autosar-and-what-are-its-main-layers/)
6. [What is MISRA C?](../../topics/embedded-c/what-is-misra-c/)
7. [What is the difference between a mutex and a binary semaphore?](../../topics/rtos/what-is-the-difference-between-a-mutex-and-a-binary-semaphore/)
8. [Write I2C register read and write functions.](../../topics/coding-embedded-drivers/write-i2c-register-read-and-write-functions/)
9. [How do virtual functions work? What is a vtable?](../../topics/cpp-embedded/how-do-virtual-functions-work-what-is-a-vtable/)
10. [How do you reverse a singly linked list?](../../topics/data-structures/how-do-you-reverse-a-singly-linked-list/)
11. [UART Packet Parser State Machine](../../problems/frame-parser/) *(coding)*
12. [CRC-16/CCITT-FALSE](../../problems/crc16-ccitt/) *(coding)*
13. [Moving Average Filter](../../problems/moving-average/) *(coding)*

## How to prepare

1. Know CAN thoroughly: arbitration, bit stuffing, error counters, bus-off, CAN FD.
2. Learn the AUTOSAR layers and what lives in each, even if you have not used AUTOSAR yet.
3. Revise MISRA C rules you have applied, and be ready to discuss testing (unit, HIL).
4. Practise [UART Packet Parser](../../problems/frame-parser/) and [CRC-16](../../problems/crc16-ccitt/) as proxies for protocol code.
