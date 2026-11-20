---
slug: virtualization
title: Virtualization (QEMU & KVM)
icon: 🖥️
level: Advanced
order: 17
desc: Emulation vs virtualization, ARM exception levels and EL2, QEMU code flow, TCG, QOM devices, memory regions, the KVM ioctl loop, VM exits, stage-2 translation, vGIC and virtio.
---
Virtualization questions come up for automotive (hypervisor-based cockpit systems), avionics, server and cloud roles, and any team that uses QEMU for pre-silicon development or CI. Interviewers usually start with "what is the difference between QEMU and KVM", then go down into the code flow. Source file and function names below are from recent QEMU and Linux versions; older QEMU used `softmmu/` where it now uses `system/`, and some function names have changed, so say "roughly" when you quote them.

### What is the difference between emulation and virtualization (QEMU TCG vs KVM)? {E}
**Short answer:** **Emulation** runs guest instructions by translating them in software, so the guest CPU can be a different architecture from the host (ARM guest on an x86 PC). QEMU does this with **TCG**. **Hardware-assisted virtualization** runs guest instructions directly on the real CPU, with hardware support to trap the few operations the hypervisor must control; guest and host must be the same architecture. **KVM** is the Linux kernel part that provides this, and QEMU uses it as an accelerator.

| | QEMU with TCG (emulation) | QEMU + KVM (virtualization) |
|---|---|---|
| Guest instructions | translated to host code by software | run natively on the CPU |
| Guest arch | any QEMU supports (ARM on x86, RISC-V on ARM) | same as host (ARM64 on ARM64, x86 on x86) |
| Speed | roughly 5–20× slower than native, depends heavily on workload | close to native for CPU work |
| Needs | nothing special | CPU virtualization extensions (ARM EL2, Intel VT-x, AMD-V) and `/dev/kvm` |
| Device models | QEMU (user space) | still mostly QEMU, plus in-kernel GIC/timer and vhost |
| Typical use | pre-silicon bring-up, cross-arch development, CI, debugging | servers, cloud, automotive/industrial consolidation |

**Who does what with KVM**

- **KVM (kernel module / built-in):** creates VMs and vCPUs, sets up stage-2 page tables, switches the CPU between host and guest, handles most traps itself (system registers, timers, interrupt controller).
- **QEMU (user space):** parses the command line, builds the machine (memory map, device tree, devices), loads the kernel, runs one thread per vCPU calling `ioctl(KVM_RUN)`, and emulates devices when the guest touches their MMIO space.

**Other user-space VMMs using KVM:** Firecracker, Cloud Hypervisor, crosvm, kvmtool (`lkvm`). They are smaller than QEMU and support fewer devices.

**One-line summary for interviews:** "QEMU is the machine emulator and VMM; TCG is how it runs foreign code; KVM is how it runs native code at near-native speed using the CPU's virtualization extensions."

### What is a hypervisor, and what is the difference between type 1 and type 2? {E}
**Short answer:** A hypervisor (virtual machine monitor) creates and runs virtual machines, sharing the physical CPU, memory and devices between them while keeping them isolated. A **type 1** (bare-metal) hypervisor runs directly on the hardware (Xen, VMware ESXi, QNX Hypervisor, many automotive hypervisors). A **type 2** (hosted) hypervisor runs as a program on a normal OS (VirtualBox, QEMU with TCG). **KVM** turns Linux itself into a hypervisor, so it is usually described as type 1, with QEMU as its user-space helper.

**What a hypervisor must provide**

- **CPU virtualization:** each VM has virtual CPUs; privileged operations by the guest kernel are trapped and handled.
- **Memory virtualization:** each VM sees its own "physical" memory, mapped by the hypervisor to real RAM (stage-2 / EPT page tables).
- **Device and interrupt virtualization:** emulated devices, paravirtual devices (virtio) or real devices passed through (VFIO with an IOMMU/SMMU).
- **Isolation:** a crash or attack in one VM must not affect the others.

**Where KVM fits**

```
+-------------------+   +-------------------+
| Guest OS (EL1)    |   | Guest OS (EL1)    |
| QEMU process      |   | QEMU process      |   <- user space on the host
+-------------------+---+-------------------+
|        Linux kernel + KVM (EL2 with VHE)  |   <- host OS *is* the hypervisor
+-------------------------------------------+
|                Hardware                   |
+-------------------------------------------+
```

**Embedded and automotive angle:** a single SoC runs a safety-relevant instrument cluster (an RTOS or Linux) next to the infotainment system (Android) under a type-1 hypervisor. The hypervisor guarantees that an Android crash cannot take the cluster down. Examples: QNX Hypervisor, Xen (with the Arm safety work), PikeOS, ACRN (x86), and KVM-based solutions.

**Related terms:** *paravirtualization* (the guest knows it is virtualized and calls the hypervisor directly, e.g. virtio, Xen PV), *full virtualization* (an unmodified guest), and *containers*, which share one kernel and are not virtual machines.

