from flask import Flask;
from update import df_loops
from flask import request

app = Flask(__name__)

@app.route("/update")
def hello_world():
    updateproduct = df_loops(request.args.get('productId'))
    return updateproduct