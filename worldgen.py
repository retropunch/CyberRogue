#!/usr/bin/python

import random
import libtcodpy as libtcod

global corpone, corponeproducts, corponehistory, corptwo, corptwoproducts, corptwohistory, corpthree, corpthreeproducts, corpthreehistory


def setcorps():
	global corpone, corponeproducts, corponehistory, corptwo, corptwoproducts, corptwohistory, corpthree, corpthreeproducts, corpthreehistory

	libtcod.namegen_parse('corpgen.txt')

	corpone = libtcod.namegen_generate('corpnames')
	corponeproducts = libtcod.namegen_generate('corpproducts')
	corponehistyear = random.randrange(2014, 2019, 1)
	corponehistory = "in the year " + str(corponehistyear) + " " + corpone + " " + str(libtcod.namegen_generate('corpactions')) + " " + str(libtcod.namegen_generate('corpnames')) + " causing " + corpone + " to gain a monopoly on " + corponeproducts

	corptwo = libtcod.namegen_generate('corpnames')
	corptwoproducts = libtcod.namegen_generate('corpproducts')
	corptwohistyear = random.randrange(2014, 2019, 1)
	corptwohistory = "in the year " + str(corptwohistyear) + " " + corptwo + " " + str(libtcod.namegen_generate('corpactions')) \
					 + " " + str(libtcod.namegen_generate('corpnames')) + " causing " + corptwo + " to gain a monopoly on " + corptwoproducts

	corpthree = libtcod.namegen_generate('corpnames')
	corpthreeproducts = libtcod.namegen_generate('corpproducts')
	corpthreehistyear = random.randrange(2014, 2019, 1)
	corpthreehistory = "in the year " + str(corpthreehistyear) + " " + corpthree + " " + str(libtcod.namegen_generate('corpactions')) \
					 + " " + str(libtcod.namegen_generate('corpnames')) + " causing " + corpthree + " to gain a monopoly on " + corpthreeproducts
