from os import system
from time import time, sleep
from json import loads
from requests import post, get
from secrets import token_hex
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def rnd() -> str:
    return token_hex(8)

def tempmail_headers() -> dict:
    return {
        'authority': 'tempail.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'tr-TR,tr;q=0.9',
        'cache-control': 'max-age=0',
        'referer': 'https://tempail.com/en/',
        'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    }

def tempmail_get() -> tuple or None:
    trying = 0
    while True:
        try:
            response = get(
                'https://tempail.com/en/',
                headers=tempmail_headers(),
                proxies={'http': f'http://{proxy}', 'https': f'http://{proxy}'}
            )
            res_text = response.text

            email = res_text.split('adres-input" value="')[1].split('"')[0]
            session = res_text.split('var oturum="')[1].split('"')[0]
            phpsid = response.cookies.get("PHPSESSID")

            return email, session, phpsid
        except Exception as e:
            print(f"[-] Get email error => {e}")
        trying += 1
        if trying == 5:
            return None
        sleep(1)

def tempmail_code(session: str, phpsid: str) -> str:
    sleep(5)
    payload = {
        'oturum': session,
        'tarih': str(time()*1000)[:10],
        'geri_don': 'https://tempail.com/en/',
    }
    trying = 0
    while True:
        try:
            response = post(
                "https://tempail.com/en/api/kontrol/",
                headers=tempmail_headers(),
                data=payload,
                cookies={'PHPSESSID': phpsid},
                proxies={'http': f'http://{proxy}', 'https': f'http://{proxy}'}
            ).text
            if 'baslik' in response and 'Waiting for emails' not in response:
                if 'Opera' in response:
                    mail_no = response.split('mail_')[1].split('"')[0]
                    response = post(
                        f"https://tempail.com/en/api/icerik/?oturum={session}&mail_no={mail_no}",
                        headers=tempmail_headers(),
                        cookies={'PHPSESSID': phpsid},
                        proxies={'http': f'http://{proxy}', 'https': f'http://{proxy}'}
                    ).text
                    return "https://auth.opera.com/" + response.split('https://auth.opera.com/')[1].split('"')[0]
                else:
                    return ""
        except Exception as e:
            print(f"[-] Get code error => {e}")
        if trying == 15:
            print("[-] Code did not arrive")
            return ""
        trying += 1
        sleep(2)

def browser() -> webdriver.Chrome:
    options = Options()
    options.add_argument('--log-level=3')
    options.add_argument("--lang=en")
    options.add_argument('--no-sandbox')
    options.add_argument('--start-maximized')
    options.add_argument('--single-process')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("disable-infobars")

    proxy_options = {
        'proxy': {
            'http': 'http://' + proxy,
            'https': 'https://' + proxy,
            'no_proxy': 'localhost,127.0.0.1'
        }
    }

    driver = webdriver.Chrome(options=options, seleniumwire_options=proxy_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source":
            "const newProto = navigator.__proto__;"
            "delete newProto.webdriver;"
            "navigator.__proto__ = newProto;"
    })
    driver.implicitly_wait(10)

    return driver

def register(driver: webdriver.Chrome, email: str, password: str) -> bool:
    try:
        driver.get("https://auth.opera.com/account/authenticate/email")
        sleep(2)

        driver.find_element(By.ID, "email").send_keys(email)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        sleep(5)
        driver.find_element(By.ID, "newPassword").send_keys(password)
        sleep(0.3)
        driver.find_element(By.ID, "repeatPassword").send_keys(password)
        sleep(0.3)
        driver.find_element(By.XPATH, "//button[@class='primaryButton']").click()
        sleep(5)

        if driver.current_url == "https://auth.opera.com/account/edit-profile":
            return True
    except Exception as e:
        print(f"[!] Register error => {e}")
    return False

def verify_email(driver: webdriver.Chrome, verify_url: str) -> bool:
    driver.get(verify_url.replace('amp;', ''))
    sleep(5)

    if driver.current_url == "https://auth.opera.com/account/email-verification/result?service=auth":
        return True
    return False

def gx_me(driver: webdriver.Chrome) -> bool:
    try:
        driver.get("https://gx.me/tr/")
        sleep(2)
        driver.find_element(By.XPATH, "/html/body/div[4]/div/div/div/div/div[3]/button[1]").click()
        sleep(1)
        driver.find_elements(By.XPATH, "//button")[0].click()
        sleep(2)
        driver.find_element(By.XPATH, "//ul/li/div").click()
        sleep(3)
        driver.find_element(By.NAME, "username").send_keys(rnd())
        driver.find_element(By.XPATH, "//button[@class='primaryButton']").click()
        sleep(6)

        return True
    except Exception as e:
        print(f"[!] Gx error => {e}")
    return False

def get_token(driver: webdriver.Chrome) -> str:
    driver.get("https://api.gx.me/profile/token")
    sleep(2)

    token = loads(driver.find_element(By.XPATH, "//pre").text)

    return token["data"]

def get_promocode(auth: str) -> str:
    try:
        headers = {
            "Accept": "*/*",
            "Origin": "https://www.opera.com",
            "Referer": "https://www.opera.com/",
            "Sec-Ch-Ua": '"Not A(Brand";v="99", "Opera GX";v="107", "Chromium";v="121"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "Authorization": auth,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 OPR/107.0.0.0"
        }
        token = post('https://discord.opr.gg/v2/direct-fulfillment', headers=headers, proxies=proxies).json()["token"]
        return token
    except:
        pass
    return ""

def start() -> None:
    while True:
        try:
            email, session, phpsid = tempmail_get()
            password = rnd() + "*"

            print("[+] Email alındı =>", email)

            driver = browser()
            if register(driver, email, password):
                print(f"[+] Hesap açıldı => {email}:{password}")
                code = tempmail_code(session, phpsid)
                if code != "":
                    if verify_email(driver, code):
                        print("[+] Email confirmed")
                        if gx_me(driver):
                            auth = get_token(driver)
                            token = get_promocode(auth)
                            if token != "":
                                open("codes.txt", "a+").write(f"{code_url}{token}" + "\n")
                                open("accounts.txt", "a+").write(f"{email}{password}" + "\n")
                                print(f"[+] Nitro code generated => {token}")
                            else:
                                print(f"[-] Nitro code could not be generated => {token}")
                        else:
                            print("[-] Auth token could not be received")
                    else:
                        print("[-] Email not confirmed")
                else:
                    print("[-] Email code did not arrive")

            driver.close()
        except Exception as e:
            print(f"[!] Main error => {e}")

if __name__ == '__main__':
    system("title Nitro Generator ^| @hiddenexe")
    code_url = "https://discord.com/billing/partner-promotions/1180231712274387115/"

    proxy = 'user:pass@ip:port'
    proxies = {
        'http': f'http://{proxy}',
        'https': f'http://{proxy}'
    }
    #proxies = None

    start()


#code By Scrxll

