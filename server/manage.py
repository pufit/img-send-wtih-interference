from server import Server
from flask import *
from config import *


app = Flask(__name__)
app.config.from_object(Configuration)

if __name__ == '__main__':
    server = Server()
    server.start()

    app.run(IP, HTTP_PORT)
