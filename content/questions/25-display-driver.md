---
slug: display-driver
title: Display Driver
icon: 🖥️
level: Intermediate
order: 25
desc: Linux DRM/KMS, display pipelines, framebuffers, atomic commits, DMA, VSync, MSM/DPU and panel initialization.
---
Display driver interview preparation for embedded Linux, Android, BSP and graphics engineers.

### Explain the complete flow of a display driver in Linux. {M}
In Linux, modern display drivers are implemented using the **DRM (Direct Rendering Manager) and KMS (Kernel Mode Setting)** frameworks.

The display driver is responsible for configuring display hardware, managing framebuffers, processing pixels, and sending them to the physical display panel.

#### 1. Complete Linux display architecture

<figure style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 576" width="100%" role="img" aria-label="Simplified userspace-to-hardware display architecture; rendering and scanout are separate operations." font-family="system-ui,sans-serif" text-anchor="middle"><rect x="80" y="3" width="520" height="52" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="24" fill="#0c4a6e" font-size="16" font-weight="600">Application</text><text x="340" y="43" fill="#0c4a6e" font-size="13">Android App / Linux Application</text><path d="M340 55 v17 m-5 -5 l5 5 l5 -5" fill="none" stroke="#0369a1" stroke-width="2"/><rect x="80" y="75" width="520" height="52" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="96" fill="#0c4a6e" font-size="16" font-weight="600">Graphics API</text><text x="340" y="115" fill="#0c4a6e" font-size="13">OpenGL ES / Vulkan / EGL</text><path d="M340 127 v17 m-5 -5 l5 5 l5 -5" fill="none" stroke="#0369a1" stroke-width="2"/><rect x="80" y="147" width="520" height="52" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="168" fill="#0c4a6e" font-size="16" font-weight="600">Display Compositor</text><text x="340" y="187" fill="#0c4a6e" font-size="13">SurfaceFlinger / Weston / X11</text><path d="M340 199 v17 m-5 -5 l5 5 l5 -5" fill="none" stroke="#0369a1" stroke-width="2"/><rect x="80" y="219" width="520" height="52" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="240" fill="#0c4a6e" font-size="16" font-weight="600">DRM Userspace Interface</text><text x="340" y="259" fill="#0c4a6e" font-size="13">libdrm / Hardware Composer</text><path d="M340 271 v17 m-5 -5 l5 5 l5 -5" fill="none" stroke="#0369a1" stroke-width="2"/><rect x="80" y="291" width="520" height="52" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="312" fill="#0c4a6e" font-size="16" font-weight="600">Linux DRM / KMS Framework</text><text x="340" y="331" fill="#0c4a6e" font-size="13">Atomic commit / Mode setting</text><path d="M340 343 v17 m-5 -5 l5 5 l5 -5" fill="none" stroke="#0369a1" stroke-width="2"/><rect x="80" y="363" width="520" height="52" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="384" fill="#0c4a6e" font-size="16" font-weight="600">SoC Display Driver</text><text x="340" y="403" fill="#0c4a6e" font-size="13">MSM / Intel i915</text><path d="M340 415 v17 m-5 -5 l5 5 l5 -5" fill="none" stroke="#0369a1" stroke-width="2"/><rect x="80" y="435" width="520" height="52" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="456" fill="#0c4a6e" font-size="16" font-weight="600">Display Controller (DPU)</text><text x="340" y="475" fill="#0c4a6e" font-size="13">Planes / Mixer / Timing Engine</text><path d="M340 487 v17 m-5 -5 l5 5 l5 -5" fill="none" stroke="#0369a1" stroke-width="2"/><rect x="80" y="507" width="520" height="52" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="528" fill="#0c4a6e" font-size="16" font-weight="600">Physical Display Panel</text><text x="340" y="547" fill="#0c4a6e" font-size="13">DSI / eDP / HDMI</text></svg><figcaption>Simplified userspace-to-hardware display architecture; rendering and scanout are separate operations.</figcaption></figure>

