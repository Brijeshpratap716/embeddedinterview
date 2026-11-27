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
**Short answer:** Device-managed resource functions (`devm_kzalloc`, `devm_platform_ioremap_resource`, `devm_request_irq`, `devm_clk_get_enabled`, `devm_regulator_get`, `devm_gpiod_get`...) record a release action on the device. If `probe` fails, or the device is later unbound, all managed resources are released automatically in reverse order. This removes most error-path cleanup code and the leaks that come with it.

**Before and after**

```c
/* manual: every error path must undo the previous steps */
base = ioremap(res->start, resource_size(res));
if (!base) return -ENOMEM;
ret = request_irq(irq, handler, 0, "x", d);
if (ret) { iounmap(base); return ret; }

/* managed: just return on error */
base = devm_ioremap_resource(dev, res);
if (IS_ERR(base)) return PTR_ERR(base);
ret = devm_request_irq(dev, irq, handler, 0, "x", d);
if (ret) return ret;
```

**Custom cleanup:** `devm_add_action_or_reset(dev, my_cleanup, data)` registers any function to run on release (e.g. to put hardware into reset).

**Pitfalls**

- **Ordering with `remove()`:** managed resources are released **after** `remove()` returns. A managed IRQ can still fire after `remove()` has stopped or freed something the handler uses; disable the device's interrupts in hardware in `remove()`, or make that teardown itself a devm action registered in the right order.
- **Lifetime:** memory from `devm_kzalloc` is freed when the device unbinds, even if user space still has the `/dev` file open; data reachable from open files must be reference-counted separately.
- Do not use devm functions outside probe paths for resources that are created and destroyed repeatedly (they accumulate until unbind).

### What is pinctrl, and how do GPIO, clock and regulator frameworks work in drivers? {M}
**Short answer:** These frameworks let drivers request board resources by name from the device tree instead of programming SoC registers directly. **pinctrl** sets pin multiplexing and electrical settings (pull-ups, drive strength) for named states (`default`, `sleep`), applied automatically before `probe`. The **GPIO** consumer API (`devm_gpiod_get(dev, "reset", GPIOD_OUT_HIGH)`, `gpiod_set_value_cansleep()`) handles active-low polarity from the DT. The **clock** framework (`devm_clk_get`, `clk_prepare_enable`, `clk_set_rate`) manages clock trees and reference counts. The **regulator** framework (`devm_regulator_get`, `regulator_enable`, `regulator_set_voltage`) controls power rails.

**Device tree side**

```dts
panel@0 {
    compatible = "acme,panel";
    reset-gpios = <&gpio3 7 GPIO_ACTIVE_LOW>;
    vdd-supply = <&ldo3>;
    clocks = <&ccu CLK_DSI>;
    clock-names = "pixel";
    pinctrl-names = "default", "sleep";
    pinctrl-0 = <&panel_pins_default>;
    pinctrl-1 = <&panel_pins_sleep>;
};
```

**Driver side (power-on sequence)**

```c
d->vdd   = devm_regulator_get(dev, "vdd");                       /* matches vdd-supply */
d->reset = devm_gpiod_get(dev, "reset", GPIOD_OUT_HIGH);         /* asserted (logical 1) */
d->clk   = devm_clk_get(dev, "pixel");

ret = regulator_enable(d->vdd);
usleep_range(10000, 11000);                 /* datasheet: power stable before reset release */
ret = clk_prepare_enable(d->clk);
gpiod_set_value_cansleep(d->reset, 0);      /* logical deassert; framework handles ACTIVE_LOW */
msleep(120);
```

**Points interviewers check**

- GPIO descriptor values are **logical**: 1 = active, regardless of the physical polarity, which the DT defines.
- `_cansleep` variants are needed for GPIOs on I2C expanders.
- `clk_prepare` may sleep, `clk_enable` may not: hence `clk_prepare_enable` in process context.
- Regulators and clocks are reference-counted: balance every enable with a disable.
- Missing providers make `devm_*_get` return `-EPROBE_DEFER`; return it from `probe` and the core retries.
- Debug: `/sys/kernel/debug/pinctrl/`, `/sys/kernel/debug/gpio`, `/sys/kernel/debug/clk/clk_summary`, `/sys/kernel/debug/regulator/regulator_summary`.

### What is deferred probing (-EPROBE_DEFER)? {M}
**Short answer:** If a driver's `probe()` needs a resource from another driver that has not probed yet (a clock, regulator, GPIO controller, PHY, interrupt controller, I2C bus), the `get` function returns `-EPROBE_DEFER`. The driver returns that code, and the driver core puts the device on a deferred list and retries it whenever another driver binds successfully. This handles arbitrary probe ordering without hard-coded init sequences.

**Correct handling**

```c
d->vdd = devm_regulator_get(dev, "vdd");
if (IS_ERR(d->vdd))
    return dev_err_probe(dev, PTR_ERR(d->vdd), "failed to get vdd\n");
/* dev_err_probe() prints nothing for -EPROBE_DEFER and records the reason */
```

**Debugging a device that never probes**

- `cat /sys/kernel/debug/devices_deferred` lists deferred devices with the reason recorded by `dev_err_probe`.
- Common causes: the provider driver is not enabled in the kernel config or is a module not yet loaded; a typo in the DT phandle or `-supply` name; the provider node has `status = "disabled"`.
- **fw_devlink** (enabled by default) uses DT phandles to create device links, so consumers are not probed before suppliers at all, which reduces repeated deferrals and orders suspend/resume correctly.
- `deferred_probe_timeout=` on the command line makes the kernel give up after a time so optional dependencies don't block forever.

**Do not:** busy-wait or sleep in `probe` hoping the resource appears, or treat `-EPROBE_DEFER` as a fatal error and print scary messages.

### What are top halves and bottom halves? {M}
**Short answer:** Interrupt handling is split in two so that the hard IRQ handler stays short. The **top half** is the handler registered with `request_irq`: it runs in hard-interrupt context with its line masked, acknowledges the device, grabs urgent data (e.g. a status register or a received byte) and schedules the rest. The **bottom half** is deferred work that runs later with interrupts enabled: **softirqs**, **tasklets** (deprecated), **workqueues** and **threaded IRQs**.

**Why split:** while a hard IRQ handler runs, its line (and on many systems, other interrupts on that CPU) is blocked, increasing interrupt latency for everyone; it also cannot sleep, so anything involving I2C/SPI, mutexes or memory allocation with `GFP_KERNEL` must be deferred.

**Typical flow for a network or DMA device**

```
IRQ → top half: read & clear status, disable further device IRQs, napi_schedule() → return IRQ_HANDLED
     → softirq (NET_RX): NAPI poll processes up to "budget" packets, re-enables device IRQs when done
```

**Choosing a bottom half**

