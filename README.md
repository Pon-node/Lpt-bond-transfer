# OrchestratorSyphon
```git clone https://github.com/stronk-dev/OrchestratorSiphon.git```
Modify ```nano /OrchestratorSyphon/OrchestratorSyphon.py``` config variables at the top of the file

Installation instructions:

```
pip install eth-hash
pip install eth-utils
pip install web3
python3 OrchestratorSyphon.py
```

Example systemd script:
```sudo nano /etc/systemd/system/orchSiphon.service```

insert following:
```
[Unit]
Description=LPT bond transfer
After=multi-user.target

[Service]
Type=simple
Restart=always
WorkingDirectory=/path/to/OrchestratorSyphon
ExecStart=/usr/bin/python3 -u /path/to/OrchestratorSyphon/OrchestratorSyphon.py

[Install]
WantedBy=multi-user.target
```

Save service file and type following commands:

systemctl daemon-reload
systemctl enable --now orchSiphon.service

journalctl -u orchSiphon.service -n 500 -f

