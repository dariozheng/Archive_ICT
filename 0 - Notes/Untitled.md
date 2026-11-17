##### radius-server attribute 6 on-for-login-auth

Includes [[PBA - NAC - ISE Server#Service-Type|Service-Type]] in Access-Requests for <strong>login authentication</strong>: someone logging into the switch itself (SSH, console, HTTPS through `aaa authentication login`), or a user signing in on the switch's own Local WebAuth portal.

Without it, the switch removes the attribute from those requests. `debug radius` shows:
`dropping service type, "radius-server attribute 6 on-for-login-auth" is off`

With it, login requests carry:

```
Service-Type = Login (1)
```

Scope:
- <strong>Device administration (RADSERV):</strong> PBA-RADIUS can tell an admin login apart from other requests and match its policy on `Service-Type = Login`.
- <strong>Local WebAuth:</strong> the Access-Request built from the portal credentials also includes Service-Type.
- <strong>802.1X / MAB: no effect.</strong> These requests always carry Service-Type, with or without this command: `Framed (2)` for 802.1X, `Call-Check (10)` for MAB.

##### radius-server attribute 6 support-multiple

Allows the switch to <strong>accept more than one Service-Type attribute in an Access-Accept</strong>, i.e. multiple Service-Type values for each RADIUS profile. By default, the switch expects at most one.

Each request carries exactly one Service-Type (RFC 2865), and 802.1X and MAB never share a packet. They are separate requests:

```
802.1X Access-Request:  Service-Type = Framed (2)
MAB Access-Request:     Service-Type = Call-Check (10)
```

In practice, this only matters if an ISE authorization profile returns more than one Service-Type. It is kept in the template because it's part of Cisco's baseline switch configuration for ISE, and it does no harm when unused.