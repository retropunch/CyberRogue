__author__ = 'Bim'



import libtcodpy as libtcod

room = "room"

#def monsterplace():


def monster_chance():


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
def num_monsters():
	global maxmon
	libtcod.random_get_int(0, 0, maxmon)

	for i in range(num_monsters):
		#choose random spot for this monster
		x = libtcod.random_get_int(0, room , room )
		y = libtcod.random_get_int(0, room , room )

		#x = libtcod.random_get_int(0, room.x1 + 1, room.x2 - 1)
		#y = libtcod.random_get_int(0, room.y1 + 1, room.y2 - 1)

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
											eloyalty=0, vloyalty=0, ammo=0, charge=0, xp=100, move_speed=1, flicker=0, robot=False, death_function=monster_death, creddrop=0)
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

			object.append(monster)
