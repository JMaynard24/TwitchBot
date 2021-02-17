from collections import Counter
from math import ceil, floor
from MathUtility import is_number
from random import randint
from Commands import chat, globalchat
from os.path import isfile
from enum import Enum
import copy
import os
import time
import operator
import random
import threading

# Global lookup dictionaries
PLAYER = {}
MONSTER = {}
ITEM = {}
TECH = {}
LOCATION = {}

# def chat(fake_socket, fake_channel, message):
#     print(message)


def isobject(data):
    return hasattr(data, '__dict__')


# def testEncounter(player, encType, bossName):
#     t = threading.Thread(target=encounter, args=([player.name], 0, 0, False, encType, bossName, False))
#     t.start()


class Encounter(Enum):
    NORMAL = 0
    BOSS = 1
    RAID = 2
    PVP = 3


class Character:
    def __init__(self, name):
        # Shared Variables
        self.name = name
        self.level = 1
        self.maxlife = 40
        self.life = 40
        self.maxmana = 10
        self.mana = 10
        self.maxfocus = 10
        self.focus = 10
        self.vigor = 10
        self.power = 10
        self.finesse = 10
        self.will = 10
        self.guard = 10
        self.magic = 10
        self.speed = 10
        self.luck = 10
        self.energy = 0
        self.critchance = 5
        self.isplayer = False
        self.description = 'This is %s, an adventurer just like you!' % self.name
        self.team = 0
        self.isguarding = False
        self.chargecount = 1
        self.skills = []
        self.spells = []

        # Player Variables
        self.potential = 0
        self.respecpoints = 0
        self.money = 0
        self.exp = 0
        self.trainingpoints = 0
        self.kills = 0
        self.deaths = 0
        self.timeouts = 0
        self.runaway = 0
        self.location = getLocation('Prison of Hope')
        self.lasttown = getLocation('Tarrow')
        self.weapon = getItem('Worn Sword')
        self.shield = getItem('Barrel Lid')
        self.armor = getItem('Prison Garb')
        self.charm = getItem('Pendant')
        self.lastmessage = ''
        self.lastwhisper = ''
        self.lastchannel = ''
        self.encountertimer = 0
        self.encountersinsamearea = 0
        self.killstreak = 0
        self.challenger = ''
        self.inencounter = False
        self.inshop = False
        self.intrainer = False
        self.bossesbeaten = []
        self.raidbossesbeaten = []
        self.allowedlocations = ['Prison of Hope']
        self.inventory = []

        # Enemy Variables
        self.moneyaward = 0
        self.expaward = 0
        self.opening = 'Missing Opening?'
        self.statusinflict = 0
        self.statuschance = 0
        self.enemyenergyuse = 200
        self.droplist = {}
        self.isboss = False
        self.israidboss = False
        self.bossoutro = 'Missing Outro?'
        self.damagetext = 'Missing DamageText?'
        self.nodamagetext = 'Missing NoDamageText?'
        self.crittext = 'Missing CritText?'
        self.unlocklocations = []

        # Shared Dictionaries
        self.status = {'Poison': False,
                       'Stun': False,
                       'Paralysis': False,
                       'Toxic': False,
                       'Sleep': False,
                       'Blind': False,
                       'Panic': False,
                       'Bleed': False,
                       'Sap': False,
                       'Silence': False,
                       'Horror': False
                       }
        self.statchange = {'maxlife': 0,
                           'maxmana': 0,
                           'maxfocus': 0,
                           'power': 0,
                           'finesse': 0,
                           'will': 0,
                           'guard': 0,
                           'magic': 0,
                           'speed': 0,
                           'luck': 0,
                           'critchance': 0,
                           }
        self.elementalatk = {'Fire': 0,
                             'Elec': 0,
                             'Water': 0,
                             'Earth': 0,
                             'Psyche': 0,
                             }
        self.elementaldef = {'Fire': 0,
                             'Elec': 0,
                             'Water': 0,
                             'Earth': 0,
                             'Psyche': 0,
                             }
        self.clearStatChanges()

    def get(self, stat):
        return getattr(self, stat) + self.statchange[stat]

    def handleRPG(self, RPGTestMode, s, channel):
        if self.lastmessage == '!playRPG' or self.lastwhisper == '!playRPG':
            t = threading.Thread(target=startRPG, args=(self.name, PLAYER, s, channel,))
            t.start()
        elif self.lastwhisper[:9] == '!examine ':
            item = self.lastwhisper[9:]
            t = threading.Thread(target=PLAYER[self.name].examineItem, args=(item, s, channel, PLAYER,))
            t.start()
        elif self.lastwhisper[:5] == '!use ' and self.inencounter is False:
            item = self.lastwhisper[5:]
            t = threading.Thread(target=PLAYER[self.name].useItem, args=(item, s, channel,))
            t.start()
        elif self.lastwhisper == '!shop':
            t = threading.Thread(target=PLAYER[self.name].shopping, args=(s, channel,))
            t.start()
        elif self.lastwhisper == '!trainer':
            t = threading.Thread(target=PLAYER[self.name].training, args=(s, channel,))
            t.start()
        elif self.lastwhisper == '!travel':
            t = threading.Thread(target=PLAYER[self.name].displayTravel, args=(s, channel,))
            t.start()
        elif self.lastwhisper == '!location' or self.lastwhisper == '!loc':
            chat(s, channel, ("/w %s You are at %s!" % (self.name, PLAYER[self.name].location.name)))
        elif self.lastmessage[:5] == '!lbs ':
            board = self.lastmessage[5:]
            t = threading.Thread(target=leaderBoards, args=(self.name, board, s, channel,))
            t.start()
        elif self.lastwhisper == '!commands':
            if PLAYER[self.name].inencounter:
                chat(s, channel, ("/w %s Commands are: !fight (%s), !check (100), !use (examine item for energy use), !escape (200)" %
                     (self.name, PLAYER[self.name].weapon.energyuse)))
        elif self.lastwhisper[:8] == '!travel ':
            if self.inencounter is False and self.inshop is False and self.inencounter is False:
                location = self.lastwhisper[8:]
                if location in PLAYER[self.name].allowedlocations and location != PLAYER[self.name].location:
                    t = threading.Thread(target=PLAYER[self.name].travel, args=(s, channel, location,))
                    t.start()
                elif location == PLAYER[self.name].location:
                    chat(s, channel, ("/w %s You are already at %s!" % (self.name, location)))
                else:
                    chat(s, channel, ("/w %s You don't know how to get to %s!" % (self.name, location)))
            elif PLAYER[self.name].inshop is True:
                chat(s, channel, ("/w %s You can't travel while in the shop!" % (self.name)))
            elif PLAYER[self.name].intrainer is True:
                chat(s, channel, ("/w %s You can't travel while training!" % (self.name)))
            else:
                chat(s, channel, ("/w %s You can't travel during an encounter!" % (self.name)))
        elif self.lastwhisper == '!surroundings' or self.lastwhisper == '!look':
            t = threading.Thread(target=PLAYER[self.name].displaySurroundings, args=(s, channel,))
            t.start()
        elif self.lastwhisper == '!stats':
            t = threading.Thread(target=PLAYER[self.name].displayStats, args=(s, channel,))
            t.start()
        elif self.lastwhisper == '!inv':
            t = threading.Thread(target=PLAYER[self.name].displayInventory, args=(s, channel,))
            t.start()
        elif self.lastwhisper[:9] == '!discard ':
            itemname = self.lastwhisper[9:]
            t = threading.Thread(target=PLAYER[self.name].discarditem, args=(s, channel, itemname,))
            t.start()
        elif self.lastwhisper[:7] == '!equip ':
            itemname = self.lastwhisper[7:]
            t = threading.Thread(target=PLAYER[self.name].equipitem, args=(s, channel, itemname,))
            t.start()
        elif self.lastwhisper[:11] == '!encounter':
            if self.inshop is True:
                chat(s, channel, ("/w %s You are busy shopping!" % (self.name)))
            elif self.intrainer is True:
                chat(s, channel, ("/w %s You are busy training!" % (self.name)))
            else:
                t = threading.Thread(target=encounterTimer, args=([PLAYER[self.name]], s, channel, RPGTestMode, Encounter.NORMAL, '', False))
                t.start()
        elif self.lastwhisper == '!encounter boss':
            if self.inshop is True:
                chat(s, channel, ("/w %s You are busy shopping!" % (self.name)))
            elif self.intrainer is True:
                chat(s, channel, ("/w %s You are busy training!" % (self.name)))
            else:
                t = threading.Thread(target=encounterTimer, args=([PLAYER[self.name]], s, channel, RPGTestMode, Encounter.BOSS, '', False))
                t.start()
        elif self.lastwhisper[:7] == '!meditate ' or self.lastwhisper[:13] == '!concentrate ' or self.lastwhisper[:5] == '!med ' or self.lastwhisper[:5] == '!con ':
            command, amount = self.lastwhisper.split(' ')
            t = threading.Thread(target=PLAYER[self.name].meditateconcentrate, args=(s, channel, command, amount,))
            t.start()

    def setPlayer(self):
        if self.name not in PLAYER:
            PLAYER[self.name] = self

    def setMonster(self):
        if self.name not in MONSTER:
            MONSTER[self.name] = self

    def clearStatusEffects(self):
        for i in self.status.keys():
            self.status[i] = False

    def clearStatChanges(self):
        for i in self.statchange.keys():
            self.statchange[i] = 0
            self.statchange[i] += self.weapon.buff[i]
            if self.weapon.is2handed is False:
                self.statchange[i] += self.shield.buff[i]
            self.statchange[i] += self.armor.buff[i]
            self.statchange[i] += self.charm.buff[i]

    def cleanUp(self, s, channel, droplist, die):
        self.clearStatChanges()
        self.clearStatusEffects()
        self.energy = 0
        self.chargecount = 1
        self.save()
        if die is False:
            t = threading.Thread(target=self.levelUp, args=(s, channel, droplist))
            t.start()

    def meditateconcentrate(self, s, channel, command, amount):
        if self.inencounter:
            chat(s, channel, ("/w %s You can't use this during battle!" % (self.name)))
            return
        if is_number(amount) or amount == 'all':
            if amount != 'all':
                amount = int(amount)
            if command == '!meditate' or command == '!med':
                if 'Meditate' not in self.skills:
                    chat(s, channel, ("/w %s You don't know how to Meditate!" % (self.name)))
                    return
                if amount == 'all':
                    amount = self.mana
                maxamount = self.get('maxfocus') - self.focus
                if amount > maxamount:
                    amount = maxamount
                if amount == 0:
                    chat(s, channel, ("/w %s You already had full Focus!" % (self.name)))
                    return
                if amount > self.mana:
                    amount = self.mana
                if amount == 0:
                    chat(s, channel, ("/w %s You don't have any Mana to meditate!" % (self.name)))
                    return
                self.mana -= amount
                self.focus += amount
                chat(s, channel, ("/w %s You used %s Mana to regain %s Focus!" % (self.name, amount, amount)))
                self.save()
            if command == '!concentrate' or command == '!con':
                if 'Concentrate' not in self.skills:
                    chat(s, channel, ("/w %s You don't know how to Concentrate!" % (self.name)))
                    return
                if amount == 'all':
                    amount = self.focus
                maxamount = self.get('maxmana') - self.mana
                if amount > maxamount:
                    amount = maxamount
                if amount == 0:
                    chat(s, channel, ("/w %s You already had full Mana!" % (self.name)))
                if amount > self.focus:
                    amount = self.focus
                if amount == 0:
                    chat(s, channel, ("/w %s You don't have any Focus to concentrate!" % (self.name)))
                    return
                self.focus -= amount
                self.mana += amount
                chat(s, channel, ("/w %s You used %s Focus to regain %s Mana!" % (self.name, amount, amount)))
                self.save()
        else:
            chat(s, channel, ("/w %s Amount must be a number or 'all'!" % (self.name)))

    def evaluateStatus(self, playersinencounter, s, channel, inflict, chance):
        if inflict > 0:
            statroll = randint(1, 100)
            chance *= 1 - (self.will / 272)
            if chance >= statroll:
                if inflict == 1 and self.status['Poison'] is False:
                    self.status['Poison'] = True
                    for chatter in playersinencounter:
                        if chatter.name == self.name:
                            globalchat(s, channel, ("/w %s You got poisoned!" % (self.name)))
                        else:
                            globalchat(s, channel, "/w %s %s has been poisoned!" % (chatter.name, self.name))
                elif inflict == 2 and self.status['Stun'] is False:
                    for chatter in playersinencounter:
                        if chatter.name == self.name:
                            globalchat(s, channel, ("/w %s You have been stunned and lost 100 energy!" % (self.name)))
                            self.energy -= 100
                        else:
                            globalchat(s, channel, "/w %s %s has been stunned and lost 100 energy!" % (chatter.name, self.name))
                elif inflict == 3 and self.status['Paralysis'] is False:
                    self.status['Paralysis'] = True
                    for chatter in playersinencounter:
                        if chatter.name == self.name:
                            globalchat(s, channel, ("/w %s You have been paralyzed!" % (self.name)))
                        else:
                            globalchat(s, channel, "/w %s %s has been paralyzed!" % (chatter.name, self.name))
                elif inflict == 4 and self.status['Toxic'] is False:
                    self.status['Toxic'] = True
                    for chatter in playersinencounter:
                        if chatter.name == self.name:
                            globalchat(s, channel, ("/w %s You are toxic!" % (self.name)))
                        else:
                            globalchat(s, channel, "/w %s %s is toxic!" % (chatter.name, self.name))
                elif inflict == 5 and self.status['Sleep'] is False:
                    self.status['Sleep'] = True
                    for chatter in playersinencounter:
                        if chatter.name == self.name:
                            globalchat(s, channel, ("/w %s You have been put to sleep!" % (self.name)))
                        else:
                            globalchat(s, channel, "/w %s %s has been put to sleep!" % (chatter.name, self.name))
                elif inflict == 6 and self.status['Blind'] is False:
                    self.status['Blind'] = True
                    for chatter in playersinencounter:
                        if chatter.name == self.name:
                            globalchat(s, channel, ("/w %s You have been blined!" % (self.name)))
                        else:
                            globalchat(s, channel, "/w %s %s has been blined!" % (chatter.name, self.name))
                elif inflict == 7 and self.status['Panic'] is False:
                    self.status['Panic'] = True
                    for chatter in playersinencounter:
                        if chatter.name == self.name:
                            globalchat(s, channel, ("/w %s You have been put into a panic!" % (self.name)))
                        else:
                            globalchat(s, channel, "/w %s %s has been put into a panic!" % (chatter.name, self.name))
                elif inflict == 8 and self.status['Bleed'] is False:
                    self.status['Bleed'] = True
                    for chatter in playersinencounter:
                        if chatter.name == self.name:
                            globalchat(s, channel, ("/w %s You begin to bleed!" % (self.name)))
                        else:
                            globalchat(s, channel, "/w %s %s begins to bleed!" % (chatter.name, self.name))
                elif inflict == 11 and self.status['Horror'] is False:
                    damage = ceil(self.life / 4)
                    for chatter in playersinencounter:
                        if chatter.name == self.name:
                            globalchat(s, channel, ("/w %s Horrible images fill your vision. You claw at your eyes for %s damage!" % (self.name, damage)))
                            chatter.takeDamage([], playersinencounter, s, channel, damage)
                        else:
                            globalchat(s, channel, "/w %s %s claws at their eyes for %s damage!" % (chatter.name, self.name, damage))

    def damageRoll(self, target, charactersinencounter, playersinencounter, s, channel):
        time.sleep(1)
        if not self.hitChance(target):
            if self.status['Blind']:
                for chatter in playersinencounter:
                    if chatter.name == target.name:
                        globalchat(s, channel, "/w %s %s flails blindly and misses you!" % (chatter.name, self.name))
                    elif chatter.name == self.name:
                        globalchat(s, channel, "/w %s You flail blindly and miss %s!" % (chatter.name, target.name))
                    else:
                        globalchat(s, channel, "/w %s %s flails blindly and misses %s!" % (chatter.name, self.name, target.name))
            else:
                for chatter in playersinencounter:
                    if chatter.name == target.name:
                        globalchat(s, channel, "/w %s You dodged %s's attack!" % (chatter.name, self.name))
                    elif chatter.name == self.name:
                        globalchat(s, channel, "/w %s %s dodged your attack!" % (chatter.name, target.name))
                    else:
                        globalchat(s, channel, "/w %s %s dodged %s's attack!" % (chatter.name, target.name, self.name))
            return
        iscrit = False
        Damage = randint(ceil(self.power / 2), self.power)
        CritRoll = randint(1, 100)
        if ceil(self.critchance + self.luck * 0.075) >= CritRoll:
            Damage += self.power
            iscrit = True
        Damage = ceil(Damage * min(1, (self.power / target.guard) * 0.5))
        if Damage == 0:
            for chatter in playersinencounter:
                if chatter.name == target.name and target.behavior == 'Player' and target.weapon.is2handed:
                    globalchat(s, channel, "/w %s %s" % (chatter.name, self.weapon.nodamagereceivetext.format(player=self.name)))
                elif chatter.name == target.name and target.behavior == 'Player' and target.weapon.is2handed is False:
                    globalchat(s, channel, "/w %s %s" % (chatter.name, self.shield.nodamagereceivetext.format(player=self.name)))
                elif chatter.name == self.name and target.behavior != 'Player':
                    globalchat(s, channel, "/w %s %s" % (chatter.name, target.nodamagetext))
                elif chatter.name == self.name and target.weapon.is2handed:
                    globalchat(s, channel, "/w %s %s" % (chatter.name, target.weapon.nodamagedealtext.format(player=target.name)))
                elif chatter.name == self.name and target.weapon.is2handed is False:
                    globalchat(s, channel, "/w %s %s" % (chatter.name, target.shield.nodamagedealtext.format(player=target.name)))
                else:
                    globalchat(s, channel, "/w %s %s's attack bounced off %s's armor!" % (chatter.name, target.name, self.name))
        elif iscrit:
            for chatter in playersinencounter:
                if chatter.name == target.name and self.isplayer is False:
                    globalchat(s, channel, "/w %s %s" % (chatter.name, self.crittext.format(damage=Damage)))
                elif chatter.name == target.name and self.isplayer:
                    globalchat(s, channel, "/w %s %s" % (chatter.name, self.weapon.critreceivetext.format(player=self.name, damage=Damage)))
                elif chatter.name == self.name:
                    globalchat(s, channel, "/w %s %s" % (chatter.name, self.weapon.critdealtext.format(player=target.name, damage=Damage)))
                else:
                    globalchat(s, channel, "/w %s %s was dealt a critical blow by %s for %s damage!" % (chatter.name, target.name, self.name, Damage))
        else:
            for chatter in playersinencounter:
                if chatter.name == target.name and self.isplayer is False:
                    globalchat(s, channel, "/w %s %s" % (chatter.name, self.damagetext.format(damage=Damage)))
                elif chatter.name == target.name and self.isplayer:
                    globalchat(s, channel, "/w %s %s" % (chatter.name, self.weapon.damagereceivetext.format(player=self.name, damage=Damage)))
                elif chatter.name == self.name:
                    globalchat(s, channel, "/w %s %s" % (chatter.name, self.weapon.damagedealtext.format(player=target.name, damage=Damage)))
                else:
                    globalchat(s, channel, "/w %s %s was hit by %s for %s damage!" % (chatter.name, target.name, self.name, Damage))
        target.takeDamage(charactersinencounter, playersinencounter, s, channel, Damage)
        if target.life > 0 and Damage > 0:
            if self.isplayer:
                target.evaluateStatus(playersinencounter, s, channel, self.weapon.statusinflict, self.weapon.statuschance)
            else:
                target.evaluateStatus(playersinencounter, s, channel, self.statusinflict, self.statuschance)

    def statusDamage(self, charactersinencounter, playersinencounter, s, channel):
        TotalDamage = 0
        if self.status['Poison'] is True:
            time.sleep(1)
            Damage = randint(1, 5)
            TotalDamage += Damage
            for i in playersinencounter:
                if i.name == self.name:
                    globalchat(s, channel, "/w %s You took %s poison damage!" % (i.name, Damage))
                else:
                    globalchat(s, channel, "/w %s %s took %s poison damage!" % (i.name, self.name, Damage))
        if self.status['Toxic'] is True:
            time.sleep(1)
            Damage = randint(ceil((self.maxlife + self.statchange['maxlife']) / 10), ceil((self.maxlife + self.statchange['maxlife']) / 4))
            TotalDamage += Damage
            for i in playersinencounter:
                if i.name == self.name:
                    globalchat(s, channel, "/w %s You took %s toxic damage!" % (i.name, Damage))
                else:
                    globalchat(s, channel, "/w %s %s took %s toxic damage!" % (i.name, self.name, Damage))
        if self.status['Bleed'] is True:
            time.sleep(1)
            Damage = randint(ceil((self.maxlife + self.statchange['maxlife']) / 10), ceil((self.maxlife + self.statchange['maxlife']) / 4))
            TotalDamage += Damage
            for i in playersinencounter:
                if i.name == self.name:
                    globalchat(s, channel, "/w %s You took %s bleeding damage!" % (i.name, Damage))
                else:
                    globalchat(s, channel, "/w %s %s took %s bleeding damage!" % (i.name, self.name, Damage))
        self.takeDamage(charactersinencounter, playersinencounter, s, channel, TotalDamage)

    def takeDamage(self, charactersinencounter, playersinencounter, s, channel, amount):
        self.life -= amount
        if self.life <= 0:
            charactersinencounter.remove(self)
            time.sleep(1)
            for chatter in playersinencounter:
                if chatter.name == self.name:
                    globalchat(s, channel, "/w %s You collapse!" % (chatter.name))
                else:
                    globalchat(s, channel, "/w %s %s dies!" % (chatter.name, self.name))
            if self.isplayer is False:
                time.sleep(1)
                for chatter in playersinencounter:
                    moneyfound = floor(self.moneyaward * (1 + (chatter.luck / 100)))
                    if self.isboss is True and self.name in chatter.bossesbeaten:
                        chatter.money += floor(moneyfound / 3)
                        chatter.exp += floor(self.expaward / 3)
                        money = floor(moneyfound / 3)
                        exp = floor(self.expaward / 3)
                    else:
                        chatter.money += moneyfound
                        chatter.exp += self.expaward
                        money = moneyfound
                        exp = self.expaward
                    if self.isboss:
                        if self.name not in chatter.bossesbeaten:
                            chatter.bossesbeaten.append(self.name)
                            chat(s, channel, "/w %s %s" % (chatter.name, self.bossoutro))
                            globalchat(s, channel, "%s has cleared %s!" % (chatter.name, chatter.location.name))
                    if self.israidboss:
                        if self.name not in chatter.raidbossesbeaten:
                            chatter.raidbossesbeaten.append(self.name)
                            globalchat(s, channel, "/w %s %s" % (chatter.name, self.bossoutro))
                    globalchat(s, channel, "/w %s You got %s ides and %s experience!" % (chatter.name, money, exp))
                    if len(self.unlocklocations) > 0:
                        addedlocations = []
                        for location in self.unlocklocations:
                            if location not in chatter.allowedlocations:
                                chatter.allowedlocations.append(location)
                                addedlocations.append(location)
                        if len(addedlocations) > 0:
                            chat(s, channel, "/w %s You've unlocked new destinations: %s" % (chatter.name, ', '.join(addedlocations)))
                    chatter.encountersinsamearea += 1
                    chatter.kills += 1
                    if chatter.encountersinsamearea > chatter.killstreak:
                        chatter.killstreak = chatter.encountersinsamearea
                    chatter.cleanUp(s, channel, self.droplist, False)
            else:
                self.inencounter = False
                self.clearStatChanges()
                self.clearStatusEffects()
                self.life = (self.maxlife + self.statchange['maxlife'])
                playersinencounter.remove(self)
                moneyloss = ceil(self.money / 10)
                self.money = self.money - moneyloss
                self.encountersinsamearea = 0
                self.deaths += 1
                if len(self.allowedlocations) == 1:
                    if moneyloss > 0:
                        chat(s, channel, "/w %s A guard drags you back to your cell. He smirks as he pilfers a portion of your ides (%s). After some time, you return to your feet." % (self.name, moneyloss))
                    else:
                        chat(s, channel, "/w %s A guard drags you back to your cell. Finding no ides on you, he gives you a solid kick to the ribs and leaves. After some time, you return to your feet." % (self.name))
                else:
                    self.location = LOCATION[self.lasttown]
                    if moneyloss > 0:
                        chat(s, channel, "/w %s A mysterious figure approaches as you lose consciousness. You awaken in the %s inn clutching a note, \"Your generous payment of %s ides is accepted. Be vigilant, stranger.\"" % (self.name, self.location.name, moneyloss))
                    else:
                        chat(s, channel, "/w %s A mysterious figure approaches as you lose consciousness. You awaken in the %s inn clutching a note, \"You owe me, stranger. Dearly.\"" % (self.name, self.location.name))
                self.save()
                self.cleanUp(s, channel, {}, True)

    def hitChance(self, target):
        chance = min(100, (self.speed / target.speed) * 50 + 50 + (self.luck * 0.0392) - (target.luck * 0.0392))
        chance = max(chance, 0)
        if self.status['Blind']:
            chance *= 0.5
        if chance >= randint(1, 100) or target.status['Paralysis'] or target.status['Sleep']:
            return True
        else:
            return False

    def energyRecovery(self, playersInEncounter, s, channel):
        self.energy += (self.speed * 5 + 95)

    def save(self):
        fileobj = open("RPG/Players/%s.temp.txt" % self.name, "w+")
        for attr in vars(self):
            attrval = getattr(self, attr)
            if isobject(attrval):
                fileobj.write("%s: \"%s\"\n" % (attr, attrval.name))
            elif isinstance(attrval, dict):
                for k in attrval:
                    v = attrval[k]
                    if isobject(v):
                        fileobj.write("%s.%s: \"%s\"\n" % (attr, k, v.name))
                    elif isinstance(v, str):
                        fileobj.write("%s.%s: \"%s\"\n" % (attr, k, v))
                    else:
                        fileobj.write("%s.%s: %s\n" % (attr, k, v))
            elif isinstance(attrval, str):
                fileobj.write("%s: \"%s\"\n" % (attr, attrval))
            elif isinstance(attrval, list):
                if len(attrval) == 0:
                    fileobj.write("%s: []\n" % attr)
                elif isobject(attrval[0]):
                    savelist = [obj.name for obj in attrval]
                    fileobj.write("%s: %s\n" % (attr, savelist))
                else:
                    fileobj.write("%s: %s\n" % (attr, attrval))
            else:
                fileobj.write("%s: %s\n" % (attr, attrval))
        fileobj.close()
        if isfile("RPG/Players/%s.txt" % self.name) is True:
            os.remove("RPG/Players/%s.txt" % self.name)
        os.rename("RPG/Players/%s.temp.txt" % self.name, "RPG/Players/%s.txt" % self.name)

    def load(self):
        self.setPlayer()
        fileobj = open("RPG/Players/%s.txt" % self.name)
        data = fileobj .readlines()
        fileobj .close()
        for line in data:
            parsed = line.split(': ', 1)
            if '.' in parsed[0]:
                attr, key = tuple(parsed[0].split('.', 1))
                val = parsed[1]
                dct = getattr(self, attr)
                dct[key] = eval(val)
            else:
                attr = parsed[0]
                val = parsed[1]
                setattr(self, attr, eval(val))
        self.location = LOCATION[self.location]
        self.weapon = getItem(self.weapon)
        self.shield = getItem(self.shield)
        self.armor = getItem(self.armor)
        self.charm = getItem(self.charm)
        for item in self.inventory.copy():
            self.inventory.remove(item)
            self.inventory.append(ITEM[item])
        self.inencounter = False
        self.inshop = False
        self.intrainer = False
        self.isplayer = True

    def delete(self, s, channel):
        if isfile('RPG\Players\Deleted\%s.txt' % self.name):
            os.remove('RPG\Players\Deleted\%s.txt' % self.name)
        os.rename('RPG\Players\%s.txt' % self.name, 'RPG\Players\Deleted\%s.txt' % self.name)
        chat(s, channel, ("Deleted %s!" % self.name))

    def displayInventory(self, s, channel):
        stacks = {}
        for item in self.inventory:
            if item.name not in stacks:
                stacks[item.name] = 1
            else:
                stacks[item.name] += 1
        sortedstacks = sorted(stacks.items(), key=operator.itemgetter(1), reverse=True)
        stringofitems = ''
        if len(sortedstacks) == 0:
            stringofitems = 'Nothing...'
        else:
            if len(sortedstacks) < 3:
                item, number = sortedstacks[0]
                if number == 1:
                    stringofitems = '%s' % item
                else:
                    stringofitems = '%s x%s' % (item, number)
            else:
                item, number = sortedstacks[0]
                if number == 1:
                    stringofitems = '%s,' % item
                else:
                    stringofitems = '%s x%s,' % (item, number)
            if len(sortedstacks) >= 2:
                for itempair in sortedstacks[1:len(stacks) - 1]:
                    item, number = itempair
                    if number == 1:
                        stringofitems += (' %s,' % item)
                    else:
                        stringofitems += (' %s x%s,' % (item, number))
            if len(sortedstacks) == 1:
                pass
            else:
                item, number = sortedstacks[len(stacks) - 1]
                if number == 1:
                    stringofitems += ' and %s' % item
                else:
                    stringofitems += ' and %s x%s' % (item, number)
        if self.weapon is None or self.weapon.is2handed is False:
            chat(s, channel, "/w %s You have %s, %s, %s, and %s equipped" % (self.name, self.weapon.name, self.shield.name, self.armor.name, self.charm.name))
        else:
            chat(s, channel, "/w %s You have %s, %s (Inactive), %s, and %s equipped" % (self.name, self.weapon.name, self.shield.name, self.armor.name, self.charm.name))
        chat(s, channel, "/w %s You have: %s" % (self.name, stringofitems))

    def displayStats(self, s, channel):
        self.clearStatChanges()
        chat(s, channel, ("/w %s %s Level: %s - Life: %s/%s - " % (self.name, self.name, self.level, self.life, self.get('maxlife')) +
                          "Mana: %s/%s - Focus: %s/%s - Vigor: %s - " % (self.mana, self.get('maxmana'), self.focus, self.get('maxfocus'), self.vigor) +
                          "Power: %s - Finesse: %s - Will: %s - " % (self.get('power'), self.get('finesse'), self.get('will')) +
                          "Guard: %s - Speed: %s - Luck: %s - " % (self.get('guard'), self.get('speed'), self.get('luck')) +
                          "Ides: %s - EXP: %s/%s - Potential: %s" % (self.money, self.exp, (self.level ** 2), self.potential)))

    def displayTravel(self, s, channel):
        if len(self.allowedlocations) < 3:
            stringofitems = self.allowedlocations[0]
        else:
            stringofitems = self.allowedlocations[0] + ','
        if len(self.allowedlocations) > 2:
            for item in self.allowedlocations[1:len(self.allowedlocations) - 1]:
                stringofitems += (' %s,' % item)
        if len(self.allowedlocations) > 1:
            stringofitems += ' and %s' % self.allowedlocations[len(self.allowedlocations) - 1]
        chat(s, channel, "/w %s You can travel to: %s" % (self.name, stringofitems))

    def displaySurroundings(self, s, channel):
        chat(s, channel, "/w %s %s" % (self.name, self.location.surroundings))

    def travel(self, s, channel, location):
        if location == self.location.name:
            chat(s, channel, "/w %s You are already here!" % (self.name))
        else:
            chat(s, channel, "/w %s You traveled to %s! %s" % (self.name, location, LOCATION[location].traveltext))
            self.encountersinsamearea = 0
            self.location = LOCATION[location]
            self.life = self.maxlife + self.statchange['maxlife']
            if self.location.name in townlocationlist:
                self.lasttown = self.location
            self.save()

    def shopping(self, s, channel):
        if self.location.hasshop is False:
            chat(s, channel, "/w %s There is no shop in %s!" % (self.name, self.location.name))
        elif self.inshop is True:
            chat(s, channel, "/w %s You are already shopping!" % (self.name))
        elif self.intrainer is True:
            chat(s, channel, "/w %s You can't shop while training!" % (self.name))
        elif self.inencounter is True:
            chat(s, channel, "/w %s You can't shop during an encounter!" % (self.name))
        else:
            self.inshop = True
            chat(s, channel, "/w %s %s" % (self.name, self.location.shopopening))
            chat(s, channel, "/w %s What would you like to do? (!commands)" % (self.name))
            self.lastwhisper = ''
            rumorcount = 0
            buysomething = False
            while True:
                if self.lastwhisper == "!commands":
                    chat(s, channel, "/w %s !buy <item name>, !sell <item name>, !examine <item name>, !list <weapons|shields|armor|charms|items>, !rumors, !leave" % (self.name))
                    self.lastwhisper = ''
                elif self.lastwhisper[:5] == "!buy ":
                    itemname = self.lastwhisper[5:]
                    if itemname not in ITEM:
                        chat(s, channel, "/w %s Such a thing has nary been spotted in Iodra." % (self.name))
                    else:
                        itemfound = False
                        for item in self.location.shopitem:
                            if item == itemname:
                                if self.checkinventoryslots(s, channel):
                                    if self.money > ITEM[itemname].price:
                                        self.money -= ITEM[itemname].price
                                        self.inventory.insert(0, ITEM[itemname])
                                        chat(s, channel, "/w %s You bought %s for %s ides" % (self.name, itemname, ITEM[itemname].price))
                                        self.save()
                                        buysomething = True
                                    else:
                                        chat(s, channel, "/w %s You don't have enough ides!" % (self.name))
                                else:
                                    chat(s, channel, "/w %s You decide not to purchase %s!" % (self.name, itemname))
                                itemfound = True
                                break
                        if itemfound is False:
                            chat(s, channel, "/w %s The shop doesn't sell %s!" % (self.name, itemname))
                    self.lastwhisper = ''
                elif self.lastwhisper[:6] == "!sell ":
                    itemname = self.lastwhisper[6:]
                    sold = False
                    if itemname not in ITEM:
                        chat(s, channel, "/w %s Such a thing has nary been spotted in Iodra." % (self.name))
                    elif ITEM[itemname] in self.inventory:
                        item = ITEM[itemname]
                        self.money += floor(item.price / 2)
                        chat(s, channel, "/w %s You sold %s for %s ides!" % (self.name, itemname, floor(item.price / 2)))
                        self.inventory.remove(item)
                        sold = True
                        self.save()
                    elif itemname in [self.weapon.name, self.shield.name, self.armor.name, self.charm.name]:
                        chat(s, channel, "/w %s You can't sell something you have equipped!" % (self.name, itemname))
                    elif sold is False:
                        chat(s, channel, "/w %s You do not have %s" % (self.name, itemname))
                    self.lastwhisper = ''
                elif self.lastwhisper[:9] == "!examine ":
                    itemname = self.lastwhisper[9:]
                    if itemname not in ITEM:
                        chat(s, channel, "/w %s Such a thing has nary been spotted in Iodra." % (self.name))
                    else:
                        inventorylist = [item.name for item in self.inventory]
                        examinelist = self.location.shopitem + [self.weapon.name, self.armor.name, self.shield.name, self.charm.name] + inventorylist
                        if itemname in examinelist:
                            chat(s, channel, "/w %s %s" % (self.name, ITEM[itemname].description))
                        else:
                            chat(s, channel, "/w %s You can't find the item to examine..." % (self.name))
                    self.lastwhisper = ''
                elif self.lastwhisper[:6] == "!list ":
                    listname = self.lastwhisper[6:]
                    shopdict = {}
                    if listname in ['weapons', 'shields', 'armor', 'charms', 'items']:
                        typestring = listname.capitalize()
                        for item in self.location.shopitem:
                            if ITEM[item].typeof == typestring:
                                shopdict[item] = ITEM[item].price
                        liststring = ''
                        for item in shopdict:
                            liststring += ('%s: %s, ' % (item, shopdict[item]))
                        liststring = liststring[:-2]
                        print('Liststring = %s' % liststring)
                        chat(s, channel, "/w %s %s" % (self.name, liststring))
                    else:
                        chat(s, channel, "/w %s That list does not exist!" % (liststring))
                    self.lastwhisper = ''
                elif self.lastwhisper == "!rumors":
                    chat(s, channel, "/w %s %s" % (self.name, self.location.shoprumor[rumorcount]))
                    if rumorcount < len(self.location.shoprumor) - 1:
                        rumorcount += 1
                    self.lastwhisper = ''
                elif self.lastwhisper == '!leave':
                    if buysomething is False:
                        chat(s, channel, "/w %s %s" % (self.name, self.location.shopclosingnobuy))
                    elif buysomething is True:
                        chat(s, channel, "/w %s %s" % (self.name, self.location.shopclosingbuy))
                    break
            self.inshop = False

    def training(self, s, channel):
        if self.location.hastrainer is False:
            chat(s, channel, "/w %s There is no trainer in %s!" % (self.name, self.location.name))
        elif self.inshop is True:
            chat(s, channel, "/w %s You can't train while shopping!" % (self.name))
        elif self.inencounter is True:
            chat(s, channel, "/w %s You can't train during an encounter!" % (self.name))
        elif self.intrainer is True:
            chat(s, channel, "/w %s You are already training!" % (self.name))
        else:
            self.intrainer = True
            chat(s, channel, "/w %s %s" % (self.name, self.location.traineropening))
            chat(s, channel, "/w %s You have %s Potential! What would you like to do? (!commands)" % (self.name, self.potential))
            self.lastwhisper = ''
            rumorcount = 0
            while True:
                if self.lastwhisper == "!commands":
                    chat(s, channel, "/w %s !train <attribute> <numberofpoints>, !learn <spell name|skill name>, !examine <spell name|skill name>, \
                                            !list <spells|skills>, !respec, !rumors, !leave" % (self.name))
                    self.lastwhisper = ''
                elif self.lastwhisper[:7] == "!train ":
                    if self.lastwhisper[7:].find(' ') != -1:
                        attribute, value = self.lastwhisper[7:].split(' ')
                        attribute = attribute.lower()
                        if is_number(value) is True:
                            value = int(value)
                            if attribute in ['vigor', 'power', 'finesse', 'guard', 'will', 'magic', 'luck', 'speed'] and value <= self.potential:
                                if attribute == 'vigor':
                                    self.vigor += value
                                    self.maxlife += (value * 4)
                                    self.life += (value * 4)
                                    self.respecpoints += value
                                    self.potential -= value
                                    chat(s, channel, "/w %s You gained %s Vigor and %s Life!" % (self.name, value, (value * 4)))
                                elif attribute == 'power':
                                    self.power += value
                                    self.respecpoints += value
                                    self.potential -= value
                                    chat(s, channel, "/w %s You gained %s Power!" % (self.name, value))
                                elif attribute == 'finesse':
                                    self.finesse += value
                                    self.maxfocus += value
                                    self.focus += value
                                    self.respecpoints += value
                                    self.potential -= value
                                    chat(s, channel, "/w %s You gained %s Finesse and %s Focus!" % (self.name, value, value))
                                elif attribute == 'guard':
                                    self.guard += value
                                    self.respecpoints += value
                                    self.potential -= value
                                    chat(s, channel, "/w %s You gained %s Guard!" % (self.name, value))
                                elif attribute == 'will':
                                    self.will += value
                                    self.respecpoints += value
                                    self.potential -= value
                                    chat(s, channel, "/w %s You gained %s Will!" % (self.name, value))
                                elif attribute == 'speed':
                                    self.speed += value
                                    self.respecpoints += value
                                    self.potential -= value
                                    chat(s, channel, "/w %s You gained %s Speed!" % (self.name, value))
                                elif attribute == 'magic':
                                    self.magic += value
                                    self.maxmana += value
                                    self.mana += value
                                    self.respecpoints += value
                                    self.potential -= value
                                    chat(s, channel, "/w %s You gained %s Magic and %s Mana!" % (self.name, value, value))
                                elif attribute == 'luck':
                                    self.luck += value
                                    self.respecpoints += value
                                    self.potential -= value
                                    chat(s, channel, "/w %s You gained %s Luck!" % (self.name, value))
                                chat(s, channel, "/w %s You have %s Potential remaining!" % (self.name, self.potential))
                            elif value > self.potential:
                                chat(s, channel, "/w %s You don't have enough potential for that!" % (self.name))
                            else:
                                chat(s, channel, "/w %s You need to input an attribute and a number of points (example: !train power 3 )!" % (self.name))
                        else:
                            chat(s, channel, "/w %s You need to input an attribute and a number of points (example: !train power 3 )!" % (self.name))
                    else:
                        chat(s, channel, "/w %s You need to input an attribute and a number of points (example: !train power 3 )!" % (self.name))
                    self.lastwhisper = ''
                    self.save()
                elif self.lastwhisper[:7] == "!learn ":
                    if self.location.name == 'Prison of Hope':
                        chat(s, channel, "/w %s I am afraid my frailty prevents me from teaching you some of my greater techniques." % (self.name))
                    else:
                        itemname = self.lastwhisper[7:]
                        if itemname not in ITEM:
                            chat(s, channel, "/w %s %s is not a spell nor skill." % (self.name))
                        else:
                            itemfound = False
                            for item in self.location.traineritem:
                                if item == itemname:
                                    if item not in self.skills and item not in self.spells:
                                        if (TECH[itemname].prereq in self.skills or TECH[itemname].prereq in self.skills) or TECH[itemname].prereq is None:
                                            if self.potential >= TECH[itemname].potentialcost:
                                                self.potential -= TECH[itemname].potentialcost
                                                self.respecpoints += TECH[itemname].potentialcost
                                                if TECH[itemname].type == 'Spell':
                                                    self.spells.append(TECH[itemname])
                                                else:
                                                    self.skills.append(TECH[itemname])
                                                chat(s, channel, "/w %s You learned %s for %s Potential!" % (self.name, itemname, ITEM[itemname].price))
                                                self.save()
                                                chat(s, channel, "/w %s You have %s Potential left!" % (self.name, self.potential))
                                            else:
                                                chat(s, channel, "/w %s You don't have enough Potential!" % (self.name))
                                        else:
                                            chat(s, channel, "/w %s You need to learn %s before I can teach you %s." % (self.name, TECH[itemname].prereq, itemname))
                                    else:
                                        chat(s, channel, "/w %s I can't teach you what you already know!" % (self.name))
                                    itemfound = True
                                    break
                            if itemfound is False:
                                chat(s, channel, "/w %s Sorry, I can't teach %s to you." % (self.name, itemname))
                    self.lastwhisper = ''
                elif self.lastwhisper[:9] == "!examine ":
                    itemname = self.lastwhisper[9:]
                    if itemname not in TECH:
                        chat(s, channel, "/w %s %s is neither a spell nor skill." % (self.name, itemname))
                    else:
                        inventorylist = [item.name for item in self.skills] + [item.name for item in self.spells]
                        examinelist = self.location.traineritem + inventorylist
                        if itemname in examinelist:
                            chat(s, channel, "/w %s %s" % (self.name, TECH[itemname].description))
                        else:
                            chat(s, channel, "/w %s No one around knows that spell or skill..." % (self.name))
                    self.lastwhisper = ''
                elif self.lastwhisper[:6] == "!list ":
                    if self.location.name == 'Prison of Hope':
                        chat(s, channel, "/w %s I am afraid my frailty prevents me from teaching you some of my greater techniques." % (self.name))
                    else:
                        listname = self.lastwhisper[6:]
                        trainerdict = {}
                        if listname in ['spells', 'skills']:
                            typestring = listname.capitalize()
                            for item in self.location.traineritem:
                                if TECH[item].typeof == typestring:
                                    trainerdict[item] = TECH[item].potentialcost
                            liststring = ''
                            for item in trainerdict:
                                liststring += ('%s: %s, ' % (item, trainerdict[item]))
                            liststring = liststring[:-2]
                            print('Liststring = %s' % liststring)
                            chat(s, channel, "/w %s %s" % (self.name, liststring))
                        else:
                            chat(s, channel, "/w %s That list does not exist!" % (liststring))
                    self.lastwhisper = ''
                elif self.lastwhisper == "!rumors":
                    chat(s, channel, "/w %s %s" % (self.name, self.location.trainerrumor[rumorcount]))
                    if rumorcount < len(self.location.trainerrumor) - 1:
                        rumorcount += 1
                    self.lastwhisper = ''
                elif self.lastwhisper == "!respec":
                    chat(s, channel, "/w %s Are you sure you wish to return all your potential? \
                                            You will have to relearn all your spells and skills as well as retrain all of your attributes. \
                                            Also, it's not cheap at 2500 ides (!accept|!decline)." % self.name)
                    while True:
                        if self.lastwhisper == '!accept' and self.money >= 2500:
                            self.potential = self.potential + self.respecpoints
                            self.respecpoints = 0
                            self.maxlife = 40 + (self.level - 1) * 10
                            self.life = 40 + (self.level - 1) * 10
                            self.maxmana = 10
                            self.mana = 10
                            self.maxfocus = 10
                            self.focus = 10
                            self.vigor = 10
                            self.power = 10
                            self.finesse = 10
                            self.will = 10
                            self.guard = 10
                            self.magic = 10
                            self.speed = 10
                            self.luck = 10
                            self.skills = []
                            self.spells = []
                            self.clearStatChanges()
                            self.money -= 2500
                            self.save()
                            chat(s, channel, "/w %s Your mind and body feel the same now as when you first picked up your sword and decided to carve your own fate. \
                                                    A world of potential is laid before you. (Don't forget to spend your points!)" % (self.name))
                            break
                        elif self.lastwhisper == '!accept':
                            chat(s, channel, "/w %s You cannot afford this special training." % (self.name))
                            break
                        elif self.lastwhisper == '!decline':
                            chat(s, channel, "/w %s Ahh, maybe another time then." % (self.name))
                            break
                    self.lastwhisper = ''
                elif self.lastwhisper == '!leave':
                    chat(s, channel, "/w %s %s" % (self.name, self.location.trainerclosing))
                    break
            self.intrainer = False

    def itemAmbiguity(self, itemname):
        itemwords = [i.name for i in self.inventory] + [self.weapon.name, self.shield.name, self.armor.name, self.charm.name]
        c = Counter(itemwords)
        if c[itemname] > 1:
            return True
        return False

    def useItem(self, item, s, channel):
        if self.inencounter is False:
            if ITEM[item].worlditem is True:
                if item not in ITEM:
                    chat(s, channel, "/w %s Such a thing has nary been spotted in Iodra." % (self.name))
                elif ITEM[item] in self.inventory:
                    chat(s, channel, ("/w %s You use %s!" % (self.name, ITEM[item].name)))
                    chat(s, channel, ("/w %s %s!" % (self.name, ITEM[item].usedtext)))
                    self.life = min(self.life + ceil(self.get('maxlife') * (ITEM[item].curelife / 100)), self.get('maxlife'))
                    self.focus = min(self.focus + ceil(self.get('maxfocus') * (ITEM[item].curefocus / 100)), self.get('maxfocus'))
                    self.mana = min(self.mana + ceil(self.get('maxmana') * (ITEM[item].curemana / 100)), self.get('maxmana'))
                    if ITEM[item].name == 'Briarmist Pellet':
                        t = threading.Thread(target=encounterTimer, args=([PLAYER[self.name]], s, channel, False, Encounter.NORMAL, '', False))
                        t.start()
                    for items in self.inventory:
                        if items.name == item:
                            self.inventory.remove(items)
                            break
                else:
                    chat(s, channel, "/w %s You don't have that item." % (self.name))
            else:
                chat(s, channel, "/w %s You cannot use this item in this way." % (self.name))

    def examineItem(self, item, s, channel, PLAYER):
        if self.inshop is False and self.intrainer is False:
            showitem = False
            if item in PLAYER:
                copyofplayer = copy.copy(PLAYER[item])
                copyofplayer.clearStatChanges()
                chat(s, channel, "/w %s %s - Level: %s - Life: %s - Will:%s - Power: %s - Guard: %s - Speed: %s - Luck: %s - Ides: %s - EXP: %s/%s"
                     % (self.name, copyofplayer.name, copyofplayer.level, (copyofplayer.maxlife + copyofplayer.statchange['maxlife']),
                        (copyofplayer.maxmana + copyofplayer.statchange['maxmana']), (copyofplayer.maxfocus + copyofplayer.statchange['maxfocus']),
                        copyofplayer.vigor, (copyofplayer.power + copyofplayer.statchange['power']),
                        (copyofplayer.finesse + copyofplayer.statchange['finesse']), (copyofplayer.will + copyofplayer.statchange['will']),
                        (copyofplayer.guard + copyofplayer.statchange['guard']), (copyofplayer.speed + copyofplayer.statchange['speed']),
                        (copyofplayer.luck + copyofplayer.statchange['luck']), copyofplayer.money, copyofplayer.exp, (copyofplayer.level ** 2)))
                del copyofplayer
                showitem = True
            elif item not in ITEM:
                chat(s, channel, "/w %s Such a thing has nary been spotted in Iodra." % (self.name))
            elif ITEM[item] in self.inventory:
                chat(s, channel, ("/w %s %s" % (self.name, ITEM[item].description)))
                showitem = True
            if item == self.weapon.name and showitem is False:
                chat(s, channel, ("/w %s %s" % (self.name, self.weapon.description)))
                showitem = True
            elif item == self.shield.name and showitem is False:
                chat(s, channel, ("/w %s %s" % (self.name, self.shield.description)))
                showitem = True
            elif item == self.armor.name and showitem is False:
                chat(s, channel, ("/w %s %s" % (self.name, self.armor.description)))
                showitem = True
            elif item == self.charm.name and showitem is False:
                chat(s, channel, ("/w %s %s" % (self.name, self.charm.description)))
                showitem = True
            if showitem is False:
                chat(s, channel, ("/w %s You can't find the item to examine..." % (self.name)))

    def levelUp(self, s, channel, droplist):
        while self.exp >= self.level ** 2:
            self.exp -= self.level ** 2
            self.level += 1
            chat(s, channel, "/w %s You hit level %s! You gain 5 Potential and 10 Life!" % (self.name, self.level))
            globalchat(s, channel, "%s hit level %s!" % (self.name, self.level))
            self.potential += 5
            self.maxlife += 10
            self.life += 10
            if randint(1, 100) < self.luck:
                chat(s, channel, "/w %s What luck! You gain 1 extra Potential!" % (self.name))
                self.potential += 1
        self.drops(s, channel, droplist)

    def drops(self, s, channel, droplist):
        for item in droplist:
            if randint(1, 100) <= (droplist[item] + (100 - droplist[item]) * (0.01 * self.encountersinsamearea) + (self.luck / 15)):
                chat(s, channel, ("/w %s You find %s!" % (self.name, item)))
                if self.checkinventoryslots(s, channel):
                    self.inventory.insert(0, ITEM[item])
                    chat(s, channel, ("/w %s You take %s!" % (self.name, item)))
                else:
                    chat(s, channel, ("/w %s You forfeit %s." % (self.name, item)))
        if self.life > (self.maxlife + self.statchange['maxlife']) * .75:
            chat(s, channel, ("/w %s With a feeling of triumph, you press on." % (self.name)))
        elif self.life > (self.maxlife + self.statchange['maxlife']) * .5:
            chat(s, channel, ("/w %s Wounded, but not discouraged, you press on." % (self.name)))
        elif self.life > (self.maxlife + self.statchange['maxlife']) * .25:
            chat(s, channel, ("/w %s After the trying conflict, you pick yourself up and press on." % (self.name)))
        else:
            chat(s, channel, ("/w %s Holding on by a thread, you drag yourself to your feet and press on." % (self.name)))
        self.inencounter = False
        self.save()

    def checkinventoryslots(self, s, channel):
        if len(self.inventory) < 8:
            return True
        return self.fullinventory(s, channel)

    def fullinventory(self, s, channel):
        chat(s, channel, ("/w %s Your inventory is full! Discard something now or say !forfeit" % (self.name)))
        self.lastwhisper = ''
        while True:
            if self.lastwhisper[:8] == '!discard':
                if len(self.inventory) < 8:
                    time.sleep(1)
                    return True
            elif self.lastwhisper == '!forfeit':
                return False

    def discarditem(self, s, channel, itemname):
        if itemname not in ITEM:
            chat(s, channel, "/w %s Such a thing has nary been spotted in Iodra." % (self.name))
        elif ITEM[itemname] in self.inventory:
            self.inventory.remove(ITEM[itemname])
            chat(s, channel, "/w %s You discard %s." % (self.name, itemname))
        elif itemname in [self.weapon.name, self.shield.name, self.armor.name, self.charm.name]:
            chat(s, channel, "/w %s You can't discard something you have equipped!" % (self.name))
        else:
            chat(s, channel, "/w %s You don't have %s!" % (self.name, itemname))

    def equipitem(self, s, channel, itemname):
        if self.inencounter:
            chat(s, channel, "/w %s You don't have time for that!" % (self.name))
        else:
            if itemname not in ITEM:
                chat(s, channel, "/w %s Such a thing has nary been spotted in Iodra." % (self.name))
            elif ITEM[itemname] in self.inventory:
                item = ITEM[itemname]
                if item.typeof == 'Weapons':
                    self.inventory.remove(item)
                    self.inventory.insert(0, self.weapon)
                    self.weapon = item
                    chat(s, channel, ("/w %s You equip %s" % (self.name, itemname)))
                    return
                elif item.typeof == 'Armor':
                    self.inventory.remove(item)
                    self.inventory.insert(0, self.armor)
                    self.armor = item
                    chat(s, channel, ("/w %s You equip %s" % (self.name, itemname)))
                    return
                elif item.typeof == 'Shields':
                    self.inventory.remove(item)
                    self.inventory.insert(0, self.shield)
                    self.shield = item
                    chat(s, channel, ("/w %s You equip %s" % (self.name, itemname)))
                    return
                elif item.typeof == 'Charms':
                    self.inventory.remove(item)
                    self.inventory.insert(0, self.charm)
                    self.charm = item
                    chat(s, channel, ("/w %s You equip %s" % (self.name, itemname)))
                    return
                else:
                    chat(s, channel, ("/w %s %s cannot be equipped!" % (self.name, itemname)))
            chat(s, channel, ("/w %s You don't have %s!" % (self.name, itemname)))

    def give(self, user, Change, Amount, s, channel):
        Amount = int(Amount)
        if Change == 'ides':
            self.money += Amount
            chat(s, channel, ("/w %s Gave %s %s %s!" % (user, self.name, Amount, Change)))
            chat(s, channel, ("/w %s %s gave you %s %s!" % (self.name, user, Amount, Change)))
        elif Change == 'exp':
            self.exp += Amount
            chat(s, channel, ("/w %s Gave %s %s %s!" % (user, self.name, Amount, Change)))
            chat(s, channel, ("/w %s %s gave you %s %s!" % (self.name, user, Amount, Change)))
        elif Change == 'maxlife':
            self.maxlife += Amount
            chat(s, channel, ("/w %s Gave %s %s %s!" % (user, self.name, Amount, Change)))
            chat(s, channel, ("/w %s %s gave you %s %s!" % (self.name, user, Amount, Change)))
        elif Change == 'power':
            self.power += Amount
            chat(s, channel, ("/w %s Gave %s %s %s!" % (user, self.name, Amount, Change)))
            chat(s, channel, ("/w %s %s gave you %s %s!" % (self.name, user, Amount, Change)))
        elif Change == 'guard':
            self.guard += Amount
            chat(s, channel, ("/w %s Gave %s %s %s!" % (user, self.name, Amount, Change)))
            chat(s, channel, ("/w %s %s gave you %s %s!" % (self.name, user, Amount, Change)))
        elif Change == 'speed':
            self.speed += Amount
            chat(s, channel, ("/w %s Gave %s %s %s!" % (user, self.name, Amount, Change)))
            chat(s, channel, ("/w %s %s gave you %s %s!" % (self.name, user, Amount, Change)))
        elif Change == 'luck':
            self.luck += Amount
            chat(s, channel, ("/w %s Gave %s %s %s!" % (user, self.name, Amount, Change)))
            chat(s, channel, ("/w %s %s gave you %s %s!" % (self.name, user, Amount, Change)))
        else:
            chat(s, channel, ("/w %s Not able to give %s" % (user, Change)))

    def playerTurn(self, charactersinencounter, playersinencounter, s, channel, target, escape):
        if self.lastwhisper == '!fight' or self.lastwhisper == '!attack':
            self.damageRoll(target, charactersinencounter, playersinencounter, s, channel)
            self.energy -= self.weapon.energyuse
            if self.energy >= 1000 and target.life > 0:
                chat(s, channel, ("/w %s You are at %s energy!" % (self.name, self.energy)))
            self.lastwhisper = ''
            self.chargecount = 1
        elif self.lastwhisper == '!check':
            time.sleep(1)
            for chatter in playersinencounter:
                if chatter.name == self.name:
                    globalchat(s, channel, ("/w %s %s - Life: %s - Will: %s - Power: %s - Guard: %s - Speed: %s - Luck: %s - %s" %
                                            (self.name, target.name, target.life, (target.will + target.statchange['will']),
                                             (target.power + target.statchange['power']), (target.guard + target.statchange['guard']),
                                             (target.speed + target.statchange['speed']),
                                             (target.luck + target.statchange['luck']), target.description)))
                elif chatter.name == target.name:
                    globalchat(s, channel, "/w %s %s is checking you out!" % (chatter.name, self.name))
                else:
                    globalchat(s, channel, "/w %s %s is checking out %s!" % (chatter.name, self.name, target.name))
            self.energy -= 100
            if self.energy >= 1000 and target.life > 0:
                chat(s, channel, ("/w %s You are at %s energy!" % (self.name, self.energy)))
            self.lastwhisper = ''
        elif self.lastwhisper[:5] == '!use ':
            itemname = self.lastwhisper[5:]
            if itemname not in ITEM:
                chat(s, channel, "/w %s Such a thing has nary been spotted in Iodra." % (self.name))
            elif ITEM[itemname] in self.inventory:
                item = ITEM[itemname]
                if item.battleitem is False:
                    chat(s, channel, "/w %s You can't use %s in this way." % (self.name, itemname))
                else:
                    time.sleep(1)
                    for chatter in playersinencounter:
                        if chatter.name == self.name:
                            globalchat(s, channel, "/w %s %s" % (self.name, item.usedtext))
                        else:
                            globalchat(s, channel, "/w %s %s used %s!" % (chatter.name, self.name, item.name))
                    self.energy -= item.energyuse
                    self.life = min(self.life + ceil(self.get('maxlife') * (item.curelife / 100)), self.get('maxlife'))
                    self.focus = min(self.focus + ceil(self.get('maxfocus') * (item.curefocus / 100)), self.get('maxfocus'))
                    self.mana = min(self.mana + ceil(self.get('maxmana') * (item.curemana / 100)), self.get('maxmana'))
                    if item.curestatus == 0:
                        self.clearStatusEffects()
                        self.clearStatChanges()
                    for stat in self.statchange:
                        self.statchange[stat] += item.buff[stat]
                    target.evaluateStatus(playersinencounter, s, channel, item.statusinflict, item.statuschance)
                    self.inventory.remove(item)
                    if itemname == 'Flask of Shadows':
                        chat(s, channel, "/w %s You escape!" % (self.name))
                        self.runaway += 1
                        self.lastwhisper = ''
                        return True
            if self.energy >= 1000 and target.life > 0:
                chat(s, channel, "/w %s You are at %s energy!" % (self.name, self.energy))
            self.lastwhisper = ''
        elif self.lastwhisper == '!escape':
            if escape is True:
                escaperoll = randint(1, 100)
                escapechance = ((self.life / self.get('maxlife')) * (self.get('speed') / target.get('speed')) + self.get('luck') * 0.002) * 100
                if escapechance >= escaperoll:
                    chat(s, channel, "/w %s You escape!" % (self.name))
                    self.runaway += 1
                    self.lastwhisper = ''
                    return True
                else:
                    chat(s, channel, "/w %s You fail to escape!" % (self.name))
                    self.energy -= 200
                    if self.energy >= 1000 and target.life > 0:
                        chat(s, channel, "/w %s You are at %s energy!" % (self.name, self.energy))
            else:
                chat(s, channel, "/w %s You can not escape!" % (self.name))
            self.lastwhisper = ''
            return False

    def enemyTurn(self, charactersinencounter, playersinencounter, s, channel):
        target = random.choice(playersinencounter)
        if target is not None:
            self.damageRoll(target, charactersinencounter, playersinencounter, s, channel)
        self.energy -= self.enemyenergyuse


