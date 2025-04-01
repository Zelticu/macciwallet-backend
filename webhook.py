import stripe
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# ✅ Replace this with your Stripe test secret key
stripe.api_key = 'sk_test_placeholder'

# ✅ Your actual webhook secret (from Render or CLI)
STRIPE_WEBHOOK_SECRET = 'whsec_86370940d1a09fe720e7d9768c776b104517b7c95e08d4c6f38520aae95d5c36'

@app.route('/stripe-webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
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

        # ✅ Try to extract custom wallet address
        custom_fields = session.get("custom_fields", [])
        for field in custom_fields:
            try:
                if field["label"]["custom"] == "Macci Wallet Address":
                    wallet_address = field["text"]["value"]
                    break
            except Exception as e:
                print(f"⚠️ Failed to read custom field: {e}")

        if wallet_address:
            print(f"✅ Payment received: ${amount_paid} → {amount_macci} MACCI sent to {wallet_address}")
            # TODO: Integrate with MACCI balance logic (optional)
        else:
            print("⚠️ No wallet address found in custom fields.")

    return jsonify(success=True), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 4242))
    app.run(host="0.0.0.0", port=port)
