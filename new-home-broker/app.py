import queue
import uuid
import threading
import random

import flask
from flask_cors import CORS
from flask import request, jsonify

app = flask.Flask(__name__)
CORS(app)

clients = []
stocks = [{"code": "PETR4", "price": 15.87}, {"code": "VALE3", "price": 54.76}, {"code": "MGLU3", "price": 89.90}]
bookBuy = []
bookSell = []
teste = 0

def updateStockPrice():
    global stocks
    for stock in stocks:
        n = random.uniform(-1,1) # The random() method in random module generates a float number between 0 and 1.
        stock['price'] = round(stock['price'] + n, 2)
        print(stock)
    threading.Timer(2, updateStockPrice).start()
    return

# chama a função do timer depois de declarar as funcões
updateStockPrice()

@app.route("/")
def hello_world():
    return "Hello, World!"


class MessageAnnouncer:
    def __init__(self):
        self.listeners = []

    def listen(self):
        self.listeners.append(queue.Queue(maxsize=5))
        return self.listeners[-1]

    def announce(self, msg):
        # We go in reverse order because we might have to delete an element, which will shift the
        # indices backward
        for i in reversed(range(len(self.listeners))):
            try:
                self.listeners[i].put_nowait(msg)
            except queue.Full:
                del self.listeners[i]


def format_sse(data: str, event=None) -> str:
    """Formats a string and an event name in order to follow the event stream convention.

    >>> format_sse(data=json.dumps({'abc': 123}), event='Jackson 5')
    'event: Jackson 5\\ndata: {"abc": 123}\\n\\n'

    """
    msg = f"data: {data}\n\n"
    if event is not None:
        msg = f"event: {event}\n{msg}"
    return msg


@app.route("/connect/<id>", methods=["GET"])
def connect(id):
    global clients
    clients.append({"id": id, "stockList": [{"code": "PETR4", "price": 15.87, "quantity": 100}, {"code": "VALE3", "price": 54.76, "quantity": 100}, {"code": "MGLU3", "price": 89.90, "quantity": 100}], 
    "quoteList": [stocks[0], stocks[1], stocks[2]]})
    return {"message": "Cliente conectado com sucesso!"}, 200


@app.route("/disconnect/<id>", methods=["GET"])
def disconnect(id):
    global clients
    index = findClientIndex(id)
    if index >= 0:
        del clients[index]
        print(clients)
    return {"message": "Cliente desconectado com sucesso!"}, 200


@app.route("/buy-stock", methods=["POST"])
def buyStock():
    global clients, bookBuy
    content = request.get_json(silent=True)
    announcer = MessageAnnouncer()
    order = {"id": uuid.uuid4(), "userId": content["userId"], "code": content["code"], "quantity": content["quantity"], 
    "price": content["price"], "announcer": announcer}

    bookBuy.append(order)
    orderToBuy = tryBuyStock(order)
    if orderToBuy == None:
        return {"message": "Ordem de compra de {0}x {1} por R${2} foi cadastrada com sucesso! Você será notificado quando a ordem for executada!".format(order["quantity"], order["code"], order["price"]), "orderId": orderToBuy}, 200
    else:
        return {"message": "Ordem de compra de {0}x {1} por R${2} foi executada com sucesso!".format(order["quantity"], order["code"], order["price"]), "orderId": orderToBuy['id']}, 200

@app.route("/sell-stock", methods=["POST"])
def sellStock():
    global clients, bookBuy, bookSell
    content = request.get_json(silent=True)
    announcer = MessageAnnouncer()
    order = {"id": uuid.uuid4(), "userId": content["userId"], "code": content["code"], "quantity": content["quantity"], 
    "price": content["price"], "announcer": announcer}

    # procura se o stock está na lista do cliente
    clientSellerIndex = findClientIndex(order["userId"])
    stock = findStockInMyWallet(order["code"], clients[clientSellerIndex]["stockList"])

    if(stock == None or int(stock["quantity"]) < int(order['quantity'])):
        return {"message": "Ordem de venda inválida!", "orderId": None}, 200
    
    bookSell.append(order)
    orderToSell = trySellStock(order, stock)
    
    if orderToSell != None:
        return {"message": "Ordem de venda de {0}x {1} por R${2} foi cadastrada com sucesso! Você será notificado quando a ordem for executada!".format(order["quantity"], 
        order["code"], order["price"]), "orderId": orderToSell['id']}, 200
    elif orderToSell == -1:
        return {"message": "Ordem de venda inválida!", "orderId": None}, 200
    else:
        return {"message": "Ordem de venda de {0}x {1} por R${2} foi executada com sucesso!".format(orderToSell["quantity"], order["code"], order["price"]), "orderId": orderToSell["id"]}, 200

