# -*- coding: utf-8 -*-
#author: chenyan

from websocket import create_connection
import gzip
import time
import json
import sys
from urllib.request import Request, urlopen

def getPrice(coinID, tradeType):
    huobiapi = "https://otc-api.huobi.pro/v1/data/trade/list/public"
    api_url = huobiapi + "?coinId=" + coinID + "&tradeType=" + tradeType + "&currPage=1&payMethod=0&country=&merchant=1&online=1&currency=1"
    firefox_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}
    request = Request( api_url, headers=firefox_headers )
    html = urlopen( request )
    data = html.read().decode( 'utf-8' )
    dataJson = json.loads( data )
    price = dataJson['data'][0]['price']
    return price

if __name__ == '__main__':
    while(1):
        try:
            ws = create_connection("wss://api.huobi.pro/ws")
            break
        except:
            print('connect ws error,retry...')
            time.sleep(5)

    # 订阅 KLine 数据
    # tradeStr="""{"sub": "market.htusdt.kline.1min","id": "id10"}"""

    #订阅 Trade Detail 数据
    #tradeStr="""{"sub": "market.btcusdt.trade.detail", "id": "id10"}"""
    
    #订阅 Market Detail 数据
    coinname = 'ht'
    if len(sys.argv) > 1:
        coinname = sys.argv[1]

    market = """{"sub": "market.""" + coinname.lower() + """usdt.kline.1day", "id": "id10"}"""
    ws.send(market)
    trade_id = ''
    while(1):
        compressData=ws.recv()
        result=gzip.decompress(compressData).decode('utf-8')
        if result[:7] == '{"ping"':
            ts=result[8:21]
            pong='{"pong":'+ts+'}'
            ws.send(pong)
        else:
            jsonobj = json.loads(result)
            if 'tick' in jsonobj.keys():
                close = jsonobj['tick']['close']
                rate = (close - jsonobj['tick']['open'])/jsonobj['tick']['open'] * 100
                price = getPrice('2', '1')
                print ("{}: {:.4f} | {:+.2f}% | {:.2f}".format(coinname.upper(), close, rate, close * price))