### What are the ARMv8 exception levels, and how does virtualization use EL2? {M}
**Short answer:** ARMv8-A has four exception levels: **EL0** user applications, **EL1** the OS kernel, **EL2** the hypervisor, and **EL3** the secure monitor (firmware such as TF-A that switches between Normal and Secure worlds). A guest kernel runs at EL1 and its applications at EL0, exactly as on bare metal; EL2 configures what traps to it and controls the second stage of address translation, which is how the hypervisor stays in control.

| Level | Runs | Examples |
|---|---|---|
| EL0 | applications | user processes (guest and host) |
| EL1 | OS kernel | Linux, guest kernels |
| EL2 | hypervisor | KVM (or its low-level part), Xen |
| EL3 | secure monitor | TF-A BL31, handles SMC calls and PSCI |

Higher numbers are more privileged. Moving up happens only through an exception (interrupt, abort, or the instructions `SVC` → EL1, `HVC` → EL2, `SMC` → EL3). Moving down happens with `ERET`.

**What EL2 controls**

- **`HCR_EL2`** (Hypervisor Configuration Register): which guest operations trap to EL2 (e.g. `TWI` traps `WFI`, `TSC` traps `SMC`, `IMO`/`FMO` route physical IRQ/FIQ to EL2, `VM` enables stage-2 translation).
- **Stage-2 translation** (`VTTBR_EL2`, `VTCR_EL2`): the guest's "physical" addresses (IPAs) are translated again to real physical addresses.
- **Virtual interrupts**: injecting IRQs into the guest through the GIC's virtual CPU interface.
- **Virtual timer offset** (`CNTVOFF_EL2`) so each guest sees its own time base.

**How KVM uses EL2: nVHE vs VHE**

- **nVHE (non-VHE, ARMv8.0):** the host kernel runs at EL1. A small piece of KVM code ("hyp" code) is installed at EL2 and does the world switch. Every switch between host and guest goes EL1 → EL2 → EL1.
- **VHE (Virtualization Host Extensions, ARMv8.1+):** the host kernel itself runs at **EL2**, and EL1 register accesses are redirected to their EL2 versions. Entering and leaving the guest is cheaper. Cortex-A53 does **not** have VHE (it is ARMv8.0); Cortex-A55/A76 and later do.
- **pKVM (protected KVM)**, used on Android: the host runs at EL1 and a small trusted hypervisor at EL2 protects guest memory even from the host kernel.

**Interview follow-up:** "Does a guest system call (`SVC`) go to the hypervisor?" No. It goes to the guest kernel at EL1 without any hypervisor involvement. That is a big part of why virtualization is fast.

### What happens in QEMU when you start a virtual machine? Explain the code flow. {H}
**Short answer:** `main()` calls `qemu_init()`, which parses the command line, selects the accelerator (TCG or KVM), creates the machine object, and runs the machine's init function (e.g. `machvirt_init()` for `-M virt` on ARM, `pc_init1()`/`pc_q35_init()` on x86). That function creates the CPUs, RAM, interrupt controller and devices, generates the device tree or ACPI tables and loads the kernel/firmware. Then `qemu_main_loop()` runs the event loop while separate vCPU threads execute guest code (with TCG's `cpu_exec()` or KVM's `kvm_cpu_exec()`).

**Main thread (paths from recent QEMU)**

```
system/main.c       main()
system/vl.c           qemu_init(argc, argv)
                        parse options, qemu_create_machine()
                        configure_accelerators()      -> kvm_init() or tcg init
                        qmp_x_exit_preconfig()
                          qemu_init_board()
                            machine_run_board_init()
                              MachineClass->init()    -> machvirt_init()  (hw/arm/virt.c)
                                                      -> pc_q35_init()    (hw/i386/pc_q35.c)
                          qemu_machine_creation_done()
system/runstate.c     qemu_main_loop()                -> main_loop_wait(): timers, fd/IO events, BHs
```

**What the board init does (ARM `virt` example)**

