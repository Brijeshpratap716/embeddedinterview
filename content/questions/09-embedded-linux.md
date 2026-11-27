---
slug: embedded-linux
title: Embedded Linux & Boot
icon: 📦
level: Advanced
order: 9
desc: The full boot flow from boot ROM to U-Boot to start_kernel to init, root filesystems, Yocto and Buildroot, cross-compilation, OTA updates and secure boot.
---
Embedded Linux roles care about the whole system: how the board boots, how the image is built, and how it is updated in the field. Interviewers love "walk me through the boot process" because it shows whether you have actually brought up a board. Each answer starts with the short version, then goes into the detail you would add if the interviewer keeps asking.

### Walk through the complete boot process of an embedded Linux system, from power-on to the login prompt. {M}
Embedded Linux boot proceeds from reset through platform firmware, bootloader, Linux kernel and userspace. Exact stages differ between SoCs.

#### 1. Typical boot sequence

<div style="max-width:650px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 365" width="100%" role="img" aria-label="Boot ROM to firmware, U-Boot, kernel, root filesystem, PID 1 and login">
<rect x="13" y="5" width="314" height="44" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="22" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">Boot ROM</text><text x="170" y="37" text-anchor="middle" font-size="10" fill="currentColor">Select boot medium and load initial firmware</text><path d="M170 49 v16 m-4-5 4 5 4-5" stroke="currentColor" fill="none"/><rect x="13" y="65" width="314" height="44" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="82" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">Early firmware / SPL</text><text x="170" y="97" text-anchor="middle" font-size="10" fill="currentColor">Initialize required clocks, RAM and security state</text><path d="M170 109 v16 m-4-5 4 5 4-5" stroke="currentColor" fill="none"/><rect x="13" y="125" width="314" height="44" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="142" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">U-Boot</text><text x="170" y="157" text-anchor="middle" font-size="10" fill="currentColor">Load kernel Image, DTB, optional initramfs</text><path d="M170 169 v16 m-4-5 4 5 4-5" stroke="currentColor" fill="none"/><rect x="13" y="185" width="314" height="44" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="202" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">Linux kernel</text><text x="170" y="217" text-anchor="middle" font-size="10" fill="currentColor">MMU, memory, scheduler, interrupts, drivers</text><path d="M170 229 v16 m-4-5 4 5 4-5" stroke="currentColor" fill="none"/><rect x="13" y="245" width="314" height="44" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="262" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">Root filesystem / PID 1</text><text x="170" y="277" text-anchor="middle" font-size="10" fill="currentColor">Mount filesystems and start init</text><path d="M170 289 v16 m-4-5 4 5 4-5" stroke="currentColor" fill="none"/><rect x="13" y="305" width="314" height="44" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="322" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">Services / login</text><text x="170" y="337" text-anchor="middle" font-size="10" fill="currentColor">getty, authentication, shell or UI</text></svg></div>

#### 2. Example: Arm application SoC

Boot ROM is immutable on-chip code. It reads the boot source and starts platform firmware. Some systems use SPL in SRAM to initialize DRAM, trusted firmware or a system controller before full U-Boot. Others have different firmware arrangements.

U-Boot loads the Linux image and hardware description, supplies boot arguments and enters the kernel using its boot protocol. Linux initializes memory, interrupts, scheduler, driver subsystems and filesystems.

#### 3. Userspace

The kernel executes the first userspace init program. It starts necessary services, mounts additional filesystems, configures networking and launches a login service or application. Android normally uses its own /init.

**Interview takeaway:** Boot is a dependency chain. Identify the last successful stage before debugging; do not assume every SoC uses SPL or the same trusted-firmware order.

### What happens inside U-Boot from reset until it boots the kernel? {M}
U-Boot initializes the hardware necessary to load and start an operating system. Its startup sequence depends on architecture, build configuration and whether SPL or earlier firmware already initialized the platform.

#### 1. Typical full U-Boot flow

```text
Architecture entry (start.S / CRT code)
    -> establish early stack and required CPU state
    -> board_init_f(): early initialization, relocation planning
    -> relocate code/data when required
    -> board_init_r(): full initialization
    -> main_loop(): autoboot or interactive shell
    -> boot command: load and start OS
```

#### 2. What each stage does

