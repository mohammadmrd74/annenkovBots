from multiprocessing.pool import ThreadPool
import re
from matplotlib.style import available
import mysql.connector
import requests
from bs4 import BeautifulSoup
import json
import os
import random
import time
import threading

sem = threading.Semaphore()
path = os.path.abspath(os.getcwd())
print(path)
sucess = False
TYPE = "insert"
# TYPE='insert'
print(TYPE)

f = open(path + "/errorLinks.txt", "a")


def Diff(first, second):
    return list(set(first) - set(second))


def disableProduct(id):
    print('disableProduct', id)
    sem.acquire()
    try:
        mycursor.execute("UPDATE products SET active=0 where productId = %s", [id])
        mydb.commit()
    except Exception as e: 
        print(e)
        f.write("disableProduct error\n")
    sem.release()
    print('disableProduct rel', id)


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


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


def updateDb(productId, price, totalPrice, sizes):
    print("sem get", productId)
    sem.acquire()
    try:
        mycursor.execute(
            "select size from size join linkSizeAndProduct lsp on size.sizeId = lsp.sizeId where productId = %s",
            [productId],
        )
        beforeSizes = mycursor.fetchall()
        beforeSizes = list(map(lambda x: x["size"], beforeSizes))
        sizesToInsert = Diff(sizes, beforeSizes)
        sizezToUpdate = Diff(beforeSizes, sizes)
        print("sizesToInsert", sizesToInsert)
        print("sizezToUpdate", sizezToUpdate)
        if len(sizesToInsert):
            #   print('sizesToInsert', productId)
            for size in sizesToInsert:
                mycursor.execute("SELECT sizeId from size where size = %s", [size])
                sizeId = mycursor.fetchall()
                mycursor.execute(
                    "INSERT INTO linkSizeAndProduct(sizeId, productId) VALUES (%s, %s)",
                    [sizeId[0]["sizeId"], productId],
                )
                mydb.commit()

        if len(sizezToUpdate):
            #   print('sizezToUpdate', productId)
            for size in sizezToUpdate:
                mycursor.execute("SELECT sizeId from size where size = %s", [size])
                sizeId = mycursor.fetchall()
                mycursor.execute(
                    "UPDATE linkSizeAndProduct SET available = 0 where sizeId = %s AND productId = %s",
                    [sizeId[0]["sizeId"], productId],
                )
                mydb.commit()
        mycursor.execute("SELECT count(*) as count from linkSizeAndProduct where productId = %s and available = 1", [productId])
        availableSizes = mycursor.fetchall()
        availableSizes = availableSizes[0]["count"]
        print(type(availableSizes))
        if(availableSizes == 0):
            print(availableSizes)
            mycursor.execute(
                "UPDATE products SET price=%s, totalPrice = %s,  active=0 where productId = %s",
                [price, totalPrice, productId],
            )
        else: 
            mycursor.execute(
                "UPDATE products SET price=%s, totalPrice = %s,  active=1 where productId = %s",
                [price, totalPrice, productId],
            )
        mydb.commit()
        sem.release()
        print("sem rel", productId)

    except Exception as e:
        print(e)
        f.write(str("update error" + str(productId)) + "\n")

        sem.release()


def insertIntoDb(
    link, title, price, totalPrice, styleNum, availableSizesInNumber, mappedImages
):
    sem.acquire()
    try:
        mycursor.execute("SELECT id from brands where brandName = %s", [link["brand"]])
        brandId = mycursor.fetchall()
        sql = "INSERT INTO products (title, price, totalPrice, styleNumber, currencyId, brandId, mainAndCategoryId, typeId, linkId, link, colorId, sColorId) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        val = (
            title,
            price,
            totalPrice,
            styleNum,
            1,
            brandId[0]["id"],
            link["mainAndCategId"],
            link["typeId"],
            link["id"],
            link["link"],
            link["colorId"],
            link["sColorId"],
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

        mycursor.execute("UPDATE links SET inserted=%s where id = %s", [1, link["id"]])
        mydb.commit()
        sem.release()
    except Exception as e:
        print("error insert")
        print(link)
        print(e)
        sem.release()


mydb = mysql.connector.connect(
    host="171.22.24.215", user="anenkov", db="annenkovstore", password="anenanenkovkov"
)

mycursor = mydb.cursor(dictionary=True)

if (TYPE == "update"):
    mycursor.execute("select productId, link, (select brandName from brands where id = brandId) as brand from products")
