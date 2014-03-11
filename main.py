#!/usr/bin/python
#
# libtcod python tutorial
#
#hi bim

import libtcodpy as libtcod
import math
import textwrap
import shelve
import maps
import random



#actual size of the window
SCREEN_WIDTH = 89
SCREEN_HEIGHT = 40

#size of the map
MAP_WIDTH = 80
MAP_HEIGHT = 80

#sizes and coordinates relevant for the GUI
BAR_WIDTH = 20
PANEL_HEIGHT = 8
PANEL_WIDTH = 8
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT
PANEL_X = SCREEN_WIDTH - PANEL_WIDTH

SIDEBAR_HEIGHT = 20
SIDEBAR_WIDTH = 18
SIDEBAR_Y = 0
SIDEBAR_X = 81
#SCREEN_WIDTH - SIDEBAR_WIDTH

MSG_X = BAR_WIDTH + 2
MSG_WIDTH = SCREEN_WIDTH - BAR_WIDTH - 2
MSG_HEIGHT = PANEL_HEIGHT - 1
INVENTORY_WIDTH = 40
CHARACTER_SCREEN_WIDTH = 40
LEVEL_SCREEN_WIDTH = 50


#parameters for dungeon generator
ROOM_MAX_SIZE = 12
ROOM_MIN_SIZE = 5
MAX_ROOMS = 35


#spell values
HEAL_AMOUNT = 40
LIGHTNING_DAMAGE = 40
LIGHTNING_RANGE = 5
CONFUSE_RANGE = 8
CONFUSE_NUM_TURNS = 10
PARALYSE_NUM_TURNS = 4
FIREBALL_RADIUS = 3
FIREBALL_DAMAGE = 25

SINGLE_RADIUS = 0
FIREARM_DMG = 20
PLAYER_RADIUS = 2



#experience and level-ups
LEVEL_UP_BASE = 200
LEVEL_UP_FACTOR = 150
HUNGER_BASE = 5

FOV_ALGO = 0  #default FOV algorithm
FOV_LIGHT_WALLS = True  #light walls or not
TORCH_RADIUS = 8

LIMIT_FPS = 25  #20 frames-per-second maximum

color_dark_wall = libtcod.Color(22, 22, 22)
color_light_wall = libtcod.Color(54, 54, 54)
color_dark_ground = libtcod.Color(48, 38, 38)
color_light_ground = libtcod.Color(86, 76, 76)


class Tile:
	#a tile of the map and its properties
	def __init__(self, blocked, sludge, bar, door, water, block_sight=None):
		self.blocked = blocked

		self.sludge = sludge
		self.bar = bar
		self.door = door
		self.water = water

		#all tiles start unexplored
		self.explored = False

		#by default, if a tile is blocked, it also blocks sight
		if block_sight is None: block_sight = blocked
		self.block_sight = block_sight


class Rect:
	#a rectangle on the map. used to characterize a room.
	def __init__(self, x, y, w, h):
		self.x1 = x
		self.y1 = y
		self.x2 = x + w
		self.y2 = y + h

	def center(self):
		center_x = (self.x1 + self.x2) / 2
		center_y = (self.y1 + self.y2) / 2
		return (center_x, center_y)

	def intersect(self, other):
		#returns true if this rectangle intersects with another one
		return (self.x1 <= other.x2 and self.x2 >= other.x1 and
				self.y1 <= other.y2 and self.y2 >= other.y1)


class Object:
	#this is a generic object: the player, a monster, an item, the stairs...
	#it's always represented by a character on screen.
	def __init__(self, x, y, char, name, color, make=None, desc=None, value=0, blocks=False, open=None, always_visible=False, fighter=None, nonplayerchar=None, ai=None, item=None,
				 equipment=None, furniture=None):
		self.x = x
		self.y = y
		self.char = char
		self.name = name
		self.make = make
		self.desc = desc
		self.value = value
		self.color = color
		self.blocks = blocks
		self.open = open
		self.always_visible = always_visible
		self.fighter = fighter

		if self.fighter:  #let the fighter component know who owns it
			self.fighter.owner = self

		self.nonplayerchar = nonplayerchar
		if self.nonplayerchar:
			self.nonplayerchar.owner = self

		self.ai = ai
		if self.ai:  #let the AI component know who owns it
			self.ai.owner = self

		self.item = item
		if self.item:  #let the Item component know who owns it
			self.item.owner = self

		self.furniture = furniture
		if self.furniture:
			self.furniture.owner = self

		self.equipment = equipment
		if self.equipment:  #let the Equipment component know who owns it
			self.equipment.owner = self

			#there must be an Item component for the Equipment component to work properly
			self.item = Item()
			self.item.owner = self



	def move(self, dx, dy):
		#move by the given amount, if the destination is not blocked
		if not is_blocked(self.x + dx, self.y + dy):
			self.x += dx
			self.y += dy



	#def move_towards(self, target_x, target_y):
	#    #vector from this object to the target, and distance
	#    dx = target_x - self.x
	#    dy = target_y - self.y
	#    distance = math.sqrt(dx ** 2 + dy ** 2)
	#
	#    #normalize it to length 1 (preserving direction), then round it and
	#    #convert to integer so the movement is restricted to the map grid
	#    dx = int(round(dx / distance))
	#    dy = int(round(dy / distance))
	#    self.move(dx, dy)

	#def move_away(self, target_x, target_y):
	#	#vector from this object to the target, and distance
	#	dx = target_x + self.x
	#	dy = target_y + self.y
	#	distance = math.sqrt(dx ** 2 + dy ** 2)

	#	#normalize it to length 1 (preserving direction), then round it and
	#	#convert to integer so the movement is restricted to the map grid
	#	dx = int(round(dx / distance))
	#	dy = int(round(dy / distance))
	#	self.move(dx, dy)

	def distance_to(self, other):
		#return the distance to another object
		dx = other.x - self.x
		dy = other.y - self.y
		return math.sqrt(dx ** 2 + dy ** 2)

	def distance(self, x, y):
		#return the distance to some coordinates
		return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

	def send_to_back(self):
		#make this object be drawn first, so all others appear above it if they're in the same tile.
		global objects
		objects.remove(self)
		objects.insert(0, self)

	def send_to_front(self):
		#make this object be drawn first, so all others appear above it if they're in the same tile.
		global objects
		objects.remove(self)
		objects.insert(100, self)

	def draw(self):
		#only show if it's visible to the player; or it's set to "always visible" and on an explored tile
		if (libtcod.map_is_in_fov(fov_map, self.x, self.y) or
				(self.always_visible and map[self.x][self.y].explored)):
			#set the color and then draw the character that represents this object at its position
			libtcod.console_set_default_foreground(con, self.color)
			libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)

	def clear(self):
		#erase the character that represents this object
		libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE)


class Fighter:
	#combat-related properties and methods (monster, player, NPC).
	def __init__(self, my_path, lastx, lasty, hp, defense, power, dex, accuracy, hack, charge, firearmdmg, firearmacc, eloyalty, vloyalty, ammo, xp, move_speed, flicker, robot=True, paralysis=False, death_function=None, creddrop=None,):
		self.my_path = my_path
		self.lastx = lastx
		self.lasty = lasty

		self.base_max_hp = hp
		self.hp = hp

		self.base_defense = defense
		self.base_power = power
		self.base_hack = hack
		self.base_dex = dex
		self.base_accuracy = accuracy
		self.base_charge = charge

		self.base_eloyalty = eloyalty
		self.base_vloyalty = vloyalty

		self.charge = charge
		self.firearmdmg = firearmdmg
		self.firearmacc = firearmacc
		self.ammo = ammo

		self.xp = xp
		self.death_function = death_function
		self.creddrop = creddrop
		self.base_move_speed = move_speed
		self.flicker = flicker
		self.robot = robot
		self.paralysis = paralysis

	@property
	def power(self):  #return actual power, by summing up the bonuses from all equipped items
		bonus = sum(equipment.power_bonus for equipment in get_all_equipped(self.owner))
		return self.base_power + bonus

	@property
	def defense(self):  #return actual defense, by summing up the bonuses from all equipped items
		bonus = sum(equipment.defense_bonus for equipment in get_all_equipped(self.owner))
		return self.base_defense + bonus

	@property
	def hack(self):  #return actual defense, by summing up the bonuses from all equipped items
		bonus = sum(equipment.hack_bonus for equipment in get_all_equipped(self.owner))
		return self.base_hack + bonus

	@property
	def eloyalty(self):  #return actual defense, by summing up the bonuses from all equipped items
		bonus = sum(equipment.eloyalty_bonus for equipment in get_all_equipped(self.owner))
		return self.base_eloyalty + bonus

	@property
	def vloyalty(self):  #return actual defense, by summing up the bonuses from all equipped items
		bonus = sum(equipment.vloyalty_bonus for equipment in get_all_equipped(self.owner))
		return self.base_vloyalty + bonus

	@property
	def dex(self):
		bonus = sum(equipment.dex_bonus for equipment in get_all_equipped(self.owner))
		return self.base_dex + bonus

	@property
	def accuracy(self):
		bonus = sum(equipment.accuracy_bonus for equipment in get_all_equipped(self.owner))
		return self.base_accuracy + bonus

	@property
	def move_speed(self):
		return self.base_move_speed

	@property
	def max_hp(self):  #return actual max_hp, by summing up the bonuses from all equipped items
		bonus = sum(equipment.max_hp_bonus for equipment in get_all_equipped(self.owner))
		return self.base_max_hp + bonus


	def move_towards(self, target_x, target_y):
		#get yo' a-star on in a fistful of code?!  this lib is awesome!

		#if no path exists yet, get right onto that, stat!
		if self.my_path is 0:
			self.my_path = libtcod.path_new_using_map(fov_map, 1.0)

		reblock = False

		#need some logic here...constantly refresh path seems omniscient and computationally expensive

		if not libtcod.map_is_walkable(fov_map, target_x, target_y):
			reblock = True

		libtcod.map_set_properties(fov_map, target_x, target_y, True, True)	#momentarily set the target to unblocked so the pathing works. kludgy, I know, but easier than writing my own a*!!!!

		libtcod.path_compute(self.my_path, self.owner.x, self.owner.y, target_x, target_y)

		if reblock:
			libtcod.map_set_properties(fov_map, target_x, target_y, True, False) #kludge moment over. resume normal viewing!

		if not libtcod.path_is_empty(self.my_path):
			x, y = libtcod.path_walk(self.my_path,True)
			if x and not is_blocked(x,y) and libtcod.path_size(self.my_path) < 10: #more than ten is too far, don't worry about it
				libtcod.map_set_properties(fov_map, self.owner.x, self.owner.y, True, True)
				self.owner.x = x
				self.owner.y = y
				libtcod.map_set_properties(fov_map, x, y, True, False)
			else:
				self.owner.move(libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1))

	def move_away(self, target_x, target_y):
		#get yo' a-star on in a fistful of code?!  this lib is awesome!

		#if no path exists yet, get right onto that, stat!
		if self.my_path is 0:
			self.my_path = libtcod.path_new_using_map(fov_map, 1.0)

		reblock = False

		#need some logic here...constantly refresh path seems omniscient and computationally expensive

		if not libtcod.map_is_walkable(fov_map, target_x, target_y):
			reblock = True

		libtcod.map_set_properties(fov_map, target_x, target_y, True, True)	#momentarily set the target to unblocked so the pathing works. kludgy, I know, but easier than writing my own a*!!!!

		libtcod.path_compute(self.my_path, self.owner.x, self.owner.y, target_x+10, target_y+20)

		if reblock:
			libtcod.map_set_properties(fov_map, target_x+10, target_y+20, True, False) #kludge moment over. resume normal viewing!

		if not libtcod.path_is_empty(self.my_path):
			x, y = libtcod.path_walk(self.my_path,True)
			if x and not is_blocked(x,y) and libtcod.path_size(self.my_path) < 10: #more than ten is too far, don't worry about it
				libtcod.map_set_properties(fov_map, self.owner.x, self.owner.y, True, True)
				self.owner.x = x
				self.owner.y = y
				libtcod.map_set_properties(fov_map, x, y, True, False)
			else:
				self.owner.move(libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1))

	def shoot(self, target):
		#a simple formula for attack damage
		global game_turn
		damage = (self.firearmdmg - target.fighter.defense) + libtcod.random_get_int(0, 0, 6)
		tohit = ((self.dex / 4) + self.firearmacc + 2) - libtcod.random_get_int(0, 0, 4)
		if tohit >= target.fighter.dex:
			if damage > 0:
				#make the target take some damage
				message('The ' + self.owner.name.capitalize() + ' shoots the ' + target.name + ' for ' + str(damage) + ' hit points.')
				target.fighter.take_damage(damage)
			else:
				message('The ' + self.owner.name.capitalize() + ' shoots the ' + target.name + ' but it has no effect!')
		else:
			message('The ' + self.owner.name.capitalize() + ' misses!')


	def attack(self, target):
		#a simple formula for attack damage
		damage = (self.power - target.fighter.defense) + libtcod.random_get_int(0, 0, 3)
		tohit = ((self.dex / 2) + self.accuracy) - libtcod.random_get_int(0, 0, 3)
		if tohit >= target.fighter.dex:
			if damage > 0:
				#make the target take some damage
				message('The ' + self.owner.name.capitalize() + ' attacks the ' + target.name + ' for ' + str(damage) + ' hit points.')
				target.fighter.take_damage(damage)

			else:
				message('The ' + self.owner.name.capitalize() + ' attacks the ' + target.name + ' but it has no effect!')
		else:
			message('The ' + self.owner.name.capitalize() + ' misses!')

	def lightattack(self, target):
		#a simple formula for attack damage
		damage = ((self.power - target.fighter.defense) - 2) + libtcod.random_get_int(0, 0, 3)
		tohit = (((self.dex / 2) + self.accuracy)+2) - libtcod.random_get_int(0, 0, 3)
		if tohit >= target.fighter.dex:
			if damage > 0:
				#make the target take some damage
				message('The ' + self.owner.name.capitalize() + ' quickly hits the ' + target.name + ' for ' + str(damage) + ' hit points.')
				target.fighter.take_damage(damage)

			else:
				message('The ' + self.owner.name.capitalize() + ' quickly attacks the ' + target.name + ' but it has no effect!')
		else:
			message('The ' + self.owner.name.capitalize() + ' misses!')

	def take_damage(self, damage):
		#apply damage if possible
		if damage > 0:
			self.hp -= damage
			self.flicker = 1

			if self.hp <= 4 and self.hp > 0 :
				message('The ' + self.owner.name.capitalize() + ' looks badly wounded!')

			#check for death. if there's a death function, call it
			if self.hp <= 0:
				function = self.death_function
				if function is not None:
					function(self.owner)

				if self.owner != player:  #yield experience to the player
					player.fighter.xp += self.xp

	def heal(self, amount):
		#heal by the given amount, without going over the maximum
		self.hp += amount
		if self.hp > self.max_hp:
			self.hp = self.max_hp

	def paralyse(self, target):
		#paralyse the player
		message('The dog bites you', libtcod.blue)
		target.fighter.become_paralysed()

	def become_paralysed(self):
		global counter

		if self.paralysis==False:
			self.paralysis=True
			counter = PARALYSE_NUM_TURNS
		else:
			if counter > 0:
				counter-=1
				take_game_turn()
			else:
				self.paralysis=False


