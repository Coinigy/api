#!/usr/bin/env python

"""
    A basic example of how to subscribe to channels in coinigy websocket api

    Coinigy's api is designed around SocketCluster (http://socketcluster.io/). Unfortunately at the moment there is
    no python implementation of it. However it is still using WebSocket protocol at its root so we can work around
    and build a barebone interface in python.

    This implementation is using AutoBahn Twisted and is a modified version of a script written by Jesper Nohr
    https://bitbucket.org/snippets/jespern/6rBz9

    NB: note that after you have authenticated yourself once (with the --api argument) a file coinigy.token will be 
        created and used for subsequent authentication so your key and secret will no longer be necessary

    1) The configs can be provided in json form (see coinigy_ws_config.json)
        "api":              credentials for authentication
        "subscriptions"     trade/order channels one wishes to subscribe to
        "publishers"        output files for trade/order data, if not provided will default to stdout/log file

    2) If the log file is not provided as an input (--out) then it will default to stdout

    3) When launched a console mode allows to interact with the WebSocketClient protocol. Depending on the command
       one will get outputs either in the console if the method returns something, or some acks can appear in the log
       file

       examples:
        a) get the configuration provided
        >>> send config

        b) perform a new subscriptiopn
        >>> send subscribe TRADE-OK--BTC--CNY trade

        c) perform a unsubscription
        >>> send unsubscribe TRADE-OK--BTC--CNY

    4) Example launch
        ./coinigy_ws.py --out ws.log --config coinigy_ws_config.json


"""
import argparse
from autobahn.twisted.websocket import WebSocketClientProtocol, WebSocketClientFactory, connectWS
import csv
import json
import os
import pandas as pd
import random
import sys
from twisted.internet import reactor, ssl, stdio, defer
from twisted.python import log
from utils.console import Console


pd.set_option('display.width', 200)

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

    def __init__(self, cfg):
        self._file = None
        self._writer = None
        self.setup(cfg)

    def __del__(self):
        self._file.close()

    def setup(self, cfg):
        outfile = cfg.get('trade', None)
        if outfile is not None and os.path.exists(outfile):
            print("[TradePublisher] will publish in {}".format(outfile))
            self._file = open(outfile, 'a+')
            self._writer = csv.DictWriter(
                self._file,
                fieldnames=['time_local', 'market_history_id', 'exchange', 'label', 'type', 'price', 'quantity', 'total'])
        else:
            print("[TradePublisher] will publish in {}".format(outfile))

    def publish(self, channel, data):
        if self._writer is None:
            print ' '.join(['{k}={v}'.format(k=k, v=str(v)) for k, v in data.iteritems()])
        else:
            self._writer.writerow(data)


class OrderPublisher:
    def __init__(self, cfg):
        self._file = None
        self.setup(cfg)

    def setup(self, cfg):
        outfile = cfg.get('order', None)
        if outfile is not None and os.path.exists(outfile):
            print("[OrderPublisher] will publish in {}".format(outfile))
            self._file = open(outfile, 'a+')
        else:
            print("[OrderPublisher] will publish on stdout")

    def publish(self, channel, data):
        df = pd.DataFrame.from_records(data)
        if self._file is not None:
            df.to_csv(self._file)
        else:
            print('[OrderPublisher][{}]'.format(channel))
            print(df)


class AuthHandler(object):
    def __init__(self, path):
        self.path = path

        print("AuthHandler: {0}".format(self.path))

    def save(self, token):
        with open(self.path, 'w') as fp:
            fp.write(token)

    def load(self):
        if not os.path.exists(self.path):
            return None

        with open(self.path, 'r') as fp:
            data = fp.read()

        return data


