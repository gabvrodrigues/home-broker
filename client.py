import Pyro4

# homeBroker = Pyro4.Proxy("PYRONAME:home.broker.server")   # use name server object lookup uri shortcut
# Pyro4.config.COMMTIMEOUT=0.5

class Callback(object):
    @Pyro4.expose
    @Pyro4.callback
    def call(self):
        print("callback received")
        

daemon = Pyro4.core.Daemon()
callback = Callback()
daemon.register(callback)

homeBroker = Pyro4.Proxy("PYRONAME:home.broker.server")

# print("waiting for callbacks to arrive...")
# print("(ctrl-c/break the program once it's done)\n")
# daemon.requestLoop()

def printMenu():
    print("-----------HOME BROKER-----------")
    print("1) Adicionar ação às minhas cotações")
    print("2) Remover ação às minhas cotações")
    print("3) Ver minha lista de cotações")
    print("4) Comprar ação")
    print("5) Vender ação")

while True:
    printMenu()
    option = input("Escolha: ").strip()

    if(option == "1"):
        code = input("Código: ").strip()
        print(homeBroker.addStockToQuoteList(code))
    elif(option == "2"):
        code = input("Código: ").strip()
        print(homeBroker.removeStockToQuoteList(code))
    elif(option == "3"):
        for stock in homeBroker.getQuoteList():
            print("{0} - {1}".format(stock["code"], stock["price"]))
    elif(option == "4"):
        code = input("Código: ").strip()
        quantity = input("Quantidade: ").strip()
        price = input("Preço: ").strip()
        print(homeBroker.buyStock(code, quantity, price))
        # homeBroker._pyroOneway.add("doCallback")
        homeBroker.doCallback(callback)

    elif(option == "5"):
        code = input("Código: ").strip()
        quantity = input("Quantidade: ").strip()
        price = input("Preço: ").strip()
        print(homeBroker.sellStock(code, quantity, price))