class NonplayerChar:
	#combat-related properties and methods (monster, player, NPC).
	def __init__(self, my_path, lastx, lasty, hp, defense, power, dex, accuracy, hack, eloyalty, vloyalty, xp, move_speed, flicker, robot=True, paralysis=False, death_function=None, creddrop=None, use_function=None):
		self.my_path = my_path
		self.lastx = lastx
		self.lasty = lasty

		self.base_max_hp = hp
		self.hp = hp

		self.base_defense = defense
		self.base_power = power
		self.base_hack = hack
		self.base_dex = dex
		self.base_accuracy = accuracy

		self.base_eloyalty = eloyalty
		self.base_vloyalty = vloyalty

		self.xp = xp
		self.death_function = death_function
		self.creddrop = creddrop
		self.base_move_speed = move_speed
		self.flicker = flicker
		self.robot = robot
		self.use_function = use_function

	@property
	def power(self):  #return actual power, by summing up the bonuses from all equipped items
		bonus = sum(equipment.power_bonus for equipment in get_all_equipped(self.owner))
		return self.base_power + bonus

	@property
	def defense(self):  #return actual defense, by summing up the bonuses from all equipped items
		bonus = sum(equipment.defense_bonus for equipment in get_all_equipped(self.owner))
		return self.base_defense + bonus

	@property
	def hack(self):  #return actual defense, by summing up the bonuses from all equipped items
		bonus = sum(equipment.hack_bonus for equipment in get_all_equipped(self.owner))
		return self.base_hack + bonus

	@property
	def eloyalty(self):  #return actual defense, by summing up the bonuses from all equipped items
		bonus = sum(equipment.eloyalty_bonus for equipment in get_all_equipped(self.owner))
		return self.base_eloyalty + bonus

	@property
	def vloyalty(self):  #return actual defense, by summing up the bonuses from all equipped items
		bonus = sum(equipment.vloyalty_bonus for equipment in get_all_equipped(self.owner))
		return self.base_vloyalty + bonus

	@property
	def dex(self):
		bonus = sum(equipment.dex_bonus for equipment in get_all_equipped(self.owner))
		return self.base_dex + bonus

	@property
	def accuracy(self):
		bonus = sum(equipment.accuracy_bonus for equipment in get_all_equipped(self.owner))
		return self.base_accuracy + bonus

	@property
	def move_speed(self):
		return self.base_move_speed

	@property
	def max_hp(self):  #return actual max_hp, by summing up the bonuses from all equipped items
		bonus = sum(equipment.max_hp_bonus for equipment in get_all_equipped(self.owner))
		return self.base_max_hp + bonus


	def move_towards(self, target_x, target_y):
		#get yo' a-star on in a fistful of code?!  this lib is awesome!

		#if no path exists yet, get right onto that, stat!
		if self.my_path is 0:
			self.my_path = libtcod.path_new_using_map(fov_map, 1.0)

		reblock = False

		#need some logic here...constantly refresh path seems omniscient and computationally expensive

		if not libtcod.map_is_walkable(fov_map, target_x, target_y):
			reblock = True

		libtcod.map_set_properties(fov_map, target_x, target_y, True, True)	#momentarily set the target to unblocked so the pathing works. kludgy, I know, but easier than writing my own a*!!!!

		libtcod.path_compute(self.my_path, self.owner.x, self.owner.y, target_x, target_y)

		if reblock:
			libtcod.map_set_properties(fov_map, target_x, target_y, True, False) #kludge moment over. resume normal viewing!

		if not libtcod.path_is_empty(self.my_path):
			x, y = libtcod.path_walk(self.my_path,True)
			if x and not is_blocked(x,y) and libtcod.path_size(self.my_path) < 10: #more than ten is too far, don't worry about it
				libtcod.map_set_properties(fov_map, self.owner.x, self.owner.y, True, True)
				self.owner.x = x
				self.owner.y = y
				libtcod.map_set_properties(fov_map, x, y, True, False)
			else:
				self.owner.move(libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1))

	def move_away(self, target_x, target_y):
		#get yo' a-star on in a fistful of code?!  this lib is awesome!

		#if no path exists yet, get right onto that, stat!
		if self.my_path is 0:
			self.my_path = libtcod.path_new_using_map(fov_map, 1.0)

		reblock = False

		#need some logic here...constantly refresh path seems omniscient and computationally expensive

		if not libtcod.map_is_walkable(fov_map, target_x, target_y):
			reblock = True

		libtcod.map_set_properties(fov_map, target_x, target_y, True, True)	#momentarily set the target to unblocked so the pathing works. kludgy, I know, but easier than writing my own a*!!!!

		libtcod.path_compute(self.my_path, self.owner.x, self.owner.y, target_x+10, target_y+20)

		if reblock:
			libtcod.map_set_properties(fov_map, target_x+10, target_y+20, True, False) #kludge moment over. resume normal viewing!

		if not libtcod.path_is_empty(self.my_path):
			x, y = libtcod.path_walk(self.my_path,True)
			if x and not is_blocked(x,y) and libtcod.path_size(self.my_path) < 10: #more than ten is too far, don't worry about it
				libtcod.map_set_properties(fov_map, self.owner.x, self.owner.y, True, True)
				self.owner.x = x
				self.owner.y = y
				libtcod.map_set_properties(fov_map, x, y, True, False)
			else:
				self.owner.move(libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1))

	def shoot(self, target):
		#a simple formula for attack damage
		global game_turn
		damage = (self.firearmdmg - target.fighter.defense) + libtcod.random_get_int(0, 0, 6)
		tohit = ((self.dex / 4) + self.firearmacc + 2) - libtcod.random_get_int(0, 0, 4)
		if tohit >= target.fighter.dex:
			if damage > 0:
				#make the target take some damage
				message('The ' + self.owner.name.capitalize() + ' shoots the ' + target.name + ' for ' + str(damage) + ' hit points.')
				target.fighter.take_damage(damage)
			else:
				message('The ' + self.owner.name.capitalize() + ' shoots the ' + target.name + ' but it has no effect!')
		else:
			message('The ' + self.owner.name.capitalize() + ' misses!')

	def use(self):
		#just call the "use_function" if it is defined
		if self.use_function is None:
			message('The ' + self.owner.name + ' cannot be used.')

	def attack(self, target):
		#a simple formula for attack damage
		damage = (self.power - target.fighter.defense) + libtcod.random_get_int(0, 0, 3)
		tohit = ((self.dex / 2) + self.accuracy) - libtcod.random_get_int(0, 0, 3)
		if tohit >= target.fighter.dex:
			if damage > 0:
				#make the target take some damage
				message('The ' + self.owner.name.capitalize() + ' attacks the ' + target.name + ' for ' + str(damage) + ' hit points.')
				target.fighter.take_damage(damage)

			else:
				message('The ' + self.owner.name.capitalize() + ' attacks the ' + target.name + ' but it has no effect!')
		else:
			message('The ' + self.owner.name.capitalize() + ' misses!')

	def take_damage(self, damage):
		#apply damage if possible
		if damage > 0:
			self.hp -= damage
			self.flicker = 1

			if self.hp <= 4 and self.hp > 0 :
				message('The ' + self.owner.name.capitalize() + ' looks badly wounded!')

			#check for death. if there's a death function, call it
			if self.hp <= 0:
				function = self.death_function
				if function is not None:
					function(self.owner)

				if self.owner != player:  #yield experience to the player
					player.fighter.xp += self.xp


class Item:

	#an item that can be picked up and used.
	def __init__(self, use_function=None):
		self.use_function = use_function

	def pick_up(self):
		#add to the player's inventory and remove from the map
		if len(inventory) >= 10:
			message('Your inventory is full, cannot pick up ' + self.owner.name + '.', libtcod.red)
		else:
			inventory.append(self.owner)
			objects.remove(self.owner)
			message('You picked up ' + self.owner.name + '!', libtcod.green)

			#special case: automatically equip, if the corresponding equipment slot is unused
			equipment = self.owner.equipment
			if equipment and get_equipped_in_slot(equipment.slot) is None:
				equipment.equip()

	def drop(self):
		#special case: if the object has the Equipment component, dequip it before dropping
		if self.owner.equipment:
			self.owner.equipment.dequip()

		#add to the map and remove from the player's inventory. also, place it at the player's coordinates
		objects.append(self.owner)
		inventory.remove(self.owner)
		self.owner.x = player.x
		self.owner.y = player.y
		message('You dropped a ' + self.owner.name + '.', libtcod.yellow)

	def sell(self, obj):
		global cred
		#special case: if the object has the Equipment component, dequip it before dropping
		if self.owner.equipment:
			self.owner.equipment.dequip()

		objects.append(self.owner)
		inventory.remove(self.owner)
		if self.owner.value !=0:
			message('Thanks for that')
			cred += self.owner.value
		else:
			message('It isnt worth anything')

	def use(self):
		#special case: if the object has the Equipment component, the "use" action is to equip/dequip
		if self.owner.equipment:
			self.owner.equipment.toggle_equip()
			return

		#just call the "use_function" if it is defined
		if self.use_function is None:
			message('The ' + self.owner.name + ' cannot be used.')
		else:
			if self.use_function() != 'cancelled':
				inventory.remove(self.owner)  #destroy after use, unless it was cancelled for some reason


class Furniture:
	#an item that can be picked up and used.
	def __init__(self, use_function=None):
		self.use_function = use_function


	def use(self):
		#just call the "use_function" if it is defined
		if self.use_function is None:
			message('The ' + self.owner.name + ' cannot be used.')


class Equipment:
	#an object that can be equipped, yielding bonuses. automatically adds the Item component.
	def __init__(self, slot, power_bonus=0, defense_bonus=0, hack_bonus=0, dex_bonus=0, accuracy_bonus=0, max_hp_bonus=0, firearm_dmg_bonus=0, eloyalty_bonus=0, vloyalty_bonus=0, firearm_acc_bonus=0):
		self.power_bonus = power_bonus
		self.defense_bonus = defense_bonus
		self.hack_bonus = hack_bonus
		self.dex_bonus = dex_bonus
		self.accuracy_bonus = accuracy_bonus
		self.max_hp_bonus = max_hp_bonus
		self.firearm_dmg_bonus = firearm_dmg_bonus
		self.firearm_acc_bonus = firearm_acc_bonus

		self.eloyalty_bonus = eloyalty_bonus
		self.vloyalty_bonus = vloyalty_bonus

		self.slot = slot
		self.is_equipped = False

	def toggle_equip(self):  #toggle equip/dequip status
		if self.is_equipped:
			self.dequip()
		else:
			self.equip()

	def equip(self):
		#if the slot is already being used, dequip whatever is there first
		old_equipment = get_equipped_in_slot(self.slot)
		if old_equipment is not None:
			old_equipment.dequip()

		#equip object and show a message about it
		self.is_equipped = True
		message('Equipped ' + self.owner.name + ' (' + self.slot + ')', libtcod.light_green)

	def dequip(self):
		#dequip object and show a message about it
		if not self.is_equipped: return
		self.is_equipped = False
		message('Dequipped ' + self.owner.name + ' from ' + self.slot + '.', libtcod.light_yellow)


#AI:
class BasicMonster:
	def take_turn(self):
		global game_turn
		monster = self.owner
		if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):
			#if sees player, stores location
			monster.fighter.lastx = player.x
			monster.fighter.lasty = player.y

			if monster.distance_to(player) >= 2:
				monster.fighter.move_towards(player.x, player.y)

			elif player.fighter.hp > 0:
				monster.fighter.attack(player)


		else:
			#if hasn't seen ever player, random moving
			if monster.fighter.lastx == None and monster.fighter.lasty == None:
				self.owner.move(libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1))
			else:
				#if seen player, move towards the location
				monster.fighter.move_towards(monster.fighter.lastx, monster.fighter.lasty)
				#same location now where last saw player, set location to none so it resumes normal activity
				if monster.x == monster.fighter.lastx and monster.y == monster.fighter.lasty and monster.distance_to(player) <= TORCH_RADIUS * 1.5:
					monster.fighter.lastx = player.x + libtcod.random_get_int(0, -TORCH_RADIUS/2, TORCH_RADIUS/2)
					monster.fighter.lasty = player.y + libtcod.random_get_int(0, -TORCH_RADIUS/2, TORCH_RADIUS/2)
				elif monster.x == monster.fighter.lastx and monster.y == monster.fighter.lasty and monster.distance_to(player) <= TORCH_RADIUS * 2:
					monster.fighter.lastx = player.x + libtcod.random_get_int(0, -TORCH_RADIUS, TORCH_RADIUS)
					monster.fighter.lasty = player.y + libtcod.random_get_int(0, -TORCH_RADIUS, TORCH_RADIUS)
				elif monster.x == monster.fighter.lastx and monster.y == monster.fighter.lasty:
					monster.fighter.lastx = None
					monster.fighter.lasty = None


class CleverMonster:
	def take_turn(self):
		global game_turn
		monster = self.owner
		lowhp = 20
		if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):
			#if sees player, stores location
			monster.fighter.lastx = player.x
			monster.fighter.lasty = player.y

			if monster.fighter.ammo > 0:
				if monster.distance_to(player) >= 3 and monster.fighter.hp > lowhp:
					monster.fighter.shoot(player)
					monster.fighter.ammo -= 1
				elif monster.distance_to(player) >= 2 and monster.fighter.hp > lowhp:
					monster.fighter.move_towards(player.x, player.y)
				elif player.fighter.hp > 0 and monster.fighter.hp > lowhp:
					monster.fighter.attack(player)
				elif player.fighter.hp > 0 and monster.fighter.hp < lowhp:
					monster.fighter.move_away(player.x, player.y)
				elif monster.distance_to(player) >= 2 and monster.fighter.hp < lowhp:
					monster.fighter.move_away(player.x, player.y)

			else:
				if monster.distance_to(player) >= 2 and monster.fighter.hp > lowhp:
					monster.fighter.move_towards(player.x, player.y)
				elif monster.distance_to(player) >= 2 and monster.fighter.hp < lowhp:
					monster.fighter.move_away(player.x, player.y)
				elif player.fighter.hp > 0 and monster.fighter.hp > lowhp:
					monster.fighter.attack(player)
				elif player.fighter.hp > 0 and monster.fighter.hp < lowhp:
					monster.fighter.move_away(player.x, player.y)

		else:
			#if hasn't seen ever player, random moving
			if monster.fighter.lastx == None and monster.fighter.lasty == None:
				self.owner.move(libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1))
			else:
				#if seen player, move towards the location
				monster.fighter.move_towards(monster.fighter.lastx, monster.fighter.lasty)
				#same location now where last saw player, set location to none so it resumes normal activity
				if monster.x == monster.fighter.lastx and monster.y == monster.fighter.lasty and monster.distance_to(player) <= TORCH_RADIUS * 1.5:
					monster.fighter.lastx = player.x + libtcod.random_get_int(0, -TORCH_RADIUS/2, TORCH_RADIUS/2)
					monster.fighter.lasty = player.y + libtcod.random_get_int(0, -TORCH_RADIUS/2, TORCH_RADIUS/2)
				elif monster.x == monster.fighter.lastx and monster.y == monster.fighter.lasty and monster.distance_to(player) <= TORCH_RADIUS * 2:
					monster.fighter.lastx = player.x + libtcod.random_get_int(0, -TORCH_RADIUS, TORCH_RADIUS)
					monster.fighter.lasty = player.y + libtcod.random_get_int(0, -TORCH_RADIUS, TORCH_RADIUS)
				elif monster.x == monster.fighter.lastx and monster.y == monster.fighter.lasty:
					monster.fighter.lastx = None
					monster.fighter.lasty = None


