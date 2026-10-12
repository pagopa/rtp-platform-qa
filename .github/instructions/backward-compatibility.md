# Linee Guida per la Gestione della Retrocompatibilità

## Principio e significato degli obblighi

Una modifica è retrocompatibile quando i sistemi esterni esistenti possono continuare a interagire con il servizio aggiornato senza modifiche obbligatorie, nel rispetto dei contratti strutturali, semantici e operativi concordati.

**DEVE**, **NON DEVE** e **DEVONO** indicano obblighi; **PUÒ** indica una scelta. Versionamento, header e feature flag sono strumenti e **NON DEVONO** essere considerati, da soli, prova di retrocompatibilità.

La valutazione riguarda i contratti e i consumatori identificati, non utilizzi sconosciuti o comportamenti non supportati. Contratti impliciti utilizzati dai consumatori identificati **DEVONO** essere censiti e trattati esplicitamente, non ignorati perché non documentati. Lacune nell'inventario **DEVONO** essere dichiarate: non è ammessa una garanzia assoluta priva di evidenze.

## BC-SCOPE: Perimetro esterno e analisi di impatto

Per ogni modifica **DEVONO** essere identificati i confini interessati, i contratti esistenti e i relativi consumatori o responsabili. Il perimetro include:

- API in ingresso e chiamate in uscita, REST e altri protocolli, callback e webhook.
- Messaggi prodotti e consumati, topic, code, subscription e schemi condivisi.
- Database e storage condivisi, file importati/esportati e processi batch o schedulati.
- Configurazioni, credenziali, permessi e meccanismi di autenticazione utilizzati nell'integrazione.
- Health check, metriche, log e altri segnali su cui si basano monitoraggi o automazioni esterne.

L'analisi **DEVE** considerare anche modifiche indirette dovute a librerie, serializer, framework, configurazioni o infrastruttura. Un refactoring che preserva tutti i contratti non richiede una nuova versione, ma **DEVE** essere verificato rispetto ai comportamenti interessati.

## BC-BEHAVIOR: Compatibilità semantica e operativa

Per i consumatori esistenti **DEVONO** essere preservati significato e unità dei dati, obbligatorietà e default, gestione di NULL e valori mancanti, validazioni, errori, codici di stato, ordinamento e paginazione previsti dal contratto.

**DEVONO** essere preservate le garanzie concordate di autenticazione e autorizzazione, idempotenza, effetti collaterali, transazioni, retry, deduplicazione, ordine e consegna dei messaggi.

La modifica **NON DEVE** violare timeout, limiti, disponibilità o obiettivi prestazionali concordati. Non è richiesta l'identità di ogni dettaglio interno, ma il rispetto delle garanzie esterne. Cambiare il significato di un campo mantenendone nome e tipo è una modifica del contratto.

Le chiamate in uscita **DEVONO** restare compatibili con le versioni effettivamente supportate dalle dipendenze: il servizio aggiornato **NON DEVE** presumere che un downstream sia già stato aggiornato.

## BC-REST: Modifiche alle interfacce REST API

Ogni modifica del contratto REST, strutturale o semantica, **DEVE** essere versionata tramite header HTTP, ad esempio `X-API-Version`. Il nome è esemplificativo; versionamento solo nel path, nella query o nel body non soddisfa questa regola.

- L'header **DEVE** selezionare realmente il contratto e la logica della versione richiesta, non essere solo documentato.
- Le versioni già supportate **DEVONO** continuare a rispettare il comportamento precedente e rimanere utilizzabili dai relativi client.
- L'assenza dell'header **DEVE** preservare il comportamento dei client precedenti che non lo inviavano; **NON DEVE** selezionare automaticamente una nuova versione incompatibile.
- Versioni sconosciute o header malformati **DEVONO** essere gestiti secondo una politica esplicita, senza attivare implicitamente logiche incompatibili.
- Specifiche API, routing, gateway e gestione degli header **DEVONO** essere coerenti con l'implementazione. Cache e proxy **DEVONO** distinguere le varianti dove necessario, senza restituire risposte di una versione a client di un'altra.

