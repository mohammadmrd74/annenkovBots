from flask import Flask
from update import df_loops
from flask import request

app = Flask(__name__)

@app.route("/update")
def hello_world():
    print(124124, request.args.get('productId'))
    updateproduct = df_loops(request.args.get('productId'))
    return updateproduct

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)