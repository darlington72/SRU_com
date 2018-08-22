tableau = bytearray()
j = 0

while j < 1472:
    tableau.append(j % 256)
    j += 1

print(tableau.hex())

tableau2 = bytearray(j % 256 for j in range(1472))

print(tableau2)

if tableau == tableau2:
    print("oui")