Early code sets up a valid execution environment. board_init_f commonly initializes early devices and calculates relocation addresses; DRAM may already be ready from SPL/firmware or be initialized in the configured early path. Relocation moves U-Boot to its runtime memory area when required.

board_init_r completes driver model, environment, storage, networking and other configured subsystems. The autoboot flow selects a boot configuration and executes the relevant boot command.

#### 3. Typical U-Boot shell

```sh
printenv bootcmd
printenv bootargs
mmc list
```

Inspect actual board configuration and environment; do not assume universal load addresses or command availability.

**Interview takeaway:** U-Boot is already executing on a CPU before board_init_f. Early CPU initialization refines the processor state for the next stage; it does not make a previously inactive CPU start running.

### How does U-Boot pass control to the Linux kernel, and what state must the CPU be in? {H}
U-Boot transfers control to Linux after placing the kernel and required boot data in suitable memory and establishing the architecture-defined entry state.

#### 1. Direct ARM64 device-tree boot

A typical command uses booti for an appropriate ARM64 Image:

```sh
booti ${kernel_addr_r} - ${fdt_addr_r}
```

The environment variables must refer to valid loaded objects. The dash indicates no initrd in this example.

#### 2. Required entry contract

For the ordinary arm64 boot protocol, x0 carries the physical DTB address; x1–x3 are reserved and zero. The MMU must be off at kernel entry, with the required cache maintenance, interrupt masking and supported exception-level state. Other requirements apply to system registers, firmware services and secondary CPUs.

The exact requirements should be checked against the target kernel's arm64 booting documentation. UEFI boot and other architectures have different entry protocols.

#### 3. Transfer flow

```text
Load Image / DTB / optional initramfs
Prepare bootargs and memory reservations
Clean or synchronize caches as required
Quiesce platform state according to boot protocol
Branch to kernel entry address
```

Linux then establishes its own translation environment. U-Boot does not remain an ordinary running process underneath Linux.

**Interview takeaway:** Bootloader-to-kernel handoff is an ABI. Correct addresses alone are insufficient; CPU state, cache visibility, DTB and firmware interfaces must also be valid.

### What does the Linux kernel do from head.S to starting the init process? {H}
Linux initializes itself in stages, from architecture-specific early assembly to generic kernel initialization and finally userspace. Function details change between versions.

#### 1. Representative ARM64 flow

```text
arch/arm64/kernel/head.S
    -> early entry, preserve boot arguments
    -> establish translation and execution environment
    -> start_kernel()
       -> architecture setup, memory management
       -> scheduler, IRQ, timer and core initialization
    -> rest_init()
       -> create init and kthreadd execution contexts
    -> kernel_init()
       -> initialization calls and root filesystem setup
       -> execute userspace init
```

#### 2. Important functions

start_kernel is the central generic initialization entry. Architecture-specific setup discovers CPU and memory information and processes the supplied hardware description. The kernel builds its own mappings and initializes the page allocator, scheduler and interrupts.

Initcalls initialize built-in subsystems and drivers at ordered initialization levels. Probing can continue asynchronously or be deferred. The init path prepares root filesystem access and executes an appropriate init program.

#### 3. When does userspace begin?

The initial init task begins in kernel context and becomes a userspace program when the kernel successfully executes init. PID 1 then handles userspace initialization; it is not the function start_kernel.

**Interview takeaway:** Separate early architecture setup, generic kernel initialization, device initialization and userspace startup. Exact symbols and ordering are version-specific.

### What does the init process (PID 1) do, and what special rules apply to it? {M}
PID 1 is the first userspace process in the initial Linux PID namespace. It initializes userspace, manages service lifecycles and has special responsibilities for orphaned processes.

#### 1. Typical tasks

- Mount required virtual and additional filesystems such as /proc and /sys.
- Start services and device-management components.
- Configure networking and start login services or applications.
- Adopt/reap orphaned descendants when required by namespace and subreaper rules.

#### 2. What is special about PID 1?

Its signal behavior differs from ordinary processes, especially for signals without installed handlers. A namespace's init process also has special lifecycle rules. The loss of the initial namespace's PID 1 is fatal to normal system operation.

#### 3. Example

On a systemd-based distribution, PID 1 starts configured units and tracks dependencies. BusyBox init can use a much smaller configuration. Android init parses its own init configuration and starts platform services.

