import Pyro4
import uuid


@Pyro4.expose
class HomeBroker(object):
    stocks = [{"code": "PETR4", "price": 15.90}, {"code": "VALE3", "price" : 30.20}]
    bookSell = []
    bookBuy = []

    def __init__(self):
        self.quoteList = []
        self.myStocks = []
    
    def buyStock(self, code, quantity, price):
        stock = self.findStock(code)
        if(not stock):
            return "Ação não encontrada!"
        order = {"id": uuid.uuid4(), "code": code, "quantity": quantity, "price": price}
        self.bookBuy.append(order)
        self.executeOrderBuy(order)
        return "Ordem de compra criada com sucesso!"

    def executeOrderBuy(self, orderToExecute):
        for order in self.bookSell:
            if(order["code"] == orderToExecute["code"] and order["quantity"] >= orderToExecute["quantity"] 
            and order['price'] == orderToExecute["price"]):
                self.myStocks.append({"code": orderToExecute["code"], "quantity": orderToExecute["quantity"], "price": orderToExecute["price"]})
                self.bookSell.remove(order)
                self.bookBuy.remove(self.findOrderBuy(orderToExecute['id']))
                #Notificar compra e venda
    
    def sellStock(self, code, quantity, price):
        stock = self.findStock(code)
        if(not stock):
            return "Ação não encontrada!"
        order = {"id": uuid.uuid4(), "code": code, "quantity": quantity, "price": price}
        self.bookSell.append(order)
        self.executeOrderSell(order)
        return "Ordem de venda criada com sucesso!"

    def executeOrderSell(self, orderToExecute):
        for order in self.bookBuy:
            if(order["code"] == orderToExecute["code"] and order["quantity"] >= orderToExecute["quantity"] 
            and order['price'] == orderToExecute["price"]):
                self.myStocks.append({"code": orderToExecute["code"], "quantity": orderToExecute["quantity"], "price": orderToExecute["price"]})
                self.bookBuy.remove(order)
                self.bookSell.remove(self.findOrderSell(orderToExecute['id']))
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
    
    def doCallback(self, callback):
        try:
            callback.call()
        except:
            print("got an exception from the callback.")
            print("".join(Pyro4.util.getPyroTraceback()))
        print("server: callbacks done")

daemon = Pyro4.Daemon()                # make a Pyro daemon
ns = Pyro4.locateNS()                  # find the name server
uri = daemon.register(HomeBroker)      # register the greeting maker as a Pyro object
ns.register("home.broker.server", uri) # register the object with a name in the name server


print("Ready.")
daemon.requestLoop()                   # start the event loop of the server to wait for calls