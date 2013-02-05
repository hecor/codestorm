#!/usr/bin/python

import sys
from socket import *
#import cjson
import simplejson as json
#from cPickle import *
from time import *

teamName = "Nirvana_sample"
teamKey  = "note77past"
server   = "114.80.213.55"
port     = 8897
#1024 worked fine for both test and competition rounds
buffer   = 1024

#switch to simplejson functions, but be warned they might be too slow.
#decode=cjson.decode
#encode=cjson.encode
decode=json.loads
encode=json.dumps

######################################
##### our own variables #####
g_mmds_prices = {}		# for record market player demand and supply price for every fruit in each round

def evaluateS(price,quantitysold,quantityown,quantitymarket,prod):
	#put your evaluation function here, currently buys everything offered
	buyflag=True
	bidprice=price
	bidquantity=quantitysold
	return buyflag,bidprice,bidquantity

def evaluateD(price,quantityasked,quantityown,quantitymarket,prod):
	#put your evaluation function here, currently sells everything asked
	sellflag=True
	bidprice=price
	bidquantity=quantityasked
	return sellflag,bidprice,bidquantity

portfolio={}
marketportfolio={}
cash=0
currentRound=0

def getOrder(roundStart):
    "Calculate your order here and return it as a dict"
    bids = []
    newbid = {"side":"BUY", "teamName":teamName}
    for i,bid in enumerate(roundStart["supply"]):
        prod=bid["productId"]
        price=bid["price"]
        try:
            quantown=portfolio[prod]
        except KeyError:
            quantown=0
        try:
            quantmarket=marketportfolio[prod]
        except KeyError:
            quantmarket=0
        quantbid=bid["quantity"]
        buyflag,mybidprice,mybidquantity=evaluateS(price,quantbid,quantown,quantmarket,prod)
        if(buyflag):
            mybid = newbid.copy()
            mybid["orderId"] = "buybid"+str(i)
            mybid["productId"] = prod
            mybid["price"] = mybidprice
            mybid["quantity"] = int(mybidquantity)
            bids.append(mybid)
    # Append a created bid to your list
    

    # Do likewise for your asks
    asks=[]
    newask = {"side":"SELL", "teamName":teamName}
    for i,bid in enumerate(roundStart["demand"]):
        prod=bid["productId"]
        price=bid["price"]
        try:
            quantown=portfolio[prod]
        except KeyError:
            continue
        try:
            quantmarket=marketportfolio[prod]
        except KeyError:
            quantmarket=0
        quantask=bid["quantity"]
        sellflag,mybidprice,mybidquantity=evaluateD(price,quantask,quantown,quantmarket,prod)
        if(sellflag):
            myask = newask.copy()
            myask["orderId"] = "sellbid"+str(i)
            myask["productId"] = prod
            myask["price"] = mybidprice
            myask["quantity"] = int(mybidquantity)
            asks.append(myask)
    order = {"Order": {"bids": bids, "asks": asks}}
    return order

def processRoundStart(roundStart):
    for item in roundStart['portfolio']['positions']:
        portfolio[item["productId"]]=item["quantity"]
  
    #process the RoundStart
    global g_mmds_prices
    currentRound = roundStart["roundNumber"]
    for item in roundStart['supply']:
        productId = item["productId"]
        if productId not in g_mmds_prices:
            g_mmds_prices[productId] = []
        g_mmds_prices[productId].append( item["price"] )
    
def processRoundEnd(roundEnd):
    "Do any processing you want with the round end data here"
    for item in roundEnd["marketTransactions"]:
        try:
            marketportfolio[item["productId"]]=marketportfolio[item["productId"]]+item["quantity"]
        except KeyError:
            marketportfolio[item["productId"]]=item["quantity"]
            
#MAIN LOOP
s = socket(AF_INET, SOCK_STREAM)
s.connect((server, port))
f=s.makefile('r',0)
login=encode({"Login":{"teamName":teamName,"key":teamKey}})
s.send(login+"\n")

# Get the Welcome Message back
welcome = decode(f.readline())['Welcome']
totalRounds = welcome["roundTotal"]
cash = welcome["initialCash"]
portfoliovalue=0
currentRound = 0

while currentRound<totalRounds:
    print currentRound,cash,portfoliovalue
    # Get the Round Start Message
    js=f.readline()
    timestart=time()
    try:
        roundStart = decode(js)["RoundStart"]
    except KeyError:
        print "Decoding problem with ",js

    processRoundStart(roundStart)
    
    cash = roundStart["portfolio"]["cashValue"]
    portfoliovalue=roundStart['portfolio']['inventoryValue']
    currentRound = roundStart["roundNumber"]

    # Process the info, come up with our order,
    # send it off, and get back the Ack
    
    myOrder = getOrder(roundStart)
    s.send(encode(myOrder)+"\n")
    js=f.readline()
    try:
    	Ack=decode(js)["Ack"]
    except KeyError:
    	print "Decoding problem with ",js

    # Get the Round End, do Round End calculations
    js=f.readline()
    try:
        roundEnd=decode(js)["RoundEnd"]
    except KeyError:
        print "Decoding problem with ",js
    
    processRoundEnd(roundEnd)

# The Game is over, print out how we did
js=f.readline()
try:
       gameEnd=decode(js)["GameEnd"]
except KeyError:
       print "Decoding problem with ",js

print ("cash: %f" % gameEnd["portfolio"]["cashValue"])
print ("inv : %f" % gameEnd["portfolio"]["inventoryValue"])
print ("tot : %f" % (gameEnd["portfolio"]["cashValue"] + gameEnd["portfolio"]["inventoryValue"]))


###### analysis the data after the game ######
ds_price_file = open( "ds_price_file.txt", "w" )
for (k, v) in g_mmds_prices.iteritems() :
#   ds_price_file.write( k )
    ds_price_file.write( str(v) )
    ds_price_file.write( "\n" )
ds_price_file.close()










