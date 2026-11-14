Embedding: lokálny model `all-MiniLM-L6-v2` (sentence-transformers), je zadarmo, beží bez API kľúča a je rýchly. Embeduje sa cesta k súboru, názov triedy, názvy funkcií/metód a samotný kód chunku, pretože názvy nesú veľa významu a zlepšujú zhodu s otázkou.
Uloženie: dvojice chunk–embedding sú v json. Každý objekt obsahuje pôvodný chunk s metadátami a jeho vektor. 
