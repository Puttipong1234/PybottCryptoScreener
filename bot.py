import math

import numpy
import talib
from binance.client import Client


def CheckAccount(symbol,client):
    Symbol = symbol.split("USDT")[0]
    pr = float(client.get_avg_price(symbol=symbol)["price"])
    balance = client.get_asset_balance(asset=Symbol)
    try:
        if float(balance["free"]) * pr > 20:
            return True
        else:
            return False
    except:
        return False


def CheckCross(symbol,client):
    klines = client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1DAY, "100 day ago UTC")
    CLOSE = [float(i[1]) for i in klines]
    CLOSE = numpy.array(CLOSE)
    CLOSE = numpy.nan_to_num(CLOSE)
    EMA12 = talib.MA(CLOSE, timeperiod=12, matype=1)
    EMA26 = talib.MA(CLOSE, timeperiod=26, matype=1)
    EMA12 = list(numpy.nan_to_num(EMA12))
    EMA26 = list(numpy.nan_to_num(EMA26))
    if ( EMA12[-1] - EMA26[-1] ) > 0 and ( EMA12[-2] - EMA26[-2] ) < 0 :
        return "CrossUp" , 0 
        
    elif ( EMA12[-1] - EMA26[-1] ) < 0 and ( EMA12[-2] - EMA26[-2] ) > 0 :
        return "CrossDown" , 0 
    
    else :
        cross_date = 0
        cross_signals = None
        for index , (ema12 , ema26) in enumerate(zip(EMA12,EMA26)):
            if index > 26:
                if ( ema12 - ema26 ) > 0 and ( EMA12[index-1] - EMA26[index-1] ) < 0 :
                    cross_date = index
                    cross_signals = "CrossUp"
                
                elif ( ema12 - ema26 ) < 0 and ( EMA12[index-1] - EMA26[index-1] ) > 0 :
                    cross_date = index
                    cross_signals = "CrossDown"
        
        if (cross_signals == "CrossUp") and (CLOSE[-1] < CLOSE[cross_date] * 1.1) : # ราคายังวิ่งไม่มาก (ไม่ถึง 10% จากราคาเปิดสัญญาณ) ขึ้นรถทัน
            return cross_signals , len(EMA12) - cross_date - 2 , "ยังซื้อทัน"
        
        else :
            return cross_signals , len(EMA12) - cross_date - 2 , "ซื้อไม่ทันแล้ว"

from line_notify import LineNotify
from datetime import date

def Checkport(API_KEY,API_SECRET,LINE_API,NAME):
    client = Client(API_KEY, API_SECRET)
    today = date.today()
    ACCESS_TOKEN = LINE_API

    notify = LineNotify(ACCESS_TOKEN)
    notify.send("สวัสดี {} ยินดีต้อนรับสู่บริการตรวจสอบ \nPortFolio Healthy Check  \n By CDC action Zone".format(NAME))
    notify.send("--------------------------------\nสัญญาณเขียวแดงประจำวัน\nวันที่ {}\nระบบกำลังประมวลผล PortFolio ของคุณ {}\n อาจใช้เวลาประมาณ 3-5 นาที กรุณารอซักครู่\n--------------------------------".format(today.strftime("%d/%m/%Y"),NAME))

    # check เขียวแรก แดงแรก
    exchange_info = client.get_exchange_info()
    list_msg_1 = []
    for s in exchange_info['symbols']:
        if "USDT" in s['symbol']:
            msg = ""
            try:
                res = CheckCross(s['symbol'],client)
                if res[1] == 0:
                    print(s['symbol'])
                    print(res)
                    if res[0] == "CrossUp":
                        msg = msg + "\n 🟢 เขียวแรก! "
                        msg = msg + s['symbol']

                        if not CheckAccount(s['symbol'],client): # check ว่ามีอยู่หรือไม่ ถ้าไม่มี ซื้อ
                            msg = msg + "\n👦 {} - ยังไม่มีของนะ".format(NAME)
                    
                    elif res[0] == "CrossDown":
                        msg = msg + "\n 🔻 แดงแรก! "
                        msg = msg + s['symbol']

                        if CheckAccount(s['symbol'],client): # check ว่ามีอยู่หรือไม่ ถ้ามี ขาย
                            msg = msg + "\n👦 {} - ยังมีของนะ".format(NAME)

                    list_msg_1.append(msg)
            except Exception as e :
                print(e)
                pass
            
    
    for msg in list_msg_1:
        notify.send(msg)


    notify.send("--------------------------------\nสัญญาณเขียวแล้ว[แต่ยังซื้อทัน ราคาไม่วิ่งมาก]\nวันที่ {}\nระบบกำลังประมวลผล PortFolio ของคุณ {}\n อาจใช้เวลาประมาณ 3-5 นาที กรุณารอซักครู่\n--------------------------------".format(today.strftime("%d/%m/%Y"),NAME))
    # check ไม่มีของ แต่ยังซื้อทัน ราคายังวิ่งไม่มาก
    list_msg_2 = []
    exchange_info = client.get_exchange_info()
    for s in exchange_info['symbols']:
        if "USDT" in s['symbol']:
            msg = ""
            try:
                res = CheckCross(s['symbol'],client)
                if 0 < res[1] < 20 and res[2] == "ยังซื้อทัน":
                    print(s['symbol'])
                    print(res)
                    if res[0] == "CrossUp":
                        msg = msg + "\n🟢⚠️🟢\nเขียวแล้ว {} วัน\nยังซื้อทัน!".format(res[1])
                        msg = msg + s['symbol']
                        if not CheckAccount(s['symbol'],client): # check ว่ามีอยู่หรือไม่
                            msg = msg + "\n👦 {} - ยังไม่มีของนะ".format(NAME)
                        list_msg_2.append(msg)
            except Exception as e :
                print(e)
                pass
            
            
    
    for msg in list_msg_2:
        notify.send(msg)

    notify.send("--------------------------------\nสัญญาณแดงแล้ว[แต่ยังไม่ยอมขาย]\nวันที่ {}\nระบบกำลังประมวลผล PortFolio ของคุณ\n {} \nอาจใช้เวลาประมาณ 3-5 นาที กรุณารอซักครู่\n--------------------------------".format(today.strftime("%d/%m/%Y"),NAME))
    # check เราถืออยู่ ไม่ยอมขาย ถ้าแดงอยู่แล้วไม่ขาย = เตือนให้ขาย
    list_msg_3 = []
    exchange_info = client.get_exchange_info()
    for s in exchange_info['symbols']:
        if "USDT" in s['symbol']:
            msg = ""
            
            try:
                res = CheckCross(s['symbol'],client)
                if res[0] == "CrossDown":
                    msg = msg + "\n 🔻 แดงแล้วขายด่วน! "
                    msg = msg + s['symbol']

                    if CheckAccount(s['symbol'],client): # check ว่ามีอยู่หรือไม่
                        msg = msg + "\n👦 {} - ยังมีของนะ".format(NAME)
                        list_msg_3.append(msg)
            except Exception as e :
                print(e)
                pass    
            
            
    if not list_msg_3:
        notify.send("ไม่มีพบการถือเหรียญที่แดงอยู่เลย ! สุดยอด")
    else:
        for msg in list_msg_3:
            notify.send(msg)

    notify.send("--------------------------------\nจบการรายงาน PortFolio ของคุณ {} \nขอบพระคุณที่ใช้บริการ\n--------------------------------".format(NAME))


