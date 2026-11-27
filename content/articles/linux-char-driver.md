---
title: Writing Your First Linux Character Driver
tag: Linux Kernel
desc: A complete, modern misc character driver with read, write and a wait queue, plus the questions interviewers ask about it.
date: 2026-11-20
order: 3
---

A character driver exposes a device file such as /dev/echofifo.

**Flow:** Application → system call → VFS → file_operations → driver → hardware or buffer.

## Complete C example

This misc driver implements blocking reads, FIFO writes, poll and synchronization.

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

## Key functions

| Function | Purpose |
|---|---|
| misc_register() | Registers the character device |
| read / write | Transfers data to/from userspace |
| kfifo_to_user / kfifo_from_user | Safely copies data |
| mutex_lock | Serializes access; user-copy may sleep |
| wait_event_interruptible | Blocks a reader when FIFO is empty |
| wake_up_interruptible | Notifies readers and poll waiters |
| poll_wait | Registers readiness notification |

## Build and test

Save as echofifo.c. Set the Kbuild Makefile to obj-m += echofifo.o. Build using make -C /lib/modules/$(uname -r)/build M="$PWD" modules. Load with sudo insmod echofifo.ko, read /dev/echofifo in one terminal and write to it in another (root permissions required). Stop readers before unloading.

For a conventional character driver, use alloc_chrdev_region → cdev_init → cdev_add → class_create → device_create.

This example must be built and tested against the target kernel.
