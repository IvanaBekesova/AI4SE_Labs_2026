# E-Farmers — architektonické poznámky (Run 2)

## Priebežný záznam: kontext a rozsah

- Zdroj požiadaviek: `Tasks/data/EFarmers.txt`; cieľom je e-commerce platforma prepájajúca farmárov, zákazníkov a kuriérov.
- Funkčný rozsah zahŕňa účty (e-mail/OAuth), roly zákazník/farmár/kuriér, profily a ponuky, kalendár a rezervácie boxov, vyhľadávanie, košík/objednávky/platby, doručenie, odbery a notifikácie, recenzie a odznaky.
- Zvlášť citlivé toky: súbežné rezervovanie posledného boxu, farmárom prijímané alebo odmietané rezervácie, checkout a externé platby, doručenie a opakované webhooky.
- Požiadavky nešpecifikujú návštevnosť, objem dát, dostupnosť/latenciu, hosting, rozpočet, zloženie tímu ani platobného/identitného poskytovateľa. Tieto údaje ostávajú otvorené; nebudú sa z nich odvodzovať vymyslené kapacitné ciele.
- Existujúci `adr.md` už zaznamenáva prijatý modulárny monolit. Tento súbor je samostatný návrhový záznam: nemení ani nenahrádza jeho stav.

Priebežný stav: kontext a invarianty sú zaznamenané; nižšie sú tri alternatívy, porovnanie a pracovné odporúčanie.

## Ovládače, predpoklady a invarianty

### Priorita podľa dostupných požiadaviek

1. **Správnosť zásob, rezervácií a objednávok:** dostupný počet boxov nesmie klesnúť pod nulu; súbežné požiadavky nesmú predať ten istý box dvakrát.
2. **Bezpečná platba a jednoznačný stav:** platobná brána je externá hranica; úspech ani návrat používateľa do aplikácie nie sú dôkazom zaplatenia.
3. **Serverová autorizácia:** roly a vlastníctvo ponuky/objednávky sa overujú pri každej operácii na serveri, nie iba skrytím ovládacích prvkov v UI.
4. **Odolné asynchrónne spracovanie:** notifikácie, expirácie a webhooky sa môžu oneskoriť, opakovať alebo zlyhať.
5. **Primeraná jednoduchosť MVP:** požiadavky nepreukazujú potrebu samostatného škálovania služieb, viacerých tímov ani konkrétneho cloudu.

Merateľné ciele dostupnosti, latencie, objemu, obnovy po havárii a rozpočtu nie sú zadané. Pred návrhom produkčných kapacít treba ich zistiť.

### Predpoklady a hranice

- Predpoklad: MVP prevádzkuje jeden produktový tím; ide o východiskový predpoklad, nie fakt zo zdroja.
- Predpoklad: relačná databáza je vhodná pre účty, ponuky, zásoby, rezervácie a objednávky; konkrétny produkt je otvorená voľba.
- Platobná brána, OAuth, e-mail/push a prípadne objektové úložisko sú externé závislosti.
- V rozsahu je návrh aplikácie a jej kritických backendových tokov. Výber konkrétneho cloudu, technológie, cieľov SLO, právne/regulačné posúdenie platieb a presné pravidlá doručenia nie sú špecifikované.
- Klient je nedôveryhodný; citlivé platobné údaje nemajú prechádzať ani sa ukladať v aplikácii, ak to poskytovateľ umožňuje.

### Doménové pravidlá, ktoré musia platiť vo všetkých variantoch