class BasicDog:
	def take_turn(self):
		global game_turn
		monster = self.owner
		if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):
			#if sees player, stores location
			monster.fighter.lastx = player.x
			monster.fighter.lasty = player.y

			if monster.distance_to(player) >= 2:
				monster.fighter.move_towards(player.x, player.y)
				take_game_turn()
			elif player.fighter.hp > 0:
				if random.randint(0,100) < 10:
					monster.fighter.paralyse(player)
				else:
					monster.fighter.attack(player)
					take_game_turn()

		else:
			#if hasn't seen ever player, random moving
			if monster.fighter.lastx == None and monster.fighter.lasty == None:
				self.owner.move(libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1))
			else:
				#if seen player, move towards the location
				monster.fighter.move_towards(monster.fighter.lastx, monster.fighter.lasty)
				#same location now where last saw player, set location to none so it resumes normal activity
				if monster.x == monster.fighter.lastx and monster.y == monster.fighter.lasty and monster.distance_to(player) <= TORCH_RADIUS * 1.5:
					monster.fighter.lastx = player.x + libtcod.random_get_int(0, -TORCH_RADIUS/2, TORCH_RADIUS/2)
					monster.fighter.lasty = player.y + libtcod.random_get_int(0, -TORCH_RADIUS/2, TORCH_RADIUS/2)
				elif monster.x == monster.fighter.lastx and monster.y == monster.fighter.lasty and monster.distance_to(player) <= TORCH_RADIUS * 2:
					monster.fighter.lastx = player.x + libtcod.random_get_int(0, -TORCH_RADIUS, TORCH_RADIUS)
					monster.fighter.lasty = player.y + libtcod.random_get_int(0, -TORCH_RADIUS, TORCH_RADIUS)
				elif monster.x == monster.fighter.lastx and monster.y == monster.fighter.lasty:
					monster.fighter.lastx = None
					monster.fighter.lasty = None


class BasicHologram:
	def take_turn(self):
		monster = self.owner
		if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):
			#if sees player, stores location
			monster.fighter.lastx = player.x
			monster.fighter.lasty = player.y

			if monster.distance_to(player) >= 2:
				monster.fighter.move_towards(player.x, player.y)

		else:
			#if hasn't seen ever player, random moving
			if monster.fighter.lastx == None and monster.fighter.lasty == None:
				self.owner.move(libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1))
			else:
				#if seen player, move towards the location
				monster.fighter.move_towards(monster.fighter.lastx, monster.fighter.lasty)
				#same location now where last saw player, set location to none so it resumes normal activity
				if monster.x == monster.fighter.lastx and monster.y == monster.fighter.lasty:
					monster.fighter.lastx = None
					monster.fighter.lasty = None


class BasicNpc:
	def take_turn(self):
		monster = self.owner
		if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):
				self.owner.move(libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1))


class BasicShooter:
	#AI for a basic monster.
	def take_turn(self):
		global game_turn
		#a basic monster takes its turn. if you can see it, it can see you
		monster = self.owner
		if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):

			monster.fighter.lastx = player.x
			monster.fighter.lasty = player.y
			if monster.fighter.ammo > 0:
				if monster.distance_to(player) >= 3:
					monster.fighter.shoot(player)
					monster.fighter.ammo -= 1
				elif monster.distance_to(player) >= 2:
					monster.fighter.move_towards(player.x, player.y)
				elif player.fighter.hp > 0:
					monster.fighter.attack(player)
			else:
				if monster.distance_to(player) >= 2:
					monster.fighter.move_towards(player.x, player.y)
				elif player.fighter.hp > 0:
					monster.fighter.attack(player)

		else:
			#if hasn't seen ever player, random moving
			if monster.fighter.lastx == None and monster.fighter.lasty == None:
				self.owner.move(libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1))
			else:
				#if seen player, move towards the location
				monster.fighter.move_towards(monster.fighter.lastx, monster.fighter.lasty)
				#same location now where last saw player, set location to none so it resumes normal activity
				if monster.x == monster.fighter.lastx and monster.y == monster.fighter.lasty:
					monster.fighter.lastx = None
					monster.fighter.lasty = None

			#if monster.fighter.hp > 6:
			#	if monster.fighter.ammo > 0:
			#	#move towards player if far away
			#		if monster.distance_to(player) <= 3:
			#			monster.fighter.move_towards(player.x, player.y)
			#
			#		#close enough, attack! (if the player is still alive.)
			#		elif player.fighter.hp > 0 and monster.distance_to(player) <= 6:
			#			monster.fighter.shoot(player)
			#			monster.fighter.ammo -= 1
			#
			#		elif player.fighter.hp > 0 and monster.distance_to(player) <= 1:
			#			monster.fighter.attack(player)
			#
			#	else:
			#		if monster.distance_to(player) >= 2:
			#			monster.fighter.move_towards(player.x, player.y)
			#
			#		#close enough, attack! (if the player is still alive.)
			#		elif player.fighter.hp > 0:
			#			monster.fighter.attack(player)
			#else:
			#	monster.move_away(player.x, player.y)


	   #AI for a basic monster.


class BasicTurret:
	#AI for a basic monster.
	tookturn = 0
	def take_turn(self):
		global game_turn

		#a basic monster takes its turn. if you can see it, it can see you
		monster = self.owner
		if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):
			if player.fighter.vloyalty < 5:
				if monster.fighter.ammo > 0 and player.fighter.hp > 0 and monster.distance_to(player) < 6:
					monster.fighter.shoot(player)
					monster.fighter.ammo -= 1

				elif monster.fighter.ammo <= 0 and BasicTurret.tookturn == 0:
					message('The ' + str(self.owner.name) + ' shuts down!')
					monster.fighter.defense += 4
					BasicTurret.tookturn += 1
			else:
				message('The ' + str(self.owner.name) + ' senses your loyalty and shuts down!')
				monster.fighter.defense += 4
				BasicTurret.tookturn += 1

			#if monster.fighter.hp > 6:
			#	if monster.fighter.ammo > 0:
			#	#move towards player if far away
			#		if monster.distance_to(player) <= 3:
			#			monster.fighter.move_towards(player.x, player.y)
			#
			#		#close enough, attack! (if the player is still alive.)
			#		elif player.fighter.hp > 0 and monster.distance_to(player) <= 6:
			#			monster.fighter.shoot(player)
			#			monster.fighter.ammo -= 1
			#
			#		elif player.fighter.hp > 0 and monster.distance_to(player) <= 1:
			#			monster.fighter.attack(player)
			#
			#	else:
			#		if monster.distance_to(player) >= 2:
			#			monster.fighter.move_towards(player.x, player.y)
			#
			#		#close enough, attack! (if the player is still alive.)
			#		elif player.fighter.hp > 0:
			#			monster.fighter.attack(player)
			#else:
			#	monster.move_away(player.x, player.y)


	   #AI for a basic monster.


class AlliedMonster:
	#AI for a basic monster.
	def __init__(self, old_ai, num_turns=CONFUSE_NUM_TURNS):
		self.old_ai = old_ai
		self.num_turns = num_turns

	def take_turn(self):
		global game_turn
		monster = closest_monster(2)
		#a basic monster takes its turn. if you can see it, it can see you

				#move towards player if far away
		if monster.distance_to(monster) >= 2:
			monster.move_towards(monster.x, monster.y)

			#close enough, attack! (if the player is still alive.)
		elif monster.fighter.hp > 0:
			monster.fighter.attack(monster)

		else:
			message('The ' + self.owner.name + ' is no longer slaved to you!', libtcod.red)



	#AI for a temporarily confused monster (reverts to previous AI after a while).

	#def take_turn(self):
	#    if self.num_turns > 0:  #still confused...
	#        #move in a random direction, and decrease the number of turns confused
	#        self.owner.move(libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1))
	#        self.num_turns -= 1
	#
	#    else:  #restore the previous AI (this one will be deleted because it's not referenced anymore)
	#        self.owner.ai = self.old_ai
	#        message('The ' + self.owner.name + ' is no longer confused!', libtcod.red)


class ConfusedMonster:
	#AI for a temporarily confused monster (reverts to previous AI after a while).
	def __init__(self, old_ai, num_turns=CONFUSE_NUM_TURNS):
		self.old_ai = old_ai
		self.num_turns = num_turns

	def take_turn(self):
		if self.num_turns > 0:  #still confused...
			#move in a random direction, and decrease the number of turns confused
			self.owner.move(libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1))
			self.num_turns -= 1

		else:  #restore the previous AI (this one will be deleted because it's not referenced anymore)
			self.owner.ai = self.old_ai
			message('The ' + self.owner.name + ' is no longer confused!', libtcod.red)




## Engine stuff

def is_blocked(x, y):
	#first test the map tile
	if map[x][y].blocked:
		return True

	#now check for any blocking objects
	for object in objects:
		if object.blocks and object.x == x and object.y == y:
			return True

	return False


def sightblocked (x, y):
	map[x][y].block_sight = True


def create_room(room):
	global map
	#go through the tiles in the rectangle and make them passable
	for x in range(room.x1 + 1, room.x2):
		for y in range(room.y1 + 1, room.y2):
			map[x][y].blocked = False
			map[x][y].block_sight = False


def create_h_tunnel(x1, x2, y):
	global map
	#horizontal tunnel. min() and max() are used in case x1>x2
	for x in range(min(x1, x2), max(x1, x2) + 1):
		map[x][y].blocked = False
		map[x][y].block_sight = False


def create_v_tunnel(y1, y2, x):
	global map
	#vertical tunnel
	for y in range(min(y1, y2), max(y1, y2) + 1):
		map[x][y].blocked = False
		map[x][y].block_sight = False


def make_map():
	global map, objects, stairs, upstairs, factorystairs, factoryexitstairs, MAP_HEIGHT, MAP_WIDTH

	#the list of objects with just the player
	objects = [player]

	if dungeon_level == 1:
		#use custom map from samples
		maps.hubmap

		#NOTE: height and width should really be lower-cased, since we are not treating them as constants anymore
		MAP_HEIGHT = len(maps.hubmap)
		MAP_WIDTH = len(maps.hubmap[0])

		#declare variable 'map' and fill it with blocked tilesc
		map = [[Tile(True, sludge=False, bar=False, door=False, water=False) for y in range(MAP_HEIGHT)] for x in range(MAP_WIDTH)]
		for y in range(MAP_HEIGHT):
			for x in range(MAP_WIDTH):
				if maps.hubmap[y][x] == ' ':
					map[x][y] = Tile(False, False, False, False, False)

				elif maps.hubmap[y][x] == '~':
					map[x][y] = Tile(False, True, False, False, False)

				elif maps.hubmap[y][x] == '_':
					map[x][y] = Tile(False, False, True, False, False)
					furniture_component = Furniture(nouse)
					furniture = Object(x, y, 178, 'bar', libtcod.brass, desc='bar', blocks=True, furniture=furniture_component)
					objects.append(furniture)

				elif maps.hubmap[y][x] == 'X':
					map[x][y] = Tile(False, False, False, True, False)
					furniture_component = Furniture(use_function=door)
					furniture = Object(x, y, 'X', 'door', libtcod.brass, desc='a door', blocks=True, always_visible=True, furniture=furniture_component)
					objects.append(furniture)
					map[x][y].block_sight = True

				elif maps.hubmap[y][x] == 'W':
					map[x][y] = Tile(False, False, False, False, True)



		#upstairs = Object(2, 3, '>', 'upstairs', libtcod.white, always_visible=True)
		#objects.append(upstairs)
		#upstairs.x, upstairs.y = random_unblocked_tile_on_map()
		#upstairs.send_to_back()  #so it's drawn below the monsters

		stairs = Object(65, 2, '<', 'stairs', libtcod.white, always_visible=True)
		objects.append(stairs)
		#stairs.x, stairs.y = random_unblocked_tile_on_map()
		stairs.send_to_back()  #so it's drawn below the monsters

		factorystairs = Object(24, 3, '<', 'factorystairs', libtcod.white, always_visible=True)
		objects.append(factorystairs)
		factorystairs.send_to_back()  #so it's drawn below the monsters

		##Call the hub objects!
		hub()

	elif dungeon_level == 'factory':
		#use custom map from samples


		#NOTE: height and width should really be lower-cased, since we are not treating them as constants anymore
		MAP_HEIGHT = len(maps.factorymap)
		MAP_WIDTH = len(maps.factorymap[0])

		#declare variable 'map' and fill it with blocked tiles
		map = [[Tile(True, sludge=False, bar=False, door=False, water=False) for y in range(MAP_HEIGHT)] for x in range(MAP_WIDTH)]
		for y in range(MAP_HEIGHT):
			for x in range(MAP_WIDTH):
				if maps.factorymap[y][x] == ' ':
					map[x][y] = Tile(False, False, False, False, False)

				elif maps.factorymap[y][x] == '~':
					map[x][y] = Tile(False, True, False, False, False)

				elif maps.factorymap[y][x] == '_':
					map[x][y] = Tile(False, False, True, False, False)
					furniture_component = Furniture(nouse)
					furniture = Object(x, y, 178, 'bar', libtcod.brass, desc='bar', blocks=True, furniture=furniture_component)
					objects.append(furniture)

				elif maps.factorymap[y][x] == 'X':
					map[x][y] = Tile(False, False, False, True, False)
					furniture_component = Furniture(use_function=door)
					furniture = Object(x, y, 'X', 'door', libtcod.brass, desc='a door', blocks=True, furniture=furniture_component)
					objects.append(furniture)
					map[x][y].block_sight = True

				elif maps.factorymap[y][x] == 'W':
					map[x][y] = Tile(False, False, False, False, True, False)


		#as I can't be bothered to keep defining the stairs global, I've just put in an invisible one:
		upstairs = Object(0, 0, ' ', 'upstairs', libtcod.black, always_visible=False)

		factoryexitstairs = Object(24, 3, '>', 'factory exit stairs', libtcod.white, always_visible=True)
		objects.append(factoryexitstairs)
		#stairs.x, stairs.y = random_unblocked_tile_on_map()
		factoryexitstairs.send_to_back()  #so it's drawn below the monsters



	else:
	#fill map with "blocked" tiles
		map = [[Tile(True, False, False, False, False)
				for y in range(MAP_HEIGHT)]
			   for x in range(MAP_WIDTH)]

		rooms = []
		num_rooms = 0

		for r in range(MAX_ROOMS):
			#random width and height
			w = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
			h = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
			#random position without going out of the boundaries of the map
			x = libtcod.random_get_int(0, 0, MAP_WIDTH - w - 1)
			y = libtcod.random_get_int(0, 0, MAP_HEIGHT - h - 1)

			#"Rect" class makes rectangles easier to work with
			new_room = Rect(x, y, w, h)

			#run through the other rooms and see if they intersect with this one
			failed = False
			for other_room in rooms:
				if new_room.intersect(other_room):
					failed = True
					break

			if not failed:
				#this means there are no intersections, so this room is valid

				#"paint" it to the map's tiles
				create_room(new_room)

				#add some contents to this room
				place_objects(new_room)

				#add furniture
				place_furniture(new_room)

				#add monsters
				place_monsters(new_room)

				#center coordinates of new room, will be useful later
				(new_x, new_y) = new_room.center()

				if num_rooms == 0:
					#this is the first room, where the player starts at
					player.x = new_x
					player.y = new_y
				else:
					#all rooms after the first:
					#connect it to the previous room with a tunnel

					#center coordinates of previous room
					(prev_x, prev_y) = rooms[num_rooms - 1].center()

					#draw a coin (random number that is either 0 or 1)
					if libtcod.random_get_int(0, 0, 1) == 1:
						#first move horizontally, then vertically
						create_h_tunnel(prev_x, new_x, prev_y)
						create_v_tunnel(prev_y, new_y, new_x)
					else:
						#first move vertically, then horizontally
						create_v_tunnel(prev_y, new_y, prev_x)
						create_h_tunnel(prev_x, new_x, new_y)

				#finally, append the new room to the list
				rooms.append(new_room)
				num_rooms += 1

		stairs = Object(new_x, new_y, '<', 'stairs', libtcod.white, always_visible=True)
		objects.append(stairs)
		stairs.send_to_back()  #so it's drawn below the monsters

		upstairs = Object(2, 3, '>', 'upstairs', libtcod.white, always_visible=True)
		objects.append(upstairs)
		upstairs.x, upstairs.y = random_unblocked_tile_on_map()
		upstairs.send_to_back()  #so it's drawn below the monsters


