import time
import json

from database import *
from objects import *
from constants import *
from packettypes import *
from utils import *

import globalvars as g


def canAttackPlayer(attacker, victim):
    # check attack timer
    if time.time() < TempPlayer[attacker].attackTimer + 1:
        return False

    # check for subscript out of range
    if not isPlaying(victim):
        return False

    # make sure they are on the same map
    if not getPlayerMap(attacker) == getPlayerMap(victim):
        return False

    # make sure we dont attack the player if they are switching maps
    if TempPlayer[victim].gettingMap:
        return False

    # check if at same coordinates

    attackDir = getPlayerDir(attacker)

    if attackDir == DIR_UP:
        if not ((getPlayerY(victim) + 1 == getPlayerY(attacker)) and (getPlayerX(victim) == getPlayerX(attacker))):
            return False
    elif attackDir == DIR_DOWN:
        if not ((getPlayerY(victim) - 1 == getPlayerY(attacker)) and (getPlayerX(victim) == getPlayerX(attacker))):
            return False
    elif attackDir == DIR_LEFT:
        if not ((getPlayerY(victim) == getPlayerY(attacker)) and (getPlayerX(victim) + 1 == getPlayerX(attacker))):
            return False
    elif attackDir == DIR_RIGHT:
        if not ((getPlayerY(victim) == getPlayerY(attacker)) and (getPlayerX(victim) - 1 == getPlayerX(attacker))):
            return False

    # check if map is attackable
    # todo

    # make sure they have more than 0 hp
    if getPlayerVital(victim, Vitals.hp) <= 0:
        return False

    # check to make sure they dont have access
    # todo

    # check to make sure the victim isnt an admin
    # todo

    # make sure attacker is high enough level
    # todo

    # make sure victim is high enough level
    # todo

    return True


def attackPlayer(attacker, victim, damage):
    # check for subscript out of range
    if not isPlaying(attacker) or not isPlaying(victim) or damage < 0:
        return

    # todo: check weapon

    # send packet to map so they can see person attacking
    packet = json.dumps([{"packet": ServerPackets.SAttack, "attacker": attacker}])
    g.conn.sendDataToMapBut(getPlayerMap(attacker), attacker, packet)

    # reset attack timer
    TempPlayer[attacker].attackTimer = time.time()