#### 2. Important DRM/KMS components

| Component | Responsibility |
|---|---|
| GEM | Graphics buffer memory management |
| Framebuffer | Describes pixel buffer, format, pitch and dimensions |
| Plane | Reads framebuffer and performs scaling, cropping and rotation if supported |
| CRTC | Controls composition, scanout and display timing |
| Encoder | Represents the conversion of display output to an appropriate interface signal |
| Bridge | Converts or processes display interface signals |
| Connector | Represents the display output endpoint |
| Panel | Represents the physical display panel |

<figure style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 360" width="100%" role="img" aria-label="Multiple hardware planes can be combined into a single display output. The connector is a logical KMS object." font-family="system-ui,sans-serif" text-anchor="middle"><rect x="80" y="3" width="520" height="52" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="24" fill="#0c4a6e" font-size="16" font-weight="600">Framebuffers 0, 1, 2</text><text x="340" y="43" fill="#0c4a6e" font-size="13">Separate pixel buffers</text><path d="M340 55 v17 m-5 -5 l5 5 l5 -5" fill="none" stroke="#0369a1" stroke-width="2"/><rect x="80" y="75" width="520" height="52" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="96" fill="#0c4a6e" font-size="16" font-weight="600">Planes 0, 1, 2</text><text x="340" y="115" fill="#0c4a6e" font-size="13">Fetch, crop and scale</text><path d="M340 127 v17 m-5 -5 l5 5 l5 -5" fill="none" stroke="#0369a1" stroke-width="2"/><rect x="80" y="147" width="520" height="52" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="168" fill="#0c4a6e" font-size="16" font-weight="600">CRTC / Layer Mixer</text><text x="340" y="187" fill="#0c4a6e" font-size="13">Combine layers and control timing</text><path d="M340 199 v17 m-5 -5 l5 5 l5 -5" fill="none" stroke="#0369a1" stroke-width="2"/><rect x="80" y="219" width="520" height="52" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="240" fill="#0c4a6e" font-size="16" font-weight="600">Encoder / Bridge</text><text x="340" y="259" fill="#0c4a6e" font-size="13">Display link</text><path d="M340 271 v17 m-5 -5 l5 5 l5 -5" fill="none" stroke="#0369a1" stroke-width="2"/><rect x="80" y="291" width="520" height="52" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="312" fill="#0c4a6e" font-size="16" font-weight="600">Connector / Panel</text><text x="340" y="331" fill="#0c4a6e" font-size="13">Logical output endpoint and physical display</text></svg><figcaption>Multiple hardware planes can be combined into a single display output. The connector is a logical KMS object.</figcaption></figure>

#### 3. Display driver initialization flow

During Linux kernel boot:

1. Kernel reads the Device Tree or discovers hardware through ACPI/PCI.
2. Display platform driver's `probe()` function is called.
3. Driver initializes hardware resources: MMIO registers, clocks and regulators, interrupts, IOMMU, GPIOs and power domains.
4. DRM device is allocated.
5. Planes, CRTCs, encoders and connectors are initialized.
6. Panel and bridge drivers are attached.
7. DRM device is registered using `drm_dev_register()`.
8. Userspace gets access through `/dev/dri/card0` (device number may vary).

#### 4. Runtime display flow

**Step 1: Frame rendering**

The application uses OpenGL ES, Vulkan or CPU rendering to generate pixel data. The GPU or CPU writes the rendered frame into a graphics buffer in memory.

**Step 2: Framebuffer creation**

Userspace creates or imports a graphics buffer and registers a framebuffer using DRM APIs.

```c
drmModeAddFB2();
```

The framebuffer contains metadata such as width, height, pixel format, pitch and buffer handles.

**Step 3: Atomic commit**

The compositor configures display properties and submits an atomic commit.