@app.route("/show-my-quote-list/<id>", methods=["GET"])
def showMyQuoteList(id):
    global clients
    index = findClientIndex(id)
    if index < 0:
        return {"message": "Erro ao listar cotações: cliente não encontrado!"}, 500
    
    return {"quoteList": clients[index]["quoteList"]}, 200

@app.route("/show-my-wallet/<id>", methods=["GET"])
def showMyWallet(id):
    global clients
    index = findClientIndex(id)
    if index < 0:
        return {"message": "Erro ao listar carteira: cliente não encontrado!"}, 500
    
    return {"stockList": clients[index]["stockList"]}, 200


@app.route("/add-stock-to-my-quote-list", methods=["POST"])
def addStockToMyQuoteList():
    global clients, stocks
    content = request.get_json(silent=True)
    userId = content["userId"]
    stockCode = content["stockCode"]

    indexClient = findClientIndex(userId)
    indexStock = findStockIndex(stockCode)

    if indexClient < 0:
        return {"message": "Erro ao adicionar ação as cotações: cliente não encontrado!"}, 500
    if indexStock < 0:
        return {"message": "Erro ao adicionar ação as cotações: ação não encontrada!"}, 500

    clients[indexClient]["quoteList"].append(stocks[indexStock])
    return {"message": "A ação {0} foi adicionada à sua lista de cotações".format(stockCode)}, 200


@app.route("/remove-stock-to-my-quote-list", methods=["POST"])
def removeStockToMyQuoteList():
    global clients
    content = request.get_json(silent=True)
    userId = content["userId"]
    stockCode = content["stockCode"]

    indexClient = findClientIndex(userId)
   
    if indexClient < 0:
        return {"message": "Erro ao adicionar ação as cotações: cliente não encontrado!"}, 500

    if len(clients[indexClient]["quoteList"]) == 0:
        return {"message": "Erro ao remover ação as cotações: sua lista está vazia!"}, 500

    indexStock = findStockInQuoteListIndex(stockCode, clients[indexClient]["quoteList"])

    if indexStock < 0:
        return {"message": "Erro ao remover ação da sua lista de cotações: ação não encontrada!"}, 500

    del clients[indexClient]["quoteList"][indexStock]
    return {"message": "A ação {0} foi removida da sua lista de cotações".format(stockCode)}, 200

@app.route("/listen-buy-stock/<id>", methods=["GET"])
def listenBuyStock(id):
    global bookBuy
    def stream(id):
        global bookBuy
        orderIndex = findOrderBuyIndex(id)
        newOrdersSell = bookBuy[orderIndex]["announcer"].listen()  # returns a queue.Queue
        while True:
            orderToExecute = newOrdersSell.get()  # blocks until a new message arrives
            yield orderToExecute

    return flask.Response(stream(id), mimetype="text/event-stream")

@app.route("/listen-sell-stock/<id>", methods=["GET"])
def listenSellStock(id):
    global bookSell
    def stream(id):
        global bookSell
        orderIndex = findOrderSellIndex(id)
        newOrdersBuy = bookSell[orderIndex]["announcer"].listen()  # returns a queue.Queue
        while True:
            orderToExecute = newOrdersBuy.get()  # blocks until a new message arrives
            yield orderToExecute

    return flask.Response(stream(id), mimetype="text/event-stream")

def trySellStock(orderToExecute, stock):
    global bookBuy
    clientSellerIndex = findClientIndex(orderToExecute["userId"])
    for orderOnBookBuy in bookBuy:
        if(orderOnBookBuy["code"] == orderToExecute["code"] and orderOnBookBuy["quantity"] >= orderToExecute["quantity"] 
        and orderOnBookBuy['price'] == orderToExecute["price"]):
            clientBuyerIndex = findClientIndex(orderOnBookBuy["userId"])
            print(int(orderOnBookBuy["quantity"]), int(orderToExecute["quantity"]))
            if(int(orderOnBookBuy["quantity"]) < int(orderToExecute["quantity"])):
                stock["quantity"] = int(orderToExecute["quantity"]) - int(orderOnBookBuy["quantity"])
                # se for igual a quantidade total possuida   
            elif(int(orderOnBookBuy["quantity"]) == int(orderToExecute["quantity"])):
                indexStock = findStockIndex(orderToExecute["code"])
                clients[clientSellerIndex]["stockList"].remove(stock)
                clients[clientSellerIndex]["quoteList"].remove(stocks[indexStock])
                bookSell.remove(orderToExecute)

            else:
                return -1
            
            # atualiza cliente comprador
            indexStock = findStockIndex(orderToExecute["code"])
            stockBought = {"code": orderToExecute["code"], "price": orderToExecute["price"], "quantity": orderOnBookBuy["quantity"]}
            
            # procura se o stock já está na lista do cliente
            oldStockBuyer = findStockInMyWallet(stockBought["code"], clients[clientBuyerIndex]["stockList"])
            if oldStockBuyer != None:
                oldStockBuyer["price"] = ((float(oldStockBuyer["quantity"]) * float(oldStockBuyer["price"])) + (float(stockBought["quantity"]) * float(stockBought["price"]))) / (int(oldStockBuyer["quantity"]) + int(stockBought["quantity"]))
                oldStockBuyer["quantity"] = int(oldStockBuyer["quantity"]) + int(stockBought["quantity"])
            else:
                clients[clientBuyerIndex]["stockList"].append(stockBought)
                clients[clientBuyerIndex]["quoteList"].append(stocks[indexStock])
            
            bookBuy.remove(orderOnBookBuy)

            msg = format_sse(data="Ordem de compra de {0}x {1} por {2} foi executada com sucesso".format(orderOnBookBuy["quantity"], orderOnBookBuy["code"], orderOnBookBuy["price"]), event="listenBuy")
            orderOnBookBuy["announcer"].announce(msg=msg)
            return None
    return orderToExecute

