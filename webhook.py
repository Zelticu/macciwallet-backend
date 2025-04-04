import stripe
from flask import Flask, request, jsonify
import os
import json
import requests

app = Flask(__name__)

# Your actual webhook secret from Stripe CLI or Dashboard
STRIPE_WEBHOOK_SECRET = "whsec_86370940d1a09fe720e7d9768c776b104517b7c95e08d4c6f38520aae95d5c36"

# Your local backend (must match app.py terminal port)
BACKEND_URL = "http://127.0.0.1:1000/trade"

@app.route("/stripe-webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except ValueError:
        print("❌ Invalid payload")
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError:
        print("❌ Invalid signature")
        return "Invalid signature", 400

    print(f"✅ Webhook received: {event['type']}")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        amount_paid = int(session.get("amount_total", 0)) / 100
        amount_macci = int(amount_paid / 0.01)

        wallet_address = None

        # Try custom_fields (for live Stripe checkout)
        try:
            custom_fields = session.get("custom_fields", [])
            for field in custom_fields:
                if "Macci wallet address" in field.get("label", {}).get("custom", ""):
                    wallet_address = field.get("text", {}).get("value")
                    break
        except Exception as e:
            print("⚠️ Error checking custom_fields:", e)

        # Fallback: try metadata
        if not wallet_address:
            wallet_address = session.get("metadata", {}).get("wallet_address")

        print("📦 Session object:")
        print(json.dumps(session, indent=2))

        if wallet_address:
            print(f"✅ Payment: ${amount_paid} → {amount_macci} MACCI → {wallet_address}")

                    # 🔁 Call backend /trade endpoint
        try:
            payload = {
                "wallet_address": wallet_address,
                "private_key": "UNKNOWN",  # backend will ignore key if "UNKNOWN"
                "usdt_amount": str(amount_paid)
            }
            response = requests.post(BACKEND_URL, json=payload)

            try:
                result = response.json().get("output", "❌ No output from backend")
            except Exception as e:
                print("❌ Backend responded with invalid JSON:", response.text)
                result = "❌ Invalid JSON response"

            print("🎯 Trade result:", result)

        except Exception as e:
            print("❌ Failed to call backend:", e)
    else:
        print("❌ Wallet address missing in session")

    return jsonify(success=True), 200

if __name__ == "__main__":
    stripe.api_key = "sk_test_placeholder"  # Stripe lib requires this, even if unused
    port = int(os.environ.get("PORT", 4242))
    app.run(host="0.0.0.0", port=port)

