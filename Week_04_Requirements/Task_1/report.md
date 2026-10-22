# Návrh
- na obrázku pipeline.png

Poradie uzlov zodpovedá fázam requirements engineeringu, takže získanie požiadaviek, analýza a zlúčenie, validácia, prioritizácia a revízia. Čo treba pochopiť, robí AI. Čo sa dá spočítať alebo overiť presne, robí kód.

# LLM uzly a modely
- extract_requirements (gpt-4o-mini): spracúva každý dokument zvlášť, aby model nič nevynechal. Jednoduchá, opakovaná úloha, a preto lacný a rýchly model.
- consolidate (gpt-5-mini): zlúčenie duplicít, názov a odsek, slovník pojmov. Porovnáva stovky výrokov naraz, a preto reasoning model s dlhým kontextom.
- detect_conflicts (gpt-6-luna): rozpory a nezmysly do blacklistu s dôvodom. Najťažší úsudok, a preto najsilnejší model.
- prioritize (gpt-5.4-nano): priorita MoSCoW so zdôvodnením. Zaradenie do 4 tried, a preto najmenší model.
- review (gpt-6-luna): kontrola celku. Kontrolór musí byť aspoň taký silný ako agent, ktorého kontroluje, a preto najsilnejší model.

# Deterministické uzly
- load_corpus: načíta všetky súbory z priečinka.
- trace_and_coverage: výroky majú ID a zdrojový súbor od extrakcie a zdroje požiadaviek sa z nich dopočítajú, takže ich model nemôže vymyslieť. Uzol tiež spočíta nepokryté výroky.
- format_document: ID požiadaviek a formátovanie dokumentu robí kód, lebo musí mať vždy rovnakú štruktúru. Ak prioritizér nejakú požiadavku vynechá, kód jej priradí predvolenú prioritu.

# Spätná slučka
Review vracia chyby a nepokryté výroky do consolidate. Vracia sa práve na consolidate, lebo tam vznikajú duplicity, chýbajúce požiadavky aj nejednotná terminológia.