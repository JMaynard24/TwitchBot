import time
import os
from random import randint
from Settings import CHAN


RPGSlotsTimer = {}


# -----------------------------------------------------------------------------


def chat(sock, channel, msg):
    """
    Send a chat message to the server.

    Keyword arguments:
    sock -- the socket over which to send the message
    msg  -- the message to be sent
    """
    if channel == '':
        channel = CHAN
    time.sleep(1)
    sock.send(("PRIVMSG " + channel + " :" + msg + "\n").encode("utf-8"))


# -----------------------------------------------------------------------------


def globalchat(sock, channel, msg):
    """
    Send a chat message to the server.

    Keyword arguments:
    sock -- the socket over which to send the message
    msg  -- the message to be sent
    """
    if channel == '':
        channel = CHAN
    sock.send(("PRIVMSG " + channel + " :" + msg + "\n").encode("utf-8"))


# -----------------------------------------------------------------------------


def ban(sock, user):
    """
    Ban a user from the current channel.

    Keyword arguments:
    sock -- the socket over which to send the ban command
    user -- the user to be banned
    """
    chat(sock, ".ban {}".format(user))


# -----------------------------------------------------------------------------


def timeout(sock, user, secs):
    """
    Time out a user for a set period of time.

    Keyword arguments:
    sock -- the socket over which to send the timeout command
    user -- the user to be timed out
    secs -- the length of the timeout in seconds (default 600)
    """
    chat(sock, ".timeout {}".format(user, secs))


# -----------------------------------------------------------------------------


def slotsTimer(character, s, channel, testmode):
    if character.money < 100:
        chat(s, channel, ("/w %s Sorry, you don't have enough ides to play!" % character.name))
    elif character.name in RPGSlotsTimer:
        if RPGSlotsTimer[character.name] + 300 > time.time() and testmode is False:
            slotTimerTimeleft = round((RPGSlotsTimer[character.name] + 300.0) - time.time())
            slotTimerminutes = round((slotTimerTimeleft / 60) - 0.5)
            slotTimerseconds = round(slotTimerTimeleft % 60)
            if slotTimerminutes > 0:
                chat(s, channel, ("/w %s You can only do slots every 5 minutes! (%s minute(s) and %s second(s) left!)" % (character.name, slotTimerminutes, slotTimerseconds)))
            else:
                chat(s, channel, ("/w %s You can only do slots every 5 minutes! (%s second(s) left!)" % (character.name, slotTimerseconds)))
        else:
            slots(character, s, channel)
    else:
        slots(character, s, channel)


def slots(character, s, channel):
            RPGSlotsTimer[character.name] = time.time()
            slot1 = randint(1, 7)
            slot2 = randint(1, 7)
            slot3 = randint(1, 7)
            slotseastereggs = randint(1, 1000)
            slotsfreeturn = randint(1, 10)
            if slotseastereggs == 1000:
                chat(s, channel, ("| % | # | $ |"))
                chat(s, channel, ("Huh? What does that mean?"))
                chat(s, channel, ("The machine spits out a ton of ides, I think it broke..."))
                chat(s, channel, ("%s takes the ides and runs!" % character.name))
                character.money += 200000
                character.save()
            else:
                chat(s, channel, ("| %s | %s | %s |" % (str(slot1), str(slot2), str(slot3))))
                if slot1 == 7 and slot2 == 7 and slot3 == 7:
                    chat(s, channel, ("Wow %s, You got the jackpot!!!" % character.name))
                    character.money += 50000
                    character.save()
                elif slot1 == 6 and slot2 == 6 and slot3 == 6:
                    ohnothiscouldbebad = randint(1, 3)
                    chat(s, channel, "The machine starts to rumble....")
                    chat(s, channel, "Next thing you know, the Devil himself shoots out of the coin slot!")
                    chat(s, channel, "He looks at you with evil eyes and pulls out a simple 1d3 die...")
                    chat(s, channel, "He rolls it across the nearest table...")
                    if ohnothiscouldbebad == 1:
                        chat(s, channel, "And he rolls a 1!")
                        chat(s, channel, "The Devil laughs like mad!")
                        chat(s, channel, "Your ides rushes out of your pockets into the air!")
                        chat(s, channel, "The Devil and your ides flow into the machine and you are left with nothing...")
                        character.money = 0
                        character.save()
                    elif ohnothiscouldbebad == 2:
                        chat(s, channel, "And he rolls a 2!")
                        chat(s, channel, "The Devil sighs before turning around and leaving....")
                    elif ohnothiscouldbebad == 3:
                        chat(s, channel, "And he rolls a 3!")
                        chat(s, channel, "The Devil slams his fist on the table right before getting pulled back into the machine")
                        chat(s, channel, "As the Devil is entering the machine you notice the numbers are changing....")
                        chat(s, channel, "7....... 7....... 7....... Wait, could it be???")
                        chat(s, channel, ("Wow %s, You got the jackpot!!!" % character.name))
                        character.money += 50000
                        character.save()
                elif slot1 == slot2 and slot1 == slot3:
                    chat(s, channel, ("Congratulations %s, You win!" % character.name))
                    character.money += 2000
                    character.save()
                elif slot1 + 1 == slot2 and slot2 + 1 == slot3:
                    chat(s, channel, ("Nice one %s, You got a sequence!" % character.name))
                    character.money += 500
                    character.save()
                elif slot1 - 1 == slot2 and slot2 - 1 == slot3:
                    chat(s, channel, ("Nice one %s, You got a sequence!" % character.name))
                    character.money += 500
                    character.save()
                elif slot1 == slot2 and slot1 != slot3:
                    chat(s, channel, ("So close %s, but you still lose!" % character.name))
                    if slotsfreeturn == 10:
                        chat(s, channel, "Lucky you! The machine spits your ides back out!")
                    else:
                        character.money -= 100
                        character.save()
                elif slot1 != slot2 and slot1 == slot3:
                    chat(s, channel, ("So close %s, but you still lose!" % character.name))
                    if slotsfreeturn == 10:
                        chat(s, channel, "Lucky you! The machine spits your ides back out!")
                    else:
                        character.money -= 100
                        character.save()
                elif slot2 == slot3 and slot1 != slot2:
                    chat(s, channel, ("So close %s, but you still lose!" % character.name))
                    if slotsfreeturn == 10:
                        chat(s, channel, "Lucky you! The machine spits your ides back out!")
                    else:
                        character.money -= 100
                        character.save()
                else:
                    chat(s, channel, ("Bad luck %s, You lose!" % character.name))
                    if slotsfreeturn == 10:
                        chat(s, channel, "Lucky you! The machine spits your ides back out!")
                    else:
                        character.money -= 100
                        character.save()


