---
categories:
  - "[[Networking]]"
topic@networking:
  - "[[Networking General]]"
created: 2026-01-01T23:08:38+01:00
modified: 2026-01-02T08:06:59+01:00
---
Segmenting an enterprise network is an important strategy to enhance network security, efficiency, and ease of management. 

While every network is unique, enterprise networks share a common structure and segmented elements. 

The diagram shows tht <mark style="background: #FFB8EBA6;">the basic top-level structure consists of two segments</mark>: <mark style="background: #FF5582A6;">a demilitarized zone (DMZ)</mark> and <mark style="background: #FFB86CA6;">an internal network</mark> or <mark style="background: #FFB86CA6;">enterprise segment</mark>. Within the enterprise segment, there are common segments including server, database, security, and users.
![[Segment Structure.png]]

# Segmented Elements

## Enterprise Network Firewalls

Commonly, enterprise networks have at least two firewalls:

- <strong>Firewall Protecting the Demilitarized Zone</strong>: <mark style="background: #FFB8EBA6;">The DMZ firewall usually faces an organization's perimeter</mark> and <mark style="background: #FF5582A6;">isolates a segment that will be exposed to Internet requests</mark>.

- <strong>Firewall Protecting the Enterprise Segment</strong>: <mark style="background: #FFF3A3A6;">The enterprise firewall is likely to have far more stringent permissions and allow far less traffic through</mark>.

## DMZ

The DMZ serves an important role in any network with internet-facing services. 

Most internet-facing services are protected by a DMZ firewall, including web servers, WordPress servers, Internet Information Servers (IIS), Domain Name Servers (DNS), and email relay servers.

<mark style="background: #ADCCFFA6;">The DMZ firewall allows requests to reach devices within the DMZ, even though firewalls typically block incoming traffic</mark>. 
When a web server is hosted behind a DMZ firewall, it receives all requests and forwards them to the servers.

## Servers

Services in the server segment are available to internal users and other hosts within the enterprise network, similar to how servers in a DMZ are accessible to external users. 

For instance, within the server segment, companies often house: 

- Active Directory (AD)
- E-Policy Orchestrator (ePO)
- Dynamic Host Configuration Protocol Server (DHCP)
- E-Mail servers, Domain Controllers (DC)
- Structured Query Language server (SQL)
- File server

## Users Segment

The users segment typically includes business functions like sales, marketing, finance, and IT.

Some networks have a "flat" users segment where all users are in the same network, but this increases the risk of malware spreading rapidly and compromising the entire user base.

Some users pose a higher risk by taking their devices on and off the network, for example, salespeople who are often on the road and executives who travel frequently. 
The most commonly found devices within user segments are desktop and laptop computers with Windows, Mac, and Linux systems.

## Database

The database segment contains databases and database servers. Prime examples of this are MySQL and MSSQL servers.
