# Regles pour agents de code

- Garder le code en anglais technique.
- Garder la documentation, les rapports et les explications utilisateur en francais.
- Ne pas casser la structure modulaire `src/galapagos`.
- Ne jamais melanger donnees reelles et mocks sans statut explicite.
- Ne pas ajouter d'execution reelle en V1.
- Toute methode future d'ordre reel doit lever `NotImplementedError` ou une exception explicite et
  etre couverte par test.
- Ajouter ou ajuster des tests pour toute modification importante.
- Produire un rapport francais apres toute grosse evolution.

