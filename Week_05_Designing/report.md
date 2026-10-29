Práca si skillom bola podla mňa rýchlejšia a zároveň viac podľa predstáv. ADR vyzerá hneď na prvú oveľa lepšie ako bez skillu, je oveľa viac informatívny aj prehľadnejší. Všetko čo sa predtým upravovalo a pridávalo, tak podľa očakávania už obsahovalo, ako napiríklad diagram alebo tabuľku aby to bolo prehľadnejšie.


# Porovnanie coding asistentom

## Čo je v oboch dokumentoch spoločné

- Modulárny monolit sa vyberá pre jednoduchšiu lokálnu transakčnú konzistenciu pri zásobách, rezerváciách a objednávkach.
- Dôležité sú jasné hranice modulov a vlastníctvo ich dát.
- Externé platby a asynchrónne notifikácie nemožno považovať za súčasť jednej lokálnej databázovej transakcie.
- Opakovanie webhookov a asynchrónnych úloh vyžaduje idempotentné spracovanie.
- Mikroslužby prinášajú prevádzkovú a distribuovanú zložitosť, ktorá nie je pre MVP zatiaľ odôvodnená.
- Serverless môže byť relevantný pri premenlivej záťaži, no prináša cloudovú závislosť a vlastné prevádzkové kompromisy.

## Hlavné rozdiely a prínos verzie so skillom

1. **Presnejšie narába s neistotou.** Run 2 netvrdí, že tím, návštevnosť alebo hosting sú známe; označuje ich za nezadané alebo pracovné predpoklady. Vďaka tomu je odporúčanie primerane ohraničené.
2. **Lepšie prepája rozhodnutie s konkrétnym správaním systému.** Checkout, rezervácie, expirácie, webhooky a opakovanie požiadaviek sú vysvetlené ako procesy, nie iba ako všeobecné implementačné zásady.
3. **Zreteľnejšie odlišuje lokálnu a externú konzistenciu.** Upozorňuje, že timeout platobnej brány neznamená neúspešnú platbu a že stav treba overiť, nie slepo opakovať strhnutie.
4. **Zviditeľňuje rozhodnutia, ktoré ešte treba urobiť.** Napríklad nadväznosť prijatej rezervácie na checkout, lehotu držania zásoby, pravidlá refundácie či časové hranice expirácie.
5. **Zachováva formálny stav predchádzajúceho ADR.** Prvý dokument je prijatý; Run 2 je návrh a výslovne uvádza, že sám osebe nemení jeho schválenie.