def random_unblocked_tile_on_map():
	tries = 1000
	#1000 tries, and we'll punt - most probably producing an error in the calling code
	for i in range(tries):
		x = libtcod.random_get_int(0, 0, MAP_WIDTH - 1)
		y = libtcod.random_get_int(0, 0, MAP_HEIGHT - 1)
		if not is_blocked(x, y):
			return x, y


def random_choice_index(chances):  #choose one option from list of chances, returning its index
	#the dice will land on some number between 1 and the sum of the chances
	dice = libtcod.random_get_int(0, 1, sum(chances))

	#go through all chances, keeping the sum so far
	running_sum = 0
	choice = 0
	for w in chances:
		running_sum += w

		#see if the dice landed in the part that corresponds to this choice
		if dice <= running_sum:
			return choice
		choice += 1


def random_choice(chances_dict):
	#choose one option from dictionary of chances, returning its key
	chances = chances_dict.values()
	strings = chances_dict.keys()

	return strings[random_choice_index(chances)]


def closest_monster(max_range):
	#find closest enemy, up to a maximum range, and in the player's FOV
	closest_enemy = None
	closest_dist = max_range + 1  #start with (slightly more than) maximum range

	for object in objects:
		if object.fighter and not object == player and libtcod.map_is_in_fov(fov_map, object.x, object.y):
			#calculate distance between this object and the player
			dist = player.distance_to(object)
			if dist < closest_dist:  #it's closer, so remember it
				closest_enemy = object
				closest_dist = dist
	return closest_enemy


def target_tile(max_range=None):
	global key, mouse
	#return the position of a tile left-clicked in player's FOV (optionally in a range), or (None,None) if right-clicked.
	while True:
		#render the screen. this erases the inventory and shows the names of objects under the mouse.
		libtcod.console_flush()
		libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)
		render_all()

		(x, y) = (mouse.cx, mouse.cy)

		if mouse.rbutton_pressed or key.vk == libtcod.KEY_ESCAPE:
			message('Cancelled')
			return (None, None)  #cancel if the player right-clicked or pressed Escape


		#accept the target if the player clicked in FOV, and in case a range is specified, if it's in that range
		if (mouse.lbutton_pressed and libtcod.map_is_in_fov(fov_map, x, y) and
				(max_range is None or player.distance(x, y) <= max_range)):
			return (x, y)


def target_monster(max_range=None):
	#returns a clicked monster inside FOV up to a range, or None if right-clicked
	while True:
		(x, y) = target_tile(max_range)
		if x is None:  #player cancelled
			return None

		#return the first clicked monster, otherwise continue looping
		for obj in objects:
			if obj.x == x and obj.y == y and obj.fighter and obj != player:
				return obj




## Rendering and visuals


def msgbox(text, width=50):
	menu(text, [], width)  #use menu() as a sort of "message box"


def render_bar(x, y, total_width, name, value, maximum, bar_color, back_color):
	#render a bar (HP, experience, etc). first calculate the width of the bar
	bar_width = int(float(value) / maximum * total_width)

	#render the background first
	libtcod.console_set_default_background(sidebar, back_color)
	libtcod.console_rect(sidebar, x, y, total_width, 1, False, libtcod.BKGND_SCREEN)

	#now render the bar on top
	libtcod.console_set_default_background(sidebar, bar_color)
	if bar_width > 0:
		libtcod.console_rect(sidebar, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)

	#finally, some centered text with the values
	libtcod.console_set_default_foreground(sidebar, libtcod.white)
	libtcod.console_print_ex(sidebar, x + total_width / 2, y, libtcod.BKGND_NONE, libtcod.CENTER,
							 name + ': ' + str(value) + '/' + str(maximum))


def menu(header, options, width):
	if len(options) > 26: raise ValueError('Cannot have a menu with more than 26 options.')

	#calculate total height for the header (after auto-wrap) and one line per option
	header_height = libtcod.console_get_height_rect(con, 0, 0, width, SCREEN_HEIGHT, header)
	if header == '':
		header_height = 0
	height = len(options) + header_height

	#create an off-screen console that represents the menu's window
	window = libtcod.console_new(width, height)

	#print the header, with auto-wrap
	libtcod.console_set_default_foreground(window, libtcod.green)
	libtcod.console_print_rect_ex(window, 0, 0, width, height, libtcod.BKGND_ADD, libtcod.LEFT, header)

	#print all the options
	y = header_height
	letter_index = ord('a')
	for option_text in options:
		text = '(' + chr(letter_index) + ') ' + option_text
		libtcod.console_print_ex(window, 0, y, libtcod.BKGND_ADD, libtcod.LEFT, text)
		y += 1
		letter_index += 1

	#blit the contents of "window" to the root console
	x = SCREEN_WIDTH / 2 - width / 2
	y = SCREEN_HEIGHT / 2 - height / 2
	libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)

	#present the root console to the player and wait for a key-press
	libtcod.console_flush()
	key = libtcod.console_wait_for_keypress(True)
	key = libtcod.console_wait_for_keypress(True)

	if key.vk == libtcod.KEY_ENTER and key.lalt:  #(special case) Alt+Enter: toggle fullscreen
		libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen)

	#convert the ASCII code to an index; if it corresponds to an option, return it
	index = key.c - ord('a')
	if index >= 0 and index < len(options): return index
	return None


def message(new_msg, color=libtcod.white):
	#split the message if necessary, among multiple lines
	new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)

	for line in new_msg_lines:
		#if the buffer is full, remove the first line to make room for the new one
		if len(game_msgs) == MSG_HEIGHT:
			del game_msgs[0]

		#add the new line as a tuple, with the text and the color
		game_msgs.append((line, color))


def get_names_under_mouse():
	global mouse
	#return a string with the names of all objects under the mouse

	(x, y) = (mouse.cx, mouse.cy)

	#create a list with the names of all objects at the mouse's coordinates and in FOV
	names = [obj.name for obj in objects
			 if obj.x == x and obj.y == y and libtcod.map_is_in_fov(fov_map, obj.x, obj.y)]

	names = ', '.join(names)  #join the names, separated by commas
	return names.capitalize()


def flicker_all():
	global fov_recompute
	render_all()
	timer = 0
	while (timer < 3):
		for frame in range(5):
			for object in objects:
				if object.fighter and libtcod.map_is_in_fov(fov_map, object.x, object.y) and object.fighter.flicker is not None:
					if object.fighter.robot:
						libtcod.console_set_char_foreground(con, object.x, object.y, libtcod.light_blue)
						libtcod.console_blit(con, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0, 0)
					else:
						libtcod.console_set_char_foreground(con, object.x, object.y, libtcod.dark_red)
						libtcod.console_blit(con, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0, 0)
		libtcod.console_check_for_keypress()
		#render_all()
		libtcod.console_flush()#show result
		timer += 1
	fov_recompute = True
	render_all()
	for object in objects:
		if object.fighter:
			object.fighter.flicker = None


def render_all():
	global fov_map, color_dark_wall, color_light_wall
	global color_dark_ground, color_light_ground
	global fov_recompute, hour
	#plyx = player.x + 2
	#plyy = player.y + 2

	if fov_recompute:
		#recompute FOV if needed (the player moved or something)
		fov_recompute = False
		libtcod.map_compute_fov(fov_map, player.x, player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)

		#go through all tiles, and set their background color according to the FOV
		for y in range(MAP_HEIGHT):
			for x in range(MAP_WIDTH):
				visible = libtcod.map_is_in_fov(fov_map, x, y)

				wall = map[x][y].block_sight
				sludge = map[x][y].sludge
				water = map[x][y].water

				if not visible:
					#if it's not visible right now, the player can only see it if it's explored
					if map[x][y].explored:
						if wall:
							libtcod.console_set_char_background(con, x, y, color_dark_wall, libtcod.BKGND_SET)
						elif sludge:
							libtcod.console_set_char_background(con, x, y, libtcod.darkest_lime, libtcod.BKGND_SET)
						elif water:
							libtcod.console_set_char_background(con, x, y, libtcod.darkest_blue, libtcod.BKGND_SET)
						else:
							libtcod.console_set_char_background(con, x, y, color_dark_ground, libtcod.BKGND_SET)

				else:
					#it's visible
					if wall:
						libtcod.console_set_char_background(con, x, y, color_light_wall, libtcod.BKGND_SET)
					elif sludge:
						libtcod.console_set_char_background(con, x, y, libtcod.darker_lime, libtcod.BKGND_SET)
					elif water:
						libtcod.console_set_char_background(con, x, y, libtcod.darkest_blue, libtcod.BKGND_SET)
					else:
						libtcod.console_set_char_background(con, x, y, color_light_ground, libtcod.BKGND_SET)
						#since it's visible, explore it
					map[x][y].explored = True



	#draw all objects in the list, except the player. we want it to
	#always appear over all other objects! so it's drawn later.
	for object in objects:
		if object != player:
			object.draw()
	player.draw()


	#blit the contents of "con" to the root console
	libtcod.console_blit(con, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0, 0, 1, 1)


	#prepare to render the GUI panel

	libtcod.console_set_default_background(panel, libtcod.black)
	libtcod.console_clear(panel)


	#print the game messages, one line at a time
	y = 1
	x = 1
	for (line, color) in game_msgs:
		libtcod.console_set_default_foreground(panel, color)
		libtcod.console_print_ex(panel, x, y, libtcod.BKGND_NONE, libtcod.LEFT, line)
		y += 1


	#show the player's stats

	libtcod.console_set_default_background(sidebar, libtcod.black)
	libtcod.console_clear(sidebar)

	libtcod.console_print_ex(sidebar, 1, 3, libtcod.BKGND_NONE, libtcod.LEFT, 'Sprawl Depth: ' + str(dungeon_level))

	libtcod.console_print_ex(sidebar, 1, 4, libtcod.BKGND_NONE, libtcod.LEFT, 'Hunger: ' + str(hunger_stat))
	libtcod.console_print_ex(sidebar, 9, 7, libtcod.BKGND_NONE, libtcod.LEFT, 'Cr:' + str(cred))
	libtcod.console_print_ex(sidebar, 1, 6, libtcod.BKGND_NONE, libtcod.LEFT, 'Time:' + str(hour))
	libtcod.console_print_ex(sidebar, 1, 7, libtcod.BKGND_NONE, libtcod.LEFT, 'Ammo:' + str(player.fighter.ammo))


	libtcod.console_print_ex(sidebar, 1, 15, libtcod.BKGND_NONE, libtcod.LEFT, 'Atk:' + str(player.fighter.power))
	libtcod.console_print_ex(sidebar, 9, 15, libtcod.BKGND_NONE, libtcod.LEFT, 'Dex:' + str(player.fighter.dex))
	libtcod.console_print_ex(sidebar, 1, 16, libtcod.BKGND_NONE, libtcod.LEFT, 'Def:' + str(player.fighter.defense))
	libtcod.console_print_ex(sidebar, 1, 17, libtcod.BKGND_NONE, libtcod.LEFT, 'Acc:' + str(player.fighter.accuracy))



	render_bar(0, 1, BAR_WIDTH, 'HP', player.fighter.hp, player.fighter.max_hp,
			   libtcod.light_red, libtcod.darker_red)

	render_bar(0, 2, BAR_WIDTH, 'Charge', player.fighter.charge, player.fighter.base_charge,
			   libtcod.light_blue, libtcod.darker_blue)

	#display names of objects under the mouse
	libtcod.console_set_default_foreground(panel, libtcod.light_gray)
	libtcod.console_print_ex(panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT, get_names_under_mouse())

	#blit the contents of "panel" to the root console
	libtcod.console_blit(panel, 0, 0, SCREEN_WIDTH, PANEL_HEIGHT, 0, 0, PANEL_Y, 0.94, 0.2)
	libtcod.console_blit(sidebar ,0, 0, SIDEBAR_WIDTH, SCREEN_HEIGHT, 0, 71, SIDEBAR_Y, 0.94, 0.2)


## Object placement!!!!!!

def from_dungeon_level(table):
	#returns a value that depends on level. the table specifies what value occurs after each level, default is 0.
	for (value, level) in reversed(table):
		if dungeon_level >= level:
			return value
	return 0


