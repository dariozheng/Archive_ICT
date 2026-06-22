---
categories:
  - "[[Linux]]"
topic@linux:
tags:
  - glossaries
---
#### kernel modules
independent pieces of compiled C code that extend the functionality of the Linux operating system without requiring you to reboot the computer.

They act like software plugins for the Linux kernel, loaded using commands like `insmod` or `modprobe`.
Because they run inside the kernel space, they have direct access to system hardware and network packets.
They run at the highest privilege level, making packet processing incredibly fast.