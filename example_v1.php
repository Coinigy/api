<?php 

class example_v1  {
    
    private $coinigy_api_key = '';   
    private $coinigy_api_secret = '';   
    private $endpoint = 'https://www.coinigy.com/api/v1/';
    
    function __construct()
    {
        parent::__construct();          
    }
    
    public function index()
    {
        unitTest();
    }		
   
    //common vars
    private $exchange_code ='EXCH';
    private $exchange_market ='LTC/BTC'; 
    private $auth_id=0;  
    
    //data vars
    private $start_time = '2015-02-01 14:00:00'; 
    private $end_time = ''; 
    
    //create alert var
    private $alert_price = "650";
    
    //balances var
    private $auth_ids = ''; //comma or underscore delimited
    
    //delete alert var
    private $delete_alert_id = 0;
        
    //add order vars
    private $order_auth_id = 1966;
    private $order_exch_id = 7;
    private $order_mkt_id = 125;     
    private $order_type_id = 1;
    private $price_type_id = 3;
    private $limit_price = 234.32;
    private $stop_price = .024;
    private $order_quantity = 0.00003920;
    
    //cancel order vars
    private $cancel_order_id = 2605;
    

    
    
        
    public function unitTest()
    {
        
        foreach(get_class_methods("example_v1") as $method)
        {
            $exclude[0] = "__construct";
            $exclude[1] = "index";
            $exclude[2] = "unitTest";
            $exclude[3] = "doWebRequest";
            $exclude[4] = "output_result";
            $exclude[5] = "get_instance";
            
            if(! in_array($method, $exclude))
            {
                echo($method);
                $this->$method();                
            }
        }
    }
    
    
    
    
    
    
    
    public function accounts()
    {
        $post_arr = array();
        $result = $this->doWebRequest('accounts', $post_arr);        
        $this->output_result($result);                  
    }
    
    
    
  
    
    
    
    
    
    public function activity()
    {
        $post_arr = array();
        $result = $this->doWebRequest('activity', $post_arr);        
        $this->output_result($result);                  
    }
    
    
    
    
    
    
  
    public function balances()
    {
        $post_arr = array();
        $post_arr["auth_ids"] = $this->auth_ids;  
        $post_arr["show_nils"] = $this->show_nils;
        
        $result = $this->doWebRequest('balances', $post_arr);        
        $this->output_result($result);                  
    }

    
    
    
    

    
    public function pushNotifications()
    {
        $post_arr = array();
        $result = $this->doWebRequest('pushNotifications', $post_arr);        
        $this->output_result($result);                  
    }
    
    
    
    
    
    
    
    
    
    
    public function user_orders()
    {
        $post_arr = array();
        $result = $this->doWebRequest('orders', $post_arr);        
        $this->output_result($result);                  
    }
    
    
    
   
    
    
    
    
    
    
    public function alerts()
    {
        $post_arr = array();
        $result = $this->doWebRequest('alerts', $post_arr);        
        $this->output_result($result);                  
    }
    
    
    
    
    
    
    
    
   
    public function exchanges()
    {
        $post_arr = array();
        $result = $this->doWebRequest('exchanges', $post_arr);        
        $this->output_result($result);                  
    }
    
    
    
    
    
    
    
  
 
    public function markets()
    {
        $post_arr = array();
        $post_arr["exchange_code"] = $this->exchange_code;  
        
        $result = $this->doWebRequest('markets', $post_arr);        
        $this->output_result($result);                  
    }
    
    
    
    
    
    
    
    
    
  
    public function history()
    {
        $post_arr = array();        
        $post_arr["exchange_code"] = $this->exchange_code;  
        $post_arr["exchange_market"] = $this->exchange_market;
        $post_arr["type"] = "history";
        
        
        $result = $this->doWebRequest('data', $post_arr);        
        $this->output_result($result);                  
    }
    
    
    
    
    
   
    public function asks()
    {
        $post_arr = array();
        $post_arr["exchange_code"] = $this->exchange_code;  
        $post_arr["exchange_market"] = $this->exchange_market;
        $post_arr["type"] = "asks";
        
        $result = $this->doWebRequest('data', $post_arr);        
        $this->output_result($result);                  
    }
    
    
    
    
    
    
    
  
    public function bids()
    {
        $post_arr = array();
        $post_arr["exchange_code"] = $this->exchange_code;  
        $post_arr["exchange_market"] = $this->exchange_market;
        $post_arr["type"] = "bids";
        
        $result = $this->doWebRequest('data', $post_arr);        
        $this->output_result($result);                  
    }
    
    
    
    
    
    
    
    
    
    
    
    
    //asks + bids + history
    public function data()
    {               
        $post_arr = array();
        $post_arr["exchange_code"] = $this->exchange_code;  
        $post_arr["exchange_market"] = $this->exchange_market;
        $post_arr["type"] = "all";
        
        $result = $this->doWebRequest('data', $post_arr);        
        $this->output_result($result);                  
    }
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    //asks + bids
    public function orders()
    {
        
        $post_arr = array();
        $post_arr["exchange_code"] = $this->exchange_code;  
        $post_arr["exchange_market"] = $this->exchange_market;
        $post_arr["type"] = "orders";
        
        $result = $this->doWebRequest('data', $post_arr);        
        
        $this->output_result($result);                  
    }
    
    
    
    
    
    
    
