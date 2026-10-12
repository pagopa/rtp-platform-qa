---
applyTo: "**"
excludeAgent: "cloud-agent"
---

# Code review: retrocompatibilita

Nella review rispondi in italiano e applica [la policy](backward-compatibility.md) al diff della PR e ai commit disponibili rispetto ai parent. Non dichiarare verificati commit non esaminati. Non modificare codice.

## Metodo e segnalazioni

- Leggi la policy e verifica codice, contratti, migrazioni, configurazioni, test e implementazioni collegate. Header, flag o dichiarazioni non provano conformita.
- Segnala problemi introdotti/aggravati dal diff. Escludi superfici estranee; refactoring a contratti invariati non richiedono versioni.
- Indica ID, file e riga pertinente, evidenza, impatto e correzione minima. Ordina per gravita senza duplicati.
- Distingui violazioni, aspetti non verificabili e prove obbligatorie mancanti. Non inventare comportamenti o esiti; non dichiarare conformita senza prove. Una breaking change approvata resta incompatibile.

## BC-SCOPE: perimetro esterno

Verifica inventario e impatto su ingressi/uscite, webhook, messaggi, dati, file, batch, configurazioni, permessi e segnali operativi. Considera contratti impliciti, dipendenze e infrastruttura. Esplicita consumatori non identificati.

## BC-BEHAVIOR: semantica e operativita

Verifica significato e unita dei dati, default, NULL, validazioni, errori, ordine, paginazione, auth, idempotenza, transazioni, effetti collaterali e garanzie di messaggistica. Controlla timeout e obiettivi operativi concordati e compatibilita con downstream non aggiornati.

## BC-REST: interfacce REST

Modifiche strutturali o semantiche richiedono versione via header HTTP (es. `X-API-Version`) che selezioni la logica. Path/query/body non bastano. Preserva versioni supportate e comportamento senza header; verifica versioni sconosciute, specifiche, gateway, proxy e cache. I nomi degli header di versione sono esempi.

## BC-DB: schema dei database

Nel percorso retrocompatibile ammetti solo nuovi campi NULLABLE, non rimozioni, rinomine o cambi di tipo; un default non giustifica NOT NULL. Verifica campi assenti, SQL posizionale, SELECT *, mapping, validatori, vincoli, viste, trigger, indici e permessi. Controlla lock, backfill e leggibilita/scrivibilita dei dati per versioni coesistenti e di rollback.

## BC-MSG: Kafka e Azure Service Bus

Ogni modifica strutturale o semantica richiede versione nei metadati (es. `X-Msg-Version`), scritta dal producer e letta dal consumer. Verifica messaggi precedenti, header assente/sconosciuto, backlog, retry, dead-letter e replay. I producer nuovi non devono inviare formati incompatibili ai consumer vecchi: verifica formato o routing e sequenza di aggiornamento. Controlla partizionamento, TTL, retention e duplicazione degli effetti.

## BC-FEATURES: logiche on-demand

Quando richiesto dalla policy, verifica `X-Features` multi-valore in tutti gli ingressi REST/Kafka/Service Bus e propagazione downstream HTTP/messaggi. Controlla sintassi, valori e combinazioni, assenza dell'header, autorizzazione, confini di fiducia e supporto downstream. Le varianti e i test in produzione non devono compromettere sistemi esterni.

## BC-FLAGS: feature flag

Sono facoltativi, ma disattivi di default anche nelle configurazioni e nei fallback. Verifica varianti, combinazioni e attivazione coordinata. Disattivarli non annulla dati o messaggi prodotti. Non sostituiscono versionamento o X-Features obbligatori.

## BC-RELEASE: distribuzione e dismissione

Verifica versioni ammesse, vincoli contro combinazioni vietate e rollout/rollback. Dismissioni richiedono migrazione coordinata, consenso e criteri verificabili, inclusi backlog/replay. Ogni stato rilasciabile deve essere conforme.

## BC-EVIDENCE: prove di conformita

Verifica impatto nella PR e prove: regressione, contratti vecchi/nuovi, integrazione, varianti, coesistenza, migrazioni, rollback e limiti operativi. Distingui test eseguiti da proposti. Per lacune indica prova mancante, responsabile e azione prima del rilascio. La review non sostituisce test e controlli di rilascio.