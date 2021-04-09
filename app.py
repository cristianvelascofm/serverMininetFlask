from flask import Flask
from flask_cors import CORS
from flask import request

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})



@app.route('/',methods=['GET'])
def get():
    return 'Este es el Sevidor Mininet'

@app.route('/',methods=['POST'])
def show():
    content = request.json
    print(content);
    aux = 'Nada de nada'
    return aux
    
if __name__ == '__main__':
    app.run(debug=True, host='192.168.56.1')