## BC-DB: Modifiche allo schema e ai dati

Nel percorso retrocompatibile **SI POSSONO** solo aggiungere campi **NULLABLE**; **NON SI DEVONO** rimuovere o rinominare campi, cambiarne il tipo o introdurre nuovi campi obbligatori. Un default non rende conforme un nuovo campo NOT NULL.

- Lettura, deserializzazione e logica applicativa **DEVONO** gestire sia NULL sia record/documenti privi dei nuovi campi.
- **DEVONO** continuare a funzionare gli utilizzatori esistenti del database, incluse le versioni precedenti del servizio durante rollout e rollback. **DEVONO** essere verificati SQL posizionale, `SELECT *`, ORM, mapping e validatori: un'aggiunta nullable non è automaticamente sicura.
- Modifiche a vincoli, relazioni, indici, viste, procedure, trigger e permessi **DEVONO** essere analizzate rispetto a comportamenti, query e garanzie esistenti; **NON DEVONO** introdurre incompatibilità.
- Migrazioni e backfill **DEVONO** preservare significato, leggibilità e scrivibilità dei dati per le versioni che devono coesistere. **NON DEVONO** introdurre lock o indisponibilità oltre i limiti concordati.
- I dati scritti dalla nuova versione **DEVONO** restare gestibili dalla versione di rollback finché il rollback è previsto. Un rollback applicativo **NON DEVE** presumere che le modifiche ai dati siano annullate.

Rimozioni o trasformazioni incompatibili dello schema richiedono il percorso di migrazione coordinata di BC-RELEASE e **NON DEVONO** essere dichiarate retrocompatibili.

## BC-MSG: Messaggi Kafka e Azure Service Bus

Ogni modifica della struttura o della semantica del payload **DEVE** essere versionata tramite header del messaggio, ad esempio `X-Msg-Version`, effettivamente scritto e letto nei metadati di trasporto. Una versione solo nel payload o nel nome del topic non basta.

- I consumer aggiornati **DEVONO** gestire le versioni precedenti ancora supportate, inclusi messaggi in transito, backlog, retry, dead-letter e replay previsti dal contratto.
- L'assenza dell'header **DEVE** mantenere l'interpretazione dei messaggi precedenti che non lo contenevano. Versioni sconosciute o malformate **DEVONO** seguire una politica esplicita senza perdita silenziosa dei messaggi.
- Un producer aggiornato **NON DEVE** inviare un nuovo formato a consumer che non lo supportano. L'header da solo non protegge i consumer vecchi: **DEVE** essere mantenuto un formato compatibile o previsto un instradamento che separi i flussi, con sequenza di aggiornamento verificata.
- Eventuali pubblicazioni parallele **NON DEVONO** duplicare effetti collaterali per lo stesso consumatore.
- **DEVONO** essere preservati anche i contratti di chiavi e partizionamento, routing, ordinamento, retention, TTL, consegna e deduplicazione interessati dalla modifica.

## BC-FEATURES: Logiche differenti on-demand

Quando servono logiche attivate caso per caso e non sono utilizzabili i meccanismi REST, DB o messaggi sopra descritti, **DEVE** essere previsto l'header multi-valore `X-Features` in **TUTTI** gli ingressi REST, Kafka e Azure Service Bus dell'applicazione.

- **DEVONO** essere definite sintassi, valori ammessi, gestione di valori sconosciuti e combinazioni supportate. In assenza dell'header **DEVE** restare attiva la logica precedente.
- Tutti i valori **DEVONO** essere propagati ai servizi downstream coinvolti, anche nei passaggi tra HTTP e messaggistica, senza perdite o sovrascritture e rispettando i confini di fiducia.
- L'attivazione **DEVE** essere autorizzata. Un header ricevuto da un chiamante non fidato **NON DEVE** abilitare funzioni riservate o test in produzione.
- Le funzioni richieste **DEVONO** essere supportate dai servizi che le eseguono; la propagazione **NON DEVE** essere interpretata come prova del loro supporto.
- Le varianti **DEVONO** preservare i contratti esterni o essere isolate tramite una migrazione concordata. Test in produzione **DEVONO** isolare gli effetti su dati, messaggi e sistemi esterni.