| Need | Use |
|---|---|
| Must sleep (I2C/SPI, mutex, GFP_KERNEL) | threaded IRQ or workqueue |
| Very high rate, per-CPU, no sleeping | softirq (subsystem-level: networking, block, timers) or BH workqueue |
| Delay before running | `delayed_work` (`schedule_delayed_work`) |
| Run on a schedulable RT priority | threaded IRQ (`irq/NN-name` thread, SCHED_FIFO 50 by default) |

**Return values of the top half:** `IRQ_HANDLED`, `IRQ_NONE` (not my device: important for shared interrupt lines and spurious-IRQ detection) and `IRQ_WAKE_THREAD` (run the threaded handler).

### What is the difference between a tasklet, a workqueue and a threaded IRQ? {H}
**Short answer:** A **tasklet** runs in softirq context: soon after the interrupt, on the same CPU, but it cannot sleep, and tasklets are deprecated for new code. A **workqueue** item runs in a kernel thread (`kworker`) in process context, so it can sleep, at the cost of more scheduling latency. A **threaded IRQ** gives each interrupt its own kernel thread (`irq/NN-name`) with real-time priority; it can sleep and is the standard choice for devices on slow buses like I2C and SPI.

| | Tasklet / softirq | Workqueue | Threaded IRQ |
|---|---|---|---|
| Context | softirq (atomic) | process (kworker thread) | process (dedicated irq thread) |
| Can sleep | no | yes | yes |
| Latency | low | higher (normal priority, shared workers) | low, SCHED_FIFO priority |
| Concurrency | a given tasklet never runs on two CPUs at once | configurable (ordered, unbound, per-CPU) | one thread per IRQ |
| Typical use | legacy fast deferral | slow or delayed work, firmware loading, retries | I2C/SPI devices, GPIO interrupts, most new drivers |
| Status | deprecated (use BH workqueues) | current | current |

**Threaded IRQ for an I2C device**

```c
static irqreturn_t sensor_thread(int irq, void *data)
{
    struct mysensor *s = data;
    unsigned int status;

    if (regmap_read(s->map, REG_STATUS, &status))     /* sleeps: OK in the thread */
        return IRQ_NONE;
    if (!(status & DATA_READY))
        return IRQ_NONE;
    read_sample_and_push(s);
    return IRQ_HANDLED;
}

ret = devm_request_threaded_irq(dev, client->irq, NULL, sensor_thread,
                                IRQF_ONESHOT, "mysensor", s);
```

With no primary handler and `IRQF_ONESHOT`, the core masks the line until the thread finishes, which is required for level-triggered interrupts that can only be cleared by an I2C read.

**Workqueue example**

```c
INIT_WORK(&d->work, mydev_work_fn);                 /* in probe */
schedule_work(&d->work);                            /* from the IRQ handler */
cancel_work_sync(&d->work);                         /* in remove: wait for it to finish */
```

**Follow-up:** with PREEMPT_RT, all interrupt handlers are forced into threads (except those marked `IRQF_NO_THREAD`), and softirqs run in thread context too.

### What is atomic context and what can't you do in it? {M}
**Short answer:** Code is in atomic context when it must not sleep or be scheduled out: hard IRQ handlers, softirqs and tasklets, sections holding a spinlock, and sections with pre-emption or interrupts disabled (also `rcu_read_lock()` sections on non-RT kernels). In atomic context you must not call anything that may sleep: `mutex_lock`, `msleep`, `kmalloc(GFP_KERNEL)`, `copy_to_user`/`copy_from_user`, I2C/SPI transfers, `wait_event`, `vmalloc`, `request_firmware`, and most `regulator`/`clk_prepare` calls.

**What to use instead**

| Instead of | Use in atomic context |
|---|---|
| `kmalloc(GFP_KERNEL)` | `kmalloc(GFP_ATOMIC)` (may fail; preallocate where possible) |
| `msleep`, `usleep_range` | `udelay`/`ndelay` for a few microseconds, or defer |
| `mutex_lock` | spinlock |
| I2C/SPI transfer | defer to a threaded IRQ or workqueue |
| `copy_to_user` | copy to a kernel buffer, then copy out later in process context |

**Why sleeping is forbidden:** with a spinlock held or pre-emption disabled, sleeping would let another task run on this CPU that might spin on the same lock forever (deadlock); in interrupt context there is no task to put to sleep at all.

**Detecting bugs:** `CONFIG_DEBUG_ATOMIC_SLEEP` makes `might_sleep()` calls (present in all sleeping functions) print "BUG: sleeping function called from invalid context" with a backtrace. Lockdep also reports locking problems. Check with `in_atomic()`, `in_interrupt()`, `in_task()` only for debugging, not to change behaviour.

### What is the difference between a spinlock and a mutex in the kernel? {M}
**Short answer:** A **spinlock** busy-waits until the lock is free and disables pre-emption while held, so it can be used in atomic and interrupt context but must only protect very short critical sections that never sleep. A **mutex** puts the waiting task to sleep, so it can only be used in process context, but the holder may sleep (e.g. do I2C transfers) and hold it longer; it also enforces ownership.

| | Spinlock | Mutex |
|---|---|---|
| Waiting | busy-waits (spins) | sleeps (other tasks run) |
| Usable in IRQ/softirq context | yes | no |
| May sleep while held | no | yes |
| Pre-emption while held | disabled | allowed |
| Hold time | very short (microseconds) | can be longer |
| Ownership | no | yes; only the owner unlocks, debug checks |
| On PREEMPT_RT | becomes a sleeping rt_mutex (except `raw_spinlock_t`) | rt_mutex with priority inheritance |

**Other primitives**

- **Semaphore:** counting, can be released by another task; rarely the right choice for new code.
- **rwlock / rw_semaphore:** many readers or one writer.
- **Completion:** "wait until X is done" (`wait_for_completion`, `complete`).
- **Atomics and RCU:** lock-free options for counters and read-mostly data.

**Rule of thumb:** if the critical section can sleep or is long → mutex. If it is short or the data is touched from interrupt context → spinlock (with the correct irq variant). Never hold a spinlock while calling a function that might sleep.

**On a single-CPU kernel** without `CONFIG_SMP`, spinlocks reduce to disabling pre-emption (and interrupts for the `_irqsave` variants), because there is no other CPU to race with — but the code must still be written correctly for SMP.

### When should you use spin_lock_irqsave? {H}
**Short answer:** Use `spin_lock_irqsave` when the data protected by the lock is also accessed from a **hard interrupt handler**. If process-context code takes a plain `spin_lock` and the interrupt fires on the same CPU, the handler spins forever on a lock that its own CPU holds, and the CPU deadlocks. `spin_lock_irqsave(&lock, flags)` disables local interrupts and saves their previous state, so it is safe from any context.

