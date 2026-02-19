---
categories:
  - "[[Security]]"
topic@security:
  - "[[Palo Alto Networks]]"
tags:
  - palo_alto/ngfw
  - tobecompleted
created: 2026-02-06T12:24:24+01:00
modified: 2026-02-19T16:34:16+01:00
---
![[Phishing Protection.png]]
1) Attacker sends phishing email that contains a link to the compromised web server.
2) Bob clicks the link and enter his corporate credentials.
3) The firewall notices <mark style="background: #FFB8EBA6;">credential information in the web traffic</mark> and uses <mark style="background: #FF5582A6;">User-ID to detect whether they are valid corporate credentials</mark>. You can configure User-ID to use one of three different methods to detect corporate credentials in web traffic.
4) If User-ID detects valid corporate credentials, then the <mark style="background: #FFB86CA6;">firewall consults its URL filtering configuration</mark> <mark style="background: #FFF3A3A6;">to determine the URL categories for which users should be prevented from entering their corporate credentials</mark>.
5) In this case, Bob is attempting to enter his corporate credentials to a blocked website and the firewall blocks his credentials from being submitted.
Block is not the only action that you can configure. You also can configure the firewall to allow credential submission or <mark style="background: #BBFABBA6;">to present a response page that warns users against submitting credentials to websites</mark>. You can customize your response page to educate users against re-using corporate credentials, even on legitimate, non-phishing sites.
# Phishing Protection #configuration 
1) Configuration of User-ID to detect user credential submission to websites.
2) Configuration of a URL Filtering Profile to block access to known phishing sites by blocking access to the phishing URL category. This configuration prevents your users from even having the opportunity to submit their credentials to a phishing website.
3) Configure a URL Filtering Profile to control user credential submission to allowed websites.
4) Add the URL Filtering Profiles to Security policy rules, where they can enforce anti-phishing and user credential submission protections.
## User-ID
### LDAP Server Profile and Group Mapping
User-ID relies on user group membership information that resides in an LDAP directory service. 

Before User-ID can access this information, you must configure the firewall with an LDAP Server Profile.

[[User-ID™#Configure Group Mapping configuration|LDAP Server Profile and Group Mapping Configuration Link]]


