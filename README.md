Steps:
* Fork to your own repo
* Create Heroku account
* Create new Heroku app and connect to your forked repo
* Select Buildpack: Python
* Add required env vars to Heroku under Settings. You will need one called IS_SERVER: Y and a few others (see secret.py)
* Provision Heroku Scheduler add-on and edit the config to call the script and set the frequency. Eg: "python binance_monitor.py abc@gmail.com 720 ETHBTC KNCETH ZRXETH REQETH OMGETH ASTETH NEOETH"
* Wait until script has run. Check logs for failures.


