---
categories:
  - "[[Security]]"
topic@security:
tags:
created: 2026-02-26T15:04:22+01:00
modified: 2026-02-27T12:21:31+01:00
---
It is recommended that when you generate a trust certificate, it should be a <strong>Subordinate certificate authority</strong> (CA) of your PKI. 

This way, when you load it onto your firewall, it will already be trusted by your PKI, providing a smooth experience when you roll it out. 

All of your devices and browsers should have your Root CA trusted.

To make certificate management easier, we recommend using one Subordinate CA per firewall proxy. 

This way, if a certificate needs to be revoked, you will only have to revoke a single certificate across all your firewalls. This is more efficient than having to revoke a single certificate across 20-100 firewalls.![[Certificates - Palo Alto.png]]
<mark style="background: #FFB8EBA6;">When integrating with existing PKIs</mark>, it is best to use a forward trust certificate as the Subordinate CA to the Root CA. 

This allows clients to implicitly trust the Root CA, providing a better user experience. 

This is because most endpoints will already have the Root CA certificate imported into their store, so there is no extra step required to push it out. 

However, this may not be applicable if you are creating self-signed certificates.

**Note:** It is also recommended to use one Subordinate CA per gateway for easier management of certificates. Additionally, self-signed certificates should be installed in the operating system's certificate store for all browsers on Windows. This includes Chrome, Opera, Safari, and Explorer. For Firefox, the certificate store is built into the browser, with the option to default to the system's store if needed.

# Forward Proxy

To obtain a subordinate CA from your Root CA for the firewall to sign certificates for sites that require decryption, follow the best practice of generating a certificate signing request via the certificate page and using it to generate a subordinate CA from the enterprise root. This ensures that the private key remains secure on the firewall.