```sh
ps -p 1 -o pid,comm,args
```

This shows which init program is running on a Linux system.

**Interview takeaway:** The kernel initializes the OS core; PID 1 initializes userspace and manages its process hierarchy. The exact service behavior depends on the init implementation.

### How does a Raspberry Pi boot, and how is it different from a typical SoC? {M}
Raspberry Pi boards use a platform-specific firmware boot chain rather than one universal U-Boot/SPL sequence. The exact boot components depend on the Pi generation and configured boot medium.

#### 1. General sequence

```text
On-chip boot ROM
   -> platform boot firmware / EEPROM bootloader where applicable
   -> select and read boot files
   -> configure platform and load kernel / DTB
   -> Linux kernel
   -> root filesystem and init
```

Older models use boot files and firmware arrangements that differ from newer EEPROM-bootloader-based models. Do not assume filenames or execution order are identical across Pi 3, Pi 4 and Pi 5.

#### 2. Difference from conventional embedded SoC

Many Arm SoCs use a chain such as Boot ROM, SPL, trusted firmware and U-Boot. Raspberry Pi firmware can directly load Linux using its own supported configuration. U-Boot can also be included in selected custom boot flows.

#### 3. Debugging

Identify the board revision and bootloader generation. Check the boot medium, platform-specific boot diagnostics, configuration, kernel/DTB compatibility and root filesystem. Use the board's supported UART diagnostic setup.

**Interview takeaway:** Raspberry Pi boot is a useful example of platform-specific firmware. Describe the general chain, then verify model-specific details instead of applying the same SoC boot sequence everywhere.

### What happens when a user logs in on a Linux terminal? {M}
A Linux terminal login establishes an authenticated user session and starts a shell or another configured program.

#### 1. Typical local-console flow

```text
PID 1 starts getty
       -> display login prompt on tty
       -> login / authentication stack
       -> set user and group credentials
       -> establish environment and session
       -> execute user's shell
```

On many distributions, PAM participates in authentication and session setup. Minimal embedded systems may use a different authentication implementation.

#### 2. Why credentials matter

The login process validates credentials, then establishes the user's UID, GID, supplementary groups, home directory and environment according to system policy. The resulting shell executes with the user's permissions, not automatically root privileges.

#### 3. Related commands

```sh
tty
id
ps -o pid,ppid,tty,comm
```

An SSH login uses a network service and a different session setup path, while a graphical login uses a display manager or equivalent.

**Interview takeaway:** A login prompt is userspace functionality. The kernel provides process, terminal and credential mechanisms; userspace authentication and session software apply the login policy.

### What is a bootloader and why does an embedded Linux system need one? {E}
A bootloader is software that prepares a system to start an operating system or another firmware image. It bridges the platform's reset environment and the next image's entry requirements.

#### 1. Responsibilities

Initialize required hardware, select a boot image, load it into accessible memory, validate/authenticate it when configured, supply hardware description and boot parameters, then transfer control.

#### 2. Example

```text
Boot ROM -> early firmware -> U-Boot -> Linux
```

U-Boot may load Image and DTB from eMMC, SD, SPI flash or network storage. Its command/environment and recovery mechanisms simplify development and maintenance.

#### 3. Does every board need U-Boot?

No. A firmware component, UEFI or a custom loader can perform the required handoff. Some small MCU applications execute directly after reset and do not need a separate application bootloader.

#### 4. Recovery and updates

A bootloader can select an alternate image, enter recovery, enforce secure boot or manage A/B slot metadata. These features depend on the configured design.

**Interview takeaway:** A bootloader is not the OS. It establishes the next image's required environment and starts it; the implementation may be split across several firmware stages.

### What are the common U-Boot commands? {E}
U-Boot offers commands for inspecting the platform, manipulating its environment, loading images and starting an operating system. Available commands depend on build configuration.

| Command | Purpose |
|---|---|
| printenv / setenv | Inspect/change environment variables |
| saveenv | Persist environment when supported |
| mmc list / mmc dev | Inspect/select MMC devices |
| fatload / ext4load | Load a file from supported filesystems |
| tftpboot | Load using TFTP when network is configured |
| md / mw | Display/write memory (carefully) |
| booti / bootm / bootz | Boot supported image formats |
| reset | Reset platform |

#### 1. Illustrative ARM64 boot commands

