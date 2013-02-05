#!/usr/bin/python

import sys
from socket import *
#import cjson
import simplejson as json
#from cPickle import *
from time import *

from pylab import *

teamName = "Nivarna"
teamKey = "wahl95hell"
server = "114.80.213.55"
port = 8897
#1024 worked fine for both test and competition rounds
buffer = 1024

#switch to simplejson functions, but be warned they might be too slow.
#decode=cjson.decode
#encode=cjson.encode
decode = json.loads
encode = json.dumps

######################################
##### our own variables #####
g_history = {}		# for record market player demand and supply price for every fruit in each round

log_file = open( "log.txt", "w" )      # log file
class Logger:
    def write( self, s ):
        log_file.write( s )
        log_file.flush()
        sys.stderr.write( s )

mylogger = Logger()
sys.stdout = mylogger

g_test_fruit = "Durian"
g_fruit_category = 10

######################################

def evaluateS( price, quantitysold, quantityown, quantitymarket, prod, currentRound ):
	#put your evaluation function here, currently buys everything offered
    buyflag = False
    bidprice = price
    bidquantity = quantitysold
    if currentRound <= 4:
        buyflag = True
        bidprice = price
        bidquantity = min( quantitysold, int( 500 / bidprice ) )
    elif price >= sum( g_history[prod]["history_prices"][-5:-1] ) / 4 and g_history[prod]["history_prices"][-1] >= g_history[prod]["history_prices"][-2] and g_history[prod]["history_prices"][-2] >= g_history[prod]["history_prices"][-3]:
        buyflag = True
        g_history[prod]["buy_rounds"].append(currentRound)
        bidprice = price * ( 1 + 0.02 * min( g_history[prod]["not_buy_days"], 3 ) ) + 0.01
        bidquantity = min( quantitysold, int( min( cash, 2500 ) / bidprice ) )
    if currentRound >= 150:
        buyflag = False
        
    if buyflag == False:
    	g_history[prod]["not_buy_days"] = 0
    
    return buyflag, bidprice, bidquantity

def evaluateD( price, quantityasked, quantityown, quantitymarket, prod, currentRound ):
	#put your evaluation function here, currently sells everything asked
    global g_history
    sellflag = False
    if g_history[prod]["first_bid"] != 0 and price < g_history[prod]["first_bid"] * 0.9:
        sellflag = True
    if len(g_history[prod]["history_prices"]) >= 2 and price < g_history[prod]["history_prices"][-2] * 0.9:
        sellflag = True
    if price < g_history[prod]["max_price"] * 0.8:
        sellflag = True
    bidprice = price * ( 1 - 0.03 * min( g_history[prod]["not_sell_days"], 4 ) ) - 0.01
    bidquantity = min( quantityasked, quantityown )
    
    if sellflag == False:
        g_history[prod]["not_sell_days"] = 0
        
    return sellflag, bidprice, bidquantity

portfolio = {}
marketportfolio = {}
cash = 0
currentRound = 0

def getOrder( roundStart ):
    "Calculate your order here and return it as a dict"
    bids = []
    newbid = {"side":"BUY", "teamName":teamName}
    currentRound = roundStart["roundNumber"]
    for i, bid in enumerate( roundStart["supply"] ):
        prod = bid["productId"]
        price = bid["price"]
        try:
            quantown = portfolio[prod]
        except KeyError:
            quantown = 0
        try:
            quantmarket = marketportfolio[prod]
        except KeyError:
            quantmarket = 0
        quantbid = bid["quantity"]
        buyflag, mybidprice, mybidquantity = evaluateS( price, quantbid, quantown, quantmarket, prod, currentRound )
        if( buyflag ):
            mybid = newbid.copy()
            mybid["orderId"] = "buybid" + str( i )
            mybid["productId"] = prod
            mybid["price"] = mybidprice
            mybid["quantity"] = int( mybidquantity )
            bids.append( mybid )
            
        if prod == g_test_fruit:
            print "\nquantown: ", quantown
    # Append a created bid to your list
    

    # Do likewise for your asks
    asks = []
    newask = {"side":"SELL", "teamName":teamName}
    for i, bid in enumerate( roundStart["demand"] ):
        prod = bid["productId"]
        price = bid["price"]
        try:
            quantown = portfolio[prod]
        except KeyError:
            continue
        try:
            quantmarket = marketportfolio[prod]
        except KeyError:
            quantmarket = 0
        quantasked = bid["quantity"]
        sellflag, mybidprice, mybidquantity = evaluateD( price, quantasked, quantown, quantmarket, prod, currentRound )
        if( sellflag ):
            myask = newask.copy()
            myask["orderId"] = "sellbid" + str( i )
            myask["productId"] = prod
            myask["price"] = mybidprice
            myask["quantity"] = int( mybidquantity )
            asks.append( myask )
    order = {"Order": {"bids": bids, "asks": asks}}
    return order

