import datetime
import json
import prometheus_client
import requests
import time


_LAST_TS_METRIC = prometheus_client.Gauge('last_hashrate_timestamp_ms',
    'The last reported timestamp in ms associated with a data point.')

_HASHRATE_METRIC = prometheus_client.Gauge('hashrate',
    'The last reported hashrate.')


class AlpereumProber(object):

    def __init__(self, account):
        self._stats_url = 'https://eiger.alpereum.net/api/miner_stats?address='
        self._account = account

    def GetLatestHashrate(self):
        r = requests.get(self._stats_url + self._account)
        max_ts = 0
        for row in r.json():
           current_ts = row['time']
           if current_ts > max_ts:
               max_ts = current_ts
               hashrate = row['submittedHashrate']
        return hashrate, max_ts
              
    
def _Main():
    # GEt these from flags.
    poll_interval_seconds = 60
    port = 8000
    account = '0xf493999e090f3a1001d782326847742a1fa84c2c'

    prober = AlpereumProber(account)
    # Start up the server to expose the metrics.
    prometheus_client.start_http_server(port)

    while True:
	hashrate, last_ts = prober.GetLatestHashrate()
        print hashrate, datetime.datetime.fromtimestamp(
            last_ts/1000).strftime('%Y-%m-%d %H:%M:%S')
        _HASHRATE_METRIC.set(hashrate)
        _LAST_TS_METRIC.set(last_ts)
	time.sleep(poll_interval_seconds)


if __name__ == '__main__':
    _Main()

