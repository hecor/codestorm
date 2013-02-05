#!/usr/bin/python

""" 
bug strategy:
    add vola to the buy strategy
    total_spend_money = min( max( 500, f(x) ), 3000 )
    f(x) = 25000*vola

sell strategy:
    add a case to sell: the price fall in 3 continuous days
"""

import sys
from socket import *
#import cjson
import simplejson as json
#from cPickle import *
from time import *

from pylab import *
import threading
import random
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, RadioButtons
from matplotlib.font_manager import *


######################################
g_value = {}
g_value["cashValue"] = []
g_value["inventoryValue"] = []
g_value["totalValue"] = []
g_drawRound = 0

class Animate(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.fig = plt.figure()
        self.ax_quantity = self.fig.add_axes([0.05,0.05,0.56,0.2])
        self.ax_price = self.fig.add_axes([0.05, 0.3, 0.56, 0.2])
        self.ax_value = self.fig.add_axes([0.05, 0.55, 0.56, 0.4])
        self.ax_list = self.fig.add_axes([0.66, 0.05, 0.29, 0.45])
        self.ax_pie = self.fig.add_axes([0.66, 0.55, 0.29, 0.4])
        self.colors = ('b', 'g', 'r', 'c', 'm', 'y', 'w')
        self.ax_pie.pie([], labels=[], colors = self.colors, autopct='%1.1f%%', shadow=True)
        # attributes for list
        self.list_col = 3
        self.fp = FontProperties(size="small")
        self.fp_selected = FontProperties(size="large", style="italic")
        
    def run(self):
        self.fig.canvas.mpl_connect('pick_event', self.onpick)
        timer = self.fig.canvas.new_timer(interval=500)
        timer.add_callback(self.myfresh)
        timer.start()
        plt.show()
    
    def draw_value(self, ax_value):
        ax_value.clear()
        ax_value.set_xlim(1, totalRounds)
        ax_value.set_xlabel('rounds')
        ax_value.set_ylabel('portfolio($)')
        ax_value.plot(arange(1, g_drawRound+1), g_value["totalValue"][ : g_drawRound], label='total')
        ax_value.plot(arange(1, g_drawRound+1), g_value["cashValue"][ : g_drawRound], label='cash')
        ax_value.plot(arange(1, g_drawRound+1), g_value["inventoryValue"][ : g_drawRound], label='inventory')
        ax_value.legend(loc="best")
        
    def draw_test_fruit(self, ax_price, ax_quantity):
        ax_price.clear()
        ax_quantity.clear()
        
        ax_price.set_xlim(1, totalRounds)
        ax_quantity.set_xlabel('rounds')
        ax_quantity.set_ylabel('price($)')
 #       ax_price.set_title(g_test_fruit)
        ax_price.plot(arange(1, g_drawRound+1), g_history[g_test_fruit]["history_prices"][ : g_drawRound])

        ax_quantity.set_xlim(1, totalRounds)
        ax_quantity.set_xlabel('rounds')
        ax_quantity.set_ylabel('quantity')
        ax_quantity.set_title(g_test_fruit)
        ax_quantity.plot(arange(1, g_drawRound+1), g_history[g_test_fruit]["history_own_quantity"][ : g_drawRound])
        
#    def onbutton(self, label):
#        global g_test_fruit
#        g_test_fruit = label
        
    def onpick(self, event):
        global g_test_fruit
        if isinstance(event.artist, Text):
            t = event.artist
            g_test_fruit = t.get_text()
       #     print g_test_fruit
        
    def draw_button(self, ax_list):
        fruits = g_history.keys()
        length = len(fruits)
        rows = int((length + self.list_col - 1) / self.list_col)
        xlim = self.list_col * 20 + 20 * 2
        ylim = rows * 10 + 10
        try:
            index = fruits.index(g_test_fruit)
        except ValueError:
            print "value error in fruits.index()"
            index = 0
            
        ax_list.clear()
        ax_list.set_xlim(0, xlim)
        ax_list.set_ylim(0, ylim)
        
        i = 0
        while i < length:
            if i != index:
                ax_list.text(i%self.list_col * 20 + 20, int(i/self.list_col)* 10 + 10, fruits[i], fontproperties=self.fp, picker=True)
            else:
                ax_list.text(i%self.list_col * 20 + 20, int(i/self.list_col)* 10 + 10, fruits[i], fontproperties=self.fp_selected, color='r', picker=True)
            i = i + 1
        
    def myfresh(self):
        if g_drawRound == 0:
            return
        
        self.draw_value(self.ax_value)
        self.draw_pie(self.ax_pie)
        self.draw_test_fruit(self.ax_price, self.ax_quantity)
        self.draw_button(self.ax_list)
        
        self.fig.canvas.draw()
    
    def draw_pie(self, ax_pie):
        fruits = []
        percentage = []
        values = {}
        fruits.append("Cash")
        percentage.append(g_value["cashValue"][g_drawRound-1])
        for (k,v) in g_history.iteritems():
            value = g_history[k]["history_prices"][g_drawRound-1] * g_history[k]["history_own_quantity"][g_drawRound-1]
            values[k] = value
        i = 0
        for (k, v) in sorted( values.items(), key=lambda values:values[1], reverse=True ):
            fruits.append(k)
            percentage.append(v)
            i = i+1
            if i >= 5:
                break
        fruits.append("Others")
        percentage.append(g_value["totalValue"][g_drawRound-1] - sum(percentage))
        ax_pie.clear()
        ax_pie.pie(percentage, labels=fruits, colors=self.colors, autopct='%1.1f%%', shadow=True)


#########################################



teamName = "Nivarna_buy_1"
teamKey = "nave40rare"
server = "114.80.213.55"
port = 9220
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

log_file = open( "log_1.txt", "w" )      # log file
class Logger:
    def write( self, s ):
        log_file.write( s )
        log_file.flush()
        sys.stderr.write( s )

mylogger = Logger()
sys.stdout = mylogger

g_test_fruit = "Durian"
g_fruit_category = 30

g_trade_volume = 0

g_parameters = {"bull":{"first_bid":0.92, "max_price":0.78, "max_price2":0.90, "buy_unit":60000, "buy_min":800, "buy_max":6000}, 
                "bear":{"first_bid":0.95, "max_price":0.84, "max_price2":0.93, "buy_unit":40000, "buy_min":500, "buy_max":3500}}
g_market_kind = "bull"

######################################

def evaluateS( price, quantitysold, quantityown, quantitymarket, prod, currentRound ):
	#put your evaluation function here, currently buys everything offered
    buyflag = False
    bidprice = price
    bidquantity = quantitysold
    if len(g_history[prod]["history_prices"]) >= 7 and price >= sum( g_history[prod]["history_prices"][-7:-1] ) / 6 and g_history[prod]["history_prices"][-1] >= g_history[prod]["history_prices"][-2] and g_history[prod]["history_prices"][-2] >= g_history[prod]["history_prices"][-3]:
        buyflag = True
        bidprice = price * ( 1 + 0.012 * min( g_history[prod]["not_buy_days"], 4 ) ) + 0.02
        spend_money = g_parameters[g_market_kind]["buy_unit"] * g_history[prod]["history_volatility"][-1]
        bidquantity = min( quantitysold, min( max( g_parameters[g_market_kind]["buy_min"], spend_money ), g_parameters[g_market_kind]["buy_max"], cash ) / bidprice )
    bidquantity = int( bidquantity )
    if bidquantity <= 0:
        buyflag = False
    if len( g_history[prod]["history_demand"] ) >= 5 and g_history[prod]["history_own_quantity"][-1] >= average( g_history[prod]["history_demand"][-5 : ] ) * 2.8 :
        buyflag = False
    
    if buyflag == False:
    	g_history[prod]["not_buy_days"] = 0
    else:
        g_history[prod]["buy_rounds"].append( currentRound )
        if g_history[prod]["if_clear_max_price"]:
            g_history[prod]["max_price"] = price
            g_history[prod]["first_bid"] = 0
            g_history[prod]["if_clear_max_price"] = False
    
    return buyflag, bidprice, bidquantity

def evaluateD( price, quantityasked, quantityown, quantitymarket, prod, currentRound ):
	#put your evaluation function here, currently sells everything asked
    global g_history
    sellflag = False
    if g_history[prod]["first_bid"] != 0 and price < g_history[prod]["first_bid"] * g_parameters[g_market_kind]["first_bid"]:
        sellflag = True
    if len( g_history[prod]["history_prices"] ) >= 2 and price < g_history[prod]["history_prices"][-2] * 0.92:
        sellflag = True
    if price < g_history[prod]["max_price"] * g_parameters[g_market_kind]["max_price"]:
        sellflag = True
    if currentRound >= 5 and price < g_history[prod]["max_price"] * g_parameters[g_market_kind]["max_price2"] and g_history[prod]["history_own_quantity"][-1] >= average( g_history[prod]["history_demand"][-5 : ] ) * 2:
        sellflag = True
    if len( g_history[prod]["history_prices"] ) >= 4 and g_history[prod]["history_prices"][-1] < g_history[prod]["history_prices"][-2] and g_history[prod]["history_prices"][-2] < g_history[prod]["history_prices"][-3] and g_history[prod]["history_prices"][-3] < g_history[prod]["history_prices"][-4] :
        sellflag = True
    bidprice = price * ( 1 - 0.03 * min( g_history[prod]["not_sell_days"], 3 ) ) - 0.02
    bidquantity = min( quantityasked, quantityown )
    
    bidquantity = int( bidquantity )
    if bidquantity <= 0:
        sellflag = False
    
    if sellflag == False:
        g_history[prod]["not_sell_days"] = 0
    else:
        g_history[prod]["sell_rounds"].append( currentRound )
        g_history[prod]["if_clear_max_price"] = True
        
    return sellflag, bidprice, bidquantity

portfolio = {}
portfolio[g_test_fruit] = 0
marketportfolio = {}
marketportfolio[g_test_fruit] = 0
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

    # Append a created bid to your list
#    global g_trade_volume
#    if currentRound % 10 == 0:
#        if g_trade_volume < 5000:
#            best_prod = ""
#            best_price = 0
#            for (k, v) in g_history.iteritems():
#                if v["history_prices"][-1] / v["history_prices"][-7] > best_price:
#                    best_prod = k
#                    best_price = v["history_prices"][-1] / v["history_prices"][-7]
#            mybid = newbid.copy()
#            mybid["orderId"] = "buybid_extra_1"
#            mybid["productId"] = best_prod
#            try:
#                mybid["price"] = g_history[best_prod]["history_prices"][-1]*1.06
#                mybid["quantity"] = int( (5000-g_trade_volume) / mybid["price"] )
#            except KeyError:
#                print "key error when append extra bid"
#            bids.append( mybid )
#        g_trade_volume = 0
    

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
    try:
        g_value["cashValue"].append( roundStart['portfolio']['cashValue'] )
        g_value["inventoryValue"].append( roundStart['portfolio']['inventoryValue'] )
        g_value["totalValue"].append( roundStart['portfolio']['cashValue'] + roundStart['portfolio']['inventoryValue'] )
    except KeyError:
        print "key error in g_history['cashValue'].append()"

    for ( k, v ) in portfolio.iteritems():
        portfolio[k] = 0
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
            g_history[productId]["history_own_quantity"] = []
            g_history[productId]["buy_rounds"] = []
            g_history[productId]["sell_rounds"] = []
            g_history[productId]["max_price"] = 0
            g_history[productId]["if_clear_max_price"] = False
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
			( 4 * g_history[productId]["history_volatility"][currentRound - 2] 
			  + abs( g_history[productId]["history_prices"][-1] 
			  - g_history[productId]["history_prices"][-2] ) 
			  / g_history[productId]["history_prices"][-2] ) / 5 )
            
    for item in roundStart['demand']:
        productId = item["productId"]
        if productId not in g_history:
            g_history[productId] = {}
            g_history[productId]["history_prices"] = []
            g_history[productId]["history_supply"] = []
            g_history[productId]["history_demand"] = []
            g_history[productId]["history_volatility"] = []
            g_history[productId]["history_own_quantity"] = []
            g_history[productId]["buy_rounds"] = []
            g_history[productId]["sell_rounds"] = []
            g_history[productId]["max_price"] = 0
            g_history[productId]["if_clear_max_price"] = False
            g_history[productId]["first_bid"] = 0
            g_history[productId]["not_buy_days"] = 0
            g_history[productId]["not_sell_days"] = 0
        g_history[productId]["history_demand"].append( item["quantity"] )
        try:
            g_history[productId]["history_own_quantity"].append( portfolio[productId] )
        except KeyError:
            g_history[productId]["history_own_quantity"].append( 0 )
            
        if currentRound > 40:
            total_price_inc = 0
            for (k, v) in g_history.iteritems():
                avg_price = average( v["history_prices"][ -40 : ] )
                price_inc = (v["history_prices"][-1] - avg_price) / avg_price
                total_price_inc = total_price_inc + price_inc
            if total_price_inc > 0:
                g_market_kind = "bull"
            else:
                g_market_kind = "bear"
    
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

    "update first_bid price"
    for item in roundEnd["winningBids"]:
        prod = item["productId"]
        if g_history[prod]["first_bid"] == 0:
            g_history[prod]["first_bid"] = item["price"]
            
    "update g_trade_volume"
    global g_trade_volume
    for item in roundEnd["winningBids"]:
        g_trade_volume = g_trade_volume + item["price"]*abs(item["quantity"])
    for item in roundEnd["winningAsks"]:
        g_trade_volume = g_trade_volume + item["price"]*abs(item["quantity"])
    
    global g_drawRound
    g_drawRound = currentRound
    
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

    print "not_bug_days: " + str( g_history[g_test_fruit]["not_buy_days"] )
    print "not_sell_days: " + str( g_history[g_test_fruit]["not_sell_days"] )
    print "quantown: ", portfolio[g_test_fruit]
    print "marketportfolio: " + str( marketportfolio[g_test_fruit] )
    print "max_price: " + str( g_history[g_test_fruit]["max_price"] )
    print "first_bid: " + str( g_history[g_test_fruit]["first_bid"] )
            
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

