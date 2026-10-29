---
name: architecture-decision-record
description: "Use when turning system requirements into architecture options, comparing materially different designs, recommending or selecting an architecture, and writing or reviewing an Architecture Decision Record (ADR)."
---

# Návrh architektúry a ADR

Použi tento postup na návrh architektúry pre ľubovoľný systém — nový alebo existujúci, softvérový alebo distribuovaný. Výsledkom má byť rozhodnutie vysledovateľné k požiadavkám, férové porovnanie reálnych možností a ADR, ktoré vysvetľuje aj dôsledky a hranice rozhodnutia. Príklady technológií vyberaj podľa kontextu; nevnášaj do návrhu doménu E-Farmers ani jej konkrétne predpoklady.

## Postup

### 1. Zisti kontext a rozhodovací rozsah

- Prečítaj dostupné požiadavky, zadanie, existujúcu dokumentáciu a relevantnú časť systému. Pri zmene existujúcej architektúry zisti aktuálne hranice a obmedzenia; nenavrhuj nový systém bez zohľadnenia fungujúceho stavu.
- Stručne vymedz problém a rozhodnutie, ktoré treba urobiť, dotknutých aktérov a čo je mimo rozsahu.
- Oddeľ:
  - funkčné požiadavky a hlavné používateľské toky;
  - kvalitatívne požiadavky, ako sú bezpečnosť, dostupnosť, latencia, konzistencia, obnoviteľnosť, škálovanie a auditovateľnosť;
  - obmedzenia (rozpočet, tím, technológie, hosting, regulácie, termín);
  - predpoklady a neznáme skutočnosti.
- Zoraď najdôležitejšie kvalitatívne požiadavky. Ak sú potrebné merateľné ciele, vyžiadaj si ich alebo ich označ ako otvorené predpoklady; nevymýšľaj SLO či kapacitu.
- Ak nejasnosť mení vhodný variant alebo rozhodnutie a nemožno ju bezpečne označiť ako predpoklad, polož cielenú otázku pred výberom. Inak pokračuj s explicitným predpokladom a uveď, ako ovplyvňuje záver.

### 2. Odvoď architektonické ovládače a invarianty

Prepoj požiadavky s dôsledkami návrhu. Zaznamenaj kľúčové entity a ich životný cyklus, vlastníkov dát, hranice dôvery, externé závislosti, synchronné a asynchrónne toky, objem/špičky a kritické režimy zlyhania.

Pre každý dôležitý invariant urč:

- kde je autoritatívny zdroj pravdy a ktorý komponent ho vynucuje;
- ktoré operácie musia byť atómové a v akej hranici;
- ktoré prechody stavov sú povolené a kto ich môže vykonať;
- čo sa stane pri súbehu, opakovaní, oneskorení, timeoute, čiastočnom zlyhaní alebo obnove.

Rozlíš obchodné pojmy a časové limity, ktoré sa môžu podobať, ale majú odlišný význam alebo účinok. Napríklad platnosť produktu, lehota na rozhodnutie a lehota platby nie sú jedna expirácia. Pre každý pojem používaj samostatný názov, autoritatívny časový zdroj a pravidlo pre hraničný okamih.

### 3. Navrhni skutočne odlišné alternatívy

- Predstav zvyčajne 2–3 uskutočniteľné alternatívy, ktoré sa líšia podstatnou architektonickou voľbou (napr. hranice nasadenia/vlastníctva dát, spôsob behu alebo model komunikácie), nie iba názvom produktu.
- Zahrň aj jednoduchšiu alternatívu a odôvodni, prečo je primeraná alebo nedostatočná. Nepridávaj variant len na dosiahnutie počtu; ak existujú iba dve obhájiteľné možnosti, vysvetli to.
- Každý variant opíš na rovnakej úrovni: komponenty a zodpovednosti, hranice dát, komunikácia, nasadenie a prevádzka, kľúčové toky a relevantné kvalitatívne vlastnosti.
- Pri každom variante ukáž aspoň jeden kritický tok vrátane zlyhania alebo obnovy, ak sú pre rozhodnutie dôležité. Odlišuj lokálnu transakčnú konzistenciu od konzistencie naprieč službami či externými systémami. Nepredpokladaj ACID transakciu cez nezávislé databázy alebo externého poskytovateľa.
- Uveď výhody, nevýhody, prevádzkové a migračné náklady, riziká, závislosti a predpoklady. Porovnávaj reálne dôsledky pre tento systém, nie všeobecné slogany.

### 4. Porovnaj a vyber

Vytvor súhrnnú tabuľku variantov podľa kritérií relevantných pre rozhodnutie. Podľa kontextu zváž najmä:

- splnenie prioritných kvalitatívnych požiadaviek a konzistenciu;
- zložitosť vývoja, prevádzky a lokálneho vývoja;
- škálovanie a izoláciu porúch;
- nezávislosť nasadzovania a vhodnosť pre veľkosť/štruktúru tímu;
- náklady a ich predvídateľnosť;
- závislosť od poskytovateľa a náročnosť migrácie.

Opíš, z akých predpokladov hodnotenie vychádza. Nepoužívaj falošnú presnosť ani skóre bez vysvetlenej metódy. Pre každú zamietnutú alternatívu vyvážene pomenuj, v čom je lepšia než zvolená možnosť a prečo jej výhody v danom kontexte neprevažujú. Nevykresľuj odmietnutý variant ako chybný; uveď, za akých podmienok by bol vhodnejší.