def tryBuyStock(orderToExecute):
    global bookSell
    stockAddSucess = 0
    clientBuyerIndex = findClientIndex(orderToExecute["userId"])
    clientSellerIndex = None
    for order in bookSell:
        if(order["code"] == orderToExecute["code"] and order["quantity"] >= orderToExecute["quantity"] 
        and order['price'] == orderToExecute["price"]):
            print(order, orderToExecute)
            clientSellerIndex = findClientIndex(order["userId"])
            # procura se o stock já está na lista do cliente comprador
            oldStockBuyer = findStockInMyWallet(order["code"], clients[clientBuyerIndex]["stockList"])
            if(oldStockBuyer != None):
                oldStockBuyer["price"] = ((float(oldStockBuyer["quantity"]) * float(oldStockBuyer["price"])) + (float(orderToExecute["quantity"]) * float(orderToExecute["price"]))) / (int(oldStockBuyer["quantity"]) + int(orderToExecute["quantity"]))
                oldStockBuyer["quantity"] = int(oldStockBuyer["quantity"]) + int(orderToExecute["quantity"])
            # se for stock nova, adiciona pela primeira vez
            else:
                indexStock = findStockIndex(orderToExecute["code"])
                clients[clientBuyerIndex]["stockList"].append({"code": orderToExecute["code"], "quantity": orderToExecute["quantity"], "price": orderToExecute["price"]})
                clients[clientBuyerIndex]["quoteList"].append(stocks[indexStock])
            
            # desconta quantidade comprada da ordem de venda se ainda sobrar quantidade para vender
            if orderToExecute["quantity"] < order["quantity"]:
                order["quantity"] = int(order["quantity"]) - int(orderToExecute["quantity"])
                stockToReduce = findStockInMyWallet(order["code"], clients[clientSellerIndex]["stockList"])
                stockToReduce["quantity"] -= int(orderToExecute["quantity"])
            # senão deleta toda a ordem de venda
            else:
                bookSell.remove(order)
                stockToRemove = findStockInMyWallet(order["code"], clients[clientSellerIndex]["stockList"])
                clients[clientSellerIndex]["stockList"].remove(stockToRemove)
                # atualiza cliente vendedor
                indexStock = findStockIndex(orderToExecute["code"])
                clients[clientSellerIndex]["quoteList"].remove(stocks[indexStock])

            bookBuy.remove(orderToExecute)

            msg = format_sse(data="Ordem de venda de {0}x {1} por {2} foi executada com sucesso".format(order["quantity"], order["code"], order["price"]), event="listenSell")
            order["announcer"].announce(msg=msg)
            return orderToExecute
    return None

def findStockInMyWallet(code, myWallet):
    for index, stock in enumerate(myWallet):
        if stock['code'] == code:
            return stock
    else:
        return None

def findClientIndex(id):
    global clients
    for index, item in enumerate(clients):
        if item['id'] == id:
            return index
    else:
        return -1

def findStockIndex(code):
    global stocks
    for index, item in enumerate(stocks):
        if item["code"] == code:
            return index
    else:
        return -1

def findStockInQuoteListIndex(code, quoteList):
    for index, item in enumerate(quoteList):
        if item["code"] == code:
            return index
    else:
        return -1

def findOrderBuyIndex(id):
    global bookBuy
    for index, item in enumerate(bookBuy):
        if item["id"] == id:
                return index
        else:
            return -1

def findOrderSellIndex(id):
    global bookSell
    for index, item in enumerate(bookSell):
        if item["id"] == id:
                return index
        else:
            return -1

