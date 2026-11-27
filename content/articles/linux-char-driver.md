---
title: Writing Your First Linux Character Driver
tag: Linux Kernel
desc: A complete, modern misc character driver with read, write and a wait queue, plus the questions interviewers ask about it.
date: 2026-11-20
order: 3
---

A **character driver** exposes a device file (e.g. /dev/echofifo) and handles user-space operations through file_operations.

## Driver flow

```text
Application → open/read/write/poll → System call → VFS
→ Driver file_operations → Device or kernel buffer
```

This example uses a misc device, a kernel FIFO, a mutex and a wait queue. Reads block until data arrives; writes return an error when the FIFO is full.

## Complete example

```c
// SPDX-License-Identifier: GPL-2.0
#include <linux/module.h>
#include <linux/miscdevice.h>
#include <linux/fs.h>
#include <linux/kfifo.h>
#include <linux/mutex.h>
#include <linux/wait.h>
#include <linux/poll.h>

static DEFINE_KFIFO(fifo, char, 1024);
static DEFINE_MUTEX(lock);
static DECLARE_WAIT_QUEUE_HEAD(q);

static bool has_data(void)
{
    return READ_ONCE(fifo.kfifo.in) != READ_ONCE(fifo.kfifo.out);
}

static ssize_t echo_read(struct file *f, char __user *buf,
                         size_t len, loff_t *off)
{
    unsigned int copied = 0;
    int ret;

    if (!len)
        return 0;
    for (;;) {
        if (mutex_lock_interruptible(&lock))
            return -ERESTARTSYS;
        if (!kfifo_is_empty(&fifo))
            break;
        mutex_unlock(&lock);

        if (f->f_flags & O_NONBLOCK)
            return -EAGAIN;
        ret = wait_event_interruptible(q, has_data());
        if (ret)
            return ret;
    }

    ret = kfifo_to_user(&fifo, buf, len, &copied);
    mutex_unlock(&lock);
    if (copied)
        wake_up_interruptible(&q);
    return copied ? (ssize_t)copied : ret;
}

static ssize_t echo_write(struct file *f, const char __user *buf,
                          size_t len, loff_t *off)
{
    unsigned int copied = 0;
    int ret;

    if (!len)
        return 0;
    if (mutex_lock_interruptible(&lock))
        return -ERESTARTSYS;
    ret = kfifo_from_user(&fifo, buf, len, &copied);
    mutex_unlock(&lock);

    if (copied) {
        wake_up_interruptible(&q);
        return copied;
    }
    if (ret)
        return ret;
    return (f->f_flags & O_NONBLOCK) ? -EAGAIN : -ENOSPC;
}

static __poll_t echo_poll(struct file *f, poll_table *wait)
{
    __poll_t mask = 0;

    poll_wait(f, &q, wait);
    mutex_lock(&lock);
    if (!kfifo_is_empty(&fifo))
        mask |= EPOLLIN | EPOLLRDNORM;
    if (!kfifo_is_full(&fifo))
        mask |= EPOLLOUT | EPOLLWRNORM;
    mutex_unlock(&lock);
    return mask;
}

static const struct file_operations echo_fops = {
    .owner = THIS_MODULE,
    .read = echo_read,
    .write = echo_write,
    .poll = echo_poll,
    .llseek = no_llseek,
};

static struct miscdevice echo_dev = {
    .minor = MISC_DYNAMIC_MINOR,
    .name = "echofifo",
    .fops = &echo_fops,
    .mode = 0600,
};

module_misc_device(echo_dev);
MODULE_LICENSE("GPL");
```

For kernels where no_llseek is unavailable, omit .llseek. Save as echofifo.c.

## Build and test

```makefile
obj-m += echofifo.o
```

```sh
make -C /lib/modules/$(uname -r)/build M="$PWD" modules
sudo insmod echofifo.ko
# Terminal 1:
sudo cat /dev/echofifo
# Terminal 2:
echo hello | sudo tee /dev/echofifo
# Stop cat before unloading:
sudo rmmod echofifo
```

## Important functions

| Function | Purpose |
|---|---|
| misc_register() | Registers misc character device |
| kfifo_from_user() / kfifo_to_user() | Transfers data between user space and FIFO |
| mutex_lock_interruptible() | Serializes process-context access |
| wait_event_interruptible() | Sleeps until data is available or a signal arrives |
| wake_up_interruptible() | Wakes waiting tasks |
| poll_wait() | Registers readiness notification |

## Interview follow-ups

- **Normal cdev registration:** alloc_chrdev_region → cdev_init → cdev_add → class_create → device_create.
- **Why not dereference user pointers?** Use copy_to_user/copy_from_user to safely access user memory.
- **Why mutex?** User-copy can sleep. Never hold a spinlock across a user-copy operation.
- **Multiple readers?** Recheck FIFO state under the mutex after waking.
- **Real hardware?** Match the device tree in probe(), map registers, request IRQ and use the appropriate kernel subsystem (IIO, input, DRM/KMS, etc.).
- **Debugging:** dmesg, dynamic debug, strace and lockdep.

This is an illustrative module; build and test against your target kernel before use.
