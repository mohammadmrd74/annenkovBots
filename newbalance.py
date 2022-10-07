
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
        mycursor.execute("SELECT id from brands where brandName = 'asics'")
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




print("\n\n******** NEWBALANCE *********\n\n")

s = requests.Session()
# URL = "https://www.newbalance.com.tr/urun/new-balance-997-410916.html"
URL = "https://www.newbalance.com.tr/urun/new-balance-680-1399"
page = s.get(URL.strip())
soup = BeautifulSoup(page.content, "html.parser")
print(soup)
product = soup.find_all("h1", class_="product-name")
title = product[0].text.strip()
price = extractPrice(soup.find("span", class_="price-value").text.strip())
morePrice= price
if(soup.find(id="plhSatisIlkFiyat").text):
    morePrice = extractPrice(soup.find(id="plhSatisIlkFiyat").text.strip())
    
cloudId = URL.strip().split("/")[-1]
cloudId = cloudId.split("-")[-1].replace(".html", "")
styleNum = soup.find("div", class_="ems-prd-sort-desc").text.strip()
tags = soup.find_all("ul", class_="swiper-wrapper slide-wrp")[0]
images = tags.find_all("a")
mappedImages = []
for image in images:
    try:
        if(image["data-large"]):
            mappedImages.append(image["data-large"])
    except KeyError:
        continue

sizes = page = s.get("https://www.newbalance.com.tr/usercontrols/urunDetay/ajxUrunSecenek.aspx?urn="+cloudId+"&fn=dty&std=True&type=scd1&index=0&objectId=ctl00_u23_ascUrunDetay_dtUrunDetay_ctl00&runatId=urunDetay&scd1=0&lang=tr-TR")
soup = BeautifulSoup(page.content, "html.parser")
realSizes = []
sizes = soup.find_all("a")
for size in sizes:
    try:
        if(size["class"] and size["class"].count("stokYok") != 0):     
            continue
        else:
            realSizes.append(size.text.strip())
    except KeyError:
        realSizes.append(size.text.strip())

print(price)
print(morePrice)