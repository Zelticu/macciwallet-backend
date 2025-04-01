from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# === Blockchain-Like Presale System ===

MAX_SUPPLY = 100_000_000
PREMINE_AMOUNT = 40_000_000
PRESALE_RATE = 10000  # 100 MACCI = $0.01 → 10,000 MACCI per $1

wallets = {}  # { address: balance }
total_minted = 0

# Your main wallet (premine address)
MAIN_WALLET = "7fc8cb7519f34a0dbef5b2e15ecc24be"
wallets[MAIN_WALLET] = PREMINE_AMOUNT
total_minted += PREMINE_AMOUNT

@app.route('/buy', methods=['POST'])
def buy_macci():
    global total_minted

    data = request.get_json()
    address = data.get("wallet_address")
    amount_usd = data.get("amount_usd")

    if not address or amount_usd is None:
        return jsonify({"success": False, "message": "Missing wallet address or amount."}), 400

    try:
        amount_usd = float(amount_usd)
    except:
        return jsonify({"success": False, "message": "Invalid amount."}), 400

    if amount_usd < 0.01:
        return jsonify({"success": False, "message": "Minimum purchase is $0.01."}), 400

    macci_amount = int(amount_usd * PRESALE_RATE)

    if total_minted + macci_amount > MAX_SUPPLY:
        return jsonify({"success": False, "message": "❌ Max supply reached. Cannot mint more MACCI."}), 400

    wallets[address] = wallets.get(address, 0) + macci_amount
    total_minted += macci_amount

    return jsonify({
        "success": True,
        "message": f"✅ You bought {macci_amount} MACCI!",
        "wallet_address": address,
        "new_balance": wallets[address],
        "total_minted": total_minted,
        "max_supply": MAX_SUPPLY
    })

@app.route('/presale_balance', methods=['GET'])
def presale_balance():
    address = request.args.get("wallet_address")
    if not address:
        return jsonify({"success": False, "message": "Missing wallet address."}), 400
    balance = wallets.get(address, 0)
    return jsonify({"success": True, "balance": balance})

@app.route('/total_supply', methods=['GET'])
def get_total_supply():
    return jsonify({
        "total_minted": total_minted,
        "max_supply": MAX_SUPPLY
    })

@app.route('/wallets', methods=['GET'])
def get_all_wallets():
    return jsonify(wallets)

if __name__ == "__main__":
    print(f"✅ Pre-mined {PREMINE_AMOUNT} MACCI to {MAIN_WALLET}")
    app.run(port=5050)
