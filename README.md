# prometheus-tankutility-exporter

A prometheus exporter that accesses the tankutility.com API.

I've had a couple of glitches with battery level reporting and
reporting of loss of contact, so I want to get the data into
my own monitoring system.

## Installation

Make sure the python prometheus client library is available:
```
pip3 install prometheus_client
```
and the python requests library:
```
pip3 install requests
```

Create a `~/.tank-utility-login` file with contents like

```
[login]
user=myuser@example.com
password=correct-horse-battery-staple
```

## Metrics

Label 'deviceId' is short device ID
Gauge 'tankutility_battery' is the battery status:
- 2 = normal
- 1 = warning
- 0 = critical
Gauge 'tankutility_reading' is the tank reading in %, with a timestamp supplied by tankutility
Gauge 'tankutility_temperature' is the temperature in F, with a timestamp supplied by tankutility
Gauge 'tankutility_capacity' is the tank capacity in gallons
Gauge 'tankutility_tank_info' is a place holder for labels for the address and name fields

