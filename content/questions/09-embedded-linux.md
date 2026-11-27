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
**Short answer:** init starts `getty` on each terminal; `getty` opens the TTY, prints the login prompt and reads the user name, then `exec`s `login`. `login` checks the password (via PAM against `/etc/shadow`), sets up the session, changes to the user's UID/GID with `setgid()`/`setuid()`, and `exec`s the user's shell from `/etc/passwd`. Over SSH, `sshd` does the same job instead of getty/login.

**Step by step on a serial console**

1. **init** starts `getty` (`agetty`, or BusyBox `getty`) for `ttyS0`/`ttyAMA0`, as configured in `/etc/inittab` or a systemd `serial-getty@.service`.
2. **getty** opens the terminal device, sets the baud rate and line settings (`termios`), makes it the controlling terminal of a new session (`setsid()`), prints `/etc/issue` and `login:`, reads the name.
3. getty `exec`s **`login username`** (the same process, PID unchanged).
4. **login** reads the password with echo disabled, verifies it through **PAM** (which hashes the input and compares with `/etc/shadow`), checks account expiry and `/etc/nologin`.
5. login records the session (`utmp`/`wtmp`, `lastlog`), sets the TTY owner to the user, then **drops privileges**: `initgroups()`, `setgid()`, `setuid()`. This order matters: after `setuid()` to a normal user it can no longer change groups.
6. It sets `HOME`, `SHELL`, `USER`, `PATH`, changes to the home directory and `exec`s the **shell** with a leading `-` in `argv[0]` (e.g. `-bash`), which tells the shell it is a login shell and should read `/etc/profile` and `~/.profile`.

**Where the kernel is involved**

- The **TTY layer** and line discipline handle echo, line editing (canonical mode), and turning Ctrl-C into `SIGINT` for the foreground process group.
- `setuid()`/`setgid()` are system calls; the kernel checks that only a privileged process (root, or with `CAP_SETUID`) may change to an arbitrary UID.
- Sessions and process groups (`setsid`, `tcsetpgrp`) let the shell do job control.
- When you log out, the shell exits, init sees its child died and starts a fresh `getty`.

**Embedded note:** many products disable login on the serial console in production, or use `autologin` during development. Leaving a root shell on the debug UART of a shipped device is a classic security finding.

### What is a bootloader and why does an embedded Linux system need one? {E}
**Short answer:** A bootloader is the program that runs before the operating system. It initialises the minimum hardware the kernel needs (clocks, DRAM, storage, console), loads the kernel, device tree and optional initramfs into RAM, prepares the boot arguments and jumps to the kernel. The kernel cannot do this itself because, at power-on, nothing (not even DRAM) is ready to hold it.

**What only the bootloader can do**

- **DRAM bring-up:** the memory controller needs board-specific timings and training before DRAM is usable.
- **Find and load the kernel** from eMMC, SD, NAND, SPI NOR, USB or the network.
- **Hand over information:** the device tree, `bootargs`, the initramfs address.
- **Choose what to boot:** A/B slot selection, recovery mode, factory mode.
- **Verify signatures** as part of secure boot.
- **Recovery and production:** flash an image over USB/TFTP, read hardware IDs, run memory tests.

**Multi-stage boot is normal.** The on-chip **boot ROM** loads a small first stage (**U-Boot SPL**, a vendor FSBL, or TF-A BL2) into internal SRAM. That stage initialises DRAM and loads the full bootloader. On ARM64 the chain often includes **TF-A** (BL31, the EL3 secure monitor) and optionally **OP-TEE**.

**Common bootloaders**

| Bootloader | Where |
|---|---|
| **U-Boot** | most ARM/RISC-V embedded boards |
| barebox | an alternative with a cleaner driver model, used by some industrial vendors |
| GRUB / systemd-boot | x86 and ARM servers with UEFI |
| UEFI (EDK II) | ARM servers, some high-end SoCs |
| Vendor (e.g. Qualcomm XBL/ABL, Android bootloaders) | phones and some SoCs |

**Follow-up: "Can you boot Linux without U-Boot?"** Yes: Falcon mode (SPL loads the kernel directly), EFI stub (UEFI loads the kernel as an EFI application), or the Raspberry Pi firmware loading the kernel itself. You lose U-Boot's flexibility (interactive recovery, network loading), but boot is faster.

