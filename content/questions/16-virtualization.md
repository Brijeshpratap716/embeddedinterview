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

### Explain full QEMU flow in brief, with all functions for ARM SoC i.MX8 on x86 {H}
When you run an **ARM-based i.MX8 SoC on an x86 laptop using QEMU**, QEMU uses **TCG (Tiny Code Generator)** to dynamically translate ARM instructions into x86 instructions.

KVM cannot accelerate ARM guest CPU execution on an x86 host because the guest and host CPU architectures are different.

#### 1. Complete QEMU architecture

```text
Guest applications (ARM64 applications)
    ↓
Guest operating system (ARM Linux kernel and device drivers)
    ↓
Virtual i.MX8 hardware (Cortex-A CPU, GIC, UART, RAM, I2C)
    ↓
QEMU (TCG, softMMU, device emulation)
    ↓
Host operating system (Linux / Windows)
    ↓
Physical x86 hardware (CPU, RAM, storage)
```

#### 2. QEMU initialization flow

```text
main()
  └── qemu_init()
       ├── Module initialization
       ├── Command-line parsing
       ├── qemu_create_machine()
       ├── Accelerator initialization (TCG)
       ├── Board initialization
       ├── Device initialization
       └── System reset
  └── qemu_main_loop()
```

| Function | Purpose |
|---|---|
| `main()` | Entry point of QEMU. |
| `qemu_init()` | Initializes the QEMU environment. |
| `module_call_init()` | Registers machine, CPU and device types. |
| `qemu_create_machine()` | Creates the selected machine object. |
| `configure_accelerator()` | Selects and initializes TCG. |
| `machine_run_board_init()` | Initializes board-specific hardware models. |
| `qemu_system_reset()` | Resets the virtual system. |
| `qemu_main_loop()` | Handles timers, events and I/O. |

#### 3. i.MX8 SoC initialization

QEMU uses **QOM (QEMU Object Model)** to represent hardware components as software objects.

| Function | Purpose |
|---|---|
| `type_register_static()` | Registers a hardware object type. |
| `object_initialize_child()` | Creates embedded CPU or peripheral objects. |
| `qdev_realize()` | Initializes and activates a device. |
| `memory_region_init_ram()` | Allocates guest RAM. |
| `memory_region_init_io()` | Registers MMIO operations. |
| `memory_region_add_subregion()` | Maps memory into the guest physical address space. |
| `sysbus_mmio_map()` | Maps peripheral registers. |
| `sysbus_connect_irq()` | Connects peripheral interrupts to the interrupt controller. |
| `arm_load_kernel()` | Prepares the ARM kernel boot environment. |
| `qemu_init_vcpu()` | Initializes virtual CPU execution. |

The emulated SoC can contain Cortex-A cores, DDR, UART, GIC, GPIO, I2C and other supported peripherals.

#### 4. Virtual CPU execution flow

Each virtual CPU can execute in a separate host thread using multi-threaded TCG.

```text
qemu_init_vcpu()
    ↓
mttcg_start_vcpu_thread()
    ↓
mttcg_cpu_thread_fn()
    ↓
tcg_cpu_exec()
    ↓
cpu_exec()
    ↓
cpu_exec_loop()
    ↓
Translation Block lookup
    ↓
Execute or generate TB
```

| Function | Purpose |
|---|---|
| `mttcg_start_vcpu_thread()` | Creates a host thread for the virtual CPU. |
| `tcg_cpu_exec()` | Starts TCG CPU execution. |
| `cpu_exec()` | Manages guest CPU execution and exceptions. |
| `cpu_exec_loop()` | Repeatedly executes translation blocks. |
| `tb_lookup()` | Searches for previously translated code. |
| `tb_gen_code()` | Generates a new translation block if required. |

#### 5. TCG instruction translation

This is the most important part when running ARM on x86.

```text
ARM64 instructions (ADD X0, X1, X2)
    ↓
ARM frontend / decoder (Decode ARM instructions)
    ↓
TCG intermediate representation (add_i64 t0, t1, t2)
    ↓
TCG optimization (Optimize intermediate operations)
    ↓
x86 backend (Generate native x86 machine code)
    ↓
Physical x86 CPU (Execute translated instructions)
```

**Function flow**

```text
tb_gen_code()
    ↓
gen_intermediate_code()
    ↓
translator_loop()
    ↓
aarch64_tr_translate_insn()
    ↓
ARM instruction decoding
    ↓
tcg_gen_*()
    ↓
tcg_gen_code()
    ↓
x86 machine code generation
```

| Function | Purpose |
|---|---|
| `tb_gen_code()` | Generates a translation block. |
| `gen_intermediate_code()` | Starts guest instruction translation. |
| `translator_loop()` | Iterates through guest instructions. |
| `aarch64_tr_translate_insn()` | Translates ARM64 instructions. |
| `tcg_gen_add_i64()` | Generates an intermediate addition operation. |
| `tcg_optimize()` | Optimizes intermediate operations. |
| `tcg_gen_code()` | Generates native host machine code. |
| `tcg_out_*()` | Backend functions emitting host instructions. |