def processRoundStart( roundStart ):
    for item in roundStart['portfolio']['positions']:
        portfolio[item["productId"]] = item["quantity"]
#        print item
#    print "\n\n"

    print "\nsupply: "
    for item in roundStart["supply"]:
    	if item["productId"] == g_test_fruit:
    	   print item
    	   break
    print "\ndemand: "
    for item in roundStart["demand"]:
    	if item["productId"] == g_test_fruit:
    	   print item
    	   break
  
    #process the RoundStart
    global g_history
    currentRound = roundStart["roundNumber"]
    for item in roundStart['supply']:
        productId = item["productId"]
        if productId not in g_history:
            g_history[productId] = {}
            g_history[productId]["history_prices"] = []
            g_history[productId]["history_supply"] = []
            g_history[productId]["history_demand"] = []
            g_history[productId]["history_volatility"] = []
            g_history[productId]["buy_rounds"] = []
            g_history[productId]["max_price"] = 0
            g_history[productId]["first_bid"] = 0
            g_history[productId]["not_buy_days"] = 0
            g_history[productId]["not_sell_days"] = 0
        g_history[productId]["history_prices"].append( item["price"] )
        g_history[productId]["history_supply"].append( item["quantity"] )
        if item["price"] > g_history[productId]["max_price"]:
            g_history[productId]["max_price"] = item["price"]
        if currentRound == 1:
        	g_history[productId]["history_volatility"].append( 0 )
        else:
        	g_history[productId]["history_volatility"].append( 
			( 4*g_history[productId]["history_volatility"][currentRound - 2] 
			  + abs(g_history[productId]["history_prices"][currentRound - 1] 
			  - g_history[productId]["history_prices"][currentRound - 2]) 
			  / g_history[productId]["history_prices"][currentRound-2] ) / 5 )
            
    for item in roundStart['demand']:
        productId = item["productId"]
        if productId not in g_history:
            g_history[productId] = {}
            g_history[productId]["history_prices"] = []
            g_history[productId]["history_supply"] = []
            g_history[productId]["history_demand"] = []
            g_history[productId]["history_volatility"] = []
            g_history[productId]["buy_rounds"] = []
            g_history[productId]["max_price"] = 0
            g_history[productId]["first_bid"] = 0
            g_history[productId]["not_buy_days"] = 0
            g_history[productId]["not_sell_days"] = 0
        g_history[productId]["history_demand"].append( item["quantity"] )
    
def processRoundEnd( roundEnd, myOrder ):
    "Do any processing you want with the round end data here"
    for item in roundEnd["marketTransactions"]:
        try:
            marketportfolio[item["productId"]] = marketportfolio[item["productId"]] + item["quantity"]
        except KeyError:
            marketportfolio[item["productId"]] = item["quantity"]
    
    global g_history
    "update g_history[prod]['not_sell_days']"
    for item in myOrder["asks"]:
        prod = item["productId"]
        flag = False
        for sold_item in roundEnd["winningAsks"]:
            if sold_item["productId"] == prod:
                g_history[prod]["not_sell_days"] = 0
                flag = True
                break
        if flag == False:
            g_history[prod]["not_sell_days"] = g_history[prod]["not_sell_days"] + 1

    "update g_history[prod]['not_buy_days']"
    for item in myOrder["bids"]:
        prod = item["productId"]
        flag = False
        for buy_item in roundEnd["winningBids"]:
            if buy_item["productId"] == prod:
                g_history[prod]["not_buy_days"] = 0
                flag = True
                break
        if flag == False:
            g_history[prod]["not_buy_days"] = g_history[prod]["not_buy_days"] + 1

    "update first_bidprice"
    for item in roundEnd["winningBids"]:
        prod = item["productId"]
        if g_history[prod]["first_bid"] == 0:
            g_history[prod]["first_bid"] = item["price"]
    
    
    print "\nmyOrder{'bids'}: "
    for item in myOrder["bids"]:
    	if item["productId"] == g_test_fruit:
    	   print item
    	   break
    print "\nmyOrder{'asks'}: "
    for item in myOrder["asks"]:
    	if item["productId"] == g_test_fruit:
    	   print item
    	   break
    print "\nroundEnd{'winningBids'}: "
    for item in roundEnd["winningBids"]:
    	if item["productId"] == g_test_fruit:
    	   print item
    	   break
    print "\nroundEnd{'winningAsks'}: "
    for item in roundEnd["winningAsks"]:
    	if item["productId"] == g_test_fruit:
    	   print item
    	   break
    print "\nnot_bug_days: " + str( g_history[g_test_fruit]["not_buy_days"] )
    print "\nnot_sell_days: " + str( g_history[g_test_fruit]["not_sell_days"] )
    print "\nmarketportfolio: " + str( marketportfolio[g_test_fruit] )
            
