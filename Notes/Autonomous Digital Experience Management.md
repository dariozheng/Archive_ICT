---
categories:
  - "[[Security]]"
topic@security:
  - "[[Palo Alto Networks]]"
tags:
  - palo_alto/sase
aliases:
  - ADEM
---
<strong>Autonomous Digital Experience Management (ADEM)</strong> is a <strong>service</strong> that provides <strong>native end-to-end visibility</strong> and <strong>performance metrics</strong> for real application traffic in your <strong>secure access service edge (SASE) environment</strong>. 

<mark style="background: #FFB8EBA6;"><strong>SASE</strong> is a cloud-delivered service that combines all of the networking and security capabilities an organization needs for their mobile users and remote sites</mark>. <mark style="background: #FF5582A6;">SASE-native ADEM provides <strong>visibility</strong> to improve <strong>operational efficiency</strong></mark> and deliver optimal user experiences and application performance. <strong>ADEM</strong> provides: 

- <mark style="background: #ADCCFFA6;"><strong>ADEM Observability</strong></mark>
<mark style="background: #FFB86CA6;">A unified dashboard</mark> <mark style="background: #FFF3A3A6;">provides</mark> every line of business across IT with<mark style="background: #FFF3A3A6;"> a single view of the IT environment</mark>. <mark style="background: #BBFABBA6;">Know the health and performance of mobile and branch users, networks, applications, and underlying IT infrastructure</mark>, <mark style="background: #ABF7F7A6;">with easy drill-down capability for further investigation</mark>.
With the <strong>ADEM Observability license</strong>, you can gain <mark style="background: #ADCCFFA6;">end-user monitoring</mark> of <mark style="background: #D2B3FFA6;">user-to-application health and performance</mark> <mark style="background: #CACFD9A6;">with synthetic tests</mark>.

- <mark style="background: #ADCCFFA6;"><strong>AIOps</strong></mark>
The platform’s <mark style="background: #FFB8EBA6;">built-in artificial intelligence (AI)-based</mark> <mark style="background: #FFB86CA6;"><strong>incident detection</strong>, <strong>diagnostics</strong>, <strong>predictive analytics</strong>, and <strong>automated workflows</strong></mark> empower IT teams to detect and resolve complex problems before they have a widespread impact. 
With the <strong>AI-Powered ADEM license</strong>, you can access comprehensive capabilities, including <strong>ADEM Observability</strong> and <strong>AIOps</strong>.

<mark style="background: #FFF3A3A6;"><strong>ADEM</strong> functionality is natively integrated into</mark> the <mark style="background: #BBFABBA6;">GlobalProtect app</mark>, <mark style="background: #ABF7F7A6;">Prisma SD-WAN device</mark>, and <mark style="background: #ADCCFFA6;">Prisma Access</mark> and <mark style="background: #FFF3A3A6;">therefore does not require you to deploy any additional appliances or agents</mark>. 

<mark style="background: #D2B3FFA6;">Because of this native integration, the ADEM service enables <strong>synthetic tests</strong> for applications you specify</mark>, <mark style="background: #CACFD9A6;">from the endpoint, from the Prisma SD-WAN device, and from deployed Prisma Access locations in your environment</mark>. 

<mark style="background: #FFB8EBA6;">ADEM continuously monitors all the segments from the endpoint to the application</mark> for <mark style="background: #FFB8EBA6;">GlobalProtect mobile users</mark> and <mark style="background: #FF5582A6;">monitors all segments on all WAN paths</mark> (active and backup) <mark style="background: #FF5582A6;">for Prisma SD-WAN remote sites</mark> <mark style="background: #CACFD9A6;">and identifies baseline metrics for each monitored application</mark>.