def place_monsters(room):
	max_monsters = from_dungeon_level([[2, 1], [3, 5], [4, 8]])
	#chance of each monster
	monster_chances ={}
	monster_chances['thug'] = from_dungeon_level([[80, 2], [40, 5], [10,9], [0, 12]])   #thug always shows up, even if all other monsters have 0 chance
	monster_chances['thugboss'] = from_dungeon_level([[10, 3], [15, 5], [10, 7], [0,12]])
	#monster_chances['hologram'] = from_dungeon_level([[0, 1], [10, 4]])
	monster_chances['mutant'] = from_dungeon_level([[15, 4], [30, 6], [40, 9]])
	monster_chances['fastmutant'] = from_dungeon_level([[5, 5], [10, 8], [20, 11]])
	monster_chances['dog'] = from_dungeon_level([[80, 2], [0, 3]])
	#robots:
	monster_chances['manhack'] = from_dungeon_level([[20, 4], [25, 6], [30, 8]])
	monster_chances['vturret'] = from_dungeon_level([[15, 5], [30, 7]])
	monster_chances['replicant'] = from_dungeon_level([[5, 5], [10, 7], [20, 9]])


	#choose random number of monsters
	num_monsters = libtcod.random_get_int(0, 0, max_monsters)

	for i in range(num_monsters):
		#choose random spot for this monster
		x = libtcod.random_get_int(0, room.x1 + 1, room.x2 - 1)
		y = libtcod.random_get_int(0, room.y1 + 1, room.y2 - 1)

		#only place it if the tile is not blocked
		if not is_blocked(x, y):
			choice = random_choice(monster_chances)
			if choice == 'thug':
				#create an orc
				fighter_component = Fighter(my_path=0, lastx=0, lasty=0, hp=20, defense=0, power=4, dex=2, hack=0, accuracy=4, firearmdmg=0, firearmacc=0,
											eloyalty=0, vloyalty=0, ammo=0, charge=0, xp=35, move_speed=2, flicker=0, robot=False, death_function=monster_death, creddrop=0)
				ai_component = BasicMonster()

				monster = Object(x, y, 't', 'Thug', libtcod.green, desc='a bloodthirsty thug',
								 blocks=True, fighter=fighter_component, ai=ai_component)

			if choice == 'thugboss':
				#create an orc
				fighter_component = Fighter(my_path=0, lastx=0, lasty=0, hp=40, defense=1, power=4, dex=2, hack=0, accuracy=6, firearmdmg=4, firearmacc=4,
											eloyalty=0, vloyalty=0, ammo=2, charge=0, xp=70, move_speed=2, flicker=0, robot=False, death_function=monster_death, creddrop=2)
				ai_component = CleverMonster()

				monster = Object(x, y, 'T', 'Thug Lieutenant', libtcod.green, desc='a thug which has risen to the rank of Lieutenant, armed and vaugely intelligent',
								 blocks=True, fighter=fighter_component, ai=ai_component)

			#if choice == 'hologram':
			#	#create an hologram
			#	fighter_component = Fighter(my_path=0, lastx=0, lasty=0, hp=10, defense=0, power=0, dex=6, accuracy=0, firearmdmg=0, firearmacc=0,
			#								eloyalty=0, vloyalty=0, ammo=0, charge=0, xp=70, move_speed=2, flicker=0, robot=False, death_function=monster_death, creddrop=0)
			#	ai_component = BasicHologram()
			#
			#	monster = Object(x, y, 'H', 'hologram', libtcod.green, desc='an annoying though harmless hologram that will stalk travellers through the dungeon',
			#					 blocks=True, fighter=fighter_component, ai=ai_component)

			elif choice == 'mutant':
				#create a troll
				fighter_component = Fighter(my_path=0, lastx=0, lasty=0, hp=60, defense=2, power=10, dex=1, hack=0, accuracy=4, firearmdmg=0, firearmacc=2,
											eloyalty=0, vloyalty=0, ammo=0, charge=0, xp=100, move_speed=3, flicker=0, robot=False, death_function=monster_death, creddrop=0)
				ai_component = BasicMonster()

				monster = Object(x, y, 'M', 'Slow Mutant', libtcod.dark_green, desc='a slow mutant, contaminated by radiation and failed biotech',
								 blocks=True, fighter=fighter_component, ai=ai_component)

			elif choice == 'fastmutant':
				#create a troll
				fighter_component = Fighter(my_path=0, lastx=0, lasty=0, hp=30, defense=2, power=9, dex=2, hack=0, accuracy=5, firearmdmg=0, firearmacc=2,
											eloyalty=0, vloyalty=0, ammo=0, charge=0, xp=100, move_speed=1, flicker=0, robot=False, death_function=monster_death, creddrop=0)
				ai_component = BasicMonster()

				monster = Object(x, y, 'm', 'Fast Mutant', libtcod.darker_green, desc='a fast mutant, contaminated by radiation and failed biotech',
								 blocks=True, fighter=fighter_component, ai=ai_component)

			elif choice == 'dog':
				#create a troll
				fighter_component = Fighter(my_path=0, lastx=0, lasty=0, hp=10, defense=2, power=2, dex=2, hack=0, accuracy=4, firearmdmg=0, firearmacc=0,
											eloyalty=0, vloyalty=0, ammo=0, charge=0, xp=20, move_speed=1, flicker=0, robot=False, death_function=monster_death, creddrop=0)
				ai_component = BasicDog()

				monster = Object(x, y, 'd', 'Dog', libtcod.dark_green, desc='a rabid hound capable of sniffing out its victims',
								 blocks=True, fighter=fighter_component, ai=ai_component)

			##robots:
			elif choice == 'manhack':
				#create a manhack
				fighter_component = Fighter(my_path=0, lastx=0, lasty=0, hp=15, defense=0, power=4, dex=3, hack=0, accuracy=5, firearmdmg=0, firearmacc=2,
											eloyalty=0, vloyalty=0, ammo=0, charge=0, xp=50, move_speed=1, flicker=0, robot=True, death_function=robot_death, creddrop=0)
				ai_component = BasicMonster()

				monster = Object(x, y, 'h', 'Manhack', libtcod.light_flame, desc='a mass produced law enforcement drone, reprogrammed for maximum waste disposal',
								 blocks=True, fighter=fighter_component, ai=ai_component)

			elif choice == 'vturret':
				#create a manhack
				fighter_component = Fighter(my_path=0, lastx=0, lasty=0, hp=25, defense=2, power=0, dex=3, hack=0, accuracy=5, firearmdmg=2, firearmacc=4,
											eloyalty=0, vloyalty=0, ammo=6, charge=0, xp=50, move_speed=2, flicker=0, robot=True, death_function=robot_death, creddrop=0)
				ai_component = BasicTurret()

				monster = Object(x, y, 'v', 'Viper Turret', libtcod.flame, desc='a mass produced turret for corporate and private use.',
								 blocks=True, fighter=fighter_component, ai=ai_component)

			elif choice == 'replicant':
				#create a replicant
				fighter_component = Fighter(my_path=0, lastx=0, lasty=0, hp=50, defense=4, power=10, dex=4, hack=0, accuracy=5, firearmdmg=6, firearmacc=5,
											eloyalty=0, vloyalty=0, ammo=4, charge=0, xp=200, move_speed=2, flicker=0, robot=True, death_function=robot_death, creddrop=5)
				ai_component = BasicShooter()

				monster = Object(x, y, 'R', 'Replicant', libtcod.dark_flame, desc='A skin-job on the run, tears in the rain',
								 blocks=True, fighter=fighter_component, ai=ai_component)

			objects.append(monster)


def place_furniture(room):
	max_furniture = from_dungeon_level([[1, 1]])
	furniture_chances = {}
	furniture_chances['box'] = 5
	furniture_chances['rubble'] = 15
	furniture_chances['fuse_box'] = from_dungeon_level([[10, 3], [15, 5]])

	#furniture placement
	num_furniture = libtcod.random_get_int(0, 0, max_furniture)

	for i in range(num_furniture):
		#choose random spot for this monster
		x = libtcod.random_get_int(0, room.x1 + 1, room.x2 - 1)
		y = libtcod.random_get_int(0, room.y1 + 1, room.y2 - 1)

		#only place it if the tile is not blocked
		if not is_blocked(x, y):
			choice = random_choice(furniture_chances)

			if choice == 'box':
				furniture_component = Furniture(use_function=open_box)
				furniture = Object(x, y, 146, 'box', libtcod.brass, desc='a storage container', blocks=True, furniture=furniture_component)

			if choice == 'rubble':
				furniture_component = Furniture(use_function=rubble)
				furniture = Object(x, y, 'x', 'rubble', libtcod.grey, desc='the cast offs of a broken city', blocks=True, furniture=furniture_component)

			elif choice == 'fuse_box':
				furniture_component = Furniture(use_function=recharge)
				furniture = Object(x, y, '&', 'fuse box', libtcod.blue, desc='a fuse box, with enough ports for you to plug into', blocks=True, furniture=furniture_component)

			objects.append(furniture)


def place_objects(room):

	#this is where we decide the chance of each monster or item appearing.

	#maximum number of items per room
	max_items = from_dungeon_level([[1, 3], [2, 8]])
	#chance of each item (by default they have a chance of 0 at level 1, which then goes up)
	item_chances = {}
	item_chances['None'] = 50
	item_chances['heal'] = 20  #healing potion always shows up, even if all other items have 0 chance
	item_chances['food'] = 10
	item_chances['bullets'] = from_dungeon_level([[15, 1], [25, 3]])
	item_chances['overload'] = from_dungeon_level([[15, 5]])

	##Weapons:
	item_chances['dagger'] = from_dungeon_level([[5, 4], [15, 6]])
	item_chances['nanosteelblade'] = from_dungeon_level([[5, 6], [15, 8]])
	item_chances['combatblade'] = from_dungeon_level([[5, 9], [8, 12]])
	item_chances['katana'] = from_dungeon_level([[5, 12], [10, 15]])
	item_chances['revolver'] = from_dungeon_level([[5, 4], [10, 6]])
	item_chances['vk19'] = from_dungeon_level([[5, 6], [8, 10]])
	item_chances['vkp5'] = from_dungeon_level([[5, 6], [8, 10]])
	item_chances['vk180'] = from_dungeon_level([[5, 12], [10, 15]])

	##Armour:
	item_chances['meshlegs'] = from_dungeon_level([[5, 3], [8, 5]])
	item_chances['platedlegs'] = from_dungeon_level([[5, 7], [10, 9]])
	item_chances['Type1'] = from_dungeon_level([[10, 2], [5, 4], [0, 6]])
	item_chances['Type2'] = from_dungeon_level([[5, 2], [10, 4], [15, 6], [0, 8]])
	item_chances['Type3'] = from_dungeon_level([[10, 5], [15, 7]])
	item_chances['goggles'] = from_dungeon_level([[10, 5], [15, 7]])
	item_chances['visor'] = from_dungeon_level([[5, 6], [10, 7], [15, 10]])



	#choose random number of items
	num_items = libtcod.random_get_int(0, 0, max_items)

	for i in range(num_items):
		#choose random spot for this item
		x = libtcod.random_get_int(0, room.x1 + 1, room.x2 - 1)
		y = libtcod.random_get_int(0, room.y1 + 1, room.y2 - 1)

		#only place it if the tile is not blocked
		if not is_blocked(x, y):
			choice = random_choice(item_chances)

			if choice == 'heal':
				#create a healing potion
				item_component = Item(use_function=cast_heal)
				item = Object(x, y, '!', 'a medikit', libtcod.magenta, desc='a basic Erma medikit', value=50, item=item_component)

			elif choice == 'food':
				item_component = Item(use_function=eat)
				item = Object(x, y, 'g', 'Food', libtcod.magenta, desc='a Food Package', value=0, item=item_component)

			elif choice == 'None':
				#create a healing potion
				item_component = Item(use_function=None)
				item = Object(x, y, ' ', ' ', libtcod.magenta, desc=' ', item=item_component)

			elif choice == 'overload':
				#create a lightning bolt scroll
				item_component = Item(use_function=cast_overload)
				item = Object(x, y, '#', 'an overload pack', libtcod.light_yellow, desc='a standard Erma overload pack, used for short circuiting faulty stock', value=80, item=item_component)

			#elif choice == 'fireball':
			#	#create a fireball scroll
			#	item_component = Item(use_function=cast_fireball)
			#	item = Object(x, y, '#', 'a scroll of fireball', libtcod.light_yellow, item=item_component)

			#elif choice == 'confuse':
			#	#create a confuse scroll
			#	item_component = Item(use_function=cast_confuse)
			#	item = Object(x, y, '#', 'a scroll of confusion', libtcod.light_yellow, item=item_component)

			elif choice == 'bullets':
				#inventory bullets
				item_component = Item(use_function=reload_ammo)
				item = Object(x, y, '=', 'bullets', libtcod.light_yellow, desc='a fistful of bullets', item=item_component)

			## weapons

			elif choice == 'dagger':
				#create a dagger
				equipment_component = Equipment(slot='Right hand', power_bonus=3)
				item = Object(x, y, '/', 'a dagger', libtcod.sky,
							  desc='a worn dagger, built for knife fights', equipment=equipment_component)

			elif choice == 'nanosteelblade':
				#create a dagger
				equipment_component = Equipment(slot='Right hand', power_bonus=4)
				item = Object(x, y, '/', 'a nano-steel blade', libtcod.dark_sky, make='Erma',
							  desc='an Erma Nano-Steel Blade', equipment=equipment_component)

			elif choice == 'combatblade':
				#create a dagger
				equipment_component = Equipment(slot='Right hand', power_bonus=6, dex_bonus=-1)
				item = Object(x, y, '/', 'a combat blade', libtcod.darker_sky, make='Vorikov',
							  desc='a Vorikov Combat Blade, Deadly but bulky', equipment=equipment_component)

			elif choice == 'Katana':
				#create a dagger
				equipment_component = Equipment(slot='Right hand', power_bonus=8, dex_bonus=1)
				item = Object(x, y, '/', 'a katana', libtcod.darkest_sky, make=' ',
							  desc='a Katana, Deadly and accurate', equipment=equipment_component)

			elif choice == 'revolver':
				#create a dagger
				equipment_component = Equipment(slot='Left hand', firearm_dmg_bonus=3)
				item = Object(x, y, 'f', 'a revolver', libtcod.sky, make='Vorikov',
							  desc='a Vorikov revolver', equipment=equipment_component)

			elif choice == 'vk19':
				#create a dagger
				equipment_component = Equipment(slot='Left hand', firearm_dmg_bonus=4, firearm_acc_bonus=1)
				item = Object(x, y, 'f', 'VK-19', libtcod.dark_sky, make='Vorikov',
							  desc='a Vorikov VK-19 rifle. Accurate and moderately powerful.',  value=150, equipment=equipment_component)

			elif choice == 'vkp5':
				#create a dagger
				equipment_component = Equipment(slot='Left hand', firearm_dmg_bonus=6, firearm_acc_bonus=-2)
				item = Object(x, y, 'f', 'VK-P5', libtcod.darker_sky, make='Vorikov',
							  desc='a Vorikov VK-P5. A powerful but innacurate peppergun.', value=150, equipment=equipment_component)

			elif choice == 'vk180':
				#create a dagger
				equipment_component = Equipment(slot='Left hand', firearm_dmg_bonus=9, dex_bonus=-3)
				item = Object(x, y, 'f', 'VK-180', libtcod.darkest_sky, make='Vorikov',
							  desc='a Vorikov VK-180, an immensely powerful heavy rifle which completely cripples your dexterity', value=300, equipment=equipment_component)

			## Armour:

			elif choice == 'Type1':
				#create a shield
				equipment_component = Equipment(slot='Torso', defense_bonus=1)
				item = Object(x, y, 'A', 'a Type 1 vest', libtcod.yellow, make='Erma', desc='an Erma Type 1 armoured vest', equipment=equipment_component)

			elif choice == 'Type2':
				#create a shield
				equipment_component = Equipment(slot='Torso', defense_bonus=2)
				item = Object(x, y, 'A', 'a Type 2 vest', libtcod.orange, make='Erma', desc='an Erma Type 2 armoured vest', equipment=equipment_component)

			elif choice == 'Type3':
				#create a shield
				equipment_component = Equipment(slot='Torso', defense_bonus=3, dex_bonus=-1, eloyalty_bonus=1)
				item = Object(x, y, 'A', 'a Type 3 vest', libtcod.red, make='Erma', desc='an Erma Type 3 armoured vest, quite bulky', equipment=equipment_component)

			elif choice == 'meshlegs':
				#create a shield
				equipment_component = Equipment(slot='Legs', defense_bonus=1)
				item = Object(x, y, '{', 'Mesh Leg Armour', libtcod.orange, make='Erma', desc='Erma mesh leg armour', equipment=equipment_component)

			elif choice == 'platedlegs':
				#create a shield
				equipment_component = Equipment(slot='Legs', defense_bonus=3, dex_bonus=-1)
				item = Object(x, y, '{', 'Plated Leg Armour', libtcod.red, make='Erma', desc='Erma plated leg armour, quite bulky', equipment=equipment_component)

			elif choice == 'goggles':
				#create a shield
				equipment_component = Equipment(slot='Head', accuracy_bonus=1)
				item = Object(x, y, 'e', 'a pair of targeting goggles', libtcod.lighter_blue, make='Erma', desc='a pair of Erma targetting goggles', equipment=equipment_component)

			elif choice == 'visor':
				#create a shield
				equipment_component = Equipment(slot='Head', accuracy_bonus=2, firearm_dmg_bonus=1, vloyalty_bonus=1)
				item = Object(x, y, 'e', 'a sharpshooter visor', libtcod.light_blue,  make='Vorikov',
							  desc='a Vorikov sharpshooter visor',  value=200, equipment=equipment_component)

			objects.append(item)
			item.send_to_back()  #items appear below other objects
			item.always_visible = True  #items are visible even out-of-FOV, if in an explored area


