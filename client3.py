import random
from Pyro5.api import expose, Daemon, Proxy, config
import signal
import _thread
import time

config.COMMTIMEOUT = 0.5

option = None
running = True
message = None
ordemFinalizada = 0

class CallbackHandler(object):
    workdone = False
    end = False

    @expose
    def done(self, messageReceived):
        print(messageReceived)
        CallbackHandler.workdone = True

    @expose
    def finish(self, order):
        print("Até Logo!")
        CallbackHandler.end = True

""" def timeout(seconds):
    def decorator(function):
        def wrapper(*args, **kwargs):
            def handler(signum, frame):
                raise Exception(f'Timeout of {function.__name__} function')
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(seconds)
            result = function(*args, **kwargs)
            signal.alarm(0)
            return result
        return wrapper
    return decorator
 """
#@timeout(seconds=2)
def readInput():
    global option
    option = input('Escolha: ').strip()

def printMenu():
    print("-----------HOME BROKER-----------")
    print("1) Adicionar ação às minhas cotações")
    print("2) Remover ação às minhas cotações")
    print("3) Ver minha lista de cotações")
    print("4) Comprar ação")
    print("5) Vender ação")
    print("6) Ver minha carteira")
    
def menu(homeBroker):
    global option, running
    printMenu()
    while running:
        try:
            readInput()
            running = False
        except Exception as e:
            print(e)      
    if(option == "1"):
        code = input("Código: ").strip()
        print(homeBroker.addStockToQuoteList(code))
    elif(option == "2"):
        code = input("Código: ").strip()
        print(homeBroker.removeStockToQuoteList(code))
    elif(option == "3"):
        if(len(homeBroker.getQuoteList()) == 0):
            print("Nenhuma ação encontrada")
        else:
            for stock in homeBroker.getQuoteList():
                print("{0} - {1}".format(stock["code"], stock["price"]))
    elif(option == "4"):
        code = input("Código: ").strip()
        quantity = input("Quantidade: ").strip()
        price = input("Preço: ").strip()
        time = input("Tempo(s): ").strip()
        buyStock({"code": code, "quantity": quantity, "price": price, "time": time, "type": "buy"}, homeBroker)
    elif(option == "5"):
        code = input("Código: ").strip()
        quantity = input("Quantidade: ").strip()
        price = input("Preço: ").strip()
        time = input("Tempo(s): ").strip()
        sellStock({"code": code, "quantity": quantity, "price": price, "time": time, "type": "sell"}, homeBroker)

    elif(option == "6"):
        myStocks = homeBroker.getMyStocks()
        print(myStocks)
        if(len(myStocks) == 0):
            print("Nenhuma ação encontrada")
        else:
            for stock in myStocks:
                print("{0} - {1}".format(stock["code"], stock["price"]))
    option = None
    running = True
    menu(homeBroker)

def loopCallBack(order):
    global option, running, ordemFinalizada
    with Proxy("PYRONAME:home.broker.server") as homeBroker:
        with Daemon() as daemon1:
            # register our callback handler
            callback = CallbackHandler()
            daemon1.register(callback)
            
        
            worker = homeBroker.addBuyOrder(callback)  # provide our callback handler!
            worker.work(order)
            print("Ordem enviada com sucesso!")
            ordemFinalizada = 1
            daemon1.requestLoop(loopCondition=lambda: CallbackHandler.workdone != True)
            CallbackHandler.workdone = False

def buyStock(order, homeBroker):
    global option, running, ordemFinalizada
    _thread.start_new_thread(loopCallBack, (order,))
    while ordemFinalizada == 0:
        time.sleep (0.2)
    option = None
    running = True
    ordemFinalizada = 0
    menu(homeBroker)

def sellStock(order, homeBroker):
    global option, running, ordemFinalizada
    _thread.start_new_thread(loopCallBack, (order,))
    while ordemFinalizada == 0:
        time.sleep (0.2)
    option = None
    running = True
    ordemFinalizada = 0
    menu(homeBroker)

def loopCallBackPrincipal():
    with Proxy("PYRONAME:home.broker.server") as homeBroker:
        with Daemon() as daemon:
            print("thread criada e rodando")
            menu(homeBroker)
            daemon.requestLoop(loopCondition=lambda: CallbackHandler.end != True)
            print("bye!")

print("Seja bem-vindo ao Home Broker")
_thread.start_new_thread(loopCallBackPrincipal, ())
while True:
    time.sleep(1)

    