```c
drmModeAtomicAddProperty();
drmModeAtomicCommit();
```

The corresponding kernel flow is approximately:

```text
DRM_IOCTL_MODE_ATOMIC
        |
drm_mode_atomic_ioctl()
        |
drm_atomic_check_only()
        |
Driver atomic_check()
        |
drm_atomic_commit()
        |
Driver atomic_commit()
        |
Hardware register programming
```

Exact call paths vary by driver and kernel version.

**Step 4: Atomic check**

The driver validates the requested configuration:

- Resolution and refresh rate
- Pixel format
- Plane availability
- Scaling limitations
- Memory bandwidth
- Clock requirements
- Hardware resource availability

If validation fails, the commit is rejected.

**Step 5: Hardware programming**

The driver configures the display controller registers, including framebuffer IOVA (when an IOMMU is used), stride, source and destination dimensions, pixel format, layer mixer and timing parameters.

**Step 6: Display controller fetches pixels**

The display controller independently fetches framebuffer data from DDR memory using DMA.

<figure style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 360" width="100%" role="img" aria-label="The CPU does not need to transfer every pixel manually." font-family="system-ui,sans-serif" text-anchor="middle"><rect x="80" y="3" width="520" height="52" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="24" fill="#0c4a6e" font-size="16" font-weight="600">GPU / CPU</text><text x="340" y="43" fill="#0c4a6e" font-size="13">Writes rendered pixels</text><path d="M340 55 v17 m-5 -5 l5 5 l5 -5" fill="none" stroke="#0369a1" stroke-width="2"/><rect x="80" y="75" width="520" height="52" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="96" fill="#0c4a6e" font-size="16" font-weight="600">DDR Memory</text><text x="340" y="115" fill="#0c4a6e" font-size="13">Framebuffer</text><path d="M340 127 v17 m-5 -5 l5 5 l5 -5" fill="none" stroke="#0369a1" stroke-width="2"/><rect x="80" y="147" width="520" height="52" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="168" fill="#0c4a6e" font-size="16" font-weight="600">DMA / IOMMU</text><text x="340" y="187" fill="#0c4a6e" font-size="13">Display controller reads pixels; IOMMU translates if enabled</text><path d="M340 199 v17 m-5 -5 l5 5 l5 -5" fill="none" stroke="#0369a1" stroke-width="2"/><rect x="80" y="219" width="520" height="52" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="240" fill="#0c4a6e" font-size="16" font-weight="600">Display Controller</text><text x="340" y="259" fill="#0c4a6e" font-size="13">Processing and scanout</text><path d="M340 271 v17 m-5 -5 l5 5 l5 -5" fill="none" stroke="#0369a1" stroke-width="2"/><rect x="80" y="291" width="520" height="52" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="312" fill="#0c4a6e" font-size="16" font-weight="600">DSI / HDMI / eDP</text><text x="340" y="331" fill="#0c4a6e" font-size="13">Pixel stream to panel</text></svg><figcaption>The CPU does not need to transfer every pixel manually.</figcaption></figure>

**Step 7: VSync and page flip**

At the appropriate display synchronization point, the hardware switches to the new framebuffer. The display controller generates interrupts, and the driver handles vblank events, page-flip completion and fence signaling. This allows smooth rendering and helps prevent tearing.

#### 5. MSM/DPU display driver example

