from http.client import OK
from logging import getLogger

from requests import get, post

from bs4 import BeautifulSoup

LOGIN_URL = "http://phc.prontonetworks.com/cgi-bin/authlogin"
LOGOUT_URL = "http://phc.prontonetworks.com/cgi-bin/authlogout"

LOGIN_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'Cache-Control': 'none',
    'Connection': 'keep-alive',
    'Content-Length': '80',
    'Content-Type': 'application/x-www-form-urlencoded',
    'DNT': '1',
    'Host': 'phc.prontonetworks.com',
    'Origin': 'http://phc.prontonetworks.com',
    'Referer': 'http://phc.prontonetworks.com/cgi-bin/authlogin',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'
}

LOGOUT_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'Connection': 'keep-alive',
    'DNT': '1',
    'Host': 'phc.prontonetworks.com', 'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'
}

HTML_PARSER = 'html.parser'


logger = getLogger(__name__)

def parse_login_response(html: bytes) -> str:
    soup = BeautifulSoup(html, HTML_PARSER)
    logger.debug(soup.find('b'))
    if title := soup.find('title'):

        if title.text.strip().lower() == "successful pronto authentication":
            return 'login-success'

        elif title.text.strip().lower() == "volswifi authentication":
            error = soup.find('td', {'class': "errorText10"}).text.strip().lower()  # type: ignore

            standard_errors = {
                "sorry, please check your username and password and try again.": 'password-failure',
                "sorry, that account does not exist": 'id-failure'
            }

            if error in standard_errors:
                return standard_errors[error]

            else:
                raise ValueError(f"Got title {title} but invalid error {error}.")

        else:
            raise ValueError(f"Invalid title {title}.")

    elif soup.find('b') and soup.find('b').text.strip().lower() == "you are already logged in":  # type: ignore
        return 'session-exists'

    else:
        raise ValueError(f"Invalid page {soup}.")


def parse_logout_response(html: bytes) -> str:
    soup = BeautifulSoup(html, HTML_PARSER)

    if title := soup.find('title'):
        title = title.text.strip().lower()

        if title == "logout failure":
            return 'logout-failure'

        elif title == "logout successful":
            return 'logout-success'

        else:
            raise ValueError(f"Invalid title {title}.")
            
    else:
        raise ValueError(f"Invalid page {soup}.")


def login(credentials: dict[str, str]) -> str:
    login_payload = {
        'serviceName': 'ProntoAuthentication',
        'Submit22': 'Login',
        'userId': credentials['register-number'],
        'password': credentials['password']
    }

    login_request = post(
        LOGIN_URL,
        data=login_payload,
        headers=LOGIN_HEADERS
    )

    if int(login_request.status_code == OK):
        logger.info("Login request acknowledged.")

        logger.debug(login_request.content)

        parsed_response_status = parse_login_response(login_request.content)
        logger.info("Response parsed.")

        return parsed_response_status

    else:
        raise ConnectionError(f"The server returned status code {login_request.status_code}.")


def logout() -> str:
    logout_request = get(
        url=LOGOUT_URL,
        headers=LOGOUT_HEADERS
    )

    if int(logout_request.status_code == OK):
        logger.info("Logout request acknowledged.")

        parsed_response_status = parse_logout_response(logout_request.content)
        logger.info("Response parsed.")

        return parsed_response_status

    else:
        raise ConnectionError(f"The server returned status code {logout_request.status_code}.")