# -----------------------------------------------------------------------------


class Item:

    def __init__(self, name):
        global ITEM
        ITEM[name] = self
        self.name = name
        self.typeof = ''
        self.is2handed = False
        self.isshield = False
        self.isarmor = False
        self.ischarm = False
        self.isconsumable = False
        self.energyuse = 400
        self.numofuses = 1
        self.curelife = 0
        self.curefocus = 0
        self.curemana = 0
        self.curestatus = -1     # -1 = no cure, 0 =  cure all, 1 = cure poison, 2 = cure toxic, 3 = cure blind, 4 = cure panic
        self.maxstacksize = 1
        self.statusinflict = 0   # -1 = random status, 0 = no status, 1+ look at status list
        self.statuschance = 0
        self.price = 0
        self.battleitem = False
        self.worlditem = False
        self.description = ''
        self.usedtext = ''
        self.damagereceivetext = 'Damage Recieve text missing {player} {damage}'
        self.damagedealtext = 'Damage Deal text missing {player} {damage}'
        self.critreceivetext = 'Crit Recieve text missing {player} {damage}'
        self.critdealtext = 'Crit Deal text missing {player} {damage}'
        self.nodamagedealtext = 'No Damage Deal Text Missing'
        self.nodamagereceivetext = 'No Damage Recieve Text Missing'
        self.buff = {'maxlife': 0,
                     'maxmana': 0,
                     'maxfocus': 0,
                     'power': 0,
                     'finesse': 0,
                     'will': 0,
                     'guard': 0,
                     'magic': 0,
                     'speed': 0,
                     'luck': 0,
                     'critchance': 0,
                     }
        self.buffelementalatk = {'Fire': 0,
                                 'Elec': 0,
                                 'Water': 0,
                                 'Earth': 0,
                                 'Psyche': 0,
                                 }
        self.buffelementaldef = {'Fire': 0,
                                 'Elec': 0,
                                 'Water': 0,
                                 'Earth': 0,
                                 'Psyche': 0,
                                 }


