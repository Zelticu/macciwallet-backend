import stripe
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Stripe webhook secret
STRIPE_WEBHOOK_SECRET = 'whsec_86370940d1a09fe720e7d9768c776b104517b7c95e08d4c6f38520aae95d5c36'

# Placeholder logic
def send_macci_to_wallet(wallet_address, amount):
    print(f"[✔] Sent {amount} MACCI to {wallet_address}")

@app.route('/stripe-webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        return 'Invalid signature', 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        amount_paid = int(session['amount_total']) / 100
        amount_macci = int(amount_paid / 0.01)

        wallet_address = None
        try:
            custom_fields = session.get("custom_fields", [])
            for field in custom_fields:
                if field["label"]["custom"] == "Macci Wallet Address":
                    wallet_address = field["text"]["value"]
                    break
        except Exception as e:
            print(f"⚠️ Error reading custom field: {e}")

        if wallet_address:
            send_macci_to_wallet(wallet_address, amount_macci)
            print(f"✅ Payment received: ${amount_paid} → {amount_macci} MACCI sent to {wallet_address}")
        else:
            print("⚠️ No wallet address found in custom fields.")

    return jsonify(success=True)

# === Run on Render ===

if __name__ == '__main__':
    stripe.api_key = 'sk_test_placeholder'
    port = int(os.environ.get("PORT", 4242))
    app.run(host="0.0.0.0", port=port)