def playerMove(index, direction, movement):
    moved = False
    setPlayerDir(index, direction)

    if direction == DIR_UP:
        if getPlayerY(index) > 0:
            # TODO: Check if tilemap thing
            if Map[getPlayerMap(index)].tile[getPlayerX(index)][getPlayerY(index)-1].type != TILE_TYPE_BLOCKED:
                setPlayerY(index, getPlayerY(index) - 1)

                packet = json.dumps([{"packet": ServerPackets.SPlayerMove, "index": index, "x": getPlayerX(index), "y": getPlayerY(index), "direction": getPlayerDir(index), "moving": movement}])
                g.conn.sendDataToAllBut(index, packet)
                moved = True
        else:
            if Map[getPlayerMap(index)].up > 0:
                playerWarp(index, Map[getPlayerMap(index)].up, getPlayerX(index), MAX_MAPY - 1)  # todo, dont use -1
                moved = True

    elif direction == DIR_DOWN:
        if getPlayerY(index) < MAX_MAPY-1:
            if Map[getPlayerMap(index)].tile[getPlayerX(index)][getPlayerY(index)+1].type != TILE_TYPE_BLOCKED:
                setPlayerY(index, getPlayerY(index) + 1)

                packet = json.dumps([{"packet": ServerPackets.SPlayerMove, "index": index, "x": getPlayerX(index), "y": getPlayerY(index), "direction": getPlayerDir(index), "moving": movement}])
                g.conn.sendDataToAllBut(index, packet)
                moved = True

        else:
            if Map[getPlayerMap(index)].down > 0:
                playerWarp(index, Map[getPlayerMap(index)].down, getPlayerX(index), 0)
                moved = True

    elif direction == DIR_LEFT:
        if getPlayerX(index) > 0:
            if Map[getPlayerMap(index)].tile[getPlayerX(index)-1][getPlayerY(index)].type != TILE_TYPE_BLOCKED:
                setPlayerX(index, getPlayerX(index) - 1)

                packet = json.dumps([{"packet": ServerPackets.SPlayerMove, "index": index, "x": getPlayerX(index), "y": getPlayerY(index), "direction": getPlayerDir(index), "moving": movement}])
                g.conn.sendDataToAllBut(index, packet)
                moved = True

        else:
            if Map[getPlayerMap(index)].left > 0:
                playerWarp(index, Map[getPlayerMap(index)].left, MAX_MAPX-1, getPlayerY(index))  # todo, dont use -1
                moved = True

    elif direction == DIR_RIGHT:
        if getPlayerX(index) < MAX_MAPX-1:
            if Map[getPlayerMap(index)].tile[getPlayerX(index)+1][getPlayerY(index)].type != TILE_TYPE_BLOCKED:
                setPlayerX(index, getPlayerX(index) + 1)

                packet = json.dumps([{"packet": ServerPackets.SPlayerMove, "index": index, "x": getPlayerX(index), "y": getPlayerY(index), "direction": getPlayerDir(index), "moving": movement}])
                g.conn.sendDataToAllBut(index, packet)
                moved = True

        else:
            if Map[getPlayerMap(index)].right > 0:
                playerWarp(index, Map[getPlayerMap(index)].right, 0, getPlayerY(index))
                moved = True

    # check to see if the tile is a warp tile, and if so warp them
    if Map[getPlayerMap(index)].tile[getPlayerX(index)][getPlayerY(index)].type == TILE_TYPE_WARP:
        mapNum = int(Map[getPlayerMap(index)].tile[getPlayerX(index)][getPlayerY(index)].data1)
        x = int(Map[getPlayerMap(index)].tile[getPlayerX(index)][getPlayerY(index)].data2)
        y = int(Map[getPlayerMap(index)].tile[getPlayerX(index)][getPlayerY(index)].data3)

        playerWarp(index, mapNum, x, y)
        moved = True

    if not moved:
        # hacking attempt
        g.serverLogger.info("hacking attempt (playerMove)")


def playerWarp(index, mapNum, x, y):
    oldMap = getPlayerMap(index)

    if oldMap != mapNum:
        sendLeaveMap(index, oldMap)

    setPlayerMap(index, mapNum)
    setPlayerX(index, x)
    setPlayerY(index, y)

    playersOnMap[mapNum] = 1

    TempPlayer[index].gettingMap = 1

    packet = json.dumps([{"packet": ServerPackets.SCheckForMap, "mapnum": mapNum, "revision": Map[mapNum].revision}])
    g.conn.sendDataTo(index, packet)


    #packet = json.dumps([{"packet": ServerPackets.SPlayerMove, "index": index, "x": getPlayerX(index), "y": getPlayerY(index), "direction": getPlayerDir(index), "moving": 0}])
    #g.conn.sendDataToAllBut(index, packet)

def joinGame(index):
    TempPlayer[index].inGame = True

    g.totalPlayersOnline += 1
    updateHighIndex()

    if getPlayerAccess(index) <= ADMIN_MONITOR:
        globalMsg(getPlayerName(index) + " has joined!", joinLeftColor)
    else:
        globalMsg(getPlayerName(index) + " has joined!", textColor.WHITE)

    # send ok to client to start receiving game data
    packet = json.dumps([{"packet": ServerPackets.SLoginOK, "index": index}])
    g.conn.sendDataTo(index, packet)

    # send more goodies
    sendClasses(index)
    sendItems(index)
    # npc
    # shops
    # spells
    sendInventory(index)
    # worn equipment

    for i in range(0, Vitals.vital_count):  # vital.vital_count -1
        sendVital(index, i)

    sendStats(index)

    # warp player to saved location
    playerWarp(index, getPlayerMap(index), getPlayerX(index), getPlayerY(index))

    # send welcome messages (todo)
    sendWelcome(index)

    # send that we're ingame
    packet = json.dumps([{"packet": ServerPackets.SInGame}])
    g.conn.sendDataTo(index, packet)


