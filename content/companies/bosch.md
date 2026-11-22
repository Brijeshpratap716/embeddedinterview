---
title: Bosch
desc: Bosch embedded and automotive software interviews: CAN, AUTOSAR layers, Embedded C, RTOS, MISRA, HIL testing and project deep dives. What candidates report.
roles: Embedded Software Engineer, Embedded Developer, AUTOSAR Engineer
hubs: Bengaluru, Coimbatore, Stuttgart, Budapest, Ho Chi Minh City
focus: CAN, AUTOSAR, Embedded C, RTOS, automotive testing
order: 12
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

## How to prepare

1. Know CAN thoroughly: arbitration, bit stuffing, error counters, bus-off, CAN FD.
2. Learn the AUTOSAR layers and what lives in each, even if you have not used AUTOSAR yet.
3. Revise MISRA C rules you have applied, and be ready to discuss testing (unit, HIL).
4. Practise [UART Packet Parser](../../problems/frame-parser/) and [CRC-16](../../problems/crc16-ccitt/) as proxies for protocol code.

## Read real experiences

- [Glassdoor: Robert Bosch – CAN frames, error management, Embedded C (Coimbatore)](https://www.glassdoor.com.au/Interview/Robert-Bosch-Interview-E3353-RVW8430885.htm)
- [Glassdoor: Robert Bosch – linked lists, mutexes, I2C drivers, CAN](https://www.glassdoor.com/Interview/Robert-Bosch-Interview-E3353-RVW13938744.htm)
- [Glassdoor: Robert Bosch Embedded Developer interview questions (AUTOSAR layers)](https://static.glassdoor.com.br/Interview/Robert-Bosch-Embedded-Developer-Interview-Questions-EI_IE3353.0,12_KO13,31.htm)
- [Glassdoor: Robert Bosch – temperature sensor integration and RTOS](https://www.glassdoor.ca/Interview/Robert-Bosch-Interview-E3353-RVW82453143.htm)
- [Glassdoor: Bosch Embedded Software Engineer – CAN questions](https://www.glassdoor.com/Interview/Bosch-Interview-RVW5567201.htm)
- [AmbitionBox: Bosch Embedded Software Engineer interview questions](https://www.ambitionbox.com/interviews/bosch-interview-questions/embedded-software-engineer)
