from random import randint
from math import ceil

print("""
Balance which stat?
[A] Status Resistance
[B] Hit Chance
[C] Damage Roll
[D] Crit Chance
[E] Crit Damage
[F] Active Guard
[G] Energy Recovery
[H] Experience Needed
[I] Drop Chance


[Q] Quit
Type ? to show this list again.""")
while True:
    com = input("\n>>> ").lower()
    if com == '?':
        print("""
Balance which stat?
[A] Status Resistance
[B] Hit Chance
[C] Damage Roll
[D] Crit Chance
[E] Crit Damage
[F] Active Guard
[G] Energy Recovery
[H] Experience Needed
[I] Drop Chance

[Q] Quit
Type ? to show this list again.""")
    elif com == 'q':
        exit()
    elif com == 'a':
        arg1 = int(input("\nStatus Chance: "))
        arg2 = int(input("Target Will: "))
        arg3 = 1 - (arg2 / 272)
        print("\nTarget's Resistance Modifier: ~{:.2f}".format(arg3))
        print("Modified Status Chance: ~{:.2f}".format(arg1 * arg3))
    elif com == 'b':
        arg1 = int(input("\nPlayer Speed: "))
        arg2 = int(input("Player Luck: "))
        arg3 = int(input("Enemy Speed: "))
        arg4 = int(input("Enemy Luck: "))
        arg5 = min(100, (arg1 / arg3) * 50 + 50 + (arg2 * 0.0392) - (arg4 * 0.0392))
        arg6 = min(100, (arg3 / arg1) * 50 + 50 + (arg4 * 0.0392) - (arg2 * 0.0392))
        arg5 = max(arg5, 0)
        arg6 = max(arg6, 0)
        print("\nPlayer Chance to Hit Enemy: ~{:.2f}".format(arg5))
        print("Enemy Chance to Hit Player: ~{:.2f}".format(arg6))
    elif com == 'c':
        arg1 = int(input("\nAttacker Power: "))
        arg2 = int(input("Attacker Charge Level (0-3): "))
        arg3 = int(input("Target Guard: "))
        if arg2 == 0:
            dmg = [ceil(arg1 / 5), arg1]
        elif arg2 == 1:
            dmg = [ceil(arg1 / 2), ceil(arg1 * 3 / 2)]
        elif arg2 == 2:
            dmg = [arg1, arg1 * 2]
        elif arg2 == 3:
            dmg = [ceil(arg1 * 3 / 2), ceil(arg1 * 5 / 2)]
        arg4 = min(1, (arg1 / arg3) * 0.5)
        print("\nAttacker Base Damage Roll: {} - {}".format(dmg[0], dmg[1]))
        print("Target Defense Modifier: ~{:.2f}".format(arg4))
        dmg[0] = ceil(dmg[0] * arg4)
        dmg[1] = ceil(dmg[1] * arg4)
        print("Modified Damage: {} - {}".format(dmg[0], dmg[1]))
    elif com == 'd':
        arg1 = int(input("\nAttacker Crit Chance: "))
        arg2 = int(input("Attacker Luck: "))
        arg3 = arg1 + arg2 * 0.075
        print("\nFinal Crit Chance: ~{:.2f}".format(arg3))
    elif com == 'e':
        arg1 = int(input("\nOriginal Damage: "))
        print("\nCritical Damage: {}".format(ceil(arg1 * 1.5)))
    elif com == 'f':
        arg1 = int(input("\nTarget Guard: "))
        arg2 = int(input("Incoming Damage: "))
        arg3 = (arg1 / 512) + 0.5
        arg4 = [ceil(ceil(arg2 * 3 / 4) * arg3 * arg3), ceil(arg2 * arg3)]
        print("\nTarget Guard Modifier: ~{:.2f}".format(arg3))
        print("Blocked Damage: {} - {}".format(arg4[0], arg4[1]))
        print("Final Damage: {} - {}".format(arg2 - arg4[1], arg2 - arg4[0]))
    elif com == 'g':
        arg1 = int(input("\nCharacter Speed: "))
        print("\nRecovery Per Encounter Update: {}".format(arg1 * 2 + 100))
    elif com == 'h':
        arg1 = int(input("\nPlayer Starting Level: "))
        arg2 = int(input("Player Ending Level: "))
        arg3 = (arg2 - 1) ** 2
        arg4 = arg2 ** 2
        arg5 = arg4 - arg3
        cumulative = 0
        for level in range(arg1, arg2):
            cumulative += level ** 2
        print("\nCumulative Exp: {:,}".format(cumulative))
        print("Exp To This Level: {:,}".format(arg3))
        print("Exp To Next Level: {:,}".format(arg4))
        print("Difference: {:,}".format(arg5))
    elif com == 'i':
        arg1 = int(input("\nDrop Chance: "))
        arg2 = int(input("Encounter Number: "))
        arg3 = int(input("Luck: "))
        newvalue = arg1 + (100 - arg1) * (0.01 * arg2) + (arg3 / 15)
        print("\nNew Drop Chance: {:,}".format(newvalue))
