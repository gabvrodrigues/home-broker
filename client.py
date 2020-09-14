import Pyro4

homeBroker = Pyro4.Proxy("PYRONAME:home.broker.server")   # use name server object lookup uri shortcut
def printMenu():
    print("-----------HOME BROKER-----------")
    print("1) Adicionar ação às minhas cotações")
    print("2) Remover ação às minhas cotações")
    print("3) Ver minha lista de cotações")

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





