# Code Review V1.93.5

V1.93.5 élimine strictement tout usage de 'pass' dans les tests.
Le validateur AST inspecte désormais l'intégralité du fichier de test.
Les assertions tautologiques sont interdites même sous forme de comparaison complexe.