#MAIN LOOP
s = socket( AF_INET, SOCK_STREAM )
s.connect( ( server, port ) )
f = s.makefile( 'r', 0 )
login = encode( {"Login":{"teamName":teamName, "key":teamKey}} )
s.send( login + "\n" )

# Get the Welcome Message back
welcome = decode( f.readline() )['Welcome']
totalRounds = welcome["roundTotal"]
cash = welcome["initialCash"]
init_cash = cash
portfoliovalue = 0
currentRound = 0

print "Game begin: ", cash, portfoliovalue

while currentRound < totalRounds:
    # Get the Round Start Message
    js = f.readline()
    timestart = time()
    try:
        roundStart = decode( js )["RoundStart"]
    except KeyError:
        print "Decoding problem with ", js
    
    cash = roundStart["portfolio"]["cashValue"]
    portfoliovalue = roundStart['portfolio']['inventoryValue']
    currentRound = roundStart["roundNumber"]
    print "\n\n**********************************"
    print "Round", currentRound, ":", cash, portfoliovalue
    
    processRoundStart( roundStart )

    # Process the info, come up with our order,
    # send it off, and get back the Ack
    
    myOrder = getOrder( roundStart )
    s.send( encode( myOrder ) + "\n" )
    js = f.readline()
    try:
    	Ack = decode( js )["Ack"]
    except KeyError:
    	print "Decoding problem with ", js

    # Get the Round End, do Round End calculations
    js = f.readline()
    try:
        roundEnd = decode( js )["RoundEnd"]
    except KeyError:
        print "Decoding problem with ", js
    
    processRoundEnd( roundEnd, myOrder["Order"] )

# The Game is over, print out how we did
js = f.readline()
try:
       gameEnd = decode( js )["GameEnd"]
except KeyError:
       print "Decoding problem with ", js

print ( "cash: %f" % gameEnd["portfolio"]["cashValue"] )
print ( "inv : %f" % gameEnd["portfolio"]["inventoryValue"] )
print ( "tot : %f" % ( gameEnd["portfolio"]["cashValue"] + gameEnd["portfolio"]["inventoryValue"] ) )


###### analysis the data after the game ######
history_data_file = open( "history_data.txt", "w" )
for ( k, v ) in sorted( g_history.iteritems(), key = lambda g_history:g_history[0] ) :
    history_data_file.write( str( k ) + ':\n' )
    for ( kk, vv ) in sorted( v.iteritems(), key = lambda v:v[0] ) :
    	history_data_file.write( '\t' + str( kk ) + ':\t' + str( vv ) + '\n' )
history_data_file.close()


info_file = open( "info.txt", "w" )

info_file.write( "the sequence of fruits: " )
for ( k, v ) in sorted( g_history.iteritems(), key = lambda g_history:g_history[0] ) :
	info_file.write( str( k ) + '\t' )
	
info_file.write( '\nprices:\n' )
for ( k, v ) in sorted( g_history.iteritems(), key = lambda g_history:g_history[0] ) :
    info_file.write( str( v["history_prices"] ) )
    info_file.write( '\n' )

info_file.write( '\nsupply:\n' )
for ( k, v ) in sorted( g_history.iteritems(), key = lambda g_history:g_history[0] ) :
    info_file.write( str( v["history_supply"] ) )
    info_file.write( '\n' )
    
info_file.write( '\ndemand:\n' )
for ( k, v ) in sorted( g_history.iteritems(), key = lambda g_history:g_history[0] ) :
    info_file.write( str( v["history_demand"] ) )
    info_file.write( '\n' )

info_file.close()


i = 1
for ( k, v ) in sorted( g_history.iteritems(), key = lambda g_history:g_history[0] ) :
	subplot( 2, 5, i )
	t = arange( 0, totalRounds, 1 )
	prices = []
	p0 = v["history_prices"][0]
	for p in v["history_prices"] :
		prices.append( p / p0 )
	plot( t, prices, 'b', linewidth = 1.0 )
	
#	supplies = []
#	s0 = v["history_supply"][0]
#	for s in v["history_supply"] :
#		supplies.append( float( s ) / s0 )
#	plot( t, supplies, 'g', linewidth = 1.0 )
#	
#	demands = []
##	d0 = v["history_demand"][0]
#	for d in v["history_demand"] :
#		demands.append( float( d ) / s0 )
#	plot( t, demands, 'r', linewidth = 1.0 )
	
	volas = []
	v0 = v["history_volatility"][5]
	for v in v["history_volatility"]:
		volas.append( float(v) / v0 )
	plot( t, volas, 'c', linewidth = 1.0 )
	
	title( str( k ) )
	i = i + 1
	
show()










