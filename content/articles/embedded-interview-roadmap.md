---
title: How to Prepare for an Embedded Software Interview
tag: Career
desc: What firmware, BSP and Linux driver interviews actually test, how to structure your preparation, and how to answer well.
date: 2026-11-20
order: 6
---
Embedded interviews look broad: C, hardware, operating systems, protocols, debugging stories. In practice, most companies test the same few areas in a predictable order. This guide shows you what to expect and how to spend your preparation time.

## The usual interview loop

1. **Recruiter or hiring-manager screen** (30 min): your background, the projects on your CV, why this role.
2. **Technical phone screen** (45–60 min): rapid C questions (`volatile`, `static`, pointers, bit manipulation) and one small coding exercise.
3. **On-site or virtual loop** (3–5 rounds):
   - a **coding** round in C on a shared editor or whiteboard,
   - an **embedded fundamentals** round: interrupts, memory, RTOS, peripherals,
   - a **domain** round matching the team: Linux kernel, protocols, power, display, automotive,
   - a **design** round: "design the firmware for a smart thermostat" or "design a driver for this sensor",
   - a **behavioural** round: conflict, ownership, the hardest bug you fixed.

## What each round is really testing

**C fundamentals.** Can you write correct C without a compiler holding your hand? Expect pointer declarations, integer promotion, undefined behaviour, `static`/`extern`/`const`/`volatile`, struct padding and macros. Every answer on the C topic pages is phrased the way you should say it out loud.

**Embedded coding.** The problems are small but must be **correct at the edges**: bit manipulation, a ring buffer, string parsing, a state machine, `memmove`. Interviewers watch whether you consider overflow, NULL, wrap-around, alignment and concurrency without being prompted. The practice problems on this site are built around exactly those edge cases.

**Systems knowledge.** What happens on reset, how an interrupt is taken, how a context switch works, why priority inversion happens. You need mental models, not memorised definitions.

**Domain depth.** For a Linux driver role: the device model, device tree, locking in the kernel, interrupts and bottom halves, DMA. For an MCU role: the specific peripherals and the RTOS. For automotive: CAN, AUTOSAR concepts, functional safety. Read the job description and prepare two levels deeper in that area.

**Design.** Interviewers want structure: clarify requirements, list the hardware interfaces, choose an architecture (super loop, RTOS tasks, event-driven), define data flow and timing, then cover power, error handling, updates and testing. Draw a block diagram early.

**Debugging stories.** Prepare two or three real bugs using the STAR format (situation, task, action, result), with technical detail: the symptom, what you measured, the tools you used, the root cause and what you changed to prevent it next time.

## A six-week preparation plan

| Week | Focus | On this site |
|---|---|---|
| 1 | C language and pointers | C Programming, Pointers & Memory, Bit Manipulation |
| 2 | Embedded C and the MCU | Embedded C, Microcontrollers & ARM Cortex-M |
| 3 | Concurrency | RTOS & Real-Time Systems, Operating System Concepts |
| 4 | Interfaces | Communication Protocols, Electronics & Hardware Basics |
| 5 | Your domain | Linux Kernel & Device Drivers, Embedded Linux & Boot |
| 6 | Coding speed and mock interviews | All practice problems, the quiz, timed mock sessions |

Every day, solve one or two practice problems **without looking at the solution first**, and do a 10-question quiz. Mark questions as done so you can see your weak areas.

## How to answer technical questions

- **Lead with the short answer**, then add detail. "volatile tells the compiler every access must really happen. I use it for…"
- **Name the limits** of what you just said. Interviewers love the follow-up "but it isn't atomic".
- **Give a concrete example** from hardware you have used: a register, a bug, a measurement.
- **Think aloud while coding.** State the edge cases before you write code, then test your code by walking through an example.
- **Say when you do not know**, then reason towards an answer. "I haven't used CAN FD, but I'd expect the main changes to be payload size and the data-phase bit rate because…"

## Common mistakes

- Answering `volatile` questions with "it prevents optimisation" and stopping there.
- Writing `1 << 31`, signed loop counters compared with `sizeof`, or `mid = (lo + hi) / 2` without noticing.
- Ignoring the interrupt in every shared-data question.
- Describing only what the vendor HAL did, without understanding the registers underneath.
- Talking about projects at a level so high that the interviewer cannot tell what *you* did.

## On the day

Have a pen and paper (or a whiteboard tool) ready for diagrams, a quiet room and a working headset. Keep a short list of your projects, numbers and bug stories in front of you. Ask the interviewers what the team works on day to day: it shows interest, and it tells you which questions are coming next.

Good luck. Start with the [roadmap](../../roadmap/) and work through the topics in order.
