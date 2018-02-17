# modbus-tcp2mqtt
Simple MQTT publishing of Modbus TCP sources. (C) 2018 Lubomir Kamensky lubomir.kamensky@gmail.com

Dependencies
------------
* pyModbusTCP - https://github.com/sourceperl/pyModbusTCP

* Eclipse Paho for Python - http://www.eclipse.org/paho/clients/python/

Example use
-----------
python3 modbus-tcp2mqtt.py --mqtt-topic futura --modbus-host 192.168.88.201 --registers futura.ini

Example use pm2 usage
---------------------
pm2 start /usr/bin/python3 --name "modbus-tcp2mqtt-futura" -- /home/luba/Git/modbus-tcp2mqtt/modbus-tcp2mqtt.py --mqtt-topic futura --modbus-host 192.168.88.201 --registers futura.ini

pm2 save
