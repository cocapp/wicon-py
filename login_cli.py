"""
- integrate the entire application
- define the CLI and serve the it
- handle user settings
- handle logging
- handle notifications
- handle exceptions
"""

from argparse import ArgumentParser
from argparse import Namespace as ArgNamespace
from getpass import getpass
from json import JSONDecodeError, dump, loads
from logging import DEBUG, INFO, FileHandler, Formatter, Logger, getLogger
from os import environ
from pathlib import Path
from sys import argv
from sys import exit as sys_exit

from colorama import Fore, Style
from notifypy import Notify

import src.auth
import src.credentials

# set the logger level
LOGGER_LEVEL = INFO

# set a scheme for the notifying the user based on custom status messages
# in general, the user is notified only of failures or other abnormal events
# the user is not notified if they are expected to be active on a command line
DEFAULT_USER_NOTIFICATION_SCHEME: dict[str, dict[str, str | bool]] = {
    'login-success': {
        'notification': False,
        'title': "Login successful",
        'message': "Logged in to the Wi-Fi network.",
        'error': False
    },
    'password-failure': {
        'notification': True,
        'message': "Incorrect password",
        'title': "Login failed",
        'error': True
    },
    'id-failure': {
        'notification': True,
        'message': "Invalid register number",
        'title': "Login failed",
        'error': True
    },
    'no-credentials': {
        'notification': True,
        'title': "Login failed",
        'message': "No credentials found. Please create then using the command \"wicon addcreds\".",
        'error': True
    },
    'session-exists': {
        'notification': True,
        'message': "Already logged in",
        'title': "Login successful",
        'error': False
    },
    'logout-failure': {
        'notification': True,
        'message': "Logout failed",
        'title': "Possibly server error",
        'error': True
    },
    'logout-success': {
        'notification': True,
        'message': "Logout successful",
        'title': "Logged out of the Wi-Fi network",
        'error': False
    },
    'not-on-vit': {
        'notification': False,
        'error': False
    },
    'credadd-success': {
        'notification': False,
        'error': False
    },
    'credadd-failure': {
        'notification': False,
        'error': True
    },
    'credpurge-success': {
        'notification': False,
        'error': False
    },
    'credpurge-failure': {
        'notification': False,
        'error': True
    }
}

# raise a default notification in case of a key error
DEFAULT_NOTIFICATION: dict[str, str | bool] = {
    'notification': True,
    'title': "Unknown Status",
    'message': "Please send the log file to the developer.",
}


def load_settings(settings_file_path: Path, logger: Logger) -> dict[str, dict[str, dict[str, str | bool]]]:
    """load the user settings from the settings file
    - if the file does not exist, create it and return the default settings"""

    if settings_file_path.exists():
        with open(settings_file_path, 'r') as settings_file:
            settings = settings_file.read().strip()

            if settings:
                try:
                    USER_SETTINGS = loads(settings)

                except JSONDecodeError as e:
                    logger.warn(settings)
                    raise ValueError("Invalid settings JSON.") from e

                else:
                    logger.info("Settings file found and loaded.")
                    return USER_SETTINGS

    settings_file_path.touch()
    with open(settings_file_path, 'w') as settings_file:
        logger.info("Creating settings file with default settings.")

        USER_SETTINGS = {
            "notification-settings": DEFAULT_USER_NOTIFICATION_SCHEME
        }

        dump(USER_SETTINGS, settings_file, indent=4)
        logger.info("Settings file created.")

    return USER_SETTINGS