- Zdroj pravdy pre používateľov/roly, ponuky/boxy, rezervácie, objednávky a ich stavy je serverová databáza príslušnej domény. Pri variantovi s mikroslužbami je každý takýto zdroj pravdy lokálny konkrétnej službe.
- Vytvorenie rezervácie kontroluje dostupnosť a `food_expires_at` a atómovo vytvorí hold/rezerváciu a zníži dostupnosť alebo zapíše ekvivalentnú alokáciu. Použije sa transakcia s podmienenou aktualizáciou alebo zamykaním; súbeh neprejde, ak už zásoba nie je dostupná.
- `food_expires_at` (koniec použiteľnosti produktu) je odlišné od `decision_deadline` (lehota, dokedy farmár rozhodne o rezervácii). Prvý čas blokuje ponúkanie/rezervovanie po expirácii jedla; druhý po vypršaní uvoľní hold podľa stavového automatu. Hraničné pravidlá a časová zóna musia byť výslovne definované.
- Rezervácia má povolené prechody napr. `PENDING -> ACCEPTED | DECLINED | EXPIRED`; o prijatí/odmietnutí rozhoduje oprávnený farmár, expiruje ju serverový proces. Opakovaná alebo oneskorená požiadavka nemení terminálny stav ani nealokuje zásobu druhýkrát.
- Rezervácia z kalendára, ktorú musí farmár prijať/odmietnuť, nie je totožná s nákupnou objednávkou. Požiadavky neurčujú, či prijatá rezervácia následne vytvára objednávku/platbu; tento handoff a jeho lehota ostávajú otvoreným obchodným pravidlom.
- Košík nie je potvrdená objednávka. Pri checkout sa na serveri znovu overia cena, dostupnosť, expirácia a oprávnenie; objednávka uchová cenový/produktový snapshot.
- Platba je samostatný stavový tok: odoslanie požiadavky používa idempotency key, webhook sa autentifikuje podľa mechanizmu poskytovateľa, deduplikuje a stav sa zosúladí s poskytovateľom. Timeout znamená „výsledok neznámy“, nie automaticky neúspech; pred opakovaním sa najprv zisťuje stav. Žiadna transakcia nepredstiera ACID cez databázu a bránu.
- Každý async účinok je opakovateľný/idempotentný; dočasné chyby sa retryujú s limitom a odkladom, trvalé chyby sa dajú dohľadať a riešiť. Outbox (ak sa publikuje udalosť) sa zapisuje v rovnakej lokálnej transakcii ako doménová zmena.
- Doručenie aktualizuje len oprávnený kuriér priradený k objednávke; zmena stavu je auditovateľná. Presné stavy, priradenie kuriéra a pravidlá kompenzácie ostávajú otvorené doménové rozhodnutia.

## Tri architektonické alternatívy

Všetky varianty pokrývajú tie isté story: webové UI a API, identity/profily a roly, ponuky/zásoby, kalendár/rezervácie, košík/objednávky/platby, doručenie, odbery/notifikácie a recenzie/odznaky. Názvy komponentov sú logické hranice, nie záväzok ku konkrétnym technológiám.

### A — Modulárny monolit s asynchrónnym workerom

- **Komponenty a dáta:** jeden backend rozdelený na moduly s explicitným vlastníctvom (Identity/Profiles, Listings/Inventory, Calendar/Bookings, Cart/Orders, Payments, Delivery, Subscriptions/Notifications, Reviews/Badges); jedna relačná databáza, objektové úložisko médií, outbox a worker.
- **Komunikácia/nasadenie:** web volá serverové REST API; moduly volajú doménové rozhrania v procese. Backend a worker možno nasadiť spolu alebo ako dva procesy z rovnakého kódu. OAuth, platby a notifikační poskytovatelia sú za adaptérmi.
- **Kritický tok:** rezervácia z kalendára vytvorí žiadosť a hold v transakcii; farmár ju prijme/odmietne alebo worker ju po `decision_deadline` ukončí a uvoľní hold. Samostatný checkout opätovne overí zásobu a vytvorí objednávku v databázovej transakcii. Platobná požiadavka sa odošle až po commite; idempotency key bráni duplicitnej platbe. Overený webhook aktualizuje stav idempotentne. Pri výpadku platobného poskytovateľa zostáva objednávka v stave „platba čaká/neznámy výsledok“; worker alebo pravidelná reconciliácia zistí výsledok. Outbox worker doručí notifikáciu opakovane bez opakovania obchodnej zmeny.
- **Výhody:** jednoduchá lokálna konzistencia zásob a objednávok, jeden vývojový/deployovací model, nízka prevádzková záťaž, jednoduché testovanie a ladenie.
- **Nevýhody/riziká:** backend sa prevažne škáluje ako celok; hranice modulov treba vynucovať disciplínou/kontrolami; jedna databáza je spoločný prevádzkový bod a potenciálny limit.
- **Náklady/migrácia:** najnižšie počiatočné infra náklady pri jednom tíme; neskoršie vyčlenenie modulu vyžaduje najprv odstrániť priame zdieľanie tabuliek a zaviesť kontrakt/eventy.

### B — Doménové mikroslužby s udalosťami a databázou na službu

