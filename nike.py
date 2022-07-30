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
    host="171.22.24.215", user="root", db="annenkovstore", password="kaskas"
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
    print(link)
    sem.acquire()
    try:
        mycursor.execute("SELECT id from brands where brandName = 'nike'")
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

        mycursor.execute("SELECT LAST_INSERT_ID() as insertedId")
        insertedId = mycursor.fetchall()
        insertedId = insertedId[0]["insertedId"]
        for size in availableSizesInNumber:
            mycursor.execute("SELECT sizeId from size where size = %s", [size])
            sizeId = mycursor.fetchall()
            mycursor.execute(
                "INSERT INTO linkSizeAndProduct(sizeId, productId) VALUES (%s, %s)",
                [sizeId[0]["sizeId"], insertedId],
            )
            mydb.commit()

        for image in mappedImages:
            mycursor.execute(
                "INSERT INTO images(imageUrl, productId) VALUES (%s, %s)",
                [image, insertedId],
            )
            mydb.commit()

        mycursor.execute("UPDATE links SET inserted=%s where id = %s", [1, 1])
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


mydb = mysql.connector.connect(
    host="171.22.24.215", user="root", db="annenkovstore", password="kaskas"
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
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
    "cookie": 'AnalysisUserId=2.19.196.126.256951659079848165; feature_enabled__as_nav_rollout=true; audience_segmentation_performed=true; AKA_A2=A; geoloc=cc=IR,rc=,tp=vhigh,tz=GMT+3.50,la=35.67,lo=51.42; bm_sz=C1C68DE8A29B46FB8D5CA39AD730EA93~YAAQfsQTAqRf2iKCAQAAp3XdSBAOjH7sVJXEs5miW5fAImFArgiXElDh0Sc1VXnyA6xsCqbUw16a+ejvy0LGlj0PfICFW6gHykKdNit/YVNGWF+2wAnRf76nUX4KDhK2dGCgy/pi2GAIyWcFT+G6ntMGVf6dfM/DHKYn160nWHEPzx1hsiYk6hJXBLEkx1fDD7zk8HVvx0xRN9QOw7Zljv7vfUClQv24qH8eWc/jq4XQ1k9U7O8fdzG0W/bevxyB0jEg7sUCjccA85EzCVoX6W8gCnD+ijZ9svUfe0hNBq3TJ5cnnYk7SxBq/jGlqN219U7d2uEOQMhjDQXuP4ELqZL8kA5DeQjaeBdoOd2EOMa4rRTBdBIQhA+KTxQ8EDzs66hnW1ib26VOsDnB8IY=~3290182~3422261; guidS=38eb665d-e175-415a-fc4d-4db58995f2f5; guidU=c28b6939-84d9-4d4c-84bc-284e5c1e07cf; NIKE_COMMERCE_COUNTRY=TR; NIKE_COMMERCE_LANG_LOCALE=tr_TR; s_ecid=MCMID%7C00078281668325488764570501589095094480; AMCVS_F0935E09512D2C270A490D4D%40AdobeOrg=1; AMCV_F0935E09512D2C270A490D4D%40AdobeOrg=1994364360%7CMCMID%7C00078281668325488764570501589095094480%7CMCAID%7CNONE%7CMCOPTOUT-1659087049s%7CNONE%7CvVersion%7C3.4.0; ak_bmsc=426AA54AB58D4930B1912B5F4F4265A4~000000000000000000000000000000~YAAQfsQTAqNg2iKCAQAA4nndSBCSwwO+6axi6dcDcu/pIO2RkGIXZU0uuOXZVg1obQri1MuxS2Q/V1WL4l4GWLtl/K888M/uCCkVVv5V4CaUpU8dkwK2+hYABv3hVM+3bAi2LtzeHOE1Os4ThsYYJBhvmczrF+t/EuK4UFK3FLJvL3OkEbFjFaa2BxPnDUHu7mbK7kJTeT8D2MtNc0U+5R7Ryub99FahCBAgoahoL9wqL7HL7ZjEi+DkVBdr803nYAuU0uueJd8GzZ/8ZaGLcMFGvyHf1Rt+6UJed0Kn/vySGVSwVJjdZlWxcfkOdnuqqO9dMgct95T8SQ1dJE8UxUXTuGLdAIxHlDe9HNM5CyCDvwVH2xetpUlYn0Dcd8RyTR14Zuf+McAP28PFHMkwfpl6bQwpp7hefqfiS7JmgOtZQqfa4cu/siI5dPeXC36fOo3f3Xl6aGd0fKYPbAyn/1/uTLrhgMq6ieR673Kdkamb69nDU/RB; RES_TRACKINGID=27309745747803; RES_SESSIONID=594658110776082; ResonanceSegment=1; anonymousId=7DD74E1DD1BB61FCC6FFF08698D260B5; ppd=pdp|nikecom>pdp>kd%20trey%205%20x; bm_sv=780B22F9C2976F46AE77DF28295C2171~YAAQfsQTAt3K3CKCAQAAAOXoSBCTrFlviAHitDgIib/0CyLapcgM/nr0PQgAfkqc5CVJZwdzBIqiIWRfy3ZpVw8WrgPFfPLhvkhgr3iTtfu8RBn+iW+JCt3joO5gYRbvSyNI95NMQuetTGxpuKTZ3/YmaE1T2IH5XDoFDNlv3cXAX3M9qv7bV9az144Lte1+HYI2TwJZP3ugLnZ/rRXDb1+mXl5Fi8NNC3GWOjwExBHo8SUgcCZl3eK9+nSzFcw=~1; _abck=1B2682DED7212205EAFEB69F39FC665A~-1~YAAQDt46F8BkuSCCAQAAieroSAhQuA5qxU9a36WqHWF5SW3nZjoyXKB66+zpN5viF6ncIwu1eGkoJzHRbBM67Bu9v0XMJwRUPmCymGtuAKuSGwKtofYGw0KIv9hM5zDqqZyG+V8xYqvQSzmxhhRlfr8ParChQ97gUjUMQ3OitwfexhO+HGimxnHvdrMnsX/KlJzdmz8heVWrIIqK+7hadvH4UW+IzU/WFk3lbynkhU3R2A76nY2m+yB7Gf8+nY9ELx7QFhQLexd2/Rc7tIHq5dmS8UpCk2qQDtK+NMIHwmqW18f/U5b04HPB2nvN7VqV0Ik9qNSiljBh6/uf22KVRDEC6bPntItl+8sjVkygfnP2rdAOK9KZ5m9uMszeiNh8F+zYBDYfzgLvVAYtBZjStMqqey/PcX3A36y8bORfPIMVbI0A3qBgUChNHjHvHp4cLfxhFKBsTVV/u1UF8zGS1UN/Yy8acFAZV5o0PS3pvQ2uy6GY31gd+/f0UtoLuZ7hnM98R6JRKxkGHwJknpCorvI=~-1~-1~-1; RT="z=1&dm=nike.com&si=4d9dbf13-532c-4226-bdb6-4bd179df7cc8&ss=l665az2f&sl=5&tt=kq1&bcn=%2F%2F684dd32d.akstat.io%2F&ld=g3qc&ul=g55s"',
    "origin": "https://www.nike.com/tr",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
}

