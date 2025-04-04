from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib
import json
import time
import uuid

app = Flask(__name__)
CORS(app)

# === MACCI CONFIG ===
MAX_SUPPLY = 100_000_000
PREMINE_AMOUNT = 40_000_000
PRESALE_RATE = 10000  # 1 USDT = 10,000 MACCI
MINING_REWARD = 10
DIFFICULTY = 9

wallets = {}  # wallet_address: {balance, private_key}
chain = []
transactions = []
total_mined = 0

MAIN_WALLET = "7fc8cb7519f34a0dbef5b2e15ecc24be"
wallets[MAIN_WALLET] = {"balance": PREMINE_AMOUNT, "private_key": "PREMINED_KEY"}
total_mined += PREMINE_AMOUNT

# === Blockchain Core ===

def create_genesis_block():
    genesis = {
        'index': 1,
        'timestamp': time.time(),
        'proof': 100,
        'previous_hash': '1',
        'transactions': []
    }
    chain.append(genesis)

def hash_block(block):
    return hashlib.sha256(json.dumps(block, sort_keys=True).encode()).hexdigest()

def proof_of_work(previous_proof):
    proof = 1
    while True:
        guess = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
        if guess[:DIFFICULTY] == "0" * DIFFICULTY:
            return proof
        proof += 1

def mine_block(address):
    global total_mined
    if address not in wallets:
        return "❌ Wallet not found."

    if total_mined + MINING_REWARD > MAX_SUPPLY:
        return "❌ Max supply reached. Cannot mine more MACCI."

    previous_proof = chain[-1]['proof']
    proof = proof_of_work(previous_proof)
    block = {
        'index': len(chain) + 1,
        'timestamp': time.time(),
        'proof': proof,
        'previous_hash': hash_block(chain[-1]),
        'transactions': transactions.copy()
    }

    chain.append(block)
    wallets[address]['balance'] += MINING_REWARD
    total_mined += MINING_REWARD
    transactions.clear()

    return f"⛏️ Block mined! +{MINING_REWARD} MACCI to {address}"

def create_wallet():
    addr = uuid.uuid4().hex[:32]
    key = uuid.uuid4().hex
    wallets[addr] = {"balance": 0, "private_key": key}
    return addr, key

def recover_wallet(key):
    for addr, data in wallets.items():
        if data['private_key'] == key:
            return addr
    return None

def get_balance(address, key):
    if address not in wallets:
        return "❌ Wallet not found."
    if wallets[address]['private_key'] != key:
        return "❌ Invalid private key."
    return f"💰 Balance: {wallets[address]['balance']} MACCI"

def send_macci(sender, recipient, amount, key):
    if sender not in wallets:
        return "❌ Sender not found."
    if wallets[sender]['private_key'] != key:
        return "❌ Invalid private key."
    if wallets[sender]['balance'] < amount:
        return "❌ Not enough balance."

    if recipient not in wallets:
        wallets[recipient] = {"balance": 0, "private_key": "UNKNOWN"}

    wallets[sender]['balance'] -= amount
    wallets[recipient]['balance'] += amount
    return f"✅ Sent {amount} MACCI from {sender} to {recipient}"

def trade_usdt(wallet, usdt_amount):
    global total_mined
    if wallet not in wallets:
        return "❌ Wallet not found."

    try:
        usdt = float(usdt_amount)
    except:
        return "❌ Invalid USDT amount."

    if usdt <= 0:
        return "❌ Must trade more than 0 USDT."

    macci = int(usdt * PRESALE_RATE)

    if total_mined + macci > MAX_SUPPLY:
        return "❌ Max supply reached. Cannot mint more MACCI."

    wallets[wallet]['balance'] += macci
    total_mined += macci
    return f"💱 Traded {usdt} USDT → {macci} MACCI"

# === Terminal Command Route ===

@app.route('/terminal', methods=['POST'])
def terminal():
    data = request.get_json()
    cmd = data.get('input', '').strip().split()
    if not cmd:
        return jsonify({"output": "⚠️ No command entered."})

    match cmd[0].lower():
        case 'create':
            addr, key = create_wallet()
            return jsonify({"output": f"✅ Wallet Created\nAddress: {addr}\nKey: {key}"})
        case 'recover':
            if len(cmd) != 2:
                return jsonify({"output": "Usage: recover <private_key>"})
            addr = recover_wallet(cmd[1])
            return jsonify({"output": f"🔑 Wallet Address: {addr}" if addr else "❌ No wallet matches that key."})
        case 'mine':
            if len(cmd) != 2:
                return jsonify({"output": "Usage: mine <wallet_address>"})
            return jsonify({"output": mine_block(cmd[1])})
        case 'balance':
            if len(cmd) != 3:
                return jsonify({"output": "Usage: balance <wallet_address> <private_key>"})
            return jsonify({"output": get_balance(cmd[1], cmd[2])})
        case 'send':
            if len(cmd) != 5:
                return jsonify({"output": "Usage: send <from> <to> <amount> <private_key>"})
            try:
                amount = float(cmd[3])
            except:
                return jsonify({"output": "❌ Invalid amount."})
            return jsonify({"output": send_macci(cmd[1], cmd[2], amount, cmd[4])})
        case 'trade':
            if len(cmd) != 3:
                return jsonify({"output": "Usage: trade <wallet_address> <usdt_amount>"})
            return jsonify({"output": trade_usdt(cmd[1], cmd[2])})
        case _:
            return jsonify({"output": "❓ Unknown command. Try: create, recover, mine, balance, send, trade"})

if __name__ == '__main__':
    create_genesis_block()
    print(f"✅ MACCI server running with difficulty {DIFFICULTY}")
    app.run(port=1000)