1. Create the vCPUs from the `-cpu` model (e.g. `cortex-a53`, defined with an init function in `target/arm/cpu64.c`) and **realize** them: this sets the ID registers and features, and with KVM creates the KVM vCPU.
2. Create **RAM** (`memory_region_init_ram` or the machine's memory backend) and map it at the board's RAM base (`0x40000000` on `virt`).
3. Create the **GIC**, UARTs (PL011), RTC, GPIO, virtio-mmio transports, PCIe host bridge, flash for firmware, `fw_cfg`.
4. Wire up **interrupts** (`qdev_connect_gpio_out` / `sysbus_connect_irq`).
5. Generate the **device tree** describing all of this (or ACPI tables for UEFI boots).
6. Set up the **boot**: load `-kernel`, `-initrd`, `-dtb`, or firmware (`-bios`), and set the CPU start state (PC and `x0` = DTB address).

**vCPU threads**

- TCG: `mttcg_cpu_thread_fn()` (one thread per vCPU when multi-threaded TCG is enabled) loops on `tcg_cpu_exec()` → `cpu_exec()`.
- KVM: `kvm_vcpu_thread_fn()` loops on `kvm_cpu_exec()` → `ioctl(KVM_RUN)`. (Older QEMU called it `qemu_kvm_cpu_thread_fn`.)

**The big QEMU lock (BQL):** device emulation runs under a global mutex. A vCPU that exits to handle MMIO takes the BQL, calls the device model, releases it and goes back to running the guest.

**x86 `pc` machine:** same structure, but the board also loads SeaBIOS/OVMF into the top of the 4 GB space with `rom_load_file()`, the CPU starts in 16-bit real mode at the reset vector, and the firmware then loads the bootloader.

### How does QEMU's TCG translate and run guest code? {H}
**Short answer:** TCG (Tiny Code Generator) works on **translation blocks** (TBs): a straight-line run of guest instructions ending at a branch. The target front end decodes each guest instruction into architecture-neutral TCG intermediate operations, the TCG back end optimises them and generates host machine code, and the result is cached. `cpu_exec()` looks up the TB for the current guest PC, translates it if missing, runs it, and repeats. Blocks are **chained** directly to each other so the common path does not return to the main loop.

**Pipeline**

```
guest code (ARM64)
   │  front end: target/arm/tcg/translate-a64.c  (decode, emit TCG ops)
   ▼
TCG ops (IR):  ld_i64 tmp, env, x1 ; add_i64 tmp, tmp, $4 ; st_i64 tmp, env, x0 ...
   │  optimiser + register allocation: tcg/tcg.c, tcg/optimize.c   (tcg_gen_code)
   ▼
host code (x86-64 or ARM64) in the code cache
```

**The execution loop (`accel/tcg/cpu-exec.c`)**

1. `cpu_exec()` → `cpu_exec_loop()`.
2. Check for pending interrupts and exceptions (`cpu_handle_interrupt`, `cpu_handle_exception`).
3. `tb_lookup()` finds a TB by (PC, CPU flags such as exception level); on a miss, `tb_gen_code()` translates a new one.
4. `cpu_tb_exec()` jumps into the generated host code.
5. The TB ends by jumping straight to the next TB (**chaining**/`goto_tb`) or returning to the loop.

**Key ideas to mention**

- **Guest CPU state** lives in a C structure (`CPUARMState env`): registers are memory fields, and the generated code loads and stores them.
- **Helpers:** complex instructions (system registers, floating point corner cases, crypto) call C helper functions instead of being expanded inline.
- **Softmmu:** every guest load/store goes through a software TLB that maps guest virtual addresses to host addresses. A miss calls the slow path, which walks the guest page tables and, for MMIO, calls the device model's read/write callbacks.
- **Self-modifying code:** pages that contain translated code are write-protected in the software TLB; writing to them invalidates the affected TBs.
- **MTTCG:** since QEMU 2.9, each vCPU can run in its own host thread, which needs correct handling of guest memory ordering (barriers and atomics are translated to host equivalents).

**Debugging with TCG:** `-d in_asm,op,out_asm -D log.txt` dumps guest instructions, TCG ops and host code; `-d int` logs interrupts and exceptions, which is very useful when a guest kernel crashes early. `-singlestep`/`-one-insn-per-tb` makes each TB one instruction for precise tracing.

### How do you use QEMU to run and debug an ARM64 Linux kernel? {M}
**Short answer:** Use the `virt` machine: `qemu-system-aarch64 -M virt -cpu cortex-a53 -smp 2 -m 1G -nographic -kernel Image -initrd rootfs.cpio.gz -append "console=ttyAMA0"`. Add `-s -S` to make QEMU wait for GDB on port 1234, then connect `gdb vmlinux` with `target remote :1234` and debug the kernel from the first instruction.

```bash
qemu-system-aarch64 \
  -M virt -cpu cortex-a53 -smp 2 -m 1024 \
  -nographic \
  -kernel arch/arm64/boot/Image \
  -initrd rootfs.cpio.gz \
  -append "console=ttyAMA0 nokaslr" \
  -s -S
```

| Option | Meaning |
|---|---|
| `-M virt` | generic ARM virtual board (no real hardware equivalent; QEMU generates its device tree) |
| `-cpu cortex-a53` | CPU model for TCG; with KVM use `-cpu host` |
| `-smp 2` / `-m 1024` | 2 vCPUs, 1 GiB RAM |
| `-nographic` | no display window; serial console on the terminal (`Ctrl-A x` to quit, `Ctrl-A c` for the monitor) |
| `-kernel` / `-initrd` / `-append` | direct kernel boot, no bootloader needed |
| `-dtb` | use your own device tree instead of the generated one |
| `-accel kvm` (`-enable-kvm`) | use KVM; only works when the host is ARM64 |
| `-s -S` | GDB server on TCP 1234 (`-s`), and do not start the CPUs until GDB says so (`-S`) |

**Debug session**

```bash
aarch64-linux-gnu-gdb vmlinux     # or gdb-multiarch
(gdb) target remote :1234
(gdb) hbreak start_kernel
(gdb) continue
(gdb) bt
```

Build the kernel with `CONFIG_DEBUG_INFO` and `CONFIG_GDB_SCRIPTS` (then `lx-dmesg`, `lx-ps` work in GDB), and boot with `nokaslr` so addresses match the symbols.

**More debugging tools**

- `-d int,guest_errors -D qemu.log` – log exceptions and invalid device accesses.
- QEMU monitor (`Ctrl-A c`): `info registers`, `info mtree` (memory map), `info qtree` (devices), `xp /16x 0x40000000` (physical memory).
- `-trace "pl011*"` – trace events of a device model.
- `-machine dumpdtb=virt.dtb` – save the generated device tree, then `dtc -I dtb -O dts virt.dtb` to read it.

**Why teams use this:** kernel and driver development before hardware exists, reproducible CI tests (boot every commit in QEMU), and debugging early boot crashes that are hard to catch on a real board.

### What is the QEMU Object Model (QOM), and how is a device model added? {H}
**Short answer:** QOM is QEMU's object system in C: every machine, CPU, bus and device is a **type** registered with a `TypeInfo` (name, parent type, instance size, class and instance init functions). Devices inherit from `TYPE_DEVICE` or `TYPE_SYS_BUS_DEVICE`, expose properties, and do their setup in a `realize()` method. A memory-mapped device registers a `MemoryRegion` with read/write callbacks and output IRQ lines, and the board maps it at an address and wires its interrupt.

**Minimal sysbus device**

```c
#define TYPE_MY_TIMER "my-timer"
OBJECT_DECLARE_SIMPLE_TYPE(MyTimerState, MY_TIMER)

struct MyTimerState {
    SysBusDevice parent_obj;
    MemoryRegion iomem;
    qemu_irq irq;
    uint32_t ctrl, count;
};

static uint64_t my_timer_read(void *opaque, hwaddr off, unsigned size)
{
    MyTimerState *s = opaque;
    switch (off) {
    case 0x0: return s->ctrl;
    case 0x4: return s->count;
    default:
        qemu_log_mask(LOG_GUEST_ERROR, "my-timer: bad read 0x%" HWADDR_PRIx "\n", off);
        return 0;
    }
}

static void my_timer_write(void *opaque, hwaddr off, uint64_t val, unsigned size)
{
    MyTimerState *s = opaque;
    if (off == 0x0) { s->ctrl = val; qemu_set_irq(s->irq, val & 1); }
}

static const MemoryRegionOps my_timer_ops = {
    .read = my_timer_read,
    .write = my_timer_write,
    .endianness = DEVICE_NATIVE_ENDIAN,
    .valid = { .min_access_size = 4, .max_access_size = 4 },
};

static void my_timer_realize(DeviceState *dev, Error **errp)
{
    MyTimerState *s = MY_TIMER(dev);
    memory_region_init_io(&s->iomem, OBJECT(s), &my_timer_ops, s, "my-timer", 0x1000);
    sysbus_init_mmio(SYS_BUS_DEVICE(s), &s->iomem);
    sysbus_init_irq(SYS_BUS_DEVICE(s), &s->irq);
}

static void my_timer_class_init(ObjectClass *klass, void *data)
{
    DEVICE_CLASS(klass)->realize = my_timer_realize;
}

static const TypeInfo my_timer_info = {
    .name = TYPE_MY_TIMER,
    .parent = TYPE_SYS_BUS_DEVICE,
    .instance_size = sizeof(MyTimerState),
    .class_init = my_timer_class_init,
};

static void my_timer_register_types(void) { type_register_static(&my_timer_info); }
type_init(my_timer_register_types)
```

**In the board code:**

```c
DeviceState *dev = sysbus_create_simple(TYPE_MY_TIMER, 0x09100000,
                                        qdev_get_gpio_in(gic, MY_TIMER_IRQ));
```

Then add a device tree node so the guest kernel finds it.

**Things a reviewer expects**

- **Reset** handling (`device_class_set_legacy_reset` or the `ResettableClass` phases) so registers return to their reset values on a machine reset.
- **Migration state** (`VMStateDescription`) so the VM can be saved and migrated.
- **Properties** (`DEFINE_PROP_UINT32`) for configurable values, instead of hard-coding them.
- Log invalid guest accesses with `LOG_GUEST_ERROR`, never `abort()` on guest behaviour.

**Older terms you may hear:** `qdev_create()`/`qdev_init_nofail()` were replaced by `qdev_new()` + `sysbus_realize_and_unref()`, but `sysbus_create_simple()` is still common in board code.

### How does QEMU model guest memory and MMIO (MemoryRegion and AddressSpace)? {H}
**Short answer:** QEMU describes the guest's physical address map as a tree of **`MemoryRegion`s**: RAM regions backed by host memory, I/O regions whose accesses call device callbacks (`MemoryRegionOps`), aliases, and containers that hold sub-regions at offsets. An **`AddressSpace`** (e.g. the system address space each CPU sees, or a device's DMA address space) points to a root region. QEMU flattens the tree into a **`FlatView`** (a sorted list of ranges) for fast lookup, and with KVM it registers the RAM ranges with the kernel.

