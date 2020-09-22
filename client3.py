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

#Classe que trata o callback (notificação do servidor para o cliente)
class CallbackHandler(object):
    workdone = False
    end = False

    #Método chamado pelo servidor para notificar o cliente
    @expose
    def done(self, messageReceived):
        print(bcolors.UNDERLINE + bcolors.OKGREEN + messageReceived + bcolors.ENDC)
        #CallbackHandler.workdone = True

#Método para pegar a escolha digitada pelo usuário
def readInput():
    global option
    option = input(bcolors.WARNING + bcolors.BOLD + 'Escolha: ' + bcolors.ENDC).strip()

def printMenu():
    print(bcolors.BOLD + "-----------HOME BROKER-----------" +  bcolors.ENDC)
    print("1) Adicionar ação às minhas cotações")
    print("2) Remover ação às minhas cotações")
    print("3) Ver minha lista de cotações")
    print("4) Comprar ação")
    print("5) Vender ação")
    print("6) Ver minha carteira")
    print("7) Adicionar alerta de preço")

#Método que trata as opções escolhidas pelo usuário
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
        print(homeBroker.addStockToQuoteList(code)) #Chama o método do servidor para adicionar uma ação na lista de cotações

    elif(option == "2"):
        code = input("Código: ").strip()
        print(homeBroker.removeStockToQuoteList(code)) #Chama o método do servidor para remover uma ação na lista de cotações

    elif(option == "3"):
        if(len(homeBroker.getQuoteList()) == 0):
            print("Nenhuma ação encontrada")
        else:
            for stock in homeBroker.getQuoteList(): #Chama o método do servidor para listar as ações da lista de cotações
                print("{0} - {1}".format(stock["code"], stock["price"]))

    #Pega as informações da nova ordem de compra
    elif(option == "4"):
        code = input("Código: ").strip()
        quantity = input("Quantidade: ").strip()
        price = input("Preço: ").strip()
        time = input("Tempo(s): ").strip()
        storeOrder({"code": code, "quantity": quantity, "price": price, "time": time, "type": "buy"}, homeBroker)

    #Pega as informações da nova ordem de venda
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
                print("{0} - {1}".format(stock["code"], stock["quantity"]))

    elif(option == "7"):
        code = input("Código: ").strip()
        price = input("Preço: ").strip()
        alertType = input("Tipo de Alerta - Ganho (g) ou Perda (p): ").strip()
        createAlert({"code": code, "price": price, 'alertType': alertType}, homeBroker)

    option = None
    running = True
    menu(homeBroker)

#Thread criada para acompanhar a execução da ordem
def threadExecuteOrder(order, homeBroker):
    global option, running, ordemFinalizada
    
    with Daemon() as daemon1:
        homeBroker._pyroClaimOwnership()

        callback = CallbackHandler()
        daemon1.register(callback)
        
        worker = homeBroker.createWorker(callback) #Cria worker no servidor para tentar executar a ordem
        worker.tryExecuteOrder(order)
        print("Ordem enviada com sucesso!")
        ordemFinalizada = 1
        daemon1.requestLoop(loopCondition=lambda: CallbackHandler.workdone != True)
        CallbackHandler.workdone = False

#Thread criada para cada alerta cadastrado
def threadAlert(stock, homeBroker):
    global option, running, ordemFinalizada
    
    with Daemon() as daemon2:
        homeBroker._pyroClaimOwnership()

        callback = CallbackHandler()
        daemon2.register(callback)
        
        worker = homeBroker.createWorker(callback) #Cria worker no servidor para verificar preço da ação
        worker.addStockToAlert(stock)
        print("Alerta criado com sucesso!")
        ordemFinalizada = 1
        daemon2.requestLoop(loopCondition=lambda: CallbackHandler.workdone != True)
        CallbackHandler.workdone = False

#Método que cria uma thread para receber a notificação se a ordem foi executada ou não
def storeOrder(order, homeBroker):
    global option, running, ordemFinalizada
    _thread.start_new_thread(threadExecuteOrder, (order,homeBroker))
    while ordemFinalizada == 0:
        time.sleep (0.2)
    option = None
    running = True
    ordemFinalizada = 0
    menu(homeBroker)

#Método que cria uma thread para receber a notificação se a ação atingiu o preço desejado
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

    