def hub():

	#Shops
	furniture_component = Furniture(use_function=Ermashopsell)
	furniture = Object(8, 2, '$', 'Erma Shopping Terminal', libtcod.red, desc='an Erma Shopping Terminal', blocks=True, furniture=furniture_component)
	objects.append(furniture)
	furniture.always_visible = True

	furniture_component = Furniture(use_function=Vorishopsell)
	furniture = Object(9, 12, '$', 'Vorikov Shopping Terminal', libtcod.dark_red, desc='a Vorikov Shopping Terminal', blocks=True, furniture=furniture_component)
	objects.append(furniture)
	furniture.always_visible = True

	furniture_component = Furniture(use_function=foodshop)
	furniture = Object(25, 7, '$', 'Noodle Bar Terminal', libtcod.dark_green, desc='The terminal for a Noodle Bar', blocks=True, furniture=furniture_component)
	objects.append(furniture)
	furniture.always_visible = True

	furniture_component = Furniture(use_function=fenceshop)
	furniture = Object(62, 2, '$', 'Manual Jack, the fence', libtcod.black, desc='Manual Jack, the fence.', blocks=True, furniture=furniture_component)
	objects.append(furniture)
	furniture.always_visible = True

	furniture_component = Furniture(use_function=potionshop)
	furniture = Object(27, 24, '$', 'Sandii, the pusher', libtcod.magenta, desc='Sandii, the pusher', blocks=True, furniture=furniture_component)
	objects.append(furniture)
	furniture.always_visible = True

	#NPCs
	#NPC direct placement:
	npcplace = [(4,24), (5,24), (7, 4), (9, 8), (15, 28), (30, 10)]
	for x,y in npcplace:
		libtcod.namegen_parse('names.txt')
		name = libtcod.namegen_generate('npcnames')
		nonplayerchar_component = NonplayerChar(my_path=0, lastx=0, lasty=0, hp=20, defense=10, power=4, hack=0, dex=10, accuracy=4,
											eloyalty=0, vloyalty=0, xp=0, move_speed=5, flicker=0, robot=False, death_function=monster_death, creddrop=0, use_function=convo)
		ai_component = BasicNpc()
		npc = Object(x, y, 'N', name, libtcod.fuchsia, desc=name,
								 blocks=True, nonplayerchar=nonplayerchar_component, ai=ai_component)
		objects.append(npc)

	for n in range(1,10):
		libtcod.namegen_parse('names.txt')
		name = libtcod.namegen_generate('npcnames')
		nonplayerchar_component = NonplayerChar(my_path=0, lastx=0, lasty=0, hp=20, defense=10, power=4, hack=0, dex=10, accuracy=4,
											eloyalty=0, vloyalty=0, xp=0, move_speed=5, flicker=0, robot=False, death_function=monster_death, creddrop=0, use_function=convo)
		ai_component = BasicNpc()
		npc = Object(x, y, 'N', name, libtcod.fuchsia, desc=name,
								 blocks=True, nonplayerchar=nonplayerchar_component, ai=ai_component)
		npc.x, npc.y = random_unblocked_tile_on_map()
		objects.append(npc)

	#n = range(1,15)
	for n in range(1,15):
		furniture_component = Furniture(use_function=rubble)
		furniture = Object(5, 5, 'x', 'rubble', libtcod.grey, desc='the cast offs of a broken city', blocks=True, furniture=furniture_component)
		furniture.x, furniture.y = random_unblocked_tile_on_map()
		objects.append(furniture)
		furniture.send_to_front()
		n+=1

	#misc
	furniture_component = Furniture(use_function=playerterminal)
	furniture = Object(60, 21, '&', 'Player Terminal', libtcod.white, desc='Your Terminal', blocks=True, furniture=furniture_component)
	objects.append(furniture)
	furniture.always_visible = True

	furniture_component = Furniture(use_function=bed)
	furniture = Object(56, 21, '#', 'Bed', libtcod.lightest_amber, desc='Your Bed', blocks=True, furniture=furniture_component)
	objects.append(furniture)
	furniture.always_visible = True

	#chairs, useless, useless chairs.
	chairplace = [(3,21),(4,21), (7,21), (8,21), (3,28),(4,28), (7,28), (8,28)]

	for x,y in chairplace:
			furniture_component = Furniture(nouse)
			furniture = Object(x, y, 'n', 'chair', libtcod.brass, desc='a chair', blocks=False, furniture=furniture_component)
			objects.append(furniture)

	#some signs

	furniture_component = Furniture(use_function=lookat)
	furniture = Object(11, 8, '?', 'ErmaCorp Defence', libtcod.red, desc='Erma Corporation defence superstore', blocks=True, furniture=furniture_component)
	objects.append(furniture)
	furniture.always_visible = True

	furniture_component = Furniture(use_function=lookat)
	furniture = Object(11, 16, '?', 'Vorikov Surplus', libtcod.dark_red, desc='Vorikov Corporation Surplus', blocks=True, furniture=furniture_component)
	objects.append(furniture)
	furniture.always_visible = True

	furniture_component = Furniture(use_function=lookat)
	furniture = Object(25, 19, '?', 'Bar Artiste', libtcod.sea, desc='Bar Artiste - open all hours.', blocks=True, furniture=furniture_component)
	objects.append(furniture)
	furniture.always_visible = True

	furniture_component = Furniture(use_function=lookat)
	furniture = Object(61, 19, '?', 'Appartment Block Y2', libtcod.sea, desc='Appartment Block Y2', blocks=True, furniture=furniture_component)
	objects.append(furniture)
	furniture.always_visible = True

	furniture_component = Furniture(use_function=lookat)
	furniture = Object(44, 3, '?', 'Rose Hotel', libtcod.sea, desc='The Rose Hotel', blocks=True, furniture=furniture_component)
	objects.append(furniture)
	furniture.always_visible = True

	#add the player
	player.x, player.y = 62, 22


def factory():
	cultistplace = [(20,5), (5,24), (7, 4), (9, 8), (30, 10)]
	for x,y in cultistplace:
		fighter_component = Fighter(my_path=0, lastx=0, lasty=0, hp=20, defense=5, power=8, dex=2, hack=0, accuracy=5, firearmdmg=0, firearmacc=0,
											eloyalty=0, vloyalty=0, ammo=0, charge=0, xp=100, move_speed=2, flicker=0, robot=False, death_function=monster_death, creddrop=0)
		ai_component = CleverMonster()
		monster = Object(x, y, 'c', 'Cultist', libtcod.light_red, desc='a Leucrocota Cultist',
								 blocks=True, fighter=fighter_component, ai=ai_component)
		objects.append(monster)

	deviationplace = [(10,5), (5,30), (7, 9), (9, 15), (32, 20)]
	for x,y in deviationplace:
		fighter_component = Fighter(my_path=0, lastx=0, lasty=0, hp=120, defense=5, power=10, dex=1, hack=0, accuracy=6, firearmdmg=0, firearmacc=0,
											eloyalty=0, vloyalty=0, ammo=0, charge=0, xp=120, move_speed=3, flicker=0, robot=False, death_function=monster_death, creddrop=0)
		ai_component = CleverMonster()
		monster = Object(x, y, 'D', 'Deviation', libtcod.red, desc='a Leucrocota Deviation, a towering amalgamation of decaying flesh and sharp bone',
								 blocks=True, fighter=fighter_component, ai=ai_component)
		objects.append(monster)



## Player stuff!

def player_move_or_attack(dx, dy):
	global fov_recompute
	global game_turn

	#if game_turn % player.fighter.move_speed == 0:
		#the coordinates the player is moving to/attacking
	x = player.x + dx
	y = player.y + dy

		#try to find an attackable object there
	target = None
	for object in objects:
		if object.fighter and object.x == x and object.y == y:
			target = object
			break

		#attack if target found, move otherwise
	if target is not None:
		player.fighter.attack(target)
		take_game_turn()
	else:
		player.move(dx, dy)
		fov_recompute = True
		take_game_turn()


def player_move_or_lightattack(dx, dy):
	global fov_recompute
	global game_turn

	#if game_turn % player.fighter.move_speed == 0:
		#the coordinates the player is moving to/attacking
	x = player.x + dx
	y = player.y + dy

		#try to find an attackable object there
	target = None
	for object in objects:
		if object.fighter and object.x == x and object.y == y:
			target = object
			break

		#attack if target found, move otherwise
	if target is not None:
		player.fighter.lightattack(target)
		take_game_turn()
	else:
		player.move(dx, dy)
		fov_recompute = True
		take_game_turn()


def hacking():
	message('Choose a hack to launch, your charge level is ' + str(player.fighter.charge) + '!', libtcod.yellow)
	choice = None
	if player.fighter.hack == 1:
		while choice == None:  #keep asking until a choice is made
				choice = menu('Choose a hack:\n',
							['Confusion (-5 charge)',
							'Cancel'], LEVEL_SCREEN_WIDTH)

		if choice == 0:
			if player.fighter.charge >= 5:
				cast_confuse()
				player.fighter.charge -= 5
			else:
				message('You do not have enough charge')
		elif choice == 1:
			message('You cancel the hack')

	elif player.fighter.hack == 2:

		while choice == None:  #keep asking until a choice is made
				choice = menu('Choose a hack:\n',
							['Confusion (-5 charge)',
							'Overload (-10 charge)',
							'Cancel'], LEVEL_SCREEN_WIDTH)

		if choice == 0:
			if player.fighter.charge >= 5:
				cast_confuse()
				player.fighter.charge -= 5
			else:
				message('You do not have enough charge')
		elif choice == 1:
			if player.fighter.charge >= 10:
					cast_overload()
					player.fighter.charge -= 10
			else:
				message('You do not have enough charge')

		elif choice == 2:
			message('You cancel the hack')

	elif player.fighter.hack >= 3:
		while choice == None:  #keep asking until a choice is made
				choice = menu('Choose a hack:\n',
							['Confusion (-5 charge)',
							'Overload (-10 charge)',
							'Repair (-10 charge)'
							'Cancel'], LEVEL_SCREEN_WIDTH)

		if choice == 0:
			if player.fighter.charge >= 5:
				cast_confuse()
				player.fighter.charge -= 5
			else:
				message('You do not have enough charge')
		elif choice == 1:
			if player.fighter.charge >= 10:
					cast_overload()
					player.fighter.charge -= 10
			else:
				message('You do not have enough charge')
		elif choice == 2:
			if player.fighter.charge >= 10:
				if player.fighter.hp != player.fighter.max_hp:
					cast_heal()
					player.fighter.charge -= 10
				else:
					message('You are already at full health!')
			else:
				message('You do not have enough charge')
		elif choice == 3:
			message('You cancel the hack')


def inventory_menu(header):
	#show a menu with each item of the inventory as an option
	if len(inventory) == 0:
		options = ['Inventory is empty.']
	else:
		options = []
		for item in inventory:
			text = item.name
			#show additional information, in case it's equipped
			if item.equipment and item.equipment.is_equipped:
				text = text + ' (' + item.equipment.slot + ')'
			options.append(text)

	index = menu(header, options, INVENTORY_WIDTH)

	#if an item was chosen, return it
	if index is None or len(inventory) == 0: return None
	return inventory[index].item


def get_equipped_in_slot(slot):  #returns the equipment in a slot, or None if it's empty
	for obj in inventory:
		if obj.equipment and obj.equipment.slot == slot and obj.equipment.is_equipped:
			return obj.equipment
	return None


def get_all_equipped(obj):  #returns a list of equipped items
	if obj == player:
		equipped_list = []
		for item in inventory:
			if item.equipment and item.equipment.is_equipped:
				equipped_list.append(item.equipment)
		return equipped_list
	else:
		return []  #other objects have no equipment


