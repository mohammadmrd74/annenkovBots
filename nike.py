import requests
import mysql.connector
from bs4 import BeautifulSoup
import threading
sem = threading.Semaphore()
import time
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

def insertIntoDb(link, title, price, totalPrice, styleNum, availableSizesInNumber, mappedImages):
    print(link)
    sem.acquire()
    try:
        mycursor.execute("SELECT id from brands where brandName = 'nike'")
        brandId = mycursor.fetchall()
        sql = "INSERT INTO products (title, price, totalPrice, styleNumber, currencyId, brandId, mainAndCategoryId, typeId, linkId, link, colorId, sColorId) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        val = (title, price, totalPrice, styleNum, 1, brandId[0]['id'], 4, 1, 1, link,3, 2)
        mycursor.execute(sql, val)
        mydb.commit()

        mycursor.execute("SELECT LAST_INSERT_ID() as insertedId")
        insertedId = mycursor.fetchall()
        insertedId = insertedId[0]['insertedId']
        for size in availableSizesInNumber:
            mycursor.execute("SELECT sizeId from size where size = %s", [size])
            sizeId = mycursor.fetchall()
            mycursor.execute("INSERT INTO linkSizeAndProduct(sizeId, productId) VALUES (%s, %s)", [sizeId[0]['sizeId'], insertedId])
            mydb.commit()
        
        for image in mappedImages:
            mycursor.execute("INSERT INTO images(imageUrl, productId) VALUES (%s, %s)", [image, insertedId])
            mydb.commit()

        mycursor.execute("UPDATE links SET inserted=%s where id = %s", [1, 1])
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

mydb = mysql.connector.connect(
    host="171.22.24.215",
    user="root",
    db="annenkovstore",
    password="kaskas"
)
print(mydb)

mycursor = mydb.cursor(dictionary=True)

mycursor.execute("select * from links where id = 857")
import os
links = mycursor.fetchall()
path = os.path.abspath(os.getcwd())
f = open(path + "/ttt.txt", "a")

s = requests.Session()

headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
        'cookie': '',
        'origin': 'https://www.nike.com'
        }
print('https://www.nike.com/tr/t/air-zoom-rival-fly-3-yol-yar%C4%B1%C5%9F-ayakkab%C4%B1s%C4%B1-sTqqkg/CT2405-358')
print(links[0]['link'])
print('https://www.nike.com/tr/t/air-zoom-rival-fly-3-yol-yar%C4%B1%C5%9F-ayakkab%C4%B1s%C4%B1-sTqqkg/CT2405-358' == links[0]['link'])
URL = links[0]['link']
page = s.get(URL, headers=headers)
soup = BeautifulSoup(page.content, "html.parser")
# f.write(page.text)

if (soup.find("li", class_="description-preview__style-color ncss-li") == None):
    print('first try')
    time.sleep(2)
    s = requests.Session()
    page = s.get(URL, headers=headers)
    soup = BeautifulSoup(page.content, "html.parser")
    scripts = soup.find_all("script")
    if (soup.find("li", class_="description-preview__style-color ncss-li") == None):
        print('second try')
        time.sleep(2)
        s = requests.Session()
        page = s.get(URL, headers=headers)
        soup = BeautifulSoup(page.content, "html.parser")
        scripts = soup.find_all("script")
        if (soup.find("li", class_="description-preview__style-color ncss-li") == None):
            print('third try')
            time.sleep(2)
            s = requests.Session()
            page = s.get(URL, headers=headers)
            soup = BeautifulSoup(page.content, "html.parser")
            scripts = soup.find_all("script")
            if (soup.find("li", class_="description-preview__style-color ncss-li") == None):
                print('forth try')
                time.sleep(2)
                s = requests.Session()
                page = s.get(URL, headers=headers)
                soup = BeautifulSoup(page.content, "html.parser")
                scripts = soup.find_all("script")

details = ''
for script in scripts:
    if(script.text.find("INITIAL_REDUX_STATE") != -1):
        details = script.text
fstyleNum = soup.find("li", class_="description-preview__style-color ncss-li").text.strip().replace('Stil: ', '')


styleNum = fstyleNum
details = details.replace('window.INITIAL_REDUX_STATE=', '')
details = details[0:-1]
# pyperclip.copy(details)
jsonDetails = json.loads(details)
if(fstyleNum not in jsonDetails['Threads']['products']):
    print(fstyleNum)
    urlst = URL.strip().split('/')[-1]
    if(urlst in jsonDetails['Threads']['products']):
        styleNum = urlst
    else:
        styleNum = list(jsonDetails['Threads']['products'].keys())[0]
print('123123123')

images = jsonDetails['Threads']['products'][styleNum]['nodes'][0]['nodes']

mappedImages = list(map(lambda x: x["properties"]['squarishURL'].replace('t_default', 't_PDP_1280_v1/f_auto,q_auto:eco') if ('squarishURL' in x["properties"]) else None, images))
mappedImages = list(filter(None, mappedImages))
price = jsonDetails['Threads']['products'][styleNum]['currentPrice']
fullPrice = jsonDetails['Threads']['products'][styleNum]['fullPrice']
allSizes = jsonDetails['Threads']['products'][styleNum]['skus']
availableSizes = jsonDetails['Threads']['products'][styleNum]['availableSkus']
title = jsonDetails['Threads']['products'][styleNum]['title']
availableSizesInNumber = []
for size in allSizes:
    for asize in availableSizes:
        if(size['skuId'] == asize['id']):
            availableSizesInNumber.append(size['localizedSize'])
price = extractPrice(str(price), ',')
fullPrice = extractPrice(str(fullPrice), ',')
print(price)
print(fullPrice)

# insertIntoDb(URL, title, fullPrice, price, fstyleNum, availableSizesInNumber, mappedImages)

