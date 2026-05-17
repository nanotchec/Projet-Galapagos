# Code Review V1.93.1

V1.93.1 durcit la review post-seed avec un scan sémantique physique récursif.
Le validateur rejette désormais les champs interdits même si les checksums sont recalculés.
Le smoke test utilise un fast-path dédié pour éviter tout timeout.