def handle_keys():
	global key, game_turn, upstairs, factoryexitstairs

	if key.vk == libtcod.KEY_ENTER and key.lalt:
		#Alt+Enter: toggle fullscreen
		libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

	elif key.vk == libtcod.KEY_ESCAPE:
		return 'exit'  #exit game

	if game_state == 'playing':
		#movement keys
		if key.vk == libtcod.KEY_UP or key.vk == libtcod.KEY_KP8:
			if player.fighter.paralysis:
				take_game_turn()
				message('You are paralysed', libtcod.red)
				player.fighter.become_paralysed()
			else:
				if key.lctrl:
					player_move_or_lightattack(0, -1)
					take_game_turn()
				else:
					player_move_or_attack(0, -1)
					take_game_turn()

		elif key.vk == libtcod.KEY_DOWN or key.vk == libtcod.KEY_KP2:
			if player.fighter.paralysis:
				random.randint(0,100) < 36
				message('You are paralysed', libtcod.red)
				player.fighter.become_paralysed()
			else:
				if key.lctrl:
					player_move_or_lightattack(0, 1)
					take_game_turn()
				else:
					player_move_or_attack(0, 1)
					take_game_turn()

		elif key.vk == libtcod.KEY_LEFT or key.vk == libtcod.KEY_KP4:
			if player.fighter.paralysis:
				take_game_turn()
				message('You are paralysed', libtcod.red)
				player.fighter.become_paralysed()
			else:
				if key.lctrl:
					player_move_or_lightattack(-1, 0)
					take_game_turn()
				else:
					player_move_or_attack(-1, 0)
					take_game_turn()

		elif key.vk == libtcod.KEY_RIGHT or key.vk == libtcod.KEY_KP6:
			if player.fighter.paralysis:
				take_game_turn()
				message('You are paralysed', libtcod.red)
				player.fighter.become_paralysed()
			else:
				if key.lctrl:
					player_move_or_lightattack(1, 0)
					take_game_turn()
				else:
					player_move_or_attack(1, 0)
					take_game_turn()

		elif key.vk == libtcod.KEY_HOME or key.vk == libtcod.KEY_KP7:
			if player.fighter.paralysis:
				take_game_turn()
				message('You are paralysed', libtcod.red)
				player.fighter.become_paralysed()
			else:
				if key.lctrl:
					player_move_or_lightattack(-1, -1)
					take_game_turn()
				else:
					player_move_or_attack(-1, -1)
					take_game_turn()

		elif key.vk == libtcod.KEY_PAGEUP or key.vk == libtcod.KEY_KP9:
			if player.fighter.paralysis:
				take_game_turn()
				message('You are paralysed', libtcod.red)
				player.fighter.become_paralysed()
			else:
				if key.lctrl:
					player_move_or_lightattack(1, -1)
					take_game_turn()
				else:
					player_move_or_attack(1, -1)
					take_game_turn()

		elif key.vk == libtcod.KEY_END or key.vk == libtcod.KEY_KP1:
			if player.fighter.paralysis:
				take_game_turn()
				message('You are paralysed', libtcod.red)
				player.fighter.become_paralysed()
			else:
				if key.lctrl:
					player_move_or_lightattack(-1, 1)
					take_game_turn()
				else:
					player_move_or_attack(-1, 1)
					take_game_turn()

		elif key.vk == libtcod.KEY_PAGEDOWN or key.vk == libtcod.KEY_KP3:
			if player.fighter.paralysis:
				take_game_turn()
				message('You are paralysed', libtcod.red)
				player.fighter.become_paralysed()
			else:
				if key.lctrl:
					player_move_or_lightattack(1, 1)
					take_game_turn()
				else:
					player_move_or_attack(1, 1)
					take_game_turn()

		elif key.vk == libtcod.KEY_KP5:
			if player.fighter.paralysis:
				take_game_turn()
				message('You are paralysed', libtcod.red)
				player.figher.become_paralysed()
			else:
				#pass  #do nothing ie wait for the monster to come to you
				take_game_turn()
				take_game_turn()

		else:
			#test for other keys
			key_char = chr(key.c)

			if key_char == 'g':
				#pick up an item
				for object in objects:  #look for an item in the player's tile
					if object.x == player.x and object.y == player.y and object.item:
						object.item.pick_up()
						break

			#if key_char == 'r':
			#    #reload an item
			#        for item in inventory:
			#            if item.name = bullets
			#                player.bullets += 5
			#            else:
			#                message('you have no bullets to reload')

			if key_char == 'i':
				#show the inventory; if an item is selected, use it
				chosen_item = inventory_menu('Press the key next to an item to use it, or any other to cancel.\n')
				if chosen_item is not None:
					chosen_item.use()

			if key_char == 'j':
				#show the inventory; if an item is selected, use it
				next_level()

			if key_char == 'e':
				message('Left-click an object to use, or right-click to cancel.', libtcod.light_cyan)
				max_range = 3
				(x, y) = target_tile(max_range)
				for obj in objects:
					if obj.x == x and obj.y == y and obj.furniture:
						obj.furniture.use_function(obj)

					elif obj.x == x and obj.y == y and obj.nonplayerchar:
						obj.nonplayerchar.use_function(obj)

			#! make this message only show if not able to use, or if no object is in range!

			if key_char == 'x':
				message('Left-click an object to examine it, or right-click to cancel.', libtcod.light_cyan)
				(x, y) = target_tile()
				for obj in objects:
					if obj.x == x and obj.y == y and obj:
						message('You see ' + str(obj.desc))


			if key_char == 'd':
				#show the inventory; if an item is selected, drop it
				chosen_item = inventory_menu('Press the key next to an item to drop it, or any other to cancel.\n')
				if chosen_item is not None:
					chosen_item.drop()

			if key_char == 'c':
				#show character information
				level_up_xp = LEVEL_UP_BASE + player.level * LEVEL_UP_FACTOR
				msgbox(
					'Character Information\n\nLevel: ' + str(player.level) + '\nExperience: ' + str(player.fighter.xp) +
					'\nExperience to level up: ' + str(level_up_xp) + '\n\nMaximum HP: ' + str(player.fighter.max_hp) +
					'\nAttack: ' + str(player.fighter.power) + '\nDefense: ' + str(player.fighter.defense) +
					'\nDexterity: ' + str(player.fighter.dex) + '\nAccuracy: ' + str(player.fighter.accuracy) +
					'\nErma Loyalty: ' + str(player.fighter.eloyalty) + '   Vorikov Loyalty: ' + str(player.fighter.vloyalty),
					CHARACTER_SCREEN_WIDTH)

			if key_char == '<':
				#go down stairs, if the player is on them
				if stairs.x == player.x and stairs.y == player.y:
					next_level()
				elif factorystairs.x == player.x and factorystairs.y == player.y:
					enterfactory()

			if key_char == '>':
				#go down stairs, if the player is on them
				try:
					if factoryexitstairs.x == player.x and factoryexitstairs.y == player.y:
						exitfactory()
				except NameError:
					if upstairs.x == player.x and upstairs.y == player.y:
						past_level()
				else:
					exitfactory()


			if key_char == 'f':
					#ask the player for a target tile to shoot at
				if player.fighter.ammo >= 1:
					message('Left-click an enemy to shoot it, or right-click to cancel.', libtcod.light_cyan)
					monster = target_monster()
					if monster is None:
						return 'cancelled'
					else:
						player.fighter.shoot(monster)
						player.fighter.ammo -= 1

				else:
					message('you have run out of bullets')


			if key_char == 'h':
				#ask the player for a target tile to hack it
				if player.fighter.charge >= 0:
					hacking()
				else:
					message('you have run out of charge! ')

			return 'didnt-take-turn'


def check_hunger():
	global hunger, hunger_stat
	if hunger > 100:
		hunger == 100
	if hunger > 61:
		hunger_stat = 'Full'
	if hunger == 60:
		message ('You are hungry', libtcod.dark_red)
		hunger_stat = 'Hungry'
	if hunger == 30:
		message (' You are very hungry', libtcod.dark_red)
		hunger_stat = 'Very Hungry'
	elif hunger == 15:
		message (' You are starving!', libtcod.dark_red)
		hunger_stat = 'Starving'
	elif hunger < 0:
		message('You died of starvation', libtcod.dark_red)
		game_state = 'dead'


def check_level_up():
	#see if the player's experience is enough to level-up
	level_up_xp = LEVEL_UP_BASE + player.level * LEVEL_UP_FACTOR
	if player.fighter.xp >= level_up_xp:
		#it is! level up and ask to raise some stats
		player.level += 1
		player.fighter.xp -= level_up_xp
		level_up()


def level_up():
		message('Your have grown more experienced! You reached level ' + str(player.level) + '!', libtcod.yellow)

		choice = None
		while choice == None:  #keep asking until a choice is made
			choice = menu('Level up! Choose a stat to raise:\n',
						  ['Constitution (+20 HP, from ' + str(player.fighter.max_hp) + ')',
						   'Strength (+1 attack, from ' + str(player.fighter.power) + ')',
						   'Dexterity (+1 dexterity, from ' + str(player.fighter.base_dex) + ')',
						   'Hacking (+1 hacking, +2 charge, from ' + str(player.fighter.charge) + ')'], LEVEL_SCREEN_WIDTH)

		if choice == 0:
			player.fighter.base_max_hp += 20
			player.fighter.hp += 20
		elif choice == 1:
			player.fighter.base_power += 1
		elif choice == 2:
			player.fighter.base_dex += 1
		elif choice == 3:
			player.fighter.hack += 1
			player.fighter.base_charge += 2
			player.fighter.charge += 2


#Death!

def player_death(player):
	#the game ended!
	global game_state
	message('You died!', libtcod.red)
	game_state = 'dead'

	#for added effect, transform the player into a corpse!
	player.char = '%'
	player.color = libtcod.dark_red


def monster_death(monster):
	global cred
	#transform it into a nasty corpse! it doesn't block, can't be
	#attacked and doesn't move
	addcred = 0
	addcred += monster.fighter.creddrop + libtcod.random_get_int(0, 0, 5)
	cred += addcred
	message('The ' + monster.name + ' is dead! You gain ' + str(monster.fighter.xp) + ' XP and ' + str(addcred) + 'Cr',
			libtcod.orange)
	monster.char = '%'
	monster.color = libtcod.dark_red
	monster.blocks = False
	monster.fighter = None
	monster.ai = None
	monster.name = 'remains of ' + monster.name
	monster.send_to_back()
	libtcod.map_set_properties(fov_map, monster.x, monster.y, True, True)

	for y in range(1,4):
		n=random.randint(-1, 2)
		if n == 1:
			bloodcolour= libtcod.dark_red
		elif n == 2:
			bloodcolour= libtcod.darker_red
		else:
			bloodcolour= libtcod.darkest_red
		libtcod.console_set_char_background(con, monster.x+n, monster.y, bloodcolour)
		libtcod.console_set_char_background(con, monster.x, monster.y-n, bloodcolour)
		y += 1


def robot_death(monster):
	#transform it into a nasty corpse! it doesn't block, can't be
	#attacked and doesn't move
	message('The ' + monster.name + ' is destroyed! You gain ' + str(monster.fighter.xp) + ' XP.',
			libtcod.orange)
	monster.char = '%'
	monster.color = libtcod.light_grey
	monster.blocks = False
	monster.fighter = None
	monster.ai = None
	monster.name = 'remains of ' + monster.name
	monster.send_to_back()
	libtcod.map_set_properties(fov_map, monster.x, monster.y, True, True)



## Furniture stuff

def target_furniture(max_range=4):
	#returns a clicked monster inside FOV up to a range, or None if right-clicked
	while True:
		(x, y) = target_tile(max_range)
		if x is None:  #player cancelled
			return None

		#return the first clicked furniture, otherwise continue looping
		for obj in objects:
			if obj.x == x and obj.y == y and obj.furniture:
				obj.furniture.use_function()


def object_destroy(obj):
	#transform it into a nasty corpse! it doesn't block, can't be
	#attacked and doesn't move
	message('It has broken! ',
			libtcod.orange)
	obj.char = '%'
	obj.color = libtcod.light_grey
	obj.blocks = False
	obj.furniture = None
	obj.name = 'remains of ' + obj.name
	obj.send_to_back()
	libtcod.map_set_properties(fov_map, obj.x, obj.y, True, True)


def open_box(obj):
	global game_turn, cred
	message('you have opened the box!')
	x = 0
	y = 0

	box_chances = {}
	box_chances['heal'] = 35  #healing potion always shows up, even if all other items have 0 chance
	box_chances['bullets'] = 45
	box_chances['cred'] = 40

	choice = random_choice(box_chances)
	for item in objects:
			if choice == 'heal':
					#create a healing potion
				item_component = Item(use_function=cast_heal)
				item = Object(x, y, '!', 'a medikit', libtcod.magenta, item=item_component)

			elif choice == 'bullets':
					#inventory bullets
				item_component = Item(use_function=reload_ammo)
				item = Object(x, y, '=', 'bullets', libtcod.light_yellow, item=item_component)

			elif choice == 'cred':
					#inventory bullets
				cred += 5

	inventory.append(item)
	message('You picked up ' + item.name + '!', libtcod.green)
	object_destroy(obj)


def convo(obj):
	talk = ['Go away', 'Why are you talking to me?', 'Who are you?', 'Get lost.']
	from random import choice
	message(choice(talk))


def rubble(obj):
	global game_turn
	message('you break up the rubble!')
	object_destroy(obj)


def bed(obj):
	global hour
	hour += 8
	player.fighter.hp = player.fighter.max_hp
	player.fighter.charge = player.fighter.base_charge
	message('you feel rested')


def recharge(obj):
	global game_turn
	if player.fighter.charge == player.fighter.base_charge:
		message('You are already fully charged.', libtcod.red)
		return 'cancelled'

	message('You recharge yourself off the fuse box.')
	player.fighter.charge += 5
	object_destroy(obj)
	return True


def Ermashopsell(obj):
	global cred
	x=0
	y=0

	if player.fighter.eloyalty >= 1:
		message('This has been an Erma Corporation shopping terminal experience', libtcod.yellow)
		choice = None
		while choice == None:  #keep asking until a choice is made
			choice = menu('Welcome to the Erma self-protection shopping terminal. You have ' + str(cred) + ' Credits',
						['Type 1 body armour [Torso] (50 Cr)',
						'Mesh Leg Armour [Legs] (50 Cr)',
						'Type 2 body armour [Torso] (200 Cr)',
						'Cancel'], LEVEL_SCREEN_WIDTH)

			if choice == 0 and cred >= 50:
				#create a shield
				equipment_component = Equipment(slot='Torso', defense_bonus=1)
				item = Object(x, y, 'A', 'a Type 1 vest', libtcod.yellow, make='Erma', desc='an Erma Type 1 armoured vest', equipment=equipment_component)
				inventory.append(item)
				cred -= 50
				message('thank you for your purchase', libtcod.yellow)


			elif choice == 1 and cred >= 50:
				#create a shield
				equipment_component = Equipment(slot='Legs', defense_bonus=1)
				item = Object(x, y, '{', 'Mesh Leg Armour', libtcod.orange, make='Erma', desc='Erma mesh leg armour', equipment=equipment_component)
				if cred >= 50:
					inventory.append(item)
					cred -= 50
					message('thank you for your purchase', libtcod.yellow)
				else:
					return

			elif choice == 2 and cred >= 200:
				equipment_component = Equipment(slot='Torso', defense_bonus=2)
				item = Object(x, y, 'A', 'a Type 2 vest', libtcod.yellow, make='Erma', desc='an Erma Type 2 armoured vest', equipment=equipment_component)
				inventory.append(item)
				if cred >= 50:
					inventory.append(item)
					cred -= 50
					message('thank you for your purchase', libtcod.yellow)
				else:
					return

			elif choice == 3:
				return

			else:
				message('You do not have enough credits', libtcod.yellow)
	else:
		message('The Erma Corporation only recognises loyal customers', libtcod.yellow)


def Vorishopsell(obj):

	global cred
	x=0
	y=0

	if player.fighter.vloyalty >= 1:
		message('This has been an Vorikov Corporation shopping terminal experience', libtcod.yellow)
		choice = None
		while choice == None:  #keep asking until a choice is made
			choice = menu('Welcome to the Vorikov self-protection shopping terminal. You have ' + str(cred) + ' Credits',
						['Type 1 body armour [Torso] (50 Cr)',
						'Mesh Leg Armour [Legs] (50 Cr)',
						'Type 2 body armour [Torso] (200 Cr)',
						'Cancel'], LEVEL_SCREEN_WIDTH)

			if choice == 0 and cred >= 50:
				#create a shield
				equipment_component = Equipment(slot='Torso', defense_bonus=1)
				item = Object(x, y, 'A', 'a Type 1 vest', libtcod.yellow, make='Erma', desc='an Erma Type 1 armoured vest', equipment=equipment_component)
				inventory.append(item)
				cred -= 50
				message('thank you for your purchase', libtcod.yellow)


			elif choice == 1 and cred >= 50:
				#create a shield
				equipment_component = Equipment(slot='Legs', defense_bonus=1)
				item = Object(x, y, '{', 'Mesh Leg Armour', libtcod.orange, make='Erma', desc='Erma mesh leg armour', equipment=equipment_component)
				if cred >= 50:
					inventory.append(item)
					cred -= 50
					message('thank you for your purchase', libtcod.yellow)
				else:
					return

			elif choice == 2 and cred >= 200:
				equipment_component = Equipment(slot='Torso', defense_bonus=2)
				item = Object(x, y, 'A', 'a Type 2 vest', libtcod.yellow, make='Erma', desc='an Erma Type 2 armoured vest', equipment=equipment_component)
				inventory.append(item)
				if cred >= 50:
					inventory.append(item)
					cred -= 50
					message('thank you for your purchase', libtcod.yellow)
				else:
					return

			elif choice == 3:
				return

			else:
				message('You do not have enough credits', libtcod.yellow)
	else:
		message('The Vorikov Corporation only recognises loyal customers', libtcod.yellow)


def fenceshop(obj):
	chosen_item = inventory_menu('Press the key next to an item to sell it, or any other to cancel.\n')
	if chosen_item is not None:
		chosen_item.sell(obj)
	else:
		return


def foodshop(obj):

	global cred
	x=0
	y=0


	message('Enjoy your meal!', libtcod.yellow)
	choice = None
	while choice == None:  #keep asking until a choice is made
		choice = menu('Welcome to the Vorikov self-protection shopping terminal. You have ' + str(cred) + ' Credits',
						['Food package (20 Cr)',
						'Big Food package (50 Cr)',
						'Cancel'], LEVEL_SCREEN_WIDTH)

		if choice == 0 and cred >= 20:
			item_component = Item(use_function=eat)
			item = Object(x, y, 'g', 'Food package', libtcod.magenta, desc='a food Package', value=0, item=item_component)
			inventory.append(item)
			cred -= 20
			message('thank you for your purchase', libtcod.yellow)


		elif choice == 1 and cred >= 50:
				#create a shield
			item_component = Item(use_function=big_eat)
			item = Object(x, y, 'G', 'Big food package', libtcod.magenta, desc='a big food Package', value=0, item=item_component)
			if cred >= 50:
				inventory.append(item)
				cred -= 50
				message('thank you for your purchase', libtcod.yellow)
			else:
				return