```sh
fatload mmc 0:1 ${kernel_addr_r} Image
fatload mmc 0:1 ${fdt_addr_r} board.dtb
booti ${kernel_addr_r} - ${fdt_addr_r}
```

The partition, filenames and addresses must match the actual board. Ensure loaded objects do not overlap.

#### 2. Debugging autoboot

Inspect bootcmd and bootargs and interrupt autoboot using the platform's configured console mechanism. Avoid persisting experimental environment changes until the boot flow is validated.

**Interview takeaway:** U-Boot commands manipulate real hardware and memory. Understand address ranges and image formats before issuing memory writes or persistent environment operations.

### What are kernel command line (bootargs) parameters? {E}
Kernel command-line parameters supply configuration options to Linux at boot. U-Boot commonly stores the command line in bootargs and passes it through the configured boot mechanism, such as the device tree's chosen node.

#### 1. Example

```text
console=ttyS0,115200 root=/dev/mmcblk0p2 rootwait rw
```

| Parameter | Purpose |
|---|---|
| console= | Select kernel console device/settings |
| root= | Specify root filesystem device or identifier |
| rootwait | Wait for the root device to appear |
| ro / rw | Initial root mount mode |
| earlycon | Enable supported early console output |
| init= | Override normal init program selection |

Actual device names and console settings are platform-specific. Stable identifiers such as PARTUUID may be preferable to enumeration-dependent names.

#### 2. Inspect running kernel

```sh
cat /proc/cmdline
```

This reports the command line the kernel received. Built-in kernel parameters, module parameters and userspace-consumed options have distinct handling.

**Interview takeaway:** bootargs configures the kernel at boot; it is not the same as U-Boot bootcmd, which determines the bootloader commands that run.

### What is an initramfs and when is it needed? {M}
An initramfs is an initial root filesystem unpacked into RAM during Linux boot. It provides early userspace before the final root filesystem is available.

#### 1. Boot sequence

```text
Kernel starts
    -> unpack built-in/external initramfs archive
    -> execute /init if present
    -> discover storage / unlock or assemble volumes
    -> mount final root filesystem
    -> switch_root and execute final init
```

An initramfs commonly uses a compressed cpio archive. It may be built into the kernel or loaded separately by the bootloader.

#### 2. When needed

Use it when root storage requires early modules, encryption unlock, RAID assembly, network setup or recovery logic. Some embedded systems keep their entire root filesystem in RAM. A kernel with all necessary root drivers built in can often mount its final root directly.

#### 3. Minimal content

A functional early userspace may contain /init, BusyBox or other required binaries, libraries if dynamically linked, and access to appropriate device nodes and virtual filesystems.

#### 4. initramfs vs initrd

Traditional initrd is an initial RAM disk image with a filesystem; initramfs is an archive unpacked into the kernel's initial rootfs. The terms are sometimes used loosely.

**Interview takeaway:** Initramfs solves early userspace dependencies before the final root is available. It is not mandatory for every embedded Linux system.

### What is the difference between Buildroot and Yocto? {M}
Buildroot and the Yocto Project are tools for building customized embedded Linux systems, but they organize the build and distribution lifecycle differently.

| Buildroot | Yocto / OpenEmbedded |
|---|---|
| Simple integrated image-building workflow | Highly configurable distribution-building framework |
| Kconfig-style package selection | BitBake recipes, layers and configuration |
| Commonly rebuilds complete images | Supports granular metadata and package-oriented workflows |
| Lower initial complexity | More flexible for multi-product customization |

#### 1. Buildroot example

```sh
make menuconfig
make
```

Select target architecture, toolchain, kernel, packages and image format. Buildroot can generate a cross-toolchain, rootfs and other configured artifacts.

#### 2. Yocto example

```sh
source oe-init-build-env
bitbake core-image-minimal
```

This assumes a configured OpenEmbedded/Yocto environment. The image recipe and layers determine the resulting distribution.

#### 3. Selection

Buildroot is attractive for a small appliance or straightforward image. Yocto is useful for maintaining multiple products, reusable BSP layers, custom distributions and detailed package/license metadata. Both require security maintenance and reproducible build practices.

**Interview takeaway:** Buildroot is an integrated build system; Yocto is a distribution construction ecosystem. Choose based on product lifecycle and customization, not simply image size.

