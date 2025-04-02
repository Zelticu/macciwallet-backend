import stripe
from flask import Flask, request, jsonify
import os
import json

app = Flask(__name__)

# Set your real Stripe secret key
stripe.api_key = "sk_test_placeholder"  # Required for stripe lib

# Webhook secret
STRIPE_WEBHOOK_SECRET = "whsec_86370940d1a09fe720e7d9768c776b104517b7c95e08d4c6f38520aae95d5c36"

# Simulate MACCI wallet function
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
        amount_macci = int(amount_paid / 0.01)

        wallet_address = None

        # Try custom_fields first
        try:
            custom_fields = session.get("custom_fields", [])
            for field in custom_fields:
                if "Macci Wallet Address" in field.get("label", {}).get("custom", ""):
                    wallet_address = field.get("text", {}).get("value")
                    break
        except Exception as e:
            print(f"⚠️ Failed to parse custom_fields: {e}")

        # Try metadata fallback
        if not wallet_address:
            try:
                wallet_address = session.get("metadata", {}).get("wallet_address")
            except Exception as e:
                print(f"⚠️ Failed to parse metadata: {e}")

        # Log everything for debugging
        print("📝 Full session object:")
        print(json.dumps(session, indent=2))

        if wallet_address:
            send_macci_to_wallet(wallet_address, amount_macci)
            print(f"✅ Payment received: ${amount_paid} → {amount_macci} MACCI sent to {wallet_address}")
        else:
            print("❌ Wallet address missing — cannot send MACCI.")

    return jsonify(success=True), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 4242))
    app.run(host="0.0.0.0", port=port)
