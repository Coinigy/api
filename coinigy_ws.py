"""
    A basic example of how to subscribe to channels in coinigy websocket api

    Coinigy's api is designed around SocketCluster (http://socketcluster.io/). Unfortunately at the moment there is
    no python implementation of it. However it is still using WebSocket protocol at its root so we can work around
    and build a barebone interface in python.

    This implementation is using AutoBahn Twisted and is a modified version of a script written by Jesper Nohr
    https://bitbucket.org/snippets/jespern/6rBz9

    NB:  in order to run this script please edit __API_KEY and __API_SECRET with your information
    NNB: note that after you have run one time a file coinigy.token will be created and used for subsequent
         authentication so your key and secret will no longer be necessary
"""
import argparse
from autobahn.twisted.websocket import WebSocketClientProtocol, \
    WebSocketClientFactory, connectWS
import json
import pandas as pd
import random
import sys
from twisted.python import log
from twisted.internet import reactor, ssl

pd.set_option('display.width', 200)
log.startLogging(sys.stdout)

# API information
_API_KEY = '<YOUR PUBLIC KEY HERE>'
_API_SECRET = '<YOUR SECRET HERE>'
_END_POINT = u"wss://sc-01.coinigy.com:443"


# Incomplete port of sc-format npm package, enough to get it working for me, though.
def convert_buffers_to_base64(obj, ancestors=None):
    if not ancestors:
        ancestors = []

    new_ancestors = ancestors.append(obj)

    if isinstance(obj, (list, tuple)):
        new_list = []

        for item in obj:
            new_list.append(convert_buffers_to_base64(item, new_ancestors))

        obj = new_list
    elif isinstance(obj, dict):
        for key, val in obj.items():
            obj[key] = convert_buffers_to_base64(val, new_ancestors)
    # elif isinstance(obj, str):
    #     # `Buffer`?
    #     obj = {
    #         'base64': True,
    #         'data': obj.encode('base64')
    #     }
    # TODO: `ArrayBuffer`

    return obj


def stringify(obj):
    bas64_obj = convert_buffers_to_base64(obj)
    return json.dumps(bas64_obj)


# The next 2 classes handle the publication of channel messages
class TradePublisher:
    def __init__(self, channel=None):
        self._channel = channel

    def publish(self, data):
        print ' '.join(['{k}={v}'.format(k=k, v=str(v)) for k, v in data.iteritems()])


class OrderPublisher:
    def __init__(self, channel=None):
        self._channel = channel

    def publish(self, data):
        print('[OrderPublisher][{}]'.format(self._channel))
        print(pd.DataFrame.from_records(data))

__CHANNEL_MANAGERS__ = dict(
    trade=TradePublisher,
    order=OrderPublisher
)


class AuthHandler(object):
    def __init__(self, path):
        self.path = path

        print("AuthHandler: {0}".format(self.path))

    def save(self, token):
        with open(self.path, 'w') as fp:
            fp.write(token)

    def load(self):
        with open(self.path, 'r') as fp:
            data = fp.read()

        return data