### What are Yocto layers, recipes and bbappend files? {M}
Yocto/OpenEmbedded uses BitBake metadata to describe how software is fetched, configured, built, installed and packaged.

#### 1. Main concepts

| Item | Role |
|---|---|
| Layer | Organized collection of metadata |
| .bb recipe | Describes a software build and packages |
| .bbappend | Extends or modifies a matching recipe |
| Machine configuration | Board/architecture-specific configuration |
| Distro configuration | Distribution policy and features |

#### 2. Recipe example

```bitbake
SUMMARY = "Demo program"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://LICENSE;md5=<actual-checksum>"
SRC_URI = "file://demo.c file://LICENSE"

do_compile() {
    ${CC} ${CFLAGS} ${LDFLAGS} ${WORKDIR}/demo.c -o demo
}

do_install() {
    install -d ${D}${bindir}
    install -m 0755 demo ${D}${bindir}/demo
}
```

This is illustrative; source unpack locations and build-directory conventions vary with Yocto release, so adapt to the target metadata version and use the real license checksum.

#### 3. Extend a recipe

A layer can provide a matching .bbappend to add a patch, change configuration or extend installation without editing the upstream recipe. Layer priority and matching version patterns affect selection.

**Interview takeaway:** Recipes describe software builds, layers organize reusable metadata, and bbappend files customize recipes. Verify the effective configuration with BitBake tools.

### What is cross-compilation and what is a toolchain? {E}
Cross-compilation builds software on one architecture (host) for execution on another (target). A toolchain contains a compiler, assembler, linker, supporting tools and often target headers/libraries.

#### 1. Example

Build an ARM64 Linux executable on an x86-64 workstation:

```sh
aarch64-linux-gnu-gcc hello.c -o hello
file hello
```

The output should identify an AArch64 executable. It cannot execute natively on an ordinary x86-64 CPU without emulation.

#### 2. Target ABI

```text
Source --> host-running cross compiler --> target ELF
                                          |
                               target OS / CPU / ABI
```

The target architecture, ABI, floating-point conventions, C library and sysroot must match the deployed system. Bare-metal arm-none-eabi and Linux arm-linux-gnueabihf toolchains target different environments.

#### 3. Kernel build example

```sh
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- Image
```

Use the appropriate kernel configuration and prepared source tree. LLVM-based builds may use different flags.

**Interview takeaway:** The compiler runs on the host but emits target instructions and ABI-compatible objects. A correct CPU architecture alone does not guarantee library or OS compatibility.

### What is the difference between glibc, musl and uClibc-ng? {M}
glibc, musl and uClibc-ng are C library implementations used in Linux systems. They provide standard C APIs and operating-system interfaces, with different design and compatibility characteristics.

| Library | Common characteristics |
|---|---|
| glibc | Broad GNU/Linux compatibility and extensive functionality |
| musl | Compact implementation, simple design and static-linking suitability |
| uClibc-ng | Configurable lightweight library for embedded targets |

#### 1. Why the choice matters

Dynamically linked programs need the matching runtime loader and libraries. An executable built against glibc cannot generally be moved unchanged to a musl-based rootfs merely because both use the same CPU architecture.

```sh
readelf -l app
readelf -d app
```

Inspect the interpreter and shared-library dependencies.

#### 2. Selection

Consider application compatibility, target architecture, memory footprint, locale/threading requirements, security support and licensing obligations. Static linking can simplify deployment but has its own size, update and licensing considerations.

**Interview takeaway:** A C library is part of the userspace ABI. Select it with the toolchain and root filesystem, not independently of the application ecosystem.

### Which filesystems are used on embedded flash? {M}
Embedded storage filesystems depend on whether the device exposes raw flash or a managed block interface.

| Storage | Suitable examples |
|---|---|
| Raw NAND/NOR flash via MTD | UBIFS on UBI, JFFS2 where appropriate |
| Managed eMMC, SD, SSD | ext4, F2FS, other block filesystems |
| Read-only compressed image | SquashFS |
| RAM-backed storage | tmpfs |

#### 1. Raw versus managed flash

Raw NAND has erase blocks, bad blocks and endurance constraints. UBI manages eraseblock mapping and wear-related concerns; UBIFS operates on UBI volumes. Managed block devices generally hide physical flash management behind their controller.

