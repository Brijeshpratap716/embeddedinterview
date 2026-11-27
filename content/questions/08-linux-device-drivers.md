---
slug: linux-device-drivers
title: Linux Kernel & Device Drivers
icon: 🐧
level: Advanced
order: 8
desc: Kernel modules, char drivers with ioctl, the driver model, device tree, I2C/SPI client drivers, GPIO/pinctrl/clocks, interrupts, bottom halves, locking, wait queues, timers, memory, DMA, mmap, power management, PREEMPT_RT, debugging and DRM.
---
For Linux BSP and driver roles, expect questions on kernel internals, how drivers bind to hardware, and concurrency in the kernel. Answers refer to recent mainline kernels (6.x). Each answer gives a short version first, then details, code and the follow-ups interviewers ask.

### What is the difference between kernel space and user space? {E}
Linux separates application execution from privileged kernel execution to protect system resources and isolate processes.

| User space | Kernel space |
|---|---|
| Restricted CPU privilege | Privileged kernel execution |
| Process-specific virtual memory mappings | Kernel mappings and hardware access |
| Applications and libraries | Scheduler, memory manager, filesystems, drivers |
| Fault often terminates a process | Fault may compromise the entire system |

#### 1. System-call flow

```text
Application: read(fd, buf, n)
       |
libc / architecture syscall ABI
       |
CPU exception into kernel
       |
VFS / driver callback
       |
Copy result to user buffer and return
```

On ARM64 Linux, an ordinary system call uses SVC from EL0 and normally enters EL1 kernel code. Hypervisor configurations can affect the host kernel's exception level.

#### 2. Memory access

A user pointer refers to an address in a process's virtual address space. Kernel code must use the appropriate uaccess helpers and validate lengths, not assume that a user-provided address is an ordinary kernel pointer.

**Interview takeaway:** User/kernel separation is enforced by processor privilege and memory protection. System calls provide controlled entry; applications cannot directly invoke arbitrary privileged kernel functions.

### What is a loadable kernel module? {E}
A loadable kernel module (LKM) is compiled kernel code that can be linked into a running Linux kernel at runtime when module loading is enabled.

#### 1. Minimal module

```c
#include <linux/module.h>
#include <linux/init.h>

static int __init demo_init(void)
{
    pr_info("demo loaded\n");
    return 0;
}

static void __exit demo_exit(void)
{
    pr_info("demo unloaded\n");
}

module_init(demo_init);
module_exit(demo_exit);
MODULE_LICENSE("GPL");
```

Build it against the matching kernel build environment. Loading invokes demo_init; unloading invokes demo_exit when permitted.

#### 2. Important constraints

A module executes with kernel privileges. Kernel ABI/configuration, exported symbols, module signature policy and reference counts affect loading and unloading. Linux does not promise a stable internal driver ABI across releases.

#### 3. Debugging

```sh
lsmod
modinfo demo.ko
dmesg
```

Use logs and module metadata to diagnose missing symbols, version mismatch or signature rejection.

**Interview takeaway:** Modules extend the running kernel, not user space. They must obey kernel context, memory and lifetime rules.

### What is the difference between insmod and modprobe? {E}
`insmod` inserts a specified module file directly. `modprobe` locates a module by name and uses the installed module dependency/configuration information to load it and its dependencies.

| insmod | modprobe |
|---|---|
| Takes a module file path | Normally takes module name |
| Does not automatically resolve dependencies | Loads required dependencies |
| Useful for a local test .ko | Preferred for installed modules |

#### 1. Examples

```sh
sudo insmod ./my_driver.ko
sudo modprobe my_driver
sudo modprobe -r my_driver
```

Unloading is possible only if permitted and no references prevent it.

#### 2. Module installation

Install modules for the running kernel under the correct module directory, then run depmod as appropriate to refresh module dependency metadata. modprobe can also apply configured module options, aliases and blacklist rules.

#### 3. Failure diagnosis

Check dmesg, modinfo and the running kernel release. A module may fail due to unresolved symbols, mismatched vermagic, signature enforcement or missing hardware dependencies.

**Interview takeaway:** insmod is a low-level direct insertion tool; modprobe is the normal dependency-aware module management interface.

### What are the types of device drivers in Linux? {E}
Linux drivers are organized into device classes and specialized kernel subsystems. Traditional categories include character, block and network drivers, but modern drivers often expose subsystem-specific interfaces.

| Category | Examples | Interface |
|---|---|---|
| Character | Serial, misc device | File operations |
| Block | eMMC, NVMe, storage | Block I/O requests |
| Network | Ethernet, Wi-Fi | net_device and network stack |
| Display | DRM/KMS | DRM objects, ioctls |
| Input | Touch, keyboard | Input subsystem events |
| Bus/other | I2C, SPI, GPIO, IIO | Subsystem APIs |

#### 1. Example

A touch controller connected through I2C is an I2C client driver, but it reports touch events through the input subsystem rather than inventing a custom character-device interface. Similarly, a display controller commonly registers DRM/KMS objects.

#### 2. Driver selection

Identify the hardware bus, then choose the subsystem matching the device's function. The bus manages discovery/binding and communication; the functional subsystem defines user/kernel interfaces and common behavior.

**Interview takeaway:** Do not build a custom char driver for every peripheral. Use the established Linux subsystem to obtain standard APIs, resource management and userspace compatibility.

### How do you write a character driver? {M}
A character driver exposes a device through a character-device file and registered file operations. A simple miscdevice is a convenient way to demonstrate the mechanism without manually allocating major/minor numbers.

#### 1. Minimal read-only driver

```c
#include <linux/module.h>
#include <linux/fs.h>
#include <linux/miscdevice.h>

static ssize_t demo_read(struct file *file, char __user *buf,
                         size_t count, loff_t *pos)
{
    static const char msg[] = "hello\n";
    return simple_read_from_buffer(buf, count, pos,
                                   msg, sizeof(msg) - 1);
}

static const struct file_operations demo_fops = {
    .owner = THIS_MODULE,
    .read = demo_read,
    .llseek = no_llseek,
};

static struct miscdevice demo_dev = {
    .minor = MISC_DYNAMIC_MINOR,
    .name = "demo_char",
    .fops = &demo_fops,
};

static int __init demo_init(void)
{
    return misc_register(&demo_dev);
}

static void __exit demo_exit(void)
{
    misc_deregister(&demo_dev);
}

module_init(demo_init);
module_exit(demo_exit);
MODULE_LICENSE("GPL");
```

With appropriate device-node management, read using:

```sh
cat /dev/demo_char
```

#### 2. Internal flow

```text
open/read --> system call --> VFS --> demo_fops.read
                                     |
                           copy data to userspace
```

The file offset prevents endless repeated data on sequential reads.

#### 3. Full cdev alternative

Use alloc_chrdev_region, cdev_init/cdev_add and the appropriate class/device APIs if the driver needs its own registered number range. Unwind every successful initialization step on failure.

**Interview takeaway:** File operations are callbacks, not direct userspace calls. Validate user requests, manage device lifetime and handle concurrency before adding real hardware access.

### How do you implement ioctl in a character driver, with a complete example? {H}
ioctl provides device-specific control commands that do not fit ordinary read/write semantics. The userspace and kernel sides share a command definition and a stable data layout.

#### 1. Shared UAPI header (demo_ioctl.h)

```c
#ifndef DEMO_IOCTL_H
#define DEMO_IOCTL_H
#include <linux/ioctl.h>
#include <linux/types.h>

#define DEMO_GET _IOR('D', 0, __u32)
#define DEMO_SET _IOW('D', 1, __u32)
#endif
```

Direction is defined from the userspace perspective. Fixed-width UAPI fields avoid dependence on native long or pointer size.

#### 2. Kernel misc-device implementation

