import re
import socket
from os.path import isfile
import time
import threading
from RPG import startRPG, checkExistence, raidlobby, pvplobby, PLAYER
from Commands import chat, slotsTimer, vote, endVote, say, pyramid, listedit
from Settings import NICK, MAIN, PASS, CHAN, HOST, PORT
from MathUtility import is_number

# -----------------------------------------------------------------------------

s = socket.socket()
s.connect((HOST, PORT))
s.send("PASS {}\r\n".format(PASS).encode("utf-8"))
s.send("NICK {}\r\n".format(NICK).encode("utf-8"))
s.send("JOIN {}\r\n".format(CHAN).encode("utf-8"))
s.send("CAP REQ :twitch.tv/commands\r\n".encode("utf-8"))
CHAT_MSG = re.compile(r"^:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :")
WHISPER_MSG = re.compile(r"^:\w+!\w+@\w+\.tmi\.twitch\.tv WHISPER \w+ :")

# Initializing some varaibles
votelisten = 0
voting = {}
lastmessage = ''
starter = ''
startignore = False
cartcount = 0
RPGTestMode = True
MainLoop = True

alist = open("botfiles/admins.txt", "r+")
alistread = alist.readlines()
admin = []
for i in alistread:
    i = i.strip("\n")
    admin.append(i)
alist.close()
print("Admins: %s\n" % ', '.join(admin))

alist = open("botfiles/regulars.txt", "r+")
alistread = alist.readlines()
reglist = []
for i in alistread:
    i = i.strip("\n")
    reglist.append(i)
alist.close()
print("Regulars: %s\n" % ', '.join(reglist))

# -----------------------------------------------------------------------------


