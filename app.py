from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib, json, time, uuid, os

app = Flask(__name__)
CORS(app)

wallets = {}
chain = []
transactions = []
WALLET_FILE = "macci_wallets.json"
MAX_SUPPLY = 100_000_000
MINING_REWARD = 10
PRESALE_RATE = 10000
DIFFICULTY = 9
total_mined = 0

MAIN_WALLET = "7fc8cb7519f34a0dbef5b2e15ecc24be"
MAIN_KEY = "895175c759ae4f7db233da59c9cec12c"

def save_wallets():
    data = {"wallets": wallets, "total_mined": total_mined}
    with open(WALLET_FILE, "w") as f:
        json.dump(data, f)

def load_wallets():
    global wallets, total_mined
    if os.path.exists(WALLET_FILE):
        with open(WALLET_FILE, "r") as f:
            data = json.load(f)
            wallets = data.get("wallets", {})
            total_mined = data.get("total_mined", 0)
    else:
        wallets[MAIN_WALLET] = {"balance": 40_000_000, "private_key": MAIN_KEY}
        total_mined = 40_000_000
        save_wallets()

def hash_block(block):
    return hashlib.sha256(json.dumps(block, sort_keys=True).encode()).hexdigest()

def proof_of_work(prev_proof):
    proof = 1
    while True:
        guess = hashlib.sha256(str(proof**2 - prev_proof**2).encode()).hexdigest()
        if guess[:DIFFICULTY] == "0" * DIFFICULTY:
            return proof
        proof += 1

@app.route('/mine', methods=['POST'])
def mine():
    data = request.get_json()
    address = data.get("wallet_address")
    key = data.get("private_key")

    if not address or not key:
        return jsonify({"output": "❌ Missing wallet or key"}), 400
    if address not in wallets or wallets[address]["private_key"] != key:
        return jsonify({"output": "❌ Invalid wallet or private key"}), 403
    global total_mined
    if total_mined + MINING_REWARD > MAX_SUPPLY:
        return jsonify({"output": "❌ Max supply reached"}), 403

    previous_proof = chain[-1]['proof']
    proof = proof_of_work(previous_proof)
    new_block = {
        "index": len(chain) + 1,
        "timestamp": time.time(),
        "proof": proof,
        "previous_hash": hash_block(chain[-1]),
        "transactions": transactions.copy()
    }
    chain.append(new_block)
    wallets[address]["balance"] += MINING_REWARD
    total_mined += MINING_REWARD
    transactions.clear()
    save_wallets()
    return jsonify({"output": f"⛏️ Block mined! +{MINING_REWARD} MACCI → {address}"}), 200

@app.route('/balance', methods=['POST'])
def balance():
    data = request.get_json()
    address = data.get("wallet_address")
    key = data.get("private_key")

    if not address or not key:
        return jsonify({"output": "❌ Missing data"}), 400
    if address not in wallets or wallets[address]["private_key"] != key:
        return jsonify({"output": "❌ Invalid wallet or key"}), 403
    return jsonify({"output": f"💰 Balance: {wallets[address]['balance']} MACCI"}), 200

@app.route('/send', methods=['POST'])
def send():
    data = request.get_json()
    sender = data.get("wallet_address")
    key = data.get("private_key")
    to = data.get("to")
    amount = data.get("amount")

    if not all([sender, key, to, amount]):
        return jsonify({"output": "❌ Missing required fields"}), 400
    if sender not in wallets or wallets[sender]["private_key"] != key:
        return jsonify({"output": "❌ Invalid wallet or key"}), 403
    if wallets[sender]["balance"] < float(amount):
        return jsonify({"output": "❌ Insufficient balance"}), 403

    if to not in wallets:
        wallets[to] = {"balance": 0, "private_key": "unknown"}

    wallets[sender]["balance"] -= float(amount)
    wallets[to]["balance"] += float(amount)
    save_wallets()
    return jsonify({"output": f"✅ Sent {amount} MACCI → {to}"}), 200

@app.route('/trade', methods=['POST'])
def trade():
    data = request.get_json()
    address = data.get("wallet_address")
    key = data.get("private_key")
    usdt_amount = float(data.get("usdt_amount", 0))

    global total_mined
    if not address or not key:
        return jsonify({"output": "❌ Missing data"}), 400
    if address not in wallets or wallets[address]["private_key"] != key:
        return jsonify({"output": "❌ Invalid wallet or key"}), 403
    if usdt_amount <= 0:
        return jsonify({"output": "❌ USDT amount must be greater than 0"}), 400

    macci_amount = int(usdt_amount * PRESALE_RATE)
    if total_mined + macci_amount > MAX_SUPPLY:
        return jsonify({"output": "❌ Max supply reached"}), 403

    wallets[address]["balance"] += macci_amount
    total_mined += macci_amount
    save_wallets()
    return jsonify({"output": f"💱 Traded {usdt_amount} USDT → {macci_amount} MACCI"}), 200

@app.route('/recover', methods=['POST'])
def recover():
    data = request.get_json()
    key = data.get("private_key")
    for addr, info in wallets.items():
        if info["private_key"] == key:
            return jsonify({"output": f"🔑 Wallet Address: {addr}"}), 200
    return jsonify({"output": "❌ Key not found"}), 404

if __name__ == '__main__':
    load_wallets()
    chain.append({
        "index": 1,
        "timestamp": time.time(),
        "proof": 100,
        "previous_hash": "1",
        "transactions": []
    })
    print(f"✅ MACCI Node Running! Difficulty {DIFFICULTY}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