class CoinigyWSClient(WebSocketClientProtocol):
    """
    WebSocket-based protocol which can communicate with Coinigy's WS API
    """
    def __init__(self, *args, **kwargs):
        print("Init client protocol.")

        # every call to the server is assigned a unique id 'cid'
        # every ack from the server will be returned with a matching 'rid'
        self._cid = 0

        self._auth = AuthHandler('coinigy.token')

        # override to True to enable debugging
        self._debug = False

        # remembers all info regarding our payload, callbacks etc..
        self._requests = {}

        # indirection
        self._channel2rid = {}

        super(CoinigyWSClient, self).__init__(*args, **kwargs)

    @classmethod
    def subscriptions(cls):
        return dict()

    def call_id_gen(self):
        self._cid += 1

        return self._cid

    def emit_raw(self, event, data, callback=None, **extra_infos):
        """
            Main wrapper to send WS queries to server
        """
        # Make an event object and send it out
        cid = self.call_id_gen()
        event = dict(event=event, data=data, cid=cid)
        if self._debug:
            print("Sending: {0}".format(event))

        payload = stringify(event)
        self.sendMessage(payload)
        print("Sent: {0}".format(payload))

        # Keep reference of the request
        request = dict(_callback=callback, _event=event)
        request.update(extra_infos)
        self._requests[cid] = request

        return cid

    # WEBSOCKET API methods
    def onConnect(self, response):
        print("Server connected: {0}".format(response.peer))

    def onOpen(self):
        print("WebSocket connection open.")

        # Try and get a saved token.
        token = self._auth.load()
        if not token:
            token = "ux87psl{0}z8l".format(random.randint(1096, sys.maxint))

        self.emit_raw('#handshake', dict(authToken=token), self.handshake_callback)

    def onMessage(self, payload, is_binary):
        if self._debug:
            if is_binary:
                print("Binary message received: {0} bytes".format(len(payload)))
            else:
                print("Text message received: {0}".format(payload.decode('utf8')))

        # ping
        if payload == '1':
            return self.sendMessage("2")

        # elif payload == '#1':
        #    return self.sendMessage("#2")

        try:
            data = json.loads(payload.decode('utf8'))

            if 'rid' in data:
                call = self._requests[data['rid']]['_event']
                if self._debug:
                    print("In response to {}".format(call))
            elif 'cid' in data:
                self.handle_command(data)

            if self._debug:
                if len(payload.decode('utf8')) > 2048:
                    print("Ignoring payload of {0} bytes.".format(len(payload)))
                else:
                    from pprint import pprint
                    pprint(data)

            if 'rid' in data and data['rid'] in self._requests:
                cb = self._requests[data['rid']]['_callback']
                cb(data)

        except Exception, e:
            print("Text message received: {0}: {1}".format(payload.decode('utf8'), e))

    def onClose(self, was_clean, code, reason):
        print("WebSocket connection closed: {0} -- clean: {1}".format(reason, was_clean))

    # CALLBACKS
    def auth_callback(self, data):
        print("AUTH CALLBACK")

        # send a couple of queries
        # FIXME: not sure it's the right place or time to do that!
        self.emit_raw('channels', None, self.handle_channels)
        self.emit_raw('exchanges', None, self.handle_exchanges)

        print('performing subscription to {} channels'.format(len(self.subscriptions())))
        for channel_name, channel_type in self.subscriptions().iteritems():
            self.channel_subscribe(channel_name, channel_type)

    def handle_subscribe(self, data):
        print("SUBSCRIPTION CALLBACK")
        if 'rid' in data.keys():
            print("acked subscription to channel {0}".format(self._requests[data['rid']]['_event']['data']))

    def handle_exchanges(self, data):
        print("EXCHANGES CALLBACK")
        print(data)

    def handle_channels(self, data):
        print("CHANNEL CALLBACK")
        channels, _ = data.get('data')
        print("Got {0} channels.".format(len(channels)))
        print(pd.DataFrame.from_records(channels))

    def handshake_callback(self, data):
        print("HANDSHAKE CALLBACK")

        self.emit_raw('auth', dict(apiKey=_API_KEY, apiSecret=_API_SECRET), self.auth_callback)

    def handle_command(self, data):
        # Server told us to do something.
        event = data.get('event', '#unknownEvent')
        cid = data.get('cid')

        if event == '#setAuthToken':
            # Set/save auth token.
            token = data.get('data').get('token')
            self._auth.save(token)
        if event == '#publish':
            self.channel_publish(data['data'])
        else:
            print("Unhandled server event: {0}".format(event))

    # CHANNELS MANAGEMENT
    def channel_subscribe(self, channel, channel_type):
        chan_manager = __CHANNEL_MANAGERS__[channel_type](channel)
        cid = self.emit_raw(event='#subscribe',
                            data=channel,
                            callback=self.handle_subscribe,
                            channel_manager=chan_manager)
        if self._debug:
            print('[_subscribe] cid={cid} channel={channel}'.format(channel=channel, cid=cid))
        self._channel2rid[channel] = cid

    def channel_publish(self, data):
        if self._debug:
            print('PUBLISH CALLBACK')

        channel = data['channel']
        cid = self._channel2rid[channel]
        cdata = data['data']
        manager = self._requests[cid]['channel_manager']
        manager.publish(cdata)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--trades', help="trade channels, eg TRADE-OK--BTC--CNY", nargs='*', default=[])
    parser.add_argument('--orders', help="order channels, eg ORDER-OK--BTC--CNY", nargs='*', default=[])
    args = parser.parse_args()

    all_subs = dict()
    for channel in args.trades:
        all_subs[channel] = 'trade'

    for channel in args.orders:
        all_subs[channel] = 'order'

    def subscriptions(cls):
        return all_subs

    print args
    print 'SUBSCRIPTIONS: {}'.format(subscriptions('toto'))

    CoinigyWSClient.subscriptions = subscriptions

    factory = WebSocketClientFactory(_END_POINT)
    factory.protocol = CoinigyWSClient

    if factory.isSecure:
        contextFactory = ssl.ClientContextFactory()
    else:
        contextFactory = None

    print("Has SSL context factory: {}".format(contextFactory))

    connectWS(factory, contextFactory)
    reactor.run()