```c
/* process context (e.g. ioctl) */
unsigned long flags;
spin_lock_irqsave(&d->lock, flags);
d->config = new_config;
spin_unlock_irqrestore(&d->lock, flags);

/* hard IRQ handler on the same data */
static irqreturn_t mydev_irq(int irq, void *data)
{
    struct mydev *d = data;
    spin_lock(&d->lock);        /* interrupts are already disabled here: plain lock is enough */
    d->count++;
    spin_unlock(&d->lock);
    return IRQ_HANDLED;
}
```

**Choosing the variant**

| Data shared with | Process-context side uses |
|---|---|
| only other process context | `spin_lock` (or a mutex if it may sleep) |
| softirq / tasklet / timer | `spin_lock_bh` (disables bottom halves locally) |
| hard IRQ handler | `spin_lock_irqsave` (or `spin_lock_irq` if interrupts are known to be enabled) |

- `spin_lock_irq` / `spin_unlock_irq` unconditionally re-enable interrupts, which is a bug if they were already disabled by the caller; `irqsave/irqrestore` restores the original state.
- Interrupts are disabled only on the **local** CPU; another CPU can still run the handler and spin briefly on the lock, which is fine — that is what the spinlock is for.
- Lockdep reports "inconsistent lock state" when a lock is taken both with and without IRQs disabled where an IRQ could interrupt the holder.
- Keep these sections short: interrupt latency on that CPU grows while they are held.

### What are atomic_t, RCU and seqlocks? {H}
**Short answer:** **`atomic_t`/`atomic64_t`** provide lock-free integer operations (`atomic_inc`, `atomic_dec_and_test`, `atomic_cmpxchg`), and **`refcount_t`** is the safe type for reference counts (it saturates and warns instead of wrapping). **RCU (read-copy-update)** lets readers access shared data with almost no overhead and no locks: writers publish a new version with `rcu_assign_pointer` and free the old version only after a **grace period**, when all pre-existing readers have finished. **Seqlocks** let readers proceed without locks and retry if a writer changed the data during the read; they suit small, frequently read, rarely written data like timekeeping.

**RCU example: read-mostly configuration**

```c
struct cfg { int rate; int gain; struct rcu_head rcu; };
static struct cfg __rcu *cur_cfg;
static DEFINE_MUTEX(cfg_lock);

int read_rate(void)                               /* readers: fast, never block */
{
    int r;
    rcu_read_lock();
    r = rcu_dereference(cur_cfg)->rate;
    rcu_read_unlock();
    return r;
}

int update_cfg(int rate, int gain)                /* writers: copy, publish, free later */
{
    struct cfg *new = kmalloc(sizeof(*new), GFP_KERNEL), *old;
    if (!new) return -ENOMEM;
    new->rate = rate; new->gain = gain;
    mutex_lock(&cfg_lock);
    old = rcu_dereference_protected(cur_cfg, lockdep_is_held(&cfg_lock));
    rcu_assign_pointer(cur_cfg, new);
    mutex_unlock(&cfg_lock);
    if (old) kfree_rcu(old, rcu);                 /* freed after all current readers finish */
    return 0;
}
```

**Seqlock pattern**

```c
unsigned int seq;
do {
    seq = read_seqbegin(&tk_lock);
    t = timekeeper_time;                          /* copy the data */
} while (read_seqretry(&tk_lock, seq));           /* writer was active: retry */
```

**Comparison**

| | Readers | Writers | Good for |
|---|---|---|---|
| spinlock / mutex | take the lock | take the lock | general use |
| rwlock | shared lock (still cache-line bouncing) | exclusive | rarely the best choice today |
| RCU | nearly free, never block | copy + publish + deferred free | read-mostly lists, tables, configs (routing, module lists) |
| seqlock | lock-free, may retry | exclusive, never wait for readers | small data, frequent reads, readers can retry (no pointers to chase) |
| atomics | – | – | counters, flags, refcounts |

**Memory ordering:** `atomic_inc` alone has no ordering guarantees; use `smp_mb__after_atomic()` or ordered variants (`atomic_inc_return`, `_acquire`/`_release`) when ordering matters.

### What are wait queues and completions? {M}
**Short answer:** A **wait queue** lets a task sleep until a condition becomes true: the sleeper calls `wait_event_interruptible(wq, condition)`, and the code that changes the condition (often an interrupt handler) calls `wake_up_interruptible(&wq)`; the condition is re-checked after every wake-up, so spurious wake-ups are harmless. A **completion** is a simpler wrapper for the common case "wait until this one thing has finished" (`wait_for_completion_timeout()` and `complete()`), e.g. waiting for a DMA transfer or a firmware response.

**Blocking read using a wait queue**

```c
static ssize_t mydev_read(struct file *f, char __user *ubuf, size_t n, loff_t *pos)
{
    struct mydev *d = f->private_data;
    u32 val;

    if (f->f_flags & O_NONBLOCK) {
        if (!READ_ONCE(d->data_ready)) return -EAGAIN;
    } else if (wait_event_interruptible(d->wq, READ_ONCE(d->data_ready))) {
        return -ERESTARTSYS;                        /* interrupted by a signal */
    }

    spin_lock_irq(&d->lock);
    val = d->sample;
    d->data_ready = false;
    spin_unlock_irq(&d->lock);

    if (n < sizeof(val)) return -EINVAL;
    return copy_to_user(ubuf, &val, sizeof(val)) ? -EFAULT : sizeof(val);
}

/* in the IRQ handler */
spin_lock(&d->lock);
d->sample = readl(d->base + DATA);
d->data_ready = true;
spin_unlock(&d->lock);
wake_up_interruptible(&d->wq);
```

**Completion for a DMA transfer**

```c
reinit_completion(&d->dma_done);
start_dma(d);
if (!wait_for_completion_timeout(&d->dma_done, msecs_to_jiffies(100))) {
    dmaengine_terminate_sync(d->chan);
    return -ETIMEDOUT;
}
/* DMA callback: complete(&d->dma_done); */
```

**Points**

- Always use a timeout for hardware events, and handle signals (`-ERESTARTSYS`).
- `wait_event_killable` only lets fatal signals interrupt the wait.
- Never wait in atomic context.
- Wait queues also back `poll()` (next question).

### How does user space wait for events from a driver (poll/select)? {M}
**Short answer:** Implement `.poll` in `file_operations`. It calls `poll_wait()` to add the caller to the driver's wait queue (this does **not** sleep) and returns a mask of the events that are ready **now** (`EPOLLIN | EPOLLRDNORM` for readable, `EPOLLOUT | EPOLLWRNORM` for writable, `EPOLLERR`/`EPOLLHUP`). When data arrives, the driver calls `wake_up_interruptible(&wq)`, which makes `poll`, `select` and `epoll` callers re-check.