def init(__name__: str) -> tuple[dict[str, dict[str, dict[str, str | bool]]], Path, Logger]:
    """initialize objects for later use
    - set file path objects for credentials and logging
    - configure the loggers
    """

    # handle cases where the folder is not the default
    if (folder_name := environ.get('DATA')):
        FOLDER_PATH = Path(folder_name)

    else:
        FOLDER_PATH = Path.home() / '.wicon'

    FOLDER_PATH.mkdir(exist_ok=True, parents=True)

    # configure the loggers
    logger_formatter = Formatter(
        fmt="[{asctime}][{process:05}][{name}][{levelname}] {message}",
        style='{'
    )
    logger_file_handler = FileHandler(
        FOLDER_PATH / 'wicon.log',
        mode='a'
    )
    logger_file_handler.setFormatter(logger_formatter)

    logger = getLogger(__name__)

    src.auth.logger.addHandler(logger_file_handler)
    src.auth.logger.setLevel(LOGGER_LEVEL)

    src.credentials.logger.addHandler(logger_file_handler)
    src.credentials.logger.setLevel(LOGGER_LEVEL)

    logger.addHandler(logger_file_handler)
    logger.setLevel(LOGGER_LEVEL)

    # set the paths for individual files
    CREDENTIALS_FILE_PATH = FOLDER_PATH / "credentials.json"
    SETTINGS_FILE_PATH = FOLDER_PATH / "wicon-settings.json"

    # load the user settings
    USER_SETTINGS = load_settings(SETTINGS_FILE_PATH, logger)

    return USER_SETTINGS, CREDENTIALS_FILE_PATH, logger


def define_and_read_args(arguments: list[str]) -> ArgNamespace:
    """configure parsers
    - define the main parser for the application executable
    - define subparsers (one for each functionality)
    - parse the arguments"""

    main_parser = ArgumentParser(
        prog='wicon',
        description="Connects your Wi-Fi in VIT."
    )
    functions = main_parser.add_subparsers(required=True)

    connect_parser = functions.add_parser(
        'login',
        help="Login to the Wi-Fi network."
    )
    connect_parser.set_defaults(func=connect)
    connect_parser.add_argument(
        '-r',
        '--registernumber',
        type=str,
        help="You VIT register number"
    )
    connect_parser.add_argument(
        '-p',
        '--password',
        type=str,
        help="Your VIT Wi-Fi password"
    )
    connect_parser.add_argument(
        '-n',
        '--notify',
        action='store_true',
        help="Notify the user of the status."
    )

    disconnect_parser = functions.add_parser(
        'logout',
        help="Logout of the Wi-Fi network."
    )
    disconnect_parser.set_defaults(func=disconnect)
    disconnect_parser.add_argument(
        '-n',
        '--notify',
        action='store_true',
        help="Notify the user of the status."
    )

    add_credentials = functions.add_parser(
        'addcreds',
        help="Add/update your register number and password."
    )
    add_credentials.set_defaults(func=addcreds)

    purge_credentials = functions.add_parser(
        'purgecreds',
        help="Remove your register number and password."
    )
    purge_credentials.set_defaults(func=purgecreds)

    return main_parser.parse_args(arguments)


def connect(parsed_arguments: ArgNamespace) -> str:
    """log in to the Wi-Fi network
    - check if on VIT network
    - get credentials and handle relevant CLI arguments
    - send the request
    - return the response/status"""

    if not src.auth.check_ssid(src.auth.get_ssid()):
        return 'not-on-vit'

    logger.info("Attempting to login.")

    try:
        credentials = src.credentials.load_credentials(CREDENTIALS_FILE_PATH)

    except FileNotFoundError as e:
        return 'no-credentials'

    # prioritize the arguments
    # so if a credential is available as an argument, override the credential from file
    if parsed_arguments.registernumber:
        credentials['register-number'] = parsed_arguments.registernumber

    if parsed_arguments.password:
        credentials['password'] = parsed_arguments.password

    if not (('register-number' in credentials) and ('password' in credentials)):
        logger.warning("Possibly missing credentials.")

    return src.auth.login(credentials)


def disconnect(parsed_arguments: ArgNamespace) -> str:
    """log out of the Wi-Fi network
    - check if on VIT network
    - send the request
    - return the response/status"""

    if not src.auth.check_ssid(src.auth.get_ssid()):
        return 'not-on-vit'
    
    logger.info("Attempting to logout.")

    return src.auth.logout()


