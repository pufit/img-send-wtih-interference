from server import Server
from flask import *
from config import *
from werkzeug.utils import secure_filename
from _thread import start_new_thread
import os

app = Flask(__name__)
app.config.from_object(Configuration)


@app.route('/', methods=['POST', 'GET'])
def main():
    if request.method == 'GET':
        return render_template('base.html', name=session.get('name'))
    file = request.files['file']
    name = secure_filename(request.form.get('name'))
    if not os.path.exists('solutions/' + name):
        os.mkdir('solutions/' + name)
    file.save('solutions/' + name + '/' + name + '.py')
    with open('solutions/' + name + '/input', 'wb') as f:
        f.write(b'')
    with open('solutions/' + name + '/output', 'wb') as f:
        f.write(b'')
    session['name'] = name
    return render_template('base.html', status='OK', name=session.get('name'))


if __name__ == '__main__':
    start_new_thread(app.run, (IP, HTTP_PORT))
    server = Server()
    server.run()