```c
static __poll_t mydev_poll(struct file *f, poll_table *wait)
{
    struct mydev *d = f->private_data;
    __poll_t mask = 0;

    poll_wait(f, &d->wq, wait);                 /* registers; the VFS does the sleeping */
    if (READ_ONCE(d->data_ready))
        mask |= EPOLLIN | EPOLLRDNORM;
    if (fifo_has_space(d))
        mask |= EPOLLOUT | EPOLLWRNORM;
    if (d->disconnected)
        mask |= EPOLLHUP;
    return mask;
}
```

**User space**

```c
struct pollfd p = { .fd = fd, .events = POLLIN };
int r = poll(&p, 1, 1000);                      /* 1 s timeout */
if (r > 0 && (p.revents & POLLIN)) read(fd, &val, sizeof val);
```

**How it works internally:** the VFS calls your `.poll`; if no requested event is ready, it sleeps; your `wake_up` wakes it, and it calls `.poll` again to get the new mask. That is why `.poll` must be cheap and must not block.

**Other notification mechanisms**

- `fasync` / `SIGIO` (`kill_fasync`): asynchronous signal to user space; rarely used now.
- `eventfd`: a simple counter file descriptor, used by KVM/VFIO/vhost to signal interrupts.
- sysfs `sysfs_notify()` wakes user programs polling a sysfs attribute (used by GPIO and IIO events).
- uevents (`kobject_uevent`) for device state changes handled by udev.

### What is sysfs and how do you add attributes? {M}
**Short answer:** Sysfs (`/sys`) exposes the kernel's device model as a directory tree: each device is a directory, and each **attribute** is a file holding one value (in text). Drivers add attributes with `DEVICE_ATTR_RW(name)` plus `name_show()`/`name_store()` functions, group them, and attach the group through the driver's `.dev_groups` field so they are created and removed together with the device (no race with user space).

```c
static ssize_t gain_show(struct device *dev, struct device_attribute *attr, char *buf)
{
    struct mydev *d = dev_get_drvdata(dev);
    return sysfs_emit(buf, "%u\n", d->gain);
}

static ssize_t gain_store(struct device *dev, struct device_attribute *attr,
                          const char *buf, size_t count)
{
    struct mydev *d = dev_get_drvdata(dev);
    unsigned int val;
    int ret = kstrtouint(buf, 0, &val);
    if (ret) return ret;
    if (val > 7) return -EINVAL;
    mutex_lock(&d->lock);
    d->gain = val;
    mydev_apply_gain(d);
    mutex_unlock(&d->lock);
    return count;
}
static DEVICE_ATTR_RW(gain);

static struct attribute *mydev_attrs[] = { &dev_attr_gain.attr, NULL };
ATTRIBUTE_GROUPS(mydev);                     /* defines mydev_groups */

static struct platform_driver mydev_driver = {
    .driver = { .name = "mydev", .of_match_table = mydev_of_match, .dev_groups = mydev_groups },
    .probe = mydev_probe,
};
```

Use: `cat /sys/bus/platform/devices/40010000.mydev/gain`, `echo 3 > .../gain`.

**Rules**

- One value per file; text format; `sysfs_emit()` in show functions (bounds-safe).
- Attributes are ABI: document them in `Documentation/ABI/` and do not change them casually.
- Validate input in `store` and return `count` on success or a negative error.
- `DEVICE_ATTR_RO` / `_WO` for read-only/write-only; binary attributes for blobs (e.g. EEPROM contents).
- For debug-only data, use debugfs instead (next question).

### What is the difference between procfs, sysfs and debugfs? {E}
**Short answer:** **procfs** (`/proc`) exposes process information and some legacy kernel tunables (`/proc/cpuinfo`, `/proc/<pid>/maps`, `/proc/sys/` sysctls); new device data should not go there. **sysfs** (`/sys`) exposes the structured device model with one value per file and is a stable ABI. **debugfs** (`/sys/kernel/debug`) is a free-form debugging interface with no ABI guarantees, usually root-only and often disabled in production kernels.

| | procfs | sysfs | debugfs |
|---|---|---|---|
| Purpose | processes, system info, sysctls | devices, drivers, buses, classes | debugging |
| Format | free-form text | one value per file | anything |
| ABI stability | yes (for existing files) | yes | no |
| Typical use | `ps`, `top`, `free` read it | udev, configuration tools, power management | register dumps, statistics, fault injection, tracing (`tracefs`) |
| Driver API | `proc_create` (discouraged for drivers) | `DEVICE_ATTR_*`, attribute groups | `debugfs_create_file/u32/regset32` |

**debugfs example:** `debugfs_create_regset32("regs", 0400, dir, &d->regset)` dumps a list of registers; `debugfs_create_u32("irq_count", 0444, dir, &d->irq_count)` exposes a counter. Errors from debugfs functions can be ignored by design (debugging must not break the driver).

**Other pseudo-filesystems:** `configfs` (user space creates kernel objects: USB gadgets, iSCSI targets), `tracefs` (`/sys/kernel/tracing`), `cgroupfs`, `bpffs`, `securityfs`.

### What is the difference between kmalloc, vmalloc and kzalloc? {M}
**Short answer:** `kmalloc(size, flags)` returns **physically contiguous** memory from the slab allocator: fast, cache-friendly, usable for DMA (through the DMA API), and best for small to medium sizes (practically up to a few pages; large requests may fail when memory is fragmented). `kzalloc` is `kmalloc` plus zeroing, and `kcalloc`/`kmalloc_array` add overflow checks for arrays. `vmalloc(size)` returns memory that is **virtually** contiguous but physically scattered: good for large buffers, but slower (page-table setup, TLB pressure), it may sleep, and it is not directly usable for device DMA. `kvmalloc` tries `kmalloc` and falls back to `vmalloc`.

| | kmalloc / kzalloc | vmalloc | alloc_pages | dma_alloc_coherent |
|---|---|---|---|---|
| Physically contiguous | yes | no | yes (2^order pages) | yes (or IOMMU-contiguous) |
| Size | small–medium | large | whole pages | device buffers |
| Atomic context | yes with `GFP_ATOMIC` | no | yes with `GFP_ATOMIC` | depends; usually process context |
| Free with | `kfree` | `vfree` | `__free_pages` | `dma_free_coherent` |
| Use for | structs, small buffers | large tables, module code | page-level buffers | DMA descriptors, shared buffers |

**Other allocators to mention**

- **`kmem_cache_create` / `kmem_cache_alloc`:** dedicated slab caches for many objects of the same size (e.g. network buffers, inodes).
- **`devm_kzalloc`:** freed automatically when the device unbinds.
- **CMA** (Contiguous Memory Allocator): large physically contiguous buffers for cameras/displays without IOMMU, reserved at boot, used through the DMA API.
- **mempool:** guaranteed allocations under memory pressure for I/O paths.

**Common bugs:** freeing with the wrong function (`kfree` on `vmalloc` memory), forgetting to check for `NULL`, `kmalloc(n * size)` overflow (use `kmalloc_array`), and DMA from stack or `vmalloc` buffers.