Odporúčanie alebo vybranú možnosť zdôvodni priamo prioritnými požiadavkami, obmedzeniami a dôkazmi z kontextu. Pomenuj kompromisy, ktoré výber vedome prijíma, zostávajúce riziká a opatrenia. Rozlíš rozhodnutie prijaté používateľom od odporúčania asistenta; nevydávaj návrh za schválené rozhodnutie.

### 5. Vytvor ADR

Dodrž existujúci formát a umiestnenie v projekte. Ak vzor alebo konvencia chýba, použi stručnú štruktúru nižšie. Zachovaj existujúce ADR a ich číslovanie; neprepisuj nesúvisiace rozhodnutia. Ak cieľové umiestnenie nie je z kontextu zrejmé a záleží na ňom, opýtaj sa.

1. **Názov a metadáta** — jednoznačný názov, identifikátor podľa konvencie, stav (navrhnuté/prijaté/zamietnuté/nahradené), dátum.
2. **Kontext** — problém, aktéri a relevantné funkčné požiadavky, kvalitatívne ovládače, obmedzenia, predpoklady a hranice rozsahu.
3. **Rozhodnutie** — čo sa vyberá a prečo práve teraz.
4. **Zvolená architektúra** — komponenty a zodpovednosti, hranice modulov/služieb a vlastníctvo dát, rozhrania, dátové úložiská, externé systémy, nasadzovanie a prevádzka podľa potreby.
5. **Diagram** — ak pomáha vysvetleniu, pridaj jednoduchý Mermaid diagram. Označ hranice, smer a typ komunikácie, externé systémy a zdroje pravdy. Diagram musí súhlasiť s textom a nesmie naznačovať neexistujúcu transakčnú alebo bezpečnostnú garanciu.
6. **Kritické toky a pravidlá** — opíš reprezentatívne toky a dôležité invarianty vrátane autorizácie, konzistencie, idempotencie, timeoutov, retry, kompenzácie či obnovy, ak sú relevantné.
7. **Zvažované alternatívy** — pri každej zamietnutej možnosti použi vyvážené porovnanie: „V čom je lepšia než zvolená možnosť“ a „Prečo ju teraz nevyberáme“. Pridaj súhrnnú porovnávaciu tabuľku; nevkladaj do nej neporovnateľné predpoklady.
8. **Dôsledky** — pozitívne aj negatívne, vrátane zložitosti, nákladov, prevádzkových povinností a obmedzení, ktoré rozhodnutie vytvára.
9. **Riziká, otvorené otázky a budúce rozhodnutia** — zaznamenaj neistoty a vlastníka/následný krok, ak je známy.
10. **Spúšťače na prehodnotenie** — uveď pozorovateľné signály, pri ktorých sa rozhodnutie znovu otvorí (napr. opakované merateľné problémy s výkonom, nákladmi, releasmi alebo spoľahlivosťou). Kde je užitočné, uveď prvý kandidát na zmenu a bezpečný migračný smer; samotný hypotetický rast nestačí ako spúšťač.

ADR má vysvetliť prečo, nielen čo. Nezamieňaj požiadavky s implementačnými návrhmi. Konkrétnu technológiu pomenuj iba vtedy, keď je daná obmedzením alebo zdôvodneným rozhodnutím; inak uprednostni prenositeľný opis a označ príklady ako príklady.

## Kontrola správnosti pred odovzdaním

- Každá prioritná požiadavka a invariant má zodpovedajúce architektonické riešenie alebo otvorenú otázku.
- Alternatívy sú uskutočniteľné, podstatne odlišné a hodnotené podľa rovnakých relevantných kritérií; výhody zamietnutých možností sú uvedené férovo.
- Text rozlišuje zdroj pravdy, vlastníctvo dát, hranice transakcií a konzistenciu. Pri async spracovaní počíta s opakovaním a duplicitami; pri distribuovaných hraniciach opisuje potrebnú koordináciu a kompenzácie.
- Bezpečnostné a dôveryhodnostné hranice sú explicitné: autorizácia sa vynucuje na serveri, klient ani návratová URL nie sú autoritatívnym dôkazom a citlivé údaje sa neposúvajú do nevhodných logov alebo úložísk.
- Stavové prechody, časové limity, súbeh a čiastočné zlyhania nie sú ponechané na nejednoznačné „neskôr sa to spracuje“. Rozlišuj dočasné a trvalé zlyhanie; bezpečné opakovanie nesmie vytvoriť dvojitý účinok.
- Diagram, tabuľky a text hovoria to isté. Predpoklady, neznáme údaje a odporúčania sú jasne označené; nevytváraj nepodložené čísla ani garancie.
- Záver určuje stav rozhodnutia a konkrétne signály pre jeho budúce prehodnotenie.

Po vytvorení ADR skontroluj zmenený dokument a podľa možností projektu spusti príslušnú kontrolu Markdownu. V odpovedi stručne uveď zvolený variant, hlavné dôvody a kompromisy, cestu k ADR a nevyriešené otázky; neprezentuj neoverené predpoklady ako fakty.
