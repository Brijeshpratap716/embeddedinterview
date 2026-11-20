---
slug: communication-protocols
title: Communication Protocols
icon: 📡
level: Intermediate
order: 7
desc: UART, SPI, I2C, CAN, CAN FD, USB, RS-485, Modbus and Ethernet. Frames, timing, arbitration and debugging.
---
You will almost certainly be asked to compare UART, SPI and I2C, then pushed on one of them in detail. Automotive roles add CAN; Linux roles add USB and Ethernet.

### Compare UART, SPI and I2C. {E}
| | UART | SPI | I2C |
|---|---|---|---|
| Wires | 2 (TX, RX) + GND | 4 (SCLK, MOSI, MISO, CS) + 1 CS per extra device | 2 (SDA, SCL) |
| Clock | Asynchronous (agreed baud rate) | Synchronous, controller drives clock | Synchronous, controller drives clock |
| Duplex | Full | Full | Half |
| Devices | Point to point | One controller, many peripherals via chip selects | Multi-controller, up to 127 addresses (7-bit) |
| Speed | Typically ≤ 1–3 Mbps | Tens of MHz | 100 kHz / 400 kHz / 1 MHz / 3.4 MHz |
| Acknowledgement | None | None | ACK/NACK per byte |
| Typical use | Debug console, GPS, modems, Bluetooth modules | Flash, displays, ADCs, SD cards | Sensors, EEPROMs, PMICs, touch controllers |

### What does a UART frame look like? {E}
The idle line is high. Each frame has:

1. **Start bit** (low), which marks the start and lets the receiver synchronise,
2. **5–9 data bits**, least significant bit first,
3. optional **parity bit** (even or odd),
4. **1, 1.5 or 2 stop bits** (high).

"115200 8N1" means 115200 baud, 8 data bits, no parity, 1 stop bit, so each byte costs 10 bit times and the payload rate is 11520 bytes/s.

### How does a UART receiver sample bits, and how much baud-rate error is tolerated? {M}
The receiver detects the falling edge of the start bit and then samples each bit near its centre, typically using 16× (or 8×) oversampling and majority voting of three samples. Because it resynchronises on every start bit, clock error only accumulates over one frame. For a 10-bit frame the last sample point must stay within half a bit, giving a total tolerance of roughly ±5% between transmitter and receiver combined, or about ±2–2.5% each in practice. That is why an internal RC oscillator can be risky at high baud rates.

### What are UART framing, parity and overrun errors? {M}
- **Framing error**: the stop bit was read as 0. Usually a baud-rate mismatch, noise, or a break condition.
- **Parity error**: the received parity bit does not match the data.
- **Overrun error**: a new byte arrived before software read the previous one from the data register, so data was lost. Fix with faster ISR handling, a FIFO, or DMA.
- **Noise error**: the oversampled values within a bit disagreed.

Clear the error flags as the reference manual describes, or the UART may stop receiving.

### What is hardware flow control? {E}
RTS/CTS lines let a receiver tell the transmitter to pause. The receiver de-asserts RTS when its buffer is nearly full; the transmitter checks CTS before sending each byte. It prevents overruns at high baud rates, for example with cellular modems and Bluetooth modules. Software flow control (XON/XOFF characters) does the same in-band but cannot be used with binary data.

### How does RS-232 differ from RS-485 and TTL UART? {M}
They are physical layers for the same UART framing:

- **TTL/CMOS UART**: logic levels (0/3.3 V or 0/5 V), short board-level distances.
- **RS-232**: single-ended, inverted, ±3 V to ±15 V levels, point-to-point, up to about 15 m.
- **RS-485**: differential pair (A/B), very noise immune, up to 1200 m, **multi-drop** with up to 32 unit loads (more with fractional-load transceivers), usually half duplex. Needs 120 Ω termination at both ends and driver-enable control; protocols such as Modbus RTU run on top.

### What are the SPI modes (CPOL and CPHA)? {M}
- **CPOL** sets the idle clock level: 0 = idle low, 1 = idle high.
- **CPHA** sets the sampling edge: 0 = sample on the first (leading) edge, 1 = sample on the second (trailing) edge.

| Mode | CPOL | CPHA | Sample edge |
|---|---|---|---|
| 0 | 0 | 0 | Rising |
| 1 | 0 | 1 | Falling |
| 2 | 1 | 0 | Falling |
| 3 | 1 | 1 | Rising |

Mode 0 and 3 are most common. The controller and the device must use the same mode, or you will see bits shifted by one.

### How do you connect multiple SPI devices? {E}
- **Independent chip selects**: one CS line per device, all sharing SCLK/MOSI/MISO. Each device's MISO must be high-impedance when deselected.
- **Daisy chain**: MISO of one device feeds MOSI of the next, with one shared CS; data shifts through all devices like one long shift register (common for LED drivers and shift registers).

Use an I/O expander or decoder if you run out of CS pins.

