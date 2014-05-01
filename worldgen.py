#!/usr/bin/python

import random
import libtcodpy as libtcod

global corpone, corponeproducts, corponehistory, corptwo, corptwoproducts, corptwohistory, corpthree, corpthreeproducts, corpthreehistory


def setcorps():
	global corpone, corponeproducts, corponehistory, corptwo, corptwoproducts, corptwohistory, corpthree, corpthreeproducts, corpthreehistory, corpchosen, corpchosenproducts

	libtcod.namegen_parse('corpgen.txt'),

	#historychoice = [
	#	' In %(histyear1), %histcorp1 and + histcorp2 + "agreed to a mutual merger of equals, ending their long-running rivalry in pursuit of a common goal. The new entity," +corpchosen+ ", would start off with a complete monopoly over" +corpchosenproducts+'
	#	#,
	#	#'In %histyear2+ "," +histcorp2+ "declared bankruptcy. Their assets were forcibly seized by a shadowy cabal of investors known informally as" +corpchosen+". "+corpchosen+ "would later use those assets to engineer the destruction of several other minor competitors to secure a monopoly over" +corpchosenproducts+'
	#	#,
	#	#'"In" +histyear3+"," +corpchosen+ "("+country1+ "special operations division), refused to follow orders from their mother country and instead went rogue." +corpchosen+ "would later use their military assets to engineer the takeover of several other minor companies to secure a monopoly over" +corpchosenproducts+'
	#
	#	#'In +year+, wealthy philanthropists formed a 'nonprofit corporation  called +corpchosen+, dedicated towards +nonprofitaction+ +corpproducts+.'
	#	#,
	#	#'In +year+, +corpchosen+ (+country+ government agency) was formally privatized to help raise money for the mother country. +corpchosen+ specialized in +corpproducts+.'
	#	#,
	#	#'In +year+, the religious organization +corpchosen+ was established, dedicated towards +nonprofitaction+ +religiousactivity+. To secure funding for its nonprofit activities, +corpchosen+ opened up a business front that specialized in +corpproducts+.'
	#	#,
	#	#'In +year+, +corpname+ successfully infiltrated +corpname+, ending the long-running rivalry between the two companies. The newly merged entity, +corpchosen+, would start off with a complete monopoly over +corpproducts+.'
	#	#,
	#	#'In +year+, vulture capitalists established +corpchosen+ to fund innovative +corpproducts+ start-ups so as to later take them over and seize their considerable profits.'
	#	#,
	#	#'In +year+, the +ideology+ terrorist organization +corpchosen+  went legit  in return for legal immunity for their crimes. +corpchosen+ abandoned their political activism to instead focus on maintaining their massive +corpproducts holdings.'
	#	#,
	#	#'In +year+, the criminal organization +corpchosen+  went legit  in return for legal immunity for their crimes. +corpchosen+ abandoned their criminal activities to instead focus on maintaining their massive +corpproducts+ holdings.'
	#	#,
	#	#'In +year+, +moderateideology+ activists established a nonprofit corporation known as +corpchosen+ to help coordinate their political campaigns. To secure funding for its nonprofit activities, +corpchosen+ opened up a business front that specialized in +corpproducts+.'
	#	#,
	#	#'In +year+, a rich entrepreneur formed +corpchosen+, a +corpproducts+ startup, after being inspired by dreams about +religiousactivity+.'
	#	#,
	#	#'In +year+, +name+, +country+ preacher, declared himself the reincarnation of Jesus Christ and established a popular megachurch, today known as +corpchosen+, dedicated towards +nonprofitaction+ +religiousactivity+. To secure funding for its nonprofit activities, +corpchosen+ opened up a business front that specialized in +corpproducts+.'
	#	#,
	#	#'In +year+, +name+, +country+ general, established a private military corporation known as +corpchosen+. +corpchosen+ would later use their military assets to engineer the takeover of several other minor companies to secure a monopoly over +corpproducts+.'
	#	#,
	#	#'In +year+, +name+ died, leaving behind a charitable trust worth billions of dollars. This trust, known today as +corpchosen+, is dedicated towards +nonprofitaction+ +corpproducts+.'
	#	% dict(
	##histcorp1 = libtcod.namegen_generate('corpnames'),
	##histcorp2 = libtcod.namegen_generate('corpnames'),
	##histcorp3 = libtcod.namegen_generate('corpnames'),
	#histyear1 = random.randrange str(2014, 2019, 1))]
	##histyear2 = random.randrange(2014, 2019, 1),
	##histyear3 = random.randrange(2014, 2019, 1),
	##country1 = libtcod.namegen_generate('corpcountry'),
	##country2 = libtcod.namegen_generate('corpcountry'),
	##country3 = libtcod.namegen_generate('corpcountry'))]

	libtcod.namegen_parse('corpgen.txt')

	corpone = libtcod.namegen_generate('corpnames')
	corpchosen = corpone
	corponeproducts = libtcod.namegen_generate('corpproducts')
	corpchosenproducts = corponeproducts
	corponehistyear = random.randrange(2014, 2019, 1)
	corponehistory = "in the year " + str(corponehistyear) + " " + corpone + " " + str(
		libtcod.namegen_generate('corpactions')) \
					 + " " + str(
		libtcod.namegen_generate('corpnames')) + " causing " + corpone + " to gain a monopoly on " + corponeproducts

	corptwo = libtcod.namegen_generate('corpnames')
	corpchosen = corptwo
	corptwoproducts = libtcod.namegen_generate('corpproducts')
	corpchosenproducts = corptwoproducts
	corptwohistyear = random.randrange(2014, 2019, 1)
	corptwohistory = "in the year " + str(corptwohistyear) + " " + corptwo + " " + str(
		libtcod.namegen_generate('corpactions')) \
					 + " " + str(
		libtcod.namegen_generate('corpnames')) + " causing " + corptwo + " to gain a monopoly on " + corptwoproducts

	corpthree = libtcod.namegen_generate('corpnames')
	corpchosen = corpthree
	corpthreeproducts = libtcod.namegen_generate('corpproducts')
	corpchosenproducts = corpthreeproducts
	corpthreehistyear = random.randrange(2014, 2019, 1)
	corpthreehistory = "in the year " + str(corpthreehistyear) + " " + corpthree + " " + str(
		libtcod.namegen_generate('corpactions')) \
					   + " " + str(
		libtcod.namegen_generate('corpnames')) + " causing " + corpthree + " to gain a monopoly on " + corpthreeproducts
