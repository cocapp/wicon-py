from json import dump, load
from logging import getLogger
from pathlib import Path
from re import compile



REGISTER_NUMBER_REGEX = compile(r"^\d{2}[A-Z]{3}\d{4}$")

logger = getLogger(__name__)


def add_credentials(credentials_file_path: Path, register_number: str, password: str) -> None:
    if not REGISTER_NUMBER_REGEX.match(register_number):
        raise ValueError("Invalid register number.")

    logger.info("Register number is valid.")

    credentials = {
        'register-number': register_number,
        'password': password
    }

    if credentials_file_path.exists():
        logger.info("Credentials file already exists. Overwriting.")

    else:
        logger.info("Credentials file does not exist. Creating.")
        credentials_file_path.touch(exist_ok=True)

    with open(credentials_file_path, 'w') as credentials_file:
        logger.info("Credentials file found.")
        dump(credentials, credentials_file, indent=4)

    logger.info("Dumped credentials to file.")


def purge_credentials(credentials_file_path: Path) -> None:
    if not credentials_file_path.exists():
        raise FileNotFoundError("Credentials file does not exist.")

    logger.info("Credentials file found.")

    credentials_file_path.unlink()

    if not credentials_file_path.exists():
        logger.info("Deleted credentials file.")


def load_credentials(credentials_file_path: Path) -> dict[str, str]:
    if credentials_file_path.exists():
        logger.info("Credentials file found.")

        with open(credentials_file_path, 'r') as credentials_file:
            credentials = load(credentials_file)

            logger.info("Loaded credentials.")
            return credentials

    raise FileNotFoundError("Credentials file does not exist.")
