from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import sqlite3
from datetime import datetime

# تنظیمات Chrome در حالت هدلس
chrome_options = Options()
chrome_options.add_argument("--headless")  # اجرای بدون رابط کاربری
chrome_options.add_argument("--no-sandbox")  # جلوگیری از مشکلات سطح دسترسی
chrome_options.add_argument("--disable-dev-shm-usage")  # استفاده بهینه از حافظه
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")  # تنظیم اندازه صفحه برای جلوگیری از خطاهای نمایش
chrome_options.add_argument("--remote-debugging-port=9222")
# مسیر Chromedriver
driver_path = "/home/faraz/chromedriver"
service = Service(driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

conn = sqlite3.connect("gold_prices.db")
cursor = conn.cursor()

def setup_database():
    cursor.execute('''CREATE TABLE IF NOT EXISTS verbal_gold_price (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        price TEXT,
                        timestamp TEXT
                      )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS global_gold_price (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        price TEXT,
                        timestamp TEXT
                      )''')
    conn.commit()

setup_database()

# تابع ورود به سایت
def login(driver):
    login_url = "https://faraz.io/account/login"
    driver.get(login_url)

    username = "122912048"
    password = "aA09193709649@"

    username_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )
    username_field.send_keys(username)

    password_field = driver.find_element(By.NAME, "password")
    password_field.send_keys(password)
    password_field.send_keys(Keys.RETURN)

    WebDriverWait(driver, 15).until(EC.url_contains("dashboard"))

# تابع ذخیره قیمت در دیتابیس
def save_price(table_name, price):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(f"INSERT INTO {table_name} (price, timestamp) VALUES (?, ?)", (price, timestamp))
    conn.commit()

# تابع راه‌اندازی مرورگر
def start_browser():
    return webdriver.Chrome(service=service, options=chrome_options)

# حلقه اصلی اجرای اسکرپر
while True:
    driver = start_browser()

    try:
        login(driver)
        dashboard_url = "https://faraz.io/dashboard?s=XAU_USD&i=1&a=draft&adj=2&widget=watch-list"
        driver.get(dashboard_url)

        freeze_count = 0
        last_verbal_price = None
        last_global_price = None

        while True:
            try:
                # بررسی پیام نشست پایان یافته
                session_error_element = driver.find_elements(By.XPATH, '/div/div/div')
                if session_error_element:
                    print("Session expired, restarting login...")
                    break

                verbal_price_element = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="root"]/div[1]/div[1]/div/div[1]/div[2]/div[3]/div[4]/div/div/div/div/div/div[3]/div[3]'))
                )
                global_price_element = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="root"]/div[1]/div[1]/div/div[1]/div[2]/div[3]/div[4]/div/div/div/div/div/div[2]/div[3]'))
                )

                verbal_price = verbal_price_element.text
                global_price = global_price_element.text

                print("Verbal Gold Price:", verbal_price)
                print("Global Gold Price:", global_price)

                if verbal_price != last_verbal_price:
                    save_price("verbal_gold_price", verbal_price)
                    last_verbal_price = verbal_price

                if global_price != last_global_price:
                    save_price("global_gold_price", global_price)
                    last_global_price = global_price

                freeze_count = 0  # بازنشانی شمارنده فریز

            except Exception as e:
                print("Error during execution:", e)
                freeze_count += 1

                if freeze_count >= 10:
                    print("Restarting browser...")
                    break

            time.sleep(1)

    except Exception as e:
        print("Critical error, restarting browser:", e)

    finally:
        driver.quit()