### What do GFP_KERNEL and GFP_ATOMIC mean? {E}
**Short answer:** They are allocation flags that tell the allocator what it is allowed to do. `GFP_KERNEL` may sleep to reclaim memory (write back pages, swap, compact), so it may only be used in process context with no spinlocks held; it is the normal choice and rarely fails. `GFP_ATOMIC` never sleeps and may use emergency reserves, so it can be used in interrupt handlers and under spinlocks, but it fails more often and callers must handle `NULL`.

| Flag | Sleeps | Use |
|---|---|---|
| `GFP_KERNEL` | yes | normal kernel allocations in process context |
| `GFP_ATOMIC` | no | IRQ/softirq context, under spinlocks |
| `GFP_NOWAIT` | no | like ATOMIC but without emergency reserves; fail fast |
| `GFP_NOIO` | yes, but no I/O | inside block I/O paths (avoid recursion into the I/O you are servicing) |
| `GFP_NOFS` | yes, but no filesystem calls | inside filesystem code |
| `GFP_DMA` / `GFP_DMA32` | modifier | memory below 16 MB / 4 GB for devices with limited addressing (prefer the DMA API) |
| `__GFP_ZERO` | modifier | zeroed memory (`kzalloc`) |
| `__GFP_NOWARN`, `__GFP_RETRY_MAYFAIL`, `__GFP_NOFAIL` | modifiers | control warnings and retry behaviour |

**Best practice:** avoid allocations in atomic context altogether where possible: preallocate buffers in `probe` or `open`, or use mempools; `memalloc_noio_save()`/`memalloc_nofs_save()` scopes are preferred over passing NOIO/NOFS flags everywhere.

### How does a driver access device registers? {M}
**Short answer:** Map the physical register range into kernel virtual address space (`devm_platform_ioremap_resource()` or `devm_ioremap()`), which returns an `void __iomem *`, then access registers only through the I/O accessors `readl`/`writel` (and `readb/w/q`, `writeb/w/q`), never through plain pointer dereferences. The accessors use the right instruction width, include the barriers needed to order MMIO against DMA and normal memory, and handle endianness. For complex register maps, many drivers use **regmap**.

```c
void __iomem *base = devm_platform_ioremap_resource(pdev, 0);
if (IS_ERR(base)) return PTR_ERR(base);

u32 v = readl(base + CTRL);
writel(v | CTRL_EN, base + CTRL);

/* poll a status bit with timeout (sleeps between reads) */
ret = readl_poll_timeout(base + STATUS, v, v & STATUS_READY, 10, 1000);   /* 10 µs, 1 ms */
if (ret) return dev_err_probe(dev, ret, "device not ready\n");
```

**Accessor variants**

| Accessor | Ordering |
|---|---|
| `readl` / `writel` | ordered against other MMIO and DMA buffers: `writel` comes after earlier normal memory writes (so a descriptor written before the doorbell is visible to the device) |
| `readl_relaxed` / `writel_relaxed` | no barriers against normal memory; faster for register-only sequences |
| `ioread32` / `iowrite32` | work for both MMIO and port I/O (PCI) |
| `ioread32be`, `readl_be` (via `__raw` + swab) | big-endian device registers |
| `readl_poll_timeout(_atomic)` | polling with a timeout |

**Why not a plain pointer:** the compiler may reorder, merge or cache accesses (`volatile` only partly helps), the architecture may need specific instructions or barriers (Arm device memory, `dsb`/`dmb`), and sparse checks `__iomem` annotations to catch mistakes.

**Bit helpers:** `FIELD_PREP(GENMASK(7, 4), val)` and `FIELD_GET` from `<linux/bitfield.h>` make field updates clear.

**Debugging from user space:** `devmem2` or `busybox devmem 0x40010000 32` (needs `/dev/mem` access, often restricted with `CONFIG_STRICT_DEVMEM`).

### How do drivers do DMA in Linux? {H}
**Short answer:** Drivers use the **DMA API**, which hides IOMMUs, bus-address translation, bounce buffers and cache maintenance. **Coherent mappings** (`dma_alloc_coherent()`) give a buffer that CPU and device can both access at any time without explicit cache operations, used for descriptor rings and long-lived shared structures. **Streaming mappings** (`dma_map_single()`, `dma_map_sg()`) map an existing buffer for one transfer in one direction, with ownership handed between CPU and device by `dma_unmap_*` or `dma_sync_*_for_cpu/for_device`. The device is told the returned `dma_addr_t`, never the CPU virtual or physical address. Transfers through a separate DMA controller use the **dmaengine** API.

**Setup and coherent buffer**

```c
ret = dma_set_mask_and_coherent(dev, DMA_BIT_MASK(32));   /* device can address 32 bits */
if (ret) return ret;

d->ring = dma_alloc_coherent(dev, RING_BYTES, &d->ring_dma, GFP_KERNEL);
if (!d->ring) return -ENOMEM;
writel(lower_32_bits(d->ring_dma), d->base + RING_BASE);  /* the device gets the DMA address */
```

**Streaming mapping for a transmit buffer**

```c
dma_addr_t a = dma_map_single(dev, skb_data, len, DMA_TO_DEVICE);   /* cleans caches */
if (dma_mapping_error(dev, a)) return -ENOMEM;
desc->addr = cpu_to_le64(a);
desc->len  = cpu_to_le32(len);
dma_wmb();                                   /* descriptor fields visible before ownership flag */
desc->flags = cpu_to_le32(DESC_OWN_HW);
writel(1, d->base + DOORBELL);
/* in the completion handler: dma_unmap_single(dev, a, len, DMA_TO_DEVICE); */
```

**dmaengine (memory ↔ peripheral via a system DMA controller)**

```c
/* Illustrative fragment: check IS_ERR(chan), configuration result,
 * descriptor allocation and dma_submit_error(cookie) in real code. */
chan = dma_request_chan(dev, "rx");                       /* from DT dmas/dma-names */
dmaengine_slave_config(chan, &cfg);                       /* FIFO address, width, burst */
desc = dmaengine_prep_slave_single(chan, buf_dma, len, DMA_DEV_TO_MEM, DMA_PREP_INTERRUPT);
desc->callback = rx_done; desc->callback_param = d;
dmaengine_submit(desc);
dma_async_issue_pending(chan);
```

**Rules**

- Do not pass stack or vmalloc addresses to dma_map_single(). For non-contiguous memory, use suitable page/scatter-gather mappings and respect the platform DMA API.
- Do not touch a streaming buffer while the device owns it.
- With non-coherent devices, the DMA API performs cache clean/invalidate; buffers should be cache-line aligned (kmalloc guarantees `ARCH_DMA_MINALIGN`).
- **IOMMU** (Arm SMMU, Intel VT-d) translates device addresses, gives isolation and makes scattered pages look contiguous to the device.
- **dma-buf** shares DMA buffers between drivers (camera → GPU → display) without copying.