def leftGame(index):
    if TempPlayer[index].inGame:
        TempPlayer[index].inGame = False

        savePlayer(index)

        g.connectionLogger.info("Player left game")
        sendLeftGame(index)

        g.totalPlayersOnline -= 1
        updateHighIndex()

    clearPlayer(index)


def findPlayer(name):
    for i in range(g.totalPlayersOnline):
        # dont check a name that is too small
        if len(getPlayerName(g.playersOnline[i])) >= len(name):
            if getPlayerName(g.playersOnline[i]).lower() == name.lower():
                return g.playersOnline[i]

    return None


def findOpenInvSlot(index, itemNum):
    if not isPlaying(index) or itemNum < 0 or itemNum > MAX_ITEMS:
        return

    if Item[itemNum].type == ITEM_TYPE_CURRENCY:
        # if the the item is currency, find and add to previous item
        for i in range(MAX_INV):
            if getPlayerInvItemNum(index, i) == itemNum:
                return i

    for i in range(0, MAX_INV):
        # try to find an open free slot
        if getPlayerInvItemNum(index, i) is None:
            return i

    return None


def hasItem(index, itemNum):
    if not isPlaying(index) or itemNum < 0 or itemNum > MAX_ITEMS:
        return

    for i in range(MAX_INV):
        if getPlayerInvItemNum(index, i):
            if Item[itemNum].type == ITEM_TYPE_CURRENCY:
                return getPlayerInvItemValue(index, i)

            else:
                return 1


def giveItem(index, itemNum, itemVal):
    if not isPlaying(index) or itemNum < 0 or itemNum > MAX_ITEMS:
        return

    i = findOpenInvSlot(index, itemNum)

    # check if inventory is full
    if i is not None:
        setPlayerInvItemNum(index, i, itemNum)
        setPlayerInvItemValue(index, i, getPlayerInvItemValue(index, i) + itemVal)

        # do something if armor

        sendInventoryUpdate(index, i)

    else:
        playerMsg(index, 'Your inventory is full.', textColor.BRIGHT_RED)


def updateHighIndex():
    # TODO ALOT

    # no players are logged in
    if g.totalPlayersOnline < 1:
        g.highIndex = 0
        g.playersOnline = []
        return

    # reset array
    g.playersOnline = []

    for i in range(0, MAX_PLAYERS):
        if len(getPlayerLogin(i)) > 0:
            g.playersOnline.append(i)
            g.highIndex = i

    packet = json.dumps([{"packet": ServerPackets.SHighIndex, "highindex": g.highIndex}])
    g.conn.sendDataToAll(packet)

    g.serverLogger.info("High Index has been updated")

# (SHOULD BE IN SERVER.TCP?)
####################
# SERVER FUNCTIONS #
####################


def globalMsg(msg, color=(255, 0, 0)):
    packet = json.dumps([{"packet": ServerPackets.SGlobalMsg, "msg": msg, "color": color}])
    g.conn.sendDataToAll(packet)


def adminMsg(msg, color=(255, 0, 0)):
    packet = json.dumps([{"packet": ServerPackets.SAdminMsg, "msg": msg, "color": color}])

    for i in range(g.totalPlayersOnline):
        if getPlayerAccess(playersOnline[i]) > 0:
            g.conn.sendDataTo(playersOnline[i], packet)


def playerMsg(index, msg, color=(255, 0, 0)):
    packet = json.dumps([{"packet": ServerPackets.SPlayerMsg, "msg": msg, "color": color}])
    g.conn.sendDataTo(index, packet)


