---
title: UART vs SPI vs I2C vs CAN — Choosing a Serial Bus
tag: Protocols
desc: How the four buses differ in wiring, speed, topology and reliability, and how to choose one for a design.
date: 2026-11-20
order: 4
---

## Comparison

| Feature | UART | SPI | I2C | CAN |
|---|---|---|---|---|
| Signals | TX, RX | SCLK, MOSI, MISO, CS | SDA, SCL | CAN_H, CAN_L |
| Clock | Async | Sync | Sync | Async bit timing |
| Selection | Point-to-point | Chip select | 7/10-bit address | Message ID |
| Speed (typical) | 9.6 kbps–3 Mbps | 1–100 MHz | 100 kHz–1 MHz | Up to 1 Mbps classic |
| Error handling | Parity / framing | Application-specific | ACK/NACK | CRC, ACK, retry |
| Use | Debug, GPS | Display, flash | Sensors | Automotive |

Actual speed depends on hardware and wiring.

## How they work

- **UART:** Start bit → data → optional parity → stop bit. Both devices agree on baud rate.
- **SPI:** Select peripheral with CS, then exchange bits on clock edges. CPOL/CPHA select timing.
- **I2C:** START → address → ACK → data → STOP. Open-drain lines need pull-up resistors.
- **CAN:** Differential signalling, nondestructive arbitration and error handling. Lower IDs generally have higher priority for the same frame format. Usually terminate both ends with 120 Ω.

## C examples

Illustrative STM32 HAL calls; assume initialized peripheral handles, GPIO and a matching MCU HAL version.

```c
// UART: send a byte
uint8_t tx = 0x55;
HAL_UART_Transmit(&huart1, &tx, 1, 100);

// SPI: exchange one byte (assert/deassert CS as needed)
uint8_t rx;
HAL_SPI_TransmitReceive(&hspi1, &tx, &rx, 1, 100);

// I2C: read one byte from register 0x10 of device 0x50
HAL_I2C_Mem_Read(&hi2c1, 0x50 << 1, 0x10,
                 I2C_MEMADD_SIZE_8BIT, &rx, 1, 100);
```

For classic CAN using STM32 bxCAN HAL:

```c
CAN_TxHeaderTypeDef hdr = {
    .StdId = 0x123, .IDE = CAN_ID_STD,
    .RTR = CAN_RTR_DATA, .DLC = 1
};
uint32_t mailbox;
HAL_CAN_AddTxMessage(&hcan1, &hdr, &tx, &mailbox);
```

Production code must check return values and handle timeouts/errors.