#### 2. Embedded design example

Use a read-only SquashFS system image for predictable deployment and a separate writable partition for persistent configuration. An overlay filesystem can combine layers if the system design requires it.

#### 3. Power-loss concerns

Select the filesystem and update strategy according to consistency requirements. Journaling and atomic update protocols help, but do not guarantee every recent write survives unexpected power loss. Use appropriate fsync and storage flush semantics.

**Interview takeaway:** Do not place a normal block filesystem directly on arbitrary raw NAND. Choose according to the storage abstraction, endurance, power-loss behavior and update strategy.

### How do A/B (dual-copy) OTA updates work? {M}
A/B OTA (over-the-air) updates keep two bootable system slots so a new image can be installed without overwriting the currently working system.

#### 1. Update flow

```text
Running slot A
   -> download and authenticate update
   -> write inactive slot B
   -> verify B
   -> mark B as trial boot
   -> reboot into B
   -> health checks pass: mark B successful
   -> failure / exhausted attempts: roll back to A
```

The bootloader and update system cooperate through durable slot metadata and retry counters.

#### 2. Why safer?

A power loss while writing the inactive slot need not destroy the active image. Rollback provides recovery if the new system cannot boot or pass health checks.

#### 3. Important details

Authenticate update manifests and payloads, validate compatibility, atomically update boot metadata, and account for shared persistent data schema migrations. Anti-rollback security policies must be coordinated with legitimate recovery behavior.

#### 4. Health check

Do not mark the new slot successful merely because the kernel started. Verify the services and device functions required by the product.

**Interview takeaway:** A/B updates reduce downtime and failed-update risk, but only if slot selection, power-loss handling, verification and rollback are designed together.

### What is secure boot and a chain of trust? {H}
Secure boot verifies the authenticity and integrity of executable boot components before trusting them. A chain of trust starts from a trusted root and extends verification to later stages.

#### 1. Typical chain

```text
Immutable ROM / hardware root of trust
        verifies
First-stage firmware
        verifies
Bootloader
        verifies
Kernel, DTB, initramfs or signed boot bundle
        verifies / enforces
Protected root filesystem and other components
```

The actual verified objects and trust boundaries depend on the platform.

#### 2. Digital signature versus hash

A hash detects changes when compared with a trusted expected value. A digital signature authenticates data using a trusted public key and a corresponding private signing key. The device must protect the root key or key hash and enforce verification failures.

#### 3. Anti-rollback

A correctly signed but vulnerable older image may still be dangerous. A version policy using protected counters or equivalent mechanisms can prevent unauthorized rollback.

#### 4. Secure boot versus measured boot

Secure boot enforces a verification policy. Measured boot records measurements for later assessment; it does not necessarily block execution. Encryption protects confidentiality and is separate from signature verification.

**Interview takeaway:** Secure boot is an enforced trust chain, not simply checking a checksum. Cover the complete boot path, key management, recovery and update policy.

### What is the difference between systemd, SysVinit and BusyBox init? {E}
**Short answer:** All three are implementations of PID 1, the first user-space process that starts and supervises the rest of the system. **BusyBox init** is tiny and reads a simple `/etc/inittab`. **SysVinit** runs ordered shell scripts per runlevel. **systemd** starts services in parallel from a dependency graph and also supervises, logs and manages them, at the cost of size and complexity.

| | BusyBox init | SysVinit | systemd |
|---|---|---|---|
| Config | `/etc/inittab` + `rcS` script | `/etc/inittab`, `/etc/init.d/*`, runlevel links | unit files (`.service`, `.socket`, `.timer`, `.mount`) |
| Start order | sequential script | sequential, numbered scripts | parallel, based on dependencies (`After=`, `Requires=`) |
| Service supervision | `respawn` entries only | none built in | restart policies, cgroups track every process |
| Logging | syslogd (BusyBox) | syslog | journald |
| Extra features | – | – | watchdog support, socket activation, timers, device and mount management, resource limits |
| Size | tens of KB | small | several MB plus dependencies |
| Typical use | small Buildroot images | legacy systems | Yocto/Debian-based products, larger devices |

**A systemd service for a product application**

```ini
[Unit]
Description=Sensor daemon
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/usr/bin/sensord
Restart=on-failure
WatchdogSec=10s

[Install]
WantedBy=multi-user.target
```

