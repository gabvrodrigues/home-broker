import logging
import sys
from Pyro5.api import expose, callback, Daemon, Proxy


# initialize the logger so you can see what is happening with the callback exception message:
logging.basicConfig(stream=sys.stderr, format="[%(asctime)s,%(name)s,%(levelname)s] %(message)s")
log = logging.getLogger("Pyro5")
log.setLevel(logging.WARNING)


class CallbackHandler(object):
    @expose
    @callback
    def call2(self):
        print("\n\ncallback 2 received from server!")
        print("going to crash - but you will see the exception printed here too:")

daemon = Daemon()
callback = CallbackHandler()
daemon.register(callback)

homeBroker = Proxy("PYRONAME:home.broker.server")
# homeBroker.doCallback(callback)   # this is a oneway call, so we can continue right away

print("waiting for callbacks to arrive...")
print("(ctrl-c/break the program once it's done)")

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
        homeBroker.buyStock(callback, code, quantity, price)
        # homeBroker._pyroOneway.add("doCallback")
        # homeBroker.doCallback(callback)

    elif(option == "5"):
        code = input("Código: ").strip()
        quantity = input("Quantidade: ").strip()
        price = input("Preço: ").strip()
        homeBroker.sellStock(callback, code, quantity, price)
    daemon.requestLoop()