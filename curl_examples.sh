#!/bin/bash

#list exchanges
curl -H "X-API-KEY:yourapikeyhere" -H "X-API-SECRET:yoursecrethere" -X POST "https://www.coinigy.com/api/v1/exchanges"

#post data in json format
curl -H "Content-Type: application/json" -H "X-API-KEY:yourapikeyhere" -H "X-API-SECRET:yoursecrethere" -X POST -d '{"exchange_code":"BTCC"}' "https://www.coinigy.com/api/v1/markets"

#post data as params
curl -H "X-API-KEY:yourapikeyhere" -H "X-API-SECRET:yoursecrethere" -X POST -d 'exchange_code=BTCC' "https://www.coinigy.com/api/v1/markets"

#post multiple parameter data
curl -H "X-API-KEY:yourapikeyhere" -H "X-API-SECRET:yoursecrethere" -X POST -d 'exch_code=BTCC&market_name=BTC/CNY&alert_price=6000.00&alert_note="time to buy the yacht"' "https://www.coinigy.com/api/v1/addAlert"

#post multiple parameter data in json format
curl -H "Content-Type: application/json" -H "X-API-KEY:yourapikeyhere" -H "X-API-SECRET:yoursecrethere" -X POST -d '{"exch_code":"BTCC","market_name":"BTC/CNY","alert_price":"6000.00","alert_note":"time to buy the yacht"}' "https://www.coinigy.com/api/v1/addAlert"
