from Tank import Tank
import asyncio
import discord
import cv2
from random import randrange
import os
import os.path
from os import path
from collections import OrderedDict

class GameCommands:
    def __init__(self, userexemptionlist, gamechannel, videochannel, commandnumber):
        self.exemptusers = userexemptionlist
        self.gamechannel = gamechannel
        self.videochannel = videochannel
        self.commandnumber = commandnumber
        self.maxX = 9
        self.maxY = 9
        self.fps = 24
        self.height = 723
        self.width = 723
        self.gridsize = 60
        self.steps = 15
        self.fireframemax = 5
        self.frametranslation = 4
        self.framerotation = 6
        self.coloremojis = ["\U0001F7E9","\U0001F7E6","\U0001F7E5"]
        self.commandemojis = ["\U0001F4A5", "\U000025C0", "\U0001F53C", "\U000025B6", "\U0001F53D"]
        self.subcommandemojis = ["\U000025C0", "\U0001F53C", "\U000025B6", "\U0001F53D"]
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.gamestage = 0
        self.logrootfile = str(int(gamechannel.id)) + "_"
        self.gamenum = 0
        self.debug = True
        if not path.exists(self.dir_path + "/" + str(int(self.gamechannel.id))):
            os.mkdir(self.dir_path + "/" + str(int(self.gamechannel.id)))

    def getStatus(self):
        return (self.gamenum, self.gamechannel, self.gamestage)

    def addlog(self, text):
        if self.debug:
            with open(self.logrootfile + str(self.gamenum) + ".txt", 'a') as gamefile:
                gamefile.write(text + " \n")

    async def newGame(self):
        if self.debug:
            self.gamenum += 1
            if os.path.isfile(self.logrootfile + str(self.gamenum) + ".txt"):
                os.remove(self.logrootfile + str(self.gamenum) + ".txt")
        self.gamestage = 1
        self.startgamemessage = await self.gamechannel.send("React below to join the next game:")
        for emoji in self.coloremojis:
            await self.startgamemessage.add_reaction(emoji)

    async def checkPlayerCount(self):
        reactionset = await self.gamechannel.fetch_message(self.startgamemessage.id)
        reactions = reactionset.reactions
        fullList = []
        for emoji in self.coloremojis:
            for reaction in reactions:
                if reaction.emoji == emoji:
                    users = await reaction.users().flatten()
                    for user in users:
                        fullList.append(user.name)
        return len(list(OrderedDict.fromkeys(fullList))) - 1

    def getCommandMessages(self):
        if self.gamestage == 1:
            return ([self.startgamemessage], self.coloremojis)
        elif self.gamestage == 2:
            return (self.commandmessages, self.commandemojis)
        else:
            return ([],[])

    async def checkReaction(self, reaction, user):
        if self.gamestage == 1:
            reactionset = await self.gamechannel.fetch_message(reaction.message.id)
            reactions = reactionset.reactions
            for react in reactions:
                if not react.emoji == reaction.emoji:
                    users = await react.users().flatten()
                    if user in users:
                        await react.remove(user)
        elif self.gamestage == 2:
            if not reaction.emoji == "\U0001F4A5":
                reactionset = await self.gamechannel.fetch_message(reaction.message.id)
                reactions = reactionset.reactions
                for react in reactions:
                    if not react.emoji == reaction.emoji and not react.emoji == "\U0001F4A5":
                        users = await react.users().flatten()
                        if user in users:
                            await react.remove(user)

    def clearlist(self):
        self.tanklist = {}
        self.fullcommands = []
        self.fullevents = []
        self.round = 0
        self.commandmessages = []
        self.explosions = []

    async def gamesetup(self):
        self.gamestage = 2
        message = await self.gamechannel.fetch_message(self.startgamemessage.id)
        reactions = message.reactions
        colorset = {"\U0001F7E9":"Green","\U0001F7E6":"Blue","\U0001F7E5":"Red"}
        self.clearlist()
        taken = []
        self.beginningGrid = {}
        for react in reactions:
            users = await react.users().flatten()
            for user in users:
                if (not user in self.exemptusers) and (not user in self.tanklist.keys()):
                    solved = False
                    while not solved:
                        x, y = randrange(self.maxX + 1), randrange(self.maxY + 1)
                        newrand = str(int(x)) + "," + str(int(y))
                        if not newrand in taken:
                            taken.append(newrand)
                            solved = True
                    rotation = int(randrange(0,360,90))
                    self.tanklist[user.name] = Tank(x,y,rotation,rotation,user,colorset[react.emoji])
                    self.beginningGrid[user.name] = Tank(x,y,rotation,rotation,user,colorset[react.emoji])
        #self.tanklist = {"1":Tank(1,1,0,0,"1","Green"),"2":Tank(2,2,90,90,"2","Green"),"3":Tank(3,3,180,180,"3","Green"),"4":Tank(4,4,270,270,"4","Green")}
        await message.delete()
        for i in range(int(self.commandnumber)):
            newmessage = await self.gamechannel.send(self.make_ordinal(i + 1) + " Action")
            for emoji in self.commandemojis:
                asyncio.ensure_future(newmessage.add_reaction(emoji))
            self.commandmessages.append(newmessage)
        await self.buildImage()

    def make_ordinal(self, n):
        n = int(n)
        suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
        if 11 <= (n % 100) <= 13:
            suffix = 'th'
        return str(n) + suffix

    async def buildImage(self):
        image = self.buildraw()
        cv2.imwrite(self.dir_path + "/" + str(int(self.gamechannel.id)) + '/BattleGrid.jpg',image)
        if hasattr(self, 'GridImage'):
            await self.GridImage.delete()
        self.GridImage = await self.gamechannel.send(file = discord.File(self.dir_path + "/" + str(int(self.gamechannel.id)) + '/BattleGrid.jpg'))

    async def newCommands(self, reactions):
        ctext = {
        "\U000025C0":"Left",
        "\U0001F53C":"Up",
        "\U000025B6":"Right",
        "\U0001F53D":"Down",
        "\U0001F4A5":"Fire"
        }
        rotationguide = {
            "0Left":"CCW",
            "0Up":"Forward",
            "0Right":"CW",
            "0Down":"Backward",
            "90Left":"Backward",
            "90Up":"CCW",
            "90Right":"Forward",
            "90Down":"CW",
            "180Left":"CW",
            "180Up":"Backward",
            "180Right":"CCW",
            "180Down":"Forward",
            "270Left":"Forward",
            "270Up":"CW",
            "270Right":"Backward",
            "270Down":"CCW"
        }
        self.currentcommands = {}
        #self.round += 1
        for user in self.tanklist:
            self.currentcommands[user] = CommandContainer()
        for react in reactions:
            if react.emoji in ctext.keys():
                command = ctext[react.emoji]
                users = await react.users().flatten()
                if command == "Fire":
                    for user in users:
                        if user.name in self.currentcommands.keys():
                            if (not user in self.exemptusers):
                                self.currentcommands[user.name].fire = True
                                #query = str(int(self.tanklist[user.name].turrent)) + command
                                #self.currentcommands[user.name].command = rotationguide[query]
                                #if self.currentcommands[user.name].command == "Wait":
                                self.currentcommands[user.name].command = "Forward"
                else:
                    for user in users:
                        if user.name in self.currentcommands.keys():
                            if (not user in self.exemptusers) and (not self.tanklist[user.name].dead):
                                if self.currentcommands[user.name].fire:
                                    query = str(int(self.tanklist[user.name].turrent)) + command
                                else:
                                    query = str(int(self.tanklist[user.name].rotation)) + command
                                self.currentcommands[user.name].command = rotationguide[query]
        #for command in self.currentcommands:
            #print(command)
        #for tank in self.tanklist.values():
            #print(tank.name, tank.dead)
        self.set1 = {}
        self.set2 = {}
        self.set3 = {}
        self.coords1 = {}
        self.coords2 = {}
        self.coords3 = {}
        self.killed = []
        self.killList = {}
        self.events1 = []
        self.events2 = []
        self.events3 = []
        for user, tank in self.tanklist.items():
            if not tank.dead:
                newcoords = str(int(tank.x)) + "," + str(int(tank.y))
                #print(tank)
                self.addToDictList("coords1", newcoords, (tank.name.name, "Stay"))
                if self.currentcommands[user].fire or self.currentcommands[user].command == "Wait":
                    self.addlog(user + " coords2+3")
                    self.addToDictList("coords2", newcoords, (tank.name.name, "Stay"))
                    self.addToDictList("coords3", newcoords, (tank.name.name, "Stay"))
                elif self.currentcommands[user].command == "CCW" or self.currentcommands[user].command == "CW":
                    self.addlog(user + " coords3")
                    self.addToDictList("coords2", newcoords, (tank.name.name, "Stay"))
        for user, tankcommands in self.currentcommands.items():
            if (not tankcommands.command == "Wait") and tankcommands.fire:
                if tankcommands.command == "Forward":
                    self.addlog(user + " Fire1")
                    self.checktankshot(user, tankcommands.command)
                    self.set1[user] = "Fire"
                elif tankcommands.command == "CCW":
                    self.addlog(user + " TurrentCCW1")
                    self.set1[user] = "TurrentCCW"
                else:
                    self.addlog(user + " TurrentCW1")
                    self.set1[user] = "TurrentCW"
        for user in self.killed:
            if user in self.set1:
                if not self.set1[user] == "Fire":
                    self.addlog(user + " Killed1")
                    del self.set1[user]
                    self.currentcommands[user].command = "Wait"
                    self.currentcommands[user].fire = False
        self.killed = []
        for user, tankcommands in self.currentcommands.items():
            if not (tankcommands.command == "Wait" or tankcommands.fire):
                self.addlog(user + " Command1-1")
                self.set1[user] = tankcommands.command
                if tankcommands.command == "Forward" or tankcommands.command == "Backward":
                    self.addlog(user + " Command1-2")
                    self.movetank(user, tankcommands.command)
        solved = False
        while not solved:
            #print('trigger6')
            self.addlog("solvedloop1")
            solved = True
            coordnames, coordlist = list(self.coords2.keys()), list(self.coords2.values())
            for i in range(len(coordlist)):
                coords = coordlist[i]
                if len(coords) > 1:
                    self.addlog("Collision1")
                    #print('collision1')
                    solved = False
                    coordset = []
                    for c in coords:
                        coordset.append(c)
                    for tank in coordset:
                        #print(coordset)
                        if tank[1] == "Forward":
                            #print('Made it 1')
                            del self.set1[tank[0]]
                            usertank = self.tanklist[tank[0]]
                            newcoords = str(int(usertank.x)) + "," + str(int(usertank.y))
                            #print(tank)
                            self.addToDictList("coords2", newcoords, (tank[0], "Stay"))
                            self.addToDictList("coords3", newcoords, (tank[0], "Stay"))
                            self.coords2[coordnames[i]].remove((usertank.name.name, "Forward"))
                            self.coords3[coordnames[i]].remove((usertank.name.name, "Stay"))
        for user, tankcommands in self.currentcommands.items():
            if not (self.tanklist[user].dead or self.tanklist[user].nowdead):
                if (not tankcommands.command == "Wait") and tankcommands.fire:
                    if not tankcommands.command == "Forward":
                        if tankcommands.command == "Backward":
                            self.addlog(user + " TurrentCW2")
                            self.set2[user] = "TurrentCW"
                        else:
                            self.addlog(user + " Fire2")
                            self.checktankshot(user, tankcommands.command)
                            self.set2[user] = "Fire"
        for user in self.killed:
            if user in self.set2:
                if not self.set2[user] == "Fire":
                    self.addlog(user + " Killed2")
                    del self.set2[user]
                    self.currentcommands[user].command = "Wait"
                    self.currentcommands[user].fire = False
        self.killed = []
        for user, tankcommands in self.currentcommands.items():
            if not (self.tanklist[user].dead or self.tanklist[user].nowdead):
                if (not tankcommands.command == "Wait") and (not tankcommands.fire):
                    if tankcommands.command == "CW" or tankcommands.command == "CCW":
                        self.addlog(user + " Forward2")
                        self.set2[user] = "Forward"
                        self.movetank(user, tankcommands.command)
        solved = False
        while not solved:
            #print('trigger5')
            self.addlog("solvedloop2")
            solved = True
            coordnames, coordlist = list(self.coords3.keys()), list(self.coords3.values())
            for i in range(len(coordlist)):
                coords = coordlist[i]
                if len(coords) > 1:
                    self.addlog("Collision2")
                    #print('collision2')
                    solved = False
                    for c in coords:
                        coordset.append(c)
                    for tank in coordset:
                        if tank[1] == "Forward":
                            #print('Made it 2')
                            del self.set2[tank[0]]
                            usertank = self.tanklist[tank[0]]
                            newcoords = str(int(usertank.x)) + "," + str(int(usertank.y))
                            self.addToDictList("coords3", newcoords, (tank[0], "Stay"))
                            self.coords3[coordnames[i]].remove((usertank.name.name, "Forward"))
        for user, tankcommands in self.currentcommands.items():
            if not (self.tanklist[user].dead or self.tanklist[user].nowdead):
                if tankcommands.command == "Backward" and tankcommands.fire:
                    self.addlog(user + " Fire3")
                    self.checktankshot(user, tankcommands.command)
                    self.set3[user] = "Fire"
        '''
        print(self.coords1)
        print(self.coords2)
        print(self.coords3)
        print(self.set1)
        print(self.set2)
        print(self.set3)
        '''

    def addToDictList(self, container, key, item):
        if container == "coords1":
            if key in self.coords1.keys():
                self.coords1[key].append(item)
            else:
                self.coords1[key] = [item]
        elif container == "coords2":
            if key in self.coords2.keys():
                self.coords2[key].append(item)
            else:
                self.coords2[key] = [item]
        elif container == "coords3":
            if key in self.coords3.keys():
                self.coords3[key].append(item)
            else:
                self.coords3[key] = [item]
        elif container == "killList":
            if key in self.killList.keys():
                self.killList[key].append(item)
            else:
                self.killList[key] = [item]

    def movetank(self, user, command):#add new coords
        tank = self.tanklist[user]
        rotation, x, y = tank.rotation, tank.x, tank.y
        if command == "Backward":
            rotation = (rotation + 180) % 360
            newset = 1
        elif command == "CW":
            rotation = (rotation + 90) % 360
            newset = 2
        elif command == "CCW":
            rotation = (rotation + 270) % 360
            newset = 2
        else:
            newset = 1
        bump = False
        if rotation == 0:
            if y == 0:
                bump = True
            else:
                y -= 1
        elif rotation == 90:
            if x == self.maxX:
                bump = True
            else:
                x += 1
        elif rotation == 180:
            if y == self.maxY:
                bump = True
            else:
                y += 1
        elif rotation == 270:
            if x == 0:
                bump = True
            else:
                x -= 1
        else:
            bump = True
        newcoords = str(int(x)) + "," + str(int(y))
        if bump:
            if newset == 1:
                del self.set1[user]
                self.addToDictList("coords2", newcoords, (tank.name.name, "Stay"))
                self.addToDictList("coords3", newcoords, (tank.name.name, "Stay"))
            elif newset == 2:
                del self.set2[user]
                self.addToDictList("coords3", newcoords, (tank.name.name, "Stay"))
        else:
            if newset == 1:
                self.addToDictList("coords2", newcoords, (tank.name.name, "Forward"))
                self.addToDictList("coords3", newcoords, (tank.name.name, "Stay"))
            elif newset == 2:
                self.addToDictList("coords3", newcoords, (tank.name.name, "Forward"))

    def checktankshot(self, user, command):#build death lists, add to killed
        tank = self.tanklist[user]
        rotation, x, y = tank.turrent, tank.x, tank.y
        if command == "Backward":
            rotation = (rotation + 180) % 360
            kill = 3
        elif command == "CW":
            rotation = (rotation + 90) % 360
            kill = 2
        elif command == "CCW":
            rotation = (rotation + 270) % 360
            kill = 2
        else:
            kill = 1
        if rotation == 90:
            direction = (1, 0)
        elif rotation == 180:
            direction = (0, 1)
        elif rotation == 270:
            direction = (-1, 0)
        else:
            direction = (0, -1)
        x, y = x + direction[0], y + direction[1]
        hit = False
        if kill == 1:
            #print('trigger1')
            while self.inbounds(x, y) and not hit:
                newcoords = str(int(x)) + "," + str(int(y))
                if newcoords in self.coords1:
                    for tank in self.coords1[newcoords]:
                        if not self.tanklist[tank[0]].dead:
                            self.addToDictList("killList", 1, tank[0])
                            self.killed.append(tank[0])
                            self.tanklist[tank[0]].dead = True
                            self.events1.append(("Explosion",[x, y]))
                            self.events1.append(("Death",tank[0]))
                            hit = True
                else:
                    x, y = x + direction[0], y + direction[1]
        if kill == 2:
            #print('trigger2')
            while self.inbounds(x, y) and not hit:
                newcoords = str(int(x)) + "," + str(int(y))
                if newcoords in self.coords2:
                    for tank in self.coords2[newcoords]:
                        if not self.tanklist[tank[0]].dead:
                            self.addToDictList("killList", 2, tank[0])
                            self.killed.append(tank[0])
                            self.tanklist[tank[0]].dead = True
                            self.events2.append(("Explosion",[x, y]))
                            self.events2.append(("Death",tank[0]))
                            hit = True
                else:
                    x, y = x + direction[0], y + direction[1]
        if kill == 3:
            #print('trigger3')
            while self.inbounds(x, y) and not hit:
                newcoords = str(int(x)) + "," + str(int(y))
                if newcoords in self.coords3:
                    for tank in self.coords3[newcoords]:
                        if not self.tanklist[tank[0]].dead:
                            self.addToDictList("killList", 3, tank[0])
                            self.killed.append(tank[0])
                            self.tanklist[tank[0]].dead = True
                            self.events3.append(("Explosion",[x, y]))
                            self.events3.append(("Death",tank[0]))
                            hit = True
                else:
                    x, y = x + direction[0], y + direction[1]

    def inbounds(self, x, y):
        return x >= 0 and y >= 0 and x <= self.maxX and y <= self.maxY

    async def clearReactions(self):
        for message in self.commandmessages:
            await message.clear_reactions()
            for emoji in self.commandemojis:
                asyncio.ensure_future(message.add_reaction(emoji))

    async def generateintervalvideo(self):
        self.video = cv2.VideoWriter(self.dir_path + "/" + str(int(self.gamechannel.id)) + "/BattleVid.mp4", cv2.VideoWriter_fourcc(*'avc1'), self.fps, (self.height, self.width))
        self.buildframe()
        for message in self.commandmessages:
            self.addlog("NewCommands")
            reactionset = await self.gamechannel.fetch_message(message.id)
            await self.newCommands(reactionset.reactions)
            #print(self.set1)
            if len(self.set1) > 0:
                self.addlog("Set1")
                self.events = self.events1
                for i in range(1, self.steps + 1):
                    self.addlog("Step {}".format(str(i)))
                    for user in self.set1.keys():
                        self.tanklist[user] = self.runCommand(self.tanklist[user], self.set1[user], i)
                    self.runEvents(self.events1, i)
                    self.buildframe()
                self.shiftTanks(1)
                self.fullcommands.append(self.set1)
                self.fullevents.append(self.events1)
            #print(self.set2)
            if len(self.set2) > 0:
                self.addlog("Set2")
                self.events = self.events2
                for i in range(1, self.steps + 1):
                    self.addlog("Step {}".format(str(i)))
                    for user in self.set2.keys():
                        self.tanklist[user] = self.runCommand(self.tanklist[user], self.set2[user], i)
                    self.runEvents(self.events2, i)
                    self.buildframe()
                self.shiftTanks(2)
                self.fullcommands.append(self.set2)
                self.fullevents.append(self.events2)
            #print(self.set3)
            if len(self.set3) > 0:
                self.addlog("Set3")
                self.events = self.events3
                for i in range(1, self.steps + 1):
                    self.addlog("Step {}".format(str(i)))
                    for user in self.set3.keys():
                        self.tanklist[user] = self.runCommand(self.tanklist[user], self.set3[user], i)
                    self.runEvents(self.events3, i)
                    self.buildframe()
                self.shiftTanks(3)
                self.fullcommands.append(self.set3)
                self.fullevents.append(self.events3)
        self.video.release()
        del self.video
        newGridVideo = await self.gamechannel.send(file = discord.File(self.dir_path + "/" + str(int(self.gamechannel.id)) + '/BattleVid.mp4'))
        if hasattr(self, 'GridVideo'):
            await self.GridVideo.delete()
        self.GridVideo = newGridVideo

    async def generatefullvideo(self):
        self.video = cv2.VideoWriter(self.dir_path + "/" + str(int(self.gamechannel.id)) + "/BattleLog.mp4", cv2.VideoWriter_fourcc(*'avc1'), self.fps, (self.height, self.width))
        self.buildframe2()
        for i in range(len(self.fullcommands)):
            setlist = self.fullcommands[i]
            self.events = self.fullevents[i]
            for j in range(1, self.steps + 1):
                for user in setlist.keys():
                    self.beginningGrid[user] = self.runCommand(self.beginningGrid[user], setlist[user], j)
                self.runEvents(self.events, j, True)
                self.buildframe2()
            for user in setlist.keys():
                oldtank = self.beginningGrid[user]
                newtank = Tank(oldtank.x, oldtank.y, oldtank.rotation, oldtank.turrent, oldtank.name, oldtank.color)
                newtank.dead = oldtank.dead or oldtank.nowdead
                newtank.nowdead = oldtank.nowdead or oldtank.dead
                self.beginningGrid[user] = self.subShiftTanks(newtank, setlist[user])
        self.video.release()
        del self.video
        await self.videochannel.send(file = discord.File(self.dir_path + "/" + str(int(self.gamechannel.id)) + '/BattleLog.mp4'))

    def runCommand(self, tank, command, frame):
        if command == "Fire":
            if frame < self.fireframemax:
                tank.fireframe = frame
            elif frame == self.fireframemax:
                tank.fireframe = 0
        elif command == "Forward":
            if tank.rotation == 90:
                tank.xOffset = self.frametranslation * frame
            elif tank.rotation == 180:
                tank.yOffset = self.frametranslation * frame
            elif tank.rotation == 270:
                tank.xOffset = -self.frametranslation * frame
            else:
                tank.yOffset = -self.frametranslation * frame
        elif command == "Backward":
            if tank.rotation == 90:
                tank.xOffset = -self.frametranslation * frame
            elif tank.rotation == 180:
                tank.yOffset = -self.frametranslation * frame
            elif tank.rotation == 270:
                tank.xOffset = self.frametranslation * frame
            else:
                tank.yOffset = self.frametranslation * frame
        elif command == "CW":
            tank.rotationOffset = self.framerotation * frame
            tank.turrentOffset = self.framerotation * frame
        elif command == "CCW":
            tank.rotationOffset = -self.framerotation * frame
            tank.turrentOffset = -self.framerotation * frame
        elif command == "TurrentCW":
            tank.turrentOffset = self.framerotation * frame
        elif command == "TurrentCCW":
            tank.turrentOffset = -self.framerotation * frame
        return tank

    def runEvents(self, events, frame, fullvid = False):
        for event in events:
            #print(event)
            if event[0] == "Explosion":
                if frame > 2 and frame < 8:
                    #print((event[1][0], event[1][1], frame - 2))
                    self.explosions.append((event[1][0], event[1][1], frame - 2))
            elif event[0] == "Death":
                if frame == 4:
                    #print(event[1])
                    if fullvid:
                        self.beginningGrid[event[1]].nowdead = True
                    else:
                        self.tanklist[event[1]].nowdead = True

    def shiftTanks(self, stage):
        if stage == 1:
            for user in self.set1.keys():
                oldtank = self.tanklist[user]
                newtank = Tank(oldtank.x, oldtank.y, oldtank.rotation, oldtank.turrent, oldtank.name, oldtank.color)
                newtank.dead = oldtank.dead or oldtank.nowdead
                self.tanklist[user] = self.subShiftTanks(newtank, self.set1[user])
        elif stage == 2:
            for user in self.set2.keys():
                oldtank = self.tanklist[user]
                newtank = Tank(oldtank.x, oldtank.y, oldtank.rotation, oldtank.turrent, oldtank.name, oldtank.color)
                newtank.dead = oldtank.dead or oldtank.nowdead
                self.tanklist[user] = self.subShiftTanks(newtank, self.set2[user])
        elif stage == 3:
            for user in self.set3.keys():
                oldtank = self.tanklist[user]
                newtank = Tank(oldtank.x, oldtank.y, oldtank.rotation, oldtank.turrent, oldtank.name, oldtank.color)
                newtank.dead = oldtank.dead or oldtank.nowdead
                self.tanklist[user] = self.subShiftTanks(newtank, self.set3[user])

    def subShiftTanks(self, tank, command):
        if command == "Forward":
            if tank.rotation == 90:
                tank.x += 1
            elif tank.rotation == 180:
                tank.y += 1
            elif tank.rotation == 270:
                tank.x -= 1
            else:
                tank.y -= 1
        elif command == "Backward":
            if tank.rotation == 90:
                tank.x -= 1
            elif tank.rotation == 180:
                tank.y -= 1
            elif tank.rotation == 270:
                tank.x += 1
            else:
                tank.y += 1
        elif command == "CW":
            tank.rotation = (tank.rotation + 90) % 360
            tank.turrent = (tank.turrent + 90) % 360
        elif command == "CCW":
            tank.rotation = (tank.rotation + 270) % 360
            tank.turrent = (tank.turrent + 270) % 360
        elif command == "TurrentCW":
            tank.turrent = (tank.turrent + 90) % 360
        elif command == "TurrentCCW":
            tank.turrent = (tank.turrent + 270) % 360
        return tank

    def buildframe(self):
        self.video.write(self.buildraw())
        self.explosions = []

    def buildraw(self):
        img1 = cv2.imread(self.dir_path + r'/assets/Grid.jpg')
        for tank in self.tanklist.values():
            originx, originy = 95 + (60 * tank.x) + tank.xOffset, 90 + (60 * tank.y) + tank.yOffset
            self.addText(img1, tank.name.name, tank.color, originx, originy)
        for tank in self.tanklist.values():
            originx, originy, rotation, turrent = 95 + (60 * tank.x) + tank.xOffset, 90 + (60 * tank.y) + tank.yOffset, tank.rotation + tank.rotationOffset, tank.turrent + tank.turrentOffset
            self.addTank(img1, originx, originy, rotation, turrent, tank.color, tank.nowdead)
        for tank in self.tanklist.values():
            originx, originy, turrent = 95 + (60 * tank.x) + tank.xOffset, 90 + (60 * tank.y) + tank.yOffset, tank.turrent + tank.turrentOffset
            if tank.fireframe > 0:
                self.addFire(img1, originx, originy, turrent, tank.fireframe)
        for explosion in self.explosions:
            newx, newy = 95 + (60 * explosion[0]), 90 + (60 * explosion[1])
            #print(newx, newy, explosion[2])
            self.addExplosion(img1, newx, newy, explosion[2])
        '''
        if frame > 2 and frame < 8:
            for tank, explosion in self.explosions:
                if explosion[0] == round:
                    self.addExplosion(img1, explosion[1], explosion[2], frame)
                    '''
        return img1

    def buildframe2(self):
        self.video.write(self.buildraw2())
        self.explosions = []

    def buildraw2(self):
        img1 = cv2.imread(self.dir_path + r'/assets/Grid.jpg')
        for tank in self.beginningGrid.values():
            originx, originy = 95 + (60 * tank.x) + tank.xOffset, 90 + (60 * tank.y) + tank.yOffset
            self.addText(img1, tank.name.name, tank.color, originx, originy)
        for tank in self.beginningGrid.values():
            originx, originy, rotation, turrent = 95 + (60 * tank.x) + tank.xOffset, 90 + (60 * tank.y) + tank.yOffset, tank.rotation + tank.rotationOffset, tank.turrent + tank.turrentOffset
            self.addTank(img1, originx, originy, rotation, turrent, tank.color, tank.nowdead)
        for tank in self.beginningGrid.values():
            originx, originy, turrent = 95 + (60 * tank.x) + tank.xOffset, 90 + (60 * tank.y) + tank.yOffset, tank.turrent + tank.turrentOffset
            if tank.fireframe > 0:
                self.addFire(img1, originx, originy, turrent, tank.fireframe)
        for explosion in self.explosions:
            newx, newy = 95 + (60 * explosion[0]), 90 + (60 * explosion[1])
            self.addExplosion(img1, newx, newy, explosion[2])
        '''
        if frame > 2 and frame < 8:
            for tank, explosion in self.explosions:
                if explosion[0] == round:
                    self.addExplosion(img1, explosion[1], explosion[2], frame)
        '''
        return img1

    def addFire(self, img1, gridx, gridy, angle, frame):
        if angle == 90:
            gridx += 38
            gridy -= 1
            angletext = '090'
        elif angle == 180:
            gridx -= 4
            gridy += 42
            angletext = '180'
        elif angle == 270:
            gridx -= 36
            gridy -= 1
            angletext = '270'
        else:
            gridx -= 4
            gridy -= 33
            angletext = '000'
        self.addlog("Query image: " + self.dir_path + r'/assets/Fire_{}_{}.jpg'.format(str(int(frame)), angletext))
        img2 = cv2.imread(self.dir_path + r'/assets/Fire_{}_{}.jpg'.format(str(int(frame)), angletext))
        self.addImage(img1, img2, gridx, gridy, 200)

    def addExplosion(self, img1, gridx, gridy, frame):
        self.addlog("Query image: " + self.dir_path + r'/assets/Explosion_{}.jpg'.format(str(int(frame))))
        img2 = cv2.imread(self.dir_path + r'/assets/Explosion_{}.jpg'.format(str(int(frame))))
        self.addImage(img1,img2,gridx,gridy)

    def addTank(self, img1, gridx, gridy, angle1d, angle2d, color, dead):
        while angle1d > 359:
            angle1d -= 360
        while angle1d < 0:
            angle1d += 360
        while angle2d > 359:
            angle2d -= 360
        while angle2d < 0:
            angle2d += 360
        if int(angle1d) > 180:
            angle1 = str(360 - int(angle1d))
            rev1 = True
        else:
            angle1 = str(int(angle1d))
            rev1 = False
        while len(angle1) < 3:
            angle1 = '0' + angle1
        if int(angle2d) > 180:
            angle2 = str(360 - int(angle2d))
            rev2 = True
        else:
            angle2 = str(int(angle2d))
            rev2 = False
        while len(angle2) < 3:
            angle2 = '0' + angle2
        if dead:
            self.addlog("Query image: " + self.dir_path + r'/assets/Tank_Base_Dead{}.jpg'.format(angle1))
            self.addlog("Query image: " + self.dir_path + r'/assets/Tank_Turrent_Dead{}.jpg'.format(angle2))
            img2 = cv2.imread(self.dir_path + r'/assets/Tank_Base_Dead{}.jpg'.format(angle1))
            img3 = cv2.imread(self.dir_path + r'/assets/Tank_Turrent_Dead{}.jpg'.format(angle2))
            threshold = 180
        else:
            self.addlog("Query image: " + self.dir_path + r'/assets/Tank_Base_{}{}.jpg'.format(color, angle1))
            self.addlog("Query image: " + self.dir_path + r'/assets/Tank_Turrent_{}{}.jpg'.format(color, angle2))
            img2 = cv2.imread(self.dir_path + r'/assets/Tank_Base_{}{}.jpg'.format(color, angle1))
            img3 = cv2.imread(self.dir_path + r'/assets/Tank_Turrent_{}{}.jpg'.format(color, angle2))
            threshold = 140
        if rev1:
            img2 = cv2.flip(img2,1)
        if rev2:
            img3 = cv2.flip(img3,1)
        self.addImage(img1, img2, gridx, gridy, threshold)
        self.addImage(img1, img3, gridx, gridy, threshold)

    def addText(self, img1, text, color, originx, originy):
        #colorwheel = {"Red":(44,31,120), "Green":(80,155,75), "Blue":(163,77,15)}
        font = cv2.FONT_HERSHEY_PLAIN
        fontscale = 1
        thickness = 2
        textsize = cv2.getTextSize(text, font, fontscale, thickness)[0]
        textx, texty = originx - int(textsize[0] / 2), originy + 35 + int(textsize[1] / 2)
        cv2.putText(img1, text, (textx, texty), font, fontscale, (255,255,255), thickness)
        #cv2.putText(img1, text, (textx, texty), font, fontscale, colorwheel[color], thickness)

    def addImage(self, img1, img2, originx, originy, thresholdnum = 140):
        rows,cols = img2.shape[:2]
        offsetx, offsety = originx - int(rows/2), originy - int(cols/2)
        roi = img1[offsety:rows + offsety, offsetx:cols + offsetx]

        # Now create a mask of logo and create its inverse mask also
        img2gray = cv2.cvtColor(img2,cv2.COLOR_BGR2GRAY)
        mask = cv2.threshold(img2gray, thresholdnum, 255, cv2.THRESH_BINARY)[1]
        mask_inv = cv2.bitwise_not(mask)

        # Now black-out the area of logo in ROI
        img1_bg = cv2.bitwise_and(roi,roi,mask = mask)

        # Take only region of logo from logo image.
        img2_fg = cv2.bitwise_and(img2,img2,mask = mask_inv)

        # Put logo in ROI and modify the main image
        dst = cv2.add(img1_bg,img2_fg)
        img1[offsety:rows + offsety, offsetx:cols + offsetx] = dst
        self.addlog("Image Added")

    async def executeRound(self):
        await self.generateintervalvideo()
        await self.buildImage()
        alivetanks = []
        for tank in self.tanklist.values():
            if not tank.dead:
                alivetanks.append(tank.name)
        if len(alivetanks) > 1:
            await self.clearReactions()
            await self.gamechannel.send(str(len(alivetanks)) + " tanks remain.", delete_after = 30)
        else:
            self.finalmessage = await self.gamechannel.send('Game Over')
            await self.generatefullvideo()
        return len(alivetanks) < 2

    async def endgameCleanup(self):
        for message in self.commandmessages:
            await message.delete()
        await self.GridVideo.delete()
        del self.GridVideo
        await self.GridImage.delete()
        del self.GridImage
        await self.finalmessage.delete()

class CommandContainer:
    def __init__(self):
        self.fire = False
        self.command = "Wait" #CW, CCW, Forward, Backward, Wait, Dead
        self.finished = False
        self.deathframe = 0