#### 6. Translation Block (TB) execution

A Translation Block is a sequence of guest instructions translated into host machine code.

```text
cpu_exec_loop()
       ↓
   TB lookup
       ↓
  TB available?
    /       \
  Yes        No
   |         |
   |    tb_gen_code()
   |         |
   └────┬────┘
        ↓
cpu_loop_exec_tb()
        ↓
cpu_tb_exec()
        ↓
tcg_qemu_tb_exec()
        ↓
Physical x86 CPU
```

The translated code is cached so QEMU does not need to translate the same instructions repeatedly. TB chaining further reduces execution overhead.

#### 7. Memory management (SoftMMU)

The guest ARM MMU is also emulated in software.

```text
Guest virtual address
    ↓ QEMU SoftMMU / TLB
Guest physical address
    ↓ QEMU memory mapping
Host virtual address
    ↓ Host MMU
Host physical address
```

| Function | Purpose |
|---|---|
| `tcg_gen_qemu_ld_i64()` | Generates a guest memory load. |
| `tcg_gen_qemu_st_i64()` | Generates a guest memory store. |
| `arm_cpu_tlb_fill()` | Handles ARM TLB misses in applicable QEMU versions. |
| `get_phys_addr()` | Performs ARM address translation. |
| `tlb_set_page()` | Updates the software TLB. |
| `address_space_read()` | Reads an address space. |
| `address_space_write()` | Writes to an address space. |

QEMU maintains a software TLB to avoid repeatedly walking guest page tables.

#### 8. Peripheral emulation (MMIO)

Suppose the guest Linux UART driver writes to a UART register.

```c
writel('A', uart_base + TX_REG);
```

The execution flow is approximately:

```text
Guest UART driver
    ↓
ARM STR instruction
    ↓
TCG translated store
    ↓
SoftMMU / MMIO dispatch
    ↓
memory_region_dispatch_write()
    ↓
i.MX UART write callback
    ↓
qemu_chr_fe_write_all()
    ↓
Host terminal
```

QEMU registers peripheral read/write callbacks using a `MemoryRegionOps` structure.

```c
static const MemoryRegionOps uart_ops = {
    .read  = uart_read,
    .write = uart_write,
};
```

Therefore, accessing a hardware register inside the guest ultimately invokes a software function in QEMU.

#### 9. Interrupt handling flow

Example: UART receives data from the host.

```text
Host keyboard input
    ↓
QEMU UART receive callback
    ↓
Update virtual UART registers
    ↓
qemu_set_irq()
    ↓
Virtual GIC
    ↓
cpu_interrupt()
    ↓
arm_cpu_exec_interrupt()
    ↓
ARM exception handling
    ↓
Guest Linux UART ISR
```

| Function | Purpose |
|---|---|
| `qemu_set_irq()` | Asserts or deasserts a virtual interrupt. |
| `cpu_interrupt()` | Signals an interrupt to the virtual CPU. |
| `cpu_handle_interrupt()` | Checks pending CPU interrupts. |
| `arm_cpu_exec_interrupt()` | Handles ARM-specific interrupts. |
| `arm_cpu_do_interrupt()` | Performs ARM exception entry. |

#### 10. QEMU main event loop

```text
qemu_main_loop()
    ↓
main_loop_wait()
    ↓
Host I/O polling
    ↓
Timer callbacks
    ↓
Device callbacks
    ↓
Interrupt generation
```

The main event loop handles asynchronous I/O, timers, networking, storage and peripheral events alongside vCPU execution.

#### 11. Running i.MX8 on an x86 machine

For example, using direct kernel boot on a supported i.MX8M Plus model:

```bash
qemu-system-aarch64 \
    -M imx8mp-evk \
    -accel tcg \
    -smp 4 \
    -m 3G \
    -kernel Image \
    -dtb imx8mp-evk.dtb \
    -display none \
    -serial null \
    -serial stdio \
    -append "console=ttymxc1"
```

A compatible root filesystem must also be supplied for a complete Linux boot.

**Note:** Upstream QEMU supports i.MX8M Plus and i.MX8M Mini machine models. For i.MX8 QM/QXP, you may need a custom machine implementation. The function names and exact call hierarchy above are representative and may vary between QEMU versions.

#### 12. Important QEMU source files