def potionshop(obj):

	global cred
	x=0
	y=0


	message('Thanks.', libtcod.yellow)
	choice = None
	while choice == None:  #keep asking until a choice is made
		choice = menu('Whatcha need?. You have ' + str(cred) + ' Credits',
						['Medikit (50 Cr)',
						'Cancel'], LEVEL_SCREEN_WIDTH)

		if choice == 0 and cred >= 50:
			item_component = Item(use_function=cast_heal)
			item = Object(x, y, '!', 'a medikit', libtcod.magenta, desc='a basic Erma medikit', value=50, item=item_component)
			cred -= 50

		else:
			return


def playerterminal(obj):

	global cred
	x=0
	y=0

	choice = None
	while choice == None:  #keep asking until a choice is made
		choice = menu('Welcome to your Personal Terminal. You have ' + str(cred) + ' Credits',
						['Messages',
						'Software',
						'DarkServer',
						'Cancel'], LEVEL_SCREEN_WIDTH)

		if choice == 0:
			message('You have no messages')

		elif choice == 1:
			message('You have no installed Software')

		elif choice == 2:
			message('DarkServer is not accessible at this time')

		elif choice == 3:
			return
		else:
			message('have a pleasant day')


def lookat(obj):
	message(str(obj.desc))


def door(obj):
	message('you open the door')
	obj.char = '_'
	obj.color = libtcod.light_grey
	obj.blocks = False
	obj.furniture = None
	map[obj.x][obj.y].block_sight = False
	obj.name = 'open door'
	obj.send_to_back()
	#door.opened = 1
	libtcod.map_set_properties(fov_map, obj.x, obj.y, True, True)
	initialize_fov()


def nouse(obj):
	message('Nothing useful can be done with this')



## spells and abilities:

def cast_heal():
	#heal the player
	if player.fighter.hp == player.fighter.max_hp:
		message('You are already at full health.', libtcod.red)
		return 'cancelled'

	message('Your wounds start to feel better!', libtcod.light_violet)
	player.fighter.heal(HEAL_AMOUNT)


def eat():
	global hunger
	hunger += 25


def big_eat():
	global hunger
	hunger += 50


def cast_overload():
	#find closest enemy (inside a maximum range) and damage it
	message('Left-click an enemy to overload it, or right-click to cancel.', libtcod.light_cyan)
	monster = target_monster(LIGHTNING_RANGE)
	if monster is None: return 'cancelled'

	if monster.fighter.robot:
		message('You overload the ' + monster.name + '! The damage is '
				+ str(LIGHTNING_DAMAGE) + ' hit points.', libtcod.light_blue)
		monster.fighter.take_damage(LIGHTNING_DAMAGE)
	else:
		message('It has no effect!')


def cast_fireball():
	#ask the player for a target tile to throw a fireball at
	message('Left-click a target tile for the fireball, or right-click to cancel.', libtcod.light_cyan)
	(x, y) = target_tile()
	if x is None: return 'cancelled'
	message('The fireball explodes, burning everything within ' + str(FIREBALL_RADIUS) + ' tiles!', libtcod.orange)

	for obj in objects:  #damage every fighter in range, including the player
		if obj.distance(x, y) <= FIREBALL_RADIUS and obj.fighter:
			message('The ' + obj.name + ' gets burned for ' + str(FIREBALL_DAMAGE) + ' hit points.', libtcod.orange)
			obj.fighter.take_damage(FIREBALL_DAMAGE)


def cast_confuse():
	#ask the player for a target to confuse
	message('Left-click an enemy to confuse it, or right-click to cancel.', libtcod.light_cyan)
	monster = target_monster(CONFUSE_RANGE)
	if monster is None: return 'cancelled'

	if monster.fighter.robot:
		#replace the monster's AI with a "confused" one; after some turns it will restore the old AI
		old_ai = monster.ai
		monster.ai = ConfusedMonster(old_ai)
		monster.ai.owner = monster  #tell the new component who owns it
		message('The eyes of the ' + monster.name + ' look vacant, as he starts to stumble around!', libtcod.light_green)
	else:
		message('It has no effect!')


def reload_ammo():
	global game_turn
	player.fighter.ammo += 5
	take_game_turn()
	message('you reload your ammo')



## Overarching stuff

def main_menu():
	global pwr, sht, hck
	img = libtcod.image_load('menubackground.png')

	while not libtcod.console_is_window_closed():
		#show the background image, at twice the regular console resolution
		libtcod.image_blit_2x(img, 0, 0, 0,)

		#show the game's title, and some credits!
		libtcod.console_set_default_foreground(0, libtcod.light_yellow)
		libtcod.console_print_ex(0, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 4, libtcod.BKGND_NONE, libtcod.CENTER,
								 'CyberRogue')
		libtcod.console_print_ex(0, SCREEN_WIDTH / 2, SCREEN_HEIGHT - 2, libtcod.BKGND_NONE, libtcod.CENTER, ' ')

		#show options and wait for the player's choice
		choice = menu('', ['Play a new game', 'Continue last game', 'Help', 'Quit'], 24)

		if choice == 0:  #new game
			#while not libtcod.console_is_window_closed():
			choice = menu('Choose a class:', ['Brawler', 'Marksman', 'Hacker', 'Quit'],34)
			if choice == 0:  #new game
					pwr = 5
					sht = 1
					hck = 1
					new_game()
					play_game()
			if choice == 1:  #new game
					pwr = 3
					sht = 5
					hck = 1
					new_game()
					play_game()
			if choice == 2:
					pwr = 2
					sht = 3
					hck = 2
					new_game()
					play_game()
			elif choice == 3:  #quit
				break
		if choice == 1:  #load last game
			try:
				load_game()
			except:
				msgbox('\n No saved game to load.\n', 24)
				continue
			play_game()
		if choice ==2:
			msgbox(
				'This is a Cyberpunk Roguelike game currently in development' +
				   '\nkeys are as follows:'
				   '\ne = use'
				   '\nx = examine'
				   '\nf = fire'
				   '\nh = hack')

		elif choice == 3:  #quit
			exit()


def save_game():
	#open a new empty shelve (possibly overwriting an old one) to write the game data
	file = shelve.open('savegame', 'n')
	file['map'] = map
	file['objects'] = objects
	file['player_index'] = objects.index(player)  #index of player in objects list
	file['stairs_index'] = objects.index(stairs)  #same for the stairs
	#file['upstairs_index'] = objects.index(upstairs)  #same for the stairs
	file['inventory'] = inventory
	file['game_msgs'] = game_msgs
	file['game_state'] = game_state
	file['dungeon_level'] = dungeon_level
	file.close()


def load_game():
	#open the previously saved shelve and load the game data
	global map, objects, player, stairs, upstairs, inventory, game_msgs, game_state, dungeon_level

	file = shelve.open('savegame', 'r')
	map = file['map']
	objects = file['objects']
	player = objects[file['player_index']]  #get index of player in objects list and access it
	stairs = objects[file['stairs_index']]  #same for the stairs
	upstairs = objects[file['upstairs_index']]
	inventory = file['inventory']
	game_msgs = file['game_msgs']
	game_state = file['game_state']
	dungeon_level = file['dungeon_level']
	file.close()

	initialize_fov()


def take_game_turn():
	global game_turn, hunger, time
	game_turn += 1
	time += 1
	if random.randint(0,100) < HUNGER_BASE:
		hunger -= 1


def check_time():
	global time, hour
	if time == 240:
		hour += 1
		time = 0
	if hour == 6 and time == 0:
		message('it is morning')
	if hour == 12 and time == 0:
		message('It is mid-day')
	if hour == 18 and time == 0:
		message ('It is evening')
	if hour == 21 and time == 0:
		message ('It is night time')
	if hour >= 24 and time >= 0:
		hour = 0



def new_game():
	global player, inventory, game_msgs, game_state, dungeon_level, game_turn, cred, pwr, sht, hck, hunger, hunger_stat, time, hour


	#create object representing the player
	fighter_component = Fighter(hp=900, lastx=0, lasty=0, my_path=0, defense=1, dex=4, accuracy=2, firearmdmg=2, vloyalty=0, eloyalty=0,
								firearmacc=sht, ammo=10, power=pwr, hack=hck, charge=10+(hck * 2), xp=0, move_speed=2, flicker=0, robot=False, paralysis=False, death_function=player_death)
	player = Object(0, 0, '@', 'Player', libtcod.white, blocks=True, desc='you!', fighter=fighter_component)

	#add player start variables - pretty much whatever we want really.
	player.level = 1
	cred = 50
	player.reloadable = 0
	inventory = []

	#create the list of game messages and their colors, starts empty
	game_msgs = []
	#libtcod.namegen_parse('names.txt')
	#generate map (at this point it's not drawn to the screen)
	dungeon_level = 1
	make_map()
	initialize_fov()

	game_state = 'playing'
	game_turn = 0
	hunger = 100
	time = 0
	hour = 5
	hunger_stat = 'Full'

	#a warm welcoming message!
	message('Welcome to CyberRogue!', libtcod.red)


	#initial equipment: a knife, pistol
	equipment_component = Equipment(slot='Right hand', power_bonus=2)
	obj = Object(0, 0, '-', 'Knife', libtcod.sky, equipment=equipment_component)

	inventory.append(obj)
	equipment_component.equip()

	equipment_component = Equipment(slot='Left hand', firearm_dmg_bonus=1)
	obj2 = Object(0, 0, 'f', 'Pistol', libtcod.sky, equipment=equipment_component, value=50)

	inventory.append(obj2)
	equipment_component.equip()

	equipment_component = Equipment(slot='Insert 1', eloyalty_bonus=1)
	obj3 = Object(0, 0, '*', 'Erma Loyalty Chip', libtcod.black, equipment=equipment_component)

	inventory.append(obj3)
	equipment_component.equip()


	obj.always_visible = True


def enterfactory():
	global dungeon_level, player
	global color_dark_wall, color_light_wall, color_dark_ground, color_light_ground

	color_dark_wall = libtcod.Color(10, 10, 10)
	color_light_wall = libtcod.Color(30, 20, 15)
	color_dark_ground = libtcod.Color(15, 15, 15)
	color_light_ground = libtcod.Color(15, 20, 20)

	file = shelve.open('hub', 'n')
	file['map'] = map
	file['objects'] = objects
	file['player_index'] = objects.index(player)
	file['stairs_index'] = objects.index(stairs)  #same for the stairs
	#file['upstairs_index'] = objects.index(upstairs)
	file.close()

	dungeon_level = 'factory'
	message('You delve deeper...', libtcod.red)
	make_map()  #create a fresh new level!
	factory()
	initialize_fov()


def exitfactory():
	global dungeon_level, map, objects, player, stairs, upstairs, inventory, game_msgs, game_state, dungeon_level
	global color_dark_wall, color_light_wall, color_dark_ground, color_light_ground
	dungeon_level = 1
	file = shelve.open('hub', 'r')
	map = file['map']
	objects = file['objects']
	player = objects[file['player_index']]
	stairs = objects[file['stairs_index']]  #same for the stairs
	#upstairs = objects[file['upstairs_index']]
	file.close()

	color_dark_wall = libtcod.Color(22, 22, 22)
	color_light_wall = libtcod.Color(54, 54, 54)
	color_dark_ground = libtcod.Color(48, 38, 38)
	color_light_ground = libtcod.Color(86, 76, 76)

	message('You arrive back at the hub')
	initialize_fov()


def next_level():
	#advance to the next level
	global dungeon_level, player
	global color_dark_wall, color_light_wall, color_dark_ground, color_light_ground
	if dungeon_level == 1:
		file = shelve.open('hub', 'n')
		file['map'] = map
		file['objects'] = objects
		file['player_index'] = objects.index(player)
		file['stairs_index'] = objects.index(stairs)  #same for the stairs
		#file['upstairs_index'] = objects.index(upstairs)
		file.close()

		color_dark_wall = libtcod.Color(22, 22, 22)
		color_light_wall = libtcod.Color(54, 54, 54)
		color_dark_ground = libtcod.Color(48, 38, 38)
		color_light_ground = libtcod.Color(86, 76, 76)

		dungeon_level += 1
		make_map()  #create a fresh new level!
		initialize_fov()
	else:
		dungeon_level += 1
		message('You delve deeper...', libtcod.red)
		make_map()  #create a fresh new level!
		initialize_fov()


def past_level():
	#advance to the next level
	global dungeon_level, map, objects, player, stairs, upstairs, inventory, game_msgs, game_state, dungeon_level
	global color_dark_wall, color_light_wall, color_dark_ground, color_light_ground

	dungeon_level -= 1
	if dungeon_level == 1:
		file = shelve.open('hub', 'r')
		map = file['map']
		objects = file['objects']
		player = objects[file['player_index']]
		stairs = objects[file['stairs_index']]  #same for the stairs
		#upstairs = objects[file['upstairs_index']]
		file.close()

		color_dark_wall = libtcod.Color(22, 22, 22)
		color_light_wall = libtcod.Color(54, 54, 54)
		color_dark_ground = libtcod.Color(48, 38, 38)
		color_light_ground = libtcod.Color(86, 76, 76)

		message('You arrive back at the hub')
		initialize_fov()


	else:
		message('You climb back towards the surface...', libtcod.red)
		make_map()  #create a fresh new level!
		initialize_fov()


def initialize_fov():
	global fov_recompute, fov_map
	fov_recompute = True

	#create the FOV map, according to the generated map
	fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
	for y in range(MAP_HEIGHT):
		for x in range(MAP_WIDTH):
			libtcod.map_set_properties(fov_map, x, y, not map[x][y].block_sight, not map[x][y].blocked)

	libtcod.console_clear(con)  #unexplored areas start black (which is the default background color)

## Main loop below:
def play_game():
	global key, mouse, game_turn

	player_action = None

	mouse = libtcod.Mouse()
	key = libtcod.Key()
	#main loop
	while not libtcod.console_is_window_closed():
		libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)
		#render the screen
		render_all()

		libtcod.console_flush()

		#main loop checks
		check_level_up()
		check_hunger()
		check_time()

		#erase all objects at their old locations, before they move
		for object in objects:
			if object.fighter:
				if object.fighter.flicker is not None:
					flicker_all()
			for object in objects:
				object.clear()
		for object in objects:
			object.clear()

		#handle keys and exit game if needed
		if game_turn % player.fighter.move_speed == 0:
			player_action = handle_keys()
			if player_action == 'exit':
				save_game()
				break

		#let monsters take their turn
		if game_state == 'playing' and player_action != 'didnt-take-turn':
			for object in objects:
				try:
					if object.ai and (game_turn % object.fighter.move_speed) == 0:
						object.ai.take_turn()
				except AttributeError:
					if object.ai and (game_turn % object.nonplayerchar.move_speed) == 0:
						object.ai.take_turn()





libtcod.console_set_custom_font('Bisasam15x15.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_ASCII_INROW)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'CyberRogue', False)
libtcod.sys_set_fps(LIMIT_FPS)
con = libtcod.console_new(MAP_WIDTH, MAP_HEIGHT)
panel = libtcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)
sidebar = libtcod.console_new(SIDEBAR_WIDTH, SCREEN_HEIGHT)
main_menu()