- **Komponenty a dáta:** samostatne vlastnené Identity, Marketplace/Inventory, Booking, Orders/Payments, Delivery a Engagement (subscriptions/notifications) služby; každá vlastní svoje úložisko a API. Broker prenáša doménové udalosti; každá služba má outbox/inbox alebo rovnocennú deduplikáciu.
- **Komunikácia/nasadenie:** synchronné API len pre rozhodnutia potrebné v odpovedi; asynchrónne udalosti pre projekcie, notifikácie a koordináciu. Služby aj ich schémy sa nasadzujú nezávisle, s kompatibilitou verzií kontraktov.
- **Kritický tok:** Booking/Inventory je jediným vlastníkom dostupnej zásoby a atómovo vytvára žiadosť o rezerváciu/hold s `decision_deadline`; farmársky príkaz `accept/decline` a expirácia sú idempotentné prechody v tej istej službe. Samostatný checkout požiada Booking o idempotentný hold a potom Orders vytvorí objednávku a spustí platbu. Odpovede a udalosti môžu prísť duplicitne alebo v inom poradí, preto každý krok má identifikátor a povolené prechody. Ak sa vytvorenie objednávky alebo platba trvalo nepodarí, saga uvoľní checkout hold; ak je výsledok platby neznámy, hold sa neuvoľní, kým sa výsledok neoverí alebo neuplynie definované obchodné pravidlo. Ide o eventual consistency a kompenzácie, nie jednu distribuovanú transakciu.
- **Výhody:** nezávislé nasadzovanie a škálovanie (napr. vyhľadávanie či notifikácie), lepšia izolácia niektorých porúch, explicitné vlastníctvo dát a vhodnosť pre viac autonómnych tímov.
- **Nevýhody/riziká:** vyššie nároky na operácie a lokálny vývoj; broker, tracing, kontrakty, retry, dead-letter/dohľad a ságové procesy; používateľ môže krátko vidieť zastaraný stav. Rozdelenie booking/order hranice zvyšuje náročnosť kritického toku.
- **Náklady/migrácia:** vyššie fixné náklady na platformu, observabilitu a podporu viacerých služieb; zmysel nadobúda pri preukázanom nezávislom škálovaní, autonómii tímov alebo izolácii. Bezpečnejšia migrácia je najprv modulárny monolit s outboxom a až potom vyčlenenie jednej domény.

### C — Serverless/event-driven aplikácia na spravovaných cloudových službách

- **Komponenty a dáta:** API gateway a funkcie pre doménové príkazy/čítania; spravovaná relačná databáza je zdrojom pravdy pre transakčné jadro (zásoba, rezervácia, objednávka); managed fronty/event bus a plánovač spúšťajú notifikácie, expirácie a reconciliáciu; workflow koordinuje dlhšie checkout/platobné kroky. Objektové úložisko drží médiá.
- **Komunikácia/nasadenie:** synchronné HTTP pre používateľské operácie, udalosti/fronty a workflow pre asynchrónne kroky. Funkcie a cloudové zdroje sa nasadzujú ako IaC. Predpokladá sa spoločná relačná transakčná hranica pre inventory/booking/order kritickú zmenu; nie je to ACID naprieč workflow ani platobnou bránou.
- **Kritický tok:** kalendárová žiadosť o rezerváciu a hold sa zapíšu v transakcii; serverová funkcia oprávnenej farmárskej akcie alebo plánovaná úloha pre `decision_deadline` vykoná podmienený prechod stavu a uvoľní hold najviac raz. Samostatná checkout funkcia overí a zarezervuje zásobu v DB transakcii a uloží outbox/identifikátor workflow. Workflow zavolá platobnú bránu s idempotency key; callback/webhook prejde serverovým overením a deduplikáciou. Pri timeout-e workflow označí výsledok ako neznámy a vykoná bezpečný status check/reconciliation, nie slepé druhé strhnutie.
- **Výhody:** poskytovateľ spravuje runtime a škálovanie; funkcie/fronty/workflow môžu dobre obslúžiť premenlivú alebo nepravidelnú záťaž a odbremeniť tím od prevádzky serverov.
- **Nevýhody/riziká:** väzba na cloudové API/IAM/workflow, limity a cold starts; lokálna emulácia nemusí zodpovedať produkcii; nárazové súbežné funkcie môžu preťažiť databázové spojenia; náklady môžu byť ťažšie predvídateľné. Spravované služby neodstraňujú idempotenciu, stavové automaty ani zodpovednosť za obnovu.
- **Náklady/migrácia:** málo správy serverov, ale významná konfigurácia, cloudová observabilita a testovacie prostredia; výhodnosť závisí od skutočnej variability záťaže, cien poskytovateľa a znalostí tímu. Odchod vyžaduje nahradiť workflow/fronty/IAM a upraviť deployment.

## Porovnanie a pracovné odporúčanie

Hodnotenie je kvalitatívne, na základe uvedených user stories a predpokladu malého tímu/MVP. Nie je to meranie ani prísľub výkonu.

