sudo mkdir -p /opt/heartbeat && sudo chown -R $USER:$USER /opt/heartbeat
cd /opt/heartbeat
python3 -m venv .venv           # (venv reminder ✅)
source .venv/bin/activate
# put these files here: main.py, config.yaml, emailutil.py, requirements.txt
pip install -r requirements.txt
deactivate
sudo useradd -r -s /usr/sbin/nologin heartbeat
sudo chown -R heartbeat:heartbeat /opt/heartbeat
sudo setcap 'cap_net_raw+ep' /opt/heartbeat/.venv/bin/python3
