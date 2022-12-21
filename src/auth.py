"""
communicate with the server
- defines login/logout headers and URLs
- sends the login/logout requests
- parses the server responses
"""

from http.client import OK
from logging import getLogger
from os import popen
from platform import system as get_os_name
from re import match

from bs4 import BeautifulSoup
from requests import ConnectionError, get, post

# URLs for the service
LOGIN_URL = "http://phc.prontonetworks.com/cgi-bin/authlogin"
LOGOUT_URL = "http://phc.prontonetworks.com/cgi-bin/authlogout"

# HTML parser to understand server response
HTML_PARSER = 'html.parser'

# Regex for SSIDs at VIT
SSID_REGEX = (
    r"VIT *2\.4 *G? *\d*",
    r"VIT *5 *G? *\d*",
    r"test *\d*"
)

# create a logger for this module
logger = getLogger(__name__)

def get_ssid() -> str:
    """get the SSID of the network the user is connected to
    - detect the operating system
    - use the appropriate shell command to get the SSID
    - return the SSID"""

    os_name = get_os_name()
    logger.debug(f"Detected OS: {os_name}")

    if os_name == 'Windows':
        output = popen("netsh wlan show interfaces").read()
        status = output.split("State")[1].split(":")[1].split('\n')[0].strip()

        if status != "connected":
            raise ConnectionError("Turn on Wifi From Device Settings:)")

        ssid = output.split("SSID")[1].split(":")[1].split('\n')[0].strip()

    elif os_name == 'Linux':
        output = popen("iwgetid").read()
        status = output.split(" ")[0].strip()

        if "SSID" not in output:
            raise ConnectionError("Turn on Wifi From Device Settings:)")

        ssid = output.split('"')[1]

    elif os_name == 'Darwin':
        output = popen("ipconfig getsummary en0 | grep -e \" *SSID\"").read()

        if "SSID" not in output:
            raise ConnectionError("Turn on Wifi From Device Settings:)")

        ssid = output.split("SSID :")[1].strip()

    else:
        raise NotImplementedError(f"Unsupported OS: {os_name}")

    logger.info(f"Detected SSID: {ssid}")
    return ssid


def check_ssid(ssid: str) -> bool:
    """check if the user is connected to a VIT network
    - check if the SSID matches the regex for VIT networks
    - return True if connected to a VIT network, False otherwise"""

    return any(
        match(regex, ssid) is not None
        for regex in SSID_REGEX
    )


def parse_login_response(html: bytes) -> str:
    """parse login HTML response
    - parse using BeautifulSoup
    - read the contents to determine request outcome
    - return a custom string containing status information
    - if page has unexpected/invalid content, raise an exception
    
    steps:
    1. check page title element
    2. if page title element exists, check its value
    3. if page title element is expected/valid, return status
    4. if page title element was ambiguous, check error element
    5. if page title element didn't exist, check page contents"""

    soup = BeautifulSoup(html, HTML_PARSER)

    # if title is not none, proceed and store its value to `title`
    if title := soup.find('title'):
        clean_title = title.text.strip().lower()

        if clean_title == "successful pronto authentication":
            return 'login-success'

        elif clean_title == "active session exist":
            return 'session-exists'
        
        elif clean_title == "this is the default server vhost":
            return 'not-on-vit'

        # check error elements if we get back a generic title
        elif clean_title == "volswifi authentication":
            error = soup.find('td', {'class': "errorText10"}).text.strip().lower()  # type: ignore

            standard_errors = {
                "sorry, please check your username and password and try again.": 'password-failure',
                "sorry, that account does not exist.": 'id-failure'
            }

            if error in standard_errors:
                return standard_errors[error]

            else:
                logger.warning(html)
                raise ValueError(f"Got title \"{title}\" but invalid error \"{error}\".")

        else:
            logger.warning(html)
            raise ValueError(f"Invalid title \"{title}\".")

    elif soup.find('b') and soup.find('b').text.strip().lower() == "you are already logged in":  # type: ignore
        return 'session-exists'

    else:
        logger.warning(html)
        raise ValueError("Invalid page.")


def parse_logout_response(html: bytes) -> str:
    """parse logout HTML response
    - parse using BeautifulSoup
    - read the contents to determine request outcome
    - return a custom string containing status information
    - if page has unexpected/invalid content, raise an exception
    
    steps:
    1. check page title element
    2. if page title element exists, check its value
    3. if page title element is expected/valid, return status"""

    soup = BeautifulSoup(html, HTML_PARSER)

    if title := soup.find('title'):
        clean_title = title.text.strip().lower()

        if clean_title == "logout failure":
            return 'logout-failure'

        elif clean_title == "logout successful":
            return 'logout-success'

        else:
            logger.warning(html)
            raise ValueError(f"Invalid title \"{clean_title}\".")
            
    else:
        logger.warning(html)
        raise ValueError("Invalid page.")


def login(credentials: dict[str, str]) -> str:
    """main login HTTP request
    - create the request
    - send the request
    - return the response"""

    login_payload = {
        'serviceName': 'ProntoAuthentication',
        'Submit22': 'Login',
        'userId': credentials['register-number'],
        'password': credentials['password']
    }

    try:
        login_request = post(
            LOGIN_URL,
            data=login_payload
        )

    except ConnectionError as e:
        raise ConnectionError(f"Server-side error. Contact CTS or wait until morning.") from e

    # analyse the HTTP status code and (if available) response
    if int(login_request.status_code == OK):
        logger.info("Login request acknowledged.")

        parsed_response_status = parse_login_response(login_request.content)
        logger.info("Response parsed.")

        return parsed_response_status

    else:
        logger.warning(login_request.content)
        raise ConnectionError(f"The server returned status code {login_request.status_code}.")


def logout() -> str:
    """main login HTTP request
    - create the request
    - send the request
    - return the response"""

    try:
        logout_request = get(
        url=LOGOUT_URL
    )

    except ConnectionError as e:
        raise ConnectionError(f"Server-side error. Contact CTS or wait until morning.") from e

    # analyse the HTTP status code and (if available) response
    if int(logout_request.status_code == OK):
        logger.info("Logout request acknowledged.")

        parsed_response_status = parse_logout_response(logout_request.content)
        logger.info("Response parsed.")

        return parsed_response_status

    else:
        logger.warning(logout_request.content)
        raise ConnectionError(f"The server returned status code {logout_request.status_code}.")
