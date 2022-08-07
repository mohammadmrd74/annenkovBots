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
    host="171.22.24.215", user="anenkov", db="annenkovstore", password="anenanenkovkov"
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

def insertIntoDb(link, title, price, totalPrice, styleNum, availableSizesInNumber, mappedImages):
    sem.acquire()
    try:
        mycursor.execute("SELECT id from brands where brandName = 'timberland'")
        brandId = mycursor.fetchall()
        sql = "INSERT INTO products (title, price, totalPrice, styleNumber, currencyId, brandId, mainAndCategoryId, typeId, linkId, link, colorId, sColorId) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        val = (title, price, totalPrice, styleNum, 1, brandId[0]['id'], 4, 1, 1, link,3, 2)
        mycursor.execute(sql, val)
        mydb.commit()

        # mycursor.execute("SELECT LAST_INSERT_ID() as insertedId")
        # insertedId = mycursor.fetchall()
        # insertedId = insertedId[0]['insertedId']
        # for size in availableSizesInNumber:
        #     mycursor.execute("SELECT sizeId from size where size = %s", [size])
        #     sizeId = mycursor.fetchall()
        #     mycursor.execute("INSERT INTO linkSizeAndProduct(sizeId, productId) VALUES (%s, %s)", [sizeId[0]['sizeId'], insertedId])
        #     mydb.commit()
        
        # for image in mappedImages:
        #     mycursor.execute("INSERT INTO images(imageUrl, productId) VALUES (%s, %s)", [image, insertedId])
        #     mydb.commit()

        # mycursor.execute("UPDATE links SET inserted=%s where id = %s", [1, 1])
        mydb.commit()
        sem.release()
    except Exception as e: 
        print("error")
        print(link)
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



URL = "https://www.adidas.com.tr/tr/lite-racer-rebold-ayakkabi/GY5980.html"

print("\n\n******** timberland *********\n\n")
headers = {
'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
'Cookie': ''
}


s = requests.Session()
URL =  "https://www.timberland.com.tr/greenstride-solar-wave-lt-kadin-yuruyus-ayakkabisi-p_127264"
page = s.get(URL.strip())
soup = BeautifulSoup(page.content, "html.parser")

images = soup.find("div", class_="main-gallery").find_all("img", class_="image-blur")
mappedImages = []
for image in images:
    try:
        if(image["src"]):
            mappedImages.append(image["data-image"])
    except KeyError:
            continue


title = soup.find("h1", class_="p-name").text.strip()
# styleNum = soup.find("span", class_="sk-model-alt-title").text.strip()

npirce = ''
oprice = ''
if(soup.find("span", class_="one-price")): 
  oprice = extractPrice(soup.find("span", class_="one-price").text.strip())
  nprice = oprice
if(soup.find("span", class_="new-price")):
  nprice = extractPrice(soup.find("span", class_="new-price").text.strip())
  oprice = extractPrice(soup.find("span", class_="old-price").text.strip())

print(nprice)
print(oprice)

mappedSizes = []
sizes = soup.find("div", class_="size-options").find_all("a", class_="")
for size in sizes:
    try:
        mappedSizes.append(size.text.strip())
    except KeyError:
        continue
title = title.replace("Ayakkabı", "").replace("Spor", "").replace("Erkek", "").replace("Nubuk", "").replace("Yeşil", "").replace("Koyu", "").replace("Kadin", "")
# insertIntoDb("https://www.timberland.com.tr/union-wharf-20-ek-erkek-tekne-ayakkabisi-p_127348", title, oprice, nprice, "", mappedSizes, mappedImages)

