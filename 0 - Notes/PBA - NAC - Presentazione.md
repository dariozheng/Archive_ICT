---
categories:
  - "[[Networking]]"
topic@networking:
  - "[[Cisco ISE]]"
tags:
  - category/networking/cisco_ise
icon: FasNetworkWired
iconColor: "#003791"
last_update: 2026-10-08
status: draft
---
# Presentazione
Salve, oggi siamo riuniti per la kickoff del progetto ISE NAC e SDN, in questa meet farò un riassunto su cosa è il NAC, un breve presentazione del flusso di accesso dell'utente, l'architettura e su quali servizi e server verranno fatte le configurazioni, ed infine i vari tipi di onboarding per tipo di utente.

Il NAC ISE (Network Access Control) è un sistema che centralizza la gestione ed il monitoraggio degli accessi alla rete aziendale, riducendo il rischio di connessioni non autorizzate e mantenendo una visibilità degli utenti che hanno fatto accesso.

La gestione degli accessi si basa su diversi attributi, tra cui **identità dell'utente, tipologia di dispositivo, posizione e contesto della connessione**. In base alle informazioni raccolte e alle regole configurate, Cisco ISE determina il livello di accesso da concedere alla rete aziendale. Le informazioni relative alle autenticazioni e alle autorizzazioni vengono registrate per scopo di monitoraggio, troubleshooting e sicurezza nel log interno di Cisco ISE. La durata della conservazione dipende dalla configurazione e dalle risorse disponibili; per estendere la retention oltre quella consentita localmente, è possibile inoltrare i log a un server esterno.


![[nac-01-panoramica.png]]

Con la corretta implementazione del NAC gli utenti normali di Publiacqua non noteranno quasi nessuna differenza quando accederanno alla rete cablata, mentre i dispositivi non riconosciuti o non correttamente registrati e autorizzati si ritroveranno nella rete Guest, senza accesso a internet se non hanno l'autorizzazione da un utente di Publiacqua.

Tutte le policy sono gestite in una piattaforma centralizzata dove verrà impostata quali profili di autorizzazione ogni utente riceverà.

I profili di autorizzazione possono essere semplicemente fornire l'accesso alla VLAN di ADMIN, CLIENT, GUEST o impostare anche Access List per limitare a quali indirizzi IP l'utente può raggiungere.

Questi profili di autorizzazione e le policy che permettono questi profili possono essere personalizzati a seconda di esigenze in ogni momento.

# Architettura

L'implementazione del NAC coinvolge il Domain Controller, la Certificate Authority (CA) on-premises, il server Cisco ISE, gli switch di rete e i dispositivi che richiedono l'accesso alla rete aziendale.

![[nac-02-architettura.png]]

Il Domain Controller gestisce l'identità aziendali e consente di verificare l'appartenenza degli utenti, e dei computer di dominio. Inoltre a seconda dei gruppo AD di appartenenza dell'utente è possibile creare delle policy apposta, come l'Admin Access.

Il Domain Controller ha poi il ruolo di gestire l'installazione degli certificati sugli dispositivi degli utenti e configurare questi dispositivi a utilizzare i certificati per fare l'autenticazione tramite le Group Policy che vengono applicate a seconda dell'utenza.

Le Certificate Authority, nel nostro questo caso la SubordinateCA01 e SubordinateCA02 gestiscono i certificati, in questi server vengono creati o revocati i certificati. I certificati vengono creati da template fatte apposta per varie esigenze, ad esempio certificato utente e certificato computer. Abbiamo suddiviso i certificati utenti sulla SubordinateCA01 e certificate computer sulla SubordinateCA02.

Quando il Domain Controller fa l'onboarding del dispositivo con le GPO, usa i template presenti sulle SubCA per installare i certificate sul PC dell'utente e registra questo certificato sulle SubCA per avere un registro di certificati in validità, se sul SubCA viene revocato un certificate dal registro, il certificato presente sul pc utente non autenticherà più l'utente. Questo registro di certificati viene tenuto in synch con il server ISE.