### What are Dual, Quad and Octal SPI? {M}
Extensions that use 2, 4 or 8 bidirectional data lines instead of a single MOSI/MISO pair, multiplying throughput. Quad SPI (QSPI) NOR flash is common for external code storage, and many MCUs support **execute-in-place (XIP)**: the flash is memory-mapped so the CPU fetches instructions directly. Octal SPI and HyperBus reach hundreds of MB/s for external RAM and display frame buffers.

### What does an I2C transaction look like? {E}
1. **START**: SDA falls while SCL is high.
2. **Address byte**: 7-bit address plus a R/W bit (0 = write, 1 = read).
3. **ACK**: the addressed device pulls SDA low on the 9th clock.
4. **Data bytes**, each followed by ACK/NACK. The receiver ACKs; the controller NACKs the last byte of a read.
5. **STOP**: SDA rises while SCL is high.

To read a register, write the register address, then issue a **repeated START** (no STOP) with the read bit, then read data.

### Why does I2C need pull-up resistors, and how do you size them? {M}
Both lines are **open-drain**: devices can only pull them low, so resistors pull them high. The resistor value is a trade-off:

- **Too large**: the RC rise time from bus capacitance is too slow for the speed mode (max rise time is 1000 ns at 100 kHz, 300 ns at 400 kHz).
- **Too small**: devices cannot sink enough current to reach a valid low (3 mA at standard/fast mode).

Rp(min) = (Vdd − 0.4 V) / 3 mA, and Rp(max) ≈ t_rise / (0.8473 × C_bus). Typical values are 2.2 kΩ to 10 kΩ, with 4.7 kΩ common at 100 kHz.

### What is clock stretching? {M}
A target device holds SCL low after a byte to tell the controller to wait until it is ready, for example while it performs a conversion. The controller must check that SCL actually went high before continuing. Some controllers (notably some older Raspberry Pi I2C hardware) handle stretching badly, which causes corrupted transfers with certain sensors.

### How does I2C arbitration work with multiple controllers? {H}
Every controller monitors SDA while transmitting. Because the bus is wired-AND, a 0 always wins. If a controller sends a 1 but reads back a 0, it has lost arbitration and stops transmitting immediately, without corrupting the winner's message. Arbitration happens bit by bit through the address and data, so the transfer to the lowest address wins. Clock synchronisation works the same way on SCL: the low period is set by the slowest controller.

### How do you recover a stuck I2C bus? {M}
If a target was reset mid-read it may be holding SDA low, waiting to send the rest of a byte. Recovery:

1. Reconfigure SCL as GPIO open-drain output.
2. Toggle SCL up to 9 times until SDA is released (the target finishes its byte and sees a NACK).
3. Generate a STOP condition manually.
4. Return the pins to I2C mode and reset the peripheral.

The Linux kernel implements this in `i2c_recover_bus()`.

### What is the difference between 7-bit and 10-bit I2C addressing? {E}
7-bit addressing gives 128 addresses, of which 16 are reserved, so 112 are usable. 10-bit addressing sends a first byte `11110xx` (with the 2 high address bits) followed by a second byte with the remaining 8 bits. 10-bit devices are rare. Address conflicts between identical sensors are solved with address-select pins or an I2C multiplexer.

### What is SMBus, and what is I3C? {M}
- **SMBus** is a stricter subset of I2C for system management (batteries, power): defined voltage levels, a 25–35 ms clock timeout, a minimum 10 kHz clock, optional packet error checking (CRC-8) and standard commands.
- **I3C** (MIPI) is the successor to I2C: backward compatible with I2C targets, push-pull at up to 12.5 MHz SDR (higher in HDR modes), dynamic address assignment and **in-band interrupts** so sensors do not need separate interrupt pins.

### How does a CAN frame look? {M}
A classic CAN 2.0A data frame:

1. **SOF** (dominant bit)
2. **Arbitration field**: 11-bit identifier + RTR bit (29-bit ID in 2.0B extended frames)
3. **Control field**: IDE, r0, 4-bit DLC (0–8 data bytes)
4. **Data field**: 0–8 bytes
5. **CRC field**: 15-bit CRC + delimiter
6. **ACK slot + delimiter**: any node that received the frame correctly drives the slot dominant
7. **EOF**: 7 recessive bits

**Bit stuffing**: after 5 identical bits the transmitter inserts one opposite bit, so receivers keep synchronised.

### How does CAN arbitration work? {M}
CAN is multi-controller with **non-destructive bitwise arbitration**. Dominant (0) overrides recessive (1) on the bus. All nodes transmit their ID simultaneously and read the bus. A node that sends recessive but reads dominant has lost and stops sending, then retries later. The frame with the **lowest ID wins** without being corrupted or delayed. IDs therefore double as priorities, which is why safety-critical messages get low IDs.