### What are the common U-Boot commands? {E}
**Short answer:** Environment commands (`printenv`, `setenv`, `saveenv`), loading commands (`load`/`fatload`/`ext4load`, `tftp`, `mmc`, `sf`), boot commands (`bootm`, `bootz`, `booti`, `run bootcmd`), and hardware debug commands (`md`, `mw`, `i2c`, `gpio`).

**Environment**

```
=> printenv bootcmd
=> setenv bootargs console=ttyS0,115200 root=/dev/mmcblk0p2 rootwait
=> saveenv                     # write the environment to its storage
=> run bootcmd                 # execute the variable as a script
=> env default -a              # restore defaults
```

**Storage and loading**

```
=> mmc list                    # list MMC/SD controllers
=> mmc dev 0                   # select device
=> mmc part                    # show partitions
=> ls mmc 0:1                  # list files on partition 1
=> load mmc 0:1 ${kernel_addr_r} Image
=> sf probe; sf read ${loadaddr} 0x100000 0x400000   # SPI NOR flash
```

**Network (fast development loop)**

```
=> setenv serverip 192.168.1.10; setenv ipaddr 192.168.1.50
=> tftp ${kernel_addr_r} Image
=> tftp ${fdt_addr_r} board.dtb
=> booti ${kernel_addr_r} - ${fdt_addr_r}
```

Loading over TFTP and using an NFS root filesystem means you can rebuild and test without re-flashing the board.

**Booting**