![[nac-05-ciclo-certificati.png]]

Il server ISE ripetendo quanto detto prima si occupa delle policy di autenticazione, autorizzazione, profilo di accesso e monitoraggio.

Nelle policy di autenticazione viene definito le regole per considerare l'autenticazione dell'utente un successo o meno. Questo dipende se ISE riesce a trovare l'utente tra le sue liste di MAC address o con un confronto con il Domain Controller per gli utenti AD.

Le policy di autorizzazioni decidono quali livelli di permessi un utente può avere a seconda di vari attributi. I livelli di permessi sono definiti in profili di autorizzazioni.

Per l'utente base di Publiacqua verrà utilizzato una policy che controlla sia i certificati utente che computer per avere accesso completo. Mentre per admin basta solo il certificato utente, che sarà comunque legato al PC, installato sul dispositivo iniziale con la chiave privata non esportabile, ed quindi il questo certificato utente non può essere usato altre PC.

Le policy che verrà implementato:

![[Pasted image 20261008231318.png]]

![[nac-03-policy-set.png]]

Un controllo iniziale delle MAC address, se si trova in blacklist, dove verrà bloccato subito. Poi se utente appartiene al gruppo infrastructure admin, per un profilo sulla VLAN di ADMIN.

Un utente normale di Publiacqua utilizzerà la Client Access che è certificato utente e certificato computer, il certificato utente può essere inviato solo dopo che l'utente ha fatto il login, quindi quando l'utente non ha fatto l'accesso il PC verrà inserito su una profilo di pre-autenticazione con permessi limitati.

![[nac-04-flusso-autenticazione.png]]

MAB Access per i rari casi in cui gli utenti devono accedere con il MAC address, che può succedere in caso ci sia un consulente esterno senza utenza in dominio per fare esempio di un caso e infine il Guest Access per tutti gli utenti che hanno fallito l'accesso o veri guest.

Tutte queste policy sono molto personalizzabili e gestire la maggior parte delle situazioni.

Mentre il server ISE dichiara le policy e decide se un dispositivo ha l'accesso o meno, gli switch a implementano le decisioni di ISE.

Gli switch fanno le richieste di certificato all'utente, inviano i certificati, MAC address o credenziali a ISE, ed aspetta la risposta del server per applicare con il profilo di accesso che può bloccare, permettere o inserire tra i vari VLAN l'utente. Nella configurazione locale dello switch viene definito anche come comportarsi in casi in cui il server ISE vada down: Se l'utente aveva già fatto accesso con ISE, non nota nulla e continua ad avere gli stessi permessi mentre utenti nuovi vengono messi sulla VLAN Client con limitazioni verso indirizzi privati e può accedere solo a internet.

![[nac-06-ise-non-raggiungibile.png]]

Le configurazioni degli switch non sono fatte a mano ma tramite DNA, dove c'è un template che viene inviato allo switch che si vuole configurare, su DNA viene segnato anche la configurazione drift, per segnalare se la configurazione è stato modificata o è diversa dal template usato o dalla startup config. In questo modo abbiamo visibilità se qualcuno modifica le configurazioni e non lo documenta su DNA.

Alla fine ci sono i dispostivi degli utenti che devono fare l'onboarding, per gli utenti di Publiacqua che sono in dominio ADMIN o NON, non devono fare nulla in quanto viene gestito tutta dal Domain Controller, ma per i consulenti esterni dipende: se sono consulenti esterni con permessi ADMIN come i consulenti di TAI abbiamo una policy apposta per gli ADMIN, per i consulenti esterni normali invece ci saranno delle guide a secondo di livello di accesso che devono avere, e anche qua c'è una differenza tra consulenti con un account in AD o senza account, per consulenti senza account useranno il MAC address con profili di autenticazione specializzato.

![[nac-07-onboarding.png]]