<mark style="background: #FFB86CA6;">ADEM provides <strong>visibility</strong> into any <strong>deviations</strong> or <strong>events</strong></mark> <mark style="background: #FFF3A3A6;">that degrade the user experience across each segment between the end user and the application</mark>, whether it’s the endpoint, Wi-Fi, local area network (LAN), internet service provider (ISP), Prisma Access, or the application. 
<mark style="background: #BBFABBA6;">ADEM continuously monitors every segment in the service delivery path</mark> and <mark style="background: #ABF7F7A6;">provides insights that help you quickly isolate the segment, which is causing digital experience problems, and simplify remediation</mark>.

With <strong>ADEM</strong>, IT teams have <mark style="background: #ADCCFFA6;">end-to-end observability insights all in one place</mark>. 

<mark style="background: #FF5582A6;">ADEM data is available in the <strong>Strata Cloud Manager</strong></mark>. 

<mark style="background: #FFB86CA6;">To access the ADEM widgets</mark>, <mark style="background: #FFB8EBA6;">log into Strata Cloud Manager from the Hub</mark> with your credentials and <mark style="background: #FFF3A3A6;">view the unified visibility data</mark> <mark style="background: #BBFABBA6;">which includes ADEM widgets in the various dashboards</mark>.
# ADEM Observability Features
### Application Experience Dashboard
<mark style="background: #BBFABBA6;">The ADEM Observability license unlocks</mark> the <mark style="background: #ABF7F7A6;"><strong>Application Experience</strong> dashboard</mark>, which <mark style="background: #ADCCFFA6;">displays the <strong>Mobile User Experience</strong> card</mark> and <mark style="background: #D2B3FFA6;">the <strong>Remote Site Experience card</strong></mark> <mark style="background: #BBFABBA6;">based on the license(s) you have purchased</mark>. 
<mark style="background: #FFF3A3A6;">The Application Experience dashboard gives an overall view of the experience across all users, remote sites, and applications; it is an aggregate of data across the entire organization</mark>.
![[Application Experience Dashborad.png]]

### ADEM Zoom Integration
Video call traffic is very sensitive to network conditions. Performance issues that might not impact web browsing can be felt by users on video calls. 

In order to help administrators debug, monitor, and proactively identify <mark style="background: #BBFABBA6;">the performance issues impacting Zoom users in their organization</mark>, <mark style="background: #ABF7F7A6;">ADEM has partnered with Zoom to provide the first per-minute root-cause analysis on the market</mark>.

<mark style="background: #ADCCFFA6;">This integration provides minute-by-minute analysis of all of the Zoom calls in your network</mark>. ADEM also rolls these insights up at the organization level so that customers can find the service delivery segment most impacting users. <mark style="background: #D2B3FFA6;">The Zoom performance monitoring is restricted to the participants within the organization only</mark>. <mark style="background: #CACFD9A6;">If a Zoom call has participants attending from outside your organization</mark> (who do not belong to the tenant being monitored), <mark style="background: #CACFD9A6;">their data will not be analyzed or stored by ADEM</mark>.
![[ADEM Zoom Integration.png]]
### ADEM Self-Serve
<strong>ADEM Self-Serve</strong> empowers end users <mark style="background: #FFB8EBA6;">to resolve the application experience issues that fall into their purview</mark> <mark style="background: #FF5582A6;"><u>by displaying notifications on their endpoints with suggested remediations</u></mark>. It sends notifications to users’ devices for the following events:
- <mark style="background: #FFB86CA6;">Poor Wi-Fi quality and disconnected Wi-Fi</mark>
- <mark style="background: #FFF3A3A6;">High central processing unit (CPU) or memory consumption</mark>
- <mark style="background: #BBFABBA6;">Internet outages</mark>
![[ADEM Self-Serve.png]]
# Experience Score
<mark style="background: #ADCCFFA6;">The experience score is the average of end-to-end application performance metrics for all monitored applications across all users or remote sites</mark>. 

<mark style="background: #D2B3FFA6;">For each application that is monitored per mobile user</mark>, <mark style="background: #CACFD9A6;">ADEM calculates a score based on the five critical metrics</mark> - <strong><mark style="background: #FFB8EBA6;">application availability</mark>, <mark style="background: #FF5582A6;">DNS resolution time</mark>, <mark style="background: #FFB86CA6;">TCP connect time</mark>, <mark style="background: #FFF3A3A6;">SSL connect time</mark>, and the <mark style="background: #BBFABBA6;">HTTP latency</mark></strong>. 