<figure style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 504" width="100%" role="img" aria-label="Simplified Android display control and pixel pipeline." font-family="system-ui,sans-serif" text-anchor="middle"><rect x="80" y="3" width="520" height="52" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="24" fill="#0c4a6e" font-size="16" font-weight="600">SurfaceFlinger / HWC</text><text x="340" y="43" fill="#0c4a6e" font-size="13">Userspace</text><path d="M340 55 v17 m-5 -5 l5 5 l5 -5" fill="none" stroke="#0369a1" stroke-width="2"/><rect x="80" y="75" width="520" height="52" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="96" fill="#0c4a6e" font-size="16" font-weight="600">MSM DRM Driver</text><text x="340" y="115" fill="#0c4a6e" font-size="13">Atomic commit</text><path d="M340 127 v17 m-5 -5 l5 5 l5 -5" fill="none" stroke="#0369a1" stroke-width="2"/><rect x="80" y="147" width="520" height="52" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="168" fill="#0c4a6e" font-size="16" font-weight="600">SSPP (Source Surface Pixel Processor)</text><text x="340" y="187" fill="#0c4a6e" font-size="13">Fetch, scaling and format conversion</text><path d="M340 199 v17 m-5 -5 l5 5 l5 -5" fill="none" stroke="#0369a1" stroke-width="2"/><rect x="80" y="219" width="520" height="52" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="240" fill="#0c4a6e" font-size="16" font-weight="600">Layer Mixer (LM)</text><text x="340" y="259" fill="#0c4a6e" font-size="13">Blending and composition</text><path d="M340 271 v17 m-5 -5 l5 5 l5 -5" fill="none" stroke="#0369a1" stroke-width="2"/><rect x="80" y="291" width="520" height="52" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="312" fill="#0c4a6e" font-size="16" font-weight="600">Ping Pong / Timing / Interface</text><text x="340" y="331" fill="#0c4a6e" font-size="13">Display synchronization</text><path d="M340 343 v17 m-5 -5 l5 5 l5 -5" fill="none" stroke="#0369a1" stroke-width="2"/><rect x="80" y="363" width="520" height="52" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="384" fill="#0c4a6e" font-size="16" font-weight="600">DSI Controller + PHY</text><text x="340" y="403" fill="#0c4a6e" font-size="13">MIPI DSI transmission</text><path d="M340 415 v17 m-5 -5 l5 5 l5 -5" fill="none" stroke="#0369a1" stroke-width="2"/><rect x="80" y="435" width="520" height="52" rx="8" fill="#e0f2fe" stroke="#0369a1"/><text x="340" y="456" fill="#0c4a6e" font-size="16" font-weight="600">Display Panel</text><text x="340" y="475" fill="#0c4a6e" font-size="13">Physical pixel output</text></svg><figcaption>Simplified Android display control and pixel pipeline.</figcaption></figure>

| Block | Function |
|---|---|
| SSPP | Fetches framebuffer data from memory |
| LM | Blends multiple layers |
| CTL | Controls configuration and hardware flush |
| DSPP | Color correction and post-processing |
| Ping Pong | Display synchronization |
| INTF | Display interface and timing control |
| DSI PHY | Physical transmission of display data |

#### 6. Panel power-on sequence

A typical panel initialization sequence is:

```text
drm_panel_prepare()
    |
Enable regulators
    |
Perform GPIO reset sequence
    |
Send DSI / I2C initialization commands
    |
Configure display link and timing
    |
drm_panel_enable()
    |
Enable backlight (if applicable)
```

The exact ordering depends on the hardware and panel driver. Panel initialization commands and actual pixel transmission are separate operations.

#### 7. Interview-ready answer (60 seconds)

Linux display drivers use the DRM/KMS framework. During boot, the driver initializes hardware resources and registers DRM objects such as planes, CRTCs, encoders and connectors.

During runtime, the application renders frames into graphics buffers using the GPU or CPU. The compositor creates framebuffers and submits an atomic commit through the DRM interface.

The kernel validates the configuration and programs the display controller registers. The display controller fetches pixel data from DDR using DMA, performs scaling and layer blending, and generates display timing. The pixel stream is then transmitted to the physical panel through DSI, HDMI or eDP.

VSync interrupts, page flips and synchronization fences ensure that frames are displayed correctly and help prevent tearing.

**The most important distinction:** The GPU renders pixels, whereas the display controller fetches, processes, composes and scans out those pixels to the display.
