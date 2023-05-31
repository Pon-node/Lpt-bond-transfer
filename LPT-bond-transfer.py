import web3
import json
import time

# global config
LPT_THRESHOLD = 100
ETH_THRESHOLD = 0.1 # in ETH
DELEGATOR_PRIVATE_KEY = 'InsertDelegatorPrivateKey'
DELEGATOR_PUBLIC_KEY = 'InsertDelegatorWalletAddress'
RECEIVER_PUBLIC_KEY = 'WalletThatWillReceiveAddress'
ETH_RECEIVER_PUBLIC_KEY = 'ETHWalletThatWillReceiveAddress'
LPT_RECEIVER_PUBLIC_KEY = 'LPTWalletThatWillReceiveAddress'
L2_RPC_PROVIDER = 'https://arb1.arbitrum.io/rpc'

# global constants
WAIT_TIME_ROUND_LOCK = 60
WAIT_TIME_BALANCE_CHECK = 14400
BONDING_CONTRACT_ADDR = '0x35Bcf3c30594191d53231E4FF333E8A770453e40'
ROUNDS_CONTRACT_ADDR = '0xdd6f56DcC28D3F5f27084381fE8Df634985cc39f'

"""
@brief Returns a JSON object of ABI data
@param path: absolute/relative path to an ABI file
"""
def getABI(path):
    try:
        with open(path) as f:
            info_json = json.load(f)
            return info_json["abi"]
    except:
        print("Unable to extract ABI data. Is {0} a valid path?".format(path))
        exit(1)

"""
@brief Returns a JSON object of ABI data
@param path: absolute/relative path to an ABI file
"""
def getChecksumAddr(wallet):
    try:
        parsed_wallet = web3.Web3.toChecksumAddress(wallet.lower())
        return parsed_wallet
    except:
        print("Unable to parse delegator wallet address. Is {0} a valid address?".format(wallet))
        exit(1)

"""
@brief Waits for the delegator to reach the specified threshold in LPT stake
@param bonding_contract: bonding manager contract object on which we can call `getDelegator`
@param delegator: checksum address of the delegator which wants to transfer stake
"""
def waitForLPTStake(bonding_contract, delegator):
    # get delegator info (returns [bondedAmount, fees, delegateAddress, delegatedAmount, startRound, lastClaimRound, nextUnbondingLockId])
    pending_lptu = bonding_contract.functions.pendingStake(delegator, 99999).call()
    pending_lpt = web3.Web3.fromWei(pending_lptu, 'ether')
    print("Delegator is currently staking {0:.2f} LPT".format(pending_lpt))
    while pending_lpt < LPT_THRESHOLD:
        print("Waiting for staked LPT to reach threshold {0}. Currently has a stake of {1:.2f} LPT. Retrying in {2}...".format(LPT_THRESHOLD, pending_lpt, WAIT_TIME_BALANCE_CHECK))
        time.sleep(WAIT_TIME_BALANCE_CHECK)
        pending_lptu = bonding_contract.functions.pendingStake(delegator, 99999).call()
        pending_lpt = web3.Web3.fromWei(pending_lptu, 'ether')
    print("Delegator has a stake of {0:.2f} LPT which exceeds the minimum threshold of {1:.2f}, continuing...".format(pending_lpt, LPT_THRESHOLD))

"""
@brief Waits for the delegator's ETH balance to reach the specified threshold
@param w3: web3 object
@param parsed_delegator_wallet: checksum address of the delegator which wants to transfer ETH
"""
def waitForETHBalance(w3, parsed_delegator_wallet):
    eth_balance = w3.eth.get_balance(parsed_delegator_wallet)
    eth_balance_in_ether = web3.Web3.fromWei(eth_balance, 'ether')
    print("Delegator's ETH balance is {0:.2f} ETH".format(eth_balance_in_ether))
    while eth_balance_in_ether < ETH_THRESHOLD:
        print("Waiting for ETH balance to reach threshold {0} ETH. Currently has a balance of {1:.2f} ETH. Retrying in {2}...".format(ETH_THRESHOLD, eth_balance_in_ether, WAIT_TIME_BALANCE_CHECK))
        time.sleep(WAIT_TIME_BALANCE_CHECK)
        eth_balance = w3.eth.get_balance(parsed_delegator_wallet)
        eth_balance_in_ether = web3.Web3.fromWei(eth_balance, 'ether')
    print("Delegator's ETH balance is {0:.2f} ETH which exceeds the minimum threshold of {1:.2f} ETH, continuing...".format(eth_balance_in_ether, ETH_THRESHOLD))

"""
@brief Waits for the currents Livepeer round to become locked
@param rounds_contract: rounds manager contract object on which we can call `currentRoundLocked`
"""
def waitForLock(rounds_contract):
    round_lock = rounds_contract.functions.currentRoundLocked().call()
    while not round_lock:
        print("Waiting for round to become locked. Retrying in {0} seconds...".format(WAIT_TIME_ROUND_LOCK))
        time.sleep(WAIT_TIME_ROUND_LOCK)
        round_lock = rounds_contract.functions.currentRoundLocked().call()
    print("Round is locked, continuing...")

