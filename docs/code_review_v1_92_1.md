# Code Review V1.92.1

V1.92.1 ajoute un scan semantique recursif des cinq JSON physiques du seed.
Les fichiers V1.84, V1.87 et V1.90 sont lus en lecture seule avec verification de hashes.
Le validateur refuse les champs de type target, label, prediction, information future, EV, MFE et MAE meme si les checksums sont recalcules.
Le systeme ne peut pas passer d'ordre reel.
