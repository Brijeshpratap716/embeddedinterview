---
slug: embedded-linux
title: Embedded Linux & Boot
icon: 📦
level: Advanced
order: 9
desc: Bootloaders, U-Boot, root filesystems, Yocto and Buildroot, cross-compilation, OTA updates and secure boot.
---
Embedded Linux roles care about the whole system: how the board boots, how the image is built, and how it is updated in the field.

### What is a bootloader and why does an embedded Linux system need one? {E}
A bootloader initialises the minimum hardware the kernel needs (clocks, DRAM controller, storage, console), loads the kernel, device tree and initramfs into RAM, sets up the boot arguments and jumps to the kernel. On most SoCs booting is multi-stage: the on-chip boot ROM loads a small first stage (U-Boot SPL or vendor code) into internal SRAM, which initialises DRAM and loads the full bootloader. U-Boot is the most common; others include barebox, GRUB (x86/UEFI) and vendor loaders.

### What are the common U-Boot commands? {E}
- `printenv`, `setenv`, `saveenv`: view and change environment variables such as `bootcmd` and `bootargs`.
- `mmc list`, `mmc dev 0`, `fatload mmc 0:1 ${kernel_addr_r} Image`: load files from storage.
- `tftp ${kernel_addr_r} Image`: load over the network for fast development.
- `booti ${kernel_addr_r} - ${fdt_addr_r}`: boot an ARM64 `Image` (`bootz` for ARM32 zImage, `bootm` for FIT/uImage).
- `md`, `mw`: read and write memory; `i2c`, `gpio`, `sf` (SPI flash) for hardware checks.

### What are kernel command line (bootargs) parameters? {E}
Text passed by the bootloader (or embedded in the DTB `chosen` node) that configures the kernel at boot, for example:

```
console=ttymxc0,115200 root=/dev/mmcblk0p2 rootwait rw quiet loglevel=4
```

`console` sets the kernel console, `root` the root filesystem device, `rootwait` waits for slow storage, and `init=` overrides the init program. Read the running values in `/proc/cmdline`.

### What is an initramfs and when is it needed? {M}
An initial RAM filesystem: a cpio archive the kernel unpacks into a tmpfs and runs `/init` from before mounting the real root. It is needed when mounting root requires extra steps, such as loading storage drivers as modules, decrypting a LUKS partition, assembling RAID/LVM, choosing an A/B slot, or verifying dm-verity. Small embedded systems sometimes run entirely from an initramfs.

### What is the difference between Buildroot and Yocto? {M}
| | Buildroot | Yocto Project / OpenEmbedded |
|---|---|---|
| Model | Makefiles + Kconfig, builds one firmware image | Layers of BitBake recipes, builds a distribution |
| Learning curve | Gentle | Steep |
| Build time | Short | Long (but shared state cache helps) |
| Package management | No (full image rebuild) | Yes (ipk/deb/rpm, package feeds) |
| Customisation | Defconfig + overlays + post-build scripts | Layers, `.bbappend`, machine and distro configs |
| Typical use | Simple, fixed-function products | Products with many variants, long maintenance, vendor BSPs |

Most SoC vendors ship Yocto BSP layers (meta-imx, meta-ti, meta-qcom), which is why Yocto dominates in industry.

### What are Yocto layers, recipes and bbappend files? {M}
- A **recipe** (`.bb`) describes how to fetch, patch, configure, compile and install one piece of software, using BitBake tasks (`do_fetch`, `do_compile`, `do_install`).
- A **layer** (`meta-*`) is a collection of recipes and configuration, stacked by priority in `bblayers.conf`, so a vendor BSP, the distro and your product are kept separate.
- A **`.bbappend`** modifies an existing recipe from another layer without editing it, for example adding a patch or a config fragment to the kernel recipe.
- **Machine** config describes the board; **distro** config describes policy (init system, features); an **image** recipe lists what goes into the root filesystem.

### What is cross-compilation and what is a toolchain? {E}
Cross-compiling means building on one architecture (the host, e.g. x86-64) code that runs on another (the target, e.g. ARM64). A **toolchain** is the compiler, assembler, linker, C library and headers for the target, identified by a triplet like `aarch64-linux-gnu-` or `arm-none-eabi-` (bare metal, no OS). A **sysroot** holds the target's headers and libraries so programs link against the right versions. Build systems generate an SDK containing a matching toolchain and sysroot.