def mapMsg(mapNum, msg, color=(255, 0, 0)):
    # todo: only current map
    packet = json.dumps([{"packet": ServerPackets.SMapMsg, "msg": msg, "color": color}])
    g.conn.sendDataToMap(mapNum, packet)


def alertMsg(index, reason):
    packet = json.dumps([{"packet": ServerPackets.SAlertMsg, "msg": reason}])
    g.conn.sendDataTo(index, packet)


def isPlaying(index):
    if TempPlayer[index].inGame is True:
        return True


def isLoggedIn(index):
    if len(Player[index].Login) > 0:
        return True


def isMultiAccounts(login):
    for i in range(g.totalPlayersOnline):
        if str(Player[g.playersOnline[i]].Login).lower() == login.lower():
            return True

    return False


def closeConnection(index):
    if index >= 0:
        leftGame(index)

        g.connectionLogger.info("Connection from " + str(index) + " has been terminated.")
        clearPlayer(index)


def createFullMapCache():
    g.serverLogger.debug('createFullMapCache()')
    for i in range(MAX_MAPS):
        mapCacheCreate(i)


def mapCacheCreate(mapNum):
    mapData = []
    mapData.append({"packet": ServerPackets.SMapData,
                    "mapnum": mapNum,
                    "mapname": Map[mapNum].name,
                    "revision": Map[mapNum].revision,
                    "moral": Map[mapNum].moral,
                    "tileset": Map[mapNum].tileSet,
                    "up": Map[mapNum].up,
                    "down": Map[mapNum].down,
                    "left": Map[mapNum].left,
                    "right": Map[mapNum].right,
                    "bootmap": Map[mapNum].bootMap,
                    "bootx": Map[mapNum].bootX,
                    "booty": Map[mapNum].bootY})

    for x in range(MAX_MAPX):
        for y in range(MAX_MAPY):
            tempTile = Map[mapNum].tile[x][y]
            mapData.append([{"ground":    tempTile.ground,
                             "mask":      tempTile.mask,
                             "animation": tempTile.anim,
                             "fringe":    tempTile.fringe,
                             "type":      tempTile.type,
                             "data1":     tempTile.data1,
                             "data2":     tempTile.data2,
                             "data3":     tempTile.data3}])

    MapCache[mapNum] = mapData


def sendWhosOnline(index):
    msg = ''
    n = 0

    for i in range(g.totalPlayersOnline):
        if g.playersOnline[i] != index:
            msg += getPlayerName(g.playersOnline[i]) + ', '
            n += 1

    if n == 0:
        msg = 'There are no other players online.'
    else:
        msg = 'There are ' + str(n) + ' other players online: ' + msg[:-2] + '.'

    playerMsg(index, msg, whoColor)


def sendChars(index):
    packet = []
    packet.append({"packet": ServerPackets.SAllChars})

    for i in range(0, MAX_CHARS):
        packet.append({"charname": Player[index].char[i].name,
                       "charclass": Class[Player[index].char[i].Class].name,
                       "charlevel": Player[index].char[i].level,
                       "sprite": Player[index].char[i].sprite})

    nPacket = json.dumps(packet)
    g.conn.sendDataTo(index, nPacket)


def sendJoinMap(index):
    g.serverLogger.debug('sendJoinMap()')
    # send data of all players (on current map) to index
    for i in range(0, g.totalPlayersOnline):
        if g.playersOnline[i] != index:
            if getPlayerMap(g.playersOnline[i]) == getPlayerMap(index):
                packet = json.dumps([{"packet": ServerPackets.SPlayerData, "index": g.playersOnline[i], "name": getPlayerName(g.playersOnline[i]), "access": getPlayerAccess(index), "sprite": getPlayerSprite(g.playersOnline[i]), "map": getPlayerMap(g.playersOnline[i]), "x": getPlayerX(g.playersOnline[i]), "y": getPlayerY(g.playersOnline[i]), "direction": getPlayerDir(g.playersOnline[i])}])
                g.conn.sendDataTo(index, packet)

    # send index's data to all players including himself
    packet = json.dumps([{"packet": ServerPackets.SPlayerData, "index": index, "name": getPlayerName(index),  "access": getPlayerAccess(index), "sprite": getPlayerSprite(index), "map": getPlayerMap(index), "x": getPlayerX(index), "y": getPlayerY(index), "direction": getPlayerDir(index)}])
    g.conn.sendDataToMap(getPlayerMap(index), packet)


