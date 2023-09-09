#!/bin/sh

# Clone the repository
git clone https://github.com/cocapp/wicon-py.git

# Create and setup virtual environment
python3 -m venv `pwd`/wicon-py/.venv  --upgrade-deps
`pwd`/wicon-py/.venv/bin/python -m pip install -r `pwd`/wicon-py/requirements.txt

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

# Move login binary to NetworkManager dispatcher
sudo mv /tmp/wicon-py-login /etc/NetworkManager/dispatcher.d/wicon-py-login
sudo chown root:root /etc/NetworkManager/dispatcher.d/wicon-py-login
sudo chmod 555 /etc/NetworkManager/dispatcher.d/wicon-py-login

# Move logout binary to NetworkManager dispatcher pre-down.d
sudo mv /tmp/wicon-py-logout /etc/NetworkManager/dispatcher.d/pre-down.d/wicon-py-logout
sudo chown root:root /etc/NetworkManager/dispatcher.d/pre-down.d/wicon-py-logout
sudo chmod 555 /etc/NetworkManager/dispatcher.d/pre-down.d/wicon-py-logout

# Prompt to setup username and password
# This will be done using a command built into WiCon
# WiCon will return 0 if successful
# Continue until WiCon returns 0
while true; do
    `pwd`/wicon-py/.venv/bin/python `pwd`/wicon-py/login_cli.py addcreds
    if [ $? -eq 0 ]; then
        break
    fi
done

echo "Setup complete!"

echo "Testing logout..."
`pwd`/wicon-py/.venv/bin/python `pwd`/wicon-py/login_cli.py logout

echo "Testing login..."
`pwd`/wicon-py/.venv/bin/python `pwd`/wicon-py/login_cli.py login
