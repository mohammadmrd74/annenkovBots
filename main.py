from multiprocessing.pool import ThreadPool
import re
import mysql.connector
import requests
from bs4 import BeautifulSoup
import json
import os
from urllib import parse
import random
import time
import threading

sem = threading.Semaphore()
path = os.path.abspath(os.getcwd())

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

AdidasMenSize = {
    "4": "36",
    "4.5": "36 2/3",
    "5": "37 1/3",
    "5.5": "38",
    "6": "38 2/3",
    "6.5": "39 1/3",
    "7": "40",
    "7.5": "40 2/3",
    "8": "41 1/3",
    "8.5": "42",
    "9": "42 2/3",
    "9.5": "43 1/3",
    "10": "44",
    "10.5": "44 2/3",
    "11": "45 1/3",
    "11.5": "46",
    "12": "46 2/3",
    "12.5": "47 1/3",
    "13": "48",
    "13.5": "48 2/3",
    "14": "49 1/3",
    "14.5": "50",
    "15": "50 2/3",
    "16": "51 1/3",
    "17": "52 2/3",
    "18": "53 1/3",
    "19": "54 2/3",
    "20": "55 2/3",
}

AdidasWomenSize = {
    "5": "36",
    "5.5": "36 2/3",
    "6": "37 1/3",
    "6.5": "38",
    "7": "38 2/3",
    "7.5": "39 1/3",
    "8": "40",
    "8.5": "40 2/3",
    "9": "41 1/3",
    "9.5": "42",
    "10": "42 2/3",
    "10.5": "43 1/3",
    "11": "44",
    "11.5": "44 2/3",
    "12": "45 1/3",
    "12.5": "46",
    "13": "46 2/3",
    "13.5": "47 1/3",
    "14": "48",
    "14.5": "48 2/3",
    "15": "49 1/3",
    "15.5": "50",
}


sucess = False
# TYPE = "insert"
TYPE = "update"


f = open(path + "/errorLinks.txt", "a")


def Diff(first, second):
    return list(set(first) - set(second))


def disableProduct(id):
    print("disableProduct", id)
    sem.acquire()
    try:
        mycursor.execute("UPDATE products SET active=0 where productId = %s", [id])
        mydb.commit()
    except Exception as e:
        print(bcolors.FAIL)
        print(e)
        print(bcolors.ENDC)
        f.write("disableProduct error\n")
    sem.release()
    print("disableProduct rel", id)


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

readyToUpdates = []
def updateDb(productId, price, totalPrice, sizes):
    sem.acquire()
    try:
        mycursor.execute(
            "select size from size join linkSizeAndProduct lsp on size.sizeId = lsp.sizeId where productId = %s and available = 1",
            [productId],
        )
        beforeSizes = mycursor.fetchall()
        beforeSizes = list(map(lambda x: x["size"], beforeSizes))
        sizesToInsert = Diff(sizes, beforeSizes)
        sizezToUpdate = Diff(beforeSizes, sizes)
        if len(sizesToInsert):
            for size in sizesToInsert:
                mycursor.execute("SELECT sizeId from size where size = %s", [size])
                sizeId = mycursor.fetchall()
                mycursor.execute(
                    "select sizeId from linkSizeAndProduct lsp where productId = %s and sizeId = %s and available = 0",
                    [productId, sizeId[0]["sizeId"]],
                )
                isSizeThere = mycursor.fetchall()
                if len(isSizeThere) > 0:
                    mycursor.execute(
                        "UPDATE linkSizeAndProduct SET available = 1  where sizeId = %s AND productId = %s",
                        [sizeId[0]["sizeId"], productId],
                    )
                    mydb.commit()
                else:
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
            "SELECT count(*) as count from linkSizeAndProduct where productId = %s and available = 1",
            [productId],
        )
        availableSizes = mycursor.fetchall()
        availableSizes = availableSizes[0]["count"]
        if availableSizes == 0:
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

    except Exception as e:
        f.write(str("update error" + str(productId)) + "\n")
        
        print(bcolors.FAIL)
        print(e)
        print(bcolors.ENDC)

        sem.release()


def insertIntoDb(
    link, title, price, totalPrice, styleNum, availableSizesInNumber, mappedImages
):
    sem.acquire()
    try:
        mycursor.execute("SELECT id from brands where brandName = %s", [link["brand"]])
        brandId = mycursor.fetchall()
        sql = "INSERT INTO products (title, price, totalPrice, styleNumber, currencyId, brandId, mainAndCategoryId, typeId, linkId, link, colorId, sColorId, website) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        val = (
            title,
            price,
            totalPrice,
            styleNum,
            link["currencyId"],
            brandId[0]["id"],
            link["mainAndCategId"],
            link["typeId"],
            link["id"],
            link["link"],
            link["colorId"],
            link["sColorId"],
            link["website"]
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
        print(bcolors.FAIL)
        
        print("error insert")
        print(link)
        print(e)
        print(bcolors.ENDC)
        sem.release()