def handleCommands(username, message, whisper, message2, whisper2, s, channel):
    global MainLoop
    global RPGTestMode
    global startignore
    global votelisten
    global cartcount
    global voting
    global starter
    global admin
    global reglist
    if username != NICK:
        if len(whisper2) > len(message2):
            print("MESSAGE " + (time.strftime("%a, %d %b %Y %H:%M:%S | ", time.localtime())) + channel + ' - ' + username + ": " + message)
        elif whisper2.find(":tmi.twitch.tv USERSTATE") >= 0 or whisper2.find(":tmi.twitch.tv HOSTTARGET") >= 0 or whisper2.find(":tmi.twitch.tv NOTICE") >= 0:
            pass
        else:
            print("WHISPER " + (time.strftime("%a, %d %b %Y %H:%M:%S | ", time.localtime())) + username + ": " + whisper)
    elif username == NICK:
        return
    if startignore is True:
        if message == '!stopignore':
            startignore = False
            chat(s, channel, "Okay, taking commands again!")
    elif startignore is False:
        if isfile('RPG/Players/%s.txt' % username):
            if channel != '':
                PLAYER[username].lastchannel = channel
            PLAYER[username].lastmessage = message
            PLAYER[username].lastwhisper = whisper
        if message == '!commands':
            chat(s, channel, "Commands are: !cart, !slots, !playRPG, !stats, !money, !encounter")
        elif (message[:6] == '!vote ' or whisper[:6] == '!vote ') and votelisten == 1:
            if len(whisper) < len(message):
                message = whisper
                if username in PLAYER:
                    channel = PLAYER[username].lastchannel
            voteentry = message[6:].lower()
            t = threading.Thread(target=vote, args=(username, voteentry, voting,))
            t.start()
        elif message == '!cart' or message == '!deathcount' or message == '!death':
            cartcount += 1
            chat(s, channel, ("Streamer has died %s time(s)" % str(cartcount)))
        elif whisper[:9] == '!examine ' or whisper == '!shop' or whisper[:5] == '!use ' or \
                whisper == '!travel' or whisper == '!location' or whisper == '!loc' or \
                message[:5] == '!lbs ' or whisper == '!commands' or whisper[:8] == '!travel ' or \
                whisper == '!surroundings' or whisper == '!stats' or whisper == '!inv' or \
                whisper[:9] == '!discard ' or whisper[:7] == '!equip ' or whisper[:11] == '!encounter' or \
                whisper == '!encounter boss' or whisper == '!trainer' or whisper[:7] == '!meditate ' or \
                whisper[:13] == '!concentrate ' or whisper[:5] == '!med ' or whisper[:5] == '!con ':
            t = threading.Thread(target=checkExistence, args=(username, RPGTestMode, s, channel,))
            t.start()
        if message == '!playRPG' or whisper == '!playRPG':
            t = threading.Thread(target=startRPG, args=(username, s, channel,))
            t.start()
        elif message == '!slots':
            if len(whisper) < len(message):
                message = whisper
                if username in PLAYER:
                    channel = PLAYER[username].lastchannel
            if username not in PLAYER:
                chat(s, channel, ("/w %s Sorry, you need to play the game to earn money!" % username))
            else:
                t = threading.Thread(target=slotsTimer, args=(PLAYER[username], s, channel, RPGTestMode,))
                t.start()
        elif username in admin and username != '':
            if message == '!modcommands':
                chat(s, channel, "Commands are: !say, !pyramid, !addmod, !delmod, !addreg, !delreg, !leave, !startpoll, !endpoll, !ignore, !stopignore, !cartreset")
            elif message[:5] == "!say ":
                text = message[5:]
                say(text, s, channel)
            elif message[:9] == "!pyramid ":
                text = message[9:]
                pyramid(text, s, channel)
            elif message[:6] == "!raid ":
                boss = message[6:]
                t = threading.Thread(target=raidlobby, args=(s, channel, boss,))
                t.start()
            elif message == "!pvplobby":
                t = threading.Thread(target=pvplobby, args=(s, channel,))
                t.start()
            elif message[:8] == "!addmod ":
                user = message[8:]
                admin = listedit(user, "add", "admins", s, channel, MAIN)
                print(admin)
            elif message[:8] == "!delmod ":
                user = message[8:]
                admin = listedit(user, "del", "admins", s, channel, MAIN)
                print(admin)
            elif message[:8] == "!addreg ":
                user = message[8:]
                reglist = listedit(user, "add", "regulars", s, channel, MAIN)
            elif message[:8] == "!delreg ":
                user = message[8:]
                reglist = listedit(user, "del", "regulars", s, channel, MAIN)
            elif message[:8] == '!create ' or whisper[:8] == '!create ':
                if len(whisper) < len(message):
                    message = whisper
                    if username in PLAYER:
                        channel = PLAYER[username].lastchannel
                user = message[8:]
                startRPG(user, PLAYER, s, channel)
            elif message[:8] == '!delete ' or whisper[:8] == '!delete ':
                if len(whisper) < len(message):
                    message = whisper
                    if username in PLAYER:
                        channel = PLAYER[username].lastchannel
                user = message[8:]
                if user in PLAYER:
                    PLAYER[user].delete(s, channel)
                    del PLAYER[user]
                else:
                    chat(s, channel, ("%s is not in the game!" % user))
            elif message == '!give' or whisper == '!give':
                if len(whisper) < len(message):
                    message = whisper
                    if username in PLAYER:
                        channel = PLAYER[username].lastchannel
                chat(s, channel, ("/w %s !give <user> <stat> <amount>" % username))
            elif message[:6] == '!give ' or whisper[:6] == '!give ':
                if len(whisper) < len(message):
                    message = whisper
                    if username in PLAYER:
                        channel = PLAYER[username].lastchannel
                message = message[6:]
                try:
                    User, Change, Amount = message.split(' ')
                    if is_number(Amount) is True:
                        if User in PLAYER:
                            PLAYER[User].give(username, Change, Amount, s, channel)
                        else:
                            chat(s, channel, ("%s is not in the game!" % User))
                    else:
                        chat(s, channel, ("Amount not a number!"))
                except ValueError:
                    chat(s, channel, ("Not enough variables!"))
            elif message == '!startpoll':
                if votelisten == 1:
                    chat(s, channel, "Vote has already been started!")
                else:
                    chat(s, channel, "Voting has begun!")
                    chat(s, channel, "Use !vote <your vote> to vote!")
                    voting = {}
                    starter = username
                    votelisten = 1
            elif message == '!endpoll':
                if votelisten == 0:
                    chat(s, channel, "Vote has not started.")
                else:
                    t = threading.Thread(target=endVote, args=(voting, s, channel, starter,))
                    t.start()
                    votelisten = 0
            elif message == '!ignore':
                startignore = True
                chat(s, channel, "Will no longer respond to commands. Use !stopignore to let me respond to commands again!")
            elif message == '!cartreset':
                cartcount = 0
                chat(s, channel, "Reset cart counter!")
            elif message[:6] == '!join ' or whisper[:6] == '!join ':
                if len(whisper) < len(message):
                    message = whisper
                    if username in PLAYER:
                        channel = PLAYER[username].lastchannel
                newchannel = message[6:]
                if newchannel[0] != '#':
                    newchannel = '#%s' % newchannel
                s.send("JOIN {}\r\n".format(newchannel).encode("utf-8"))
                chat(s, channel, "Joined %s!" % newchannel)
            elif message == '!RPGtestmode':
                if RPGTestMode is False:
                    chat(s, channel, "Test Mode On!")
                    RPGTestMode = True
                else:
                    chat(s, channel, "Test Mode Off!")
                    RPGTestMode = False
            elif message == "!leave":
                chat(s, channel, "Bye!")
                print("Asked to leave, shutting down.")
                MainLoop = False

# -----------------------------------------------------------------------------


rpgmessage = time.time()

while MainLoop is True:
    response = s.recv(1024).decode("utf-8")
    if response == "PING :tmi.twitch.tv\r\n":
        s.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
    else:
        response2 = response[1:]
        channelstart = response2.find('#')
        channelend = response2.find(':')
        channel = response2[channelstart:channelend - 1]
        username = re.search(r"\w+", response).group(0)  # return the entire match
        message2 = CHAT_MSG.sub("", response)
        whisper2 = WHISPER_MSG.sub("", response)
        whisper = whisper2.rstrip('\r\n')
        message = message2.rstrip('\r\n')
        # print("'%s', '%s', '%s', '%s', '%s', '%s', '%s'" % (username, message, whisper, message2, whisper2, s, channel))
        t = threading.Thread(target=handleCommands, args=(username, message, whisper, message2, whisper2, s, channel,))
        t.start()