| Kritérium | A — Modulárny monolit | B — Mikroslužby | C — Serverless |
|---|---|---|---|
| Zásoba/rezervácia/objednávka | Najjednoduchšia transakcia v jednej DB | Lokálna silná konzistencia iba v jednej službe; koordinácia medzi Booking a Orders je eventual | Možná silná transakcia v spoločnej DB; async workflow mimo transakcie |
| Externá platba | Asynchrónna, idempotentná integrácia | Asynchrónna; saga a kompenzácie medzi službami | Asynchrónna; workflow plus reconciliácia |
| Prevádzka a lokálny vývoj | Najjednoduchšie | Najnáročnejšie | Stredná; runtime spravuje cloud, emulácia/IaC komplikuje vývoj |
| Izolácia a nezávislé škálovanie | Obmedzené, prevažne celý backend | Najlepšia izolácia a nezávislé škálovanie | Dobré škálovanie funkcií, ale DB a kvóty môžu byť zdieľaným limitom |
| Release a tím | Jeden koordinovaný release; vyhovuje jednému tímu | Nezávislé releasy za cenu kontraktov a koordinácie platforiem | Funkcie/zdroje môžu ísť samostatne; zmeny cloudovej infra treba koordinovať |
| Náklady a prenositeľnosť | Zvyčajne predvídateľnejšie; nízky až stredný lock-in | Vyššie fixné náklady; stredný lock-in podľa brokera/hostingu | Platba podľa využitia môže byť výhodná pri variabilite, no silnejší lock-in a neistota nákladov |
| Kedy je vhodnejší | MVP, jeden tím, nepreukázaná potreba nezávislého škálovania | Viac autonómnych tímov alebo preukázané doménové škálovanie/izolácia | Malá prevádzková kapacita tímu, cloudové skúsenosti a skutočne premenlivá záťaž |

**Pracovné odporúčanie:** A — modulárny monolit s outboxom a workerom. Najlepšie zodpovedá kritickým transakciám a absencii dôkazov o viacerých tímoch, veľkej prevádzke či požiadavke na konkrétny cloud. B je lepší pre nezávislé domény a tímy, no jeho eventual consistency a prevádzková cena sú pre nepreukázané potreby predčasné. C je lepší pri kolísavej záťaži a obmedzenej správe runtime, ak tím ovláda zvolený cloud; bez týchto podmienok cloudové workflow a lock-in neprevažujú.

Toto odporúčanie **nie je nové schválené rozhodnutie**: existujúci `adr.md` má stav „Prijaté“ pre modulárny monolit. Zámerne nevytváram ani neupravujem ADR, keďže požiadavka je zapisovať návrh do `run2/notes.md` a výslovne chráni existujúce `adr.md`.

## Dôsledky, otvorené otázky a spúšťače na prehodnotenie

- A vyžaduje hranice modulov a vlastníctvo tabuliek; spoločná databáza nie je dôvod na priame obchádzanie doménových rozhraní.
- Treba rozhodnúť: pravidlá a lehoty rezervácie; či košík drží zásobu alebo iba checkout; platobný flow/refundy; výber a priradenie kuriéra; auditné a súkromnostné požiadavky; SLO, RPO/RTO, kapacita, hosting, rozpočet a zodpovednosti tímu.
- Ďalšie rozhodnutie má určiť časovú zónu a hraničnú sémantiku expirácií, retenčné pravidlá, životný cyklus nevybavenej platby a ako sa rieši spor medzi webhookom a reconciliation výsledkom.
- A znovu posúdiť, ak merania opakovane preukážu, že notifikačný fan-out zhoršuje objednávkové/rezervačné transakcie aj po optimalizácii, nezávislé tímy sa opakovane blokujú pri releasoch, alebo škálovanie celého backendu spôsobuje preukázané náklady či poruchy. Prvým kandidátom na vyčlenenie je notifikačný/odberový modul, až po zavedení stabilného kontraktu a outboxu.
- C znovu posúdiť pri preukázanej nepravidelnej záťaži alebo nízkej kapacite na správu runtime, po porovnaní celkových cien a prijatí cloudovej závislosti. Samotný hypotetický budúci rast nie je spúšťač.
- B znovu posúdiť pri skutočnom raste autonómnych doménových tímov alebo nameranom zaťažení/poruche, ktorú nemožno rozumne riešiť v A. Migračný smer: najprv vynútiť hranice modulov, potom vyčleniť jednu doménu s explicitným vlastníctvom dát a idempotentnými udalosťami.
