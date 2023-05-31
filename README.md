# Lpt-bond-transfer
```gh repo clone Pon-node/Lpt-bond-transfer```
Modify ```nano /Lpt-bond-transfer/LPT-bond-Transfer.py``` to set LPT_treshold, insert wallet addresses,privates keys and you can change RPC provider if you want to

LPT_THRESHOLD = 3 (Keeping 1 LPT)
ETH_THRESHOLD = 0.1 (keeping 0.01 ETH for fee)

DELEGATOR_PRIVATE_KEY = 'InsertDelegatorPrivateKey'

DELEGATOR_PUBLIC_KEY = 'InsertDelegatorWalletAddress'

ETH_RECEIVER_PUBLIC_KEY = 'ETHWalletThatWillReceiveAddress'

LPT_RECEIVER_PUBLIC_KEY = 'LPTWalletThatWillReceiveAddress'

L2_RPC_PROVIDER = 'https://arb1.arbitrum.io/rpc'```



Installation instructions:

```pip install eth-hash==0.4.0
pip install eth-utils==1.9.5
pip install web3==5.31.3
python3 LPT-bond-transfer.py```

Creating systemd service to run LPT bond transfer script. steps to follow:
```mv Lpt-bond-transfer/* usr/local/bin/Lpt-bond-transfer/
sudo nano /etc/systemd/system/bondTransfer.service``` and insert following:


[Unit]
Description=LPT bond transfer
After=multi-user.target

[Service]
Type=simple
Restart=always
WorkingDirectory=/usr/local/bin/Lpt-bond-transfer
ExecStart=/usr/bin/python3 -u /usr/local/bin/Lpt-bond-transfer/LPT-bond-transfer.py

[Install]
WantedBy=multi-user.target

Save service file and type following commands:

systemctl daemon-reload
systemctl enable --now bondTransfer.service

journalctl -u bondTransfer.service -n 500 -f