| Source file | Responsibility |
|---|---|
| `system/vl.c` | System initialization |
| `hw/arm/` | ARM board and SoC models |
| `hw/arm/fsl-imx8mp.c` | i.MX8M Plus SoC |
| `target/arm/tcg/translate-a64.c` | ARM64 translation |
| `target/arm/ptw.c` | ARM page-table walking |
| `accel/tcg/cpu-exec.c` | CPU execution loop |
| `accel/tcg/translate-all.c` | Translation block generation |
| `accel/tcg/translator.c` | Generic instruction translation |
| `accel/tcg/cputlb.c` | SoftMMU and TLB |
| `tcg/tcg.c` | TCG code generation |
| `tcg/i386/` | x86 code-generation backend |
| `system/memory.c` | Memory and MMIO management |
| `hw/char/imx_serial.c` | i.MX UART emulation |
| `hw/intc/` | Interrupt controller emulation |

#### 13. Interview-ready summary

QEMU creates a virtual i.MX8 SoC using QOM and initializes its CPU, memory and peripherals. Since the guest is ARM and the host is x86, it uses TCG instead of KVM.

TCG decodes ARM instructions, converts them into intermediate operations, optimizes them and generates native x86 machine code. The translated instructions are cached as Translation Blocks.

SoftMMU handles guest memory translation, MMIO callbacks emulate peripheral operations, and the virtual GIC delivers interrupts to guest CPUs. The main event loop handles asynchronous I/O and timers.

**Remember this overall flow:**

```text
QEMU initialization
    ↓
Board and SoC creation
    ↓
CPU, RAM and peripheral initialization
    ↓
vCPU thread creation
    ↓
ARM instruction decoding
    ↓
TCG intermediate representation
    ↓
x86 code generation
    ↓
TB caching and execution
    ↓
Memory / MMIO / Interrupt handling
    ↓
Repeat
```

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
ARM virtualization provides interrupt and timer mechanisms that let guests receive virtual interrupts and measure time without direct ownership of physical hardware.

#### vGIC
A virtual GIC presents distributor/redistributor and CPU-interface behavior appropriate to the selected GIC version. The hypervisor or KVM tracks virtual pending/active interrupts and can use hardware list registers and maintenance interrupts where supported.

```text
Emulated device -> virtual IRQ -> vGIC -> guest ISR
```

#### Generic timer
Guests can use virtual counter/timer facilities. CNTVOFF_EL2 can offset the physical count to create a virtual time view. Timer expiration is presented as a virtual interrupt. Scheduling, migration and timer state require coordination.

**Interview takeaway:** Interrupt injection changes the guest's virtual interrupt state; it is not necessarily a physical IRQ delivery. vGIC implementation details depend on GIC version and accelerator.

### What is virtio, and why is it faster than emulating a real device? {M}
Virtio is a standardized paravirtualized device interface. Instead of reproducing every register of a physical device, the guest and backend exchange descriptors through shared virtqueues.

```text
Guest driver -> descriptor/available queue -> backend
Guest driver <- used/completion queue       <- backend
              notification / interrupt
```

With a split virtqueue, the driver supplies buffers through descriptor and available rings; the device posts completion through the used ring. Packed virtqueues use a different layout. Feature negotiation selects supported behavior.

Virtio can reduce costly traps, register emulation and copies through batching and optimized backends such as vhost.

**Interview takeaway:** Virtio improves efficiency through a virtualization-aware interface, but does not guarantee zero-copy or zero exits. Correct memory barriers, buffer ownership and DMA mapping remain necessary.

### How does hardware virtualization on x86 compare with ARM? {H}
Both x86 and ARM implement hardware-assisted guest execution, address-translation isolation and trap mechanisms, but use different architectural interfaces.

| x86 | ARMv8-A |
|---|---|
| Intel VMX / AMD SVM | EL2 virtualization |
| VMCS / VMCB control state | EL2 control registers |
| EPT / NPT second-level translation | Stage-2 translation |
| APIC virtualization | vGIC |
| VM entry / VM exit | Guest entry via exception return and traps to EL2 |

A guest OS can run its own kernel privilege level without gaining host control. On both architectures, many normal instructions execute natively and selected sensitive operations trap.

**Interview takeaway:** The concepts map across architectures, not the register names or exception model. KVM provides a common VM API with architecture-specific initialization.

### What is device passthrough (VFIO) and when would you use it? {H}
Device passthrough assigns a physical device or function to a guest so the guest driver can operate it directly. VFIO is a Linux framework for secure userspace device access, commonly using an IOMMU.

```text
Guest driver -> assigned device
                    | DMA
                    v
             IOMMU mappings -> permitted guest RAM
```

The host must release the device from its normal driver, configure isolation and expose resources/interrupts through the VMM. IOMMU grouping and reset capabilities constrain assignment; newer VFIO interfaces may use IOMMUFD.

#### Trade-offs
Passthrough can reduce emulation overhead and provide native hardware features. It reduces sharing and migration flexibility and may introduce reset and security constraints.

**Interview takeaway:** An IOMMU limits device DMA to authorized memory. Do not use unsafe no-IOMMU assignment as a substitute for isolation in untrusted environments.

