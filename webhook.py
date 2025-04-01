import stripe
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# ✅ Replace with your real secret key
stripe.api_key = 'sk_test_placeholder'
STRIPE_WEBHOOK_SECRET = 'whsec_QEXUaQvlxeH5NUgILY3AULiXc23kkDsj'  # example

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

    print("✅ Webhook received:", event['type'])

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
            print("⚠️ Couldn't read wallet address:", e)

        if wallet_address:
            print(f"✅ Sent {amount_macci} MACCI to {wallet_address}")
        else:
            print("⚠️ Wallet address missing.")

    return jsonify(success=True), 200  # ✅ Stripe expects 200 OK

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 4242))
    app.run(host="0.0.0.0", port=port)