`WatchdogSec` means the app must call `sd_notify("WATCHDOG=1")` regularly or systemd restarts it; systemd itself can pet the hardware watchdog (`RuntimeWatchdogSec=` in `system.conf`).

**How to choose:** BusyBox init when flash is tiny and the system only runs a few processes; systemd when you need robust supervision, dependency handling, timers and watchdog integration, and you can afford a few MB. Mention boot time: systemd's parallel start helps, and `systemd-analyze blame` shows what is slow.

### How do you reduce boot time on an embedded Linux device? {M}
**Short answer:** Measure first, then remove or defer work at every stage: shorten the bootloader (no countdown, minimal init, or Falcon mode), make the kernel smaller and quieter (only needed drivers built in, `quiet`, fast decompression, deferred probing), and start the critical application early in user space (fewer services, read-only compressed root, no unnecessary waits).

**Measure**

- Timestamp the serial output: `grabserial -t` or the terminal's timestamp option.
- Kernel: `printk.time=1`, `initcall_debug` (shows how long each driver init takes), `bootgraph.pl`.
- User space: `systemd-analyze`, `systemd-analyze blame`, `systemd-analyze critical-chain`, bootchart.

**Bootloader**

- `bootdelay=0` (or -2) to remove the autoboot countdown.
- Remove unused drivers and commands; skip USB/network init unless needed.
- Load only what is needed, from the fastest storage; use DMA and the highest eMMC bus speed.
- **Falcon mode**: SPL loads the kernel directly, skipping U-Boot proper.

**Kernel**

- Build in only the drivers needed for the boot path; make the rest modules loaded later, or remove them.
- `quiet` (printing to a 115200-baud UART can cost seconds).
- Use **LZ4** or an uncompressed image if storage is fast (decompression is CPU time).
- `CONFIG_PRINTK_TIME` for measurement, then disable debugging options.
- Async probe and deferred initcalls for slow, non-critical devices.
- Use `rootwait` only where needed and avoid unnecessary delays such as `rootdelay=`.

**User space**

- Start the critical application first (a dedicated early systemd unit, or directly from init).
- Remove unused services; avoid network-wait targets unless needed.
- Use a **read-only SquashFS/EROFS** root (no filesystem check), prelink or statically link the main application, reduce shared library count.
- Show a splash screen or "early camera" output from the bootloader or kernel to improve perceived boot time (automotive rear-view cameras must show within about 2 seconds).

**Results:** with this approach, 1–3 seconds to the application is achievable on modern Cortex-A SoCs. Hibernation-based "snapshot boot" can be faster still for complex systems.

### How do you access GPIO from Linux user space? {M}
**Short answer:** Use the **GPIO character device** (`/dev/gpiochipN`) through **libgpiod** and its command-line tools (`gpiodetect`, `gpioinfo`, `gpioget`, `gpioset`, `gpiomon`). The old sysfs interface (`/sys/class/gpio`) is deprecated. For production, describe fixed-function pins in the device tree and let a kernel driver own them.

**Command-line examples (libgpiod v2 syntax)**

```bash
gpiodetect                         # list GPIO chips
gpioinfo gpiochip0                 # line names, direction, consumers
gpioget -c gpiochip0 17            # read line 17
gpioset -c gpiochip0 18=1          # drive line 18 high (holds it while running)
gpiomon -c gpiochip0 -e rising 23  # wait for rising edges
```

**C with libgpiod v2 (sketch)**

```c
#include <gpiod.h>

struct gpiod_chip *chip = gpiod_chip_open("/dev/gpiochip0");
struct gpiod_line_settings *s = gpiod_line_settings_new();
gpiod_line_settings_set_direction(s, GPIOD_LINE_DIRECTION_OUTPUT);
struct gpiod_line_config *lc = gpiod_line_config_new();
unsigned int offset = 18;
gpiod_line_config_add_line_settings(lc, &offset, 1, s);
struct gpiod_line_request *req = gpiod_chip_request_lines(chip, NULL, lc);
gpiod_line_request_set_value(req, 18, GPIOD_LINE_VALUE_ACTIVE);
```

**Why sysfs was deprecated**

