---
categories:
  - "[[Networking]]"
topic@networking:
  - "[[Networking General]]"
tags:
  - cisco
  - PBA
icon: SiCisco
iconColor: "#1BA0D7"
last_update: 2026-07-09
---
Cisco DNA Center è un controller di rete intent-based e una piattaforma di gestione centrale per reti Cisco enterprise di campus, filiale e WAN. 

Sostituisce la gestione CLI per singolo dispositivo con un unico punto di amministrazione che automatizza l'intero ciclo di vita di switch Catalyst, router e wireless: onboarding, configurazione, controllo delle immagini software, applicazione delle policy e monitoraggio dello stato di salute. 

L'amministratore esprime l'intento nella GUI o tramite l'API northbound, e il controller traduce tale intento in configurazione dei dispositivi e lo distribuisce in modo coerente su tutta la rete.

La piattaforma è organizzata intorno a quattro domini di configurazione: [[#Design|Design]], [[#Policy|Policy]], [[#Provisioning|Provisioning]] e [[#Assurance|Assurance]], appoggiati su un livello di [[#Piattaforma e API|piattaforma]] programmabile. 

## Accesso

L'accesso per il portale GUI di DNA è https://pba-dna.publiacqua.it/ con le credenziali RADIUS.

## Flusso di configurazione

_L'ordine in cui gli elementi devono essere costruiti, perché i domini successivi consumano ciò che quelli precedenti producono._

La configurazione di DNA è sequenziale. Non puoi realmente [[#Provisioning|provisionare]] un dispositivo prima che sia nell'[[#Inventory|inventory]], e il provisioning produce qualcosa di utile solo se la gerarchia e le impostazioni di [[#Design|Design]] esistono già per il sito a cui il dispositivo appartiene. L'ordine consigliato è il seguente.

```text
                 ┌──────────────────────────────────────────────┐
                 │                    DESIGN                    │
                 │ gerarchia · impostazioni · credenziali       │
                 │ pool IP · wireless · immagini · profili      │
                 └───────────────────────┬──────────────────────┘
                                         │ impostazioni ereditate da ogni sito
                                         ▼
   ┌────────────────┐        ┌───────────────────────────┐
   │   DISCOVERY    │ ─────▶ │          INVENTORY         │
   │ CDP / LLDP /   │        │ dispositivi gestiti · ruoli│
   │ range IP / CIDR│        │ compliance · config drift  │
   └────────────────┘        └─────────────┬──────────────┘
                                           │ assegnazione dispositivo a sito
                                           ▼
                             ┌───────────────────────────┐
                             │        PROVISIONING        │
                             │ push impostazioni sito +   │
                             │ template Day-N + immagine  │
                             └─────────────┬──────────────┘
                               ┌───────────┴────────────┐
                               ▼                        ▼
                     ┌───────────────────┐    ┌────────────────────┐
                     │       POLICY      │    │      ASSURANCE      │
                     │  SGT / GBAC · QoS │    │ basata su telemetria│
                     └───────────────────┘    └────────────────────┘
```

[[#Plug and Play|Plug and Play]] è un punto di ingresso alternativo in questo flusso: invece di scoprire un dispositivo già configurato, un dispositivo factory-fresh contatta il controller e viene onboardato senza intervento, dopodiché finisce nell'inventory come qualsiasi altro dispositivo.

## Design

Il dominio Design (`Design` nella GUI) è dove l'intento globale e per-sito viene dichiarato una volta e poi riutilizzato. Nulla qui tocca direttamente un dispositivo; costruisce il modello che il [[#Provisioning|provisioning]] renderizzerà in seguito sull'hardware.

### Network Hierarchy

La gerarchia è `Global > Area > Building > Floor`. 

![[Pasted image 20260707150758.png]]

![[Pasted image 20260707150853.png]]

Le aree sono contenitori organizzativi; gli edifici hanno un indirizzo civico e coordinate geografiche; i piani hanno un'immagine della planimetria usata per le heatmap wireless e il posizionamento degli AP. 
Le impostazioni definite a un livello padre vengono ereditate dai figli, e un figlio può sovrascrivere un valore ereditato. Progettare prima la gerarchia è importante perché credenziali, server, pool IP e profili sono tutti assegnati rispetto ai nodi di questo albero.

### Network settings

_I valori infrastrutturali condivisi che vengono inviati ai dispositivi durante il provisioning._

In `Design > Network Settings`, i seguenti elementi sono definiti per sito (o globalmente ed ereditati):

- [[#Credenziali dei dispositivi|Credenziali dei dispositivi]] per l'accesso di management.
- Impostazioni di server e protocolli: AAA, DHCP, DNS, NTP, fuso orario, banner, syslog, trap SNMP e collector NetFlow.
- [[#Pool di indirizzi IP|Pool di indirizzi IP]] per automazione e SD-Access.
- Profili service provider per QoS WAN.
- Impostazioni wireless per SSID e comportamento RF.

#### Credenziali dei dispositivi

_Come il controller si autentica su un dispositivo per gestirlo._

![[Pasted image 20260707151254.png]]

Vengono memorizzati più set di credenziali e uno per ciascun tipo viene marcato come predefinito del sito. I tipi rilevanti sono:

- Credenziali CLI (nome utente, password e password enable) per la gestione della configurazione e l'archivio della running-config.
- Community string SNMP read e SNMP write (SNMPv2c), oppure SNMPv3 con autenticazione e privacy, usate per [[#Discovery|discovery]] e raccolta inventory.
- Credenziali HTTPS read e write per piattaforme che espongono un'interfaccia programmabile.
- NETCONF con una porta scelta (comunemente 830), richiesto per la [[#Attivazione della telemetria|telemetria]] model-driven sulle piattaforme IOS-XE supportate.

> [!important] Le credenziali definite qui devono corrispondere al dispositivo
> [[#Discovery|Discovery]] e provisioning usano entrambe queste credenziali. Se SNMP è errato, il dispositivo viene raccolto solo parzialmente; se CLI o NETCONF sono errati, il dispositivo non può essere gestito completamente. Un dispositivo ha quindi bisogno di una baseline funzionante di SSH, SNMP e, per la telemetria, NETCONF prima che il controller possa gestirlo. Questo è anche ciò che la [[#Device controllability|device controllability]] può stabilire automaticamente.

#### Network and server settings

![[Pasted image 20260707151342.png]]

![[Pasted image 20260707151423.png]]

Questi valori vengono renderizzati nella configurazione dei dispositivi al momento del [[#Provisioning|provisioning]]. AAA è definito in due ruoli da non confondere: server per l'amministrazione dei dispositivi di rete (login al dispositivo, tipicamente TACACS+) e server per l'autenticazione di client ed endpoint (802.1X e MAB, tipicamente RADIUS verso [[#Cisco ISE e pxGrid|Cisco ISE]]). 

#### Pool di indirizzi IP

_Spazio di indirizzamento che il controller può assegnare per automazione e onboarding fabric._

I pool globali sono definiti come blocchi CIDR (facoltativamente sincronizzati da un [[#Gestione degli indirizzi IP|IPAM esterno]]). Dei sottoinsiemi vengono poi riservati per sito. Questi pool riservati alimentano [[#LAN Automation|LAN Automation]] e l'[[#Reti virtuali e onboarding degli host|onboarding degli host SD-Access]], dove un pool viene associato a una rete virtuale e un gateway viene allocato automaticamente.

### Repository immagini

_Dove risiedono le immagini software dei dispositivi e dove viene dichiarata un'immagine golden per ruolo._

![[Pasted image 20260707152920.png]]

Le immagini vengono importate nel repository (`Design > Image Repository`) da un dispositivo gestito, da un URL o da cisco.com; un'immagine viene poi marcata come golden per famiglia di dispositivi, ruolo e sito. Il mark golden è la dichiarazione di stato desiderato che il flusso [[#Software Image Management|SWIM]] applica.

### Network profiles

_Il livello di associazione che collega [[#Template|template]] e impostazioni ai siti._

![[Pasted image 20260707153256.png]]

I profili di rete (`Design > Network Profiles`) esistono in tipi come switching, routing, wireless e assurance. 
Un profilo viene assegnato a uno o più siti, ed è l'oggetto attraverso cui vengono associati i <strong>template di onboarding Day-0</strong> e i <strong>template di configurazione [[#Template Day-0 e Day-N|Day-N]]</strong>. 
Quando un dispositivo in un sito con profilo viene [[#Provisioning|provisionato]], il controller interpreta i template associati e li invia. Questo è il meccanismo che collega il template astratto a un sito concreto.

### Device controllability

_Configurazione che il controller invia autonomamente per rendere un dispositivo gestibile._

![[Pasted image 20260707160820.png]]

 ![[Pasted image 20260707160923.png]]

Device controllability è un'impostazione globale o a livello di sito che consente a Catalyst Center di inviare automaticamente a un dispositivo una baseline di configurazione di management quando viene scoperto o provisionato: per esempio impostazioni SNMP e NETCONF, IP device tracking, il certificato del controller e la configurazione necessaria alla telemetria. 

Elimina la necessità di preconfigurare manualmente ogni dettaglio di management, ma significa anche che il controller aggiunge e modifica configurazione oltre a quanto presente in qualsiasi [[#Template|template]] esplicito.

## Discovery

_Portare sotto gestione dispositivi esistenti e già raggiungibili._

![[Pasted image 20260707161234.png]]

Discovery (`Tools > Discovery`) trova dispositivi nella rete e li inserisce nell'[[#Inventory|inventory]]. È il percorso per dispositivi che hanno già una configurazione di management funzionante, a differenza di [[#Plug and Play|Plug and Play]] per hardware factory-fresh.

### Metodi di discovery

- CDP: si fornisce un dispositivo seed e si lascia che il controller percorra i vicini Cisco Discovery Protocol fino a un numero di hop configurabile.
- LLDP: l'equivalente vendor-neutral per la discovery basata sui vicini.
- <strong>Range di indirizzi IP o CIDR</strong>: scansione di un range o subnet esplicita.

### Credenziali e protocolli di discovery

![[Pasted image 20260707162046.png]]

Discovery usa le [[#Credenziali dei dispositivi|credenziali dei dispositivi]] globali o un set specifico di discovery. SNMP è richiesto per raccogliere dettagli di inventory; CLI è richiesta per gestire la configurazione e archiviare la running config; NETCONF è richiesto dove verrà abilitata la [[#Telemetry activation|telemetria]] model-driven. Un dispositivo scoperto senza SNMP funzionante apparirà con dati incompleti.

### Preferred management address

_Quale indirizzo di interfaccia il controller deve trattare come identità del dispositivo._

![[Pasted image 20260707162104.png]]

Si può indicare a Discovery di preferire una loopback del dispositivo come indirizzo di management invece dell'interfaccia su cui è stato raggiunto inizialmente, mantenendo stabile la gestione se le interfacce fisiche cambiano.

## Inventory

_Il database autorevole dei dispositivi gestiti e del loro stato corrente._

![[Pasted image 20260707162146.png]]

Inventory (`Provision > Inventory`) contiene tutti gli dispositivi dentro DNA. Ogni azione successiva, come [[#Provisioning|provisioning]], [[#Software Image Management|upgrade delle immagini]] e [[#Policy|policy]], opera sui dispositivi registrati qui.

### Device reachability and managed state

_Come il controller traccia se ha realmente il controllo di un dispositivo._

Un dispositivo viene mostrato come managed, unmanaged, unreachable o partially collected. La raggiungibilità viene verificata con <strong>ICMP</strong> e <strong>SNMP</strong>, e il controller risincronizza periodicamente per aggiornare i dati raccolti e ri-archiviare la configurazione.

### Device roles

_L'etichetta topologica e di targeting assegnata a ciascun dispositivo._

A ogni dispositivo viene assegnato un ruolo: access, distribution, core, border router oppure unknown. I ruoli guidano la vista topologica e, cosa importante, delimitano il target dell'[[#Immagini golden|immagine golden]], così che un'immagine per l'access layer non venga applicata a un dispositivo core.

### Configuration drift and compliance

_Rilevare quando un dispositivo non corrisponde più alla configurazione desiderata._

Catalyst Center confronta continuamente ogni dispositivo con lo stato desiderato e segnala violazioni di compliance: drift di configurazione tra stato desiderato e running config, mismatch tra startup e running config, immagine diversa dalla golden image e advisory di sicurezza aperti. La compliance è il punto in cui il controller espone modifiche non gestite, e interagisce direttamente con il modo in cui i [[#Marker di compliance|template dichiarano quali righe ignorare]].

### Device replacement

_Sostituire hardware guasto preservando lo stato desiderato._

![[Pasted image 20260707163657.png]]

Il flusso Return Material Authorization (RMA) consente di sostituire un dispositivo guasto con un'unità equivalente: il ricambio viene onboardato, la configurazione desiderata e l'immagine software del dispositivo guasto vengono applicate, e l'inventory viene aggiornato per puntare al nuovo numero di serie.

## Provisioning

_Renderizzare l'intento di Design su dispositivi reali._

![[Pasted image 20260707163738.png]]

Provisioning (`Provision > Inventory`, poi l'azione di provisioning) è il passaggio che scrive effettivamente la configurazione sull'hardware. Tutto ciò che invia proviene da [[#Design|Design]].

### Assegnazione dei dispositivi ai siti

_Collocare un dispositivo nella gerarchia perché erediti le impostazioni corrette._

![[Pasted image 20260707163826.png]]

Prima del provisioning, un dispositivo viene assegnato a un sito nella [[#Network Hierarchy|gerarchia]]. Questa assegnazione determina quali [[#Network and server settings|impostazioni server]], credenziali e [[#Network profiles|profilo di rete]] (e quindi quali template) si applicano.

### The provisioning workflow

_Cosa invia un'azione di provisioning, e in quale forma._

![[Pasted image 20260707164429.png]]

Il provisioning renderizza le [[#Network settings|impostazioni di rete]] ereditate (AAA, DHCP, DNS, NTP, syslog, SNMP, NetFlow) nella configurazione del dispositivo, applica eventuali [[#Template Day-0 e Day-N|template Day-N]] associati tramite il [[#Network profiles|profilo di rete]] e, per il wireless, applica SSID, profili RF e profili AP al WLC e ai relativi access point. Il controller mostra un'anteprima della configurazione generata prima della distribuzione.

### Telemetry activation

_Attivare il flusso dati da cui dipende il dominio di monitoraggio._

Il provisioning è anche il punto in cui viene abilitata la telemetria (spesso esposta come azione "Update Telemetry Settings" o "Enable Telemetry"). Questo invia le sottoscrizioni di telemetria model-driven e NETCONF che alimentano [[#Assurance|Assurance]]. Senza questo passaggio, un dispositivo è gestito ma non produce dati di health.

## Template

_Il nucleo programmabile della configurazione. Dove viene scritta configurazione riutilizzabile e parametrizzata per i dispositivi._

![[Pasted image 20260707164527.png]]

I template sono il modo in cui Catalyst Center applica configurazione che va oltre le [[#Network settings|impostazioni di rete]] standardizzate: tutto ciò che è specifico di sito, di funzionalità o di organizzazione. 

### Regular and composite templates

_Template singoli e sequenze ordinate di template._

Un template regolare è un singolo corpo di configurazione. Un template composito è una raccolta ordinata di template regolari applicati come unità, utile quando la configurazione di un dispositivo è costruita naturalmente da blocchi indipendenti mantenuti separatamente.

### Velocity e Jinja2

_I due linguaggi di templating e come scegliere._

I corpi dei template sono scritti in Apache Velocity (VTL) oppure Jinja2. Entrambi supportano sostituzione di variabili, condizionali e loop, ed entrambi possono accedere alle [[#Variabili e binding|variabili di sistema bind]] del contesto dispositivo descritte sotto; la scelta tra i due è in gran parte una questione di preferenza e competenza esistente. Velocity usa `#if`, `#foreach` e `$variable`; Jinja2 usa `{% if %}`, `{% for %}` e `{{ variable }}`.

#### Variabili e binding

_Come un template riceve valori per dispositivo e per interfaccia._

Le variabili possono essere libere (l'operatore digita un valore al momento del provisioning), vincolate a una lista di selezione, oppure avere un default ed essere marcate come obbligatorie. 

Oltre alle variabili fornite dall'operatore, Catalyst Center espone system bind variables: variabili speciali di sola lettura, tutte prefissate con doppio underscore, che popola da inventory e impostazioni globali invece di richiederle. 

Le due più usate sono `__device` (attributi del dispositivo target, letti in dot notation come `__device.hostname`) e `__interface` (una lista delle interfacce del dispositivo, iterata per leggere attributi come `portName`, `vlanId` e `portMode`). Questi binding permettono a un solo template di adattarsi a ogni dispositivo su cui viene inviato.

```bash
{% block interfaces %}
{% for interface in __interface %}
{% if interface.vlanId == 802 %}
interface {{ interface.portName }}
 source template ACCESS-PORT-TEMPLATE
{% elif interface.portMode == 'trunk' %}
interface {{ interface.portName }}
 ip dhcp snooping trust
 switchport trunk allowed vlan add 802,805,850
{% endif %}
{% endfor %}
{% endblock %}
```

> [!note] Le system bind variables non sono disponibili al Day-0
> Le system bind variables e i [[#Comandi interattivi|comandi interattivi]] dipendono entrambe dal fatto che il dispositivo esista già nell'inventory, quindi nessuna delle due può essere usata nei template di onboarding (Day-0): al primo contatto tramite [[#Plug and Play|Plug and Play]], il dispositivo non ha ancora un record di inventory. Riservale ai template [[#Template Day-0 e Day-N|Day-N]].

#### Condizionali e loop

_Branching e iterazione dentro il corpo di un template._

I blocchi condizionali includono o escludono configurazione in base a una variabile o a un attributo del dispositivo, e i loop ripetono un blocco su una raccolta (più comunemente la lista delle interfacce). È così che un singolo template può, per esempio, applicare una stanza alle porte access e una stanza diversa ai trunk nello stesso push.

### Template Day-0 e Day-N

_Configurazione di onboarding rispetto a configurazione continua._

Un template Day-0 risiede nel progetto di onboarding e viene applicato da [[#Plug and Play|Plug and Play]] quando un dispositivo factory-fresh si avvia per la prima volta. 

Un template Day-N (regolare) è tutto ciò che viene applicato durante o dopo il [[#Provisioning|provisioning]] tramite un [[#Network Profiles|profilo di rete]]: la configurazione di stato stabile di un dispositivo gestito. I template Day-0 sono volutamente limitati (niente [[#Variabili e binding|system bind variables]] e niente comandi interattivi); i template Day-N hanno l'intero set di funzionalità.

### Comandi interattivi

_Rispondere ai prompt CLI del dispositivo dentro un push automatizzato._

Alcuni comandi IOS-XE chiedono conferma, cosa che bloccherebbe un push non presidiato. Catalyst Center gestisce questo caso con marker di comando interattivo: il comando viene racchiuso tra `#INTERACTIVE` e `#ENDS_INTERACTIVE`, e al suo interno il prompt e la risposta sono separati da `<IQ>` (la domanda interattiva attesa, espressa come regular expression) e `<R>` (la risposta).

```bash
#INTERACTIVE
no access-session mac-move deny<IQ>.*Do you wish to continue\? \[yes\]:\s*<R>yes
#ENDS_INTERACTIVE
```

Il controller emette il comando, abbina il prompt di conferma del dispositivo con la regex dopo `<IQ>` e invia il testo dopo `<R>` (qui `yes`), così il push si completa senza intervento dell'operatore. Quando il comando che presenta il prompt deve essere eseguito in modalità EXEC privilegiata, il blocco interattivo viene annidato dentro un [[# Enable-mode and multi-line commands|blocco enable-mode]].

### Enable-mode and multi-line commands

_Costrutti per comandi che richiedono modalità EXEC privilegiata o si estendono su più righe._

Per impostazione predefinita, i comandi di un template vengono inviati in modalità di configurazione globale, una riga alla volta. Due costrutti gestiscono le eccezioni:

- I comandi enable-mode sono racchiusi tra `#MODE_ENABLE` e `#MODE_END_ENABLE`, che eseguono i comandi inclusi in modalità EXEC privilegiata (per esempio `write memory`, o uno `show` usato per guidare un passaggio [[#Comandi interattivi|interattivo]]). Un blocco interattivo può essere annidato al loro interno.
- I comandi multi-line, come banner, blocchi di certificato o un singolo comando lungo spezzato per leggibilità, sono racchiusi nei tag `<MLTCMD>` e `</MLTCMD>`. I tag devono stare ciascuno su una riga propria (non sulla stessa riga) e non devono iniziare con uno spazio; senza di essi, ogni riga viene inviata separatamente al dispositivo.

```bash
#MODE_ENABLE
write memory
#MODE_END_ENABLE
```

### Marker di compliance

_Dire al motore di compliance quali righe non trattare come drift._

La configurazione che differisce legittimamente dallo stato desiderato, o che non dovrebbe mai generare un flag di [[# Configuration drift and compliance|drift]], può essere racchiusa tra `! @start-ignore-compliance` e `! @end-ignore-compliance`. Il `!` iniziale rende queste righe commenti per il dispositivo, quindi IOS-XE le ignora, mentre il motore di compliance di Catalyst Center le legge come direttive per escludere la configurazione racchiusa dalla valutazione del drift.

```bash
! @start-ignore-compliance
radius-server vsa send authentication
radius-server vsa send accounting
! @end-ignore-compliance
```

> [!note] Perché racchiudere queste righe
> Comandi come `write memory`, o impostazioni che variano per dispositivo o vengono riordinate dal parser, altrimenti verrebbero riportati come configuration drift a ogni controllo di compliance. Racchiuderli mantiene significativo il report di compliance: segnala solo le differenze che contano davvero.

### Conflitti di Design

_Dove la CLI del template si sovrappone alla configurazione intent-based del controller._

![[Pasted image 20260707171428.png]]

Parte della configurazione è gestita da Catalyst Center tramite i suoi flussi intent-based (le funzionalità GUI per [[#Network settings|impostazioni di rete]], wireless, [[#Policy|policy]] e SD-Access) e parte viene scritta come CLI grezza in un template. Quando un template invia un comando che anche il controller gestisce per intento, i due possono competere, e il risultato dipende dall'ordine di push. Il controllo dei design conflict dell'editor segnala questi comandi affinché possano essere rimossi dal template e lasciati al provisioning intent-based, che è la divisione del lavoro consigliata.

> [!warning] Non mettere in template ciò che il controller provisiona per intento
> Reinviare da template configurazione gestita per intento invita configuration drift e sovrascritture imprevedibili. Usa i template per ciò che l'intent non copre, e lascia il resto ai flussi integrati.

### Binding templates through network profiles

_L'ultimo passaggio che fa sì che un template abbia effetto._

Un template che è stato fatto il commit non fa nulla finché non viene associato a un [[#Network Profiles|profilo di rete]] e quel profilo non viene assegnato a un sito. Quando un dispositivo nel sito viene [[#Provisioning|provisionato]], il template viene renderizzato con i valori delle variabili e il contesto del dispositivo, e poi inviato. Authoring, commit, binding e provisioning sono quattro passaggi distinti, e saltare il passaggio di binding è il motivo più comune per cui un template "non si applica".

## Software Image Management

_Standardizzare e aggiornare il software dei dispositivi su larga scala. Comunemente abbreviato SWIM._

SWIM applica una versione software coerente in tutto il parco dispositivi, sostituendo gli upgrade manuali per singolo dispositivo.

### Immagini golden

_L'immagine corretta dichiarata per una famiglia e un ruolo di dispositivo._

Un'immagine marcata come golden nel [[#Repository immagini|repository immagini]] è lo stato software desiderato per una data famiglia di dispositivi, [[#Device roles|ruolo]] e sito. Qualsiasi dispositivo gestito che non esegua la propria immagine golden viene segnalato in [[# Configuration drift and compliance|compliance]].

### Distribuzione e attivazione

_La procedura di upgrade a due fasi e a basso rischio._

Gli upgrade sono divisi deliberatamente: 
- La distribuzione copia l'immagine nella flash del dispositivo senza interrompere il traffico.
- L'attivazione ricarica il dispositivo sulla nuova immagine (con In-Service Software Upgrade sulle piattaforme che lo supportano).
Separare le due fasi significa che lo staging può essere fatto durante il giorno e il reload impattante schedulato in una finestra di manutenzione.

### Upgrade readiness

_Controlli pre-flight prima di un'attivazione._

Prima dell'attivazione, il controller esegue controlli preliminari di readiness: spazio flash, configuration register, compatibilità hardware e versione, così che un upgrade venga tentato solo sui dispositivi che possono riuscire. 

I controlli pre e post-upgrade possono essere confrontati per confermare che il dispositivo sia tornato in stato sano.

## Plug and Play

_Onboarding Day-0 non presidiato di dispositivi factory-fresh. Comunemente abbreviato PnP._

PnP avvia un dispositivo nuovo di fabbrica senza sessione console manuale, ed è ciò che rende possibile la distribuzione in siti remoti senza un tecnico sul posto.

### Il flusso di onboarding

_Come un dispositivo factory trova il controller e si configura._

Un dispositivo factory-default con connettività di rete individua il server PnP (Catalyst Center) tramite uno di diversi meccanismi: <strong>opzione DHCP 43</strong>, record DNS per `pnpserver`, oppure reindirizzamento cloud tramite il servizio Cisco PnP Connect associato allo Smart Account. Una volta raggiunto il controller, richiede la propria configurazione.

### Claim dei dispositivi

_Autorizzare un dispositivo e assegnargli cosa deve diventare._

I dispositivi possono essere pre-registrati per numero di serie (planned) oppure apparire come unclaimed quando chiamano casa. Fare claim di un dispositivo lo assegna a un sito, seleziona l'immagine software da caricare e applica il [[#Template Day-0 e Day-N|template di onboarding]] Day-0 dal progetto di onboarding. Il dispositivo quindi si provisiona senza intervento e finisce nell'[[#Inventory|inventory]] come dispositivo gestito, dopodiché si applica il normale [[#Provisioning|provisioning]].
## LAN Automation

_Costruzione zero-touch di un underlay routed-access IS-IS a partire da un dispositivo seed._

LAN Automation è l'alternativa alla creazione manuale di una nuova rete routed. Da un dispositivo seed già gestito scopre gli switch factory-default cablati sotto di esso, li porta alla loro [[#Immagini golden|immagine golden]] tramite [[#Software Image Management|SWIM]] e invia una configurazione Layer 3 routed-access best-practice a tutto il livello senza CLI per dispositivo. È usata più spesso per costruire l'underlay su cui gira una [[#Fabric SD-Access|fabric SD-Access]], ma la rete routed che produce è ugualmente valida per un disegno routed-access tradizionale. Riutilizza il meccanismo di onboarding [[#Plug and Play|Plug and Play]], quindi valgono gli stessi prerequisiti: una [[#Network Hierarchy|gerarchia di rete]], [[#Network and server settings|server di rete]] globali e [[#Credenziali dei dispositivi|credenziali dei dispositivi]], un [[#Pool di indirizzi IP|pool IP]] riservato e almeno il dispositivo seed già nell'[[#Inventory|inventory]].

### Dispositivi seed e discovery

_Come il controller raggiunge e onboarda i nuovi switch._

Una sessione parte da un dispositivo seed (primario), cioè uno switch esistente e gestito al layer core o distribution, e facoltativamente da un peer seed così che gli switch scoperti possano essere dual-homed. Il controller configura uno scope DHCP temporaneo sul seed; gli switch Catalyst 9000 factory-default cablati a esso si avviano come agent PnP, ottengono un indirizzo e contattano il controller. La discovery si estende al massimo a due hop dal seed, quindi avviare il confine al layer core o distribution è ciò che consente a una run di raggiungere l'access layer. Dispositivi oltre due hop possono essere visti ma non automatizzati.

### Cosa provisiona LAN Automation

_La configurazione underlay scritta su ciascun dispositivo scoperto._

Gli indirizzi provengono da un pool IP riservato di tipo LAN. Da esso, ogni dispositivo scoperto riceve un /31 univoco su ogni link point-to-point e un /32 per `Loopback0`, che diventa il router ID e l'indirizzo di management del dispositivo. Il controller imposta anche l'MTU di sistema, abilita IP routing, porta il dispositivo alla sua immagine golden e configura il protocollo di routing:

- IS-IS è sempre l'IGP dell'underlay. È scelto perché le sue adiacenze si formano senza alcuna dipendenza IP, può fare peering su loopback e tratta allo stesso modo traffico IPv4, IPv6 e non-IP, tutte proprietà che rendono più robusta una costruzione automatizzata e ordinata.
- Il multicast underlay è un attributo opzionale (necessario per flooding Layer 2 fabric e multicast nativo); quando è abilitato, i seed sono configurati come rendezvous point PIM.
- Il summary del pool LAN può opzionalmente essere annunciato in un processo BGP preconfigurato sui seed, così il controller mantiene raggiungibilità verso i dispositivi scoperti senza route statiche.

> [!note] Perché IS-IS invece di OSPF o EIGRP
> IS-IS gira direttamente su Layer 2 e non richiede un indirizzo IP per formare un'adiacenza, quindi il controller può portare su i vicini prima che l'indirizzamento sia convergito. Questa proprietà, insieme al supporto dual-stack nativo e al peering su loopback, è il motivo per cui Cisco ha standardizzato l'underlay automatizzato su IS-IS.

### Avvio e arresto di una sessione

_Le due fasi e cosa succede realmente con Stop._

Una run viene lanciata da `Provision > LAN Automation` selezionando il seed (e il peer), le interfacce seed da usare, il sito target e il pool IP; fino a cinque sessioni possono girare contemporaneamente su siti diversi. Start apre la sessione e onboarda i dispositivi man mano che appaiono: DHCP, immagine e configurazione base vengono applicati mentre la sessione resta aperta. Stop la finalizza: i link point-to-point tra seed e dispositivi scoperti vengono convertiti in link routed Layer 3, lo scope DHCP temporaneo e la configurazione VLAN 1 vengono rimossi, e il subpool DHCP viene restituito al pool LAN. I dispositivi appaiono poi nell'[[#Inventory|inventory]] come normali dispositivi gestiti, pronti per essere [[#Provisioning|provisionati]] e ricevere [[#Template|template]].

> [!important] L'underlay non è finito finché non premi Stop
> La conversione Layer 3 e la pulizia avvengono con Stop, non con Start. Una sessione lasciata aperta mantiene lo scope DHCP temporaneo del seed e i dispositivi scoperti su indirizzamento transitorio, quindi una run deve essere arrestata per raggiungere il suo stato finale e supportato.

## Policy

_Definire chi e cosa può comunicare, e come viene trattato il traffico._

Il dominio Policy (`Policy` nella GUI) è il livello di intento per controllo di accesso e qualità del servizio. Le sue capacità di access control dipendono da [[#Cisco ISE e pxGrid|ISE]] come motore AAA e di distribuzione runtime.

### Group-Based Access Control

_Segmentazione per gruppo di sicurezza invece che per indirizzo IP._

![[Pasted image 20260707173804.png]]

Group-Based Access Control (GBAC) è il front end di Catalyst Center per Cisco TrustSec. 

Gli endpoint ricevono uno Scalable Group Tag (SGT) all'autenticazione, e una matrice di policy group-based definisce quali gruppi sorgente possano raggiungere quali gruppi destinazione, indipendentemente dall'indirizzamento IP. 

Catalyst Center crea gli SGT e la matrice di policy e li sincronizza verso [[#Cisco ISE e pxGrid|ISE]]; ISE assegna l'SGT a ciascun endpoint in fase di autorizzazione e distribuisce le Security Group ACL (SGACL) corrispondenti ai dispositivi di rete, che eseguono l'enforcement reale.

> [!important] ISE è un prerequisito per la policy group-based
> Group-Based Access Control è disponibile solo quando [[#Cisco ISE e pxGrid|Cisco ISE]] è integrato come server di autenticazione e policy. All'installazione o all'upgrade, il controller verifica la presenza di un ISE connesso e di versione compatibile; se è assente, la piattaforma si installa ma la policy group-based resta disabilitata. I dati SGT e policy esistenti vengono importati tramite una migrazione una tantum dei dati di policy da ISE.

### Application QoS

_QoS end-to-end guidata dall'identità applicativa._

![[Pasted image 20260707173750.png]]

Application policy consente di classificare applicazioni in gruppi, marcare ciascuna come business-relevant, default o business-irrelevant, e associarla a un profilo di queuing. Il controller renderizza quindi la configurazione QoS di marking e queuing corrispondente (usando il modello di classi del profilo SP sui link WAN) e la invia ai dispositivi nello scope.

### IP & URL Based Access Control

_Controllo classico in stile ACL per ambienti non-SGT._

![[Pasted image 20260707173735.png]]

Dove non si usa segmentazione basata su SGT, le policy di access control basate su IP applicano regole permit e deny tra pool IP, offrendo un modello più tradizionale di access list gestito centralmente.

## Assurance

_Visibilità continua, guidata dalla telemetria, su salute della rete e dei client._

Assurance (`Assurance` nella GUI) consuma la [[#Attivazione della telemetria|telemetria]] abilitata al provisioning per calcolare punteggi di salute ed esporre problemi. È principalmente un dominio di monitoraggio, ma ha dipendenze di configurazione reali, soprattutto il fatto che la telemetria sia attiva e, per i test sintetici, che sensori e test siano definiti.

### Health

_Punteggi di salute aggregati su tutta la rete._

![[Pasted image 20260707173847.png]]

Assurance presenta dashboard di salute overall, network, client e application, ognuna delle quali aggrega metriche individuali in un punteggio e consente all'operatore di fare drill down da un sito fino a un singolo dispositivo o sessione client. Le viste per-entità Device 360, Client 360 e Application 360 raccolgono tutto ciò che è noto su un dispositivo, client o applicazione in un'unica timeline.

### Issue e machine reasoning

_Rilevamento automatico e analisi guidata della root cause._

![[Pasted image 20260707173939.png]]

![[Pasted image 20260707174059.png]]

I problemi rilevati vengono aperti come issue e prioritizzati per impatto. Il Machine Reasoning Engine offre flussi guidati o automatici di root-cause analysis per pattern di guasto comuni, riducendo la correlazione manuale che un ingegnere dovrebbe altrimenti fare a mano.

### Sensors and synthetic tests

_Sondare attivamente la rete dal punto di vista del client._

![[Pasted image 20260707174145.png]]

Oltre alla telemetria raccolta passivamente, sensori dedicati o access point che agiscono da sensori eseguono test sintetici: associazione, autenticazione contro [[#Cisco ISE e pxGrid|ISE]], DHCP, DNS e raggiungibilità applicativa, così che l'esperienza client sia misurata proattivamente e non solo dopo un reclamo utente. I test, i loro SSID target e la loro schedulazione sono configurati in Assurance. Per troubleshooting wireless più profondo, Intelligent Capture raccoglie dati packet e RF on-demand o schedulati direttamente da access point e client.

## Integrazioni

_Collegare Catalyst Center all'ecosistema circostante._

Le integrazioni sono configurate in `System > Settings` e nei [[#Bundle e impostazioni di integrazione|bundle di integrazione]]. 

### Cisco ISE e pxGrid

_Il partner di identità e policy, integrato in entrambe le direzioni._

Catalyst Center integra Cisco ISE come server di autenticazione e policy. La connessione usa pxGrid per lo scambio contestuale (dati endpoint e gruppi) insieme a una connessione API ERS per la configurazione, ed è la base per [[#Group-Based Access Control|group-based access control]] e [[#Fabric SD-Access|SD-Access]]. L'integrazione opera in due direzioni che vale la pena distinguere:

- Da Catalyst Center a ISE: il controller programma SGT e policy group-based in ISE e consuma da esso il contesto degli endpoint.
- Da ISE a Catalyst Center: ISE può anche agire come sorgente di [[#Autenticazione esterna|autenticazione esterna]] per la GUI di Catalyst Center stessa, restituendo un ruolo amministrativo ai login RADIUS tramite un `cisco-av-pair` nella forma `ROLE=<role-name>` (per esempio `ROLE=SUPER-ADMIN-ROLE`).

### Gestione degli indirizzi IP

_Sincronizzare lo spazio di indirizzamento con un IPAM esterno._

Un IP Address Manager esterno (come Infoblox o BlueCat) può essere integrato in modo che i [[#Pool di indirizzi IP|pool di indirizzi]] usati per l'automazione siano originati dall'IPAM autorevole dell'organizzazione e riconciliati con esso, invece di essere mantenuti due volte.

## Fabric SD-Access

_Un'architettura overlay opzionale per segmentazione policy-based e indipendente dalla posizione._

SD-Access è una capability importante ma opzionale, non un requisito di base; una distribuzione può gestire un campus tradizionale tramite [[#Design|Design]] e [[#Provisioning|provisioning]] senza mai costruire una fabric. Dove viene usata, Catalyst Center automatizza la costruzione di una rete overlay sopra un underlay routed.

### Underlay e overlay

_Il trasporto sotto la fabric e la rete virtuale sopra di esso._

L'underlay è una rete IP routed (costruita manualmente o da [[#LAN Automation|LAN Automation]], che usa IS-IS). L'overlay trasporta il traffico utente ed è costruito su tre piani: un control plane LISP per posizione e risoluzione degli endpoint, un data plane VXLAN che incapsula il traffico utente attraverso l'underlay, e un policy plane Cisco TrustSec che trasporta gli [[#Group-Based Access Control|SGT]] per la segmentazione. Siti fabric separati sono uniti da un transit: un transit basato su IP attraverso una rete routed tradizionale, oppure un transit SD-Access che preserva informazioni di rete virtuale e SGT end-to-end tra siti.

### Ruoli fabric

_Le funzioni svolte dai dispositivi dentro una fabric._

- Control plane node: il map server e map resolver LISP che traccia dove si trova ogni endpoint.
- Border node: il gateway tra la fabric e il mondo esterno (altre fabric, data center, Internet).
- Edge node: l'access layer a cui si connettono gli endpoint e dove vengono registrati nella fabric.
- Fabric WLC e AP in fabric-mode estendono lo stesso modello al wireless.

### Reti virtuali e onboarding degli host

_Mappare pool di indirizzi e gruppi in reti virtuali segmentate._

Le reti virtuali (VN) sono le VRF della fabric e forniscono macro-segmentazione. L'host onboarding associa un [[#Pool di indirizzi IP|pool IP]] a una VN, assegna [[#Group-Based Access Control|SGT]] per la micro-segmentazione al suo interno e seleziona il template di autenticazione porta (closed, open o low-impact) che governa come gli endpoint vengono ammessi. Ogni edge node condivide lo stesso distributed anycast gateway per un dato pool, quindi il default gateway di un endpoint è identico ovunque si connetta e il roaming non richiede rinumerazione.

## Amministrazione di sistema

_Gestire il controller stesso: accesso, protezione dei dati e software._

Le impostazioni di sistema (`System` nella GUI) governano la piattaforma invece della rete gestita.

### Utenti e controllo di accesso basato sui ruoli

_Controllare chi può fare cosa dentro Catalyst Center._

![[Pasted image 20260707174602.png]]

L'accesso è governato dal role-based access control (RBAC). I ruoli integrati includono SUPER-ADMIN (controllo completo), NETWORK-ADMIN e OBSERVER (sola lettura), e ruoli custom possono delimitare l'accesso ad aree funzionali specifiche. Il ruolo posseduto da un utente è esattamente ciò che l'integrazione di [[#Autenticazione esterna|autenticazione esterna]] restituisce per i login remoti.

### Autenticazione esterna

_Delegare il login GUI a un server AAA esterno._

![[Pasted image 20260707174626.png]]

La GUI di Catalyst Center può autenticare gli amministratori contro un server RADIUS o TACACS+ esterno come [[#Cisco ISE e pxGrid|Cisco ISE]]. Il server restituisce il ruolo Catalyst Center dell'utente in un `cisco-av-pair` contenente `ROLE=<role-name>` (per esempio `ROLE=SUPER-ADMIN-ROLE`), che il controller mappa al corrispondente [[#Utenti e controllo di accesso basato sui ruoli|ruolo RBAC]]. Un account locale di fallback dovrebbe sempre essere mantenuto, così che la perdita del server AAA non blocchi fuori gli amministratori.

### Backup e restore

_Proteggere il database e la configurazione del controller._

![[Pasted image 20260707174648.png]]

I backup vengono scritti su un server esterno (comunemente NFS) e possono essere schedulati. Poiché il controller conserva lo stato desiderato dell'intera rete, un backup corrente è operativamente critico: un restore ricostruisce il modello gestito, non solo l'appliance.

### Aggiornamenti di sistema e pacchetti

_Mantenere la piattaforma aggiornata sui suoi due livelli._

La gestione software aggiorna il pacchetto di sistema e i pacchetti applicativi, provenienti dal catalogo cloud oppure, per reti isolate, da una ISO air-gapped. Le release seguono una cadenza basata sul tempo (circa tre feature release all'anno con patch periodiche), e Cisco designa una release consigliata per la produzione. I percorsi di upgrade tra versioni sono vincolati, quindi il percorso supportato deve essere verificato prima di qualsiasi salto.

### Certificati

_Stabilire trust per la GUI e per la comunicazione con i dispositivi._

Un certificato server PKI può essere importato così che GUI e API siano presentate tramite un certificato trusted invece del default self-signed, e il trust store del controller contiene i certificati necessari per validare sistemi integrati e dispositivi gestiti.

## Piattaforma e API

_Il livello programmabile sotto la GUI. Tutto ciò che l'interfaccia fa è, sotto, una chiamata API._

Il dominio Platform (`Platform` nella GUI) espone Catalyst Center per automazione e integrazione, ed è ciò che rende il controller un building block invece di un'appliance chiusa.

### Intent API

_L'interfaccia REST northbound per automatizzare il controller._

L'Intent API è una REST API northbound che rispecchia il modello di intento della GUI: discovery, inventory, siti, template, provisioning e policy possono tutti essere guidati programmaticamente. Le chiamate sono autenticate con un token e delimitate dal ruolo [[#Utenti e controllo di accesso basato sui ruoli|RBAC]] del chiamante, quindi l'accesso API rispetta lo stesso modello di permessi della GUI. Accanto a essa, API di integrazione westbound collegano sistemi esterni come ITSM e [[#Gestione degli indirizzi IP|IPAM]], e un SDK southbound multivendor con device pack consente al controller di gestire dispositivi di terze parti selezionati.

### Bundle e impostazioni di integrazione

_Abilitare i pacchetti di integrazione e funzionalità del controller._

![[Pasted image 20260707174858.png]]

I bundle di integrazione (per esempio ITSM, oppure l'applicazione Rogue Management and aWIPS) sono abilitati e configurati qui. Abilitare un bundle espone le sue impostazioni specifiche e, dove rilevante, i relativi endpoint API.

### Eventi e notifiche

_Inviare eventi del controller verso altri sistemi._

![[Pasted image 20260707174954.png]]

Catalyst Center può pubblicare eventi, dalle issue di Assurance alle notifiche di sistema, verso consumatori esterni tramite webhook, email, syslog o SNMP, guidato da un catalogo eventi che enumera ciò a cui ci si può sottoscrivere. È così che il controller alimenta dashboard, chat-ops e sistemi di ticketing quasi in tempo reale. Un motore di reporting separato produce report schedulati e on-demand, come riepiloghi di inventory, compliance, client ed executive, in formati come PDF e CSV.

## Licensing

_Cosa serve per gestire dispositivi e sbloccare livelli funzionali._

![[Pasted image 20260707175038.png]]

Catalyst Center è la console di gestione; il diritto di usarne le funzionalità è portato da licenze subscription per dispositivo. Storicamente questi erano i tier Cisco DNA Essentials, Advantage e Premier, ora allineati sotto il modello di subscription Cisco Networking che ha accompagnato il rebrand Catalyst. I tier più alti sbloccano le capability più avanzate: per esempio, SD-Access e [[#Assurance|Assurance]] completa richiedono licenze di livello Advantage. Le licenze sono gestite tramite Cisco Smart Licensing contro uno Smart Account in Cisco Smart Software Manager, e il controller riporta la compliance rispetto agli entitlement che vede.
