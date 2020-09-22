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

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class CallbackHandler(object):
    workdone = False
    end = False

    @expose
    def done(self, messageReceived):
        print(bcolors.UNDERLINE + bcolors.OKGREEN + messageReceived + bcolors.ENDC)
        CallbackHandler.workdone = True

def readInput():
    global option
    option = input('Escolha: ').strip()

def printMenu():
    print(bcolors.BOLD + "-----------HOME BROKER-----------" +  bcolors.ENDC)
    print("1) Adicionar ação às minhas cotações")
    print("2) Remover ação às minhas cotações")
    print("3) Ver minha lista de cotações")
    print("4) Comprar ação")
    print("5) Vender ação")
    print("6) Ver minha carteira")
    print("7) Adicionar alerta de preço")
    
def menu(homeBroker):
    global option, running
    homeBroker._pyroClaimOwnership()
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
        storeOrder({"code": code, "quantity": quantity, "price": price, "time": time, "type": "buy"}, homeBroker)
    elif(option == "5"):
        code = input("Código: ").strip()
        quantity = input("Quantidade: ").strip()
        price = input("Preço: ").strip()
        time = input("Tempo(s): ").strip()
        storeOrder({"code": code, "quantity": quantity, "price": price, "time": time, "type": "sell"}, homeBroker)
    elif(option == "6"):
        myStocks = homeBroker.getMyStocks()
        if(len(myStocks) == 0):
            print("Nenhuma ação encontrada")
        else:
            for stock in myStocks:
                print("{0} - {1}".format(stock["code"], stock["price"]))
    elif(option == "7"):
        code = input("Código: ").strip()
        price = input("Preço: ").strip()
        createAlert({"code": code, "price": price}, homeBroker)

    option = None
    running = True
    menu(homeBroker)

def threadExecuteOrder(order, homeBroker):
    global option, running, ordemFinalizada
    
    with Daemon() as daemon1:
        homeBroker._pyroClaimOwnership()

        callback = CallbackHandler()
        daemon1.register(callback)
        
        worker = homeBroker.createWorker(callback)
        worker.tryExecuteOrder(order)
        print("Ordem enviada com sucesso!")
        ordemFinalizada = 1
        daemon1.requestLoop(loopCondition=lambda: CallbackHandler.workdone != True)
        CallbackHandler.workdone = False

def threadAlert(stock, homeBroker):
    global option, running, ordemFinalizada
    
    with Daemon() as daemon2:
        homeBroker._pyroClaimOwnership()

        callback = CallbackHandler()
        daemon2.register(callback)
        
        worker = homeBroker.createWorker(callback)
        worker.addStockToAlert(stock)
        print("Ordem enviada com sucesso!")
        ordemFinalizada = 1
        daemon2.requestLoop(loopCondition=lambda: CallbackHandler.workdone != True)
        CallbackHandler.workdone = False

def storeOrder(order, homeBroker):
    global option, running, ordemFinalizada
    _thread.start_new_thread(threadExecuteOrder, (order,homeBroker))
    while ordemFinalizada == 0:
        time.sleep (0.2)
    option = None
    running = True
    ordemFinalizada = 0
    menu(homeBroker)

def createAlert(stock, homeBroker):
    global option, running, ordemFinalizada
    _thread.start_new_thread(threadAlert, (stock,homeBroker))
    while ordemFinalizada == 0:
        time.sleep (0.2)
    option = None
    running = True
    ordemFinalizada = 0
    menu(homeBroker)

def loopCallBackPrincipal():
    with Proxy("PYRONAME:home.broker.server") as homeBroker:
        #print("Thread criada e rodando")
        menu(homeBroker)
        print("bye!")

_thread.start_new_thread(loopCallBackPrincipal, ())
while True:
    time.sleep(1)

    