- Global GPIO numbers that change between kernel versions and boards.
- No ownership: any process could change any pin, and an exported pin stayed configured after the program crashed.
- Edge events through `poll()` on a value file were awkward and could lose events.
- The character device gives named lines, per-process ownership (released automatically when the process exits), timestamps on events, bias (pull-up/down) and debounce settings.

**Production advice**

- LEDs: `gpio-leds` driver → `/sys/class/leds/...` (with triggers like heartbeat).
- Buttons: `gpio-keys` → a standard input device (`/dev/input/eventN`).
- Resets and enables for chips: let the chip's kernel driver request them via `reset-gpios`/`enable-gpios` in the device tree.
- Use user-space GPIO for prototyping, test equipment and truly application-specific signals.

**Timing limits:** user-space GPIO toggling has jitter (scheduling, syscalls). For precise waveforms use PWM, SPI or a timer peripheral, a kernel driver, or a coprocessor (e.g. the Cortex-M core on an i.MX8M or STM32MP1).

### What is the difference between a kernel driver and a user-space driver (UIO, spidev)? {M}
**Short answer:** A kernel driver runs in kernel space, handles interrupts directly and plugs into a subsystem (network, input, IIO, DRM), so any application can use the device through a standard interface. A user-space driver talks to the hardware through a generic kernel helper (`spidev`, `i2c-dev`, `UIO`, `VFIO`, libgpiod); it is faster to write and debug and can stay proprietary, but it has higher latency, cannot be used by other kernel subsystems, and is harder to make safe.

| | Kernel driver | User-space driver |
|---|---|---|
| Interrupt latency | microseconds, top half runs immediately | scheduling latency of a process (tens of µs to ms) |
| Crash impact | can panic the whole system | only the process dies |
| Debugging | printk, ftrace, kgdb; reboot on mistakes | gdb, valgrind, normal tools |
| Integration | standard interfaces (`/dev/input`, `net`, `iio`, `v4l2`), used by any app and by other drivers | custom API for your application |
| License | must be GPL-compatible to use GPL-only kernel symbols | can be proprietary |
| Maintenance | must track kernel API changes (unless upstreamed) | stable user-space ABI |

**Generic helpers for user-space drivers**

- **spidev** (`/dev/spidevB.C`): full-duplex SPI transfers with `ioctl(SPI_IOC_MESSAGE)`.
- **i2c-dev** (`/dev/i2c-N`): `ioctl(I2C_SLAVE, addr)` then `read`/`write`, or `I2C_RDWR` for combined transactions.
- **UIO** (`/dev/uioN`): `mmap()` the device registers; a blocking `read()` returns when an interrupt arrives (the small kernel part only acknowledges/masks it).
- **VFIO**: like UIO but with IOMMU protection so a user-space driver can do DMA safely (used by DPDK and for PCIe devices).

**When to use which**

- Prototype or bring-up: user space (quick to iterate).
- A sensor read once a second by one application: `i2c-dev`/`spidev` is fine.
- Anything other applications or subsystems need (network interface, input device, display, audio), anything with tight interrupt timing, or DMA without an IOMMU: write a kernel driver, and consider upstreaming it.

**Follow-up:** "spidev in the device tree?" Bind a specific compatible that the spidev driver lists (or use `driver_override`); a plain `compatible = "spidev"` is rejected because the device tree should describe hardware, not which driver to use.

### How do you debug an embedded Linux board that does not boot? {M}
**Short answer:** Identify the last successful boot stage before debugging. Check power, reset, boot straps, serial logs, memory initialization, image loading and root filesystem in that order as appropriate.

```text
Power/reset -> Boot ROM -> SPL / firmware -> U-Boot
                                           |
                                           v
Userspace <- rootfs <- Linux kernel <- image + DTB
```

| Last visible stage | First checks |
|---|---|
| No ROM/early output | Rails, reset, clocks, boot mode, debug interface |
| SPL starts | DRAM training and clock configuration |
| U-Boot starts | Image format, load addresses, DTB, boot arguments |
| Kernel starts | earlycon, console, device tree, root device |
| VFS panic | root=, filesystem support, initramfs |
| PID 1 starts | init executable, mounts, dependencies |

**Example:** A VFS unable-to-mount-root panic suggests checking storage driver availability, root device identification and filesystem configuration rather than debugging SPL.

**Interview takeaway:** Locate the failing handoff using evidence from UART, JTAG and logs; boot stages vary by SoC.