def addcreds(parsed_arguments: ArgNamespace) -> str:
    """store/edit user credentials
    - get user credentials
    - validate credentials
    - store credentials to file
    - verify the file"""

    logger.info("Attempting to add/edit credentials.")

    try:
        register_number = input("Enter your register number: ")

        if not src.credentials.REGISTER_NUMBER_REGEX.match(register_number):
            raise ValueError("Invalid register number.")
        else:
            logger.info("Register number is valid.")

        password = getpass("Enter your password: ")
        confirm_password = getpass("Re-enter your password: ")

        if password != confirm_password:
            raise ValueError("Passwords do not match.")
        else:
            logger.info("Passwords match.")

    except ValueError as e:
        logger.exception(e)
        print(e.args[0])

    else:
        src.credentials.add_credentials(
            CREDENTIALS_FILE_PATH, register_number, password
        )

        credentials = src.credentials.load_credentials(CREDENTIALS_FILE_PATH)

        # ensure that the correct credentials were stored in the file
        if credentials and credentials.get('register-number') == register_number and credentials.get('password') == password:
            print(f"{Fore.GREEN}{Style.BRIGHT}Credentials added successfully.{Style.RESET_ALL}")
            return 'credadd-success'

    print(f"{Fore.RED}{Style.BRIGHT}Failed to add credentials.{Style.RESET_ALL}")
    return 'credadd-failure'


def purgecreds(parsed_arguments: ArgNamespace) -> str:
    """purge user credentials
    - delete credentials file
    - verify that the file has been deleted"""

    logger.info("Attempting to purge credentials.")

    try:
        src.credentials.purge_credentials(CREDENTIALS_FILE_PATH)
    
    except FileNotFoundError as e:
        logger.exception(e)
        print(e.args[0])

    else:
        if not CREDENTIALS_FILE_PATH.exists():
            print(f"{Fore.GREEN}{Style.BRIGHT}Credentials purged successfully.{Style.RESET_ALL}")
            return 'credpurge-success'

    print(f"{Fore.RED}{Style.BRIGHT}Failed to purge credentials.{Style.RESET_ALL}")
    return 'credpurge-failure'


def main(arguments: list[str]) -> int:
    """main function
    - parses the command line arguments
    - initialize the database
    - calls the appropriate function based on the arguments"""

    # parse the command line arguments
    parsed_namespace = define_and_read_args(arguments)
    try:
        status_message: str = parsed_namespace.func(parsed_namespace)

    # notify the user if an error occurs
    except Exception as e:
        logger.exception(e)
        notification = Notify(
            default_notification_title="Error",
            default_notification_message=e.args[0],
            default_notification_application_name="Wi-Con"
        )

        notification.send(block=False)
        exit_code = 1

    else:
        # check whether the status message should trigger a notification
        current_status: dict[str, dict[str, str | bool]] = USER_SETTINGS.get('notification-settings', dict()).get(status_message, DEFAULT_NOTIFICATION)  # type: ignore
        
        # if the status is an abnormal behaviour or failure, notify the user
        if current_status.get('notification', True):
            notification = Notify(
                default_notification_title=current_status.get('title', DEFAULT_NOTIFICATION['title']),  # type: ignore
                default_notification_message=current_status.get('message', DEFAULT_NOTIFICATION['message']),  # type: ignore
                default_notification_application_name="Wi-Con"
            )

            if parsed_namespace.notify:
                notification.send(block=False)

        logger.info(status_message)

        # if the status is an error, exit with a non-zero exit code
        exit_code = int(current_status.get('error', True))

    finally:
        logger.info(f"Exited with exit code {exit_code}.")
        return exit_code


if __name__ == "__main__":
    USER_SETTINGS, CREDENTIALS_FILE_PATH, logger = init(__name__)
    sys_exit(main(argv[1:]))
