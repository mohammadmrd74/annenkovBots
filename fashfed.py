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
        mycursor.execute("SELECT id from brands where brandName = 'salomon'")
        brandId = mycursor.fetchall()
        sql = "INSERT INTO products (title, price, totalPrice, styleNumber, currencyId, brandId, mainAndCategoryId, typeId, linkId, link, colorId, sColorId) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        val = (title, price, totalPrice, styleNum, 1, brandId[0]['id'], 4, 1, 1, link,3, 2)
        mycursor.execute(sql, val)

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




print("\n\n******** FASHFED *********\n\n")
headers = {
'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
'Cookie': ''
}

s = requests.Session()
URL = "https://www.fashfed.com/urun/nike-air-force-1-07-erkek-beyaz-spor-ayakkabi-cw2288-7/?integration_renk=111&integration_beden=42%2C5"
page = s.get(URL.strip())
soup = BeautifulSoup(page.content, "html.parser")

images = soup.find_all("img", class_="js-fancybox-lg")
mappedImages = []
for image in images:
    try:
        if(image["src"]):
            mappedImages.append(image["src"])
    except KeyError:
            continue


title = soup.find("div", class_="product__info--title").text.strip()
nprice = extractPrice(soup.find("span", class_="price__new").text.strip(), '.')
oprice = soup.find("span", class_="price__old")
if (oprice):
    oprice = extractPrice(oprice.text.strip(), '.')
else:
    oprice = nprice
styleNum = soup.find("div", class_="product__collapse--content").find("p").text.replace('Ürün Kodu:', '').replace(" ", "").replace("\n", "").strip()
mappedSizes = []
scripts = soup.find("select", class_="js-variants-select").find_all("option")
for size in scripts:
    try:
        if(size["value"]):
            mappedSizes.append(size["value"].replace(",",'.'))
    except KeyError:
            continue
# scripts = json.loads(scripts[scripts.find('{'):(scripts.find(';'))])
# filtered = list(filter(lambda var: var["stokAdedi"] > 0 and var["ekSecenekTipiTanim"] == "Beden", scripts["productVariantData"]))
# sizes = list(map(lambda x: x["tanim"][x["tanim"].find('(')+1:x["tanim"].find(')')], filtered))
print(mappedImages)
print(title.replace("Erkek", "").replace("Beyaz", "").replace("Spor", "").replace("Ayakkabı", "").strip())
print(oprice)
print(nprice)
print(styleNum)
print(mappedSizes)