else:
    mycursor.execute("select * from links where inserted = 0")

products = mycursor.fetchall()
# print(links)
def df_loops(link):
    if link["brand"] == "nike1" or link["brand"] == "jordan1":
        print("\n\n******** " + link["brand"] + " *********\n\n")
        headers = {
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
            "cookie": 'AnalysisUserId=2.19.196.126.256951659079848165; feature_enabled__as_nav_rollout=true; audience_segmentation_performed=true; AKA_A2=A; geoloc=cc=IR,rc=,tp=vhigh,tz=GMT+3.50,la=35.67,lo=51.42; bm_sz=C1C68DE8A29B46FB8D5CA39AD730EA93~YAAQfsQTAqRf2iKCAQAAp3XdSBAOjH7sVJXEs5miW5fAImFArgiXElDh0Sc1VXnyA6xsCqbUw16a+ejvy0LGlj0PfICFW6gHykKdNit/YVNGWF+2wAnRf76nUX4KDhK2dGCgy/pi2GAIyWcFT+G6ntMGVf6dfM/DHKYn160nWHEPzx1hsiYk6hJXBLEkx1fDD7zk8HVvx0xRN9QOw7Zljv7vfUClQv24qH8eWc/jq4XQ1k9U7O8fdzG0W/bevxyB0jEg7sUCjccA85EzCVoX6W8gCnD+ijZ9svUfe0hNBq3TJ5cnnYk7SxBq/jGlqN219U7d2uEOQMhjDQXuP4ELqZL8kA5DeQjaeBdoOd2EOMa4rRTBdBIQhA+KTxQ8EDzs66hnW1ib26VOsDnB8IY=~3290182~3422261; guidS=38eb665d-e175-415a-fc4d-4db58995f2f5; guidU=c28b6939-84d9-4d4c-84bc-284e5c1e07cf; NIKE_COMMERCE_COUNTRY=TR; NIKE_COMMERCE_LANG_LOCALE=tr_TR; s_ecid=MCMID%7C00078281668325488764570501589095094480; AMCVS_F0935E09512D2C270A490D4D%40AdobeOrg=1; AMCV_F0935E09512D2C270A490D4D%40AdobeOrg=1994364360%7CMCMID%7C00078281668325488764570501589095094480%7CMCAID%7CNONE%7CMCOPTOUT-1659087049s%7CNONE%7CvVersion%7C3.4.0; ak_bmsc=426AA54AB58D4930B1912B5F4F4265A4~000000000000000000000000000000~YAAQfsQTAqNg2iKCAQAA4nndSBCSwwO+6axi6dcDcu/pIO2RkGIXZU0uuOXZVg1obQri1MuxS2Q/V1WL4l4GWLtl/K888M/uCCkVVv5V4CaUpU8dkwK2+hYABv3hVM+3bAi2LtzeHOE1Os4ThsYYJBhvmczrF+t/EuK4UFK3FLJvL3OkEbFjFaa2BxPnDUHu7mbK7kJTeT8D2MtNc0U+5R7Ryub99FahCBAgoahoL9wqL7HL7ZjEi+DkVBdr803nYAuU0uueJd8GzZ/8ZaGLcMFGvyHf1Rt+6UJed0Kn/vySGVSwVJjdZlWxcfkOdnuqqO9dMgct95T8SQ1dJE8UxUXTuGLdAIxHlDe9HNM5CyCDvwVH2xetpUlYn0Dcd8RyTR14Zuf+McAP28PFHMkwfpl6bQwpp7hefqfiS7JmgOtZQqfa4cu/siI5dPeXC36fOo3f3Xl6aGd0fKYPbAyn/1/uTLrhgMq6ieR673Kdkamb69nDU/RB; RES_TRACKINGID=27309745747803; RES_SESSIONID=594658110776082; ResonanceSegment=1; anonymousId=7DD74E1DD1BB61FCC6FFF08698D260B5; ppd=pdp|nikecom>pdp>kd%20trey%205%20x; bm_sv=780B22F9C2976F46AE77DF28295C2171~YAAQfsQTAt3K3CKCAQAAAOXoSBCTrFlviAHitDgIib/0CyLapcgM/nr0PQgAfkqc5CVJZwdzBIqiIWRfy3ZpVw8WrgPFfPLhvkhgr3iTtfu8RBn+iW+JCt3joO5gYRbvSyNI95NMQuetTGxpuKTZ3/YmaE1T2IH5XDoFDNlv3cXAX3M9qv7bV9az144Lte1+HYI2TwJZP3ugLnZ/rRXDb1+mXl5Fi8NNC3GWOjwExBHo8SUgcCZl3eK9+nSzFcw=~1; _abck=1B2682DED7212205EAFEB69F39FC665A~-1~YAAQDt46F8BkuSCCAQAAieroSAhQuA5qxU9a36WqHWF5SW3nZjoyXKB66+zpN5viF6ncIwu1eGkoJzHRbBM67Bu9v0XMJwRUPmCymGtuAKuSGwKtofYGw0KIv9hM5zDqqZyG+V8xYqvQSzmxhhRlfr8ParChQ97gUjUMQ3OitwfexhO+HGimxnHvdrMnsX/KlJzdmz8heVWrIIqK+7hadvH4UW+IzU/WFk3lbynkhU3R2A76nY2m+yB7Gf8+nY9ELx7QFhQLexd2/Rc7tIHq5dmS8UpCk2qQDtK+NMIHwmqW18f/U5b04HPB2nvN7VqV0Ik9qNSiljBh6/uf22KVRDEC6bPntItl+8sjVkygfnP2rdAOK9KZ5m9uMszeiNh8F+zYBDYfzgLvVAYtBZjStMqqey/PcX3A36y8bORfPIMVbI0A3qBgUChNHjHvHp4cLfxhFKBsTVV/u1UF8zGS1UN/Yy8acFAZV5o0PS3pvQ2uy6GY31gd+/f0UtoLuZ7hnM98R6JRKxkGHwJknpCorvI=~-1~-1~-1; RT="z=1&dm=nike.com&si=4d9dbf13-532c-4226-bdb6-4bd179df7cc8&ss=l665az2f&sl=5&tt=kq1&bcn=%2F%2F684dd32d.akstat.io%2F&ld=g3qc&ul=g55s"',
            "origin": "https://www.nike.com/tr",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        }

        try:
            URL = link["link"]
            s = requests.Session()
            page = s.get(URL, headers=headers)
            soup = BeautifulSoup(page.content, "html.parser")


            mains = soup.find("script", id="__NEXT_DATA__").text.strip()

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
            if (TYPE != "update"):
                insertIntoDb(
                    link,
                    title,
                    fullPrice,
                    price,
                    fstyleNum,
                    availableSizesInNumber,
                    mappedImages,
                )
            else:
                updateDb(link["productId"], morePrice, price, realSizes)

        except Exception as e:
            sucess = False
            if (TYPE == "update"):
                disableProduct(link['productId'])
                f.write(str(link['link']) + '\n')
            print(link["link"])
            print(e)
            print("**")

    elif link["brand"] == "new balance":
        print("\n\n******** NEWBALANCE *********\n\n")

        s = requests.Session()
        URL = link["link"]
        try:
            page = s.get(URL.strip())
            soup = BeautifulSoup(page.content, "html.parser")
            product = soup.find_all("h1", class_="emos_H1")
            title = product[0].text.strip()
            price = extractPrice(
                soup.find(
                    id="ctl00_u23_ascUrunDetay_dtUrunDetay_ctl00_lblSatisFiyat"
                ).text.strip()
            )
            morePrice = price
            if soup.find(id="plhSatisIlkFiyat").text:
                morePrice = extractPrice(soup.find(id="plhSatisIlkFiyat").text.strip())
            cloudId = URL.strip().split("/")[-1]
            cloudId = cloudId.split("-")[-1].replace(".html", "")

            styleNum = soup.find("div", class_="ems-prd-sort-desc").text.strip()
            tags = soup.find_all("ul", class_="swiper-wrapper slide-wrp")[0]
            images = tags.find_all("a")
            mappedImages = []
            for image in images:
                try:
                    if image["data-large"]:
                        mappedImages.append(image["data-large"])
                except KeyError:
                    continue

            sizes = page = s.get(
                "https://www.newbalance.com.tr/usercontrols/urunDetay/ajxUrunSecenek.aspx?urn="
                + cloudId
                + "&fn=dty&std=True&type=scd1&index=0&objectId=ctl00_u23_ascUrunDetay_dtUrunDetay_ctl00&runatId=urunDetay&scd1=0&lang=tr-TR"
            )
            soup = BeautifulSoup(page.content, "html.parser")
            realSizes = []
            sizes = soup.find_all("a")
            for size in sizes:
                try:
                    if size["class"] and size["class"].count("stokYok") != 0:
                        continue
                    else:
                        realSizes.append(size.text.strip())
                except KeyError:
                    realSizes.append(size.text.strip())
            if (TYPE != "update"):
                insertIntoDb(
                    link,
                    title,
                    morePrice,
                    price,
                    styleNum.split(" ")[-1],
                    realSizes,
                    mappedImages,
                )
            else:
                updateDb(link["productId"], morePrice, price, realSizes)
        except Exception as e:
            sucess = False
            if (TYPE == "update"):
                disableProduct(link['productId'])
                f.write(str(link['link']) + '\n')
            print(link["link"])
            print(e)
            print("**")

    elif link["brand"] == "reebok":
        print("\n\n******** REEBOK *********\n\n")
        headers = {
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
            "Cookie": "",
        }

        try: 
            s = requests.Session()
            URL = link["link"]
            page = s.get(URL.strip())
            soup = BeautifulSoup(page.content, "html.parser")

            images = soup.find_all("img", class_="image-blur")
            mappedImages = []
            for image in images:
                try:
                    if image["src"]:
                        mappedImages.append(image["src"])
                except KeyError:
                    continue

            title = soup.find("h1", class_="gl-heading--m mb-2px").text.strip()
            price = soup.find_all("span", class_="gl-price__value")
            if price[0]:
                mainPrice = extractPrice(price[0].text.strip())
            if price[1]:
                mainTotalPrice = extractPrice(price[1].text.strip())

            styleNum = (
                soup.find("div", class_="p-info").find("p", class_="gl-label").text.strip()
            )
            sizes = soup.find("div", class_="size-options").find_all("option")
            realSizes = []
            for size in sizes:
                realSizes.append(size.text.strip().replace(",", "."))

            if (TYPE != "update"):
                insertIntoDb(
                    link,
                    title.replace("Ayakkabı", ""),
                    mainTotalPrice,
                    mainPrice,
                    styleNum,
                    realSizes,
                    mappedImages,
                )
            else:
                updateDb(link["productId"], mainTotalPrice, mainPrice, realSizes)
        except Exception as e:
            sucess = False
            if (TYPE == "update"):
                disableProduct(link['productId'])
                f.write(str(link['link']) + '\n')
            print(link["link"])
            print(e)
            print("**")

    elif link["brand"] == "adidas":
        print("\n\n******** ADIDAS *********\n\n")
        adiheaders = {
            "origin": "www.adidas.com.tr",
            "cookie": "",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36",
        }
        URL = link["link"]

        try:
            styleNum = URL.split("/")[-1]
            styleNum = re.findall("^(.*?)\.html", styleNum)[0]
            print(URL)
            page = requests.get(URL.strip(), headers=adiheaders)
            print(page)
            soup = BeautifulSoup(page.content, "html.parser")
            scripts = soup.find_all("script")
            # for sc in script:
            #     print(sc.text, end="\n\n")
            details = ""
            for script in scripts:
                if script.text.find("@context") != -1:
                    details = script.text
            # print(details)
            details = json.loads(details)
            sizes = requests.get(
                "https://www.adidas.com.tr/api/products/"
                + styleNum
                + "/availability?sitePath=en",
                headers=adiheaders,
            )
            filtered = list(
                filter(
                    lambda var: var["availability_status"] == "IN_STOCK",
                    sizes.json()["variation_list"],
                )
            )
            mappedSizes = list(map(lambda x: x["size"], filtered))
            price = extractPrice(str(details["offers"]["price"]))
            morePrice = price
            if soup.find("div", class_="gl-price-item--crossed"):
                morePrice = extractPrice(
                    soup.find("div", class_="gl-price-item--crossed").text.strip()
                )
            print(price)

            if (TYPE != "update"):
                insertIntoDb(
                    link,
                    details["name"].replace("Ayakkabı", ""),
                    morePrice,
                    price,
                    styleNum,
                    mappedSizes,
                    details["image"],
                )
            else:
                updateDb(link["productId"], morePrice, price, mappedSizes)

        except Exception as e:
            sucess = False
            if (TYPE == "update"):
                disableProduct(link['productId'])
                f.write(str(link['link']) + '\n')
            print(link["link"])
            print(e)
            print("**")

    elif link["brand"] == "puma":
        print("\n\n******** PUMA *********\n\n")
        headers = {
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
            "Cookie": "",
        }

        try:
            s = requests.Session()
            URL = link["link"]
            page = s.get(URL.strip())
            soup = BeautifulSoup(page.content, "html.parser")

            images = soup.find_all("img", class_="gallery-item__img")

            mappedImages = []
            for image in images:
                try:
                    if image["src"] and not image.has_attr("data-lazy"):
                        mappedImages.append(image["src"])
                    elif image["data-lazy"]:
                        mappedImages.append(image["data-lazy"])
                except KeyError:
                    continue

            title = soup.find("h1", class_="page-title").text.strip()
            prices1 = soup.find_all("span", class_="price")[0].text.strip()
            prices2 = soup.find_all("span", class_="price")[1].text.strip()
            prices1 = extractPrice(prices1)
            prices2 = extractPrice(prices2)
            price = extractPrice(soup.find("span", class_="price").text.strip())
            if prices1 is None or prices2 is None:
                prices1 = price
                prices2 = price
            styleNum = (
                soup.find("div", class_="product-article")
                .find("span", class_="product-article__value")
                .text.strip()
            )
            color = soup.find("span", class_="colors__text-name").text.strip()
            details = ""
            scripts = soup.find_all("script")
            for script in scripts:
                if script.text.find("spConfig") != -1:
                    details = json.loads(script.text)
            allColors = details["#product_addtocart_form"]["configurable"]["spConfig"][
                "attributes"
            ]["93"]["options"]
            allSizes = details["#product_addtocart_form"]["configurable"]["spConfig"][
                "attributes"
            ]["141"]["options"]
            founded = next(x for x in allColors if x["label"] == color)
            foundedSizes = []
            for size in allSizes:
                for pr in size["products"]:
                    if founded["products"].count(pr) != 0:
                        foundedSizes.append(size["label"])

            if (TYPE != "update"):
                insertIntoDb(
                    link,
                    title.replace("Ayakkabı", ""),
                    prices2,
                    prices1,
                    styleNum,
                    foundedSizes,
                    mappedImages,
                )
            else:
                updateDb(link["productId"], prices2, prices1, foundedSizes)

        except Exception as e:
            sucess = False
            if (TYPE == "update"):
                disableProduct(link['productId'])
                f.write(str(link['link']) + '\n')
            print("asics")
            print(link)
            print(e)
            print("**")

    elif link["brand"] == "asics":
        print("\n\n******** ASICS *********\n\n")
        headers = {
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
            "Cookie": "",
        }

        try:
            s = requests.Session()
            URL = link["link"]
            page = s.get(URL.strip())
            soup = BeautifulSoup(page.content, "html.parser")

            images = soup.find("div", class_="swiper-wrapper").find_all(
                "img", class_="swiper-lazy"
            )
            mappedImages = []
            for image in images:
                try:
                    if image["src"]:
                        mappedImages.append(image["data-src"])
                except KeyError:
                    continue

            title = soup.find("span", class_="sk-model-title").text.strip()
            styleNum = soup.find("span", class_="sk-model-alt-title").text.strip()
            price = (0,)
            morePrice = 0
            if len(soup.find_all("span", class_="pPrice")) == 2:
                price = extractPrice(
                    soup.find_all("span", class_="pPrice")[1].text.strip()
                )
                morePrice = extractPrice(
                    soup.find_all("span", class_="pPrice")[0].text.strip()
                )
            else:
                price = extractPrice(
                    soup.find_all("span", class_="pPrice")[0].text.strip()
                )
                morePrice = price

            mappedSizes = []
            sizes = soup.find("div", class_="cl-size-input-container").find_all("label")

            # print(sizes)
            for size in sizes:
                try:
                    if size["data-stock"] != "0":
                        mappedSizes.append(size.text.strip())
                except KeyError:
                    continue

            if (TYPE != "update"):
                insertIntoDb(
                    link,
                    title,
                    morePrice,
                    price,
                    styleNum.split(" ")[-1],
                    mappedSizes,
                    mappedImages,
                )
            else:
                updateDb(link["productId"], morePrice, price, mappedSizes)

        except Exception as e:
            sucess = False
            if (TYPE == "update"):
                disableProduct(link['productId'])
                f.write(str(link['link']) + '\n')
            print("asics")
            print(link)
            print(e)
            print("**")

    elif link["brand"] == "salomon":
        print("\n\n******** salomon *********\n\n")
        headers = {
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
            "Cookie": "",
        }

        try:
            s = requests.Session()
            URL = link["link"]
            page = s.get(URL.strip())
            soup = BeautifulSoup(page.content, "html.parser")

            images = soup.find_all("img", class_="cloudzoom")
            mappedImages = []
            for image in images:
                try:
                    if(image["src"]):
                        mappedImages.append("https://www.salomon.com.tr/" + image["src"])
                except KeyError:
                        continue


            title = soup.find("div", class_="ProductName").text.strip()
            price = extractPrice(soup.find("span", class_="spanFiyat").text.strip(), '.')
            styleNum = soup.find("span", class_="productcode").text.strip().replace('(', '').replace(')','')
            mappedSizes = []
            scripts = soup.find("body").find_all("script")[0].text.strip()
            scripts = json.loads(scripts[scripts.find('{'):(scripts.find(';'))])
            filtered = list(filter(lambda var: var["stokAdedi"] > 0 and var["ekSecenekTipiTanim"] == "Beden", scripts["productVariantData"]))
            sizes = list(map(lambda x: x["tanim"][x["tanim"].find('(')+1:x["tanim"].find(')')], filtered))

            if (TYPE != "update"):
                insertIntoDb(link, title, price, price, "", mappedSizes, mappedImages)
            else:
                updateDb(link["productId"], price, price, mappedSizes)

        except Exception as e:
            sucess = False
            if (TYPE == "update"):
                disableProduct(link['productId'])
                f.write(str(link['link']) + '\n')
            print("salomon")
            print(link)
            print(e)
            print("**")

    elif link["brand"] == "mizuno":
        print("\n\n******** mizuno *********\n\n")
        headers = {
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
            "Cookie": "",
            "origin": "https://www.mizunotr.com",
        }

        try:
            s = requests.Session()
            URL = link["link"]
            page = s.get(URL.strip())
            soup = BeautifulSoup(page.content, "html.parser")
            product = soup.find(id="productDetail")
            tags = product.find(id="pageContent")
            images = tags.find_all("a")
            mappedImages = []
            for image in images:
                try:
                    if image["href"].find("http") != -1:
                        mappedImages.append(image["href"])
                except KeyError:
                    continue
            sizes = soup.find_all("div", class_="pos-r fl col-12 ease variantList var-new")[
                0
            ]
            realSize = sizes.find_all("a")
            mappedSizes = []
            for size in realSize:
                mappedSizes.append(size.text.strip())
            price = extractPrice(soup.find("span", class_="product-price").text.strip())
            styleNum = soup.find_all("span", class_="supplier_product_code")[0]
            title = (
                soup.find(id="productName")
                .text.strip()
                .replace("Ayakkabı", "")
                .replace("Spor", "")
                .replace("Erkek", "")
                .replace("Nubuk", "")
                .replace("Yeşil", "")
                .replace("Koyu", "")
                .replace("Kadin", "")
            )
            if (TYPE != "update"):
                insertIntoDb(
                    link, title, price, price, styleNum.text.strip(), mappedSizes, mappedImages
                )
            else:
                updateDb(link["productId"], price, price, mappedSizes)

        except Exception as e:
            sucess = False
            if (TYPE == "update"):
                disableProduct(link['productId'])
                f.write(str(link['link']) + '\n')
            print("salomon")
            print(link)
            print(e)
            print("**")

    elif link["brand"] == "timberland":
        print("\n\n******** timberland *********\n\n")
        headers = {
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
            "Cookie": "",
        }

        try:
            s = requests.Session()
            URL = link["link"]
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

            nprice = ''
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
            if (TYPE != "update"):
                insertIntoDb(link, title, oprice, nprice, "", mappedSizes, mappedImages)
            else:
                updateDb(link["productId"], oprice, nprice, mappedSizes)
        except Exception as e:
            sucess = False
            if (TYPE == "update"):
                disableProduct(link['productId'])
                f.write(str(link['link']) + '\n')
            print("timberland error")
            print(link)
            print(e)
            print("**")

    time.sleep(3)


df = []
print(products[0])
if (TYPE == "update"):
    random.shuffle(products)
    print(products[0])
    links = [products[i:i + 40] for i in range(0, len(products), 40)]

    for chLink in links:
        with ThreadPool(40) as pool:
            for result in pool.map(df_loops, chLink):
                df.append(result)
        print('LOOOOOOOOOOOOP')
        time.sleep(2)


else:
    links = [products[i : i + 10] for i in range(0, len(products), 10)]

    for chLink in links:
        with ThreadPool(10) as pool:
            for result in pool.map(df_loops, chLink):
                df.append(result)
        time.sleep(2)

f.close()



