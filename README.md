check_liebert_ups
=================
Use with Liebert NXR-UPS. Tested on our 30kVA UPS type. No MIB needed.

I only active alert and perf data on UPS Battery temperature, Output load, System status. If anyone need more alert and more perf data, feel free to edit the script and adjust features, have guide inside.

-------------------------------------------------
Options:
-h, --help show this help message and exit
-H HOST, --host=HOST hostname or IP address
-c COMMUNITY SNMP community
-t TYPE, --type=TYPE BATTERY VOLTAGE, BATTERY CURRENT, BATTERY STATUS,
SYSTEM STATUS, INPUT, OUTPUT
-m MODULE, --module=MODULE
module to check
-a RANGE, --range=RANGE
normal range, when something out of scope alert will
be raised. Ex: -a 0,80
