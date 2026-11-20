---
title: UART vs SPI vs I2C vs CAN — Choosing a Serial Bus
tag: Protocols
desc: How the four buses differ in wiring, speed, topology and reliability, and how to choose one for a design.
date: 2026-11-20
order: 4
---
Comparing serial buses is the most predictable protocol question in embedded interviews. A table is a good start, but strong candidates explain **why** each bus behaves as it does and can justify a choice for a real design.

## The one-line summary of each

- **UART**: two wires, no clock, point to point. Simple and universal; both ends must agree on the baud rate.
- **SPI**: a shared clock and two data lines plus a chip select per device. Fast and full duplex, but no addressing or acknowledgement, and pin count grows with devices.
- **I2C**: two open-drain wires, addressed devices, acknowledgement per byte. Few pins and many devices, but slow and sensitive to bus capacitance.
- **CAN**: a differential pair, multi-controller, message-based with priority arbitration and strong error handling. Built for noisy, safety-relevant networks.

## Side-by-side

| | UART | SPI | I2C | CAN |
|---|---|---|---|---|
| Signals | TX, RX | SCLK, MOSI, MISO, CS×n | SDA, SCL | CAN_H, CAN_L |
| Clocking | Asynchronous | Synchronous | Synchronous | Asynchronous (bit-timed) |
| Topology | Point to point | One controller, star of CS lines | Multi-drop bus | Multi-drop bus |
| Addressing | None | Chip select | 7/10-bit address | Message ID |
| Typical speed | 9.6 kbps – 3 Mbps | 1 – 100 MHz | 100 kHz – 1 MHz | 125 kbps – 1 Mbps (FD: 5+ Mbps data) |
| Distance | Board (RS-485: 1 km) | Board | Board | 40 m at 1 Mbps, 500 m at 125 kbps |
| Error detection | Optional parity | None | ACK/NACK | CRC, stuffing, ACK, automatic retransmit |

## Why they behave the way they do

**UART has no clock**, so the receiver re-synchronises on every start bit and samples in the middle of each bit. That is why the clocks of both ends must match within a few percent, and why a frame cannot be very long. It is also why UART is easy to route across a cable or a connector.

**SPI is just shift registers.** Each clock edge moves one bit out and one bit in on both sides, so every transfer is full duplex and the speed is limited mainly by trace length and the slowest device. There is no protocol layer, so the controller does not know whether a device is even present; you find out by reading back an ID register.

**I2C is open-drain.** Any device can pull a line low, and resistors pull it high. This "wired-AND" makes acknowledgement, clock stretching and multi-controller arbitration possible with only two wires. The cost is speed: the rising edge is an RC curve set by the pull-up and bus capacitance, so long buses or many devices slow it down.

**CAN is differential and wired-AND too.** The dominant state (0) overrides recessive (1), so all nodes can transmit at once and the message with the lowest ID wins arbitration without being damaged. Differential signalling gives excellent noise immunity, and the error counters and bus-off state stop one faulty node from jamming the network.

## How to choose

Ask these questions in order:

1. **What does the other chip support?** Most sensors offer I2C or SPI; GPS and cellular modules use UART; vehicle and industrial networks use CAN. This usually decides it.
2. **How much bandwidth do you need?** Displays, external flash and fast ADCs need SPI (or Quad SPI). Temperature and humidity sensors are fine on I2C.
3. **How many devices and pins?** Ten sensors on I2C need two pins; on SPI they need thirteen.
4. **How far, and how noisy?** Off-board or in a vehicle, use a differential bus: CAN or RS-485. I2C and SPI are for short on-board traces.
5. **How critical is reliability?** CAN's automatic retransmission and fault confinement are hard to match. On I2C and SPI you must add CRCs and retries yourself if you need them.

## Example design answers

> *"A wearable with an accelerometer, a heart-rate sensor and a fuel gauge?"* I2C for all three: low data rates, few pins, and all three support it. I would put the accelerometer on SPI instead if I needed high sample rates with FIFO bursts.

> *"A 320×240 colour display?"* SPI with DMA at 40+ MHz; one full frame is 150 KB at 16 bits per pixel, which is far too much for I2C.

> *"Ten motor controllers spread through a machine?"* CAN (or CAN FD): long cables, electrical noise, multi-controller, priority for emergency-stop messages, and built-in error handling.

> *"A debug console?"* UART. Every USB-serial adapter and terminal program speaks it.

## Common follow-ups

- *What happens if two I2C devices have the same address?* Use their address pins, an I2C multiplexer (TCA9548A), or put them on separate buses.
- *How do you know an SPI device is connected?* Read a known ID register; there is no ACK.
- *Why does CAN need termination?* To match the 120 Ω line impedance and prevent reflections, and to pull the bus back to recessive.
- *Can I2C run at 1 MHz over 1 m of cable?* Unlikely: capacitance makes rise times too slow. Use a bus buffer or a differential extender, or pick another bus.

Each of these buses has its own topic page in the question bank with detailed questions on framing, timing and failure modes.
