# WhatsApp Cloud API Live Mode Setup Runbook

This runbook guides you through switching TaxPulse AI from `DEMO` simulator mode to `LIVE` Meta Cloud API mode.

---

## 1. Prerequisites
- A Meta for Developers account ([developers.facebook.com](https://developers.facebook.com/))
- A Meta Business Manager account
- A verified phone number dedicated to WhatsApp Business (or a Meta Test Number)

---

## 2. Meta App Configuration
1. **Create App**:
   - Go to Meta Developer Portal -> **My Apps** -> **Create App**.
   - Select **Other** -> App Type **Business**.
   - App Name: `TaxPulse AI Reconciliation`.

2. **Add WhatsApp Product**:
   - In App Dashboard, click **Add Product** and select **WhatsApp**.
   - Navigate to **WhatsApp > API Setup**.
   - Note your **Phone Number ID** and **WhatsApp Business Account ID (WABA ID)**.

3. **System User & Permanent Access Token**:
   - In Meta Business Settings, go to **System Users** -> **Add**.
   - Name: `taxpulse-bot`, Role: `Admin`.
   - Click **Generate New Token**, select your App.
   - Required Permissions:
     - `whatsapp_business_messaging`
     - `whatsapp_business_management`
   - Copy the generated permanent token to `WHATSAPP_ACCESS_TOKEN`.

---

## 3. Webhook Configuration
1. In Meta App Dashboard, go to **WhatsApp > Configuration > Webhook**.
2. Click **Edit**:
   - **Callback URL**: `https://<your-public-domain>/api/v1/whatsapp/webhook`
   - **Verify Token**: Must match `WHATSAPP_VERIFY_TOKEN` in your `.env`.
3. Click **Verify and Save**. TaxPulse returns the `hub.challenge` string in raw `text/plain`.
4. Under **Webhook fields**, click **Manage** and subscribe to:
   - `messages` (inbound user messages and status updates)

---

## 4. Environment Variables (.env)
Update your `.env` configuration:
```env
WHATSAPP_MODE=LIVE
WHATSAPP_PHONE_NUMBER_ID=109876543210987
WHATSAPP_ACCESS_TOKEN=EAAG...
WHATSAPP_VERIFY_TOKEN=taxpulse_webhook_secret_verify_token_2026
WHATSAPP_APP_SECRET=a1b2c3d4e5f6g7h8i9j0
```

---

## 5. Security & HMAC Verification
In `LIVE` mode:
- Every inbound webhook POST is verified with HMAC-SHA256 against `X-Hub-Signature-256`.
- Requests with invalid signatures are rejected with HTTP 403.
- The simulator endpoint `/api/v1/whatsapp/simulate-inbound` is disabled with HTTP 403 in `LIVE` mode.

---

## 6. Live Testing Flow
1. Send WhatsApp message `HELP` from a registered reviewer phone number to the bot's phone number.
2. Bot replies with list of commands (`HELP`, `SUMMARY`, `CRITICAL`, `EXPLAIN`, `CASE`, `REVIEW`, `CONFIRM`, `CANCEL`).
3. Send `CASE TX-10482` -> bot returns financial exposure and risk breakdown.
4. Send `REVIEW TX-10482` -> bot returns a single-use confirmation code valid for 10 minutes.
5. Send `CONFIRM TX-10482` -> case status transitions to `IN_REVIEW`, and audit log is recorded.
