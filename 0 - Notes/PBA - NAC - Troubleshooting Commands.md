---
categories:
  - "[[Networking]]"
  - "[[Security]]"
topic@networking:
  - "[[Cisco ISE]]"
topic@security:
  - "[[NAC]]"
tags:
  - category/networking/cisco_ise
  - category/security/nac
icon: LiLock
iconColor:
last_update: 2026-11-17
status: draft
---
# Powershell

####  Get-Service -ComputerName '25L1NB001' -Name dot3svc | Restart-Service -Force
#### Invoke-GPUpdate -Computer "25L1NB001"  -Force

#### query user /server:25L1NB001

#### Get-CimInstance -ClassName Win32_ComputerSystem -ComputerName 25L1NB001 | Select-Object UserName

#### Get-ADComputer -Identity "25L1NB001" -Properties OperatingSystem | Select-Object Name, OperatingSystem 25L1NB001

# Access Switch

#### show access-session brief

#### show access-session int Gi1/0/1 details

#### 