```c
#include <linux/module.h>
#include <linux/fs.h>
#include <linux/miscdevice.h>
#include <linux/uaccess.h>
#include <linux/compat.h>
#include <linux/mutex.h>
#include "demo_ioctl.h"

static DEFINE_MUTEX(value_lock);
static __u32 value;

static long demo_ioctl(struct file *file, unsigned int cmd,
                       unsigned long arg)
{
    __u32 tmp;
    void __user *p = (void __user *)arg;

    switch (cmd) {
    case DEMO_GET:
        mutex_lock(&value_lock);
        tmp = value;
        mutex_unlock(&value_lock);
        return copy_to_user(p, &tmp, sizeof tmp) ?
               -EFAULT : 0;

    case DEMO_SET:
        if (copy_from_user(&tmp, p, sizeof tmp))
            return -EFAULT;
        if (tmp > 1000)
            return -EINVAL;
        mutex_lock(&value_lock);
        value = tmp;
        mutex_unlock(&value_lock);
        return 0;

    default:
        return -ENOTTY;
    }
}

static const struct file_operations fops = {
    .owner = THIS_MODULE,
    .unlocked_ioctl = demo_ioctl,
#ifdef CONFIG_COMPAT
    .compat_ioctl = compat_ptr_ioctl,
#endif
};

static struct miscdevice dev = {
    .minor = MISC_DYNAMIC_MINOR,
    .name = "demo_ioctl",
    .fops = &fops,
};

static int __init demo_init(void)
{
    return misc_register(&dev);
}

static void __exit demo_exit(void)
{
    misc_deregister(&dev);
}

module_init(demo_init);
module_exit(demo_exit);
MODULE_LICENSE("GPL");
```

The compat helper is suitable here because both commands use pointers to the same fixed-size layout on native and compat ABIs. Kernel API availability depends on the target version.

#### 3. Userspace program

```c
#include <fcntl.h>
#include <stdio.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include "demo_ioctl.h"

int main(void)
{
    int fd = open("/dev/demo_ioctl", O_RDWR);
    __u32 v = 42;
    if (fd < 0)
        return 1;
    if (ioctl(fd, DEMO_SET, &v) < 0 ||
        ioctl(fd, DEMO_GET, &v) < 0) {
        perror("ioctl");
        close(fd);
        return 1;
    }
    printf("%u\n", (unsigned)v);
    close(fd);
    return 0;
}
```

Expected output: 42 after successful operations.

**Interview takeaway:** ioctl is a UAPI contract. Validate command, data and permissions, use uaccess helpers and maintain compatible layouts; never trust a userspace pointer.

### What are major and minor numbers? {E}
A Linux device number (dev_t) contains a major number and a minor number. The registered number range identifies a device interface, and the minor distinguishes instances within that range.

#### 1. Kernel helpers

```c
dev_t devno = MKDEV(major, minor);
unsigned int m = MAJOR(devno);
unsigned int n = MINOR(devno);
```

For a character driver, alloc_chrdev_region can dynamically allocate a device-number range. cdev_add associates a cdev with that range.

#### 2. Inspect a device node

```sh
ls -l /dev/ttyS0
cat /proc/devices
```

The character or block device node stores the major/minor pair. Opening it causes the kernel to locate the registered device operations.

#### 3. Example

A driver might reserve one range for four device instances. The minor determines which instance is opened; the driver may store its instance pointer in file->private_data after opening.

Modern systems commonly create nodes automatically through devtmpfs/udev or another device manager.

**Interview takeaway:** Major/minor numbers identify a device-number registration, not a physical MMIO address. Do not hardcode a major number when dynamic allocation is appropriate.

### Why use copy_to_user and copy_from_user instead of memcpy? {M}
`copy_to_user()` and `copy_from_user()` are Linux uaccess helpers for transferring bytes between kernel memory and user virtual addresses. Ordinary memcpy does not provide the required user-access handling.

#### 1. Driver example

```c
static long set_value(unsigned long arg)
{
    u32 value;
    if (copy_from_user(&value,
                       (void __user *)arg,
                       sizeof value))
        return -EFAULT;

    if (value > 100)
        return -EINVAL;

    return apply_value(value);
}
```

The copy functions return the number of bytes not copied, not a negative errno. Zero indicates complete success.

#### 2. Why special helpers are required

User addresses may be invalid, unmapped or faulting. Architecture mechanisms can restrict privileged access to user pages. Uaccess helpers provide the appropriate access checks, fault-handling and architecture-specific operations.

#### 3. Context restriction

Ordinary user copies may fault and sleep. Do not perform them under a raw spinlock or in hard IRQ/other atomic context. Copy data into a kernel buffer, validate it, then take the required lock for the actual update.

**Interview takeaway:** A user pointer is untrusted and potentially faulting. Use the correct uaccess API, validate copied data and interpret the residual-byte return correctly.

### What is the Linux device model (bus, device, driver)? {M}
The Linux device model represents hardware instances as devices, driver implementations as drivers and discovery/matching rules through buses. It provides a common binding and lifecycle framework.

#### 1. Binding flow

```text
Device registered (DT, ACPI, enumeration, board code)
                    |
Bus match logic <--- Driver registered
                    |
                 probe()
                    |
         Driver binds and registers interfaces
                    |
           remove / unbind when needed
```

A bus_type defines matching and related operations. A device carries resources and identity; a driver supplies callbacks.

#### 2. Example

An I2C target described by a device-tree node becomes an i2c_client. The I2C core matches its compatible string or supported ID against an i2c_driver. The driver's probe configures the target and registers its functional subsystem.

#### 3. Resources and lifetime

Drivers acquire clocks, regulators, IRQs, memory mappings and other resources during initialization. Probe failure must unwind safely; remove must stop external access and asynchronous work before resources disappear. Device references protect object lifetime.

**Interview takeaway:** Device, driver and bus are separate objects. The bus determines matching; probe initializes a specific bound instance.

### What is a platform device and platform driver? {M}
A platform device represents hardware that is not normally discovered through a self-enumerating bus like PCI or USB. Platform devices often describe SoC-integrated controllers using device tree or ACPI.

#### 1. Device-tree example

```dts
demo@40000000 {
    compatible = "vendor,demo";
    reg = <0x40000000 0x1000>;
};
```

The reg encoding must match the parent node's address/size cell configuration.

#### 2. Driver example

```c
static int demo_probe(struct platform_device *pdev)
{
    void __iomem *base;

    base = devm_platform_ioremap_resource(pdev, 0);
    if (IS_ERR(base))
        return PTR_ERR(base);

    platform_set_drvdata(pdev, base);
    return 0;
}

static const struct of_device_id demo_of_match[] = {
    { .compatible = "vendor,demo" },
    { }
};
MODULE_DEVICE_TABLE(of, demo_of_match);

static struct platform_driver demo_driver = {
    .probe = demo_probe,
    .driver = {
        .name = "demo",
        .of_match_table = demo_of_match,
    },
};
module_platform_driver(demo_driver);
```

This is a kernel module fragment requiring the relevant headers and license declaration. Real hardware initialization occurs in probe.

#### 3. Probe sequence

Firmware description creates a platform device, the platform bus matches the driver, and probe obtains resources. An unavailable dependency may require deferred probing.

**Interview takeaway:** A platform driver binds to platform-described hardware and obtains resources from the device model instead of assuming fixed physical addresses.

### How do you write an I2C (or SPI) client driver? {M}
An I2C or SPI client driver manages a peripheral connected to a controller bus. The bus core matches the device and calls the driver's probe function; the client then uses subsystem transfer APIs.

#### 1. I2C device tree

```dts
&i2c0 {
    status = "okay";
    sensor@50 {
        compatible = "vendor,sensor";
        reg = <0x50>;
    };
};
```

The reg value is the unshifted 7-bit address for this example.