## BC-FLAGS: Feature flag

Per logiche diverse non attivate caso per caso **SI PUÒ** ricorrere a feature flag: parametri di configurazione che abilitano le nuove logiche, **DEVONO** essere disattivati di default.

- Default nel codice, configurazioni distribuite e fallback per parametro assente o non valido **NON DEVONO** abilitare implicitamente la nuova logica.
- Sia la variante precedente sia quella nuova **DEVONO** rispettare i contratti esterni supportati. Le combinazioni di flag ammesse **DEVONO** essere definite e verificate.
- L'attivazione **DEVE** rispettare la capacità dei downstream e la sequenza di rollout. Un flag **NON DEVE** sostituire versionamento o `X-Features` quando obbligatori.
- La disattivazione **NON DEVE** essere considerata annullamento degli effetti già prodotti: dati scritti e messaggi emessi **DEVONO** essere compatibili con la logica ripristinata oppure richiedono un piano esplicito di recupero.

## BC-RELEASE: Rollout, rollback e dismissione

Prima del rilascio **DEVONO** essere definite le combinazioni di versioni di servizio, client, dipendenze, producer, consumer e schema che possono coesistere, la sequenza di aggiornamento e il piano di rollback o recupero.

**DEVONO** essere verificate tutte le combinazioni ammesse, compresa la gestione dei dati e dei messaggi prodotti durante il rollout. Non è richiesta compatibilità con combinazioni vietate, purché i vincoli di distribuzione ne impediscano realmente l'uso.

Una modifica incompatibile **DEVE** essere dichiarata come tale e accompagnata da migrazione coordinata, responsabili, consenso dei consumatori coinvolti, periodo di transizione e criteri verificabili di completamento. Una versione o struttura precedente **PUÒ** essere rimossa solo dopo aver accertato che non sia più necessaria, inclusi backlog e replay ancora supportati.

Un'approvazione eccezionale **NON DEVE** trasformare una breaking change in una dichiarazione di retrocompatibilità. Correzioni urgenti di sicurezza **DEVONO** rendere espliciti gli impatti e il relativo percorso di gestione.

## BC-EVIDENCE: Evidenze richieste in code review

Ogni PR **DEVE** descrivere superfici e consumatori interessati, contratti preservati, eventuali incompatibilità, combinazioni di versioni ammesse e piano di rollout/rollback. Per modifiche senza impatto esterno è sufficiente una motivazione verificabile.

Per le superfici interessate **DEVONO** essere fornite evidenze proporzionate al rischio:

- Test di contratto e regressione con richieste, dati e messaggi precedenti, anche senza nuovi header o campi.
- Test delle nuove versioni, delle varianti abilitate/disabilitate e delle combinazioni ammesse.
- Test di integrazione con le versioni esterne supportate o contratti rappresentativi concordati con i consumatori.
- Verifiche di migrazione, coesistenza, rollback e garanzie operative ove pertinenti.

Le evidenze **DEVONO** distinguere test eseguiti e relativi risultati da test solo proposti. Aspetti non verificabili **DEVONO** essere dichiarati con evidenze mancanti, responsabile e azione richiesta prima del rilascio; **NON DEVONO** essere presentati come conformi.

La review considera il diff complessivo della PR e, quando disponibili, i singoli commit. Ogni stato rilasciabile **DEVE** rispettare queste regole; i commit intermedi non rilasciabili **NON DEVONO** essere distribuiti autonomamente.

GitHub Copilot supporta la verifica e segnala le violazioni, ma **NON** sostituisce test, valutazione dei responsabili e controlli di rilascio. L'assenza di commenti nella review **NON** costituisce prova di retrocompatibilità.