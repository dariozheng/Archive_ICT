---
categories:
  - "[[Networking]]"
topic@networking:
  - "[[Networking General]]"
tags:
created: 2026-01-27T16:24:43+01:00
modified: 2026-01-27T17:18:44+01:00
aliases:
  - backhauling
  - network backhauling
  - network backhaul
---
<mark style="background: #FF5582A6;"><strong>Backhaul</strong> in networking refers to the infrastructure that connects a local network, or subnetwork, to a backbone or core network</mark>. 

<strong>Backhauling</strong> in networking is <mark style="background: #BBFABBA6;">the process of transmitting data from local, edge, or cellular access points (like cell towers or branch office routers) back to a central network, core, or the internet</mark>. It serves as a high-capacity, often long-distance link, connecting local networks to a larger network backbone.

It’s typically a high capacity, low latency link designed to transmit data efficiently and fast.
<strong>Internet service providers</strong> (<strong>ISPs</strong>) use backhaul to deliver internet access. 
ISPs connect you to the internet through a backbone network connecting data centers linked to an internet gateway.

<strong>Backhaul</strong>, or exchange backhaul, i<mark style="background: #FFB8EBA6;">s the <strong>subnetwork</strong> that connects</mark> these <mark style="background: #BBFABBA6;">data centers</mark> to <mark style="background: #ABF7F7A6;">local exchanges</mark>. <mark style="background: #FFF3A3A6;">These exchanges typically link to street cabinets, which link to your router by copper or fibre optic cable, delivering internet to your office or home.</mark>

<mark style="background: #FFF3A3A6;">Backhaul is also used for mobile data access. When you browse the internet on your mobile phone, your device connects to cell towers in a local Radio Access Network (RAN)</mark>.

Backhaul is this local RAN and its related infrastructure, which connects your mobile device to a wired backbone network and the internet.

# How does backhaul work?
![[Backhaul.png]]
1. **Data Centre**: When a customer requests a movie, the content is retrieved from Netflix’s servers in a data centre.
2. **Backbone network**: The data travels through the backbone network, a high capacity network that connects regions, ISPs and data centres to the internet and cloud services.
3. **Exchange backhaul**: Backhaul connects the backbone network to your local exchange, ensuring the data is transported efficiently to and from the internet.
4. **Access network**: If the customer uses a fixed-line connection like DSL or fibre, the data may pass through a street cabinet connecting to their home or business.
5. **Router**: The data reaches their router, which creates a wired or wireless local area network o deliver the movie to their laptop, mobile phone or smart TV. You connect your devices to the router by Wi-Fi or by plugging in an Ethernet cable.

Exchange backhaul plays a critical role in this process. By providing high capacity transport between the **backbone network (2)** and the customer’s local **access network (4)**, backhaul ensures their content is transmitted efficiently, ensuring a smooth streaming experience.
# Types of backhaul
Backhaul solutions can be divided into two broad categories: wired or wireless.
### Wired (fixed-line) backhaul
Wired or fixed-line backhaul uses cables to transmit data, which can provide higher bandwidth and lower latency than wireless backhaul.

Wired backhaul can use fibre optic, copper, Ethernet or coaxial cabling. Today, wired backhaul tends to use fibre as it offers very low latency and the highest capacity to satisfy the growing demand for data.
### Wireless backhaul
Wireless backhaul is used where wired backhaul is either impossible or not cost-effective.

Wireless backhaul typically uses microwave signals, which can make point-to-point and point-to-multipoint connections over medium to long distances. For remote areas or areas without wired infrastructure, satellites can be used to transmit data over long distances, while Wi-Fi can extend networks locally.