#### 2. I2C client driver fragment

```c
static int sensor_probe(struct i2c_client *client)
{
    int id;

    if (!i2c_check_functionality(client->adapter,
                                 I2C_FUNC_SMBUS_BYTE_DATA))
        return -EOPNOTSUPP;

    id = i2c_smbus_read_byte_data(client, 0x00);
    if (id < 0)
        return id;
    if (id != EXPECTED_ID)
        return -ENODEV;

    return 0;
}

static const struct of_device_id sensor_match[] = {
    { .compatible = "vendor,sensor" },
    { }
};
MODULE_DEVICE_TABLE(of, sensor_match);

static struct i2c_driver sensor_driver = {
    .driver = {
        .name = "demo_sensor",
        .of_match_table = sensor_match,
    },
    .probe = sensor_probe,
};
module_i2c_driver(sensor_driver);
```

EXPECTED_ID and register offsets are device-specific. This uses a contemporary single-argument probe signature; adapt to the target kernel version.

#### 3. SPI alternative

Register a spi_driver with a match table. Use spi_sync or appropriate helpers to execute spi_message/spi_transfer operations, configuring mode, speed and bits per word according to the device. SPI normally identifies devices through chip selects.

#### 4. Functional subsystem

After successful probe, register the appropriate interface such as input, IIO, hwmon or DRM panel. Transfer functions commonly sleep; do not call them from hard IRQ context.

**Interview takeaway:** The controller driver operates the bus; the client driver understands the peripheral's register protocol and function.

### What is the device tree and why is it used? {M}
Device tree is a hierarchical hardware description supplied to the kernel, especially on embedded systems. It describes devices, addresses, interrupts and relationships without hardcoding every board's resources in drivers.

#### 1. Example

```dts
&i2c0 {
    status = "okay";

    touch@38 {
        compatible = "vendor,touch";
        reg = <0x38>;
        interrupt-parent = <&gpio1>;
        interrupts = <5 IRQ_TYPE_EDGE_FALLING>;
        reset-gpios = <&gpio1 7 GPIO_ACTIVE_LOW>;
    };
};
```

The actual property names and encodings must follow the device binding and parent controllers. The example uses standard GPIO/IRQ binding macros.

#### 2. Build and boot flow

```text
DTS + included DTSI files
         |
        dtc
         |
        DTB --> bootloader supplies blob to Linux
         |
OF/device model creates applicable devices
         |
Driver match using compatible --> probe
```

Device-tree source is compiled to a binary flattened device tree. Bindings define the required property format; schema checks help catch invalid descriptions.

#### 3. Driver access

Use platform resource APIs, of_property_read_* or more generic firmware-node APIs, GPIO descriptor interfaces and other subsystem helpers. Do not manually decode standard resources unnecessarily.

**Interview takeaway:** Device tree describes hardware and board wiring, not arbitrary procedural driver logic. The driver implements behavior; bindings define their contract.

### What are device tree overlays? {M}
A device-tree overlay is a set of changes applied to a base device tree. It can add nodes or update properties for hardware variants or expansion boards.

#### 1. Example overlay

```dts
/dts-v1/;
/plugin/;

&i2c0 {
    sensor@50 {
        compatible = "vendor,sensor";
        reg = <0x50>;
        status = "okay";
    };
};
```

This references a base-tree label. Symbol/fixup support and overlay application mechanism must match the platform.

#### 2. Flow

```text
Base DTB + compiled overlay (.dtbo)
                  |
          Overlay application
                  |
       Updated device-tree description
                  |
          Kernel device binding
```

A bootloader can apply an overlay before starting Linux. Some kernel/platform configurations also support runtime application.

#### 3. Limitations

Overlay removal is not a general-purpose safe hot-unplug mechanism. Drivers and devices must support the relevant lifetime operations. Conflicting addresses, GPIOs and resource ownership can cause failures.

**Interview takeaway:** An overlay modifies hardware description, not driver code. Validate bindings and resource conflicts, and use the platform's supported overlay lifecycle.

### What are the devm_ (managed) APIs? {M}
The devm_ APIs implement device-managed resource lifetime. Resources acquired through supported managed helpers are automatically released when the device is detached or a probe attempt fails.

#### 1. Example

```c
static int demo_probe(struct platform_device *pdev)
{
    struct device *dev = &pdev->dev;
    struct demo *d;

    d = devm_kzalloc(dev, sizeof *d, GFP_KERNEL);
    if (!d)
        return -ENOMEM;

    d->base = devm_platform_ioremap_resource(pdev, 0);
    if (IS_ERR(d->base))
        return PTR_ERR(d->base);

    platform_set_drvdata(pdev, d);
    return 0;
}
```

If the mapping fails, the managed allocation is automatically released during failed-probe cleanup.

#### 2. Common helpers

| API | Resource |
|---|---|
| devm_kzalloc | Zeroed memory |
| devm_request_threaded_irq | Interrupt registration |
| devm_gpiod_get | GPIO descriptor |
| devm_clk_get | Clock reference |
| devm_regulator_get | Regulator reference |

Acquiring a clock or regulator reference is not the same as enabling it. Enable/disable actions need matching management, through suitable managed helpers or explicit cleanup.

#### 3. Important limitation

Managed release does not automatically stop hardware DMA, cancel arbitrary workqueues or make open userspace handles safe. Quiesce asynchronous activity before resources are released. devm_add_action_or_reset can register custom cleanup.

**Interview takeaway:** devm simplifies cleanup, but resource dependencies and asynchronous device lifetime still require explicit design.

### What is pinctrl, and how do GPIO, clock and regulator frameworks work in drivers? {M}
Linux drivers use common resource frameworks to configure board pins, control GPIO signals, enable clocks and manage power supplies.

#### 1. Resource roles

| Framework | Purpose |
|---|---|
| pinctrl | Select pin multiplexing and electrical settings |
| GPIO descriptor | Control or read a GPIO using logical active state |
| Clock | Get/enable/configure a clock |
| Regulator | Manage a device power supply |

#### 2. Probe example

```c
reset = devm_gpiod_get(dev, "reset", GPIOD_OUT_HIGH);
if (IS_ERR(reset))
    return dev_err_probe(dev, PTR_ERR(reset),
                         "reset GPIO unavailable\n");

clk = devm_clk_get(dev, NULL);
if (IS_ERR(clk))
    return dev_err_probe(dev, PTR_ERR(clk),
                         "clock unavailable\n");

ret = clk_prepare_enable(clk);
if (ret)
    return ret;
```

A real driver must disable/unprepare the clock when appropriate, including later failure paths. GPIOD_OUT_HIGH represents logical active-high value 1; descriptor polarity handles active-low wiring.

#### 3. Bring-up sequence

Follow the device's timing requirements: configure pins, enable supplies and clocks, assert/deassert reset as specified, then access registers. Shutdown usually reverses required dependencies.

GPIO access may sleep if the controller is behind a sleeping bus; use gpiod_set_value_cansleep in an appropriate context when required.

**Interview takeaway:** These frameworks abstract resource ownership and board-specific wiring. A successful get operation does not necessarily power or enable the resource.

### What is deferred probing (-EPROBE_DEFER)? {M}
Deferred probing occurs when a driver cannot initialize because a required supplier is not available yet. The driver returns -EPROBE_DEFER so the driver core can retry probing when appropriate.

#### 1. Example

```c
struct regulator *supply;

supply = devm_regulator_get(dev, "vdd");
if (IS_ERR(supply))
    return dev_err_probe(dev, PTR_ERR(supply),
                         "vdd supply unavailable\n");
```

If the regulator provider has not been bound, the resource API may return -EPROBE_DEFER. Preserve that error rather than converting it to -ENODEV.

#### 2. Dependency flow

