import logging
from socketclusterclient import Socketcluster
logging.basicConfig(format="%s(levelname)s:%(message)s", level=logging.DEBUG)

import json

api_credentials = json.loads('{}')
api_credentials["apiKey"]="xxx"
api_credentials["apiSecret"]="xxx"


def your_code_starts_here(socket):
    ###Code for subscription
    socket.subscribe('TRADE-OK--BTC--CNY')                 # Channel to be subscribed

    def channelmessage(key, data):                         # Messages will be received here
        print ("\n\n\nGot data "+json.dumps(data, sort_keys=True)+" from channel "+key)

    socket.onchannel('TRADE-OK--BTC--CNY', channelmessage) # This is used for watching messages over channel
    
    ###Code for emit

    def ack(eventname, error, data):
        print ("\n\n\nGot ack data " + json.dumps(data, sort_keys=True) + " and eventname is " + eventname)    
    
    socket.emitack("exchanges",None, ack)  

    socket.emitack("channels", "OK", ack)  
      


def onconnect(socket):
    logging.info("on connect got called")

def ondisconnect(socket):
    logging.info("on disconnect got called")

def onConnectError(socket, error):
    logging.info("On connect error got called")

def onSetAuthentication(socket, token):
    logging.info("Token received " + token)
    socket.setAuthtoken(token)

def onAuthentication(socket, isauthenticated):
    logging.info("Authenticated is " + str(isauthenticated))
    def ack(eventname, error, data):
        print ("token is "+ json.dumps(data, sort_keys=True))
        your_code_starts_here(socket);

    socket.emitack("auth", api_credentials, ack)

if __name__ == "__main__":
    socket = Socketcluster.socket("wss://sc-02.coinigy.com/socketcluster/")
    socket.setBasicListener(onconnect, ondisconnect, onConnectError)
    socket.setAuthenticationListener(onSetAuthentication, onAuthentication)
    socket.setreconnection(False)
    socket.connect()