**Key functions**

| Function | Creates |
|---|---|
| `memory_region_init_ram()` | RAM backed by host memory |
| `memory_region_init_rom()` | read-only memory (e.g. boot ROM) |
| `memory_region_init_io()` | MMIO region: reads/writes call the `MemoryRegionOps` callbacks |
| `memory_region_init_alias()` | a window onto part of another region (e.g. low RAM aliased below 1 MB) |
| `memory_region_add_subregion(parent, offset, child)` | place a region in the map (with priorities for overlaps) |

**How an access is handled**

- **TCG:** a guest load goes through the software TLB. For RAM, the TLB entry gives a host pointer and the access is a plain host load. For MMIO, the slow path finds the `MemoryRegion` and calls its `read` callback with the offset and size.
- **KVM:** RAM ranges are given to the kernel with `KVM_SET_USER_MEMORY_REGION` (guest physical address → QEMU's host virtual address). Guest accesses to RAM never leave the guest. An access to an address with **no RAM mapping** causes a stage-2 fault; KVM reports `KVM_EXIT_MMIO` to QEMU with the address, size and data, QEMU calls the device's callback, and then resumes the vCPU.

**See the map:** QEMU monitor `info mtree` prints the whole tree; `info mtree -f` prints the flattened view.

```
address-space: memory
  0000000000000000-ffffffffffffffff (prio 0, i/o): system
    0000000008000000-0000000008020000 (prio 0, i/o): gic_dist
    0000000009000000-0000000009000fff (prio 0, i/o): pl011
    0000000040000000-000000007fffffff (prio 0, ram): mach-virt.ram
```

**DMA:** devices use `dma_memory_read/write()` or `address_space_rw()` on their DMA address space, which may sit behind an emulated IOMMU (SMMUv3 on ARM `virt`), so the same code works whether or not an IOMMU is present.

**Why the layering matters:** the same device model works with TCG and KVM, and board code can move, alias or overlay regions (e.g. a boot ROM that is remapped after boot) without touching the device code.

### How does QEMU use KVM? Explain the ioctl sequence and the run loop. {H}
**Short answer:** QEMU opens `/dev/kvm`, creates a VM with `KVM_CREATE_VM` (which returns a VM file descriptor), registers guest RAM with `KVM_SET_USER_MEMORY_REGION`, creates each vCPU with `KVM_CREATE_VCPU`, `mmap`s the vCPU's shared `kvm_run` structure, initialises the vCPU (on ARM with `KVM_ARM_VCPU_INIT`) and sets its registers. Each vCPU thread then loops on `ioctl(vcpu_fd, KVM_RUN)`: the guest runs until something needs QEMU, KVM returns with an exit reason in `kvm_run`, QEMU handles it and calls `KVM_RUN` again.

```c
int kvm  = open("/dev/kvm", O_RDWR);
int vmfd = ioctl(kvm, KVM_CREATE_VM, 0);               /* on ARM the arg can set the IPA size */

void *ram = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANONYMOUS, -1, 0);
struct kvm_userspace_memory_region mr = {
    .slot = 0, .guest_phys_addr = 0x40000000, .memory_size = size,
    .userspace_addr = (uint64_t)ram,
};
ioctl(vmfd, KVM_SET_USER_MEMORY_REGION, &mr);

int vcpu = ioctl(vmfd, KVM_CREATE_VCPU, 0);
int run_sz = ioctl(kvm, KVM_GET_VCPU_MMAP_SIZE, 0);
struct kvm_run *run = mmap(NULL, run_sz, PROT_READ | PROT_WRITE, MAP_SHARED, vcpu, 0);

struct kvm_vcpu_init init;
ioctl(vmfd, KVM_ARM_PREFERRED_TARGET, &init);
ioctl(vcpu, KVM_ARM_VCPU_INIT, &init);
/* set PC and x0 with KVM_SET_ONE_REG ... */

for (;;) {
    ioctl(vcpu, KVM_RUN, 0);
    switch (run->exit_reason) {
    case KVM_EXIT_MMIO:          /* run->mmio.phys_addr, .data, .len, .is_write */
        handle_mmio(run);  break;
    case KVM_EXIT_SYSTEM_EVENT:  /* PSCI SYSTEM_OFF / RESET */
        return;
    case KVM_EXIT_INTR:          /* a signal interrupted KVM_RUN */
        break;
    default:
        abort();
    }
}
```

**In QEMU:** `kvm_init()` (`accel/kvm/kvm-all.c`) creates the VM; `kvm_init_vcpu()` creates vCPUs; `kvm_vcpu_thread_fn()` calls `kvm_cpu_exec()`, which contains the `KVM_RUN` loop and dispatches exits to `address_space_rw()` for MMIO (or to port I/O on x86).

**Inside the kernel, one `KVM_RUN`:** load the guest's registers and stage-2 page table base, enable traps, `ERET` into the guest at EL1. On a trap, save guest state, restore host state, and either handle it in the kernel and re-enter (most exits) or return to user space.

**Corrections to common notes**

- There are **no** `KVM_DESTROY_VM` or `KVM_DESTROY_VCPU` ioctls. A VM and its vCPUs are destroyed when their file descriptors are closed (when QEMU exits).
- On **arm64** KVM is built into the kernel image (`CONFIG_KVM`); there is no separate `kvm-arm.ko`. On x86 it is `kvm.ko` plus `kvm-intel.ko` or `kvm-amd.ko`.
- Guest **system calls do not cause VM exits**: `SVC` goes to the guest kernel at EL1. Exits come from MMIO, trapped instructions and registers, `WFI`, `HVC`/`SMC` (PSCI), and interrupts.

### What causes a VM exit on ARM, and how is an MMIO access handled? {H}
**Short answer:** A VM exit (a trap to EL2) happens when the guest does something the hypervisor configured to trap: accessing an address with no stage-2 mapping (MMIO to an emulated device), executing `HVC`/`SMC` (e.g. PSCI calls to start or stop CPUs), `WFI`/`WFE` when it has nothing to do, accessing trapped system registers, or when a physical interrupt arrives that the host must handle. KVM handles most of these in the kernel; MMIO to a QEMU device is passed to user space as `KVM_EXIT_MMIO`.

**Exit reasons (reported in `ESR_EL2`, the syndrome register)**

| Cause | Typical handling |
|---|---|
| Stage-2 **data abort** on an unmapped IPA | MMIO: decode the access, in-kernel device (vGIC, ITS) or `KVM_EXIT_MMIO` to QEMU; RAM not yet mapped: allocate/map the page and retry |
| `HVC` / `SMC` | PSCI (`CPU_ON`, `CPU_OFF`, `SYSTEM_RESET`) handled in KVM; others forwarded |
| `WFI` | put the vCPU thread to sleep until it has an interrupt (frees the physical CPU) |
| System register access (trapped by `HCR_EL2`/fine-grained traps) | emulate in KVM (e.g. performance counters, debug, cache maintenance by set/way) |
| Physical IRQ while guest runs | exit to the host so the host kernel handles it, then maybe inject a virtual IRQ |
| Stage-2 permission fault | dirty-page tracking for live migration, copy-on-write |

**MMIO step by step (guest writes a UART register)**

1. Guest executes `STR w1, [x0]` where `x0` = `0x09000000` (the PL011 on `virt`).
2. Stage-1 translation (guest page tables) gives IPA `0x09000000`. Stage 2 has **no mapping** there, so the CPU takes a data abort to EL2.
3. KVM reads `ESR_EL2` (which register, access size, read or write — the "ISV" valid syndrome) and `HPFAR_EL2` (the faulting IPA).
4. The address is not an in-kernel device, so KVM fills `kvm_run->mmio` (`phys_addr`, `len`, `is_write`, `data`) and returns from `KVM_RUN` with `KVM_EXIT_MMIO`.
5. QEMU calls `address_space_rw()`, which finds the PL011 `MemoryRegion` and calls `pl011_write()`; the character goes to the host terminal.
6. QEMU calls `KVM_RUN` again; KVM advances the guest PC past the store and resumes.

**Cost:** an exit to user space takes several microseconds. That is why heavily used devices are moved into the kernel (vGIC, arch timer, vhost-net) or replaced by paravirtual virtio devices that batch requests.

**Gotcha:** if the guest uses an instruction that does not give a valid syndrome (e.g. a load/store pair or writeback addressing to MMIO), KVM cannot decode it and reports an error; guest drivers must use simple accessors (`readl`/`writel`) for MMIO.

### What is two-stage address translation (stage 2, IPA)? {H}
**Short answer:** With virtualization there are two page-table walks. **Stage 1** is owned by the guest OS and translates guest virtual addresses (VA) to **intermediate physical addresses (IPA)**, which the guest thinks are physical. **Stage 2** is owned by the hypervisor and translates IPAs to real physical addresses (PA). The guest cannot see or change stage 2, so it can only reach memory the hypervisor has given it.

```
guest VA --(stage 1, guest's TTBR0/1_EL1)--> IPA --(stage 2, VTTBR_EL2)--> PA
```

**Why it matters**

- **Isolation:** each VM has its own stage-2 tables, so one guest cannot address another guest's or the host's memory.
- **Unmodified guests:** the guest manages its own page tables normally, with no hypervisor calls; on x86 this is EPT (Intel) or NPT/RVI (AMD).
- **Trapping MMIO:** leaving device addresses unmapped in stage 2 makes every access fault to the hypervisor, which then emulates the device.
- **Memory over-commit and migration:** the hypervisor can unmap, swap, share (KSM) or write-protect guest pages to track dirty pages during live migration.

**Cost of a TLB miss:** each step of the guest's stage-1 walk itself needs a stage-2 translation. With 4-level tables at both stages, a miss can cost up to 24 memory accesses instead of 4. TLBs cache the **combined** VA→PA result, tagged with the **VMID** (and ASID), so switching between VMs does not require flushing the whole TLB. Large pages at stage 2 (2 MB/1 GB, via hugepages for guest RAM) reduce the cost a lot.

**Related hardware:** the **SMMU** (Arm's IOMMU) also has stage-1 and stage-2 translation, so a device passed through to a guest can only DMA into that guest's memory.

**Interview check question:** "Who handles a page fault on a guest virtual address that is not in the guest's page tables?" The **guest** kernel: it is a stage-1 fault, delivered to EL1 as normal. Only stage-2 faults go to the hypervisor.

### How are interrupts and timers virtualized on ARM (vGIC and the generic timer)? {H}
**Short answer:** The GICv2/v3 has hardware virtualization support: the hypervisor writes pending virtual interrupts into **List Registers** (`ICH_LR<n>_EL2`), and the guest acknowledges and completes them through the **virtual CPU interface** without trapping. KVM emulates the distributor and redistributors (the "vGIC") in the kernel. For time, each vCPU uses the **virtual timer** (`CNTV_*`), which counts physical time minus a per-VM offset; when it fires, KVM injects the virtual timer interrupt (PPI 27) into the guest.

**Interrupt path for an emulated device**

1. A QEMU device raises its IRQ line → QEMU calls `KVM_IRQ_LINE` (or signals an **irqfd**, an eventfd the kernel waits on).
2. The in-kernel vGIC marks the virtual interrupt pending for the target vCPU.
3. Before entering the guest, KVM writes it into a **List Register** and kicks the vCPU if it is sleeping in `WFI`.
4. The guest takes a normal IRQ exception at EL1, reads `ICC_IAR1_EL1` (which the hardware serves from the virtual interface), handles it, writes EOI. No exit is needed for the acknowledge and EOI.

**Physical interrupts while the guest runs** are routed to EL2 (`HCR_EL2.IMO`), so the host can always regain the CPU (for its own devices and for scheduling).

**Device passthrough:** with **GICv4/4.1**, MSIs from a passed-through PCIe device can be delivered directly to a running vCPU without a hypervisor exit.

**Timers**

- The **physical** timer (`CNTP`) is used by the host; the **virtual** timer (`CNTV`) by the guest. `CNTVOFF_EL2` lets each VM have its own time base (useful after migration or pause).
- KVM saves and restores the guest's timer state on every world switch and uses a host hrtimer to wake a vCPU that is blocked in `WFI` when its timer is due.

**Why it was moved into the kernel:** emulating the GIC in QEMU would turn every interrupt acknowledge and EOI into an exit to user space. In-kernel vGIC plus hardware List Registers makes interrupt-heavy workloads practical.

**x86 equivalent:** APIC virtualization (APICv, AVIC) and posted interrupts.

### What is virtio, and why is it faster than emulating a real device? {M}
**Short answer:** Virtio is a standard for **paravirtual** devices: instead of emulating a real network card or disk controller register by register, the guest uses a simple driver that puts requests into shared-memory ring buffers (**virtqueues**) and notifies the host once per batch. This avoids most VM exits. Common devices are virtio-net, virtio-blk, virtio-scsi, virtio-gpu, virtio-console, virtio-rng and virtio-vsock.

**How a virtqueue works**

- A **descriptor table** of buffers (guest physical address, length, flags), an **available ring** where the guest posts descriptor indexes, and a **used ring** where the device returns completed ones (the "split" layout; virtio 1.1 adds a "packed" layout).
- The guest adds buffers, then **kicks** the device with one MMIO/PCI write (one exit, or none if the device is polling).
- The device processes many buffers, writes them to the used ring and raises **one interrupt**.
- Both sides can suppress notifications while busy, so under load there are very few exits per packet.

**Why emulated hardware is slow:** a real NIC driver performs many register reads and writes per packet; each is an MMIO exit costing microseconds. Virtio was designed for virtualization, so it needs very few.

**Making it faster still**

- **ioeventfd:** the guest's kick write is turned into an eventfd signal inside KVM, without returning to QEMU's vCPU thread.
- **irqfd:** the device raises the guest interrupt by writing an eventfd that KVM injects directly.
- **vhost:** the data path runs in a host kernel thread (`vhost-net`) or another process (**vhost-user**, e.g. with DPDK), so packets do not go through QEMU at all.
- **vDPA:** real hardware that speaks the virtio ring format, so the guest's virtio driver drives hardware directly.

**Transports:** virtio-pci on PC-like machines and the ARM `virt` PCIe bus, **virtio-mmio** on simple embedded boards (described in the device tree), and virtio-ccw on s390.

**Embedded and automotive:** virtio is the basis of the VirtIO-based sharing of GPUs, audio, cameras and sensors between VMs in automotive hypervisors, standardised so the same guest drivers work on different hypervisors.

### How does hardware virtualization on x86 compare with ARM? {H}
**Short answer:** Both run the guest kernel natively and trap sensitive operations, but they are structured differently. x86 (Intel VT-x, AMD-V) adds a separate "root" mode with a hardware-managed control structure (VMCS/VMCB) and special `VMLAUNCH`/`VMRESUME`/`VMEXIT` transitions that save and load most state automatically. ARM adds a privilege level (EL2) with its own registers; the hypervisor saves and restores guest state itself, which is more work per switch but gives finer control and is simpler hardware.

| | Intel VT-x / AMD-V | ARMv8 virtualization |
|---|---|---|
| Hypervisor mode | VMX root mode (all rings exist in both root and non-root) | separate exception level EL2 |
| Guest state | in the VMCS (Intel) / VMCB (AMD), loaded by hardware on VM entry | saved/restored by software in EL2 |
| Enter guest | `VMLAUNCH`/`VMRESUME` (`VMRUN` on AMD) | `ERET` from EL2 |
| Exit info | exit reason field in VMCS | `ESR_EL2`, `FAR_EL2`, `HPFAR_EL2` |
| Second-stage paging | EPT (Intel), NPT (AMD) | stage-2 translation, `VTTBR_EL2` |
| Interrupts | APICv / AVIC, posted interrupts | GIC virtual CPU interface, List Registers, GICv4 direct injection |
| Host kernel in hypervisor mode | host runs in root mode ring 0 | VHE (ARMv8.1) lets the host kernel run at EL2 |
| I/O MMU | VT-d / AMD-Vi | SMMU (stage 2) |

**x86 boot in QEMU, briefly:** the `pc` machine loads SeaBIOS or OVMF (UEFI) at the top of the 4 GB space; the vCPU starts in 16-bit real mode at `0xFFFFFFF0`; firmware initialises devices, then loads a bootloader from disk, which loads the kernel. ARM `virt` can boot the kernel directly or via UEFI.

**Why it matters:** if you know one architecture, interviewers often check whether you can map the concepts to the other. The common ideas are the same: trap-and-emulate for privileged operations, a second level of address translation, virtual interrupts, and paravirtual I/O.

### What is device passthrough (VFIO) and when would you use it? {H}
**Short answer:** Passthrough gives a VM direct, exclusive access to a real hardware device (a PCIe NIC, GPU or an SoC peripheral). The host's **VFIO** framework hands the device's registers and interrupts to user space (QEMU), which maps them into the guest, and the **IOMMU/SMMU** restricts the device's DMA to that guest's memory. The guest's normal driver then talks to the hardware at near-native speed.

**How it works**

1. Unbind the device from its host driver and bind it to `vfio-pci` (or `vfio-platform` for SoC devices).
2. QEMU opens the device's VFIO group/container (or the newer iommufd), maps the device's BARs (registers) into guest physical space so accesses do not exit, and programs the IOMMU so the device's DMA addresses are the guest's physical addresses.
3. Device interrupts (MSI/MSI-X) are delivered to the guest through irqfd, or directly with GICv4 / posted interrupts.

```bash
qemu-system-aarch64 ... -device vfio-pci,host=0000:01:00.0
```

**Requirements:** an IOMMU/SMMU, and devices that can be isolated in their own IOMMU group (devices behind the same PCIe bridge without ACS may have to be passed through together).

**Trade-offs**

| | Passthrough | virtio / emulated |
|---|---|---|
| Performance | near native | good (virtio) to slow (emulated) |
| Sharing | one VM owns the device (unless SR-IOV) | many VMs share |
| Live migration | hard (device state is in hardware) | supported |
| Isolation | depends on IOMMU and device reset quality | hypervisor controls everything |

**SR-IOV:** a PCIe device presents several **virtual functions** (VFs), each passed through to a different VM, which gives near-native I/O with sharing (common for NICs in cloud servers).

**Embedded use:** on automotive SoCs, a display controller, camera or CAN controller is often passed through to the VM that owns it (e.g. the safety cluster VM gets the display it must drive), while less critical devices are shared with virtio.
