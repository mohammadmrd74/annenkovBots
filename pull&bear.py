import requests
import mysql.connector
from bs4 import BeautifulSoup
import threading
from urllib import parse
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
        mycursor.execute(
            "select size from size join linkSizeAndProduct lsp on size.sizeId = lsp.sizeId where productId = %s",
            [productId],
        )
        beforeSizes = mycursor.fetchall()
        beforeSizes = list(map(lambda x: x["size"], beforeSizes))
        print(beforeSizes)

        print(Diff(sizes, beforeSizes))  # sizes to insert
        print(Diff(beforeSizes, sizes))  # sizes to update available = 0
        sizesToInsert = Diff(sizes, beforeSizes)
        sizezToUpdate = Diff(beforeSizes, sizes)

        if len(sizesToInsert):
            for size in sizesToInsert:
                mycursor.execute("SELECT sizeId from size where size = %s", [size])
                sizeId = mycursor.fetchall()
                mycursor.execute(
                    "INSERT INTO linkSizeAndProduct(sizeId, productId) VALUES (%s, %s)",
                    [sizeId[0]["sizeId"], productId],
                )
                mydb.commit()

        if len(sizezToUpdate):
            for size in sizezToUpdate:
                mycursor.execute("SELECT sizeId from size where size = %s", [size])
                sizeId = mycursor.fetchall()
                mycursor.execute(
                    "UPDATE linkSizeAndProduct SET available = 0 where sizeId = %s AND productId = %s",
                    [sizeId[0]["sizeId"], productId],
                )
                mydb.commit()

        mycursor.execute(
            "UPDATE products SET price=%s, totalPrice = %s where productId = %s",
            [price, totalPrice, productId],
        )
        mydb.commit()
        sem.release()
    except Exception as e:
        print("error")
        print(productId)
        print(e)
        sem.release()


def insertIntoDb(
    link, title, price, totalPrice, styleNum, availableSizesInNumber, mappedImages
):
    sem.acquire()
    try:
        mycursor.execute("SELECT id from brands where brandName = 'timberland'")
        brandId = mycursor.fetchall()
        sql = "INSERT INTO products (title, price, totalPrice, styleNumber, currencyId, brandId, mainAndCategoryId, typeId, linkId, link, colorId, sColorId) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        val = (
            title,
            price,
            totalPrice,
            styleNum,
            1,
            brandId[0]["id"],
            4,
            1,
            1,
            link,
            3,
            2,
        )
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


def extractPrice(price, sep="."):
    r = re.compile(r"(\d[\d.,]*)\b")
    if sep == ",":
        extPrice = [x for x in re.findall(r, price)][0]
        if extPrice.find(".") != -1:
            extPrice = int(extPrice.split(".")[0]) + 1
    else:
        extPrice = [x.replace(".", "") for x in re.findall(r, price)][0]
        if extPrice.find(",") != -1:
            extPrice = int(extPrice.split(",")[0]) + 1

    return extPrice


print("\n\n******** PULL & BEAR *********\n\n")
headers = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
}


s = requests.Session()
URL = "https://www.pullandbear.com/tr/cekme-kay%C4%B1sl%C4%B1-spor-ayakkab%C4%B1-l11221940?cS=001&pelement=538756268"
urlQuery = dict(parse.parse_qs(parse.urlsplit(URL).query))

# print("https://www.pullandbear.com/itxrest/2/catalog/store/25009521/20309432/category/0/product/" + pelement[0].replace("pelement=", "") + "/detail?languageId=-43&appId=1")

page = s.get(
    "https://www.pullandbear.com/itxrest/2/catalog/store/25009521/20309432/category/0/product/"
    + urlQuery["pelement"][0]
    + "/detail?languageId=-43&appId=1",
    headers=headers,
)
page = page.json()
title = page["nameEn"]

colors = page["bundleProductSummaries"][0]["detail"]["colors"]
media = page["bundleProductSummaries"][0]["detail"]["xmedia"]
color = next(
    item for item in colors if item["id"] ==  urlQuery["cS"][0]
)
media = next(
    item for item in media if item["colorCode"] ==  urlQuery["cS"][0]
)
price = color["sizes"][0]["price"]
oldPrice = color["sizes"][0]["oldPrice"]
if oldPrice == None:
    oldPrice = price
sizes = list(
    filter(
        lambda x: x != "",
        map(
            lambda size: size["name"] if size["visibilityValue"] == "SHOW" else "",
            color["sizes"],
        ),
    )
)


print(title)
print(extractPrice(price[0:-2]+ ',' + price[-2:]))
print(extractPrice(oldPrice[0:-2]+ ',' + oldPrice[-2:]))
print(sizes)
# print(mappedImages)
print(urlQuery["pelement"][0])

images = list(
        map(
            lambda image: "https://static.pullandbear.net/2/photos" + media["path"] + "/" + image["idMedia"] + "1.jpg",
            media["xmediaItems"][0]["medias"],
        ),
    
)

print(images)

