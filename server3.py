import time, threading
from Pyro5.api import expose, oneway, serve
import uuid
import Pyro5.server
import random

stocks = [{"code": "PETR4", "price": 15.90}, {"code": "VALE3", "price" : 30.20}]

class Worker(object):
    def __init__(self, callback, callbackServer):
        self.callback = callback
        self.callbackServer = callbackServer
        self.counter = 0
        self.orderExecuted = False

    @expose
    @oneway
    def tryExecuteOrder(self, order):
        stock = CallbackServer.findStock(self.callbackServer, order["code"])

        if(not stock):
            return None
        if(order["type"] == "buy"):
            orderToBuy = {"id": uuid.uuid4(), "code": order["code"], "quantity": order["quantity"], "price": order["price"]}
            self.callbackServer.bookBuy.append(orderToBuy)
        else:
            orderToSell = {"id": uuid.uuid4(), "code": order["code"], "quantity": order["quantity"], "price": order["price"]}
            self.callbackServer.bookSell.append(orderToSell)
        while(self.counter < int(order["time"]) and self.orderExecuted == False):
            if(order["type"] == "buy"):
                self.orderExecuted = CallbackServer.executeOrderBuy(self.callbackServer, orderToBuy)
            else:
                self.orderExecuted = CallbackServer.findOrderSell(self.callbackServer, orderToSell['id'])
            time.sleep(1)
            self.counter += 1
        print("Enviando notificação para o cliente...")
        self._pyroDaemon.unregister(self)
        self.callback._pyroClaimOwnership()
        if(not self.orderExecuted):
            self.callback.done("\nOrdem de {0} ações {1} no valor {2} expirou!".format(order["quantity"], order["code"], order["price"]))
        else:
            self.callback.done("\nOrdem de {0} ações {1} no valor {2} foi executada com sucesso!".format(order["quantity"], order["code"], order["price"]))

    @expose
    @oneway
    def addStockToAlert(self, stock):
        stockToAnalyse = CallbackServer.findStock(self.callbackServer, stock["code"])
        print(stockToAnalyse, stock['price'])
        if(stock["alertType"] == 'g'):
            while (float(stockToAnalyse['price']) < float(stock['price'])):
                stockToAnalyse = CallbackServer.findStock(self.callbackServer, stock["code"])
                time.sleep(1)
            print("Enviando notificação para o cliente...")
            self._pyroDaemon.unregister(self)
            self.callback._pyroClaimOwnership()
            self.callback.done("\nA ação {0} atingiu o limite de ganho de {1}!".format(stock["code"], stock["price"]))

        elif(stock["alertType"] == 'p'):
            while (float(stockToAnalyse['price']) > float(stock['price'])):
                stockToAnalyse = CallbackServer.findStock(self.callbackServer, stock["code"])
                time.sleep(1)
            print("Enviando notificação para o cliente...")
            self._pyroDaemon.unregister(self)
            self.callback._pyroClaimOwnership()
            self.callback.done("\nA ação {0} atingiu o limite de perda de {1}!".format(stock["code"], stock["price"]))

def updateStockPrice():
    global stocks
    for stock in stocks:
        n = random.uniform(-1,1) # The random() method in random module generates a float number between 0 and 1.
        stock['price'] = round(stock['price'] + n, 2)
        print(stock)
    threading.Timer(2, updateStockPrice).start()
    return

class CallbackServer(object):
    global stocks
    bookSell = [{"id": uuid.uuid4(), "code": "PETR4", "quantity": "100", "price": "10.10"}]
    bookBuy = []

    # chama a função do timer depois de declarar as funcões
    updateStockPrice()

    def __init__(self):
        self.quoteList = []
        self.myStocks = []

    def executeOrderBuy(self, orderToExecute):
        stockAddSucess = 0
        for index, order in enumerate(self.bookSell):
            if(order["code"] == orderToExecute["code"] and order["quantity"] >= orderToExecute["quantity"] 
            and order['price'] == orderToExecute["price"]):
                for stock in self.myStocks:
                    if stock["code"] == orderToExecute["code"]:
                        stock["quantity"] = stock["quantity"] + orderToExecute["quantity"]
                        stockAddSucess = 1
                        
                if stockAddSucess == 0:
                    self.myStocks.append({"code": orderToExecute["code"], "quantity": orderToExecute["quantity"], "price": orderToExecute["price"]})
                    self.quoteList.append(order)
                    stockAddSucess = 1

                print(self.myStocks)
                self.bookSell.remove(order)
                self.bookBuy.remove(self.findOrderBuy(orderToExecute['id']))
                return True
        return False
              
    @expose
    def getQuoteList(self):
        return self.quoteList

    @expose
    def getMyStocks(self):
        return self.myStocks

    def findStock(self, code):
        for stock in stocks:
            if(stock['code'] == code):
                return stock

    def findOrderBuy(self, id):
        for order in self.bookBuy:
            if(order['id'] == id):
                return order

    def findOrderSell(self, id):
        for order in self.bookSell:
            if(order['id'] == id):
                return False
        return True

    @expose
    def addStockToQuoteList(self, code):
        stockToSave = self.findStock(code)
        if(not stockToSave):
            return "Ação não encontrada!"
        self.quoteList.append(stockToSave)
        return "A ação {0} foi adicionada a sua lista de cotações".format(code)
        
    @expose
    def removeStockToQuoteList(self, code):
        stockToRemove = self.findStock(code)
        if(not stockToRemove):
            return "Ação não encontrada!"
        self.quoteList.remove(stockToRemove)
        return "A ação {0} foi removida a sua lista de cotações".format(code)

    @expose
    def createWorker(self, callback):
        print("server: adding worker")
        worker = Worker(callback, self)
        self._pyroDaemon.register(worker)  # make it a Pyro object
        return worker

serve({
    CallbackServer: "home.broker.server"
})
