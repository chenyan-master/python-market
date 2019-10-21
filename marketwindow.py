# -*- coding: utf-8 -*-
#author: chenyan

import websocket
import gzip
import time
import json
import sys
import _thread
from tkinter import *
from tkinter import messagebox
from urllib.request import Request, urlopen

#usdt coinid=2 tradeType: 1: buy 2: sale
usdt_price = 7.07
def getPrice(coinID, tradeType):
    global usdt_price
    huobiapi = "https://l10n-api.huobi.cn"
    api_url = huobiapi + "/general/exchange_rate/list"
    firefox_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}
    request = Request( api_url, headers=firefox_headers )
    html = urlopen( request )
    data = html.read().decode( 'utf-8' )
    dataJson = json.loads( data )
    rateList = dataJson['data']
    for ro in rateList:
        if ro['name'] == "usdt_cny":
            usdt_price = ro['rate']

def priceThread(threadname, coinID, tradeType):
    while(1):
        try:
            getPrice(coinID, tradeType)
            time.sleep(60)
        except:
            print("request error")

argList = ['ht', 'eos', 'btc', 'eth']
ws = None
def subMarketKline():
    global ws
    global argList
    for coinname in argList:
        market1day = """{"sub": "market.""" + coinname.lower() + """usdt.kline.1day", "id": "id10"}"""
        market1min = """{"sub": "market.""" + coinname.lower() + """usdt.kline.1min", "id": "id11"}"""
        ws.send(market1day)
        ws.send(market1min)

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")
    connWebSocket()

def on_open(ws):
    subMarketKline()

def handleMessage(message, coinlist, textlist):
    global ws
    global usdt_price
    try:
        result=gzip.decompress(message).decode('utf-8')
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
                if "kline.1day"  in chname:
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
                elif "kline.1min"  in chname:
                    for index in range(len(coinlist)):
                        if coinlist[index] in chname:
                            alert_message = "{} 1分钟涨跌幅：{:+.2f}%".format(coinlist[index].upper(), rate)
                            if abs(rate) >= 5:
                                messagebox.showwarning(coinlist[index].upper(), alert_message)

    except:
        print('data error')
        connWebSocket()

def on_message(ws, message):
    handleMessage(message, coinList, textList)

def connWebSocket():
    global ws
    while(1):
        try:
            ws = websocket.WebSocketApp("wss://api.huobi.pro/ws",
                                        on_open = on_open,
                                        on_message = on_message,
                                        on_error = on_error,
                                        on_close = on_close)
            ws.run_forever()
            break
        except:
            print('connect ws error,retry...')
            time.sleep(5)

root = Tk()
root.title("Market Price")
root.configure(background='black')

# 订阅 KLine 数据
coinList = []
textList = []

if len(sys.argv) > 1:
    argList = sys.argv[1:]

for coinname in argList:
    coinList.append(coinname.lower())
    coinLabel = Label(root, fg='green', bg='black', font=("微软雅黑", 24), text=coinname.upper())
    textList.append(coinLabel)
    coinLabel.grid(sticky='W')

_thread.start_new_thread(connWebSocket, ())
_thread.start_new_thread(priceThread, ("Thread-2", '2', '1'))

root.mainloop()
