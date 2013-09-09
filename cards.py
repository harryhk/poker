#!/usr/bin/env python
#
# Copyright 2009 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
"""Simplified chat demo for websockets.

Authentication, error handling, etc are left as an exercise for the reader :)
"""

import logging
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import os.path
import uuid
import game as Game
import time

from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)

game = Game.Game()


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/dealing", DealingHandler),
            (r"/login", LoginHandler),
            (r"/host", HostHandler),
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "template"),
            static_path=os.path.join(os.path.dirname(__file__),'static'),
            debug=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("login.html", player=game.idToName )

class LoginHandler(tornado.web.RequestHandler):
    def post(self):
        playerId = int( self.get_argument('playerId') ) 
        playerName = self.get_argument('playerName')

        game.addPlayer(playerId, playerName)
        self.render('shengji.html',  pid = playerId, pname = playerName)


class HostHandler(tornado.websocket.WebSocketHandler):
    Players = {}
    PlayerToIdx = {}

    def open(self):
        pass 

    def on_message(self, mesg):
        
        logging.info("got message %r", mesg)
        mesg = mesg.split(' ')
        
        if mesg[0] =='add':
            HostHandler.Players[ int(mesg[1]) ] = self
            HostHandler.PlayerToIdx[ self ] = int( mesg[1] )

        if mesg[0] == 'bidStyle':
            _card = Game.Card( int(mesg[1]) ,  game.hostNum )
            _playerId = HostHandler.PlayerToIdx[self] 
            _hostCardN = game.players[_playerId].count( _card )
            #print _hostCardN
            #if _hostCardN ==1 :
            #    cardsMesg={ "style": game.players[i][cardidx].s, "num": game.players[i][cardidx].n }
            #    HostHandler.updater(cardsMesg)

            cardsMesg={ "style": int(mesg[1]) , "num": game.hostNum }
            HostHandler.updater(cardsMesg)



    @classmethod
    def updater(cls, mesg):
        for i in cls.PlayerToIdx:
            i.write_message(mesg)
        
                

NUMPLAYER=1

class DealingHandler(tornado.websocket.WebSocketHandler):
    Players = {}
    ReadyIds = [0 , 0, 0, 0 ] 
    sendCard = 0 ;
    
    def open(self):
        #DealingHandler.players.add(self)
        pass

    def on_close(self):
        #DealingHandler.players.remove(self)
        pass

    def on_message(self, mesg):
        logging.info("got message %r", mesg)
        # message form:
        #  action playerid message
        mesg = mesg.split(' ') 
        idx = int( mesg[1] ) 
        
        # mesgToSend : mesg send to each client 
        # action: 0 : handling the cards
        #       : 1 : update host style and num 

        if mesg[0] == "ready":
            # mesg:  read id : tell server that player id is ready 
            #                : when all players are ready, server sends cards 
            DealingHandler.Players[idx] = self
            DealingHandler.ReadyIds[idx] = 1
        
            # check if every one is ready 
            if reduce(lambda x,y : x+y, DealingHandler.ReadyIds) != NUMPLAYER:  
                return 
                
            game.shuffle()
            
            for i in range(NUMPLAYER):
                _style = ' '.join( map( str, [ _.s for _ in game.players[i] ] ) )
                _num = ' '.join( map( str, [ _.n for _ in game.players[i] ]  )  )
                #print _num
                #print _style
                mesgToSend={ 'action': 0,   "style": _style,  "num": _num }
                DealingHandler.Players[i].write_message(mesgToSend)
            
            return 

        if mesg[0] == 'bid':
            # mesg : bid id style: tell server player id is bit style for host  
            #      : style : 0- 4 
            _style = int( mesg[2]  )
            if game.hostRank == 0:
                if game.playerBid(idx, _style):
                    # if player idx bit succeed 
                    # update the host among players
                    
                    mesgToSend={ 'action': 1, 'hostId': idx, "style": _style , 'num' : game.hostNum   }
                    for i in range(NUMPLAYER):
                        DealingHandler.Players[i].write_message(mesgToSend)

                    # no longer accept biding 
                    game.hostRank =1 
            
            return 

        if mesg[0] == 'handle':
            # mesg: handle id ( style, num ) , ( style,  num ), ....
            # check if handle is valid for player id 
            # if valid, send confirmation and the next player id 
            
            nextPlayer, roundEnd =  game.oneRound( idx, mesg[2:]  )  
            if nextPlayer == -1:
                # not a valid hand, send back to player idx and re-select cards
                mesgToSend = { 'action' : 2 , 'valid' : 0    }
                DealingHandler.Players[idx].write_message( mesgToSend)
            
            else:
                
                mesgToSend = { 'action' : 2 , 'valid' : 1 , 'nextId': nextPlayer , 'roundEnd' : roundEnd }
                # roundEnd : 0  ; still same round 
                # roundEnd : 1  ; ne
                for i in range(NUMPLAYER):
                    DealingHandler.Players[i].write_message(mesgToSend)

            
           
            return  





#class ChatSocketHandler(tornado.websocket.WebSocketHandler):
#    waiters = set()
#    cache = []
#    cache_size = 200
#
#    def allow_draft76(self):
#        # for iOS 5.0 Safari
#        return True
#
#    def open(self):
#        ChatSocketHandler.waiters.add(self)
#
#    def on_close(self):
#        ChatSocketHandler.waiters.remove(self)
#
#    @classmethod
#    def update_cache(cls, chat):
#        cls.cache.append(chat)
#        if len(cls.cache) > cls.cache_size:
#            cls.cache = cls.cache[-cls.cache_size:]
#
#    @classmethod
#    def send_updates(cls, chat):
#        logging.info("sending message to %d waiters", len(cls.waiters))
#        for waiter in cls.waiters:
#            try:
#                waiter.write_message(chat)
#            except:
#                logging.error("Error sending message", exc_info=True)
#
#    def on_message(self, message):
#        logging.info("got message %r", message)
#        parsed = tornado.escape.json_decode(message)
#        chat = {
#            "id": str(uuid.uuid4()),
#            "body": parsed["body"],
#            }
#        chat["html"] = tornado.escape.to_basestring(
#            self.render_string("message.html", message=chat))
#
#        ChatSocketHandler.update_cache(chat)
#        ChatSocketHandler.send_updates(chat)


def main():
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()

