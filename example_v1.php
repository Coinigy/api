<?php 


/*USAGE: 
 *   
 * 
 * 
   $coinigy_api = new coinigy_api_example_v1();
   $coinigy_api->exchanges();
   $coinigy_api->markets('OK');
 * 
 * 
 * 
*/




class coinigy_api_example_v1  {
    
    //private class vars set in constructor
    //see API docs for more info
    private $coinigy_api_key;   
    private $coinigy_api_secret;   
    private $endpoint;
    
    
    function __construct()
    {
        //see API docs for more info
        $this->coinigy_api_key = '';
        $this->coinigy_api_secret = '';
        $this->endpoint = 'https://www.coinigy.com/api/v1/'; //with trailing slash
    }
    
    

    
    
    
    
    
    public function exchanges()
    {
        $post_arr = array();
        $result = $this->doWebRequest('exchanges', $post_arr);        
        $this->output_result($result);                  
    }
    
    
    
    
    
    
    
    
    
    public function markets($exchange_code)
    {
        $post_arr = array();
        $post_arr["exchange_code"] = $exchange_code;  
        
        $result = $this->doWebRequest('markets', $post_arr);        
        $this->output_result($result);                  
    }
    
    

    
    
    
    
    private function doWebRequest($method, $post_arr)
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
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, TRUE);
        $res = curl_exec($ch);                
        
        if ($res === false)  {
            echo "CURL Failed - Check URL";
            return false;
        }        
      
        $dec = json_decode($res);
        
        if (!$dec) {
            
            echo "Invalid JSON returned";
            return false;   
        }                
        
        return $dec;        
    }
    
    
    
    
    
    
    
    
    
    private function output_result($result)
    {        
        if($result)
        {
            if(isset($result->error))
                var_dump($result->error);
            elseif(isset($result))
                var_dump($result);
        }
    }   
    	
}