URL = "https://www.nike.com/tr/t/kd-trey-5-10-basketbol-ayakkab%C4%B1s%C4%B1-4lz95M/DD9538-008"
page = s.get(URL, headers=headers)
soup = BeautifulSoup(page.content, "html.parser")


mains = soup.find("script", id="__NEXT_DATA__").text.strip()
pyperclip.copy(mains)

fstyleNum = (
    soup.find("li", class_="description-preview__style-color ncss-li")
    .text.strip()
    .replace("Stil: ", "")
)

# pyperclip.copy(details)
jsonDetails = json.loads(mains)["props"]["pageProps"]["initialState"]
styleNum = fstyleNum
if fstyleNum not in jsonDetails["Threads"]["products"]:
    print(fstyleNum)
    urlst = URL.strip().split("/")[-1]
    if urlst in jsonDetails["Threads"]["products"]:
        styleNum = urlst
    else:
        styleNum = list(jsonDetails["Threads"]["products"].keys())[0]
print("123123123")

images = jsonDetails["Threads"]["products"][styleNum]["nodes"][0]["nodes"]

mappedImages = list(
    map(
        lambda x: x["properties"]["squarishURL"].replace(
            "t_default", "t_PDP_1280_v1/f_auto,q_auto:eco"
        )
        if ("squarishURL" in x["properties"])
        else None,
        images,
    )
)
mappedImages = list(filter(None, mappedImages))
price = jsonDetails["Threads"]["products"][styleNum]["currentPrice"]
fullPrice = jsonDetails["Threads"]["products"][styleNum]["fullPrice"]
allSizes = jsonDetails["Threads"]["products"][styleNum]["skus"]
availableSizes = jsonDetails["Threads"]["products"][styleNum]["availableSkus"]
title = jsonDetails["Threads"]["products"][styleNum]["title"]
availableSizesInNumber = []
for size in allSizes:
    for asize in availableSizes:
        if size["skuId"] == asize["id"]:
            availableSizesInNumber.append(size["localizedSize"])
price = extractPrice(str(price), ",")
fullPrice = extractPrice(str(fullPrice), ",")
print(title)
print(availableSizesInNumber)
print(mappedImages)

# insertIntoDb(URL, title, fullPrice, price, fstyleNum, availableSizesInNumber, mappedImages)