def sendVital(index, vital):
    if vital == 0:    # hp
        packet = json.dumps([{"packet": ServerPackets.SPlayerHP, "hp_max": getPlayerMaxVital(index, 0), "hp": getPlayerVital(index, 0)}])
    elif vital == 1:  # mp
        packet = json.dumps([{"packet": ServerPackets.SPlayerMP, "mp_max": getPlayerMaxVital(index, 1), "mp": getPlayerVital(index, 1)}])
    elif vital == 2:  # sp
        packet = json.dumps([{"packet": ServerPackets.SPlayerSP, "sp_max": getPlayerMaxVital(index, 2), "sp": getPlayerVital(index, 2)}])

    g.conn.sendDataTo(index, packet)


def sendStats(index):
    packet = json.dumps([{"packet": ServerPackets.SPlayerStats, "strength": getPlayerStat(index, 0), "defense": getPlayerStat(index, 1), "speed": getPlayerStat(index, 2), "magic": getPlayerStat(index, 3)}])
    g.conn.sendDataTo(index, packet)


def sendWelcome(index):
    playerMsg(index, "Type /help for help on commands. Use arrows keys to move, hold down shift to run, and use ctrl to attack", textColor.CYAN)

    if len(g.MOTD) > 0:
        playerMsg(index, "MOTD: " + g.MOTD, textColor.CYAN)

    #send whos online


def sendClasses(index):
    packet = []
    packet.append({"packet": ServerPackets.SClassesData, "maxclasses": g.maxClasses})

    for i in range(0, g.maxClasses):
        packet.append({"classname": getClassName(i),
                       "sprite": Class[i].sprite,
                       "classmaxhp": getClassMaxVital(i, 0),
                       "classmaxmp": getClassMaxVital(i, 1),
                       "classmaxsp": getClassMaxVital(i, 2),
                       "classstatstr": Class[i].stat[Stats.strength],
                       "classstatdef": Class[i].stat[Stats.defense],
                       "classstatspd": Class[i].stat[Stats.speed],
                       "classstatmag": Class[i].stat[Stats.magic]})

    nPacket = json.dumps(packet)
    g.conn.sendDataTo(index, nPacket)


def sendNewCharClasses(index):
    packet = []
    packet.append({"packet": ServerPackets.SNewCharClasses, "maxclasses": g.maxClasses})

    for i in range(0, g.maxClasses):
        packet.append({"classname": getClassName(i),
                       "sprite": Class[i].sprite,
                       "classmaxhp": getClassMaxVital(i, 0),
                       "classmaxmp": getClassMaxVital(i, 1),
                       "classmaxsp": getClassMaxVital(i, 2),
                       "classstatstr": Class[i].stat[Stats.strength],
                       "classstatdef": Class[i].stat[Stats.defense],
                       "classstatspd": Class[i].stat[Stats.speed],
                       "classstatmag": Class[i].stat[Stats.magic]})

    nPacket = json.dumps(packet)
    g.conn.sendDataTo(index, nPacket)


def sendLeaveMap(index, mapNum):
    packet = json.dumps([{"packet": ServerPackets.SLeft, "index": index}])
    g.conn.sendDataToAllBut(index, packet)


def sendPlayerData(index):
    packet = json.dumps([{"packet": ServerPackets.SPlayerData, "index": index, "name": getPlayerName(index), "access": getPlayerAccess(index), "sprite": getPlayerSprite(index), "map": getPlayerMap(index), "x": getPlayerX(index), "y": getPlayerY(index), "direction": getPlayerDir(index)}])
    g.conn.sendDataToMap(getPlayerMap(index), packet)


