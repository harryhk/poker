#!/usr/bin/env python 

import random 

class Card:
    
    def __init__(self, style, num):
        #  style = 0: spade , 1: hearts , 2: club, 3: diamonds 4: joker
        #  num = 0-12: A23-K, 
        #  style==4, 0: back, 1: small joker, 2: big joker, 3: holder
        self.s = style
        self.n = num

    def __str__(self):
        return "(s: %d, n: %d)" % (self.s, self.n)




class Game:
    
    def __init__(self):
        self.players={}  # player id to player
        self.nameToId={}  # player name to id 
        
        self.hostNum= 1  # current host card number 
        self.hostRank= 0  # 

        self.hostPlayer = -1; 
        self.roundStart = -1 ; 
        
        self.idToName = ['' for _ in range(4) ] 

        # create two decks of cards 
        self.twoDecks= [  Card(i, j ) for _ in range(2) for i in range(4) for j in range(13)  ]
        self.twoDecks.extend(  [  Card(4, j ) for _ in range(2) for j in [1,2]  ] )

        

    def addPlayer(self, idx,  name ):
        self.players[idx] = None 
        self.nameToId[name] = idx
        self.idToName[idx] = name 

    def shuffle(self):
        random.shuffle(self.twoDecks)
        
        # send cards to players
        for i in range(4):
            self.players[i] = self.twoDecks[i*25 : (i+1)*25]

    def playerBid(self, idx, style):
        # player idx is bid for style 
        # return bool to check if bidding is valid : 
        # 1. check if player idx has the card 
        # 2. if valid, update game host to player idx 
        self.hostPlayer = idx 
        self.roundStart = idx 

        return True

    
            

if __name__ == '__main__':
    g= Game()
    g.shuffle()
    for i in g.players[0]:
        print i
        
        