def loadItems(folder):
    for filename in os.listdir(folder):
        if filename == "WIP":
            continue
        fileobj = open("RPG/Items/%s" % filename)
        data = fileobj .readlines()
        fileobj .close()
        currentItem = None
        for line in data:
            if line.strip() == '':
                continue
            parsed = line.split(': ', 1)
            if parsed[0] == 'name':
                name = eval(parsed[1])
                currentItem = Item(name)
                currentItem.typeof = filename[:-4]
            elif '.' in parsed[0]:
                attr, key = tuple(parsed[0].split('.', 1))
                val = parsed[1]
                dct = getattr(currentItem, attr)
                dct[key] = eval(val)
            else:
                attr = parsed[0]
                val = parsed[1]
                setattr(currentItem, attr, eval(val))


def getItem(itemname):
    global ITEM
    if itemname in ITEM:
        return ITEM[itemname]
    else:
        return None


# -----------------------------------------------------------------------------


class Location:

    def __init__(self, name):
        global LOCATION
        LOCATION[name] = self
        self.boss = None
        self.name = name
        self.traveltext = "Missing traveltext"
        self.surroundings = "Missing surroundings"
        self.encounterchance = {}
        self.hasshop = False
        self.hastrainer = False

        self.shopopening = 'Missing opening'
        self.shoprumor = []
        self.shopitem = []
        self.shopclosingbuy = 'Missing closing'
        self.shopclosingnobuy = 'Missing closing'

        self.traineropening = 'Missing opening'
        self.trainerrumor = []
        self.traineritem = []
        self.trainerclosing = 'Missing closing'