### How does CAN handle errors? {H}
Five error detection mechanisms: bit monitoring, bit stuffing check, frame (form) check, CRC check, and ACK check. A node that detects an error sends an **error frame** (6 dominant bits, violating stuffing), so all nodes discard the frame and the sender retransmits automatically.

Each node keeps transmit and receive error counters (TEC/REC):

- **Error active** (both < 128): normal.
- **Error passive** (either ≥ 128): sends passive error flags and waits longer before retransmitting.
- **Bus off** (TEC ≥ 256): the node disconnects from the bus until it sees 128 × 11 recessive bits and software requests recovery.

This confinement stops one faulty node bringing down the bus.

### What is the difference between CAN and CAN FD? {M}
CAN FD (Flexible Data-rate) keeps classic arbitration but:

- allows up to **64 data bytes** per frame instead of 8,
- switches to a **higher bit rate** for the data phase (commonly 2–5 Mbps, versus ≤ 1 Mbps for arbitration),
- uses stronger CRCs (17 or 21 bits) and a stuff-bit counter,
- drops remote frames.

The FDF bit marks a frame as FD and BRS enables the bit-rate switch. Classic CAN controllers that see an FD frame raise error frames, so mixed networks need care. **CAN XL** extends payloads to 2048 bytes.

### Why does a CAN bus need 120 Ω termination? {E}
The bus is a differential transmission line with about 120 Ω characteristic impedance. A 120 Ω resistor at **each end** prevents reflections, and the pair of them (60 Ω total) also sets the load that pulls the bus back to recessive. Measuring about 60 Ω between CAN_H and CAN_L with power off is a quick check that both terminators are present.

### What is a CAN bit time and how are its segments configured? {H}
A bit is divided into time quanta (tq): **Sync segment** (1 tq), **Propagation segment**, **Phase segment 1** and **Phase segment 2**. The **sample point** sits between phase 1 and 2, usually at 75–87.5% of the bit. The **SJW** (synchronisation jump width) limits how far the receiver may lengthen or shorten a phase segment to resync on edges. Example: 8 MHz CAN clock, prescaler 1 gives 125 ns tq; 16 tq per bit gives 500 kbps; sync 1 + prop+phase1 13 + phase2 2 puts the sample point at 87.5%.

### What are the USB transfer types? {M}
- **Control**: setup and configuration on endpoint 0 (enumeration, requests). Guaranteed delivery.
- **Bulk**: large, error-checked data with no timing guarantee (mass storage, printers, CDC data).
- **Interrupt**: small, periodic, guaranteed maximum latency (keyboards, mice, HID).
- **Isochronous**: guaranteed bandwidth and timing but no retransmission (audio, video).

All transfers are host-initiated; a device can only respond when polled.

### What happens during USB enumeration? {H}
1. Device attaches; host detects the pull-up on D+ (full speed) or D− (low speed).
2. Host resets the bus; high-speed devices perform the chirp handshake.
3. Host sends `GET_DESCRIPTOR(Device)` to address 0 to learn the max packet size of endpoint 0.
4. Host assigns an address with `SET_ADDRESS`.
5. Host reads the full device, configuration, interface, endpoint and string descriptors.
6. Host selects a driver based on class/VID/PID, then sends `SET_CONFIGURATION`.

After this the device's endpoints are usable. On Linux, `lsusb -v` shows the descriptors and `dmesg` the driver binding.

### What is Modbus? {E}
A simple request/response industrial protocol. A client (master) sends a function code and register address to a server (slave), which replies. **Modbus RTU** runs over RS-485 with binary frames, a 1-byte address and CRC-16, and frames separated by 3.5 character times of silence. **Modbus TCP** wraps the same function codes in TCP on port 502. Common function codes: 03 (read holding registers), 06 (write single register), 16 (write multiple registers).

### What layers does an embedded Ethernet interface involve? {M}
- **MAC** (media access controller), usually inside the MCU or SoC, handles framing, CRC, and DMA descriptors.
- **PHY**, often an external chip, handles the physical signalling (10/100/1000BASE-T) and auto-negotiation.
- **MII/RMII/RGMII** connects MAC and PHY for data; **MDIO/MDC** is a management bus to read and write PHY registers (link status, speed).
- A TCP/IP stack (lwIP, Zephyr's stack, or Linux) runs above the MAC driver.

Common bring-up issues: wrong RMII reference clock, wrong PHY address, and missing reset timing.

### What is the difference between TCP and UDP for embedded devices? {E}
TCP gives reliable, ordered, connection-oriented byte streams with retransmission and flow control, at the cost of RAM for buffers and higher latency. UDP sends independent datagrams with no delivery guarantee, so it is lighter and lower latency. Embedded protocols on UDP: CoAP, DNS, DHCP, real-time telemetry. On TCP: MQTT, HTTP, Modbus TCP. MQTT over TCP is the most common IoT choice; CoAP over UDP suits very constrained devices.