### What is the difference between glibc, musl and uClibc-ng? {M}
All three are C libraries. **glibc** is full-featured and the most compatible, but large. **musl** is small, clean, statically linkable and strict about standards, used by Alpine Linux and many embedded systems; some software assumes glibc behaviour. **uClibc-ng** targets very small and MMU-less systems. The choice affects image size, binary compatibility and licensing (all are LGPL or MIT-style; musl is MIT).

### Which filesystems are used on embedded flash? {M}
- **Raw NAND/NOR flash** (MTD devices): **UBIFS** on top of UBI (handles wear levelling and bad blocks), or JFFS2 for small NOR.
- **Managed flash** (eMMC, SD, UFS) has its own controller, so use **ext4** or **F2FS**.
- **Read-only root**: **SquashFS** or **EROFS** (compressed), often combined with an overlay for writable data.

Protect against power loss with journaling, read-only roots and careful write patterns.

### How do A/B (dual-copy) OTA updates work? {M}
The device has two root filesystem slots. While running from slot A, the updater writes the new image to slot B, verifies it, and tells the bootloader to try B on the next boot. If B fails to boot (no "boot successful" mark within a few attempts, often with a watchdog), the bootloader falls back to A. This gives atomic updates and automatic rollback at the cost of double storage. Tools: RAUC, SWUpdate, Mender, and Android's update_engine. Delta updates reduce download size.

### What is secure boot and a chain of trust? {H}
Each boot stage cryptographically verifies the next before running it. The boot ROM verifies the first-stage loader with a public key whose hash is burned into one-time-programmable fuses; that loader verifies the next (TF-A, U-Boot); U-Boot verifies a signed FIT image containing the kernel, DTB and initramfs; the kernel can then verify the root filesystem with **dm-verity** and modules with module signing. A break at any stage stops boot. Keys must be protected (HSM), and fuse programming is irreversible, so it needs a careful manufacturing process.

### What is the difference between systemd, SysVinit and BusyBox init? {E}
They are PID 1, the first user-space process, which starts and supervises everything else. **BusyBox init** reads a simple `/etc/inittab` and is tiny. **SysVinit** runs shell scripts in runlevel order. **systemd** starts units in parallel based on dependencies, supervises and restarts services, handles logging (journald), devices, timers and watchdogs, at the cost of size and complexity. Small devices often use BusyBox; larger products use systemd.

### How do you reduce boot time on an embedded Linux device? {M}
Measure first (`grabserial`, `bootchart`, `systemd-analyze blame`, kernel `initcall_debug`). Then:

- Bootloader: remove the countdown delay, skip unneeded hardware init, load only what is needed (Falcon mode in U-Boot can skip the full bootloader).
- Kernel: build only needed drivers in, use `quiet`, LZ4 or uncompressed images, defer non-critical drivers with modules or async probe.
- User space: start the critical application early, remove unused services, use a read-only SquashFS/EROFS root, prelink or statically link the main app.

Sub-2-second boots are achievable on modern SoCs.

### How do you access GPIO from Linux user space? {M}
Use the **GPIO character device** (`/dev/gpiochipN`) through **libgpiod** and its tools: `gpiodetect`, `gpioinfo`, `gpioget`, `gpioset`, `gpiomon`. The older sysfs interface (`/sys/class/gpio/export`) is deprecated because it has global numbering, no ownership and no proper event handling. For production, it is better to describe the pin in the device tree and let a kernel driver own it (`gpio-leds`, `gpio-keys`).

### What is the difference between a kernel driver and a user-space driver (UIO, spidev)? {M}
A kernel driver integrates with subsystems, handles interrupts directly and can be used by any application through standard interfaces. User-space drivers use generic kernel helpers: **spidev** and **i2c-dev** for bus access, **UIO** or **VFIO** to `mmap` registers and receive interrupts via `read`. They are faster to develop, easier to debug and can be proprietary, but they have higher interrupt latency, cannot be used by other kernel subsystems and are harder to make safe. Use them for prototyping or simple, exclusive devices.