def sendMap(index, mapNum):
    g.serverLogger.debug('sendMap()')
    g.conn.sendDataTo(index, json.dumps(MapCache[mapNum]))


def sendMapList(index):
    packet = []
    packet.append({"packet": ServerPackets.SMapList})
    print "todo: map editor client"

    mapNames = []
    for i in range(MAX_MAPS):
        mapNames.append(Map[i].name)

    packet.append({'mapnames': mapNames})

    nPacket = json.dumps(packet)
    g.conn.sendDataTo(index, nPacket)


def sendItems(index):
    for i in range(0, MAX_ITEMS):
        if len(Item[i].name) > 0:
            sendUpdateItemTo(index, i)


def sendInventory(index):
    packet = []
    packet.append({"packet": ServerPackets.SPlayerInv})

    for i in range(0, MAX_INV):
        packet.append({"itemnum": getPlayerInvItemNum(index, i),
                       "itemvalue": getPlayerInvItemValue(index, i),
                       "itemdur": getPlayerInvItemDur(index, i)})

    nPacket = json.dumps(packet)
    g.conn.sendDataTo(index, nPacket)


def sendInventoryUpdate(index, invSlot):
    packet = json.dumps([{"packet": ServerPackets.SPlayerInvUpdate, "invslot": invSlot, "itemnum": getPlayerInvItemNum(index, invSlot), "itemvalue": getPlayerInvItemValue(index, invSlot), "itemdur": getPlayerInvItemDur(index, invSlot)}])
    g.conn.sendDataTo(index, packet)


# (SHOULD BE IN datahandler.py)
def sendPlayerDir(index):
    packet = json.dumps([{"packet": ServerPackets.SPlayerDir, "index": index, "direction": getPlayerDir(index)}])
    g.conn.sendDataToAllBut(index, packet)


def sendLeftGame(index):
    #TODO Make name non or smth
    packet = json.dumps([{"packet": ServerPackets.SPlayerData, "index": index, "sprite": 0, "name": "", "access": 0, "map": 0, "x": 0, "y": 0, "direction": 0}])
    g.conn.sendDataToAllBut(index, packet)


def sendUpdateItemToAll(itemNum):
    packet = json.dumps([{"packet": ServerPackets.SUpdateItem, "itemnum": itemNum, "itemname": Item[itemNum].name, "itempic": Item[itemNum].pic, "itemtype": Item[itemNum].type, "itemdata1": Item[itemNum].data1, "itemdata2": Item[itemNum].data2, "itemdata3": Item[itemNum].data3}])
    g.conn.sendDataToAll(packet)


def sendUpdateItemTo(index, itemNum):
    packet = json.dumps([{"packet": ServerPackets.SUpdateItem, "itemnum": itemNum, "itemname": Item[itemNum].name, "itempic": Item[itemNum].pic, "itemtype": Item[itemNum].type, "itemdata1": Item[itemNum].data1, "itemdata2": Item[itemNum].data2, "itemdata3": Item[itemNum].data3}])
    g.conn.sendDataTo(index, packet)


def sendMapDone(index):
    g.serverLogger.debug('sendMapDone()')
    packet = json.dumps([{"packet": ServerPackets.SMapDone}])
    g.conn.sendDataTo(index, packet)


def sendEditMap(index):
    packet = json.dumps([{"packet": ServerPackets.SEditMap}])
    g.conn.sendDataTo(index, packet)

    #sendMapList(index)


def sendItemEditor(index):
    packet = json.dumps([{"packet": ServerPackets.SItemEditor}])
    g.conn.sendDataTo(index, packet)


def sendEditItem(index):
    packet = json.dumps([{"packet": ServerPackets.SEditItem}])
    g.conn.sendDataTo(index, packet)
