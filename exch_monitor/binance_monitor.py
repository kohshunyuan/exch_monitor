"""
Monitor Binance for new historical trades and email

Note: Binance doesn't allow checking for all symbols so have to pass in a list to check

Args example:
    abc@gmail.com 720 ETHBTC KNCETH ZRXETH REQETH OMGETH ASTETH

References:
    https://www.binance.com/restapipub.html
    https://github.com/sammchardy/python-binance/blob/master/binance/client.py
    https://github.com/binance-exchange/node-binance-api/blob/master/node-binance-api.js
"""

import argparse
from datetime import datetime

import binance
import broadcast
import common
import secret


def _parse_args():
    p = argparse.ArgumentParser(description='Monitor Binance')
    p.add_argument('recipient', help='email recipient')
    p.add_argument('past_seconds', help='the number of seconds before of orders to check', type=int)
    p.add_argument('symbols', help='symbols to check', nargs='+')
    p.add_argument('--disable', '-d', help='disable running', action='store_true')
    return p.parse_args()


def _get_recent_history(symbol, past_seconds):
    trades = binance.get('myTrades', {'symbol': symbol, 'limit': 30})
    print(trades)
    trades = [t for t in trades if t['time'] >= int(datetime.now().timestamp() * 1000) - past_seconds*1000]
    for t in trades:
        t['symbol'] = symbol

    return trades


def _display(historical_trades):
    def row(contents):
        return '<tr>%s</tr>' % (contents,)

    def col(contents, bold=False):
        return '<td align="left">%s%s%s</td>' % ('<b>' if bold else '', contents, '</b>' if bold else '')

    def colb(contents):
        return col(contents, bold=True)

    body = '<html>%d trade(s) found!<br><br><table border = "1">' % (len(historical_trades),)
    body += row(colb('TradeId')+colb('OrderId')+colb('Timestamp')+colb('Symbol')+colb('Direction')+colb('Price')+colb('Qty')+colb('Est. Value'))
    for t in historical_trades:
        timestamp = datetime.fromtimestamp(t['time']/1000).strftime(common.DATE_FORMAT_TZ)
        value = float(t['price'])*float(t['qty'])
        direction = 'Buy' if t['isBuyer'] else 'Sell'
        body += row(col(t['id'])+col(t['orderId'])+col(timestamp)+col(t['symbol'])+col(direction)+col(t['price'])+col(t['qty'])+col(value))

    body += "</table><br></html>"
    return body


def _run(args):
    print('running...')
    try:
        historical_trades = []
        for symbol in args.symbols:
            historical_trades.extend(_get_recent_history(symbol, args.past_seconds))
        historical_trades.sort(key=lambda t: t['time'])
        print(historical_trades)

        if historical_trades:
            broadcast.email('Binance Trade Monitoring', _display(historical_trades), to=args.recipient)
        else:
            print('no trades found')
            if datetime.now().minute//10 == 3:
                broadcast.email('Binance Trade Monitoring: Heartbeat', 'This is to let you know I am not slacking', to=args.recipient)
    except Exception as e:
        broadcast.email('Binance Trade Monitoring: Exception!!', str(e), to=args.recipient)
        raise

    print('running... done')


def _sanity():
    # check required env vars are there
    if not secret.EMAIL['USERNAME'] or not secret.EMAIL['PASSWORD']:
        raise Exception('Email details not complete')

    if not secret.BINANCE['API_KEY'] or not secret.BINANCE['API_SECRET']:
        raise Exception('Binance details not complete')


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