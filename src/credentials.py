"""
manage user credentials
- reads credentials from the user
- creates/edits/deletes credentials file
- reads credentials from files
"""

from json import dump, load
from logging import getLogger
from pathlib import Path
from re import compile

## regex for validating the register number
# first two characters must be digits, followed by three uppercase letters, and must end in four digits
REGISTER_NUMBER_REGEX = compile(r"^(?P<year>\d{2})(?P<course>[A-Z]{3})(?P<student_number>\d{4}$)")

# create a logger for this module
logger = getLogger(__name__)


def add_credentials(credentials_file_path: Path, register_number: str, password: str) -> None:
    """save or edit credentials
    - save the data to file"""

    # create a dictionary because we shall save as JSON
    credentials = {
        'register-number': register_number,
        'password': password
    }

    # if credentials already exist, overwrite to edit
    if credentials_file_path.exists():
        logger.info("Credentials file already exists. Overwriting.")

    # if credentials do not exist, create a new file
    else:
        logger.info("Credentials file does not exist. Creating.")
        credentials_file_path.touch(exist_ok=True)

    with open(credentials_file_path, 'w') as credentials_file:
        logger.info("Credentials file found.")
        dump(credentials, credentials_file, indent=4)

    logger.info("Dumped credentials to file.")


def purge_credentials(credentials_file_path: Path) -> None:
    """purge existing credentials
    - raise an exception if credentials file doesn't exist"""

    if not credentials_file_path.exists():
        raise FileNotFoundError("Credentials file does not exist.")

    logger.info("Credentials file found.")

    credentials_file_path.unlink()

    if not credentials_file_path.exists():
        logger.info("Deleted credentials file.")


def load_credentials(credentials_file_path: Path) -> dict[str, str]:
    """load credentials form file
    - raise an exception if credentials file doesn't exist"""

    if credentials_file_path.exists():
        logger.info("Credentials file found.")

        with open(credentials_file_path, 'r') as credentials_file:
            credentials = load(credentials_file)

            logger.info("Loaded credentials.")
            return credentials

    raise FileNotFoundError("Credentials file does not exist.")
