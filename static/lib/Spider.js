/**
  *	
  * @ Kun Huang  
  *  
  */

function Spider(pid) {
	this.cntr = $("#main");
	this.scoreElem = $("#score");
	this.stepElem = $("#step");
    this.poker = $('#poker');
    this.host = $('#host');
    
	this.paddingTop = 10;
    this.pid = pid;
    this.D = null;
    //this.H = null;
	this.init();
}
Spider.prototype={
    init: function(){
        var S = this; 

        
        S.collection=[]; // collection of cards 
        S.D = new Dealing(S);
        //S.H = new Hosting(S);
        /*
         * Use mode to indicate different cards 
         * 54 * 2 cards 
         * style : 0: spades, 1: hearts, 2: clubs, 3: diamonds, 4: kings 
         * num : 0-12: A234-K
         *       style==4, 0: back, 1: small joker, 2: big joker, 3: holder
         */
        
    },

    start: function(){
        var S = this; 
        //alert(location.host);
        var D = S.D;
        D.socket.send("ready "+ D.S.pid);

        var H = S.H;  
    },

    //clear: function(){
    //    var S = this; 
    //    S.poker.html('');
    //    S.collection = [];
    //},

    bidHost: function(style){
        var S = this;
        S.D.socket.send('bid '+ S.pid + ' ' +  style);
    },

    submit: function(){
        // submit selected cards to the server  
        var S = this; 
        var i , _poker; 
        var max = S.collection.length;
        var mesgString = 'handle ' + S.pid + ' ';

        for(i= 0 ; i<max; i++){
            _poker = S.collection[i];
            if(_poker.selected == 1 ){
                // if the card is selected, we append the style and num of the card to the message string 
                // should use JASON , But I do it for simplicity 

                mesgString += ( _poker.mode.style + ' ' + _poker.mode.num ); 
            }
        }
        S.D.socket.send( mesgString );
        
    },

};

function Hosting(S){
    this.S = S;
    this.socket = null;
    this.init();
}

Hosting.prototype={
    init: function(){
        var url = 'ws://' + location.host + '/host';
        var H = this;
        H.socket = new WebSocket(url);
        H.socket.onmessage = function(event){
            H.updateHost( JSON.parse(event.data));
        };
        H.socket.onopen = function(){
            H.socket.send('add '+ H.S.pid)
        };
    },

    updateHost: function(mesg){
        var S = this.S;
        var styleAll = mesg.style.split(' ');
        var numAll = mesg.num.split(' ');
        alert(mesg.style);
        var i, _poker;
        var myHost = [];
        S.host.html('');

        for(i = 0 ; i< styleAll.length ; i++ ){
            _poker = new Poker(S, {'style': styleAll[i], 'num': numAll[i]  } );
            _poker.elem.css({"top": "90px", "left": i*22+90 + 'px'});
            S.host.append(_poker.elem);
        }
        
    }
}

function Dealing(S){
    this.S = S;
    this.socket = null; 
    this.init();
    this.sendOne = [];  // this is an array of callback functions that is called every 5 s to send out one card. 
}

Dealing.prototype= {
    init: function(){
        var url = "ws://" + location.host + '/dealing';
        //var url = "ws://" + '192.168.1.105:8888' + '/dealing';
        var D = this ; 
        D.socket = new WebSocket(url);
        D.socket.onmessage = function(event){
            var mesg = JSON.parse(event.data) ; 
            if(mesg.action == 0){
                D.receiveCards( mesg );
            }
            if(mesg.action == 1){
                D.updateHost(mesg);    
            }
        };
        D.socket.onopen = function(){
            //alert("socket open" + D.S.pid);
            //D.socket.send("ready "+ D.S.pid);
            //alert("socket open");
        };
    },
    receiveCards: function(mesg){
        var D = this;
        var S = D.S;
        
        var styleAll = mesg.style.split(' ');
        var numAll = mesg.num.split(' ');
        
        var i, j,   _poker, max;
        
        // call back function which is called every 5 s. 
        // have to do this way due to javascript scope . 
        function sendOne(i, style, num) {
            return function(){
                _poker = new Poker(S, {"style": style, 'num': num} );
                
                _poker.elem.css({"top": "390px", "left": i*22+90 + 'px'});
                S.poker.append(_poker.elem);

                S.collection.push( _poker );
                
                S.collection.sort( pokerSort ); 
                
                var _top = parseInt(_poker.elem.css("top"));
                for( var j= 0; j<=i ; j += 1 ) {

                    S.collection[j].moveTo( j*22 + 90 , _top, j , 0 ); 
                }
            };
        }

        for( i = 0, max= styleAll.length; i< max;  i += 1){
            D.sendOne[i] = sendOne(i, styleAll[i], numAll[i] );
        }
        
        for( i = 0, max= styleAll.length; i< max;  i += 1){
            window.setTimeout(  D.sendOne[i]  , 500 *i ); 
        }

    },
    
    updateHost: function(mesg) {
        var S = this.S;
        // so far only single host can be bid 
        var style = mesg.style ; //.split(' ');
        var num = mesg.num ; //.split(' ');
        
        var i, max, _poker;
        
        S.host.html('');

        i=0;
        _poker = new Poker(S, {'style': style, 'num': num  } );
        // remove listener 
        _poker.elem.unbind();
        _poker.elem.css({"top": "100px", "left": i*22+10 + 'px' });
        S.host.append(_poker.elem);
        // once bid succeed, disable all biding forms. 
        $('#bidHost :input').attr('disabled', true);
        // if client player is the host , enable the submit button
        
        if(mesg.hostId == S.pid  ){
            console.log(mesg.hostId, S.pid);
            $('#subBtn').attr('disabled', false);
            $('#whosTurn').find('span').text(S.pid);
        }
    },
}


function Poker(S, mode){
    this.S= S;
    this.width = 105; 
    this.height = 148; 
    this.mode = mode; 
    this.selected= 0 ;
    this.init();
}

Poker.prototype = {
    init: function(){
        this.render();
        this.listener();
    },

    render: function(){
        var P = this;
        var S = P.S; 
        P.elem =  $("<div class='poker'></div>"); // create a poker 
        var _css ={};
        _css["background-position"] = (-(P.width*P.mode.num))+"px "+(-(P.height*P.mode.style))+"px";
        P.elem.css(_css);
    },
    
    moveTo: function(x, y, z, delay) {
        var P = this;
        P.elem.animate({"left": x+"px", "top": y+"px", 'z-index': z}, 10);
        //P.elem.delay(delay).animate({"left": x+"px", "top": y+"px", 'z-index': z}, "fast");
    },


    listener: function(){
        var P = this ; 
        var S = P.S; 

        P.elem.bind("click", function(){
            var _top = parseInt(P.elem.css("top"));
            if(P.selected == 0){
                P.elem.css({"top": _top- 20 +'px'});
                P.selected = 1; 
            }else{
                P.elem.css({"top": _top+ 20 +'px'});
                P.selected = 0; 
            }
                
        });
    }
        
};

function pokerSort(p1, p2){
    if(p1.mode.style != p2.mode.style){
        return p1.mode.style - p2.mode.style;
    }else{
        return p1.mode.num - p2.mode.num;
    }
}