```text
Consumer probe --> supplier unavailable --> -EPROBE_DEFER
Supplier driver becomes available
                  |
           driver core retries consumer
```

Modern driver-core supplier/device-link mechanisms can also influence when consumer probing is attempted.

#### 3. Debugging repeated deferral

Inspect kernel logs, device-tree phandles, enabled supplier drivers, power-domain/clock dependencies and, where available, the deferred-probe debugfs information. A missing or invalid provider can prevent successful binding indefinitely.

**Interview takeaway:** Deferred probe is not a normal retry loop inside probe. Return the actual dependency error, clean up the failed attempt and let the driver core manage retries.

### What are top halves and bottom halves? {M}
Linux interrupt handling often separates immediate work from deferred processing. The top half is the hard IRQ handler; bottom-half terminology refers to mechanisms that perform work later.

#### 1. Typical flow

```text
Device IRQ
    |
Hard IRQ: determine source, acknowledge, capture minimal state
    |
Schedule deferred work or wake IRQ thread
    |
Deferred context: process data / perform longer operation
```

The exact acknowledgement order depends on device interrupt behavior.

#### 2. Threaded IRQ example

```c
static irqreturn_t top(int irq, void *data)
{
    if (!my_irq_pending(data))
        return IRQ_NONE;

    return IRQ_WAKE_THREAD;
}

static irqreturn_t thread_fn(int irq, void *data)
{
    service_device(data);
    return IRQ_HANDLED;
}
```

Register with request_threaded_irq or a managed variant and appropriate flags. The hard handler must not perform a sleeping bus transaction to determine ownership.

#### 3. Context differences

Softirq/tasklet processing normally cannot sleep. Workqueue callbacks and threaded IRQ handlers generally run in schedulable context and may sleep subject to locking and API rules.

**Interview takeaway:** Minimize hard IRQ work and choose the deferred mechanism according to latency and sleeping requirements. Deferred processing is not one uniform execution context.

### What is the difference between a tasklet, a workqueue and a threaded IRQ? {H}
Tasklets, workqueues and threaded IRQ handlers defer work from interrupt handling, but have different context and lifetime semantics.

| Mechanism | Typical execution context | May sleep? |
|---|---|---|
| Tasklet | Softirq-related atomic context | No |
| Workqueue | Worker thread (ordinary workqueue) | Generally yes |
| Threaded IRQ | IRQ kernel thread | Generally yes |

Tasklets are a legacy mechanism; new driver designs often use threaded IRQs or workqueues when suitable.

#### 1. Workqueue example

```c
static void my_work(struct work_struct *work)
{
    struct demo *d = container_of(work, struct demo, work);
    process_device(d);
}
```

Initialize with INIT_WORK and queue the work using the appropriate workqueue API. Before freeing d, stop new work from being queued and cancel/flush existing work as required.

#### 2. Threaded IRQ example

Use devm_request_threaded_irq for a device whose interrupt requires an I2C register read or another sleeping operation. IRQF_ONESHOT may keep the interrupt masked while the threaded handler runs, when appropriate for the source and sharing rules.

#### 3. Choosing

Use a threaded IRQ for interrupt-driven work closely tied to a device. Use a workqueue for general asynchronous processing. Special workqueue types such as BH workqueues have different context constraints.

**Interview takeaway:** Choose by execution context, latency and teardown requirements, not merely because one mechanism is called a bottom half.

### What is atomic context and what can't you do in it? {M}
Atomic context is a kernel execution context in which sleeping is not allowed. Examples include hard IRQ handlers, many softirq contexts, and code holding a raw spinlock or otherwise disabling preemption/interrupts in a way that prevents scheduling.

#### 1. Forbidden operations

Do not call APIs that can block, such as ordinary mutex_lock, msleep, GFP_KERNEL allocations or ordinary user-copy operations, unless the documented context explicitly permits them.

#### 2. Example

```c
static irqreturn_t irq_handler(int irq, void *data)
{
    // Acknowledge source, capture small state.
    schedule_work(&device_work);
    return IRQ_HANDLED;
}
```

Perform sleeping operations in the worker instead of the hard IRQ.

#### 3. Allocation

GFP_ATOMIC can be used for supported non-sleeping allocation contexts, but allocations can still fail. Preallocate buffers in probe or task context when predictable resources are required.

#### 4. PREEMPT_RT caveat

PREEMPT_RT changes the implementation of many locks and threads many interrupts. Do not infer sleepability from a lock name alone; follow the actual API and execution-context rules. Hard IRQ and raw-spinlocked regions remain non-sleeping contexts.

**Interview takeaway:** Atomic context is about whether scheduling/sleeping is allowed, not whether every operation is a single atomic CPU instruction.

### What is the difference between a spinlock and a mutex in the kernel? {M}
A mutex provides sleepable mutual exclusion; a spinlock provides a short critical-section mechanism with context rules suitable for non-sleeping synchronization on ordinary non-RT kernels.

| Mutex | Spinlock (ordinary non-RT kernel) |
|---|---|
| Waiter may sleep | Waiter spins when contended |
| Process/thread context | Short non-sleeping sections |
| Has owner | Not used as a sleepable ownership mutex |
| Suitable for longer sleepable operations | Suitable for brief shared-state updates |

#### 1. Mutex example

```c
mutex_lock(&d->lock);
ret = i2c_smbus_read_byte_data(d->client, REG_STATUS);
mutex_unlock(&d->lock);
```

I2C transfers may sleep, so they must not be placed under an ordinary non-sleeping spinlock.

#### 2. Spinlock example

```c
unsigned long flags;
spin_lock_irqsave(&d->lock, flags);
d->pending |= EVENT_RX;
spin_unlock_irqrestore(&d->lock, flags);
```

The short update may be shared with interrupt context, provided the lock design is correct for the target kernel.

#### 3. PREEMPT_RT

On PREEMPT_RT, spinlock_t uses different underlying semantics and many IRQs are threaded; raw_spinlock_t retains strict spinning behavior. Follow RT-specific locking rules.

**Interview takeaway:** Use mutexes when sleeping is allowed and spinlocks for short appropriate critical sections. Never hold a non-sleeping lock across an operation that may sleep.

### When should you use spin_lock_irqsave? {H}
spin_lock_irqsave acquires a spinlock while saving the local interrupt state. On ordinary non-RT kernels, it disables local hard interrupts to avoid deadlock when the same lock is acquired by a local interrupt handler.

#### 1. Deadlock without IRQ protection

A task acquires a lock. A local IRQ interrupts that task and attempts to acquire the same lock. The handler cannot proceed because the task owns it, and the task cannot resume until the interrupt returns.

#### 2. Correct pattern

```c
unsigned long flags;

spin_lock_irqsave(&d->lock, flags);
d->pending |= EVENT_RX;
spin_unlock_irqrestore(&d->lock, flags);
```

The matching unlock restores the saved interrupt state. The lock also serializes competing CPUs.

#### 3. When to use it

Use it when a lock is shared between process context and interrupt context on a non-RT kernel, or when the relevant locking design calls for saving interrupt state. Keep the section short and do not call sleeping APIs inside it.

On PREEMPT_RT, spinlock_t and its IRQ variants have changed semantics. A true hard-IRQ shared critical section may require raw_spinlock_t or redesign; follow the documented RT locking rules.

**Interview takeaway:** Local IRQ masking prevents same-core interrupt reentry; the spinlock handles cooperating CPUs. Restoring flags is safer than blindly enabling interrupts.

### What are atomic_t, RCU and seqlocks? {H}
Linux provides different synchronization mechanisms for different access patterns: atomic_t for individual atomic operations, RCU for read-mostly shared objects, and sequence counters/seqlocks for retryable consistent snapshots.

#### 1. Atomic counter

```c
atomic_t count = ATOMIC_INIT(0);
atomic_inc(&count);
```