mydb = mysql.connector.connect(
    host="171.22.24.215", user="anenkov", db="annenkovstore", password="anenanenkovkov"
)

mycursor = mydb.cursor(dictionary=True)

if TYPE == "update":
    mycursor.execute(
        "select productId, link, website, currencyId from products where deleted = 0"
    )
else:
    mycursor.execute("select * from links where inserted = 0")



products = mycursor.fetchall()
# print(links)
def df_loops(link):
    if link["website"] == "nike" or link["website"] == "jordan":
        headers = {
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
            "origin": "https://www.nike.com/tr",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        }

        try:
            URL = link["link"]
            s = requests.Session()
            page = s.get(URL, headers=headers, timeout=10)
            soup = BeautifulSoup(page.content, "html.parser")

            mains = soup.find("script", id="__NEXT_DATA__").text.strip()

            fstyleNum = (
                soup.find("li", class_="description-preview__style-color ncss-li")
                .text.strip()
                .replace("Stil: ", "")
            )

            if(URL.split('/')[-1] != fstyleNum):
                raise Exception("gone")

            jsonDetails = json.loads(mains)["props"]["pageProps"]["initialState"]
            styleNum = fstyleNum
            if fstyleNum not in jsonDetails["Threads"]["products"]:
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
            availableSizes = jsonDetails["Threads"]["products"][styleNum][
                "availableSkus"
            ]
            title = jsonDetails["Threads"]["products"][styleNum]["title"]
            availableSizesInNumber = []
            for size in allSizes:
                for asize in availableSizes:
                    if size["skuId"] == asize["id"]:
                        availableSizesInNumber.append(size["localizedSize"])
            price = extractPrice(str(price), ",")
            fullPrice = extractPrice(str(fullPrice), ",")

            if TYPE != "update":
                insertIntoDb(
                    link,
                    title,
                    fullPrice + 60,
                    price + 60,
                    fstyleNum,
                    availableSizesInNumber,
                    mappedImages,
                )
            else:
                updateDb(
                    link["productId"],
                    fullPrice + 60,
                    price + 60,
                    availableSizesInNumber,
                )

        except Exception as e:
            print("****nike*****")
            sucess = False
            if TYPE == "update":
                disableProduct(link["productId"])
                f.write(str(link["link"]) + "\n")
            print(bcolors.FAIL)
            print(link["link"])
            print(e)
            print(bcolors.ENDC)
            print("****nike end*****")

    
    elif link["website"] == "fashfed":
        print("\n\n******** FASHFED *********\n\n")
        headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
        'Cookie': ''
        }

        try:
            s = requests.Session()
            URL =  link["link"]
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


            title = soup.find("div", class_="product__info--title").text.strip().replace("Erkek", "").replace("Beyaz", "").replace("Spor", "").replace("Ayakkabı", "").replace("Unisex", "").replace("Krem", "")
            nprice = extractPrice(soup.find("span", class_="price__new").text.strip(), '.')
            oprice = nprice
            redprice = soup.find("div", class_="red-price")
            if (redprice):
                oprice = nprice
                nprice = extractPrice(redprice.text.strip(), '.')
            styleNum = soup.find("div", class_="product__collapse--content").find("p").text.replace('Ürün Kodu:', '').replace(" ", "").replace("\n", "").strip()
            mappedSizes = []
            scripts = soup.find("select", class_="js-variants-select").find_all("option")

            for size in scripts:
                try:
                    if(size["value"] and "Gelince Haber" not in  size.text):
                        mappedSizes.append(size["value"].replace(",",'.'))
                except KeyError:
                        continue
            if TYPE != "update":
                insertIntoDb(
                    link,
                    title,
                    oprice,
                    nprice,
                    styleNum,
                    mappedSizes,
                    mappedImages,
                )
            else:
                updateDb(link["productId"], nprice, oprice, mappedSizes)
        except Exception as e:
            sucess = False
            if TYPE == "update":
                disableProduct(link["productId"])
                f.write(str(link["link"]) + "\n")
            print(bcolors.FAIL)
            print(link["link"])
            print(e)
            print("**")
            print(bcolors.ENDC)

    
    elif link["website"] == "new balance":
        s = requests.Session()
        URL = link["link"]
        try:
            page = s.get(URL.strip())
            soup = BeautifulSoup(page.content, "html.parser")
            title = soup.find("h1", class_="product-name").text.strip()
            price = extractPrice(soup.find("span", class_="price-value").text.strip(), ".")
            morePrice= price
            if(soup.find("span", class_="strike-through")):
                morePrice = extractPrice(soup.find("span", class_="strike-through").text.strip(), ",")

            styleNum = soup.find("div", class_="product-category").text.strip()
         
            images = soup.find_all("li", class_="swiper-slide")
            mappedImages = []
            for image in images:
                try:
                    mappedImages.append(image["data-large"])

                except KeyError:
                    continue
            grid = soup.find("div", class_="options-list")
            sizes = grid.find_all("li", class_="barcode-item")

            mappedSizes = []
            for size in sizes:
                try:
                    if("out-of-stock" not in size["class"]):
                        mappedSizes.append(size.text.strip())

                except KeyError:
                    continue
            if TYPE != "update":
                insertIntoDb(
                    link,
                    title,
                    morePrice,
                    price,
                    styleNum.split(" ")[-1],
                    mappedSizes,
                    mappedImages
                )
            else:
                updateDb(link["productId"], morePrice, price, mappedSizes)
        except Exception as e:
            sucess = False
            if TYPE == "update":
                disableProduct(link["productId"])
                f.write(str(link["link"]) + "\n")
            print(bcolors.FAIL)
            print(link["link"])
            print(e)
            print("**")
            print(bcolors.ENDC)

    elif link["website"] == "reebok":
        headers = {
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
        }

        try:
            s = requests.Session()
            URL = link["link"]
            page = s.get(URL.strip(), timeout=10)
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
                soup.find("div", class_="p-info")
                .find("p", class_="gl-label")
                .text.strip()
            )
            sizes = soup.find("div", class_="size-options").find_all("option")
            realSizes = []
            for size in sizes:
                realSizes.append(size.text.strip().replace(",", "."))

            if TYPE != "update":
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
            if TYPE == "update":
                disableProduct(link["productId"])
                f.write(str(link["link"]) + "\n")
            print(bcolors.FAIL)
            print(link["link"])
            print(e)
            print("**")
            print(bcolors.ENDC)
    
    elif link["website"] == "adidas" and link["currencyId"] == 1:
        adiheaders = {
            "origin": "www.adidas.com.tr",
            "cookie": "",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36",
        }
        URL = link["link"]

        try:
            styleNum = URL.split("/")[-1]
            styleNum = re.findall("^(.*?)\.html", styleNum)[0]
            page = requests.get(URL.strip(), headers=adiheaders, timeout=10)
            soup = BeautifulSoup(page.content, "html.parser")
            scripts = soup.find_all("script")
            details = ""
            for script in scripts:
                if script.text.find("@context") != -1:
                    details = script.text
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
            price = str(details["offers"]["price"])
            morePrice = price
            if soup.find("div", class_="gl-price-item--crossed"):
                morePrice = extractPrice(
                    soup.find("div", class_="gl-price-item--crossed").text.strip(), "."
                )

            if TYPE != "update":
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
            if TYPE == "update":
                disableProduct(link["productId"])
                f.write(str(link["link"]) + "\n")
            print(bcolors.FAIL)
            print(link["link"])
            print(e)
            print("**")
            print(bcolors.ENDC)

    elif link["website"] == "adidas" and link["currencyId"] == 2:
        adiheaders = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-language": "en-US,en;q=0.9,fa;q=0.8,de;q=0.7",
            "cache-control": "max-age=0",
            "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Linux"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36",
            "upgrade-insecure-requests": "1",
        }
        URL = link["link"]

        try:
            styleNum = URL.split("/")[-1]
            styleNum = re.findall("^(.*?)\.html", styleNum)[0]
            page = requests.get(URL.strip(), headers=adiheaders, timeout=10)
            soup = BeautifulSoup(page.content, "html.parser")
            scripts = soup.find_all("script")
            details = ""
            for script in scripts:
                if script.text.find("@context") != -1:
                    details = script.text
            details = json.loads(details)
            sizes = requests.get(
                "https://www.adidas.com/api/products/"
                + styleNum
                + "/availability?sitePath=us",
                headers=adiheaders,
            )
            filtered = list(
                filter(
                    lambda var: var["availability_status"] == "IN_STOCK",
                    sizes.json()["variation_list"],
                )
            )
            mappedSizes = list(map(lambda x: x["size"], filtered))
            print(details["offers"]["price"])
            price = str(details["offers"]["price"])
            morePrice = price
            print(price)
            if soup.find("div", class_="gl-price-item--crossed"):
                morePrice = extractPrice(
                    soup.find("div", class_="gl-price-item--crossed").text.strip(), "."
                )
            print(morePrice)

            normalizeSize = []
            if(link["mainAndCategId"] == 1):
                for size in mappedSizes:
                    normalizeSize.append(AdidasMenSize[size])
            elif(link["mainAndCategId"] == 4):
                for size in mappedSizes:
                    normalizeSize.append(AdidasWomenSize[size])

            if TYPE != "update":
                insertIntoDb(
                    link,
                    details["name"],
                    morePrice,
                    price,
                    styleNum,
                    normalizeSize,
                    details["image"],
                )
            else:
                updateDb(link["productId"], morePrice, price, normalizeSize)

        except Exception as e:
            sucess = False
            if TYPE == "update":
                disableProduct(link["productId"])
                f.write(str(link["link"]) + "\n")
            print(bcolors.FAIL)
            print(link["link"])
            print(e)
            print("**")
            print(bcolors.ENDC)

    elif link["website"] == "puma":
        headers = {
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
            "Cookie": "",
        }

        try:
            s = requests.Session()
            URL = link["link"]
            page = s.get(URL.strip(), timeout=10)
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
            if( prices1 is None or prices1 == 1):
                prices1 = prices2
            if( prices2 is None or prices2 == 1):
                prices2 = prices1
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

            if TYPE != "update":
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
            if TYPE == "update":
                disableProduct(link["productId"])
                f.write(str(link["link"]) + "\n")
            print(bcolors.FAIL)
            print("puma")
            print(link["link"])
            print(e)
            print("**")
            print(bcolors.ENDC)

    elif link["website"] == "asics":
        headers = {
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
            "Cookie": "",
        }

        try:
            s = requests.Session()
            URL = link["link"]
            page = s.get(URL.strip(), timeout=10)
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

            for size in sizes:
                try:
                    if size["data-stock"] != "0":
                        mappedSizes.append(size.text.strip())
                except KeyError:
                    continue

            if TYPE != "update":
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
            if TYPE == "update":
                disableProduct(link["productId"])
                f.write(str(link["link"]) + "\n")
            print(bcolors.FAIL)
            print("asics")
            print(link["link"])
            print(e)
            print("**")
            print(bcolors.ENDC)

    elif link["website"] == "salomon":
        headers = {
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
            "Cookie": "",
        }

        try:
            s = requests.Session()
            URL = link["link"]
            page = s.get(URL.strip(), timeout=10)
            soup = BeautifulSoup(page.content, "html.parser")

            images = soup.find_all("img", class_="cloudzoom")
            mappedImages = []
            for image in images:
                try:
                    if image["src"]:
                        mappedImages.append(
                            "https://www.salomon.com.tr/" + image["src"]
                        )
                except KeyError:
                    continue

            title = soup.find("div", class_="ProductName").text.strip()
            price = extractPrice(
                soup.find("span", class_="spanFiyat").text.strip(), "."
            )
            styleNum = (
                soup.find("span", class_="productcode")
                .text.strip()
                .replace("(", "")
                .replace(")", "")
            )
            mappedSizes = []
            scripts = soup.find("body").find_all("script")[0].text.strip()
            scripts = json.loads(scripts[scripts.find("{") : (scripts.find(";"))])
            filtered = list(
                filter(
                    lambda var: var["stokAdedi"] > 0
                    and var["ekSecenekTipiTanim"] == "Beden",
                    scripts["productVariantData"],
                )
            )
            sizes = list(
                map(
                    lambda x: x["tanim"][
                        x["tanim"].find("(") + 1 : x["tanim"].find(")")
                    ],
                    filtered,
                )
            )

            if TYPE != "update":
                insertIntoDb(link, title, price, price, "", sizes, mappedImages)
            else:
                print(link["productId"], price, price, sizes)
                updateDb(link["productId"], price, price, sizes)

        except Exception as e:
            sucess = False
            if TYPE == "update":
                disableProduct(link["productId"])
                f.write(str(link["link"]) + "\n")
            print(bcolors.FAIL)
            print("salomon")
            print(link["link"])
            print(e)
            print("**")
            print(bcolors.ENDC)

    elif link["website"] == "mizuno":
        headers = {
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
            "Cookie": "",
            "origin": "https://www.mizunotr.com",
        }

        try:
            s = requests.Session()
            URL = link["link"]
            page = s.get(URL.strip(), timeout=10)
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
            sizes = soup.find_all(
                "div", class_="pos-r fl col-12 ease variantList var-new"
            )[0]
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
            if TYPE != "update":
                insertIntoDb(
                    link,
                    title,
                    price,
                    price,
                    styleNum.text.strip(),
                    mappedSizes,
                    mappedImages,
                )
            else:
                updateDb(link["productId"], price, price, mappedSizes)

        except Exception as e:
            sucess = False
            if TYPE == "update":
                disableProduct(link["productId"])
                f.write(str(link["link"]) + "\n")
            print(bcolors.FAIL)
            print(link["link"])
            print(e)
            print("**")
            print(bcolors.ENDC)

    elif link["website"] == "timberland":
        headers = {
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
            "Cookie": "",
        }

        try:
            s = requests.Session()
            URL = link["link"]
            page = s.get(URL.strip(), timeout=10)
            soup = BeautifulSoup(page.content, "html.parser")

            images = soup.find("div", class_="main-gallery").find_all(
                "img", class_="image-blur"
            )
            mappedImages = []
            for image in images:
                try:
                    if image["src"]:
                        mappedImages.append(image["data-image"])
                except KeyError:
                    continue

            title = soup.find("h1", class_="p-name").text.strip()
            # styleNum = soup.find("span", class_="sk-model-alt-title").text.strip()

            nprice = ""
            oprice = ""
            if soup.find("span", class_="one-price"):
                oprice = extractPrice(
                    soup.find("span", class_="one-price").text.strip()
                )
                nprice = oprice
            if soup.find("span", class_="new-price"):
                nprice = extractPrice(
                    soup.find("span", class_="new-price").text.strip()
                )
                oprice = extractPrice(
                    soup.find("span", class_="old-price").text.strip()
                )

            mappedSizes = []
            sizes = soup.find("div", class_="size-options").find_all("a", class_="")
            for size in sizes:
                try:
                    mappedSizes.append(size.text.strip())
                except KeyError:
                    continue
            title = (
                title.replace("Ayakkabı", "")
                .replace("Spor", "")
                .replace("Erkek", "")
                .replace("Nubuk", "")
                .replace("Yeşil", "")
                .replace("Koyu", "")
                .replace("Kadin", "")
            )
            if TYPE != "update":
                insertIntoDb(link, title, oprice, nprice, "", mappedSizes, mappedImages)
            else:
                updateDb(link["productId"], oprice, nprice, mappedSizes)
        except Exception as e:
            sucess = False
            if TYPE == "update":
                disableProduct(link["productId"])
                f.write(str(link["link"]) + "\n")
            print(bcolors.FAIL)
            print("timberland error")
            print(link["link"])
            print(e)
            print("**")
            print(bcolors.ENDC)
    elif link["website"] == "pull and bear":
        try:
            print("\n\n******** PULL & BEAR *********\n\n")
            headers = {
                "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
            }


            s = requests.Session()
            URL = link["link"]
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
            images = list(
                    map(
                        lambda image: "https://static.pullandbear.net/2/photos" + media["path"] + "/" + image["idMedia"] + "1.jpg",
                        media["xmediaItems"][0]["medias"],
                    ),
                
            )

            nprice = extractPrice(price[0:-2]+ ',' + price[-2:])
            oprice = extractPrice(oldPrice[0:-2]+ ',' + oldPrice[-2:])
           
            if TYPE != "update":
                insertIntoDb(link, title, oprice, nprice, urlQuery["pelement"][0], sizes, images)
            else:
                updateDb(link["productId"], oprice, nprice, sizes)
        except Exception as e:
            if TYPE == "update":
                disableProduct(link["productId"])
                f.write(str(link["link"]) + "\n")
            print("pull and error")

    # time.sleep(3)
if __name__ == "__main__":
    df = []
    counter = 0
    if TYPE == "update":
        start_time = time.time()
        random.shuffle(products)
        print(len(products))
        
        links = [products[i : i + 3] for i in range(0, len(products), 3)]

        for chLink in links:
            with ThreadPool(4) as pool:
                for result in pool.map(df_loops, chLink):
                    df.append(result)
            time.sleep(2)
            counter += 1
            print(bcolors.OKBLUE +  str(counter) + bcolors.ENDC)
            f.write(str(counter) + "\n")
        
        print(bcolors.HEADER + "--- %s seconds ---" % (time.time() - start_time) + bcolors.ENDC)


    else:
        links = [products[i : i + 1] for i in range(0, len(products), 1)]
        for chLink in links:
            print(chLink)
            with ThreadPool(10) as pool:
                for result in pool.map(df_loops, chLink):
                    df.append(result)
            time.sleep(2)
            counter += 1
            f.write(str(counter) + "\n")


    f.close()
