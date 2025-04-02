import stripe
from flask import Flask, request, jsonify
import os
import json

app = Flask(__name__)

# ✅ Set your real secret here
STRIPE_WEBHOOK_SECRET = "whsec_86370940d1a09fe720e7d9768c776b104517b7c95e08d4c6f38520aae95d5c36"

# ✅ Simulate sending MACCI (you can later connect to blockchain.py)
def send_macci_to_wallet(wallet_address, amount):
    print(f"✅ [MACCI SENT] {amount} MACCI → {wallet_address}")

@app.route('/stripe-webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except ValueError:
        print("❌ Invalid payload")
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        print("❌ Invalid signature")
        return 'Invalid signature', 400

    print(f"✅ Webhook received: {event['type']}")

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        amount_paid = int(session.get('amount_total', 0)) / 100
        amount_macci = int(amount_paid / 0.01)  # 100 MACCI per $1.00

        # Try to extract wallet address from any custom field
        wallet_address = None
        try:
            for field in session.get("custom_fields", []):
                label = field.get("label", {}).get("custom", "").lower()
                if "wallet" in label:
                    wallet_address = field.get("text", {}).get("value")
                    break
        except Exception as e:
            print(f"⚠️ Could not parse custom_fields: {e}")

        # Fallback: check metadata
        if not wallet_address:
            wallet_address = session.get("metadata", {}).get("wallet_address")

        print("📦 Full session object:")
        print(json.dumps(session, indent=2))

        if wallet_address:
            send_macci_to_wallet(wallet_address, amount_macci)
            print(f"✅ Payment: ${amount_paid} → {amount_macci} MACCI → {wallet_address}")
        else:
            print("❌ Wallet address missing in session")

    return jsonify(success=True), 200

# ✅ Proper Render port binding
if __name__ == '__main__':
    stripe.api_key = "sk_test_placeholder"  # required by stripe lib even if unused
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