An atomic increment prevents lost updates to that object. Ordering varies by API; atomic_t does not automatically protect a group of variables.

#### 2. RCU

Readers access a published object inside the appropriate RCU read-side critical section using rcu_dereference. Writers publish a replacement with rcu_assign_pointer and defer reclamation until a grace period, for example using synchronize_rcu or call_rcu. Writers still need serialization when required.

```text
Publish new object --> old readers finish --> free old object
```

#### 3. Seqlock

A writer updates a sequence counter around a protected update. A reader captures the sequence, copies data and retries if a writer intervened.

```c
do {
    seq = read_seqbegin(&d->seqlock);
    a = d->a;
    b = d->b;
} while (read_seqretry(&d->seqlock, seq));
```

Readers must tolerate retries. Plain sequence counters alone do not protect pointer lifetime, and writer preemption/context constraints matter.

**Interview takeaway:** Choose by access pattern and lifetime needs. Atomics are not multi-object locks; RCU protects publication/lifetime, and seqlocks provide retryable snapshots.

### What are wait queues and completions? {M}
Wait queues let a kernel task sleep until a condition changes. Completions represent an event indicating that an operation has finished.

#### 1. Wait queue example

```c
ret = wait_event_interruptible(d->waitq,
                               READ_ONCE(d->ready));
if (ret)
    return ret;
```

A producer updates the condition using appropriate synchronization, then calls wake_up_interruptible. A waiter rechecks the predicate; a wakeup alone does not guarantee the desired condition remains true.

#### 2. Completion example

```c
reinit_completion(&d->done);
start_transfer(d);
if (!wait_for_completion_timeout(&d->done,
                                  msecs_to_jiffies(100)))
    return -ETIMEDOUT;
```

An interrupt or worker calls complete(&d->done) when the operation finishes. Initialize the completion before use; reinitialize only when no conflicting waiters or completions remain. On timeout, stop or synchronize the hardware so a late completion cannot corrupt the next operation.

| Wait queue | Completion |
|---|---|
| Wait on a predicate | Wait for completion signal |
| Suitable for buffer readiness | Suitable for operation completion |

**Interview takeaway:** Wait queues depend on a properly synchronized condition. Completions simplify one-operation signaling, but timeout and lifetime races still require handling.

### How does user space wait for events from a driver (poll/select)? {M}
Userspace can wait for driver readiness using poll, select or epoll. A driver's poll callback registers relevant wait queues and returns a mask describing current readiness.

#### 1. Driver example

```c
static __poll_t demo_poll(struct file *file, poll_table *pt)
{
    struct demo *d = file->private_data;
    __poll_t mask = 0;

    poll_wait(file, &d->waitq, pt);

    if (READ_ONCE(d->ready))
        mask |= EPOLLIN | EPOLLRDNORM;

    return mask;
}
```

Register this function as the file_operations .poll callback. The actual readiness predicate and buffer state must be protected by the appropriate synchronization.

#### 2. Event flow

```text
poll(fd) --> driver .poll --> register wait queue
        --> no data: sleep
Device event --> update readiness --> wake_up...
        --> poll callback rechecks and returns readiness
```

Userspace should handle nonblocking read returning EAGAIN because another reader can consume data after readiness was reported.

#### 3. Hangup and errors

Report appropriate EPOLLERR or EPOLLHUP conditions when relevant. Keep the device and wait-queue objects alive while registered userspace watchers may refer to them.

**Interview takeaway:** poll_wait does not itself wait for the event. It registers a wait source; the poll framework handles waiting and readiness rechecks.

### What is sysfs and how do you add attributes? {M}
sysfs exposes attributes of kernel objects through a virtual filesystem, commonly under /sys. It is used for structured device information and configuration.

#### 1. Read/write attribute example

```c
static ssize_t enabled_show(struct device *dev,
                            struct device_attribute *attr,
                            char *buf)
{
    struct demo *d = dev_get_drvdata(dev);
    return sysfs_emit(buf, "%d\n", READ_ONCE(d->enabled));
}

static ssize_t enabled_store(struct device *dev,
                             struct device_attribute *attr,
                             const char *buf, size_t count)
{
    struct demo *d = dev_get_drvdata(dev);
    bool value;

    if (kstrtobool(buf, &value))
        return -EINVAL;

    WRITE_ONCE(d->enabled, value);
    return count;
}

static DEVICE_ATTR_RW(enabled);
```

This simple flag example assumes the object's lifetime is managed and the flag is not part of a larger hardware state transition. Use a suitable mutex/state protocol for actual hardware operations.

#### 2. Registration

Use device_create_file/device_remove_file or preferably suitable attribute groups, including managed helpers where applicable. Assign access permissions carefully.

#### 3. ABI guidance

Expose one logical value per attribute where practical, document public ABI semantics and avoid binary or high-throughput data transfer through ordinary text attributes.

**Interview takeaway:** sysfs connects kernel objects to structured userspace attributes. Validate input and use sysfs_emit for formatted output.

### What is the difference between procfs, sysfs and debugfs? {E}
procfs, sysfs and debugfs are virtual filesystems exposing different kinds of kernel information.

| Filesystem | Main purpose | Example |
|---|---|---|
| procfs | Process and system information | /proc/PID/maps, /proc/meminfo |
| sysfs | Kernel object/device attributes | /sys/class, /sys/bus |
| debugfs | Developer diagnostics | /sys/kernel/debug |

#### 1. Choosing an interface

Use the established subsystem's sysfs or other documented UAPI for stable application-facing configuration. Use debugfs for diagnostic counters, register dumps or experimental developer information when appropriate.

#### 2. Stability

Debugfs is not intended as a stable userspace ABI. It may be unavailable, restricted or disabled in production. Existing documented procfs/sysfs interfaces can have compatibility requirements; do not assume every virtual file is an arbitrary debug interface.

#### 3. Security

Avoid exposing secrets, unrestricted register writes or kernel addresses. Validate writes and restrict access according to the interface's purpose.

**Interview takeaway:** procfs describes process/system state, sysfs represents kernel objects and debugfs supports debugging. Use the correct subsystem interface rather than creating ad hoc files.

### What is the difference between kmalloc, vmalloc and kzalloc? {M}
kmalloc, kzalloc and vmalloc allocate kernel memory but differ in initialization and physical contiguity.

| API | CPU virtual contiguity | Physical contiguity | Initialization |
|---|---|---|---|
| kmalloc | Yes | Yes for allocation | Uninitialized |
| kzalloc | Yes | Yes for allocation | Zeroed |
| vmalloc | Yes | Not necessarily | Uninitialized |

#### 1. Examples

```c
struct demo *d = kzalloc(sizeof *d, GFP_KERNEL);
if (!d)
    return -ENOMEM;
// ...
kfree(d);
```

For a larger virtual buffer:

```c
void *buf = vmalloc(size);
if (!buf)
    return -ENOMEM;
// ...
vfree(buf);
```

Use vzalloc for zeroed vmalloc memory or suitable kvmalloc/kvfree helpers when an allocation may fall back to vmalloc.

#### 2. DMA caveat

Physical contiguity of kmalloc memory does not mean the CPU pointer is a DMA address. Use DMA mapping APIs and device constraints. Ordinary dma_map_single cannot be used on arbitrary vmalloc memory.

#### 3. Allocation context

Choose appropriate GFP flags and allocation sizes. Large physically contiguous requests can fail despite free memory.

**Interview takeaway:** kmalloc is suitable for many small kernel allocations; kzalloc also zeroes them. vmalloc assembles virtually contiguous storage and is not a drop-in DMA buffer allocator.

### What do GFP_KERNEL and GFP_ATOMIC mean? {E}
GFP flags tell the Linux allocator which allocation and reclaim behaviors are permitted.

