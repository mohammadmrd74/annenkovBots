

from matplotlib import style
from matplotlib.pyplot import title
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import time

software_names = [SoftwareName.CHROME.value]
operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]   
user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=100)

user_agent = user_agent_rotator.get_random_user_agent()
print(user_agent)

DRIVER_PATH = '/home/mohammad/Downloads/chromedriver_linux64/chromedriver'
options = Options()
options.headless = True
options.add_argument("--window-size=1920,1200")
options.add_argument('disable-blink-features=AutomationControlled')
options.add_argument(f'user-agent={user_agent}')
caps = DesiredCapabilities().CHROME
# print(caps)
caps["pageLoadStrategy"] = "eager"

driver = webdriver.Chrome(desired_capabilities=caps, options=options, executable_path=DRIVER_PATH)

driver.get("https://tr.ecco.com/tr/siyah-ecco-citytray-lite-loafer_52162401001-1271")

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






    # cookie = driver.find_element(By.CLASS_NAME, 'js-cookie-consent-accept')
    # time.sleep(1)
    # cookie.click()

    
    # mainpic = driver.find_element(By.XPATH, '/html/body/div[3]/div[1]/div[2]/div[1]/div[3]/div[3]/div[1]/div[2]/div[2]/div[1]/div[2]/div[1]/div[1]/a')
    # mainpic.click()
    # time.sleep(1)

    sizeEl = driver.find_element(By.XPATH, '//*[@id="NewPd"]/div[3]/div/div[3]/div[2]/div')
    
    newSizes = sizeEl.find_elements(By.TAG_NAME, 'span')
    for size in newSizes:
        if(size.text):
            print(size.text)
    
except TimeoutException:
    print("Loading took too much time!")


driver.quit()