def getLocation(locationname):
    global LOCATION
    if locationname in LOCATION:
        return LOCATION[locationname]
    else:
        return None


def loadLocations(folder):
    for filename in os.listdir(folder):
        if filename == "WIP":
            continue
        fileobj = open("RPG/Locations/%s" % filename)
        data = fileobj.readlines()
        fileobj.close()
        location = Location(filename[:-4])
        loadEnemies = False
        currentEnemy = None
        for line in data:
            if line.strip() == '':
                continue
            elif line.strip() == 'ENEMYLIST':
                loadEnemies = True
                continue
            parsed = line.split(': ', 1)
            if loadEnemies and parsed[0] == 'name':
                name = eval(parsed[1])
                currentEnemy = Character(name)
                currentEnemy.setMonster()
            elif '.' in parsed[0]:
                attr, key = tuple(parsed[0].split('.', 1))
                val = parsed[1]
                if loadEnemies:
                    dct = getattr(currentEnemy, attr)
                else:
                    dct = getattr(location, attr)
                dct[key] = eval(val)
            elif parsed[0][-1] == '+':
                attr = parsed[0][:-1]
                val = parsed[1]
                lst = getattr(location, attr)
                lst.append(eval(val))
            else:
                attr = parsed[0]
                val = parsed[1]
                if loadEnemies:
                    setattr(currentEnemy, attr, eval(val))
                else:
                    setattr(location, attr, eval(val))


