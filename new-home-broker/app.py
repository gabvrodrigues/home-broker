import queue
import uuid

import flask
from flask_cors import CORS
from flask import request, jsonify

app = flask.Flask(__name__)
CORS(app)

clients = []
stocks = [{"code": "PETR4", "price": 15.87}, {"code": "VALE3", "price": 54.76}, {"code": "MGLU3", "price": 89.90}]
bookBuy = []
bookSell = []


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


announcer = MessageAnnouncer()


def format_sse(data: str, event=None) -> str:
    """Formats a string and an event name in order to follow the event stream convention.

    >>> format_sse(data=json.dumps({'abc': 123}), event='Jackson 5')
    'event: Jackson 5\\ndata: {"abc": 123}\\n\\n'

    """
    msg = f"data: {data}\n\n"
    if event is not None:
        msg = f"event: {event}\n{msg}"
    return msg


@app.route("/ping")
def ping():
    msg = format_sse(data="pong", event="teste")
    announcer.announce(msg=msg)
    # resp = flask.Response("Foo bar baz")
    # resp.headers['Access-Control-Allow-Origin'] = '*'
    # resp.headers['Content-Type'] = 'text/event-stream'
    return {}, 200


@app.route("/connect/<id>", methods=["GET"])
def connect(id):
    global clients
    clients.append({"id": id, "stockList": [], "quoteList": []})
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
    order = {"id": uuid.uuid4(), "userId": content["userId"], "code": content["code"], "quantity": content["quantity"], "price": content["price"]}
    bookBuy.append(order)
    orderId = tryBuyStock(order)
    print(orderId)
    if orderId != None:
        return {"message": "Ordem cadastrada com sucesso! Você será notificado quando a ordem for executada!", "orderId": orderId}, 200
    else:
        return {"message": "Ordem executada com sucesso!", "orderId": orderId}, 200

@app.route("/sell-stock", methods=["POST"])
def sellStock():
    global clients, bookBuy, bookSell
    content = request.get_json(silent=True)
    order = {"id": uuid.uuid4(), "userId": content["userId"], "code": content["code"], "quantity": content["quantity"], "price": content["price"]}
    bookSell.append(order)
    orderId = trySellStock(order)
    
    if orderId != None:
        return {"message": "Ordem cadastrada com sucesso! Você será notificado quando a ordem for executada!", "orderId": orderId}, 200
    else:
        return {"message": "Ordem executada com sucesso!", "orderId": orderId}, 200

@app.route("/show-my-quote-list/<id>", methods=["GET"])
def showMyQuoteList(id):
    global clients
    index = findClientIndex(id)
    if index < 0:
        return {"message": "Erro ao listar cotações: cliente não encontrado!"}, 500
    
    return {"quoteList": clients[index]["quoteList"]}, 200


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
    def stream(id):
        newOrdersSell = announcer.listen()  # returns a queue.Queue
        while True:
            orderToExecute = newOrdersSell.get()  # blocks until a new message arrives
            yield orderToExecute

    return flask.Response(stream(id), mimetype="text/event-stream")

@app.route("/listen-sell-stock/<id>", methods=["GET"])
def listenSellStock(id):
    def stream(id):
        newOrdersBuy = announcer.listen()  # returns a queue.Queue
        while True:
            orderToExecute = newOrdersBuy.get()  # blocks until a new message arrives
            yield orderToExecute

    return flask.Response(stream(id), mimetype="text/event-stream")

@app.route("/listen", methods=["GET"])
def listen():
    def stream():
        messages = announcer.listen()  # returns a queue.Queue
        while True:
            msg = messages.get()  # blocks until a new message arrives
            yield msg

    return flask.Response(stream(), mimetype="text/event-stream")

def trySellStock(orderToExecute):
    global bookBuy
    for order in bookBuy:
         if(order["code"] == orderToExecute["code"] and order["quantity"] >= orderToExecute["quantity"] 
            and order['price'] == orderToExecute["price"]):
            msg = format_sse(data="Ordem Executada com sucesso", event="teste")
            announcer.announce(msg=msg)
            return None
    return orderToExecute["id"]

def tryBuyStock(orderToExecute):
    global bookSell
    for order in bookSell:
         if(order["code"] == orderToExecute["code"] and order["quantity"] >= orderToExecute["quantity"] 
            and order['price'] == orderToExecute["price"]):
            msg = format_sse(data="Ordem Executada com sucesso", event="teste")
            announcer.announce(msg=msg)
            return None
    return orderToExecute["id"]

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