### How does mmap work in a driver? {H}
**Short answer:** Implementing `.mmap` lets user space map device memory or a driver buffer directly into its address space, avoiding copies. The driver checks the requested size and offset in the `vm_area_struct`, then maps the pages: `remap_pfn_range()` (or `io_remap_pfn_range` / `vm_iomap_memory()`) for device registers or reserved physical memory, `dma_mmap_coherent()` for DMA buffers, or `vm_insert_page`/`vm_map_pages` for normal kernel pages. Register mappings must be **uncached** (`pgprot_noncached` / `pgprot_device`).

**Mapping a DMA buffer to user space**

```c
static int mydev_mmap(struct file *f, struct vm_area_struct *vma)
{
    struct mydev *d = f->private_data;
    size_t size = vma->vm_end - vma->vm_start;

    if (vma->vm_pgoff != 0 || size > d->buf_size)
        return -EINVAL;                               /* never map more than you own */
    return dma_mmap_coherent(d->dev, vma, d->buf, d->buf_dma, size);
}
```

**Mapping a register page (e.g. for a user-space data path)**

```c
static int regs_mmap(struct file *f, struct vm_area_struct *vma)
{
    struct mydev *d = f->private_data;
    vma->vm_page_prot = pgprot_noncached(vma->vm_page_prot);
    return vm_iomap_memory(vma, d->regs_phys, d->regs_len);   /* checks size/offset for you */
}
```

**User space**

```c
uint32_t *buf = mmap(NULL, 4096, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
```

**Points to discuss**

- **Security:** validate size and offset; exposing registers can let user space break isolation (e.g. by programming DMA to arbitrary memory) — usually only for trusted or privileged processes, or use VFIO with an IOMMU.
- **Lifetime:** the mapping can outlive `close()`; the buffer must stay valid until the VMA is unmapped (reference counting, or `vm_operations_struct.close`).
- **Synchronisation:** user space and hardware now share memory directly: define a protocol (head/tail indices, memory barriers, cache maintenance for non-coherent buffers).
- **Page-fault-based mapping:** for large or lazily allocated buffers, implement `vm_ops->fault` and insert pages on demand.
- Frameworks provide this already: V4L2 (`VIDIOC_REQBUFS` + mmap), DRM dumb buffers/GEM, UIO, and `dma-heap`.

### What are kernel timers, hrtimers and delays? {M}
**Short answer:** **Timers** (`timer_list`, `mod_timer`) run a callback in softirq context after a delay measured in **jiffies** (resolution 1/HZ, e.g. 4 ms with HZ=250), suitable for timeouts that do not need precision. **High-resolution timers** (`hrtimer`) have nanosecond-based expiry using the hardware clock event device, for precise timing. For **delays**, use `udelay`/`ndelay` (busy-wait, for microseconds, allowed in atomic context), `usleep_range` (sleep, 10 µs–20 ms), and `msleep`/`fsleep` (sleep, longer).

**Timer example (watchdog-style timeout)**

```c
static void mydev_timeout(struct timer_list *t)
{
    struct mydev *d = from_timer(d, t, timer);      /* timer_container_of() on newest kernels */
    dev_warn(d->dev, "no response, resetting\n");
    schedule_work(&d->reset_work);                  /* softirq context: defer anything that sleeps */
}

timer_setup(&d->timer, mydev_timeout, 0);           /* in probe */
mod_timer(&d->timer, jiffies + msecs_to_jiffies(500));   /* (re)arm */
timer_delete_sync(&d->timer);                       /* in remove (del_timer_sync on older kernels) */
```

**hrtimer example (periodic 1 ms)**

```c
static enum hrtimer_restart tick(struct hrtimer *t)
{
    struct mydev *d = container_of(t, struct mydev, hrt);
    sample(d);
    hrtimer_forward_now(t, ms_to_ktime(1));
    return HRTIMER_RESTART;
}
hrtimer_setup(&d->hrt, tick, CLOCK_MONOTONIC, HRTIMER_MODE_REL);  /* hrtimer_init on older kernels */
hrtimer_start(&d->hrt, ms_to_ktime(1), HRTIMER_MODE_REL);
```

**Choosing a delay**

| Duration | Context | Use |
|---|---|---|
| < 10 µs | any | `udelay`, `ndelay` |
| 10 µs – 20 ms | process | `usleep_range(min, max)` (gives the scheduler slack to batch wake-ups) |
| > 10 ms | process | `msleep`, `msleep_interruptible` |
| unsure | process | `fsleep(us)` picks the right function |

**Pitfalls:** `msleep(1)` can sleep much longer (rounded up to jiffies, at least 1–2 jiffies); compare jiffies with `time_after()` (handles wrap-around); always cancel timers synchronously before freeing their data.

### How does power management work for drivers (system suspend and runtime PM)? {H}
**Short answer:** Drivers implement two kinds of power management through `dev_pm_ops`. **System sleep** callbacks (`suspend`/`resume`, plus `_late`/`_noirq` variants) save state and power the device down when the whole system suspends (to RAM or disk), then restore it. **Runtime PM** (`runtime_suspend`/`runtime_resume`) powers an individual device down whenever it is idle while the system runs: the driver calls `pm_runtime_resume_and_get()` before using the hardware and `pm_runtime_put_autosuspend()` when done, and the core suspends it after an autosuspend delay when the usage count reaches zero.

```c
static int mydev_runtime_suspend(struct device *dev)
{
    struct mydev *d = dev_get_drvdata(dev);
    clk_disable_unprepare(d->clk);
    return regulator_disable(d->vdd);
}

static int mydev_runtime_resume(struct device *dev)
{
    struct mydev *d = dev_get_drvdata(dev);
    int ret = regulator_enable(d->vdd);
    if (ret) return ret;
    ret = clk_prepare_enable(d->clk);
    if (ret) { regulator_disable(d->vdd); return ret; }
    regcache_cache_only(d->map, false);
    return regcache_sync(d->map);                 /* restore registers after power loss */
}

static const struct dev_pm_ops mydev_pm = {
    RUNTIME_PM_OPS(mydev_runtime_suspend, mydev_runtime_resume, NULL)
    SYSTEM_SLEEP_PM_OPS(pm_runtime_force_suspend, pm_runtime_force_resume)
};
/* .driver.pm = pm_ptr(&mydev_pm) */

/* in probe */
pm_runtime_set_autosuspend_delay(dev, 200);
pm_runtime_use_autosuspend(dev);
devm_pm_runtime_enable(dev);

/* around each hardware access */
ret = pm_runtime_resume_and_get(dev);
if (ret) return ret;
do_transfer(d);
pm_runtime_mark_last_busy(dev);
pm_runtime_put_autosuspend(dev);
```

