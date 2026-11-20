---
title: Writing Your First Linux Character Driver
tag: Linux Kernel
desc: A complete, modern misc character driver with read, write and a wait queue, plus the questions interviewers ask about it.
date: 2026-11-20
order: 3
---
Linux driver interviews often ask you to "walk through a character driver". This article builds a small but realistic one: a FIFO device that buffers writes and lets readers block until data arrives. Along the way it covers the concepts behind the follow-up questions.

## The plan

- Register a **misc device** so `/dev/echofifo` appears automatically.
- `write()` copies data from user space into a kernel FIFO.
- `read()` blocks until the FIFO has data, then copies it out.
- `poll()` lets user space use `select`/`poll`/`epoll`.
- A mutex serialises access.

## The code

```c
// SPDX-License-Identifier: GPL-2.0
#include <linux/module.h>
#include <linux/miscdevice.h>
#include <linux/fs.h>
#include <linux/kfifo.h>
#include <linux/mutex.h>
#include <linux/wait.h>
#include <linux/poll.h>

#define FIFO_SIZE 1024

static DEFINE_KFIFO(fifo, char, FIFO_SIZE);
static DEFINE_MUTEX(lock);
static DECLARE_WAIT_QUEUE_HEAD(readq);

static ssize_t echo_read(struct file *f, char __user *buf, size_t len, loff_t *off)
{
    unsigned int copied;
    int ret;

    if (kfifo_is_empty(&fifo)) {
        if (f->f_flags & O_NONBLOCK)
            return -EAGAIN;
        if (wait_event_interruptible(readq, !kfifo_is_empty(&fifo)))
            return -ERESTARTSYS;            /* interrupted by a signal */
    }

    if (mutex_lock_interruptible(&lock))
        return -ERESTARTSYS;
    ret = kfifo_to_user(&fifo, buf, len, &copied);
    mutex_unlock(&lock);

    return ret ? ret : copied;
}

static ssize_t echo_write(struct file *f, const char __user *buf, size_t len, loff_t *off)
{
    unsigned int copied;
    int ret;

    if (mutex_lock_interruptible(&lock))
        return -ERESTARTSYS;
    ret = kfifo_from_user(&fifo, buf, len, &copied);
    mutex_unlock(&lock);

    if (copied)
        wake_up_interruptible(&readq);
    if (ret)
        return ret;
    return copied ? copied : -ENOSPC;
}

static __poll_t echo_poll(struct file *f, poll_table *wait)
{
    __poll_t mask = 0;

    poll_wait(f, &readq, wait);
    if (!kfifo_is_empty(&fifo))
        mask |= EPOLLIN | EPOLLRDNORM;
    if (!kfifo_is_full(&fifo))
        mask |= EPOLLOUT | EPOLLWRNORM;
    return mask;
}

static const struct file_operations echo_fops = {
    .owner  = THIS_MODULE,
    .read   = echo_read,
    .write  = echo_write,
    .poll   = echo_poll,
    .llseek = noop_llseek,
};

static struct miscdevice echo_dev = {
    .minor = MISC_DYNAMIC_MINOR,
    .name  = "echofifo",
    .fops  = &echo_fops,
    .mode  = 0666,
};

module_misc_device(echo_dev);

MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Blocking FIFO character device example");
```

Build it with the usual out-of-tree Kbuild Makefile (`obj-m += echofifo.o`) and try it:

```sh
sudo insmod echofifo.ko
cat /dev/echofifo &          # blocks
echo "hello kernel" > /dev/echofifo
# the background cat prints: hello kernel
```

## Walking through it

**Registration.** `module_misc_device()` expands to init and exit functions that call `misc_register()` and `misc_deregister()`. A misc device shares major number 10 and gets a dynamic minor; the misc core creates the device in sysfs so udev creates `/dev/echofifo`. The long way is `alloc_chrdev_region()` + `cdev_init()`/`cdev_add()` + `class_create()`/`device_create()`, which you need when one driver handles many minors.

**`__user` pointers.** The `__user` annotation marks pointers into user space. They must never be dereferenced directly; `kfifo_to_user()` and `kfifo_from_user()` use `copy_to_user()`/`copy_from_user()` internally, which validate the address and handle page faults. Running `sparse` (`make C=1`) checks these annotations.

**Blocking.** `wait_event_interruptible()` puts the process to sleep on the wait queue until the condition is true, re-checking it after each wake-up. Returning `-ERESTARTSYS` when a signal arrives lets the kernel restart the system call or return `EINTR`. Honouring `O_NONBLOCK` is part of the contract for character devices.

**Waking up.** The writer calls `wake_up_interruptible()` after adding data. In a real hardware driver, this call would be in the interrupt handler (or its threaded half) when the device receives data.

**Locking.** The kfifo is safe without locking only with one reader and one writer. Several processes can open the device, so a mutex serialises access. A mutex is fine here because both paths run in process context and may sleep inside `copy_*_user()`. If the interrupt handler touched the FIFO, you would need a spinlock with `spin_lock_irqsave()` and could not call `copy_to_user` while holding it.

**Return values.** `read`/`write` return the number of bytes transferred or a negative errno. Returning 0 from `read` means end-of-file, which is why the code blocks instead of returning 0 when the FIFO is empty.

## Follow-up questions to expect

- *What happens if two readers wait at once?* Both wake up; one gets the data and the other may read nothing and should wait again. Using `wait_event_interruptible_exclusive()` wakes only one.
- *How would you add an ioctl to flush the FIFO?* Define `_IO('E', 1)`, implement `.unlocked_ioctl`, and call `kfifo_reset()` under the lock.
- *How do you connect this to real hardware?* Make it a platform driver: match a device tree `compatible`, map registers in `probe()` with `devm_platform_ioremap_resource()`, request the IRQ with `devm_request_threaded_irq()`, and push received bytes into the FIFO from the handler.
- *Why misc instead of cdev?* Less boilerplate for a single device node. Use a full cdev when you need multiple minors or your own major.
- *How do you debug it?* `pr_debug()` with dynamic debug, `dmesg`, `strace` on the user program, and `lockdep` to check the locking.

## Where to go next

Real drivers rarely expose raw character devices. Once you can write this one, learn the subsystem that matches your hardware: IIO for sensors, input for buttons and touch, V4L2 for cameras, ALSA for audio, and DRM/KMS for displays. Each one gives user space a standard interface, so existing tools and libraries work with your hardware unchanged.
