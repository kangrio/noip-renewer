import os
import sys
import requests
from bs4 import BeautifulSoup
import re
from pyotp import *
from time import sleep
from dotenv import load_dotenv
from string import Template

load_dotenv()

USERNAME = os.environ.get("NOIP_USERNAME")
PASSWORD = os.environ.get("NOIP_PASSWORD")
TOTP_SECRET = os.environ.get("NOIP_TOTP_SECRET")

if not USERNAME or not PASSWORD or not TOTP_SECRET:
    print("❌ Error: NOIP_SERNAME and NOIP_PASSWORD and NOIP_TOTP_SECRET must be set")
    sys.exit(1)

LOGIN_URL = "https://www.noip.com/login"
LOGOUT_URL = "https://my.noip.com/auth/logout"
VERIFY_URL = "https://www.noip.com/2fa/verify"
DASHBOARD_URL = "https://my.noip.com"
DNS_RECORD_URL = "https://my.noip.com/dns/records"
VERIFY_URL_TEMPLATE = Template("https://my.noip.com/ajax/host/$id/touch")


class Renewer:
    session: requests.Session = None
    current_csrf_token = None
    records_soup: BeautifulSoup = None

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

    def get_2fa_code(self) -> str:
        return str(TOTP(TOTP_SECRET).now())

    def renew(self) -> bool:
        try:
            if not self.login():
                return False
            if not self.verify_2fa():
                return False

            print("✅ Login successful")

            self.pull_records()

            if not self.confirm():
                return False

            print("✅ Confirm sussessul")
            return True
        except requests.Timeout:
            print("❌ Request timed out")
            return False
        except requests.RequestException as e:
            print(f"❌ Network error: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
        finally:
            self.logout()
            self.session.close()

    def pull_records(self):
        print("⌛ Pulling records")

        self.records_soup = response = self.session.get(
            DNS_RECORD_URL,
            headers={"Referer": DASHBOARD_URL},
            timeout=10,
            allow_redirects=True,
        )

        response.raise_for_status()
        self.records_soup = BeautifulSoup(response.content, "html.parser")
        
        print("✅ Pulling successful")

    def get_csrf_token(self, soup: BeautifulSoup):
        token = soup.find("meta", attrs={"name": ["csrf-token", "token"]})

        if token and token.get("content"):
            return token["content"]

        print("❌ Could not find CSRF token")
        return self.current_csrf_token

    def login(self) -> bool:
        # 1. Get login page
        print(f"⌛ Logging in as {USERNAME} ...")

        login_page = self.session.get(LOGIN_URL, timeout=10)
        login_page.raise_for_status()
        soup = BeautifulSoup(login_page.content, "html.parser")
        self.current_csrf_token = self.get_csrf_token(soup)

        # 2. Submit login
        payload = {
            "_token": self.current_csrf_token,
            "username": USERNAME,
            "password": PASSWORD,
            "submit_login_page": "1",
            "intended_hash": "",
            "g-recaptcha-response": "",
            "should_show_questionnaire": "",
        }

        response = self.session.post(
            LOGIN_URL,
            data=payload,
            headers={"Referer": LOGIN_URL},
            timeout=10,
            allow_redirects=True,
        )
        response.raise_for_status()

        if response.url != VERIFY_URL:
            print("❌ Login unsuccessful")
            print("❌ username or password incorrect")
            return False

        soup = BeautifulSoup(response.content, "html.parser")
        self.current_csrf_token = self.get_csrf_token(soup)
        return True

    def verify_2fa(self) -> bool:
        # 1. get 2fa code
        print("⌛ Verifying code ...")
        code = self.get_2fa_code()
        payload = {
            "type": "totp",
            "challenge_code": code,
            "submit": "Verify",
            "_token": self.current_csrf_token,
        }
        # 2. Submit 2Fa code
        response = self.session.post(
            VERIFY_URL,
            data=payload,
            headers={"Referer": VERIFY_URL},
            timeout=10,
            allow_redirects=True,
        )
        response.raise_for_status()

        if response.url != DASHBOARD_URL:
            print("❌ 2FA code incorrect")
            return False

        soup = BeautifulSoup(response.content, "html.parser")
        self.current_csrf_token = self.get_csrf_token(soup)
        return True

    def get_host_id(self) -> str:
        soup = self.records_soup

        tag = soup.select_one('[data-label^="host="]')
        if tag:
            host_id = tag["data-label"].replace("host=", "")
            return host_id
        return None

    def get_host_name(self) -> str:
        soup = self.records_soup
        tag = soup.select_one("[data-fqdm]")
        if tag:
            return tag["data-fqdm"]

        return None

    def get_need_confirm_hosts(self):
        soup = self.records_soup

        zone_collection = soup.find("div", {"id": "zone-collection-wrapper"})
        records = zone_collection.find_all(
            "div", id=re.compile(r"^expiration-banner-hostname-")
        )

        return records

    def confirm_with_link(self, link: str) -> bool:
        response = self.session.get(
            link,
            headers={"Referer": DNS_RECORD_URL, "HX-Request": "true"},
            timeout=10,
            allow_redirects=True,
        )

        response.raise_for_status()

        parsed = response.json()  # ✅ easiest way
        success = parsed.get("success")  # ✅ correct

        return success

    def confirm(self) -> bool:
        need_confirm = self.get_need_confirm_hosts()
        if len(need_confirm) > 0:
            host_name = self.get_host_name()
            print(f"⌛ Confirming: {host_name}")
            host_id = self.get_host_id()
            confirm_link = VERIFY_URL_TEMPLATE.substitute(id=host_id)
            return self.confirm_with_link(confirm_link)

        print("✅ No need to confirm")

        return False

    def logout(self) -> bool:
        response = self.session.get(
            LOGOUT_URL,
            headers={"Referer": DASHBOARD_URL},
            timeout=10,
            allow_redirects=True,
        )
        response.raise_for_status()

        if response.url != "https://www.noip.com/login?ref_url=console":
            print("❌ Logout unsuccessful")
            return False

        print("✅ Logout successful")
        return True


if __name__ == "__main__":
    renewer = Renewer()
    sys.exit(int(renewer.renew()))