| GFP_KERNEL | GFP_ATOMIC |
|---|---|
| May sleep and perform reclaim | Suitable for supported non-sleeping contexts |
| Ordinary process/thread context | Hard IRQ or short atomic context when permitted |
| More allocation options | May use limited reserves; can fail |

#### 1. Probe allocation

```c
d = kzalloc(sizeof *d, GFP_KERNEL);
if (!d)
    return -ENOMEM;
```

Probe normally runs in sleepable context.

#### 2. Atomic-context example

```c
event = kmalloc(sizeof *event, GFP_ATOMIC);
if (!event) {
    // Handle dropped event or use preallocated fallback.
}
```

Use this only if allocation is genuinely required and allowed in the current context. It is often better to allocate a pool in advance.

#### 3. Why GFP_ATOMIC can fail

It cannot use ordinary blocking reclaim and may have constrained memory availability. It is not a guarantee of success or constant execution time.

**Interview takeaway:** Select flags according to actual context and allocation requirements. Do not use GFP_ATOMIC everywhere to hide incorrect locking or interrupt design.

### How does a driver access device registers? {M}
Linux drivers access device registers through mapped MMIO addresses and architecture-aware accessor functions. A physical resource address is not normally directly dereferenced as a kernel pointer.

#### 1. Map a platform resource

```c
void __iomem *base;

base = devm_platform_ioremap_resource(pdev, 0);
if (IS_ERR(base))
    return PTR_ERR(base);

u32 status = readl(base + STATUS_OFFSET);
writel(ENABLE_MASK, base + CONTROL_OFFSET);
```

The offsets and register widths must match the device documentation.

#### 2. Access flow

```text
Driver readl / writel
       |
Mapped kernel MMIO virtual address
       |
CPU MMU and device-memory attributes
       |
SoC interconnect --> peripheral register
```

The mapping helper reserves/maps the resource using appropriate attributes.

#### 3. Important semantics

Use readb/readw/readl or appropriate wider/endian-specific accessors. Relaxed accessors have weaker ordering guarantees and require a documented reason. Posted writes may need a readback or another device-specific completion mechanism.

Do not blindly perform read-modify-write on W1C, read-to-clear or concurrently updated registers.

**Interview takeaway:** Use MMIO resource mappings and accessors, not arbitrary physical-address casts or ordinary memcpy. Width, byte order, ordering and side effects matter.

### How do drivers do DMA in Linux? {H}
Linux DMA APIs provide device-visible addresses, manage mapping constraints and handle cache synchronization appropriate to the platform.

#### 1. Streaming transmit buffer

```c
dma_addr_t addr = dma_map_single(dev, buf, len,
                                 DMA_TO_DEVICE);
if (dma_mapping_error(dev, addr))
    return -EIO;

/* Program the DMA address, start and wait for completion. */

dma_unmap_single(dev, addr, len, DMA_TO_DEVICE);
```

Use DMA-mappable memory with a valid lifetime. If a transfer fails, stop or synchronize the device before unmapping.

#### 2. Coherent allocation

```c
dma_addr_t dma;
void *cpu = dma_alloc_coherent(dev, size, &dma, GFP_KERNEL);
if (!cpu)
    return -ENOMEM;

/* Set up descriptors using cpu; hardware uses dma. */

dma_free_coherent(dev, size, cpu, dma);
```

Release only after the device no longer accesses the allocation.

#### 3. DMA addresses and IOMMU

```text
CPU virtual buffer -- CPU MMU --> physical memory
Device DMA address -- IOMMU (if present) --> physical memory
```

The DMA address can differ from both the CPU pointer and the physical address. Configure supported DMA masks and handle mapping failure.

#### 4. Ownership and ordering

Streaming mappings use appropriate direction and ownership synchronization, including dma_sync_single_for_cpu/device for persistent mappings. Coherent memory still needs ordering of descriptor fields and ownership flags.

**Interview takeaway:** The DMA API abstracts translation, coherency and device constraints. Never substitute virt_to_phys for a portable DMA mapping.

### How does mmap work in a driver? {H}
A driver's mmap callback maps suitable device or driver-managed memory into a userspace virtual address range. It can avoid repeated read/write copies, but requires careful permissions and lifetime management.

#### 1. Mapping flow

```text
Application mmap(fd, length, offset)
        |
VFS calls driver's .mmap callback
        |
Driver validates size, offset and access
        |
Map supported pages / device resource
        |
User virtual address accesses mapped region
```

#### 2. Coherent DMA buffer example

```c
static int demo_mmap(struct file *file,
                     struct vm_area_struct *vma)
{
    struct demo *d = file->private_data;
    unsigned long len = vma->vm_end - vma->vm_start;

    if (vma->vm_pgoff != 0 || len > d->size)
        return -EINVAL;

    return dma_mmap_coherent(d->dev, vma,
                             d->cpu_addr, d->dma_addr,
                             d->size);
}
```

This fragment assumes the buffer was allocated through dma_alloc_coherent and the device supports the mapping. Enforce page alignment, permitted mapping flags and buffer lifetime. Do not free a buffer while userspace still maps it.

#### 3. Other mappings

Use suitable VMA/PFN or page insertion helpers for documented device resources or pages, and remap_vmalloc_range for applicable vmalloc storage. A CPU physical PFN is not necessarily a DMA address.

#### 4. Security

Never map arbitrary kernel memory or adjacent resources. Validate offsets/lengths with overflow-safe arithmetic; ensure exposed pages contain only permitted data. Synchronize userspace and hardware access.

**Interview takeaway:** mmap changes the data-access interface, not the ownership problem. Choose the mapping helper for the allocation type and preserve lifetime until all mappings are gone.

### What are kernel timers, hrtimers and delays? {M}
Linux provides timers and delay APIs for different timing and execution-context requirements.

| API / mechanism | Purpose |
|---|---|
| timer_list | Schedule a callback using kernel tick-based timing |
| hrtimer | Higher-resolution timer expiration |
| msleep / usleep_range | Sleep in an appropriate context |
| udelay / ndelay | Short busy-wait delays |

#### 1. Timer example

```c
static void demo_timeout(struct timer_list *timer)
{
    struct demo *d = from_timer(d, timer, timeout);
    schedule_work(&d->work);
}

timer_setup(&d->timeout, demo_timeout, 0);
mod_timer(&d->timeout, jiffies + msecs_to_jiffies(100));
```

Ordinary timer callbacks cannot sleep on non-RT kernels. Schedule work for sleepable operations. Synchronize timer shutdown and work cancellation before freeing d.

#### 2. Device initialization delay

```c
writel(RESET_RELEASE, base + CTRL);
usleep_range(1000, 1500);
```

This assumes sleepable context and a hardware-specified minimum delay. A delay range allows the scheduler some flexibility.

#### 3. Busy waiting

Use udelay for very short hardware-required waits where sleeping is not permitted or not practical. Prefer bounded polling helpers for register readiness and handle timeout.

**Interview takeaway:** Match timing API to required resolution and context. A timer schedules work; it does not guarantee a callback runs at the exact expiration instant.

### How does power management work for drivers (system suspend and runtime PM)? {H}
Linux driver power management includes runtime PM for individual devices and system sleep transitions that coordinate the platform.

#### 1. Runtime PM

A device can suspend when idle and resume before use. The driver manages usage references and implements runtime callbacks that control clocks, supplies, context and hardware state.

```c
int ret = pm_runtime_resume_and_get(dev);
if (ret < 0)
    return ret;

ret = perform_transfer(d);

pm_runtime_mark_last_busy(dev);
pm_runtime_put_autosuspend(dev);
return ret;
```

This assumes runtime PM and autosuspend were configured appropriately during initialization. Balance successful usage references and follow target-kernel APIs.

#### 2. System suspend/resume

