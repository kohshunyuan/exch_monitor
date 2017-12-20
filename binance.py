import copy
import hashlib
import hmac
import time
from urllib.parse import quote_plus

import requests

import secret

BASE_URL = 'https://api.binance.com'
VERSION = 3
REST_URL = '%s/api/v%s' % (BASE_URL, VERSION)


def rest(endpoint, params=''):
    if params and not params.startswith('?'):
        params = '?%s' % (params,)
    return '%s/%s%s' % (REST_URL, endpoint, params)


def _prep(endpoint, orig_req, signed):
    if not orig_req:
        orig_req = {}

    req = copy.deepcopy(orig_req)

    if signed:
        req['timestamp'] = int(time.time() * 1000)
        req['recvWindow'] = 5000

    params = '&'.join(['%s=%s' % (k, quote_plus(str(v))) for k, v in req.items()])

    if signed:
        signature = hmac.new(secret.BINANCE['API_SECRET'].encode(), params.encode(), hashlib.sha256).hexdigest()
        params = '%s&signature=%s' % (params, signature)
    url = rest(endpoint, params)

    headers = {
        'X-MBX-APIKEY': secret.BINANCE['API_KEY'],
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/4.0 (compatible; Python)'
    }

    print(url)
    return url, headers


def get(endpoint, orig_req, signed=False):
    url, headers = _prep(endpoint, orig_req, signed)
    r = requests.get(url, headers=headers)

    try:
        r.raise_for_status()
        j = r.json()
        if 'error' in j:
            raise Exception('Error in GET to Binance. message: %s' % (j['error'], ))
    except Exception as e:
            raise Exception('Binance connection failed when issuing command %s with req %s. message: %s' % (endpoint, req, e))
    return j
