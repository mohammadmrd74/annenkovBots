from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem
import time
import mysql.connector

software_names = [SoftwareName.CHROME.value]
operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]   
user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=100)
user_agent = user_agent_rotator.get_random_user_agent()
DRIVER_PATH = '/home/mohammad/Downloads/chromedriver_linux64/chromedriver'
options = Options()
options.headless = True
options.add_argument("--window-size=1920,1200")
options.add_argument('disable-blink-features=AutomationControlled')
options.add_argument(f'user-agent={user_agent}')
caps = DesiredCapabilities().CHROME


user_agent = user_agent_rotator.get_random_user_agent()


mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="sarisco123"
)

mycursor = mydb.cursor(dictionary=True)

mycursor.execute("select * from annencov.links")

links = mycursor.fetchall()

for link in links:
    if(link['brand'] == 'nike'):
        caps["pageLoadStrategy"] = "eager"
        driver = webdriver.Chrome(desired_capabilities=caps, options=options, executable_path=DRIVER_PATH)  
        print("\n\n******** NIKE *********\n\n")
        URL = link['link']
        styleNum = URL.split('/')[-1]
        print(styleNum)
        driver.get(URL)
        try:
            myElem = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="pdp-6-up"]/button[3]/div/picture[2]/img')))
            pics = []
            picsSrc = []
            pics.append(driver.find_element(By.XPATH, '//*[@id="pdp-6-up"]/button[1]/div/picture[2]/img'))
            pics.append(driver.find_element(By.XPATH, '//*[@id="pdp-6-up"]/button[2]/div/picture[2]/img'))
            pics.append(driver.find_element(By.XPATH, '//*[@id="pdp-6-up"]/button[3]/div/picture[2]/img'))
            pics.append(driver.find_element(By.XPATH, '//*[@id="pdp-6-up"]/button[4]/div/picture[2]/img'))
            # print(pics)
            for el in pics:
                picsSrc.append(el.get_attribute('src'))
                

            print(picsSrc)
            titled = driver.find_element(By.XPATH, '//*[@id="RightRail"]/div/div[1]/div/div[2]/div/h1').text
            print(titled)

            sizes = driver.find_elements(By.CLASS_NAME, 'css-xf3ahq')
            for size in sizes:
                print(size.text)

            price = driver.find_element(By.XPATH, '//*[@id="RightRail"]/div/div[1]/div/div[2]/div/div/div/div/div').text
            print(price)
        except TimeoutException:
            print("Loading took too much time!")

    
        driver.quit()

    elif(link['brand'] == 'newbalance'):
        print("\n\n******** NEWBALANCE *********\n\n")
        caps["pageLoadStrategy"] = "eager"
        driver = webdriver.Chrome(desired_capabilities=caps, options=options, executable_path=DRIVER_PATH)
        URL = link['link']
        driver.get(URL)
        try:
            myElem = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="wrap"]/a/img')))
            driver.get("https://www.newbalance.com.tr/urun/new-balance-520-411182.html")
            pics = []
            pic = driver.find_elements(By.TAG_NAME, 'img')
            for p in pic:
                src = p.get_attribute('src')
                if(src != None and src.find('medium') != -1):
                    pics.append(src)

            print(pics)

            price = driver.find_element(By.CLASS_NAME, 'urunDetay_satisFiyat').text
            print(price)

            styleNum = driver.find_element(By.ID, 'plhKisaAciklama2').text
            print(styleNum)

            nsize = driver.find_elements(By.CLASS_NAME, 'stokYok')
            # print(nsize)

            sizes = driver.find_elements(By.CLASS_NAME, 'dropdownrow')
            realSize = []
            for size in sizes:
                for ns in nsize:
                    if(ns.get_attribute('innerHTML').find(size.text) == -1):
                        realSize.append(size.text)
                        break
            
            print(realSize)
        except TimeoutException:
            print("Loading took too much time!")
        

        driver.quit()
    
    elif(link['brand'] == 'reebok'):
        print("\n\n******** REEBOK *********\n\n")
        caps["pageLoadStrategy"] = "eager"
        driver = webdriver.Chrome(desired_capabilities=caps, options=options, executable_path=DRIVER_PATH)
        URL = link['link']
        driver.get(URL)
        try:
            myElem = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'image-blur')))
            pics = []
            pic = driver.find_elements(By.CLASS_NAME, 'image-blur')
            # print(pic)
            for p in pic:
                src = p.get_attribute('src')
                pics.append(src)

            print(pics)

            title = driver.find_element(By.XPATH, '//*[@id="product"]/div[2]/div/div/div[2]/div/div[2]/div[2]/h1').text
            print(title)

            price = driver.find_element(By.XPATH, '//*[@id="product"]/div[2]/div/div/div[2]/div/div[2]/div[3]/span').text
            print(price)

            styleNum = driver.find_element(By.XPATH, '//*[@id="product"]/div[2]/div/div/div[2]/div/div[2]/p').text
            print(styleNum)

            # nsize = driver.find_elements(By.CLASS_NAME, 'stokYok')
            # # print(nsize)

            sizes = driver.find_element(By.CLASS_NAME, 'selectric-wrapper')
            sizes.click()
            print(sizes)
            time.sleep(2)
            newSizes = driver.find_elements(By.XPATH, '//*[@id="frm-addbasket"]/div[3]/div[3]/div/div/div[1]/div[3]/div/ul/li')

            for size in newSizes:
                print(size.text)
        except TimeoutException:
            print("Loading took too much time!")

        
        driver.quit()

    elif(link['brand'] == 'adidas'):
        print("\n\n******** ADIADS *********\n\n")
        caps["pageLoadStrategy"] = "normal"
        options = Options()
        options.headless = True
        options.add_argument("--window-size=1920,1200")
        options.add_argument('disable-blink-features=AutomationControlled')
        options.add_argument(f'user-agent={user_agent}')
        caps = DesiredCapabilities().CHROME
        driver1 = webdriver.Chrome(desired_capabilities=caps, options=options, executable_path=DRIVER_PATH)
        driver1.get(link['link'])

        pics = []
        time.sleep(15)
        pics.append(driver1.find_element(By.XPATH, '//*[@id="navigation-target-gallery"]/section/div[1]/div[1]/div/div[1]/div/div/img').get_attribute('src'))
        pics.append(driver1.find_element(By.XPATH, '//*[@id="navigation-target-gallery"]/section/div[1]/div[1]/div/div[2]/div/div/img').get_attribute('src'))
        pics.append(driver1.find_element(By.XPATH, '//*[@id="navigation-target-gallery"]/section/div[1]/div[1]/div/div[3]/div/div/img').get_attribute('src'))
        pics.append(driver1.find_element(By.XPATH, '//*[@id="navigation-target-gallery"]/section/div[1]/div[1]/div/div[4]/div/div/img').get_attribute('src'))
        pics.append(driver1.find_element(By.XPATH, '//*[@id="navigation-target-gallery"]/section/div[1]/div[1]/div/div[5]/div/div/img').get_attribute('src'))
        pics.append(driver1.find_element(By.XPATH, '//*[@id="navigation-target-gallery"]/section/div[1]/div[1]/div/div[6]/div/div/img').get_attribute('src'))
    
        for p in pics:
            print(p)

        title = driver1.find_element(By.XPATH, '//*[@id="app"]/div/div[1]/div/div/div/div[2]/div[2]/div[2]/div/h1/span').text
        print(title)

        price = driver1.find_element(By.XPATH, '//*[@id="app"]/div/div[1]/div/div/div/div[2]/div[2]/div[2]/div/div[2]/div[1]/div/div/div').text
        print(price)

        styleNum = link['link'].split('/')[-1]
        print(styleNum)

        
        newSizes = driver1.find_elements(By.CLASS_NAME, 'size___TqqSo')
        for size in newSizes:
            print(size.text)


        driver1.quit()
    
    elif(link['brand'] == 'puma'):
        print("\n\n******** PUMA *********\n\n")
        caps["pageLoadStrategy"] = "eager"
        driver = webdriver.Chrome(desired_capabilities=caps, options=options, executable_path=DRIVER_PATH)
        URL = link['link']
        driver.get(URL)
        try:
            # myElem = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'size___TqqSo')))
            myElem = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'gallery-item__img')))
            pics = []
            time.sleep(5)
            pics = driver.find_elements(By.CLASS_NAME, 'gallery-item__img')
            for p in pics:
                print(p.get_attribute('src'))
            

            title = driver.find_element(By.XPATH, '//*[@id="product"]/div[2]/div/div[2]/h1').text
            print(title)

            price = driver.find_element(By.XPATH, '//*[@id="product-price-183255"]/span').text
            print(price)

            styleNum = driver.find_element(By.XPATH, '//*[@id="product"]/div[2]/div/div[3]/div[2]/span[2]').text
            print(styleNum)

            dropdown = driver.find_element(By.XPATH, '//*[@id="product_addtocart_form"]/div[2]/div[2]/div[1]')
            dropdown.click();
            time.sleep(3)
            newSizes = driver.find_elements(By.CLASS_NAME, 'dropdown-box__value')
            for size in newSizes:
                print(size.text)
                
            
            # print(realSize)
        except TimeoutException:
            print("Loading took too much time!")


        driver.quit()
    
    elif(link['brand'] == 'asics'):
        print("\n\n******** ASICS *********\n\n")
        caps["pageLoadStrategy"] = "eager"
        driver = webdriver.Chrome(desired_capabilities=caps, options=options, executable_path=DRIVER_PATH)
        URL = link['link']
        driver.get(URL)
        try:
            # myElem = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'size___TqqSo')))
            myElem = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'swiper-lazy')))
            picsImage = []
            time.sleep(5)
            pics = driver.find_elements(By.CLASS_NAME, 'swiper-lazy')
            
            for p in pics:
                if(p.get_attribute('src').find('livephotos') != -1):
                    picsImage.append(p.get_attribute('src'))
            
            print(picsImage)

            title = driver.find_element(By.XPATH, '//*[@id="product-details-form"]/div/div[1]/div[2]/div/h1/span[1]').text
            print(title)

            price = driver.find_element(By.XPATH, '//*[@id="product-details-form"]/div/div[1]/div[2]/div/div[1]/div/span').text
            print(price)

            styleNum = driver.find_element(By.XPATH, '//*[@id="product-details-form"]/div/div[1]/div[2]/div/h1/span[2]').text
            print(styleNum)

            newSizes = driver.find_elements(By.CLASS_NAME, 'custom-control-description')
            # dropdown.click();
            # time.sleep(3)
            # newSizes = driver.find_elements(By.CLASS_NAME, 'dropdown-box__value')
            for size in newSizes:
                if(size.text):
                    print(size.text)
                
            
            # print(realSize)
        except TimeoutException:
            print("Loading took too much time!")


        driver.quit()

    elif(link['brand'] == 'underarmour'):
        print("\n\n******** underarmour *********\n\n")
        caps["pageLoadStrategy"] = "eager"
        driver = webdriver.Chrome(desired_capabilities=caps, options=options, executable_path=DRIVER_PATH)
        URL = link['link']
        driver.get(URL)
        try:
            myElem = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'js-product-main-image')))
            time.sleep(5)
            title = driver.find_element(By.XPATH, '/html/body/div[4]/div[4]/div[1]/div[2]/div/div[1]/div[2]/h1').text
            price = driver.find_element(By.XPATH, '/html/body/div[4]/div[4]/div[1]/div[2]/div/div[1]/div[3]/div/div/pz-price').text
            print(price)

            styleNum = driver.find_element(By.XPATH, '/html/body/div[4]/div[4]/div[1]/div[2]/div/div[1]/div[4]/div').text
            print(styleNum)

            print(title)
            picsImage = []


            #  newSizes = driver.find_elements(By.CLASS_NAME, 'custom-control-description')
            # dropdown.click();
            # time.sleep(3)
            newSizes = driver.find_elements(By.CLASS_NAME, 'pz-variant__option')
            for size in newSizes:
                if(size.text):
                    print(size.text)


            mainpic = driver.find_element(By.CLASS_NAME, 'js-product-main-image')

            mainpic.click()
            time.sleep(5)
            pics = driver.find_elements(By.CLASS_NAME, 'lg-image')
            
            for p in pics:
                picsImage.append(p.get_attribute('src'))
            
            print(picsImage)
        except TimeoutException:
            print("Loading took too much time!")


        driver.quit()

    elif(link['brand'] == 'northface'):
        print("\n\n******** northface *********\n\n")
        caps["pageLoadStrategy"] = "eager"
        driver = webdriver.Chrome(desired_capabilities=caps, options=options, executable_path=DRIVER_PATH)
        URL = link['link']
        driver.get(URL)
        try:
            myElem = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'bl-main')))
            picsImage = []
            pics = driver.find_elements(By.CLASS_NAME, 'bl-main')
            
            for p in pics:
                picsImage.append(p.get_attribute('src'))
        
            print(picsImage)
            # title = driver.find_element(By.XPATH, '/html/body/div[4]/div[4]/div[1]/div[2]/div/div[1]/div[2]/h1').text
            # print(title)

            price = driver.find_element(By.XPATH, '//*[@id="product-info"]/div[1]/span').text
            print(price)

            styleNum = driver.find_element(By.XPATH, '//*[@id="product-form"]/div[3]/div/div[2]/ul/li/div[2]').text
            print(styleNum)

            # picsIm 


            newSizes = driver.find_elements(By.CLASS_NAME, 'limited-stock')
            for size in newSizes:
                print(size.text)

            newSizes = driver.find_elements(By.CLASS_NAME, 'last-stock')
            for size in newSizes:
                print(size.text)
        except TimeoutException:
            print("Loading took too much time!")


        driver.quit()
           
    elif(link['brand'] == 'salomon'):
        print("\n\n******** salomon *********\n\n")
        caps["pageLoadStrategy"] = "eager"
        driver = webdriver.Chrome(desired_capabilities=caps, options=options, executable_path=DRIVER_PATH)
        URL = link['link']
        driver.get(URL)
        try:
            myElem = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'js-fancybox-lg')))
            picsImage = []
            pics = driver.find_elements(By.CLASS_NAME, 'js-fancybox-lg')
            
            for p in pics:
                picsImage.append(p.get_attribute('src'))
        
            print(picsImage)
            title = driver.find_element(By.XPATH, '//*[@id="ProductPage"]/div[1]/div[1]/div/div[2]/div[1]/div/div[2]').text
            print(title)

            price = driver.find_element(By.XPATH, '//*[@id="ProductPage"]/div[1]/div[1]/div/div[2]/div[1]/div/div[3]/div').text
            print(price)

            newSizes = driver.find_elements(By.XPATH, '//*[@id="ProductPage"]/div[1]/div[1]/div/div[2]/div[3]/div[2]/select/option')
            newSizesDis = driver.find_elements(By.CLASS_NAME, 'not-selectable')
            newSizesDisA = []
            for nds in newSizesDis:
                newSizesDisA.append(nds.text)

            for size in newSizes:
                if(newSizesDisA.count(size.text) == 0):
                    print(size.text)
        except TimeoutException:
            print("Loading took too much time!")


        driver.quit()

    elif(link['brand'] == 'converse'):
        print("\n\n******** converse *********\n\n")
        caps["pageLoadStrategy"] = "eager"
        driver = webdriver.Chrome(desired_capabilities=caps, options=options, executable_path=DRIVER_PATH)
        URL = link['link']
        driver.get(URL)
        try:
            myElem = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'js-fancybox-lg')))
            picsImage = []
            pics = driver.find_elements(By.CLASS_NAME, 'js-fancybox-lg')
            
            for p in pics:
                picsImage.append(p.get_attribute('src'))
        
            print(picsImage)
            title = driver.find_element(By.XPATH, '//*[@id="ProductPage"]/div[1]/div/div[2]/div[2]/div/div[1]').text
            print(title)

            price = driver.find_element(By.XPATH, '//*[@id="ProductPage"]/div[1]/div/div[2]/div[2]/div/div[2]/div').text
            print(price)

            styleNum = driver.find_element(By.XPATH, '//*[@id="ProductPage"]/div[1]/div/div[2]/div[3]/div[2]/span').text
            print(styleNum)

            newSizes = driver.find_elements(By.TAG_NAME, '//*[@id="ProductPage"]/div[1]/div/div[2]/div[5]/div[2]/select/option')
            for size in newSizes:
                if(size.get_attribute('disabled') == None):
                    print(size.text)
        except TimeoutException:
            print("Loading took too much time!")


        driver.quit()

    elif(link['brand'] == 'mizuno'):
        print("\n\n******** mizuno *********\n\n")
        caps["pageLoadStrategy"] = "eager"
        driver = webdriver.Chrome(desired_capabilities=caps, options=options, executable_path=DRIVER_PATH)
        URL = link['link']
        driver.get(URL)
        try:
            myElem = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'imgInner')))
            time.sleep(3)
            picsImage = []
            pics = driver.find_elements(By.CLASS_NAME, 'imgInner')
            
            for p in pics:
                pl = p.find_element(By.TAG_NAME, 'img').get_attribute('src')
                if(pl.find("-K") == -1):
                    picsImage.append(pl)
        
            print(picsImage)

            title = driver.find_element(By.XPATH, '//*[@id="productName"]').text
            print(title)

            price = driver.find_element(By.XPATH, '//*[@id="price-flexer"]/div[2]/div/span').text
            print(price)

            styleNum = driver.find_element(By.XPATH, '//*[@id="supplier-question"]/div[1]/span').text
            print(styleNum)


            mainpic = driver.find_element(By.XPATH, '//*[@id="mobileBuyBtn"]/div[1]/div[2]/div/div[1]/div')

            mainpic.click()
            time.sleep(1)
            
            newSizes = driver.find_elements(By.XPATH, '//*[@id="mobileBuyBtn"]/div[1]/div[2]/div/div[1]/div/div[1]/a')
            for size in newSizes:
                print(size.text)
        except TimeoutException:
            print("Loading took too much time!")


        driver.quit()

    elif(link['brand'] == 'lacoste'):
        print("\n\n******** lacoste *********\n\n")
        caps["pageLoadStrategy"] = "eager"
        driver = webdriver.Chrome(desired_capabilities=caps, options=options, executable_path=DRIVER_PATH)
        URL = link['link']
        driver.get(URL)
        try:
            myElem = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'js-popup-image__toggle')))
            time.sleep(2)
            picsImage = []
            pics = driver.find_elements(By.CLASS_NAME, 'js-popup-image__toggle')
            
            for p in pics:
                pl = p.find_element(By.TAG_NAME, 'img').get_attribute('src')
                picsImage.append(pl)
        
            print(picsImage[0:5])

            title = driver.find_element(By.XPATH, '/html/body/div[3]/div[1]/div[2]/div[1]/div[3]/div[3]/div[1]/div[2]/div[2]/div[1]/div[1]/div[1]/div/div[1]/h1').text
            print(title)

            price = driver.find_element(By.XPATH, '/html/body/div[3]/div[1]/div[2]/div[1]/div[3]/div[3]/div[1]/div[2]/div[2]/div[1]/div[1]/div[1]/div/div[2]/div[1]/span').text
            print(price)

            styleNum = driver.find_element(By.XPATH, '/html/body/div[3]/div[1]/div[2]/div[1]/div[3]/div[3]/div[2]/div/div/div[1]/div/div[1]/div/div[2]/p').text
            print(styleNum)






            cookie = driver.find_element(By.CLASS_NAME, 'js-cookie-consent-accept')
            time.sleep(1)
            cookie.click()

            
            mainpic = driver.find_element(By.XPATH, '/html/body/div[3]/div[1]/div[2]/div[1]/div[3]/div[3]/div[1]/div[2]/div[2]/div[1]/div[2]/div[1]/div[1]/a')
            mainpic.click()
            time.sleep(1)
            
            newSizes = driver.find_elements(By.XPATH, '/html/body/div[3]/div[1]/div[2]/div[1]/div[3]/div[3]/div[1]/div[2]/div[2]/div[1]/div[1]/div[2]/div/div[2]/div[2]/div[2]/div/div/div/ul/li')
            for size in newSizes:
                if(size.text):
                    print(size.text)
        except TimeoutException:
            print("Loading took too much time!")


        driver.quit()

    elif(link['brand'] == 'ecco'):
        print("\n\n******** ecco *********\n\n")
        caps["pageLoadStrategy"] = "eager"
        driver = webdriver.Chrome(desired_capabilities=caps, options=options, executable_path=DRIVER_PATH)
        URL = link['link']
        driver.get(URL)
        try:
            myElem = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'ImgArea')))
            time.sleep(1)
            picsImage = []
            pics = driver.find_elements(By.CLASS_NAME, 'ImgArea')
            
            for p in pics:
                pl = p.get_attribute('href')
                picsImage.append(pl)
        
            print(picsImage[0:3])

            title = driver.find_element(By.XPATH, '//*[@id="NewPd"]/div[3]/div/div[1]/div/h1').text
            print(title)

            price = driver.find_element(By.CLASS_NAME, 'Price').text
            print(price)

            styleNum = driver.find_element(By.XPATH, '//*[@id="NewPd"]/div[3]/div/div[1]/div/span/span').text
            print(styleNum)

            sizeEl = driver.find_element(By.XPATH, '//*[@id="NewPd"]/div[3]/div/div[3]/div[2]/div')
            
            newSizes = sizeEl.find_elements(By.TAG_NAME, 'span')
            for size in newSizes:
                if(size.text):
                    print(size.text)
        except TimeoutException:
            print("Loading took too much time!")


        driver.quit()
           
           
           
        

