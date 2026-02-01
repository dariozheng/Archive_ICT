---
categories:
  - "[[Networking]]"
topic@networking:
  - "[[Networking General]]"
tags:
  - complete
created: 2026-01-27T16:24:43+01:00
modified: 2026-02-01T23:01:14+01:00
aliases:
  - backhauling
  - network backhauling
  - network backhaul
---
> [!info] Network Backhaul (The infrastructure)
><strong>Backhaul</strong> in networking refers to the <strong>infrastructure</strong> that connects a <strong>local network</strong>, or <strong>subnetwork</strong>, to a <strong>backbone</strong> or <strong>core network</strong>. 

> [!info] Backhauling (The action)
><strong>Backhauling</strong> is routing all data from each location back to a <strong>central location</strong>, even if the ultimate destination for some traffic is another office or the internet. 
>This allows security policy to be enforced and traffic inspected consistently from central hubs. 

The network backhaul It’s typically a high capacity, low latency link designed to transmit data efficiently and fast.

<strong>Internet service providers</strong> (<strong>ISPs</strong>) use <strong>backhaul</strong> to deliver internet access. 

ISPs connect you to the internet through a backbone network connecting data centers linked to an internet gateway.

<strong>Backhaul</strong>, or exchange backhaul, <mark style="background: #FFB8EBA6;">is the <strong>subnetwork</strong> that connects</mark> these <mark style="background: #BBFABBA6;">data centers</mark> to <mark style="background: #ABF7F7A6;">local exchanges</mark>. <mark style="background: #FFF3A3A6;">These exchanges typically link to street cabinets, which link to your router by copper or fibre optic cable, delivering internet to your office or home.</mark>

<mark style="background: #FFF3A3A6;">Backhaul is also used for mobile data access. When you browse the internet on your mobile phone, your device connects to cell towers in a local <strong>Radio Access Network (RAN)</strong></mark>.
<mark style="background: #D2B3FFA6;"><strong>Backhaul is</strong> this local <strong>RAN</strong> and its <strong>related infrastructure</strong></mark>, <mark style="background: #CACFD9A6;">which connects your mobile device to a wired backbone network and the internet</mark>.

# How does backhaul work?
![[Backhaul.png]]
1. **Data Centre**: When a customer requests a movie, the content is retrieved from Netflix’s servers in a data centre.
2. **Backbone network**: The data travels through the backbone network, a high capacity network that connects regions, ISPs and data centers to the internet and cloud services.
3. <strong>Exchange backhaul</strong>: <mark style="background: #FFB86CA6;">Backhaul connects the backbone network to your local exchange</mark>, <mark style="background: #ABF7F7A6;">ensuring the data is transported efficiently <strong>to</strong> and <strong>from</strong> the internet</mark>.
4. **Access network**: If the customer uses a fixed-line connection like DSL or fibre, the data may pass through a street cabinet connecting to their home or business.
5. **Router**: The data reaches their router, which creates a wired or wireless local area network o deliver the movie to their laptop, mobile phone or smart TV. You connect your devices to the router by Wi-Fi or by plugging in an Ethernet cable.

Exchange backhaul plays a critical role in this process. By providing high capacity transport between the **backbone network (2)** and the customer’s local **access network (4)**, backhaul ensures their content is transmitted efficiently, ensuring a smooth streaming experience.
# Types of backhaul
Backhaul solutions can be divided into two broad categories: wired or wireless.
### Wired (fixed-line) backhaul
<mark style="background: #FFB86CA6;">Wired or fixed-line backhaul uses cables to transmit data</mark>, which can provide higher bandwidth and lower latency than wireless backhaul.

<mark style="background: #BBFABBA6;">Wired backhaul can use fibre optic, copper, Ethernet or coaxial cabling</mark>. Today, wired backhaul tends to use fibre as it offers very low latency and the highest capacity to satisfy the growing demand for data.
### Wireless backhaul
<mark style="background: #D2B3FFA6;">Wireless backhaul typically uses microwave signals</mark>, <mark style="background: #FFF3A3A6;">which can make point-to-point and point-to-multipoint connections over medium to long distances</mark>. For remote areas or areas without wired infrastructure, <mark style="background: #CACFD9A6;">satellites can be used to transmit data over long distances</mark>, while Wi-Fi can extend networks locally.