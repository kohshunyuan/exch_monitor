"""
Monitor Idex for new historical trades and email

Args example:
    abc@gmail.com 720 0x..... 0x.....

References:
    https://github.com/AuroraDAO/idex-api-docs
"""

import argparse
from datetime import datetime

import broadcast
import common
import secret
import requests
from datetime import date, timedelta
from collections import namedtuple

Trade = namedtuple('Trade', ['address', 'tradeId', 'orderId', 'timestamp', 'symbol', 'direction', 'price', 'qty', 'estValue'])

def _parse_args():
    p = argparse.ArgumentParser(description='Monitor IDEX')
    p.add_argument('recipient', help='email recipient')
    p.add_argument('past_seconds', help='the number of seconds before of orders to check', type=int)
    p.add_argument('addresses', help='addresses to check', nargs='+')
    p.add_argument('--disable', '-d', help='disable running', action='store_true')
    return p.parse_args()



def _get_recent_history(address, past_seconds):
    dateToCheck = datetime.utcnow() - timedelta(seconds=past_seconds)
    r = requests.post(
        'https://api.idex.market/returnTradeHistory',
        json={'address': address, 'start': int(round(dateToCheck.timestamp()))}
    )
    r.raise_for_status()
    j = r.json()
    print(j)
    # {
    #     "ETH_FND": [
    #         {
    #             "date": "2018-05-17 16:42:26",
    #             "amount": "1924",
    #             "type": "sell",
    #             "total": "0.700336",
    #             "price": "0.000364",
    #             "orderHash": "0xc0becaf2cccab0619f5f3e093b12bb3b7b9d5f939ab882f958f7abba642474f0",
    #             "uuid": "48303770-59f1-11e8-8e87-0be4c258aaef",
    #             "buyerFee": "3.848",
    #             "sellerFee": "0.000700336",
    #             "gasFee": "7.939560439560438572",
    #             "timestamp": 1526575346,
    #             "maker": "0x480a93081ce13050b7a89ca5bb315b87e36905de",
    #             "taker": "0xa809d1f8df18c5355eb5a972cf70e29202769135",
    #             "transactionHash": "0x722fc88665840b2dceee0f10f2ecad52101de7afc87edd0cdfdd5b2b208c6e77"
    #         }
    #     ],
    #     "ETH_REN": [
    #             {
    #                 "date": "2018-05-17 12:33:32",
    #                 "amount": "6737.253938212438268165",
    #                 "type": "buy",
    #                 "total": "1.158807609999999999",
    #                 "price": "0.00017199999",
    #                 "orderHash": "0x2c30ed73f9d1364ff2bec4dd397bc2751c79dbc13503f3379f15b1d8f5008352",
    #                 "uuid": "82a55b10-59ce-11e8-8e87-0be4c258aaef",
    #                 "buyerFee": "6.737253938212438268",
    #                 "sellerFee": "0.00231761522",
    #                 "gasFee": "0.002209999999999999",
    #                 "timestamp": 1526560412,
    #                 "maker": "0x480a93081ce13050b7a89ca5bb315b87e36905de",
    #                 "taker": "0x53cbbb5676d1075911ac4903e1c2107570cf912b",
    #                 "transactionHash": "0x86e5925ef50e9e78c9e598b7038104aabebb8e7f6da7a77d680e8de3c0598948"
    #             },
    # }
    #     ]
    # }

    historical_trades = []
    for market, trades in j.items():
        for trade in trades:
            address = '%s...%s' % (address[:5], address[-5:])
            tradeId = '%s...%s' % (trade['transactionHash'][:5], trade['transactionHash'][-5:])
            orderId = '%s...%s' % (trade['orderHash'][:5], trade['orderHash'][-5:])
            historical_trades.append(
                Trade(
                    address,
                    tradeId,
                    orderId,
                    trade['timestamp'],
                    market,
                    trade['type'].title(),
                    trade['price'],
                    trade['amount'],
                    trade['total']
                )
            )

    return historical_trades


def _display(historical_trades):
    def row(contents):
        return '<tr>%s</tr>' % (contents,)

    def col(contents, bold=False):
        return '<td align="left">%s%s%s</td>' % ('<b>' if bold else '', contents, '</b>' if bold else '')

    def colb(contents):
        return col(contents, bold=True)

    body = '<html>Yay, %d trade(s) found!<br><br><table border = "1">' % (len(historical_trades),)
    body += row(colb('Address')+colb('TradeId')+colb('OrderId')+colb('Timestamp')+colb('Symbol')+colb('Direction')+colb('Price')+colb('Qty')+colb('Est. Value'))
    for t in historical_trades:
        timestamp = datetime.fromtimestamp(t.timestamp).strftime(common.DATE_FORMAT_TZ)
        body += row(col(t.address)+col(t.tradeId)+col(t.orderId)+col(timestamp)+col(t.symbol)+col(t.direction)+col(t.price)+col(t.qty)+col(t.estValue))

    body += "</table><br></html>"
    return body


def _run(args):
    print('running...')
    try:
        historical_trades = []

        # for symbol in args.symbols:
        for address in args.addresses:
            historical_trades.extend(_get_recent_history(address, args.past_seconds))
        historical_trades.sort(key=lambda t: t.timestamp)
        print(historical_trades)

        if historical_trades:
            broadcast.email('IDEX Trade Monitoring', _display(historical_trades), to=args.recipient)
        else:
            print('no trades found')
            if datetime.now().minute//10 == 3:
                broadcast.email('IDEX Trade Monitoring: Heartbeat', 'This is to let you know I am not slacking', to=args.recipient)
    except Exception as e:
        broadcast.email('IDEX Trade Monitoring: Exception!!', str(e), to=args.recipient)
        raise

    print('running... done')


def _sanity():
    # check required env vars are there
    if not secret.EMAIL['USERNAME'] or not secret.EMAIL['PASSWORD']:
        raise Exception('Email details not complete')


def main():
    args = _parse_args()
    print(args)

    if args.disable:
        raise Exception('Nothing done. Disabled -d flag passed in.')

    _sanity()
    _run(args)
    print('Done!')


if __name__ == '__main__':
    main()