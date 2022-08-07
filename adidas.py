
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
        mycursor.execute("SELECT id from brands where brandName = 'adidas'")
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

adiheaders = {
    'origin': 'www.adidas.com.tr',
    'cookie': '',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'
}

print("\n\n******** ADIDAS *********\n\n")
adiheaders = {
  'origin': 'www.adidas.com.tr',
  'cookie': '',
  'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'
}
URL = "https://www.adidas.com.tr/tr/pureboost-jet/GW8591.html"

styleNum = URL.split('/')[-1]
styleNum = re.findall("^(.*?)\.html", styleNum)[0]
print(styleNum)
page = requests.get(URL, headers=adiheaders)
soup = BeautifulSoup(page.content, "html.parser")
scripts = soup.find_all("script")
# for sc in script:
#     print(sc.text, end="\n\n")
# print(scripts)
details = ''
for script in scripts:
  if(script.text.find("@context") != -1):
    details = script.text
pyperclip.copy(details)
details = json.loads(details)
sizes = requests.get("https://www.adidas.com.tr/api/products/"+ styleNum + "/availability?sitePath=en", headers=adiheaders)
filtered = list(filter(lambda var: var["availability_status"] == "IN_STOCK", sizes.json()["variation_list"]))
mappedSizes = list(map(lambda x: x["size"], filtered))
price = extractPrice(str(details["offers"]["price"]))
morePrice = price
if (soup.find("div", class_="gl-price-item--crossed")):
    morePrice = extractPrice(soup.find("div", class_="gl-price-item--crossed").text.strip())
print(morePrice)

insertIntoDb("https://www.adidas.com.tr/tr/ultimashow-ayakkabi/FX3633.html", details["name"].replace('Ayakkabı', ''),price, price, styleNum, mappedSizes, details["image"])


