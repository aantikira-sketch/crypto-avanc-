import mlkem
from params import ML_KEM_768 as p

ek, dk = mlkem.keygen(p)
print(f"Clé publique ek : {len(ek)} octets, clé privée dk : {len(dk)} octets")

K, c = mlkem.encaps(ek, p)
print(f"Chiffré c : {len(c)} octets")
print("Clé d'Alice (Encaps) :", K.hex()[:32], "...")
K2 = mlkem.decaps(dk, c, p)
print("Clé de Bob (Decaps)  :", K2.hex()[:32], "...")
print("Identiques :", K == K2)

bad = bytes([c[0] ^ 1]) + c[1:]
K3 = mlkem.decaps(dk, bad, p)
print(f"Clé publique ek : {len(ek)} octets, clé privée dk : {len(dk)} octets")
print("Chiffré modifié : aucune erreur, Bob obtient", K3.hex()[:32], "...")
print("Différente de la vraie clé :", K3 != K)