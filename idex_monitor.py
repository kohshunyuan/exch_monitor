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
    # "ETH_TRAC": [
    #     {
    #         "date": "2018-05-19 04:33:36",
    #         "amount": "426.363",
    #         "type": "buy",
    #         "total": "0.17226",
    #         "price": "0.000404021924979419",
    #         "orderHash": "0x6cbb17383d314bd0eb793e11469eee022b0fa261c137e4d7b2eb17d040b58016",
    #         "uuid": "cbd65280-5b1d-11e8-8e87-0be4c258aaef",
    #         "buyerFee": "0.852726",
    #         "sellerFee": "0.00017226",
    #         "gasFee": "5.890769418321142306",
    #         "timestamp": 1526704416,
    #         "maker": "0xafe248450ef168a21ace2d54fa7c2e3d10a53215",
    #         "taker": "0xd99ba122ab50b47b2e4fb6f5e205f2dd01c0586d",
    #         "transactionHash": "0xeb277a7a8b3d640479f327c34602ef8d6c02660f74e013bc1a0f1db0c351550d"
    #     },
    #     {
    #         "date": "2018-05-19 04:25:22",
    #         "amount": "346.721532102969989892",
    #         "type": "sell",
    #         "total": "0.137565121352511833",
    #         "price": "0.000396759672",
    #         "orderHash": "0x4b022929586e463679dce4951751d29e8d05bdd7aa9eb88927c1e59e897dd24a",
    #         "uuid": "a52ad620-5b1c-11e8-8e87-0be4c258aaef",
    #         "buyerFee": "0.34672153210296999",
    #         "sellerFee": "0.000275130242705024",
    #         "gasFee": "0.00238",
    #         "timestamp": 1526703922,
    #         "maker": "0xa871b9bc40d6a2c690ac948ba80b17f1a54f8248",
    #         "taker": "0x15f2fcea05350bc3bd2851566d19af6ed1f59081",
    #         "transactionHash": "0x64bec0f270acaa73c8941c4a6df4515db3ee682b5d838aec6beb8c05e3ee9321"
    #     },

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