import configparser
from os.path import isfile

Config = configparser.ConfigParser()
NICK = ''
MAIN = ''
PASS = ''
CHAN = ''
HOST = "irc.chat.twitch.tv"                    # the Twitch IRC server
PORT = 6667                                    # always use port 6667!
RATE = (100 / 30)                                # messages per second


Config = configparser.ConfigParser()
if isfile("botfiles/settings.ini") is False:
    NICK = input("Please enter your bots Twitch username: ").lower()
    MAIN = input("Please enter your main Twitch username: ").lower()
    PASS = input("Please enter your bots Twitch OAuth Token: ")
    CHAN = input("Please enter the Twitch channel you want the bot to join: ")
    if CHAN[:1] != "#":
        CHAN = "#" + CHAN
    cfgfile = open("botfiles/settings.ini", 'a+')
    Config.add_section('Settings')
    Config.set('Settings', 'Bot Name', NICK)
    Config.set('Settings', 'Nickname', MAIN)
    Config.set('Settings', 'OAuth Token', PASS)
    Config.set('Settings', 'Channel', CHAN)
    Config.write(cfgfile)
    cfgfile.close()
else:
    Config.read("botfiles/settings.ini")
    NICK = Config.get('Settings', 'Bot Name')
    MAIN = Config.get('Settings', 'Nickname')
    PASS = Config.get('Settings', 'OAuth Token')
    CHAN = Config.get('Settings', 'Channel')

if isfile("botfiles/admins.txt") is False:
    alist = open("botfiles/admins.txt", "w+")
    alist.write(MAIN + ", ")
    alist.close()

if isfile("botfiles/regulars.txt") is False:
    rlist = open("botfiles/regulars.txt", "w+")
    rlist.write(MAIN + ", ")
    rlist.close()