- `booti` – ARM64 `Image`.
- `bootz` – ARM32 `zImage`.
- `bootm` – uImage or **FIT** (can verify signatures).
- `bootefi` – boot an EFI application (GRUB or the kernel's EFI stub).

**Hardware debugging**

- `md.l 0x40000000 10` – dump 16 words of memory (or a peripheral register).
- `mw.l 0x40000000 0xdeadbeef` – write memory.
- `i2c dev 0; i2c probe; i2c md 0x50 0 16` – scan the bus and read an EEPROM.
- `gpio status; gpio set 42` – check and drive pins.
- `mtest` – simple DRAM test. `bdinfo`, `coninfo`, `version` – board information.

**Follow-up:** "How do you stop autoboot?" Press a key during `bootdelay` (set `bootdelay=-2` to disable the prompt entirely in production, and consider disabling the console or protecting it with a password, since an open U-Boot prompt can boot anything).

### What are kernel command line (bootargs) parameters? {E}
**Short answer:** The kernel command line is a string of parameters passed by the bootloader (or stored in the device tree's `/chosen/bootargs`, or built into the kernel) that configures the kernel at boot: which console to use, where the root filesystem is, log level, and settings for built-in drivers. The running values are in `/proc/cmdline`.

```
console=ttymxc0,115200 earlycon root=/dev/mmcblk0p2 rootfstype=ext4 rootwait ro quiet loglevel=4 panic=5
```

**Common parameters**

| Parameter | Meaning |
|---|---|
| `console=ttyS0,115200` | kernel console device and baud rate (can be given more than once) |
| `earlycon` | very early console from the DT `stdout-path`, before the UART driver probes |
| `root=/dev/mmcblk0p2` | root filesystem device (also `PARTUUID=...`, `/dev/nfs`, `ubi0:rootfs`) |
| `rootfstype=ext4` | skip filesystem probing |
| `rootwait` | wait until the root device appears (needed for slow eMMC/SD/USB) |
| `ro` / `rw` | mount root read-only or read-write |
| `init=/bin/sh` | run a different first program (recovery trick) |
| `quiet`, `loglevel=N` | reduce console output (printing to a slow UART can add seconds to boot) |
| `panic=5` | reboot 5 s after a kernel panic |
| `mem=512M` | limit usable memory |
| `module.param=value` | parameter for a built-in driver, e.g. `usbcore.autosuspend=-1` |
| `nfsroot=`, `ip=dhcp` | network root filesystem for development |

**Where it comes from (priority depends on kernel config):** U-Boot's `bootargs` variable, which U-Boot writes into the DTB's `/chosen` node; the DTB itself; or `CONFIG_CMDLINE` built into the kernel (can be set to append, extend or force).

**How the kernel parses it:** parameters registered with `__setup()` or `early_param()`, and `module_param()` for built-in modules. Anything the kernel does not recognise is passed to init as arguments or environment variables.

**Security note:** if users can change `bootargs` (open U-Boot console), they can add `init=/bin/sh` and get a root shell. Locking the environment is part of hardening.

### What is an initramfs and when is it needed? {M}
**Short answer:** An initramfs is a small root filesystem packed as a cpio archive, which the kernel unpacks into a RAM-based filesystem (tmpfs/ramfs) and runs `/init` from before the real root filesystem is mounted. It is needed when mounting the real root needs work that the kernel alone cannot do: loading storage drivers built as modules, decrypting, assembling RAID/LVM, picking an A/B slot, or checking integrity.

**How it works**

1. The bootloader loads the initramfs into RAM and passes its address (or it is built into the kernel image with `CONFIG_INITRAMFS_SOURCE`).
2. The kernel unpacks it into `rootfs` (a tmpfs) early in boot.
3. If `/init` exists, the kernel runs it as PID 1.
4. `/init` does the setup, mounts the real root at e.g. `/new_root`, then calls `switch_root` (which deletes the initramfs contents to free RAM and `exec`s the real `/sbin/init`).

**Typical reasons to use one**

- Root is on a device whose driver is a module (common on generic distro kernels).
- **Encrypted root** (LUKS/dm-crypt): unlock with a key from a TPM, OP-TEE or the user.
- **dm-verity** for a verified read-only root.
- **A/B slot selection**, factory reset, or a recovery shell.
- Root over the network, iSCSI, or an overlay of a read-only image plus a writable partition.

**initramfs vs the older initrd**

| initrd (old) | initramfs |
|---|---|
| a block-device image (ext2) in a RAM disk | a cpio archive unpacked into tmpfs |
| needs a filesystem driver and a fixed-size RAM disk | no block layer, grows as needed |
| uses `pivot_root` | uses `switch_root` |

**Embedded uses:** some small products run **entirely from an initramfs** (the whole system in RAM, nothing writable on flash to get corrupted). Recovery/update images are often a kernel plus initramfs.

**Cost:** extra boot time to load and unpack it, and RAM usage. If you do not need it, booting straight to a root partition is faster.

### What is the difference between Buildroot and Yocto? {M}
**Short answer:** Both build a complete embedded Linux image (toolchain, bootloader, kernel, root filesystem) from source. **Buildroot** is simple Makefiles plus Kconfig and produces one firmware image; it is quick to learn and build. **Yocto** (OpenEmbedded with BitBake) builds a full distribution from layered recipes with package management; it is harder to learn but scales to many products and long maintenance, and SoC vendors ship their BSPs as Yocto layers.

| | Buildroot | Yocto Project / OpenEmbedded |
|---|---|---|
| Model | Makefiles + Kconfig (`make menuconfig`) | BitBake recipes in layers |
| Output | one root filesystem image | packages (ipk/deb/rpm) + images + SDK |
| Learning curve | gentle (hours) | steep (weeks) |
| Full build time | short (often < 1 hour) | long (hours), but shared-state cache reuses results |
| Incremental changes | often needs a clean rebuild of affected packages | precise task-level rebuilds |
| Package management on target | no | yes, optional package feeds |
| Customisation | defconfig, rootfs overlay, post-build scripts, `BR2_EXTERNAL` | layers, `.bbappend`, machine/distro/image configs |
| License compliance | `make legal-info` | built-in license manifests, SPDX/SBOM output |
| Typical use | single, fixed-function product; small team | product families, vendor BSPs, long-term maintained products |

**How to answer "which would you choose?"**

- Small team, one board, a fixed image, fast iteration: **Buildroot**.
- Several boards or product variants, a vendor BSP only in Yocto (meta-imx, meta-ti, meta-st-stm32mp, meta-qcom), need for SDKs, SBOMs, package updates, or 10-year maintenance: **Yocto**.

**Related tools:** Debian-based images (`debos`, `isar`, `mkosi`) when you want a full Debian userland; and Android/AOSP for Android devices.

**Interview follow-up:** "How do you add your own application?" Buildroot: a package directory with `Config.in` and `*.mk`, ideally in a `BR2_EXTERNAL` tree. Yocto: a recipe in your own layer, added to the image with `IMAGE_INSTALL:append = " myapp"`.

### What are Yocto layers, recipes and bbappend files? {M}
**Short answer:** A **recipe** (`.bb`) tells BitBake how to build one piece of software. A **layer** (`meta-*`) groups recipes and configuration so that the vendor BSP, the distribution policy and your product stay separate. A **`.bbappend`** modifies a recipe from another layer without editing it.

**Recipe:** describes the source, license and build steps through BitBake tasks.

```bitbake
SUMMARY = "Sensor daemon"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://LICENSE;md5=..."
SRC_URI = "git://github.com/acme/sensord.git;branch=main;protocol=https"
SRCREV = "1a2b3c..."
S = "${WORKDIR}/git"
inherit cmake systemd
SYSTEMD_SERVICE:${PN} = "sensord.service"
```

Tasks run in order: `do_fetch` → `do_unpack` → `do_patch` → `do_configure` → `do_compile` → `do_install` → `do_package`, and the image tasks assemble the root filesystem. Classes such as `cmake`, `autotools`, `meson`, `systemd` supply the standard steps.

**Layer:** a directory with `conf/layer.conf`, listed in `build/conf/bblayers.conf`. Each layer has a **priority** that decides which version of a recipe or file wins. A typical stack:

```
poky/meta              core recipes (openembedded-core)
meta-openembedded/...  extra recipes
meta-vendor-bsp        SoC/board support (kernel, U-Boot, firmware)
meta-mycompany         your distro, images, applications, bbappends
```

**`.bbappend`:** for example `linux-imx_%.bbappend` in your layer adds a patch and a kernel config fragment to the vendor's kernel recipe:

```bitbake
FILESEXTRAPATHS:prepend := "${THISDIR}/files:"
SRC_URI += "file://0001-add-my-panel.patch file://panel.cfg"
```

This keeps your changes out of the vendor layer, so you can upgrade it later.

**Configuration levels**

- **MACHINE** (`conf/machine/myboard.conf`): CPU tune, kernel and bootloader providers, DTB names, serial console.
- **DISTRO** (`conf/distro/mydistro.conf`): policy: init system, C library, `DISTRO_FEATURES` (wifi, bluetooth, systemd).
- **Image recipe** (`my-image.bb`): what goes into the root filesystem (`IMAGE_INSTALL`).
- `local.conf`: per-build settings (machine choice, download and sstate directories). Do not put product settings only here; they are not version controlled with the layers.

**Useful commands:** `bitbake -c devshell virtual/kernel`, `bitbake -e recipe | grep ^SRC_URI`, `devtool modify`, `bitbake-layers show-appends`.

### What is cross-compilation and what is a toolchain? {E}
**Short answer:** Cross-compiling means building on one machine (the **host**, e.g. an x86-64 PC) a program that runs on a different architecture (the **target**, e.g. an ARM64 board). A **toolchain** is the set of tools and libraries that make this possible: cross compiler, assembler, linker, binutils, the C library and kernel headers for the target.

**Why cross-compile:** the target is often too slow, has too little RAM/storage, or has no compiler at all. Building a kernel on a quad-core Cortex-A53 takes hours; on a PC it takes minutes.

**Toolchain triplets** (the prefix tells you the target)

| Prefix | Target |
|---|---|
| `aarch64-linux-gnu-` | 64-bit Arm, Linux, glibc |
| `arm-linux-gnueabihf-` | 32-bit Arm, Linux, hard-float ABI |
| `arm-none-eabi-` | bare-metal Arm (Cortex-M), no OS, newlib |
| `riscv64-linux-gnu-` | 64-bit RISC-V, Linux |
| `x86_64-linux-gnu-` | native PC |

```bash
aarch64-linux-gnu-gcc -O2 -o hello hello.c
file hello        # ELF 64-bit LSB executable, ARM aarch64
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- defconfig Image dtbs
```

**What is in a toolchain**

- `gcc`/`clang` – compiler for the target.
- `as`, `ld`, `objcopy`, `objdump`, `readelf`, `nm`, `strip`, `addr2line` – binutils.
- C library (glibc/musl/newlib) and **kernel headers** that match the target kernel's userspace API.
- `gdb` (cross) for remote debugging with `gdbserver`.

**Sysroot:** a directory with the target's headers and libraries (`--sysroot=...`). Linking against the sysroot ensures the binary uses the same library versions as the target, not the host's.

**Getting a toolchain:** distro packages, Arm GNU Toolchain releases, Bootlin toolchains, or the SDK generated by Yocto (`bitbake -c populate_sdk`) or Buildroot (`make sdk`). Using the build system's SDK guarantees it matches the image.

**Classic mistakes:** linking against host libraries (missing sysroot), mismatched glibc version ("GLIBC_2.34 not found" on the target), wrong float ABI on 32-bit Arm (hard-float vs soft-float), and forgetting `ARCH=` when building the kernel.

### What is the difference between glibc, musl and uClibc-ng? {M}
**Short answer:** All three are C standard libraries for Linux. **glibc** is the most complete and compatible but the largest. **musl** is small, clean and easy to link statically, with strict standards behaviour. **uClibc-ng** targets very small systems, including MMU-less (noMMU) Linux. The choice affects image size, compatibility with existing software, and licensing.

| | glibc | musl | uClibc-ng |
|---|---|---|---|
| Size | large (~2 MB+ shared) | small (~1 MB, tiny static binaries) | small, very configurable |
| Compatibility | reference; almost all software assumes it | high, but some glibc extensions missing or different | good for common software |
| Static linking | possible but awkward (NSS, `dlopen`) | designed for it | supported |
| noMMU support | no | limited | yes |
| Locale/i18n | full | basic (UTF-8 only) | configurable |
| License | LGPL-2.1 | MIT | LGPL-2.1 |
| Used by | most distros, Yocto default | Alpine Linux, many Buildroot/OpenWrt images | old OpenWrt, very small devices |

**Practical points**

- **Binary compatibility:** a program built against glibc will not run on a musl system (different dynamic loader and symbol versions), and vice versa. Pick one per image.
- **Behaviour differences** seen in practice: DNS resolver details, smaller default thread stack size in musl (128 KB), `dlclose()` not unloading, some GNU-only functions missing.
- **Licensing:** LGPL requires that users can relink your application with a modified library. With dynamic linking that is easy; with static linking against glibc you must provide object files. musl's MIT license avoids this, which is one reason for its use in products.
- **Bare-metal is different:** Cortex-M firmware uses **newlib** or **newlib-nano** (or picolibc), not these Linux libraries.

**How to answer "which would you choose":** glibc for compatibility with third-party and vendor software (and when a vendor SDK requires it); musl for small, statically linked, security-focused or container images; uClibc-ng only for very constrained or noMMU targets.

### Which filesystems are used on embedded flash? {M}
**Short answer:** It depends on the flash type. On **raw NAND/NOR** (an MTD device without its own controller) use **UBIFS** on top of **UBI** (or JFFS2 on small NOR), because the filesystem must handle wear levelling and bad blocks. On **managed flash** (eMMC, SD, UFS, SSD) the controller does that, so use **ext4** or **F2FS**. For a read-only root use **SquashFS** or **EROFS**.

**Raw flash vs managed flash**

| | Raw NAND/NOR (MTD) | Managed (eMMC, SD, UFS) |
|---|---|---|
| Interface | `/dev/mtdN`, erase blocks, pages, OOB area | `/dev/mmcblkN`, normal block device |
| Bad blocks, ECC, wear levelling | software (UBI, MTD, NAND driver) | controller firmware (FTL) |
| Filesystems | UBIFS (on UBI), JFFS2, YAFFS2 | ext4, F2FS, (btrfs) |

**Filesystem guide**

- **UBIFS:** journaling, compression, scales to large NAND, fast mount. UBI below it spreads erases across the whole flash and manages bad blocks and volumes.
- **JFFS2:** older log-structured filesystem for small NOR; mount time grows with size.
- **ext4:** the default on eMMC/SD; mature, journaling. Use `data=ordered` (the default) and avoid unnecessary writes.
- **F2FS:** designed for flash-based block devices; can reduce write amplification on cheap SD/eMMC.
- **SquashFS / EROFS:** compressed and **read-only**; the root image cannot be corrupted by power loss. EROFS is newer, faster to read, and used by Android.
- **tmpfs:** RAM-based, for `/tmp`, `/run` and logs that do not need to survive reboot.
- **OverlayFS:** a writable layer (on a data partition or tmpfs) over a read-only root.

**A robust layout used by many products**

```
boot partition       (FAT or raw)   bootloader, kernel, DTB
rootfs A / rootfs B  (SquashFS/EROFS or ext4 mounted ro)   A/B update slots
data                 (ext4/F2FS or UBIFS)                  config, logs, user data
```

**Protecting against power loss and wear:** keep the root read-only, write data with `fsync()` and the write-temp-then-`rename()` pattern, limit logging to flash (journald with `Storage=volatile`, or rate limits), avoid `atime` updates (`noatime`), and monitor eMMC health (`mmc extcsd read` gives the life-time estimate).

### How do A/B (dual-copy) OTA updates work? {M}
**Short answer:** The device has two copies (slots) of the system. While running from slot A, the update client writes the new image into slot B, verifies it, and tells the bootloader to try B on the next boot. If B boots and the application confirms it is healthy, B becomes the active slot. If B fails to boot after a few attempts (detected by the bootloader's boot counter, often helped by a watchdog), the bootloader rolls back to A.

**Step by step**

1. Download the update (full image or delta) over HTTPS; verify its **signature**.
2. Write it to the **inactive slot** (B) while the device keeps working on A.
3. Verify what was written (hash).
4. Set bootloader variables: `boot_slot=B`, `boot_count=0`, `upgrade_available=1`.
5. Reboot. The bootloader increments `boot_count` and boots B.
6. User space (after the application is up and passes self-tests) marks the slot good: `upgrade_available=0`.
7. If the system reboots before that and `boot_count` exceeds the limit (e.g. 3), the bootloader switches back to A (**rollback**).

**What makes it robust**

- **Atomic:** the switch is a single variable change; a power cut during writing only affects the inactive slot.
- **Automatic rollback:** a bad kernel, a missing library or a crashing application does not brick the device.
- **Watchdog:** if the new system hangs instead of crashing, the hardware watchdog resets it so the boot counter can work.

**Costs and variations**

- **Double storage** for the system partitions. Alternatives: a single system plus a small **recovery** partition (cheaper, but the device is offline during the update).
- **Delta updates** (binary diffs, casync, zchunk) reduce download size, which matters for cellular devices.
- Data, configuration and the bootloader itself are usually **not** A/B; bootloader updates need extra care.

**Tools to name:** **RAUC**, **SWUpdate**, **Mender**, OSTree/Aktualizr (file-level, not block-level), and Android's `update_engine` (A/B "seamless updates").

**Security:** sign updates, check versions to prevent **rollback attacks** (installing an old vulnerable image; anti-rollback counters in fuses or RPMB), and combine with secure boot so a modified slot cannot boot.

### What is secure boot and a chain of trust? {H}
**Short answer:** Secure boot means each boot stage cryptographically verifies the next stage before running it, starting from code that cannot be changed (the boot ROM) and a key that cannot be changed (a hash of the public key burned into one-time-programmable fuses). If any check fails, the boot stops. The chain of trust extends from the ROM through the bootloaders and kernel to the root filesystem.

**A typical ARM chain**

1. **Boot ROM** (immutable) reads the public key hash from **OTP fuses** and verifies the signature on the first-stage loader (SPL / BL2).
2. The first stage verifies **TF-A BL31**, **OP-TEE** and **U-Boot**.
3. **U-Boot** verifies a signed **FIT image** containing the kernel, DTB and initramfs (`CONFIG_FIT_SIGNATURE`, key embedded in U-Boot's own DTB).
4. The **kernel** verifies the root filesystem with **dm-verity** (a hash tree checked on every block read; the root hash is signed or embedded in the signed initramfs/command line), and signed **kernel modules**.
5. Optionally **IMA/EVM** or signed application packages extend trust into user space.

**Signing vs encryption:** secure boot is about **authenticity** (signatures). Encrypting images (for IP protection) is a separate feature that uses device-unique keys.

**Important practical points**

- **Fuses are irreversible.** Burning the key hash and then the "secure boot closed" fuse makes the device reject unsigned images forever. Test on development parts, and follow a manufacturing procedure.
- **Key protection:** the private signing keys live in an HSM or a secure signing server, never on a developer laptop or in the repository. Plan key revocation (most SoCs allow several key slots).
- **Close the side doors:** disable or lock JTAG, the U-Boot console and environment (or make the environment read-only), USB recovery modes, and `init=`/`bootargs` changes. Otherwise an attacker bypasses the checks rather than breaking them.
- **Anti-rollback:** version counters in fuses or eMMC RPMB stop signed but old, vulnerable images from being installed.

**Related terms:** "verified boot" (Android, Chrome OS), "measured boot" (each stage is hashed into a TPM so a remote server can check what booted, without blocking boot), and UEFI Secure Boot on PCs and servers.

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
