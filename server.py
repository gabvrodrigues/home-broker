import Pyro4

@Pyro4.expose
class HomeBroker(object):
    stocks = [{"code": "PETR4", "price": 15.90}, {"code": "VALE3", "price" : 30.20}]

    def __init__(self):
        self.quoteList = []

    def addStockToQuoteList(self, code):
        stockToSave = self.findStock(code)
        if(not stockToSave):
            return "Ação não encontrada!"
        self.wishList.append(self.findStock(code))
        return "A ação {0} foi adicionada a sua lista de cotações".format(code)
    
    def removeStockToQuoteList(self, code):
        stockToRemove = self.findStock(code)
        if(not stockToRemove):
            return "Ação não encontrada!"
        self.wishList.remove(self.findStock(code))
        return "A ação {0} foi removida a sua lista de cotações".format(code)

    def getQuoteList(self):
        return self.quoteList

    def findStock(self, code):
        for stock in self.stocks:
            if(stock['code'] == code):
                return stock

daemon = Pyro4.Daemon()                # make a Pyro daemon
ns = Pyro4.locateNS()                  # find the name server
uri = daemon.register(HomeBroker)      # register the greeting maker as a Pyro object
ns.register("home.broker.server", uri) # register the object with a name in the name server

print("Ready.")
daemon.requestLoop()                   # start the event loop of the server to wait for calls