**Concepts to mention**

- **Device hierarchy:** children suspend before parents and resume after them; device links handle non-parent dependencies (fw_devlink).
- **PM domains (genpd):** power islands shared by several devices, switched off when all are runtime-suspended.
- **Wake-up sources:** `device_init_wakeup()`, `enable_irq_wake()` so a button or RTC can wake the system.
- **Clocks and voltages:** DVFS via OPP tables and cpufreq/devfreq; interconnect bandwidth votes.
- **Debugging:** `/sys/devices/.../power/runtime_status`, `/sys/kernel/debug/pm_genpd/`, `echo mem > /sys/power/state`, `pm_test`, and `no_console_suspend` to see messages during suspend.

### What is PREEMPT_RT and what changes for drivers? {H}
**Short answer:** PREEMPT_RT (merged into mainline in 6.12, `CONFIG_PREEMPT_RT`) turns Linux into a real-time OS with bounded latencies of typically tens of microseconds. It makes almost all kernel code pre-emptible: interrupt handlers run in **threads** with configurable priorities, `spinlock_t` and `rwlock_t` become **sleeping rt_mutexes with priority inheritance**, softirqs run in thread context, and long non-pre-emptible sections are broken up. Drivers must not rely on "spinlock means interrupts and pre-emption are off".

**What changes**

| | Standard kernel | PREEMPT_RT |
|---|---|---|
| Hard IRQ handlers | run in interrupt context | forced into threads (`irq/NN-name`, SCHED_FIFO 50) unless `IRQF_NO_THREAD` |
| `spinlock_t` | spins, disables pre-emption | sleeping lock (rt_mutex) with priority inheritance |
| `raw_spinlock_t` | spins | still spins: only for very short, truly atomic sections (IRQ chips, scheduler) |
| `local_irq_disable()` around data | common (bad) practice | breaks: use proper locks (`local_lock`) |
| Softirqs | after IRQs, or ksoftirqd | in thread context, per-CPU, pre-emptible |
| Memory allocation under spinlock | allowed with `GFP_ATOMIC` | spinlocks can sleep, so allocations in raw-spinlock or hard-IRQ sections are forbidden |

**Driver guidelines for RT**

- Use threaded IRQs and normal `spinlock_t`; use `raw_spinlock_t` only where required (interrupt controller, clock event code) and keep those sections tiny.
- Do not disable interrupts or pre-emption to protect data; use locks or `local_lock_t` for per-CPU data.
- Avoid unbounded loops with locks held.
- Mark interrupt handlers that must stay in hard IRQ context with `IRQF_NO_THREAD` (timers, IPIs) and keep them minimal.

**Tuning a real-time system**

1. RT application threads use `SCHED_FIFO` with priorities above the IRQ threads they don't depend on; set the relevant IRQ thread priorities with `chrt`.
2. `mlockall(MCL_CURRENT | MCL_FUTURE)` and pre-fault stacks/heap to avoid page faults.
3. Isolate CPUs (`isolcpus=`, `nohz_full=`, `rcu_nocbs=`, `irqaffinity=`) for critical threads.
4. Disable deep CPU idle states and frequency scaling for lowest latency, or accept the trade-off.
5. Measure with `cyclictest` under load (`stress-ng`, `hackbench`), and find latency sources with `ftrace` (osnoise, timerlat tracers, `rtla`).

**Limits:** RT Linux gives bounded latency for most workloads but is not formally certified for hard safety-critical use; those systems pair Linux with an RTOS on another core or a hypervisor.

### How do you write a user-space driver, and when is it a good idea (UIO, VFIO, spidev, libgpiod)? {M}
**Short answer:** Some devices can be driven from user space using generic kernel interfaces: **UIO** maps device registers into a process and delivers interrupts via `read()` on `/dev/uioN`; **VFIO** does the same with IOMMU protection and full DMA support (used by DPDK, SPDK and QEMU device pass-through); **spidev**, **i2c-dev** and **libgpiod** (`/dev/gpiochipN` character device) expose buses and GPIOs. User-space drivers are easier to develop and debug and avoid GPL constraints, but they have higher latency for interrupts, cannot integrate with kernel subsystems (network stack, filesystems, input), and need care with security.

| Interface | Gives | Typical use |
|---|---|---|
| UIO (`uio_pdrv_genirq`) | mmap of registers, interrupt count via `read`, re-enable via `write` | FPGA IP cores, simple custom peripherals |
| VFIO (`vfio-pci`, `vfio-platform`) | registers, interrupts via eventfd, IOMMU-protected DMA | DPDK/SPDK high-performance NIC/NVMe drivers, VM pass-through |
| spidev / i2c-dev | raw SPI/I2C transfers | prototyping, simple sensors |
| GPIO character device (libgpiod) | line requests, events with timestamps | buttons, enables, bit-banging (the old sysfs GPIO interface is deprecated) |

**UIO interrupt loop**

```c
int fd = open("/dev/uio0", O_RDWR);
volatile uint32_t *regs = mmap(NULL, 4096, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
uint32_t enable = 1, count;
for (;;) {
    write(fd, &enable, sizeof enable);         /* (re)enable the interrupt */
    read(fd, &count, sizeof count);            /* blocks until the next interrupt */
    handle(regs);
}
```

**When kernel drivers are the right choice:** the device must integrate with a subsystem (Ethernet, storage, display, input, audio), needs low interrupt latency, must be shared safely among processes, must work at boot before user space, or must protect the system from misbehaving software (DMA without an IOMMU).

**When user space is fine:** prototypes, low-rate devices, high-throughput polling designs (DPDK), and proprietary code that cannot be GPL.

### How does the kernel boot on an ARM64 system? {M}
**Short answer:** The boot ROM loads a first-stage loader (SPL or TF-A BL2) that initialises DRAM; Trusted Firmware-A sets up the secure world and EL3 services (PSCI), then hands over to U-Boot or UEFI at EL2; the bootloader loads the kernel `Image`, the device tree and optionally an initramfs, and jumps to the kernel with the DTB address in `x0`, MMU off, at EL2 or EL1. The kernel sets up page tables and enables the MMU, then `start_kernel()` initialises memory, interrupts, timers and the scheduler, brings up secondary CPUs through PSCI, runs driver initcalls (probing devices from the DT), mounts the root filesystem and executes `/sbin/init` as PID 1.

**Kernel-side steps in more detail**