# -----------------------------------------------------------------------------


class Tech:

    def __init__(self, name):
        global TECH
        TECH[name] = self
        self.name = name
        self.type = ''
        self.prereq = None
        self.energyuse = 150
        self.pointuse = 0
        self.curelife = 0
        self.dmg = 0
        self.energydmg = 0
        self.dmgtype = 'Physical'
        self.statusinflict = 0
        self.statuschance = 0
        self.description = 'Description Missing?'
        self.dealtext = 'DealText Missing? {player} {damage}'
        self.receivetext = 'Receivetext Missing? {player} {damage}'
        self.buff = {'maxlife': 0,
                     'maxmana': 0,
                     'maxfocus': 0,
                     'power': 0,
                     'finesse': 0,
                     'will': 0,
                     'guard': 0,
                     'magic': 0,
                     'speed': 0,
                     'luck': 0,
                     'critchance': 0,
                     }
        self.debuff = {'maxlife': 0,
                       'maxmana': 0,
                       'maxfocus': 0,
                       'power': 0,
                       'finesse': 0,
                       'will': 0,
                       'guard': 0,
                       'magic': 0,
                       'speed': 0,
                       'luck': 0,
                       'critchance': 0,
                       }
        self.buffelementalatk = {'Fire': 0,
                                 'Elec': 0,
                                 'Water': 0,
                                 'Earth': 0,
                                 'Psyche': 0,
                                 }
        self.buffelementaldef = {'Fire': 0,
                                 'Elec': 0,
                                 'Water': 0,
                                 'Earth': 0,
                                 'Psyche': 0,
                                 }


