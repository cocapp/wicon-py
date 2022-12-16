# Wi-Fi login for VIT

This application helps you login to the Wi-Fi networks used for students at VIT University, Vellore, India.

### DISCLAIMERS
*   This software has been tested on Windows only, not on MacOS or GNU/Linux even though support for these is included.

    To all Linux users on campus: We would really appreciate it if you would please help us out by testing it for us 😊

*   This has not yet been approved by VIT staff in any capacity, and is **not official software**. Please use this completely at your own risk.

## Steps to run:
1.  Install the Python dependencies in your local environment:

    ```sh
    python -m pip install -r requirements.txt
    ```

    If you intend to also develop, also installing developer dependencies might be useful to you:
    ```sh
    python -m pip install -r dev-requirements.txt
    ```


2.  Set up your credentials using the `addcreds` command. You may later use the same command to edit (overwrite) your credentials.
    
    ```sh
    python ./login_cli.py addcreds
    ```
    
    Example usage:
    ```sh
    $ python ./login_cli.py addcreds
    Enter your register number: 21BEE8964
    Enter your password:
    Credentials added sucessfully.
    ```

    The echo is turned off when entering the password, and it is normal for no text to be displayed.

3.  Run the script to login:

    ```sh
    python ./login_cli.py login
    ```

    You may optionally supply your credentials as an argument:

    ```sh
    python ./login_cli.py login -r 21BEE8964 -p "my unguessable password"
    ```

4. When you're done using the internet, logout.

    ```sh
    python ./login_cli.py logout
    ```


