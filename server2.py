from Pyro5.api import expose, oneway, serve
import Pyro5.errors
import uuid


class CallbackServer(object):
    @expose
    @oneway
    def doCallback(self, callback):
        print("\n\nserver: doing callback to client")
        callback._pyroClaimOwnership()
        try:
            callback.call2()
        except Exception:
            print("got an exception from the callback:")
            print("".join(Pyro5.errors.get_pyro_traceback()))
        print("server: callbacks done.\n")

    stocks = [{"code": "PETR4", "price": 15.90}, {"code": "VALE3", "price" : 30.20}]
    bookSell = []
    bookBuy = []

    def __init__(self):
        self.quoteList = []
        self.myStocks = []

    @expose
    @oneway
    def buyStock(self, callback, code, quantity, price):
        stock = self.findStock(code)
        if(not stock):
            return "Ação não encontrada!"
        order = {"id": uuid.uuid4(), "code": code, "quantity": quantity, "price": price}
        self.bookBuy.append(order)
        self.executeOrderBuy(order, callback)
        # return "Ordem de compra criada com sucesso!"

    def executeOrderBuy(self, orderToExecute, callback):
        callback._pyroClaimOwnership()
        for order in self.bookSell:
            if(order["code"] == orderToExecute["code"] and order["quantity"] >= orderToExecute["quantity"] 
            and order['price'] == orderToExecute["price"]):
                self.myStocks.append({"code": orderToExecute["code"], "quantity": orderToExecute["quantity"], "price": orderToExecute["price"]})
                self.bookSell.remove(order)
                self.bookBuy.remove(self.findOrderBuy(orderToExecute['id']))
                print("asada")
                callback.call2()
    
    @expose
    @oneway
    def sellStock(self, callback, code, quantity, price):
        stock = self.findStock(code)
        if(not stock):
            return "Ação não encontrada!"
        order = {"id": uuid.uuid4(), "code": code, "quantity": quantity, "price": price}
        self.bookSell.append(order)
        self.executeOrderSell(order, callback)
        # return "Ordem de venda criada com sucesso!"

    def executeOrderSell(self, orderToExecute, callback):
        callback._pyroClaimOwnership()
        for order in self.bookBuy:
            if(order["code"] == orderToExecute["code"] and order["quantity"] >= orderToExecute["quantity"] 
            and order['price'] == orderToExecute["price"]):
                self.myStocks.append({"code": orderToExecute["code"], "quantity": orderToExecute["quantity"], "price": orderToExecute["price"]})
                self.bookBuy.remove(order)
                self.bookSell.remove(self.findOrderSell(orderToExecute['id']))
                print("aqii")
                callback.call2()
                #Notificar compra e venda

    def addStockToQuoteList(self, code):
        stockToSave = self.findStock(code)
        if(not stockToSave):
            return "Ação não encontrada!"
        self.quoteList.append(self.findStock(code))
        return "A ação {0} foi adicionada a sua lista de cotações".format(code)
    
    def removeStockToQuoteList(self, code):
        stockToRemove = self.findStock(code)
        if(not stockToRemove):
            return "Ação não encontrada!"
        self.quoteList.remove(self.findStock(code))
        return "A ação {0} foi removida a sua lista de cotações".format(code)

    def getQuoteList(self):
        return self.quoteList

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


serve({
    CallbackServer: "home.broker.server"
})