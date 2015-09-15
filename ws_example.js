
var socketCluster = require('socketcluster-client');
var config = require("config.json");

var api_credentials =
{
    "apiKey"    : "api_key",
    "apiSecret" : "generate_at_coinigy_website"
}

var options = {
    hostname  : config.sc_host,    
    port      : config.sc_port
};


var SCsocket = socketCluster.connect(options);


SCsocket.on('connect', function (status) {
    
    console.log(status); 
    
    SCsocket.on('error', function (err) {
        console.log(err);
    });    
    

    SCsocket.emit("auth", api_credentials, function (err, token) {        
        
        if (!err && token) {            

            var scChannel = SCsocket.subscribe("ORDER-BTRX--LTC--BTC");
            
            scChannel.watch(function (data) {
                console.log(data);
            });    
            
            
            var scChannel = SCsocket.subscribe("ORDER-BTRX--LTC--BTC");
            
            scChannel.watch(function (data) {
                console.log(data);
            }); 
            
            SCsocket.emit("exchanges", null, function (err, data) {
                if (!err) {                  
                    console.log(data);
                }
            });
            
            
            SCsocket.emit("channels", "BTRX", function (err, data) {
                if (!err) {
                    console.log(data);
                }
            }); 
        }   
    });   
});

