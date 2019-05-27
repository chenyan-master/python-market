# -*- coding: utf-8 -*-
#author: chenyan

from websocket import create_connection
import gzip
import time
import json
import sys
import _thread
from tkinter import *
from urllib.request import Request, urlopen

#usdt coinid=2 tradeType: 1: buy 2: sale
usdt_price = 6.79
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

def priceThread(threadname, coinID, tradeType):
    global usdt_price
    while(1):
        usdt_price = getPrice(coinID, tradeType)
        time.sleep(30)

ws = None
def connWebSocket():
    global ws
    while(1):
        try:
            ws = create_connection("wss://api.huobi.pro/ws")
            break
        except:
            print('connect ws error,retry...')
            time.sleep(5)

def sockeThread(threadname, coinlist, textlist):
    while(1):
        try:
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
                    chname = jsonobj['ch']
                    for index in range(len(coinlist)):
                        if coinlist[index] in chname:
                            str_close = '0.00'
                            if close >= 100:
                                str_close = "{:.2f}".format(close)
                            elif close >= 1:
                                str_close = "{:.4f}".format(close)
                            else:
                                str_close = "{:.8f}".format(close).rstrip('0')
                            cny_close = '0.00'
                            if close*usdt_price >= 1:
                                cny_close = "{:.2f}".format(close*usdt_price)
                            else:
                                cny_close = "{:.4f}".format(close*usdt_price)
                            textlist[index]['text'] = "{}: {} | {:+.2f}% | ≈ {} CNY".format(coinlist[index].upper(), str_close, rate, cny_close)
                            if rate >= 0:
                                textlist[index]['fg'] = 'green'
                            else:
                                textlist[index]['fg'] = 'red'
                            break
        except:
            print('data error')
            connWebSocket()


root = Tk()
root.title("hello market")
root.configure(background='black')

connWebSocket()

# 订阅 KLine 数据
coinList = []
textList = []
argList = ['ht', 'eos', 'btc', 'eth']

if len(sys.argv) > 1:
    argList = sys.argv[1:]

for coinname in argList:
    market = """{"sub": "market.""" + coinname.lower() + """usdt.kline.1day", "id": "id10"}"""
    coinList.append(coinname.lower())
    ws.send(market)
    coinLabel = Label(root, fg='green', bg='black', font=("微软雅黑", 24), text=coinname)
    textList.append(coinLabel)
    coinLabel.grid(sticky='W')

thread1 = _thread.start_new_thread(sockeThread, ("Thread-1", coinList, textList))
thread2 = _thread.start_new_thread(priceThread, ("Thread-2", '2', '1'))

root.mainloop()