def loadTech(folder):
    for filename in os.listdir(folder):
        if filename == "WIP":
            continue
        fileobj = open("RPG/Tech/%s" % filename)
        data = fileobj.readlines()
        fileobj.close()
        currentItem = None
        for line in data:
            if line.strip() == '':
                continue
            parsed = line.split(': ', 1)
            if parsed[0] == 'name':
                name = eval(parsed[1])
                currentItem = Tech(name)
                currentItem.typeof = filename[:-4]
            elif '.' in parsed[0]:
                attr, key = tuple(parsed[0].split('.', 1))
                val = parsed[1]
                dct = getattr(currentItem, attr)
                dct[key] = eval(val)
            else:
                attr = parsed[0]
                val = parsed[1]
                setattr(currentItem, attr, eval(val))


# -----------------------------------------------------------------------------


def sortEncounterList(self):
    return self.energy * 10000 + self.speed * 100 + self.luck


def startRPG(user, s, channel):
    if user not in PLAYER:
        newchar = Character(user)
        newchar.setPlayer()
        newchar.save()
        chat(s, channel, ("%s has joined the game at level 1!" % user))
        chat(s, channel, (('/w %s Welcome to the world of Iodra. ' +
                           'You awake in your cell in the Prison of Hope, a name that mocks all held within its walls. ' +
                           'Imprisoned under ostensibly false charges, you seek one thing... Escape, at all costs. ' +
                           'It would seem fate has favored you, for a guard has misplaced his weapon nearby... ' +
                           '(Check below the stream for RPG Instructions if you\'re unsure what to do next.)') % user))
    else:
        chat(s, channel, ("/w %s You are already in the game!" % user))


