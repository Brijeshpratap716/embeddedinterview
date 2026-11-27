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
Emulation reproduces the behavior of a guest machine in software. Hardware-assisted virtualization executes compatible guest instructions directly on the host CPU while isolating the guest and intercepting selected operations.

| QEMU TCG | QEMU + KVM |
|---|---|
| Translates guest instructions into host instructions | Guest code normally executes natively |
| Supports cross-ISA execution | Requires compatible host and guest ISA |
| Can model CPUs, memory and peripherals | Uses kernel virtualization and QEMU device models |
| Higher CPU execution overhead | Usually much lower CPU execution overhead |

#### Example
An ARM64 i.MX8 guest on an x86-64 laptop needs TCG for CPU execution. An ARM64 guest on an ARM64 Linux host with virtualization support can use KVM, provided the machine and guest configuration are compatible.

**Interview takeaway:** QEMU is a machine emulator and VMM. TCG and KVM are alternative CPU execution accelerators; both may use software device models.

### What is a hypervisor, and what is the difference between type 1 and type 2? {E}
A hypervisor controls execution and resource isolation for multiple virtual machines.

```text
Type 1: Hardware -> Hypervisor -> Guest VMs
Type 2: Hardware -> Host OS -> Hosted VMM -> Guest VMs
```

A bare-metal hypervisor owns hardware resource management directly. A hosted virtualization product relies on a host OS for services such as scheduling, file I/O and device access.

#### KVM nuance
Linux KVM adds virtualization functionality to the host kernel. QEMU runs in userspace and uses KVM ioctls to create and run guests. It is often classified as a type-1 hypervisor because guest execution is managed by kernel/hardware virtualization, although the system has a general-purpose host OS.

**Interview takeaway:** Explain the architecture rather than forcing every product into a rigid type-1/type-2 label.

### What are the ARMv8 exception levels, and how does virtualization use EL2? {M}
ARMv8-A defines exception levels that represent privilege and exception-handling contexts.

| Level | Typical role |
|---|---|
| EL0 | Applications |
| EL1 | OS kernel |
| EL2 | Hypervisor |
| EL3 | Secure monitor, when implemented |

```text
Guest application EL0
Guest kernel      EL1
       | trap / exception
Hypervisor       EL2
       | ERET
Guest resumes
```

EL2 controls guest execution through registers such as HCR_EL2 and stage-2 translation configuration. Guest accesses or instructions configured to trap are handled by the hypervisor. The guest kernel still runs its own stage-1 translation and handles ordinary guest system calls.

**Interview takeaway:** Exception levels are not security states. Secure/Non-secure state and EL are separate concepts, and VHE can allow the host kernel to run at EL2.

### What happens in QEMU when you start a virtual machine? Explain the code flow. {H}
QEMU builds a virtual machine from a machine model, CPU objects, memory regions, buses and devices, then starts vCPU execution.

#### Representative system-emulation flow
```text
main / qemu_init
 -> parse options and select MachineClass
 -> instantiate machine and configure accelerator
 -> machine initialization / device realization
 -> allocate RAM and map MMIO
 -> load firmware or kernel, set reset state
 -> start vCPU threads
 -> run main event loop and device callbacks
```

For KVM, initialization opens /dev/kvm and creates VM and vCPU fds. A vCPU thread calls KVM_RUN. For TCG, the CPU execution loop finds or translates guest translation blocks and executes generated host code. Timers, I/O and interrupts coordinate with the event loop and vCPU threads.

#### Source navigation
Start with system/vl.c (or the corresponding startup code in the checked-out version), hw/arm/virt.c for the ARM virt machine, accel/tcg for TCG and accel/kvm for KVM. Exact helper names and locations vary by QEMU release.

**Interview takeaway:** Separate machine realization, vCPU execution and device/event processing. Starting QEMU does not automatically reproduce every physical SoC.

### How does QEMU's TCG translate and run guest code? {H}
TCG (Tiny Code Generator) is QEMU's dynamic binary translation engine. It converts guest instructions into intermediate operations and then native host instructions.

```text
Guest PC -> TB lookup
             | miss
             v
Guest decoder -> TCG IR -> optimize/lower -> host code
             |
             v
Translation cache -> execute TB -> next guest PC
```

A translation block (TB) represents a sequence of guest instructions under relevant CPU-state assumptions. QEMU caches TBs and can chain compatible blocks to reduce dispatcher overhead. Guest memory accesses use generated fast paths or helpers; exceptions, MMIO and interrupt checks can return control to the execution loop.

#### Example
For ARM64 on x86-64, an ARM ADD instruction becomes TCG operations that are lowered to host arithmetic and register-state updates. Privileged operations may call C helpers.

**Interview takeaway:** TCG translates blocks on demand, not an entire guest binary in advance. Self-modifying code and mapping changes require appropriate TB invalidation.

### How do you use QEMU to run and debug an ARM64 Linux kernel? {M}
Use QEMU's ARM virt machine for generic ARM64 Linux development. The kernel must support its virtual interrupt controller, timer, UART and storage configuration.

```bash
qemu-system-aarch64 -machine virt -cpu cortex-a57 \
  -m 1024 -smp 2 -nographic \
  -kernel Image -initrd rootfs.cpio.gz \
  -append "console=ttyAMA0 rdinit=/init nokaslr" \
  -S -gdb tcp::1234
```

Assume a suitable ARM64 kernel Image and initramfs containing /init. On an x86 host use TCG; on compatible ARM hardware configure KVM if desired.

```gdb
file vmlinux
target remote localhost:1234
break start_kernel
continue
```

Keep matching debug symbols and account for early MMU mappings; an early breakpoint may require a physical address.

**Interview takeaway:** The virt machine is not i.MX8. Board-specific firmware and drivers require the relevant machine/device models, or real hardware. QEMU cannot validate undocumented electrical behavior.

### What is the QEMU Object Model (QOM), and how is a device model added? {H}
QOM (QEMU Object Model) provides object types, inheritance, properties and lifecycle management for QEMU components. qdev builds device-model infrastructure on it.

#### Device-model workflow
1. Define a type and state structure derived from DeviceState or SysBusDevice.
2. Register TypeInfo with parent type, instance size and class initialization.
3. Initialize MMIO regions, IRQs and properties.
4. Realize the device, map resources through the board model and connect interrupt lines.
5. Implement reset, migration state and error handling when applicable.

```text
Machine -> sysbus device
           |-- MemoryRegion callbacks
           |-- IRQ output
           +-- internal device state
```

For an emulated UART, a write to its transmit register invokes a MemoryRegion callback, updates state and sends a character through the configured backend.

**Interview takeaway:** Model guest-visible register semantics, timing and interrupts rather than merely returning values. QOM object creation and device realization are distinct stages.

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
