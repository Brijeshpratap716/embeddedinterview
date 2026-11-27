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
QEMU represents guest-visible memory as a hierarchy of MemoryRegion objects, viewed through an AddressSpace.

| Region | Purpose |
|---|---|
| RAM | Backed by host memory |
| ROM | Read-only guest-visible storage |
| MMIO | Read/write callbacks |
| Alias | Another view of a region |
| Container | Organizes subregions |

```c
static const MemoryRegionOps ops = {
    .read = my_read,
    .write = my_write,
    .endianness = DEVICE_LITTLE_ENDIAN,
};
/* In device initialization: */
memory_region_init_io(&s->mmio, OBJECT(s), &ops,
                      s, "my-mmio", 0x1000);
sysbus_init_mmio(SYS_BUS_DEVICE(s), &s->mmio);
```

Board code maps the region at a guest physical address. A guest load/store to that address dispatches to the corresponding callback with offset, size and value.

**Interview takeaway:** A guest physical address is not a host pointer. Address spaces and translation also matter for DMA and IOMMUs. Respect access width, alignment and side effects.

### How does QEMU use KVM? Explain the ioctl sequence and the run loop. {H}
KVM exposes virtualization through file descriptors and ioctls. QEMU manages the machine and devices while KVM runs compatible guest CPU code.

#### Representative sequence
```text
open("/dev/kvm")
 -> KVM_GET_API_VERSION / KVM_CHECK_EXTENSION
 -> KVM_CREATE_VM
 -> KVM_SET_USER_MEMORY_REGION
 -> KVM_CREATE_VCPU
 -> mmap shared struct kvm_run
 -> architecture-specific CPU initialization
 -> KVM_RUN loop
```

On ARM64, initialization uses ARM-specific ioctls and register interfaces, including KVM_ARM_VCPU_INIT and KVM_SET_ONE_REG as applicable. On x86 the setup differs.

```c
for (;;) {
    if (ioctl(vcpu_fd, KVM_RUN, 0) < 0) {
        if (errno == EINTR) continue;
        break;
    }
    switch (run->exit_reason) {
    case KVM_EXIT_MMIO: /* emulate access */ break;
    case KVM_EXIT_HLT:  /* handle idle */ break;
    default:           /* handle other exit */ break;
    }
}
```
Illustrative only: QEMU has more complete event handling and not all hardware exits return to userspace.

**Interview takeaway:** KVM_RUN enters guest execution; the kernel handles many traps internally and reports selected exits to the VMM.

### What causes a VM exit on ARM, and how is an MMIO access handled? {H}
An ARM guest exits to EL2 when a configured trap or virtualization-related exception occurs. Examples include stage-2 translation faults, trapped system-register accesses, hypercalls and physical interrupts.

#### MMIO example
```text
Guest LDR/STR -> stage-1 VA to IPA
             -> stage-2 fault for emulated MMIO
             -> EL2/KVM handles abort
             -> KVM_EXIT_MMIO to QEMU if needed
             -> device callback reads/writes register
             -> KVM_RUN resumes guest
```

KVM decodes or otherwise handles supported accesses and provides address, direction, size and data to userspace where required. QEMU dispatches to the mapped device region; read results are supplied back before re-entry.

**Interview takeaway:** Not every guest exception is a VM exit, and not every exit requires QEMU. Guest system calls normally stay within the guest EL0/EL1 relationship.

### What is two-stage address translation (stage 2, IPA)? {H}
ARM virtualization uses two stages of translation so a guest can manage its own address space without controlling host physical memory.

```text
Guest virtual address
    | stage 1: guest page tables (TTBR)
    v
Intermediate physical address (IPA)
    | stage 2: hypervisor page tables (VTTBR_EL2)
    v
Host physical address (PA)
```

For example, guest VA 0x4000 may translate to IPA 0x80004000, which stage 2 maps to a host RAM page. Stage-2 permissions constrain the guest regardless of stage-1 permissions. A stage-2 fault can signal an unmapped page or emulated MMIO region.

TLBs may cache combined translations tagged by ASID and VMID. Hypervisors must invalidate relevant cached entries when mappings change.

**Interview takeaway:** The guest believes IPA is physical memory. Stage 2 provides isolation; it does not mean every access requires two full page-table walks.

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