def initializeGame():
    loadItems("RPG/Items")
    loadLocations("RPG/Locations")
    loadTech("RPG/Tech")
    for user in os.listdir('RPG\Players'):
        if user == 'Deleted':
            continue
        user = user[:-4]
        loadchar = Character(user)
        loadchar.load()
    print("PLAYER: %s\n" % [k for k in PLAYER])
    print("MONSTER: %s\n" % [k for k in MONSTER])
    print("ITEM: %s\n" % [k for k in ITEM])
    print("TECH: %s\n" % [k for k in TECH])
    print("LOCATION: %s\n" % [k for k in LOCATION])


def leaderBoards(user, board, s, channel):
    global leaderboardtimer
    if time.time() - 120 > leaderboardtimer:
        newlist = {}
        admins = ["vorondur", "davidnotdave", "jrhard771"]
        badboard = False
        for player in PLAYER:
            if board == 'level' and player.name not in admins:
                newlist[player] = PLAYER[player].level
            elif board == 'life' and player.name not in admins:
                newlist[player] = PLAYER[player].maxlife
            elif board == 'mana' and player.name not in admins:
                newlist[player] = PLAYER[player].maxmana
            elif board == 'focus' and player.name not in admins:
                newlist[player] = PLAYER[player].maxfocus
            elif board == 'vigor' and player.name not in admins:
                newlist[player] = PLAYER[player].vigor
            elif board == 'power' and player.name not in admins:
                newlist[player] = PLAYER[player].power
            elif board == 'finesse' and player.name not in admins:
                newlist[player] = PLAYER[player].finesse
            elif board == 'will' and player.name not in admins:
                newlist[player] = PLAYER[player].will
            elif board == 'guard' and player.name not in admins:
                newlist[player] = PLAYER[player].guard
            elif board == 'magic' and player.name not in admins:
                newlist[player] = PLAYER[player].magic
            elif board == 'speed' and player.name not in admins:
                newlist[player] = PLAYER[player].speed
            elif board == 'luck' and player.name not in admins:
                newlist[player] = PLAYER[player].luck
            elif board == 'ides' and player.name not in admins:
                newlist[player] = PLAYER[player].money
            elif board == 'kills' and player.name not in admins:
                newlist[player] = PLAYER[player].kills
            elif board == 'deaths' and player.name not in admins:
                newlist[player] = PLAYER[player].deaths
            elif board == 'timeouts' and player.name not in admins:
                newlist[player] = PLAYER[player].timeouts
            elif board == 'runaways' and player.name not in admins:
                newlist[player] = PLAYER[player].runaway
            elif board == 'killstreak' and player.name not in admins:
                newlist[player] = PLAYER[player].killstreak
            else:
                chat(s, channel, "Leaderboards for that stat do not exist!")
                badboard = True
                break
        sortedlist = sorted(newlist.items(), key=operator.itemgetter(1))
        sortedlist.reverse()
        while len(sortedlist) < 5:
            sortedlist.append('No Data')
        if badboard is False:
            leaderboardtimer = time.time()
            chat(s, channel, ("Top 5 players in %s are:" % board))
            chat(s, channel, ("1. %s" % (leaderBoardsSorting(sortedlist[0]))))
            chat(s, channel, ("2. %s" % (leaderBoardsSorting(sortedlist[1]))))
            chat(s, channel, ("3. %s" % (leaderBoardsSorting(sortedlist[2]))))
            chat(s, channel, ("4. %s" % (leaderBoardsSorting(sortedlist[3]))))
            chat(s, channel, ("5. %s" % (leaderBoardsSorting(sortedlist[4]))))
    else:
        slotTimerTimeleft = round((leaderboardtimer + 120.0) - time.time())
        slotTimerminutes = round((slotTimerTimeleft / 60) - 0.5)
        slotTimerseconds = round(slotTimerTimeleft % 60)
        if slotTimerminutes > 0:
            chat(s, channel, ("/w %s Leaderboards can only be shown every 2 minutes! (%s minute(s) and %s second(s) left!)" % (user, slotTimerminutes, slotTimerseconds)))
        else:
            chat(s, channel, ("/w %s Leaderboards can only be shown every 2 minutes! (%s second(s) left!)" % (user, slotTimerseconds)))


def leaderBoardsSorting(listtuple):
    string = ''
    for i in listtuple:
        if listtuple == 'No Data':
            string = 'No Data'
            continue
        else:
            if string.find(',') >= 0:
                string += str(i)
            else:
                string += (str(i) + ', ')
    return string


def raidlobby(s, channel, boss):
    chat(s, channel, "Raid Boss %s has come to fight! Use '!joinraid' to get ready to enter the battle!" % (boss))
    joinlist = []
    starttimer = time.time()
    warning1 = False
    warning2 = False
    warning3 = False
    lobby = True
    while lobby is True:
        for player in PLAYER:
            if PLAYER[player].lastmessage == '!joinraid' or PLAYER[player].lastwhisper == '!joinraid':
                if PLAYER[player].inencounter is False:
                    if PLAYER[player] not in joinlist:
                        joinlist.append(PLAYER[player])
                        chat(s, channel, "/w %s You have joined the list to fight %s! You can leave with !leaveraid." % (PLAYER[player].name, boss))
                        PLAYER[player].lastmessage = ''
                        PLAYER[player].lastwhisper = ''
                        print(joinlist)
                    else:
                        chat(s, channel, "/w %s You are already in the list!" % (PLAYER[player].name))
                        PLAYER[player].lastmessage = ''
                        PLAYER[player].lastwhisper = ''
                else:
                    chat(s, channel, "/w %s You are already in an encounter!" % (PLAYER[player].name))
                    PLAYER[player].lastmessage = ''
                    PLAYER[player].lastwhisper = ''
            elif PLAYER[player] in joinlist and (PLAYER[player].lastmessage == '!leaveraid' or PLAYER[player].lastwhisper == '!leaveraid'):
                joinlist.remove(PLAYER[player])
                chat(s, channel, "/w %s You have left the list to fight %s..." % (PLAYER[player].name, boss))
                PLAYER[player].lastmessage = ''
                PLAYER[player].lastwhisper = ''
                print(joinlist)
        if time.time() - 30 > starttimer and warning1 is False:
            chat(s, channel, "5 minutes left to join %s fight! Current # of players: %s" % (boss, len(joinlist)))
            warning1 = True
        if time.time() - 42 > starttimer and warning2 is False:
            chat(s, channel, "3 minutes left to join %s fight! Current # of players: %s" % (boss, len(joinlist)))
            warning2 = True
        if time.time() - 54 > starttimer and warning3 is False:
            chat(s, channel, "1 minute left to join %s fight! Current # of players: %s" % (boss, len(joinlist)))
            warning3 = True
        if time.time() - 60 > starttimer:
            chat(s, channel, "Time's up! The encounter with %s has begun!" % (boss))
            if len(joinlist) > 0:
                encounter(joinlist, s, channel, False, Encounter.RAID, boss, False)
                lobby = False
            else:
                chat(s, channel, "Nobody showed up so %s got bored and left..." % (boss))
                lobby = False