<mark style="background: #ABF7F7A6;">If the application fails the availability test (application is unavailable), then the experience score is 0</mark>. 

<mark style="background: #ADCCFFA6;">If the application is reachable, only then the remaining four metrics will be calculated</mark>. Each of the metrics (other than application reachability) <mark style="background: #D2B3FFA6;">have a different weightage and baselined lower and upper thresholds, and their combined weightage equals 100</mark>. 
The sum of these individual metric scores determines the application experience score for a user. 
An average of all the test sample results for each application determines the experience score of a user.![[Experience Score.png]]

# ADEM Monitoring
<strong>Endpoint telemetry</strong> and <strong>synthetic monitoring</strong> within ADEM enable you to identify and resolve your users’ digital experience issues.

The <strong>ADEM agent</strong>, <mark style="background: #FFB86CA6;">natively integrated with the GlobalProtect agent, can collect device and Wi-Fi telemetry of the client</mark>. <mark style="background: #ABF7F7A6;">ADEM also performs cURL and ping tests to determine network and application health</mark>.

<strong>Endpoint Telemetry</strong>
Gathering information about the endpoint device (i.e. Mac or Windows device) and Wi-Fi performance
- You need to know if it's CPU, memory, etc.
- Many things go wrong with Wi-Fi

<strong>Synthetic Monitoring</strong>
Running <mark style="background: #ADCCFFA6;">tests of network connectivity</mark> and <mark style="background: #D2B3FFA6;">application sessions</mark> regularly and timing the results. You can get the <mark style="background: #BBFABBA6;">user's information about LAN, ISP, Prisma Access, and app performance</mark>.
## Monitor Dashboard: Users and Branch Sites
The Monitor dashboard lets you monitor the digital experience for your SASE <mark style="background: #ABF7F7A6;">users</mark> and <mark style="background: #ADCCFFA6;">remote sites</mark>, as well as troubleshoot performance issues. From here, you get an <mark style="background: #D2B3FFA6;">overall view of the experiences and the experience trend for all your ADEM users</mark>, as <mark style="background: #CACFD9A6;">well a per-user view of the digital experience across your SASE environment</mark>.
### Users
Select <strong>Monitor > Users</strong> for an overall view of the experiences and the experience trend for all your ADEM users, as well a per-user view of the digital experience across your SASE environment. 

You can drill down into details for the specific user by clicking on the User Name to view app performance data (<strong>Monitor > Users > <u>User Name</u> > Experience tab</strong>). Immediately when you drill down, alerts at the top of the page highlight any experience issues the specific user is having, such as low device memory or high CPU usage.
### Branch Sites
Select <strong>Monitor > Branch Sites > Prisma SD-WAN > List > <u>Branch Site Name</u></strong> to view the <mark style="background: #FFB8EBA6;">overall experience score for all the remote sites</mark>, <mark style="background: #FF5582A6;">the experience score for each site</mark>, <mark style="background: #FFB86CA6;">the connected Prisma Access location sites</mark>, and <mark style="background: #FFF3A3A6;">information on the internet and private wide area network (WAN) <strong>circuits</strong></mark> that the remote site is connected to.
## Monitor Dashboard: Applications 
Select <strong>Monitor > Applications</strong> to see the applications in your organization that are monitored (have tests configured on them). <mark style="background: #BBFABBA6;">You can see their risk scores</mark> and the <mark style="background: #ABF7F7A6;">user experience</mark> <mark style="background: #ADCCFFA6;">for each application in Prisma Access Applications widget</mark>.

The Applications dashboard gives you visibility into all of the applications that are running across your organization as observed in real-user traffic going through Prisma Access. 

For each application, you can see the total traffic usage during the selected time range.![[Monitor Dashboard Applications.png]]

