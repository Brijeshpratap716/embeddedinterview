---
title: UART vs SPI vs I2C vs CAN — Choosing a Serial Bus
tag: Protocols
desc: How the four buses differ in wiring, speed, topology and reliability, and how to choose one for a design.
date: 2026-11-20
order: 4
---

UART, SPI, I2C and CAN are common serial communication interfaces. Choose based on speed, pin count, distance and reliability.

## Comparison

| Feature | UART | SPI | I2C | CAN |
|---|---|---|---|---|
| Signals | TX, RX | SCLK, MOSI, MISO, CS | SDA, SCL | CAN_H, CAN_L |
| Clock | Asynchronous | Synchronous | Synchronous | Asynchronous bit timing |
| Topology | Point-to-point | Controller + peripherals | Shared addressed bus | Multi-controller bus |
| Addressing | None | Chip select | 7/10-bit address | Message ID |
| Typical speed | 9.6 kbps–3 Mbps | 1–100 MHz | 100 kHz–1 MHz | Up to 1 Mbps classic; faster CAN FD data phase |
| Error handling | Optional parity, framing | Application-specific | ACK/NACK, not integrity checking | CRC, ACK, retransmission, fault confinement |

Speeds depend on devices, wiring and configuration.

## How each works

- **UART:** Start bit, data bits, optional parity and stop bit. Both ends agree on baud rate.
- **SPI:** Clock shifts data between controller and peripheral, typically full duplex. Chip select chooses the peripheral. CPOL/CPHA define clock timing.
- **I2C:** Open-drain lines with pull-up resistors. START → address → ACK → data → STOP. Supports arbitration and clock stretching where implemented.
- **CAN:** Differential signalling and nondestructive arbitration. Dominant bits override recessive bits; lower numerical IDs generally win within the same frame format.

## When to use which?

| Application | Choice |
|---|---|
| Debug console or GPS module | UART |
| Fast display, ADC or flash | SPI |
| Multiple low-speed sensors | I2C |
| Automotive or industrial network | CAN |

## Common interview questions

**Why does I2C need pull-ups?** Open-drain devices pull low; resistors restore the high level.

**Same I2C address?** Change address pins, use a multiplexer or separate buses.

**How to detect an SPI device?** Read a known ID register; SPI has no built-in ACK.

**Why CAN termination?** Typically 120 Ω at each end of the bus to match impedance and reduce reflections.

**Long cable?** Prefer CAN or an appropriate differential transceiver such as RS-485 rather than raw board-level UART, SPI or I2C.