1. `head.S` (`primary_entry`): checks the boot exception level, sets up identity and kernel page tables, enables the MMU, jumps to the virtual address space.
2. `start_kernel()`: `setup_arch()` (parse DT memory, reserved regions, early console via `earlycon`), memory allocators (memblock → buddy/slab), `trap_init`, IRQ controller (GIC) init, timers (arch timer), `sched_init`, console, `rest_init()`.
3. `kernel_init` thread: SMP bring-up (`PSCI CPU_ON`), `do_initcalls()` in levels (core → postcore → arch → subsys → fs → device → late), which registers buses and drivers; devices from the DT are created by `of_platform_populate`.
4. Unpack initramfs (if any) and run its `/init`, or mount the root device given by `root=` and run `/sbin/init`.
5. PID 1 (systemd, BusyBox init) starts services and user space.

**Debugging early boot:** `earlycon` on the kernel command line, `initcall_debug`, `ignore_loglevel`, `keep_bootcon`, JTAG with the kernel stopped at `start_kernel`, and checking that the DTB address and memory node are correct.

See the Embedded Linux topic for bootloader details (SPL, U-Boot internals, FIT images).

### How do you debug a kernel oops or panic? {M}
**Short answer:** Read the oops message: it gives the reason (e.g. "Unable to handle kernel NULL pointer dereference at virtual address 0000000000000010"), the faulting instruction (`pc : my_func+0x48/0x120 [mymod]`), registers and the call trace. Translate the offset to a source line with `scripts/faddr2line` or gdb on a debug build, reproduce with debugging options enabled (KASAN, lockdep, KCSAN, `DEBUG_ATOMIC_SLEEP`), and use tracing (ftrace, dynamic debug) to see what led up to it. For crashes that stop the system, capture logs over serial, with pstore/ramoops, or with kdump.

**Reading an oops**

```
Unable to handle kernel NULL pointer dereference at virtual address 0000000000000010
pc : mydev_irq+0x24/0x80 [mydev]
lr : __handle_irq_event_percpu+0x5c/0x1e0
...
Call trace:
 mydev_irq+0x24/0x80 [mydev]
 handle_irq_event+0x4c/0xa8
 ...
```

- Address 0x10 → dereferencing a field at offset 16 of a NULL struct pointer.
- `pc` gives function + offset/size; `lr` the caller.
- "Tainted: G O" flags show out-of-tree (O) or proprietary (P) modules are loaded.

```sh
./scripts/faddr2line drivers/misc/mydev.ko mydev_irq+0x24/0x80
# or
gdb drivers/misc/mydev.ko -ex 'list *(mydev_irq+0x24)'
./scripts/decode_stacktrace.sh vmlinux < oops.txt      # decodes a whole trace
```

**Toolbox**

| Problem | Tool |
|---|---|
| use-after-free, out-of-bounds | KASAN (`CONFIG_KASAN`), KFENCE (low-overhead, for production) |
| locking errors, deadlocks | lockdep (`CONFIG_PROVE_LOCKING`) |
| data races | KCSAN |
| sleeping in atomic context | `CONFIG_DEBUG_ATOMIC_SLEEP` |
| memory leaks | kmemleak |
| hangs | soft/hard lockup and hung task detectors, `echo t > /proc/sysrq-trigger`, `echo l > ...` (backtraces of all CPUs) |
| understanding flow | ftrace (`function_graph`), tracepoints, `trace-cmd`/KernelShark, `pr_debug` with dynamic debug, bpftrace |
| crash dumps | kdump + `crash` utility, pstore/ramoops (logs survive reboot) |
| live debugging | KGDB over serial, JTAG/OpenOCD with `vmlinux` symbols, QEMU + gdb (`-s -S`) |

**Method:** make it reproducible, simplify the test case, check recent changes (`git bisect`), and check the obvious: reference counting, missing locking, use after `remove()`, IRQ firing before initialisation completes.

### What is the DRM/KMS display stack? {H}
**Short answer:** The Direct Rendering Manager (DRM) is the Linux graphics and display subsystem; **KMS** (kernel mode setting) is the display part. KMS models the display pipeline as objects: **framebuffers** (memory holding pixels, backed by GEM buffer objects), **planes** (layers that scan out a framebuffer: primary, overlay, cursor, with format, scaling and position), **CRTCs** (the scan-out engines that blend planes and generate timing for one display mode), **encoders** (convert the pixel stream to a signal type: DSI, HDMI, eDP, LVDS) and **connectors** (the outputs with their modes and hot-plug status), plus **bridges** and **panels** for external chips and displays. User space commits a complete new state with the **atomic** API, which is validated (`atomic_check`) and committed by the driver. Normal synchronized page flips typically latch at vblank; asynchronous flips may tear, and modesets can temporarily blank the output.

```
GEM buffers → framebuffers → planes ─┐
                                     ├→ CRTC (timing, blending) → encoder → bridge(s) → connector → panel/monitor
                         overlay ────┘
```

**Atomic commit flow**

1. User space (Wayland compositor, Android HWComposer via drm_hwcomposer, `modetest`, Weston) builds a property set: plane FB_ID, CRTC_X/Y/W/H, CRTC MODE_ID, ACTIVE, connector CRTC_ID.
2. `DRM_IOCTL_MODE_ATOMIC` with `TEST_ONLY` can check a configuration without applying it.
3. The driver's `atomic_check` callbacks validate bandwidth, formats, scaling limits and clocks.
4. `atomic_commit` programs the hardware (usually through helpers: `drm_atomic_helper_commit_tail`), arranges hardware programming and completion. A synchronized page flip commonly latches at vblank; completion events are delivered according to the driver's hardware and commit semantics.

**MIPI DSI panel driver essentials**

```c
static int mypanel_prepare(struct drm_panel *panel)
{
    struct mypanel *p = container_of(panel, struct mypanel, panel);
    int ret = regulator_bulk_enable(ARRAY_SIZE(p->supplies), p->supplies);
    if (ret) return ret;
    gpiod_set_value_cansleep(p->reset, 0);
    msleep(20);
    mipi_dsi_dcs_exit_sleep_mode(p->dsi);
    msleep(120);
    return mipi_dsi_dcs_set_display_on(p->dsi);
}
/* get_modes() returns the panel's drm_display_mode (timings, size);
 * probe sets dsi->lanes, dsi->format, dsi->mode_flags and calls mipi_dsi_attach() */
```

**Concepts interviewers probe**

- **GEM** (buffer objects), **dumb buffers** (simple CPU-drawn framebuffers), **PRIME/dma-buf** (sharing buffers between GPU, camera and display), **fences** (implicit/explicit synchronisation: render finished before scan-out).
- **Vblank handling** and page-flip events; **underflow** debugging (memory bandwidth, QoS, clocks).
- **Mode timings:** pixel clock, hactive/hfp/hsync/hbp, same for vertical; refresh = pixel clock / (htotal × vtotal).
- **DSI:** video vs command mode, lanes, burst mode, low-power vs high-speed transmission for DCS commands.
- Debug: `modetest -M <driver>`, `/sys/kernel/debug/dri/0/state`, `drm.debug=0x1e` on the command line, `cat /sys/class/drm/card0-DSI-1/modes`.

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
