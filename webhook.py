import stripe
from flask import Flask, request, jsonify
import os
import json

app = Flask(__name__)

# Stripe webhook secret
STRIPE_WEBHOOK_SECRET = "whsec_8DcpqnYf4RYfjFcaHDk8I3HUF9L0GxPi"

# Simulate sending MACCI
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

        # Try custom fields
        try:
            custom_fields = session.get("custom_fields", [])
            for field in custom_fields:
                if "Macci Wallet Address" in field.get("label", {}).get("custom", ""):
                    wallet_address = field.get("text", {}).get("value")
                    break
        except Exception as e:
            print(f"⚠️ Could not parse custom_fields: {e}")

        # Try metadata fallback
        if not wallet_address:
            wallet_address = session.get("metadata", {}).get("wallet_address")

        # Print full session for debugging
        print("📦 Full session object:")
        print(json.dumps(session, indent=2))

        if wallet_address:
            send_macci_to_wallet(wallet_address, amount_macci)
            print(f"✅ Payment: ${amount_paid} → {amount_macci} MACCI → {wallet_address}")
        else:
            print("❌ Wallet address missing in session")

    return jsonify(success=True), 200

# ✅ FIXED: Use correct port from Render
if __name__ == '__main__':
    stripe.api_key = "sk_test_placeholder"  # Required by stripe lib
    port = int(os.environ.get("PORT", 10000))  # ✅ Matches Render port
    app.run(host="0.0.0.0", port=port)
