#!/usr/bin/env python3
#
# This code uses the API described at
# http://apidocs.tankutility.com/
# to export propane tank metrics to prometheus.
#

import configparser

import json
import os
import requests
import time

from prometheus_client.core import GaugeMetricFamily, InfoMetricFamily, UntypedMetricFamily, REGISTRY, Timestamp
from prometheus_client import start_http_server, Counter, Histogram

h = Histogram(
    'tankutility_api_latency',
    'The amount of time parsing the tank utility API')
apirequests = Counter('tankutility_api_requests',
                      'The number of requests we have made to the API')
logins = Counter(
    'tankutility_api_logins',
    'The number of times we have logged into the API')
errors = Counter(
    'tankutility_api_errors',
    'The number of exceptions trying to use the API')


class TankUtilityApi(object):
    def __init__(self):
        self.creds = configparser.ConfigParser()
        self.creds.read(
            os.path.join(
                os.environ['HOME'],
                '.tank-utility-login'))
        self.token_ = None

    def login(self):
        # The Tank utility API says that a key is good for 24 hours.
        creds = self.creds
        # TODO: see if the token in self.creds is new enough
        r = requests.get(
            'https://data.tankutility.com/api/getToken',
            auth=(
                creds['login']['user'],
                creds['login']['password']))
        if r.status_code != 200:
            # Hope that any cached token is still good?
            return
        logins.inc()
        token = r.json()
        self.token_ = token.get('token')
        # TODO: store the token and the current time in self.creds

    def apiReq(self, path):
        if not self.token_:
            raise Exception('You need to get a token by logging in')
        r = requests.get(
            'https://data.tankutility.com/api/' +
            path +
            '?token=' +
            self.token_)
        if r.status_code != 200:
            return {}
        return r.json()

    @errors.count_exceptions()
    @h.time()
    def fetchTanks(self):
        apirequests.inc()
        self.login()
        result = {}
        devices = self.apiReq('devices')
        for device in devices['devices']:
            result[device] = self.apiReq('devices/' + device)['device']
        return result


def tankutility_scale(time):
    # The tankutility JSON returns the time in integer milliseconds.
    # Prometheus likes it in milliseconds, too, but we have to
    # scale it to float seconds, so that the Prometheus API can
    # scale it back.
    return time / 1000.0


class TankUtilityExporter(object):
    def __init__(self, api):
        self.api_ = api

    def collect(self):
        tankStatus = self.api_.fetchTanks()
        info = InfoMetricFamily('tankuility_tank', 'Tank Info', labels=['tankId'])
        capacity = GaugeMetricFamily(
            'tankuility_capacity',
            'Tank Capacity (gallons)',
            labels=['tankId'])
        reading = GaugeMetricFamily(
            'tankuility_reading',
            'Tank Level (percent)',
            labels=['tankId'])
        temperature = GaugeMetricFamily(
            'tankuility_temperature',
            'Temperature (Fahrenheit)',
            labels=['tankId'])
        battery = GaugeMetricFamily(
            'tankuility_battery',
            'Battery status (critical=0, warning=1, normal=2)',
            labels=['tankId'])
        for tank in tankStatus.values():
            tank_id = tank['short_device_id']
            info.add_metric(
                [tank_id], {
                    'name': tank['name'], 'address': tank['address']})
            capacity.add_metric([tank_id], tank['capacity'])
            reading.add_metric(
                [tank_id],
                tank['lastReading']['tank'],
                timestamp=tankutility_scale(
                    tank['lastReading']['time']))
            temperature.add_metric(
                [tank_id],
                tank['lastReading']['temperature'],
                timestamp=tankutility_scale(
                    tank['lastReading']['time']))
            battery.add_metric([tank_id], 0 if tank['battery_crit'] else
                               1 if tank['battery_warn'] else
                               2)
        yield info
        yield capacity
        yield reading
        yield temperature
        yield battery


def main():
    REGISTRY.register(TankUtilityExporter(TankUtilityApi()))
    start_http_server(2468)
    while True:
        # I guess the http server is in another thread?
        time.sleep(5)


main()