"""
@brief Transfers all but 1 LPT stake to the configured destination wallet
@param bonding_contract: bonding manager contract object on which we can call `transferBond`
@param parsed_delegator_wallet: checksum public key of the delegator which wants to transfer stake
@param parsed_destination_wallet: checksum address of the destination wallet
"""
def doTransferLPT(bonding_contract, parsed_delegator_wallet, parsed_lpt_destination_wallet):
    delegator_info = bonding_contract.functions.getDelegator(parsed_delegator_wallet).call()
    staked_lpt = web3.Web3.fromWei(delegator_info[0], 'ether')
    pending_lpt = bonding_contract.functions.pendingStake(parsed_delegator_wallet, 99999).call()
    pending_lpt = web3.Web3.fromWei(pending_lptu, 'ether')
    transfer_amount = web3.Web3.toWei(pending_lpt - 1, 'ether')
    print("Should transfer {0} LPTU".format(transfer_amount))
    # Build transaction info
    tx = bonding_contract.functions.transferBond(parsed_destination_wallet, transfer_amount,
        web3.constants.ADDRESS_ZERO, web3.constants.ADDRESS_ZERO, web3.constants.ADDRESS_ZERO,
        web3.constants.ADDRESS_ZERO).buildTransaction(
        {
            "from": parsed_delegator_wallet,
            "gasPrice": 1000000000,
            "nonce": w3.eth.get_transaction_count(parsed_delegator_wallet)
        }
    )
    # Sign and initiate transaction
    signedTx = w3.eth.account.sign_transaction(tx, DELEGATOR_PRIVATE_KEY)
    transactionHash = w3.eth.send_raw_transaction(signedTx.rawTransaction)
    print("Initiated LPT transaction with hash {0}".format(transactionHash))
    # Wait for transaction to be confirmed
    receipt = w3.eth.wait_for_transaction_receipt(transactionHash)
    print("Completed LPT transaction {0}".format(receipt))

"""
@brief Transfers all ETH balance to the configured destination wallet
@param w3: web3 object
@param parsed_delegator_wallet: checksum public key of the delegator which wants to transfer ETH
@param parsed_destination_wallet: checksum address of the destination wallet
"""
def doTransferETH(w3, parsed_delegator_wallet, parsed_destination_wallet):
    eth_balance = w3.eth.get_balance(parsed_delegator_wallet)
    transfer_amount = eth_balance - web3.Web3.toWei(0.01, 'ether') # leave 0.01 ETH as gas fee
    print("Should transfer {0} ETH".format(web3.Web3.fromWei(transfer_amount, 'ether')))
    # Build transaction info
    tx = {
        'to': parsed_destination_wallet,
        'value': transfer_amount,
        'gas': 21000,
        'gasPrice': w3.eth.gas_price,
        'nonce': w3.eth.get_transaction_count(parsed_delegator_wallet),
        'chainId': w3.eth.chain_id
    }
    # Sign and initiate transaction
    signedTx = w3.eth.account.sign_transaction(tx, DELEGATOR_PRIVATE_KEY)
    transactionHash = w3.eth.send_raw_transaction(signedTx.rawTransaction)
    print("Initiated ETH transaction with hash {0}".format(transactionHash))
    # Wait for transaction to be confirmed
    receipt = w3.eth.wait_for_transaction_receipt(transactionHash)
    print("Completed ETH transaction {0}".format(receipt))


if __name__ == "__main__":
    # convert configured wallets to usable versions
    parsed_delegator_wallet = getChecksumAddr(DELEGATOR_PUBLIC_KEY)
    parsed_eth_destination_wallet = getChecksumAddr(ETH_RECEIVER_PUBLIC_KEY)
    parsed_lpt_destination_wallet = getChecksumAddr(LPT_RECEIVER_PUBLIC_KEY)

    # open ABI files
    bondingABI = getABI("./BondingManagerTarget.json")
    roundsABI = getABI("./RoundsManagerTarget.json")

    # connect to L2 grpc provider
    provider = web3.HTTPProvider(L2_RPC_PROVIDER)
    w3 = web3.Web3(provider)
    assert w3.isConnected()

    # prepare contracts
    bonding_contract = w3.eth.contract(address=BONDING_CONTRACT_ADDR, abi=bondingABI)
    rounds_contract = w3.eth.contract(address=ROUNDS_CONTRACT_ADDR, abi=roundsABI)

    # main loop for LPT transfer
    while True:
        print("Initiating new round for delegator {0}".format(DELEGATOR_PUBLIC_KEY))
        waitForLPTStake(bonding_contract, parsed_delegator_wallet)
        waitForLock(rounds_contract)
        doTransferLPT(bonding_contract, parsed_delegator_wallet, parsed_lpt_destination_wallet)

    # main loop for ETH transfer
    while True:
        print("Initiating new round for delegator {0}".format(DELEGATOR_PUBLIC_KEY))
        waitForETHBalance(w3, parsed_delegator_wallet)
        doTransferETH(w3, parsed_delegator_wallet, parsed_eth_destination_wallet)