Before suspend, stop new work and quiesce hardware and DMA as required. Save state or configure wakeup sources. Resume restores required power, clocks, register state and ongoing interfaces in the correct order.

#### 3. Dependencies

Suppliers such as power domains, regulators and parent devices must be available before register access. Runtime and system PM callbacks can interact; use the PM framework's supported helpers rather than ad hoc state transitions.

#### 4. Debugging

Inspect runtime status and usage counts where exposed in sysfs, relevant PM logs and clock/regulator state. A device that never suspends may have an unbalanced usage reference or persistent activity.

**Interview takeaway:** Runtime PM saves power per device; system PM coordinates sleep across devices. Correct usage counts, ordering and asynchronous teardown are critical.

### What is PREEMPT_RT and what changes for drivers? {H}
PREEMPT_RT is the Linux real-time preemption infrastructure designed to reduce worst-case scheduling latency. It changes several kernel execution and locking mechanisms to make more work preemptible.

#### 1. Important changes

- Many interrupts execute in schedulable IRQ threads.
- Many spinlock_t locks use RT-mutex-based semantics with priority inheritance.
- raw_spinlock_t retains strict non-sleeping spinlock semantics.
- Kernel code must follow context and lock rules specific to the RT configuration.

Not every interrupt is threaded, and not every lock becomes sleepable.

#### 2. Driver implications

Keep true hard-IRQ handlers short, avoid long raw-spinlocked sections and minimize interrupt-disabled regions. Do not assume spin_lock_irqsave has identical hard-interrupt masking semantics on PREEMPT_RT and non-RT kernels.

Threaded IRQ priorities and task priorities can affect response latency; analyze dependencies rather than simply raising every priority.

#### 3. Measure latency

Use tools such as cyclictest for scheduling-latency measurements and ftrace or hardware trace to identify long preemption/interrupt-disabled sections. Test representative I/O and CPU load.

**Interview takeaway:** PREEMPT_RT improves predictability, not automatic hard-real-time guarantees. Drivers must still obey context rules and bound their worst-case blocking and execution times.

### How do you write a user-space driver, and when is it a good idea (UIO, VFIO, spidev, libgpiod)? {M}
Userspace drivers perform permitted device operations through kernel-provided interfaces. They are useful when hardware can be safely exposed without implementing a complete kernel functional driver.

| Interface | Typical purpose |
|---|---|
| UIO | Map selected device memory and receive interrupt notifications |
| VFIO | Controlled userspace device access with IOMMU/isolation support where available |
| spidev | Userspace SPI transfers for appropriately bound devices |
| libgpiod | GPIO character-device interface |

#### 1. Example: userspace SPI

Open the appropriate /dev/spidevB.C node, configure mode/speed through SPI ioctls, and submit transfers using the documented SPI_IOC_MESSAGE interface. Handle partial/error returns and device-specific chip-select requirements.

#### 2. When userspace works well

Prototyping, device control with moderate timing requirements and specialized userspace processing can benefit from easier debugging and process isolation.

#### 3. When a kernel driver is better

Use a kernel driver for tight interrupt response, standard subsystem integration, device power management, shared resources or security-sensitive access that must be mediated. A userspace process is still subject to scheduling latency.

VFIO requires appropriate isolation groups and configuration; direct MMIO access can still have dangerous device side effects.

**Interview takeaway:** Userspace drivers depend on safe kernel interfaces. Choose them for suitable devices, not as a shortcut around resource management and DMA isolation.

### How does the kernel boot on an ARM64 system? {M}
ARM64 Linux boot begins after platform firmware or a bootloader has prepared the machine and loaded the kernel image according to the architecture boot protocol.

#### 1. Typical flow

<div style="max-width:650px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 305" width="100%" role="img" aria-label="Arm64 boot from firmware and bootloader through kernel entry, memory initialization, drivers and PID 1">
<rect x="20" y="5" width="300" height="44" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="22" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">Firmware / bootloader</text><text x="170" y="37" text-anchor="middle" font-size="10" fill="currentColor">Prepare DRAM, load Image and DTB</text><path d="M170 49 v16 m-4-5 4 5 4-5" stroke="currentColor" fill="none"/><rect x="20" y="65" width="300" height="44" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="82" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">Kernel early assembly</text><text x="170" y="97" text-anchor="middle" font-size="10" fill="currentColor">head.S and architecture entry</text><path d="M170 109 v16 m-4-5 4 5 4-5" stroke="currentColor" fill="none"/><rect x="20" y="125" width="300" height="44" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="142" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">Kernel initialization</text><text x="170" y="157" text-anchor="middle" font-size="10" fill="currentColor">MMU, memory, scheduler, IRQs</text><path d="M170 169 v16 m-4-5 4 5 4-5" stroke="currentColor" fill="none"/><rect x="20" y="185" width="300" height="44" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="202" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">Device and filesystem setup</text><text x="170" y="217" text-anchor="middle" font-size="10" fill="currentColor">Initcalls, rootfs, kernel threads</text><path d="M170 229 v16 m-4-5 4 5 4-5" stroke="currentColor" fill="none"/><rect x="20" y="245" width="300" height="44" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="262" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">Userspace PID 1</text><text x="170" y="277" text-anchor="middle" font-size="10" fill="currentColor">init / systemd / Android init</text></svg></div>

#### 2. Bootloader handoff

For direct device-tree boot, x0 carries the physical address of the DTB; other specified registers, exception level, MMU/cache state and interrupt masks must follow the Linux arm64 boot requirements. UEFI boot has an additional firmware interface.

#### 3. Kernel internals

Early assembly establishes the required execution environment and translation tables, then reaches start_kernel. Architecture setup, memory initialization, scheduler, interrupts and other core subsystems are initialized. The kernel starts threads including the init path, executes initcalls and eventually runs the first userspace init program.

#### 4. Debugging

Use earlycon and UART boot logs to separate bootloader handoff failures from early kernel, driver probe and root filesystem failures. Exact function names/order can change with kernel version.

**Interview takeaway:** Firmware initializes the platform sufficiently to enter Linux; Linux establishes its own memory-management and runtime environment before launching userspace.

### How do you debug a kernel oops or panic? {M}
A kernel oops is a report of a serious kernel fault. Linux may continue after some oops conditions, but a kernel panic stops normal operation because continued execution is unsafe or impossible under the configured policy.

#### 1. Evidence to collect

Capture complete kernel logs, fault type/address, PC/LR, call trace, registers, kernel version, taint information and the exact reproduction steps. Persistent logs, serial console or crash dumps help when the system reboots.

#### 2. Resolve the fault

Use the matching unstripped vmlinux and module debug information. For example:

```sh
./scripts/decode_stacktrace.sh vmlinux < crash.log
```

Adjust arguments for the target kernel script and module files. Account for KASLR and module relocation when resolving raw runtime addresses.

#### 3. Common causes

Invalid pointer access, use-after-free, out-of-bounds writes, incorrect interrupt context, stack corruption, locking bugs and hardware/MMIO faults.

#### 4. Targeted tools

Use KASAN for supported memory-bug detection, KCSAN for certain race detection, lockdep for locking issues, ftrace for execution tracing and kdump where configured. These facilities can change timing and resource usage.

**Interview takeaway:** Diagnose from the first fault and matching symbols. An oops may be a symptom of earlier corruption; continuing after it is not proof that the system is safe.

### What is the DRM/KMS display stack? {H}
DRM (Direct Rendering Manager) is Linux's graphics subsystem. KMS (Kernel Mode Setting) manages display configuration, scanout and the relationship between framebuffer data and physical outputs.

#### 1. Display pipeline