class CoinigyWSClient(WebSocketClientProtocol):
    """
    WebSocket-based protocol which can communicate with Coinigy's WS API
    """
    def __init__(self, config, *args, **kwargs):
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

        #config
        self._config = config

        #channel managers
        publish_cfg = config.get('publishers', dict())
        self._publishers = dict(
            trade=TradePublisher(publish_cfg),
            order=OrderPublisher(publish_cfg)
        )

        super(CoinigyWSClient, self).__init__(*args, **kwargs)

    def __del__(self):
        print("garbage collect")

    def config(self):
        return self._config

    def subscriptions(self):
        return self.config().get('subscriptions', dict(trade=[], order=[]))

    def api(self):
        return self.config().get('api', dict(apiKey='', apiSecret=''))

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
        self.exchanges()
        self.channels()

        subs = self.subscriptions()
        for channel_type in self._publishers.keys():
            channels = subs.get(channel_type, [])
            print("[SUBSCRIBE] {type}: {channels}".format(type=channel_type, channels=channels))
            for channel_name in channels:
                self.subscribe(channel_name, channel_type)

    def handle_subscribe(self, data):
        print("SUBSCRIPTION CALLBACK")
        if 'rid' in data.keys():
            print("acked subscription to channel {0}".format(self._requests[data['rid']]['_event']['data']))

    def handle_unsubscribe(self, data):
        print("UNSUBSCRIBE CALLBACK")
        if 'rid' in data.keys():
            print("acked unsubscription to channel {}".format(self._requests[data['rid']]['_event']['data']))

    def handle_exchanges(self, data):
        print("EXCHANGES CALLBACK")
        edata, status = data['data']
        print(status)
        print(pd.DataFrame.from_records(edata))

    def handle_channels(self, data):
        print("CHANNEL CALLBACK")
        channels, _ = data.get('data')
        print("Got {0} channels.".format(len(channels)))
        print(pd.DataFrame.from_records(channels))

    def handshake_callback(self, data):
        print("HANDSHAKE CALLBACK")

        self.emit_raw('auth', self.api(), self.auth_callback)

    def handle_command(self, data):
        # Server told us to do something.
        event = data.get('event', '#unknownEvent')
        cid = data.get('cid')

        if event == '#setAuthToken':
            # Set/save auth token.
            token = data.get('data').get('token')
            self._auth.save(token)
        if event == '#publish':
            self.publish(data['data'])
        else:
            print("Unhandled server event: {0}".format(event))

    # CHANNELS MANAGEMENT
    def subscribe(self, channel, channel_type):
        chan_manager = self._publishers[channel_type]
        cid = self.emit_raw(event='#subscribe',
                            data=channel,
                            callback=self.handle_subscribe,
                            channel_manager=chan_manager)
        if self._debug:
            print('[_subscribe] cid={cid} channel={channel}'.format(channel=channel, cid=cid))
        self._channel2rid[channel] = cid

    def unsubscribe(self, channel):
        sub_id = self._channel2rid.get(channel, -1)
        if sub_id < 0:
            print("[unsubscribe error] could not find cid of subscription to {}".format(channel))
            return
        self.emit_raw(event='#unsubscribe',
                            data=channel,
                            callback=self.handle_unsubscribe,
                            sub_id=sub_id)

    def publish(self, data):
        if self._debug:
            print('PUBLISH CALLBACK')

        channel = data['channel']
        cid = self._channel2rid[channel]
        cdata = data['data']
        manager = self._requests[cid]['channel_manager']
        manager.publish(channel=channel, data=cdata)

    def exchanges(self):
        self.emit_raw('exchanges', None, self.handle_channels)

    def channels(self):
        self.emit_raw('channels', None, self.handle_exchanges)


# have user interface controller
class CoinigyWSClientFactory(WebSocketClientFactory):

    def __init__(self, addr, contr, config):
        self._instance = None
        self._controller = contr
        self._config = config

        super(CoinigyWSClientFactory, self).__init__(addr)

    def buildProtocol(self, *args, **kwargs):
        proto = CoinigyWSClient(config=self._config)
        proto.factory = self
        self._instance = proto
        self._controller.set_protocol(proto)
        return proto

    def instance(self):
        return self._instance


class Controller(Console):

    def __init__(self):
        print("[CREATE CONTROLLER]")
        self._protocol = None

    def __del__(self):
        print("[DELETE CONTROLLER]")

    def set_protocol(self, proto):
        print("set_protocol {}".format(type(proto)))
        self._protocol = proto

    def do_send(self, fn, *args, **kwargs):
        """send commands to the WebSocketClient"""
        d = defer.Deferred()
        d.addCallback(self.printResult)
        if self._protocol is not None:
            reactor.callLater(0, d.callback, getattr(self._protocol, fn)(*args, **kwargs))
            return d

    def do_protocol(self):
        """execute method from the WebSocketClient protocol"""
        self.printResult(type(self._protocol))

    def do_list(self):
        """list available methods from WebSocketClient protocol"""
        if self._protocol is not None:
            self.printResult('\n'.join([str(cmd) for cmd in dir(self._protocol)]))

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--out', help='output file', default='stdout')
    parser.add_argument('--mode', help='output mode', choices=['csv', 'std'])
    parser.add_argument('--api', help='api key/secret', nargs=2, metavar=('key', 'secret'))
    parser.add_argument('--trades', help='trade channels, eg TRADE-OK--BTC--CNY', nargs='*', default=None)
    parser.add_argument('--orders', help='order channels, eg ORDER-OK--BTC--CNY', nargs='*', default=None)
    parser.add_argument('--config', help='config file', default=None)

    args = parser.parse_args()
    output = args.out
    if output == 'stdout':
        log.startLogging(sys.stdout)
    else:
        log.startLogging(open(output, 'w+'))

    # read the config file if any and apply overrides to it as requested
    config_dict = dict()
    if args.config is not None and os.path.exists(args.config):
        with open(args.config) as config_file:
            config_dict.update(json.load(config_file))

    if args.api:
        config_dict['api'] = dict(apiKey=args.api[0], apiSecret=args.api[1])

    if args.trades is not None:
        config_dict.setdefault('subscriptions', dict())['trade'] = args.trades

    if args.orders is not None:
        config_dict.setdefault('subscriptions', dict())['order'] = args.orders

    print("[CONFIG] {}".format(config_dict))

    # ui
    controller = Controller()
    stdio.StandardIO(controller)

    factory = CoinigyWSClientFactory(_END_POINT, controller, config_dict)
    factory.protocol = CoinigyWSClient

    if factory.isSecure:
        contextFactory = ssl.ClientContextFactory()
    else:
        contextFactory = None

    print("Has SSL context factory: {}".format(contextFactory))

    connectWS(factory, contextFactory)
    reactor.run()
