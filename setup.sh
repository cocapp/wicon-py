#!/bin/sh

# Make sure user is on a VIT Wi-Fi network
echo "Please make sure you are connected to a VIT Wi-Fi network, and logged in."
echo "Press enter to continue once you are connected."
read -r _

echo "Checking system requirements..."

# Check that the user has at least Python 3.9
PYTHON3_VERSION=`python3 -c 'import sys; print(sys.version_info[1])'`

if [ $PYTHON3_VERSION -lt 9 ]; then
    echo "You have `python3 -V` but Python 3.9 or higher is required"
    exit 1
fi

# Check that the user has /etc/NetworkManager/dispatcher.d
if [ ! -d "/etc/NetworkManager/dispatcher.d" ]; then
    echo "NetworkManager is not installed"
    exit 1
fi

echo ""
echo "Downloading WiCon from GitHub..."

# Clone the repository. If it already exists, pull the latest changes
if [ -d "wicon-py" ]; then
    git -C wicon-py pull
else
    echo "Cloning repository..."
    git clone https://github.com/cocapp/wicon-py.git
fi

echo ""
echo "Setting up Python virtual environment..."

# Create and setup virtual environment
python3 -m venv `pwd`/wicon-py/.venv --upgrade-deps || python3 -m venv `pwd`/wicon-py/.venv
`pwd`/wicon-py/.venv/bin/python -m pip install -r `pwd`/wicon-py/requirements.txt || {
    echo "Failed to install dependencies."
    echo "Please check your pip installation and try again."
    exit 1
}

echo ""
echo "Creating login and logout scripts..."

# Create login binary
touch /tmp/wicon-py-login
echo "#!/bin/sh" >> /tmp/wicon-py-login
echo "if [ \"\$2\" = \"up\" ]; then" >> /tmp/wicon-py-login
echo "su $USER -c \"`pwd`/wicon-py/.venv/bin/python `pwd`/wicon-py/login_cli.py login\"" >> /tmp/wicon-py-login
echo "fi" >> /tmp/wicon-py-login

# Create logout binary
touch /tmp/wicon-py-logout
echo "#!/bin/sh" >> /tmp/wicon-py-logout
echo "su $USER -c \"`pwd`/wicon-py/.venv/bin/python `pwd`/wicon-py/login_cli.py logout\"" >> /tmp/wicon-py-logout

echo ""
echo "Setting up login and logout scripts to run on network change..."
echo "You may be prompted for your sudo password."

# Move login binary to NetworkManager dispatcher
sudo mv /tmp/wicon-py-login /etc/NetworkManager/dispatcher.d/wicon-py-login
sudo chown root:root /etc/NetworkManager/dispatcher.d/wicon-py-login
sudo chmod 555 /etc/NetworkManager/dispatcher.d/wicon-py-login

# Move logout binary to NetworkManager dispatcher pre-down.d
sudo mv /tmp/wicon-py-logout /etc/NetworkManager/dispatcher.d/pre-down.d/wicon-py-logout
sudo chown root:root /etc/NetworkManager/dispatcher.d/pre-down.d/wicon-py-logout
sudo chmod 555 /etc/NetworkManager/dispatcher.d/pre-down.d/wicon-py-logout

echo ""
echo "Setting up WiCon..."
echo "You may be prompted for your VIT Wi-Fi username and password."

# Prompt to setup username and password
# This will be done using a command built into WiCon
# WiCon will return 0 if successful
# Continue until WiCon returns 0
while ! `pwd`/wicon-py/.venv/bin/python `pwd`/wicon-py/login_cli.py addcreds; do
    echo ""
    echo "Please try again."
done

echo "Setup complete!"

echo ""
echo "Testing logout..."
if `pwd`/wicon-py/.venv/bin/python `pwd`/wicon-py/login_cli.py logout > /dev/null; then
    echo "Logout successful!"
else
    echo "Logout failed!"
fi

echo "Testing login..."
if `pwd`/wicon-py/.venv/bin/python `pwd`/wicon-py/login_cli.py login > /dev/null; then
    echo "Login successful!"
else
    echo "Login failed!"
fi

echo ""
echo "Wicon logs are located at $HOME/.wicon/wicon.log. Note that these are not sent anywhere for privacy reasons, but you can send them along when reporting issues."
echo "Wicon settings are located at $HOME/.wicon/wicon-settings.json."