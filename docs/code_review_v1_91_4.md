# Code Review V1.91.4

V1.91.4 implemente un fast-path pour le smoke test externe afin d'eviter les timeouts.
Le smoke test V1.91.4 n'execute pas pytest complet et ne scanne pas le ZIP exhaustivement.
Les controles de qualite de code interdisant 'True is not False' sont maintenus.
