# Poznámky z diskusie – E-Farmers

Dátum: 2026-10-28

- V ADR zapíšeme rozhodnutie, dôvody a kompromisy, aby sa v budúcnosti dal návrh rozšíriť bez toho, aby sa narušila konzistencia a bezpečnosť.
- Pripomienka k ADR: nezamieňať expiráciu boxu s expiráciou rezervácie. Story 11 sa týka dostupných boxov blízko dátumu spotreby (`food_expires_at`); lehota na rozhodnutie farmára o rezervácii je samostatná (`decision_deadline`). ADR bolo podľa tohto rozlíšenia opravené.
- Ďalšia pripomienka k ADR: zamietnutie alternatív má byť vyvážené. Doplnili sme výhody B oproti A (nezávislé nasadzovanie/škálovanie, vlastníctvo dát, izolácia porúch a autonómia tímov) a C oproti A (spravovaný runtime, automatické škálovanie, platba podľa využitia a managed workflow/fronty), spolu s dôvodmi, prečo tieto výhody pre MVP neprevažujú.
- Na želanie používateľa sú alternatívy B a C v ADR prehľadnejšie: pri každej je zoznam porovnávacích argumentov nahradený dvojstĺpcovou tabuľkou „V čom je lepšia než A“ a „Prečo ju teraz nevyberáme“.
- Používateľ požiadal o súhrnnú porovnávaciu tabuľku A/B/C podľa konzistencie, prevádzkovej zložitosti, škálovania, nasadenia, lokálneho vývoja, nákladov, vendor lock-in a vhodnosti pre malý tím. Tabuľka bola vložená do ADR; pri C je výslovne uvedený predpoklad spoločnej relačnej DB pre lokálnu konzistenciu.
- Na žiadosť používateľa bol do ADR doplnený jednoduchý Mermaid diagram zvoleného modulárneho monolitu. Zobrazuje backendové moduly, PostgreSQL a outbox, workera a externé systémy: platobnú bránu, OAuth providera, e-mail providera a objektové úložisko.
- Do sekcie „Budúce rozhodnutia“ v ADR boli doplnené spúšťače prehodnotenia: notifikačný fan-out zhoršuje výkon hlavnej DB, tímy sa opakovane blokujú pri releasoch a škálovanie celého backendu je neprimerané. Ako prvý kandidát na vyčlenenie je určený modul `Subscriptions/Notifications`, po potvrdení potreby a s outbox/udalosťami.