""" begin to show gui in a new thread """
ani = Animate()
ani.start()

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
log_file.close()

#""" paint """
#i = 1
#for ( k, v ) in sorted( g_history.iteritems(), key = lambda g_history:g_history[0] ) :
#	subplot( 2, 5, i )
#	t = arange( 0, totalRounds, 1 )
#
#	prices = []
#	p0 = v["history_prices"][0]
#	for p in v["history_prices"]:
#		prices.append( p / p0 )
#	plot( t, prices, 'b', linewidth=1.0 )
#    
#        sellprices = []
#        sellrounds = []
#        for r in v["sell_rounds"]:
#            sellprices.append( prices[r-1] )
#            sellrounds.append( r-1 )
#        plot( sellrounds, sellprices, 'r*', ms=10 )
#        
#        buyprices = []
#        buyrounds = []
#        for r in v["buy_rounds"]:
#            buyprices.append( prices[r-1] )
#            buyrounds.append( r-1 )
#        plot( buyrounds, buyprices, 'k*', ms=10 )
#    
#	
##	supplies = []
##	s0 = v["history_supply"][0]
##	for s in v["history_supply"] :
##		supplies.append( float( s ) / s0 )
##	plot( t, supplies, 'g', linewidth = 1.0 )
#
##	demands = []
###	d0 = v["history_demand"][0]
##	for d in v["history_demand"] :
##		demands.append( float( d ) / s0 )
#
##	plot( t, v["history_demand"], 'r', linewidth = 1.0 )
##        plot( t, v["history_own_quantity"], 'b', linewidth = 1.0 )
#
##	volas = []
##	v0 = v["history_volatility"][5]
##	for v in v["history_volatility"]:
##		volas.append( float(v) / v0 )
##	plot( t, volas, 'c', linewidth = 1.0 )
#    
#	title( str( k ) )
#	i = i + 1
#	
#show()















