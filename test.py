from joblib import PrintTime
from matplotlib import style
from matplotlib.style import available
from numpy import size
import decimal
from regex import P
import requests
import mysql.connector
from bs4 import BeautifulSoup
import threading
sem = threading.Semaphore()

import json
import re
import pyperclip

mydb = mysql.connector.connect(
    host="171.22.24.215",
    user="root",
    db="annenkovstore",
    password="kaskas"
)

mycursor = mydb.cursor(dictionary=True)


def Diff(first, second):
    return list(set(first) - set(second))

def updateDb(productId, price, totalPrice, sizes):
    sem.acquire()
    try:
        print(productId)
        mycursor.execute("select size from size join linkSizeAndProduct lsp on size.sizeId = lsp.sizeId where productId = %s", [productId])
        beforeSizes = mycursor.fetchall()
        beforeSizes = list(map(lambda x: x["size"], beforeSizes))
        print(beforeSizes)

        print(Diff(sizes, beforeSizes)) #sizes to insert
        print(Diff(beforeSizes, sizes)) #sizes to update available = 0
        sizesToInsert = Diff(sizes, beforeSizes)
        sizezToUpdate = Diff(beforeSizes, sizes)

        if(len(sizesToInsert)):
          for size in sizesToInsert:
              mycursor.execute("SELECT sizeId from size where size = %s", [size])
              sizeId = mycursor.fetchall()
              mycursor.execute("INSERT INTO linkSizeAndProduct(sizeId, productId) VALUES (%s, %s)", [sizeId[0]['sizeId'], productId])
              mydb.commit()

        if(len(sizezToUpdate)):
          for size in sizezToUpdate:
              mycursor.execute("SELECT sizeId from size where size = %s", [size])
              sizeId = mycursor.fetchall()
              mycursor.execute("UPDATE linkSizeAndProduct SET available = 0 where sizeId = %s AND productId = %s", [sizeId[0]['sizeId'], productId])
              mydb.commit()

        mycursor.execute("UPDATE products SET price=%s, totalPrice = %s where productId = %s", [price, totalPrice, productId])
        mydb.commit()
        sem.release()
    except Exception as e: 
        print("error")
        print(productId)
        print(e)
        sem.release()


def extractPrice(price, sep='.'):
  r = re.compile(r'(\d[\d.,]*)\b')
  if(sep == ','):
    extPrice = [x for x in re.findall(r, price)][0]
    if(extPrice.find('.') != -1):
      extPrice = int(extPrice.split('.')[0]) + 1
  else:
    extPrice = [x.replace('.', '') for x in re.findall(r, price)][0]
    if(extPrice.find(',') != -1):
      extPrice = int(extPrice.split(',')[0]) + 1
  
  return extPrice

adiheaders = {
    'origin': 'www.adidas.com.tr',
    'cookie': '',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'
}

s = requests.Session()
URL = 'https://www.adidas.com.tr/tr/eq19-kosu-ayakkabisi/H00924.html'
# styleNum = URL.split('/')[-1]
styleNum = URL.split('/')[-1]
styleNum = re.findall("^(.*?)\.html", styleNum)[0]
print(styleNum)
page = s.get(URL, headers=adiheaders, timeout=0.3)

soup = BeautifulSoup(page.content, "html.parser")
scripts = soup.find_all("script")
details = ''
for script in scripts:
    if (script.text.find("@context") != -1):
      details = script.text
# print(details)
details = json.loads(details)
print(details)
sizes = requests.get("https://www.adidas.com.tr/api/products/"+ styleNum + "/availability?sitePath=en", headers=adiheaders)
filtered = list(filter(lambda var: var["availability_status"] == "IN_STOCK", sizes.json()["variation_list"]))
mappedSizes = list(map(lambda x: x["size"], filtered))
price = extractPrice(str(details["offers"]["price"]))