    public function newsFeed()
    {
        $post_arr = array();        
        
        $result = $this->doWebRequest('newsFeed', $post_arr);        
        $this->output_result($result);          
    }
    
    
    
    
        
    
    public function orderTypes()
    {
        $post_arr = array();
        $result = $this->doWebRequest('orderTypes', $post_arr);        
        $this->output_result($result);          
    }
    
    
    
    
    
    
    ////////////////////////////////////////////////////////////////////////////////////
    ////////////////////////////////////////////////////////////////////////////////////
    //////////////////////                      ////////////////////////////////////////
    /////////////            ACTION METHODS         ////////////////////////////////////
    /////////////////////                       ////////////////////////////////////////
    ////////////////////////////////////////////////////////////////////////////////////
    ////////////////////////////////////////////////////////////////////////////////////
    

    
    
    public function refreshBalance()
    {
        
        $post_arr = array();
        $post_arr["auth_id"] = $this->auth_id;  
        
        $result = $this->doWebRequest('refreshBalance', $post_arr);        
        $this->output_result($result);                  
    }
    
    
    
    
    
    

    
    
    
    

  
    
    
    
    
    
    
    
    
   
    
    public function addAlert()
    {
        $post_arr = array();
        $post_arr["exch_code"] = $this->exchange_code;  
        $post_arr["market_name"] = $this->exchange_market;      
        $post_arr["alert_price"] = $this->alert_price;      
        
        $result = $this->doWebRequest('addAlert', $post_arr);        
        $this->output_result($result);          
    }
    
    
    
    
    
    
    
    
    
    
    public function deleteAlert()
    {
        $post_arr = array();
        $post_arr["alert_id"] = $this->delete_alert_id;
        
        $result = $this->doWebRequest('deleteAlert', $post_arr);        
        $this->output_result($result);          
    }
    
    
    
    
    
       
    
    
    
    
    
    
    
    
    
    
    
    
    public function addOrder()
    {
        $post_arr = array();
        $post_arr["auth_id"] = $this->order_auth_id;
        $post_arr["exch_id"] = $this->order_exch_id;
        $post_arr["mkt_id"] = $this->order_mkt_id;     
        $post_arr["order_type_id"] = $this->order_type_id;     
        $post_arr["price_type_id"] = $this->price_type_id;
        $post_arr["limit_price"] =$this->limit_price;
        $post_arr["stop_price"] = $this->stop_price;           
        $post_arr["order_quantity"] = $this->order_quantity;           
        
        $result = $this->doWebRequest('addOrder', $post_arr);        
        $this->output_result($result);          
        
    }
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    public function cancelOrder()
    {    
        $post_arr = array();
        $post_arr["internal_order_id"] = $this->cancel_order_id;           
        
        $result = $this->doWebRequest('cancelOrder', $post_arr);        
        $this->output_result($result);          
        
    }
    
    

    
    
    public function doWebRequest($method, $post_arr)
    {
                        
        $url = $this->endpoint.$method;
        
        $headers = array('X-API-KEY: ' . $this->coinigy_api_key,
                         'X-API-SECRET: ' . $this->coinigy_api_secret);
            
        
        // our curl handle (initialize if required)
        static $ch = null;
        if (is_null($ch)) {
            $ch = curl_init();
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
            curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/4.0 (compatible; Coinigy App Client; '.php_uname('s').'; PHP/'.phpversion().')');
        }                
     
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $post_arr);
        curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, FALSE);

        $res = curl_exec($ch);                
       
        if ($res === false)  {
            echo "CURL Failed - Check URL";
            return false;
        }        
        
        $dec = json_decode($res);
        
        if (!$dec) {
            
            echo "Invalid JSON returned - Redirect to Login";
            return false;   
        }                
        
        return $dec;
        
    }
        
    
    
    
    
    
    
    
    
    public function output_result($result)
    {
        if($result && !$result->error) 
            echo($result);
        else
            echo $result->error; 
        
    }
	
}
