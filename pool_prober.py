import collections
import datetime
import json
import prometheus_client
import requests
import time

_MinerStats = collections.namedtuple('_MinerStats', [
    'time',
    'hashrate',
    'stale_hashrate',
    'submitted_hashrate',
    'avgdiff',
    'avgsharetime'])

_LAST_TS_METRIC = prometheus_client.Gauge('last_hashrate_timestamp_ms',
    'The last reported timestamp in ms associated with a data point.',
    ['worker'])

_HASHRATE_METRIC = prometheus_client.Gauge('hashrate',
    'The last reported hashrate.', ['worker'])

_STALE_HASHRATE_METRIC = prometheus_client.Gauge('stale_hashrate',
    'Total stale hashes for the rig.', ['worker'])

_SUBMITTED_HASHRATE_METRIC = prometheus_client.Gauge('submitted_hashrate',
    'The last measured hashrate.', ['worker'])

_AVG_SHARE_TIME_METRIC = prometheus_client.Gauge('avg_share_time',
    'Time since last submitted share in seconds.', ['worker'])

_AVG_DIFF_METRIC = prometheus_client.Gauge('avg_difficulty',
    'Difficulty for the rig. Will varry if mining on a port using VarDif.',
    ['worker'])

class AlpereumProber(object):

    def __init__(self, account):
        self._stats_url = 'https://eiger.alpereum.net/api/miner_stats?address='
        self._account = account

    def GetLatestWorkerHashrate(self, worker):
        r = requests.get('%s%s.%s' % (self._stats_url, self._account, worker))
        max_ts = 0
        for row in r.json():
           current_ts = row['time']
           if current_ts > max_ts:
               max_ts = current_ts
               latest = row
        return _MinerStats(
            time=latest['time'],
            submitted_hashrate=latest['submittedHashrate'],
            hashrate=latest['hashrate'],
            avgdiff=latest['avgdiff'],
            avgsharetime=latest['avgsharetime'],
            stale_hashrate=latest['staleHashrate'])
         
    def GetLatestHashrate(self):
        r = requests.get(self._stats_url + self._account)
        max_ts = 0
        for row in r.json():
           current_ts = row['time']
           if current_ts > max_ts:
               max_ts = current_ts
               hashrate = row['submittedHashrate']
        return _MinerStats(submittedHashrate=hashrate, time=max_ts)
              
    
def _Main():
    # GEt these from flags.
    poll_interval_seconds = 60
    port = 8000
    account = '0xf493999e090f3a1001d782326847742a1fa84c2c'
    worker = '2d1c01'

    prober = AlpereumProber(account)
    # Start up the server to expose the metrics.
    prometheus_client.start_http_server(port)

    while True:
	stats = prober.GetLatestWorkerHashrate(worker)
        print stats, datetime.datetime.fromtimestamp(
            stats.time/1000).strftime('%Y-%m-%d %H:%M:%S')
        _HASHRATE_METRIC.labels(worker).set(stats.hashrate)
        _SUBMITTED_HASHRATE_METRIC.labels(worker).set(stats.submitted_hashrate)
        _STALE_HASHRATE_METRIC.labels(worker).set(stats.stale_hashrate)
        _AVG_SHARE_TIME_METRIC.labels(worker).set(stats.avgsharetime)
        _AVG_DIFF_METRIC.labels(worker).set(stats.avgdiff)
        _LAST_TS_METRIC.labels(worker).set(stats.time)
	time.sleep(poll_interval_seconds)


if __name__ == '__main__':
    _Main()

