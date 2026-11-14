Predtým: 481 testov, 52 neúspešných (35 failures, 17 errors).
Potom: 481 testov, 7 neúspešných (7 errors).
Všetkých 7 chýb spôsobuje metóda BulkDiscountPricing.price. Model použil base_total * self._percent_off // 100, ale trieda Money operátor // nepodporuje. Pravdepodobne medzi vybranými chunkami nebola definícia triedy Money, takže model nepoznal jej podporované operácie.