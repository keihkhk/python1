from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import pyautogui
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains

import polars as pl
from bs4 import BeautifulSoup
import cv2
import re
import os
import subprocess
import sys
import time
import array
import datetime
import dateutil.parser

# "C:\Program Files\Google\Chrome\Application\chrome.exe" -remote-debugging-port=9222 --user-data-dir="適当なパス（chromeのデータがいっぱいできても良い場所）
# をcmdで開く"


def find_and_click(driver, target_image):
    # ズーム率とスクロール位置を固定
    driver.execute_script("document.body.style.zoom='100%'")
    driver.execute_script("window.scrollTo(0, 0)")

    # 1. スクリーンショットを撮る
    driver.save_screenshot("screenshot.png")

    # 2. スクリーンショットとターゲット画像をOpenCVで読み込む
    screenshot = cv2.imread("screenshot.png", cv2.IMREAD_GRAYSCALE)
    template = cv2.imread(target_image, cv2.IMREAD_GRAYSCALE)
    w, h = template.shape[::-1]

    # 3. テンプレートマッチングを行う
    res = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)

    # 4. 最もマッチ度の高い位置を見つける
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

    # 一番マッチング度合いが高い位置を取得
    top_left = max_loc

    # マッチングした領域の中心を取得
    center_loc = (
        top_left[0] + template.shape[1] // 2,
        top_left[1] + template.shape[0] // 2,
    )

    # (0,0) への移動
    action0 = ActionChains(driver)
    action0.move_by_offset(0, 0)
    action0.perform()
    print(max_loc)
    # 5. 見つけた位置をクリックする
    x, y = center_loc[0], center_loc[1]  # この位置が最もマッチ度の高い位置

    # クリックする要素を取得
    element = driver.execute_script(f"return document.elementFromPoint({x}, {y});")

    # 要素をクリック
    driver.execute_script("arguments[0].click();", element)
    # driver.execute_script("document.elementFromPoint({}, {}).click()".format(x, y))

    print(x, y)
    time.sleep(1)


options = Options()
options.add_experimental_option("detach", True)

extension_path = "C:/Users/yutok/AppData/Local/Google/Chrome/User Data/Profile 3/Extensions/nkbihfbeogaeaoehlefnkodbefgpgknn/10.26.1_0"

options.add_argument(
    "user-data-dir=C:/Users/yutok/AppData/Local/Google/Chrome/User Data"
) 
# path to user profile directory
options.add_argument("--profile-directory=Profile 3")
options.add_argument("--no-sandbox")
# options.add_argument("--headless")


# options.add_argument(f'load-extension={extension_path}')


webdriver_path = "C:/Users/yutok/selenium/chromedriver.exe"

service = Service(executable_path=webdriver_path)
driver = webdriver.Chrome(service=service, options=options)


page_url = "https://link3.to/event/all"
driver.get(page_url)

driver.save_screenshot("screenshot.png")

time.sleep(5)

find_and_click(driver, "./auto/image/w3st.png")

find_and_click(driver, "./auto/image/venue.png")

time.sleep(3)

find_and_click(driver, "./auto/image/twitterlink3.png")

find_and_click(driver, "./auto/image/trending.png")

find_and_click(driver, "./auto/image/upcoming.png")

time.sleep(3)

# 初期化
SCROLL_PAUSE_TIME = 2  # スクロールごとの待ち時間

# Get scroll height
last_height = driver.execute_script("return document.body.scrollHeight")

while True:
    # Scroll down to bottom
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # Wait to load page
    time.sleep(SCROLL_PAUSE_TIME)

    # Calculate new scroll height and compare with last scroll height
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height

html = driver.page_source
soup = BeautifulSoup(html, "html.parser")

# HTMLデータをファイルに保存します
with open("page.html", "w", encoding="utf-8") as file:
    file.write(html)

elements = soup.find_all("a")
button_elements = soup.find_all("button")  # buttonタグを取得

link_texts = []
dates = []

date_pattern = r"(Today|Tomorrow|in \d+ days) at (\d{1,2}:\d{2} (AM|PM))"

for element in elements:
    href = element.get("href")
    if href and "https://link3.to/e/" in href:
        link_texts.append(href)

for button in button_elements:
    button_text = button.text  # buttonのテキストを取得
    date_match = re.search(date_pattern, button_text, re.IGNORECASE)  # テキストから日付を検索、大文字と小文字を区別しない 
    if date_match:
        date_string = date_match.group()  # 日付テキスト全体を取得
        dates.append(date_string)

print(link_texts)
print(dates)

# link_textsとdatesの要素数を取得
link_texts_len = len(link_texts)
dates_len = len(dates)

# link_textsとdatesの要素数を一致させる
if link_texts_len < dates_len:
    # link_textsの要素数が少ない場合、不足分を空文字で補う
    link_texts += [""] * (dates_len - link_texts_len)
else:
    # datesの要素数が少ない場合、不足分を空文字で補う
    dates += [""] * (link_texts_len - dates_len)

# データフレームの作成
df = pl.DataFrame({"link_text": link_texts, "date": dates})

# データフレームをCSVファイルとして保存
df.write_csv("links_data.csv")

driver.quit()

