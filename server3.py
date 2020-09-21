import time
from Pyro5.api import expose, oneway, serve
import uuid
import Pyro5.server

class Worker(object):
    def __init__(self, callback):
        self.callback = callback
        self.counter = 0
        self.orderExecuted = False

    @expose
    @oneway
    def work(self, order):
        callbackServer = CallbackServer()
        stock = CallbackServer.findStock(callbackServer, order["code"])

        if(not stock):
            return None
        if(order["type"] == "buy"):
            orderToBuy = {"id": uuid.uuid4(), "code": order["code"], "quantity": order["quantity"], "price": order["price"]}
            callbackServer.bookBuy.append(orderToBuy)
        else:
            orderToSell = {"id": uuid.uuid4(), "code": order["code"], "quantity": order["quantity"], "price": order["price"]}
            callbackServer.bookSell.append(orderToSell)
        while(self.counter < int(order["time"]) and self.orderExecuted == False):
            if(order["type"] == "buy"):
                self.orderExecuted = CallbackServer.executeOrderBuy(callbackServer, orderToBuy)
            time.sleep(1)
            self.counter += 1
        print("Enviando notificação para o cliente...")
        self._pyroDaemon.unregister(self)
        self.callback._pyroClaimOwnership()
        if(not self.orderExecuted):
            self.callback.done("\nOrdem de {0} ações {1} no valor {2} expirou!".format(order["quantity"], order["code"], order["price"]))
        else:
            self.callback.done("\nOrdem de {0} ações {1} no valor {2} foi executada com sucesso!".format(order["quantity"], order["code"], order["price"]))

@Pyro5.server.behavior(instance_mode="single")
class CallbackServer(object):
    stocks = [{"code": "PETR4", "price": 15.90}, {"code": "VALE3", "price" : 30.20}]
    bookSell = [{"id": uuid.uuid4(), "code": "PETR4", "quantity": "100", "price": "10.10"}]
    bookBuy = []

    def __init__(self):
        self.quoteList = []
        self.myStocks = []

    def executeOrderBuy(self, orderToExecute):
        for index, order in enumerate(self.bookSell):
            if(order["code"] == orderToExecute["code"] and order["quantity"] >= orderToExecute["quantity"] 
            and order['price'] == orderToExecute["price"]):
                self.myStocks.append({"code": orderToExecute["code"], "quantity": orderToExecute["quantity"], "price": orderToExecute["price"]})
                print(self.myStocks)
                self.bookSell.remove(order)
                self.bookBuy.remove(self.findOrderBuy(orderToExecute['id']))
                return True
        return False
    
    def executeOrderSell(self, orderToExecute):
        for order in self.bookBuy:
            if(order["code"] == orderToExecute["code"] and order["quantity"] >= orderToExecute["quantity"] 
            and order['price'] == orderToExecute["price"]):
                self.myStocks.append({"code": orderToExecute["code"], "quantity": orderToExecute["quantity"], "price": orderToExecute["price"]})
                self.bookBuy.remove(order)
                self.bookSell.remove(self.findOrderSell(orderToExecute['id']))
                return True
        return False                

    @expose
    def getQuoteList(self):
        return self.quoteList

    @expose
    def getMyStocks(self):
        print(self.myStocks)
        return self.myStocks

    def findStock(self, code):
        for stock in self.stocks:
            if(stock['code'] == code):
                return stock

    def findOrderBuy(self, id):
        for order in self.bookBuy:
            if(order['id'] == id):
                return order

    def findOrderSell(self, id):
        for order in self.bookSell:
            if(order['id'] == id):
                return order

    def isTheEnd(self):
        return self.leave

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
    def addBuyOrder(self, callback):
        print("server: adding worker")
        worker = Worker(callback)
        self._pyroDaemon.register(worker)  # make it a Pyro object
        return worker
    
    @expose
    def addSellOrder(self, callback):
        print("server: adding worker")
        worker = Worker(callback)
        self._pyroDaemon.register(worker)  # make it a Pyro object
        return worker


serve({
    CallbackServer: "home.broker.server"
})