# -----------------------------------------------------------------------------


def vote(user, voteentry, voting):
    for i in voting.keys():
        if user in voting[i]:
            voting[i].remove(user)
            if len(voting[i]) == 0:
                del voting[i]
                break
    if voteentry not in voting:
        voting[voteentry] = []
    voting[voteentry].append(user)


# -----------------------------------------------------------------------------


def endVote(voting, s, channel, starter):
    chat(s, channel, "Vote is over!")
    highest = 0
    for i in voting.values():
        if len(i) > highest:
            highest = len(i)
    winners = []
    for i in voting.keys():
        if len(voting[i]) == highest:
            winners.append(i)
    if len(winners) == 1:
        chat(s, channel, "%s wins with %s vote(s)!" % (winners[0], highest))
    else:
        competitors = ""
        for i in range(len(winners)):
            if i < len(winners) - 1:
                competitors += winners[i] + ", "
            else:
                competitors += "and " + winners[i]
        chat(s, channel, "%s tie for the lead with %s vote(s)!" % (competitors, highest))
    chat(s, channel, "/w %s Vote Results:" % starter)
    for i in voting:
        chat(s, channel, '/w %s %s - %s - %s' % (starter, i, len(voting[i]), ', '.join(voting[i])))


# -----------------------------------------------------------------------------


def say(say, s, channel):
    if say[0] != "/" and say[0] != "." and say[0] != "!":
        chat(s, channel, say)
    elif say[0] == "/" or say[0] == "." or say[0] != "!":
        chat(s, channel, "Nice try bud")


# -----------------------------------------------------------------------------


def pyramid(say, s, channel):
    if say[0] != "/" and say[0] != "." and say[0] != "!":
        chat(s, channel, say)
        globalchat(s, channel, ((say + " ") * 2))
        globalchat(s, channel, ((say + " ") * 3))
        globalchat(s, channel, ((say + " ") * 2))
        globalchat(s, channel, say)
    elif say[0] == "/" or say[0] == "." or say[0] != "!":
        chat(s, channel, "Nice try bud")


# -----------------------------------------------------------------------------


def listedit(user, setting, files, s, channel, MAIN):
    if user == MAIN and setting == "del":
        chat(s, channel, "Not allowed to remove main account.")
    else:
        rlist = open("botfiles/%s.txt" % files, "r")
        newlist = open("botfiles/%s.temp.txt" % files, "w+")
        rlist.close()
        regs = rlist.readlines()
        user = user.lower()
        userAlreadyExists = False
        for i in regs:
            if i == user:
                userAlreadyExists = True
        if setting == "add":
            for i in regs:
                if i != '':
                    newlist.write(i + '\n')
            if userAlreadyExists is False:
                newlist.write(user + '\n')
                chat(s, channel, "Added %s to %s list!" % (user, files))
            else:
                chat(s, channel, "%s is already in %s list!" % (user, files))
        elif setting == "del":
            for i in regs:
                if i != '' and i != user:
                    newlist.write(i + '\n')
            if userAlreadyExists is False:
                chat(s, channel, "%s is not in %s list!" % (user, files))
            else:
                chat(s, channel, "Removed %s from %s list!" % (user, files))
        newlist.close()
        os.remove("botfiles/%s.txt" % files)
        os.rename("botfiles/%s.temp.txt" % files, "botfiles/%s.txt" % files)
        alist = open("botfiles/%s.txt" % files, "r+")
        alistread = alist.read().split(', ')
        alist.close()
        return set(alistread)


# -----------------------------------------------------------------------------