<div style="max-width:650px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 270" width="100%" role="img" aria-label="Framebuffers feed planes, which feed CRTC composition and timings, encoder, bridge and connector panel">
<rect x="5" y="5" width="155" height="29" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="82.5" y="23" font-size="11" text-anchor="middle" fill="currentColor">Framebuffer A</text><rect x="180" y="5" width="155" height="29" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="257.5" y="23" font-size="11" text-anchor="middle" fill="currentColor">Framebuffer B</text><rect x="5" y="48" width="155" height="29" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="82.5" y="66" font-size="11" text-anchor="middle" fill="currentColor">Primary plane</text><rect x="180" y="48" width="155" height="29" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="257.5" y="66" font-size="11" text-anchor="middle" fill="currentColor">Overlay plane</text><rect x="95" y="100" width="150" height="29" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="118" font-size="11" text-anchor="middle" fill="currentColor">CRTC / mixer</text><rect x="95" y="145" width="150" height="29" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="163" font-size="11" text-anchor="middle" fill="currentColor">Encoder</text><rect x="95" y="190" width="150" height="29" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="208" font-size="11" text-anchor="middle" fill="currentColor">Bridge (optional)</text><rect x="95" y="235" width="150" height="29" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="253" font-size="11" text-anchor="middle" fill="currentColor">Connector / panel</text><path d="M82.5 34 V48 M257.5 34 V48 M82.5 77 V88 H170 V100 M257.5 77 V88 H170 M170 129 V145 M170 174 V190 M170 219 V235" stroke="currentColor" fill="none"/></svg></div>

A framebuffer describes pixel storage and layout. Planes select buffers, source/destination rectangles and blending properties. A CRTC controls composition/scanout timing. Encoders and bridges connect the pipeline to output signals; connectors represent output endpoints. Actual hardware mapping can vary.

#### 2. Atomic modesetting flow

Userspace (such as a compositor) creates an atomic request containing object properties. The driver/core validate the proposed state through atomic checks, then the commit programs the required hardware changes. Fences, vblank events and hardware-specific commit sequencing coordinate buffer readiness and presentation.

An atomic commit does not by itself guarantee every possible update is tear-free; supported modes, async flags and hardware behavior matter.

#### 3. Debugging with libdrm

```sh
modetest -M msm -c
modetest -M msm -p
```

The DRM driver name and available options depend on the platform. Enumerate actual connector, CRTC and plane IDs rather than hardcoding them.

**Interview takeaway:** KMS connects memory-backed framebuffers to display timing and outputs through atomic state. Understand both the logical DRM objects and the hardware pipeline.

### What is the difference between a kernel thread and a user thread? {E}
**Short answer:** A kernel thread runs entirely in kernel space, has no user address space (its `mm` is NULL; it borrows the previous task's page tables), and is created with `kthread_run()` or by subsystems (`kworker`, `ksoftirqd`, `irq/NN-name`, `kswapd`, `rcu_*`). A user thread belongs to a process, shares that process's address space and file descriptors, runs user code at EL0, and enters the kernel only through system calls, exceptions and interrupts. Both are `task_struct`s scheduled by the same scheduler.

**Creating a kernel thread in a driver**

```c
static int poll_fn(void *data)
{
    struct mydev *d = data;
    while (!kthread_should_stop()) {
        poll_hardware(d);
        msleep_interruptible(10);
    }
    return 0;
}

d->task = kthread_run(poll_fn, d, "mydev-poll");
if (IS_ERR(d->task)) return PTR_ERR(d->task);
/* in remove: */ kthread_stop(d->task);
```

**Points**

- Kernel threads appear in `ps` in square brackets (`[kworker/0:1H]`).
- Prefer workqueues or threaded IRQs over custom kthreads unless you need a dedicated, long-running loop or a specific RT priority (`sched_set_fifo(task)`).
- In Linux, user threads are created with `clone()` sharing the address space (pthreads, 1:1 model): each user thread has its own kernel `task_struct` and kernel stack.
- Kernel threads can be frozen during suspend (`set_freezable()`, `try_to_freeze()`).

### How do you build an out-of-tree kernel module? {E}
**Short answer:** Write a minimal Kbuild Makefile that sets `obj-m` and calls the kernel build system with `M=$(PWD)`. Build against the configured source or headers of the exact kernel the module will run on (`vermagic` must match). For an embedded target, point `KDIR` at the target kernel build tree and pass `ARCH` and `CROSS_COMPILE`.

```make
obj-m += mydrv.o
mydrv-y := main.o hw.o          # module built from several files

KDIR ?= /lib/modules/$(shell uname -r)/build

all:
	$(MAKE) -C $(KDIR) M=$(PWD) modules
clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean
install:
	$(MAKE) -C $(KDIR) M=$(PWD) modules_install
```

**Cross-compiling for an ARM64 board**

```sh
make KDIR=~/linux-build ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu-
```

The `KDIR` tree must have been configured and built (`make modules_prepare` at least) with the same configuration as the target kernel.

**Integration options**

- **Yocto:** a recipe inheriting `module` builds it with the image kernel automatically.
- **Buildroot:** `kernel-module` package infrastructure.
- **DKMS:** rebuilds out-of-tree modules automatically when distribution kernels update.
- **In-tree:** add a Kconfig entry and `obj-$(CONFIG_MYDRV) += mydrv.o` to the subsystem's Makefile; upstreaming the driver avoids constant rebuilding for API changes.

**Common errors:** "Invalid module format" or "disagrees about version of symbol" (built against a different kernel), "Unknown symbol" (missing dependency, or using a GPL-only symbol without a GPL licence), and missing `modules_prepare` in the build tree.

### What is the difference between dma_alloc_coherent and dma_map_single? {M}
**Short answer:** Coherent allocation returns a CPU pointer and a DMA address for a consistent shared allocation. Streaming mapping temporarily transfers ownership of an existing suitable CPU buffer to a device.

| API | Typical use |
|---|---|
| dma_alloc_coherent | Descriptor ring |
| dma_map_single | One TX/RX buffer |
| dma_sync_single_for_cpu | CPU accesses a still-mapped streaming buffer |
| dma_sync_single_for_device | Return ownership to device |
| dma_unmap_single | End streaming mapping |

**Example:** Ethernet TX maps a packet, programs the DMA address, waits for completion, then unmaps it. A descriptor ring may remain coherently allocated for the lifetime of the interface.

```text
CPU fills TX buffer -> dma_map_single -> Device owns buffer
CPU may reuse buffer <- dma_unmap_single <- Completion
```

**Interview takeaway:** Coherency is not the same as ordering. Even a coherent descriptor ring may require dma_wmb() before publishing ownership. Check mapping errors and match the mapping direction and size. [Linux DMA API guide](https://docs.kernel.org/core-api/dma-api-howto.html).

### How do you debug a display underflow or a black screen on Linux DRM/KMS? {H}
**Short answer:** Separate panel power and link failures from scanout and bandwidth failures. Verify the atomic state, clocks, timing and buffer readiness before changing hardware settings.

**1. Check connector and modes:** Use modetest and inspect the connector status and advertised modes.

**2. Check pipeline:** Verify framebuffer, plane, CRTC, encoder/bridge and panel enable state. Check regulators, reset, link initialization and backlight where applicable.

```text
Framebuffer -> Plane -> CRTC -> Encoder / bridge -> Panel
                ^         ^
             format    bandwidth / timing
```

**3. Check interrupts and fences:** Missing vblank, unsignaled render fences or FIFO underrun counters can narrow the failure.

**4. Reproduce:** Try a known supported mode and simple test framebuffer using modetest on a test system where taking display ownership is safe.

```sh
modetest -M msm -c -p
cat /sys/kernel/debug/dri/0/state
dmesg | grep -Ei 'drm|dsi|underflow|underrun'
```

Driver name, debugfs access and card index vary by platform.

**Interview takeaway:** Black screen is a symptom, not a diagnosis; follow the pixel data path and control/power path separately.