def pvplobby(s, channel):
    chat(s, channel, "PvP Lobby Opened! Use !joinpvp to join!")
    joinlist = []
    lobby = True
    while lobby is True:
        for player in PLAYER:
            if PLAYER[player].lastmessage == '!joinpvp' or PLAYER[player].lastwhisper == '!joinpvp':
                if PLAYER[player].inencounter is False:
                    if PLAYER[player] not in joinlist:
                        joinlist.append(PLAYER[player])
                        chat(s, channel, "PvP Lobby %s/2" % (len(joinlist)))
                        PLAYER[player].lastmessage = ''
                        PLAYER[player].lastwhisper = ''
                        print(joinlist)
                    else:
                        chat(s, channel, "/w %s You are already in the lobby!" % (PLAYER[player].name))
                        PLAYER[player].lastmessage = ''
                        PLAYER[player].lastwhisper = ''
                else:
                    chat(s, channel, "/w %s You are already in an encounter!" % (PLAYER[player].name))
                    PLAYER[player].lastmessage = ''
                    PLAYER[player].lastwhisper = ''
            if len(joinlist) == 2:
                encounter(joinlist, s, channel, False, Encounter.PVP, '', False)
                lobby = False


def encounterTimer(users, s, channel, testmode, encounterType, bossName, ambush):
    for character in users:
        if character.location.name not in hostilelocationlist:
            chat(s, channel, ("/w %s You can't get into encounters here!" % (character.name)))
        elif character.inencounter is False:
            if character.encountertimer + 300 > time.time() and testmode is False:
                slotTimerTimeleft = round((character.encountertimer + 300.0) - time.time())
                slotTimerminutes = round((slotTimerTimeleft / 60) - 0.5)
                slotTimerseconds = round(slotTimerTimeleft % 60)
                if slotTimerminutes > 0:
                    chat(s, channel, ("/w %s You can only do an encounter every 15 minutes! (%s minute(s) and %s second(s) left!)" % (character.name, slotTimerminutes, slotTimerseconds)))
                else:
                    chat(s, channel, ("/w %s You can only do an encounter every 15 minutes! (%s second(s) left!)" % (character.name, slotTimerseconds)))
            else:
                character.encountertimer = time.time()
                encounter(users, s, channel, testmode, encounterType, bossName, ambush)
        else:
            chat(s, channel, ("/w %s You are already in an encounter!" % (character.name)))


def loadenemy(location):
    encounterroll = randint(1, 100)
    for enemy in location.encounterchance:
        minchance, maxchance = location.encounterchance[enemy]
        if minchance <= encounterroll and maxchance >= encounterroll:
            return copy.deepcopy(MONSTER[enemy])


def encounter(users, s, channel, testmode, encounterType, bossName, ambush):
    playersinencounter = []
    charactersinencounter = []
    for user in users:
        playersinencounter.append(user)
        charactersinencounter.append(user)
        user.inencounter = True
        user.team = 1
        user.lastwhisper = ''
    if encounterType == Encounter.NORMAL:
        enemy = loadenemy(playersinencounter[0].location)
        charactersinencounter.append(enemy)
    elif encounterType == Encounter.BOSS:
        enemy = copy.deepcopy(MONSTER[playersinencounter[0].location.boss])
        charactersinencounter.append(enemy)
    elif encounterType == Encounter.RAID:
        enemy = copy.deepcopy(MONSTER[bossName])
        charactersinencounter.append(enemy)
    lastturn = ''
    escape = False
    encountertimestart = time.time()
    for character in charactersinencounter:
        character.energy = randint(400, 600)
    charactersinencounter.sort(key=sortEncounterList, reverse=True)
    if encounterType != Encounter.PVP:
        time.sleep(1)
        for chatter in playersinencounter:
            globalchat(s, channel, ("/w %s %s" % (chatter.name, enemy.opening)))
        time.sleep(1)
        for chatter in playersinencounter:
            globalchat(s, channel, ("/w %s You have encountered %s!" % (chatter.name, enemy.name)))
    else:
        chat(s, channel, "/w %s You are dueling %s!" % (playersinencounter[0].name, playersinencounter[1].name))
        chat(s, channel, "/w %s You are dueling %s!" % (playersinencounter[1].name, playersinencounter[0].name))
    endFight = False
    while True:
        turnlist = charactersinencounter.copy()
        for character in turnlist:
            newTurn = True
            playerCount = len(playersinencounter)
            enemyCount = len(charactersinencounter) - playerCount
            if encounterType == Encounter.PVP and playerCount <= 1:
                endFight = True
                break
            elif encounterType != Encounter.PVP and (playerCount == 0 or enemyCount == 0):
                endFight = True
                break
            elif escape is True:
                endFight = True
                break
            if character.energy < 1000:
                character.energyRecovery(playersinencounter, s, channel)
                continue
            else:
                character.statusDamage(charactersinencounter, playersinencounter, s, channel)
                if character.life <= 0:
                    continue
            while character.energy >= 1000:
                if character.status['Sleep']:
                    sleepRoll = randint(1, 10)
                    if sleepRoll > 3:
                        character.energy = 900
                        time.sleep(1)
                        for chatter in playersinencounter:
                            if character == chatter:
                                globalchat(s, channel, "/w %s You are asleep!" % chatter.name)
                            else:
                                globalchat(s, channel, "/w %s %s is asleep!" % (chatter.name, character.name))
                        break
                    else:
                        character.status['Sleep'] = False
                        time.sleep(1)
                        for chatter in playersinencounter:
                            if character == chatter:
                                globalchat(s, channel, "/w %s You woke up!" % chatter.name)
                            else:
                                globalchat(s, channel, "/w %s %s woke up!" % (chatter.name, character.name))
                if character.status['Paralysis']:
                    paralysisRoll = randint(1, 10)
                    if paralysisRoll > 5:
                        character.energy = 700
                        time.sleep(1)
                        for chatter in playersinencounter:
                            if character == chatter:
                                globalchat(s, channel, "/w %s You are paralyzed!" % chatter.name)
                            else:
                                globalchat(s, channel, "/w %s %s is paralyzed!" % (chatter.name, character.name))
                        break
                    else:
                        character.status['Paralysis'] = False
                        time.sleep(1)
                        for chatter in playersinencounter:
                            if character == chatter:
                                globalchat(s, channel, "/w %s You can move again!" % chatter.name)
                            else:
                                globalchat(s, channel, "/w %s %s can move again!" % (chatter.name, character.name))
                if character.status['Panic']:
                    panicRoll = randint(1, 10)
                    if panicRoll < 4:
                        character.energy = 900
                        time.sleep(1)
                        for chatter in playersinencounter:
                            if character == chatter:
                                globalchat(s, channel, "/w %s You panic and fumble your weapon!" % chatter.name)
                            else:
                                globalchat(s, channel, "/w %s %s is panicking!" % (chatter.name, character.name))
                        break
                    elif panicRoll == 10:
                        character.status['Panic'] = False
                        time.sleep(1)
                        for chatter in playersinencounter:
                            if character == chatter:
                                globalchat(s, channel, "/w %s Your panic subsides!" % chatter.name)
                            else:
                                globalchat(s, channel, "/w %s %s stops panicking!" % (chatter.name, character.name))
                    else:
                        chat(s, channel, "/w %s You feel very tense!" % character.name)
                if lastturn != character.name:
                    newTurn = False
                    time.sleep(1)
                    for chatter in playersinencounter:
                        if chatter == character:
                            globalchat(s, channel, ("/w %s It's your turn! You have %s energy and %s health! What "
                                                    "would you like to do? (!commands)" % (character.name,
                                                                                           character.energy,
                                                                                           character.life)))
                            character.lastwhisper == ''
                        else:
                            globalchat(s, channel, "/w %s It's %s's turn!" % (chatter.name, character.name))
                elif newTurn:
                    chat(s, channel, "/w %s You take the initiative at %s energy!" % (character.name, character.energy))
                    newTurn = False
                if character.isplayer:
                    if encounterType != Encounter.PVP:
                        escape = character.playerTurn(charactersinencounter, playersinencounter, s, channel, enemy, True)
                        if escape is True:
                            endFight = True
                            break
                    else:
                        if character == playersinencounter[0]:
                            escape = character.playerTurn(charactersinencounter, playersinencounter, s, channel, playersinencounter[1], False)
                        else:
                            escape = character.playerTurn(charactersinencounter, playersinencounter, s, channel, playersinencounter[0], False)
                elif character.isplayer is False:
                    character.enemyTurn(charactersinencounter, playersinencounter, s, channel)
                if time.time() - 3600 > encountertimestart:
                    time.sleep(1)
                    for chatter in playersinencounter:
                        globalchat(s, channel, ("/w %s Time's up! Encounters time out after one hour!" % chatter.name))
                        chatter.timeouts += 1
                        chatter.cleanUp(s, channel, {}, True)
                    endFight = True
                    break
                lastturn = character.name
        if endFight:
            break
        charactersinencounter.sort(key=sortEncounterList, reverse=True)
    for player in playersinencounter:
        player.inencounter = False
        player.energy = 0
        player.chargecount = 1
        player.clearStatChanges()
        player.clearStatusEffects()


def checkExistence(user, RPGTestMode, s, channel):
    if user in PLAYER:
        channel = PLAYER[user].lastchannel
        PLAYER[user].handleRPG(RPGTestMode, s, channel)
    else:
        chat(s, channel, ("/w %s You don't exist in the game yet!" % user))


leaderboardtimer = 0
hostilelocationlist = ['Prison of Hope', 'Eldergrimm']
townlocationlist = ['Tarrow']
initializeGame()
