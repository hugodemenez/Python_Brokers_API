<h1 align="center">Python_Brokers_API</h1>
<p align="center">This repository hosts the brain api used for my trading algorithms.</p> 

<div align="center">
  <strong>Simple functions to use crypto brokers with python 3 </strong>
</div>

<br />

<div align="center">
  <!-- license -->
  <a href="https://tldrlegal.com/license/mit-license">
    <img src="https://img.shields.io/badge/license-MIT-blue.svg"
      alt="license" />
  </a>
</div>

<br />

<div align="center">
  <sub>Built by
  <a href="https://github.com/hugodemenez">Hugo Demenez</a>
</div>

## Example
```python3

import Python_Brokers_API

broker=Python_Brokers_API.binance()

#Public data
print(
    broker.price(symbol="BTCEUR"),
    broker.get_klines_data(symbol="BTCEUR",interval="minute"),
    broker.get_24h_stats("BTCEUR"),
    )

#To create .key file
print(
  broker.create_key_file()
)

#To connect api
print(
    broker.connect_key("binance.key")
)

#To check the connection True = Ok, False = Error
print(
    broker.test_order()
)

#Private data
print(
    broker.account_information(),
    broker.get_open_orders(),
    broker.get_balances(),
    broker.create_market_order(symbol='BTCUSD',side='buy',quantity=1),
    broker.create_limit_order(symbol='BTCUSD',side='buy',quantity=1,price=10000),
    broker.create_take_profit_order(symbol='BTCUSD',side='buy',quantity=1,profitPrice=100000),
    broker.create_stop_loss_order(symbol='BTCUSD',side='buy',quantity=1,stopPrice=1000),
)

```
