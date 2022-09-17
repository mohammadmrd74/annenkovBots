from flask import Flask

import mysql.connector
import sys
import os
 
# getting the name of the directory
# where the this file is present.
current = os.path.dirname(os.path.realpath(__file__))
 
# Getting the parent directory name
# where the current directory is present.
parent = os.path.dirname(current)
 
# adding the parent directory to
# the sys.path.
sys.path.append(parent)
from main import df_loops
from flask import request

app = Flask(__name__)
mydb = mysql.connector.connect(
    host="171.22.24.215", user="anenkov", db="annenkovstore", password="anenanenkovkov"
)
mycursor = mydb.cursor(dictionary=True)
@app.route("/update")
def hello_world():
    print(124124, request.args.get('productId'))
    mycursor.execute(
        "select productId, link, website, currencyId from products where deleted = 0 and productId = %s",
        [request.args.get('productId')]
    )
    link = mycursor.fetchall()
    print(2, link)
    try:
        df_loops(link[0])
        return "done"
    except Exception as e:
        return "error"

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=5500)