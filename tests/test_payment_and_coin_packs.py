import os
import sys
import hmac
import hashlib
import json
import uuid
import urllib.request
import urllib.error

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import settings

BASE_URL = "http://127.0.0.1:8000"

def make_req(url, data=None, token=None, method=None, headers=None):
    hdrs = headers.copy() if headers else {}
    if token:
        hdrs['Authorization'] = f'Bearer {token}'
    if data is not None:
        if isinstance(data, (dict, list)):
            hdrs['Content-Type'] = 'application/json'
            body = json.dumps(data).encode('utf-8')
        elif isinstance(data, bytes):
            body = data
        else:
            body = data.encode('utf-8')
    else:
        body = None
    req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
    try:
        resp = urllib.request.urlopen(req)
        raw = resp.read().decode('utf-8')
        try:
            return resp.status, json.loads(raw)
        except Exception:
            return resp.status, raw
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        try:
            parsed = json.loads(err_body)
        except Exception:
            parsed = err_body
        return e.code, parsed

def run_tests():
    print("=" * 60)
    print("=== HunarMitra Dynamic Coin Packs & Payments Integration Test ===")
    print("=" * 60)

    # -------------------------------------------------------------
    # 1. Verify default coin packs exist and pricing is server-side
    # -------------------------------------------------------------
    print("\n--- Test 1: Verify Default Coin Packs ---")
    status, packs = make_req(f"{BASE_URL}/coin-packs")
    assert status == 200, f"Failed listing coin packs: {packs}"
    print(f"Active coin packs count: {len(packs)}")
    
    codes = {p['code']: p for p in packs}
    assert 'pack_10' in codes, "pack_10 missing"
    assert 'pack_30' in codes, "pack_30 missing"
    assert 'pack_70' in codes, "pack_70 missing"
    assert 'pack_150' in codes, "pack_150 missing"

    assert codes['pack_10']['coins'] == 10 and float(codes['pack_10']['price_inr']) == 10.00
    assert codes['pack_30']['coins'] == 30 and float(codes['pack_30']['price_inr']) == 25.00
    assert codes['pack_70']['coins'] == 70 and float(codes['pack_70']['price_inr']) == 50.00
    assert codes['pack_150']['coins'] == 150 and float(codes['pack_150']['price_inr']) == 100.00
    print("[PASS] Initial default coin packs verified (10/Rs10, 30/Rs25, 70/Rs50, 150/Rs100).")

    # -------------------------------------------------------------
    # 2. Register test customer and verify initial wallet balance
    # -------------------------------------------------------------
    print("\n--- Test 2: Register Test Customer ---")
    test_phone = f"+9188888{str(uuid.uuid4().int)[:5]}"
    status, reg = make_req(f"{BASE_URL}/api/v1/auth/register", {
        'phone_number': test_phone,
        'full_name': 'Coin Pack Tester',
        'language_preference': 'English',
        'role': 'customer'
    })
    assert status == 201, f"Customer registration failed: {reg}"

    status, login = make_req(f"{BASE_URL}/api/v1/auth/verify-otp", {
        'phone_number': test_phone,
        'otp': '123456'
    })
    assert status == 200, f"Customer login failed: {login}"
    cust_token = login['access_token']
    print(f"Customer logged in: {test_phone}")

    status, wallet = make_req(f"{BASE_URL}/wallet", token=cust_token)
    assert status == 200
    initial_total = wallet['total_coins']
    initial_purchased = wallet['purchased_coins']
    print(f"Initial wallet: total={initial_total}, purchased={initial_purchased}")

    # -------------------------------------------------------------
    # 3. Create Payment Order & Verify Server-Side Pricing Snapshot
    # -------------------------------------------------------------
    print("\n--- Test 3: Create Payment Order with Server-Side Pricing ---")
    # Even if client sends malicious or untrusted payload attributes, backend only uses DB pack definition
    status, order1 = make_req(f"{BASE_URL}/coin-packs/orders", {
        'pack_code': 'pack_30',
        'payment_method': 'UPI'
    }, token=cust_token)
    assert status == 201, f"Create order failed: {order1}"
    
    order1_id = order1['order_id']
    assert order1['coins'] == 30
    assert float(order1['amount_inr']) == 25.00
    assert order1['status'] == 'PENDING'
    assert order1['coins_credited'] is False
    assert order1['pack_code'] == 'pack_30'
    print(f"Order created: {order1_id}, Amount: Rs {order1['amount_inr']}, Coins: {order1['coins']}")
    print("[PASS] Server enforced official pack price and created snapshot.")

    # -------------------------------------------------------------
    # 4. Status Polling Before Payment
    # -------------------------------------------------------------
    print("\n--- Test 4: Poll Order Status Before Payment ---")
    status, polled = make_req(f"{BASE_URL}/coin-packs/orders/{order1_id}", token=cust_token)
    assert status == 200
    assert polled['status'] == 'PENDING'
    assert polled['coins_credited'] is False

    # Verify wallet balance has NOT changed while payment is pending
    status, wallet_check = make_req(f"{BASE_URL}/wallet", token=cust_token)
    assert wallet_check['purchased_coins'] == initial_purchased, "Pending order altered wallet balance!"
    print("[PASS] Polled status is PENDING and wallet balance remains untouched.")

    # -------------------------------------------------------------
    # 5. Signature Verification & Coin Crediting
    # -------------------------------------------------------------
    print("\n--- Test 5: Verify Payment Signature & Credit Coins ---")
    
    # 5a. Tampered / Invalid signature must be rejected and must not alter wallet
    status, bad_order = make_req(f"{BASE_URL}/coin-packs/orders", {
        'pack_code': 'pack_10',
        'payment_method': 'UPI'
    }, token=cust_token)
    assert status == 201
    bad_order_id = bad_order['order_id']
    bad_payment_id = f"pay_{uuid.uuid4().hex[:12]}"

    status, bad_res = make_req(f"{BASE_URL}/coin-packs/orders/{bad_order_id}/verify", {
        'gateway_payment_id': bad_payment_id,
        'gateway_signature': 'invalid_forged_signature_1234'
    }, token=cust_token)
    assert status == 400, f"Tampered signature should fail, got status {status}: {bad_res}"
    print("[PASS] Tampered signature rejected with 400 Bad Request.")

    # Wallet must still be unchanged
    status, wallet_check = make_req(f"{BASE_URL}/wallet", token=cust_token)
    assert wallet_check['purchased_coins'] == initial_purchased, "Failed verification altered wallet!"

    # 5b. Valid HMAC SHA256 Signature on order1
    fake_payment_id = f"pay_{uuid.uuid4().hex[:12]}"
    sign_payload = f"{order1_id}|{fake_payment_id}".encode('utf-8')
    valid_sig = hmac.new(
        settings.PAYMENT_WEBHOOK_SECRET.encode('utf-8'),
        sign_payload,
        hashlib.sha256
    ).hexdigest()

    status, verify_res = make_req(f"{BASE_URL}/coin-packs/orders/{order1_id}/verify", {
        'gateway_payment_id': fake_payment_id,
        'gateway_signature': valid_sig
    }, token=cust_token)
    assert status == 200, f"Valid verification failed: {verify_res}"
    assert verify_res['status'] == 'SUCCESS'
    assert verify_res['coins_credited'] is True
    assert verify_res['coins_added'] == 30
    print(f"Payment verified: {verify_res['message']}")

    # Check wallet balance now credited
    status, wallet_after = make_req(f"{BASE_URL}/wallet", token=cust_token)
    assert wallet_after['purchased_coins'] == initial_purchased + 30
    print(f"New wallet balance: purchased={wallet_after['purchased_coins']}, total={wallet_after['total_coins']}")
    print("[PASS] Valid signature credited +30 coins to user wallet.")

    # -------------------------------------------------------------
    # 6. Idempotency Check: Repeat verification must not double credit
    # -------------------------------------------------------------
    print("\n--- Test 6: Idempotency Protection ---")
    status, repeat_res = make_req(f"{BASE_URL}/coin-packs/orders/{order1_id}/verify", {
        'gateway_payment_id': fake_payment_id,
        'gateway_signature': valid_sig
    }, token=cust_token)
    assert status == 200
    assert repeat_res['status'] == 'SUCCESS'
    assert repeat_res['coins_credited'] is True

    status, wallet_check2 = make_req(f"{BASE_URL}/wallet", token=cust_token)
    assert wallet_check2['purchased_coins'] == initial_purchased + 30, "Duplicate verify double-credited coins!"
    print("[PASS] Idempotent retry: returned success without duplicate coin credit.")

    # -------------------------------------------------------------
    # 7. Signature-Verified Webhook Flow
    # -------------------------------------------------------------
    print("\n--- Test 7: Signature-Verified Payment Webhook ---")
    status, order2 = make_req(f"{BASE_URL}/coin-packs/orders", {
        'pack_code': 'pack_70',
        'payment_method': 'UPI'
    }, token=cust_token)
    assert status == 201
    order2_id = order2['order_id']
    print(f"Created order2: {order2_id} (70 coins / Rs 50)")

    hook_payment_id = f"pay_hook_{uuid.uuid4().hex[:10]}"
    webhook_payload_dict = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": hook_payment_id,
                    "order_id": order2_id,
                    "status": "captured",
                    "amount": 5000,
                    "currency": "INR"
                }
            }
        }
    }
    raw_payload_bytes = json.dumps(webhook_payload_dict).encode('utf-8')

    # 7a. Webhook with invalid signature
    status, hook_fail = make_req(
        f"{BASE_URL}/payments/webhook",
        data=raw_payload_bytes,
        headers={"X-Razorpay-Signature": "bad_hook_signature_xyz"}
    )
    assert status == 400, f"Webhook with bad signature should fail: {hook_fail}"
    print("[PASS] Webhook with invalid signature rejected.")

    # 7b. Webhook with valid HMAC SHA256 signature
    valid_hook_sig = hmac.new(
        settings.PAYMENT_WEBHOOK_SECRET.encode('utf-8'),
        raw_payload_bytes,
        hashlib.sha256
    ).hexdigest()

    status, hook_success = make_req(
        f"{BASE_URL}/payments/webhook",
        data=raw_payload_bytes,
        headers={"X-Razorpay-Signature": valid_hook_sig}
    )
    assert status == 200, f"Webhook processing failed: {hook_success}"
    assert hook_success['status'] == 'order_credited'
    assert hook_success['coins_credited'] == 70
    print(f"Webhook response: {hook_success}")

    # Check wallet balance now has +30 + 70 = +100
    status, wallet_after_hook = make_req(f"{BASE_URL}/wallet", token=cust_token)
    assert wallet_after_hook['purchased_coins'] == initial_purchased + 30 + 70
    print(f"Wallet balance after webhook: purchased={wallet_after_hook['purchased_coins']}")

    # 7c. Duplicate webhook must be idempotent
    status, hook_dup = make_req(
        f"{BASE_URL}/payments/webhook",
        data=raw_payload_bytes,
        headers={"X-Razorpay-Signature": valid_hook_sig}
    )
    assert status == 200
    assert hook_dup['status'] == 'already_credited'
    status, wallet_dup_check = make_req(f"{BASE_URL}/wallet", token=cust_token)
    assert wallet_dup_check['purchased_coins'] == initial_purchased + 100
    print("[PASS] Webhook processed and verified idempotency.")

    # -------------------------------------------------------------
    # 8. Paginated Transaction History (/wallet/transactions)
    # -------------------------------------------------------------
    print("\n--- Test 8: Paginated Transaction History ---")
    status, txs = make_req(f"{BASE_URL}/wallet/transactions?page=1&limit=10", token=cust_token)
    assert status == 200, f"Failed listing transactions: {txs}"
    assert txs['total'] >= 2, f"Expected at least 2 transactions, got {txs['total']}"
    assert len(txs['items']) >= 2

    # Verify transaction item structure
    first_tx = txs['items'][0]
    assert 'action' in first_tx
    assert 'amount' in first_tx
    assert 'transaction_type' in first_tx
    assert 'reference_id' in first_tx
    print(f"Found {txs['total']} transaction(s). Latest: {first_tx['transaction_type']} +{first_tx['amount']} coins (Ref: {first_tx['reference_id']})")

    # Filter test
    status, credit_txs = make_req(f"{BASE_URL}/wallet/transactions?action=CREDIT", token=cust_token)
    assert status == 200
    for it in credit_txs['items']:
        assert it['action'] == 'CREDIT'
    print("[PASS] Paginated transaction history and filtering verified.")

    # -------------------------------------------------------------
    # 9. Admin Dynamic Coin Pack Management & Live App Sync
    # -------------------------------------------------------------
    print("\n--- Test 9: Admin Dynamic Coin Pack Management ---")
    # Login admin
    status, admin_login = make_req(f"{BASE_URL}/api/v1/auth/verify-otp", {
        'phone_number': '+919999999900',
        'otp': '123456'
    })
    assert status == 200, f"Admin login failed: {admin_login}"
    admin_token = admin_login['access_token']
    print("Admin logged in successfully.")

    # 9a. Admin creates a new pack dynamically without code changes
    new_pack_code = f"pack_dynamic_{str(uuid.uuid4().hex[:6])}"
    status, created_pack = make_req(f"{BASE_URL}/admin/coin-packs", {
        'name': 'Festive Booster Pack',
        'code': new_pack_code,
        'coins': 250,
        'bonus_coins': 50,
        'price_inr': 180.00,
        'is_popular': True,
        'badge_text': 'Diwali Special',
        'description': '250 Coins + 50 Bonus Coins for Diwali',
        'sort_order': 5,
        'is_active': True
    }, token=admin_token)
    assert status == 201, f"Admin create pack failed: {created_pack}"
    pack_id = created_pack['id']
    print(f"Admin created pack: {created_pack['name']} (code={created_pack['code']}, ID={pack_id})")

    # Verify regular user immediately sees this new pack
    status, user_packs = make_req(f"{BASE_URL}/coin-packs")
    assert any(p['code'] == new_pack_code for p in user_packs), "User could not see newly created pack!"
    print("[PASS] User immediately sees newly created pack.")

    # 9b. Admin updates price and coin quantity dynamically
    status, updated_pack = make_req(f"{BASE_URL}/admin/coin-packs/{pack_id}", {
        'price_inr': 160.00,
        'bonus_coins': 75,
        'name': 'Mega Festive Booster'
    }, token=admin_token, method='PUT')
    assert status == 200, f"Admin update pack failed: {updated_pack}"
    assert float(updated_pack['price_inr']) == 160.00
    assert updated_pack['bonus_coins'] == 75
    print(f"Admin updated pack: Price=Rs {updated_pack['price_inr']}, Bonus={updated_pack['bonus_coins']}")

    # Customer orders this pack at the new price
    status, order_dyn = make_req(f"{BASE_URL}/coin-packs/orders", {
        'pack_code': new_pack_code
    }, token=cust_token)
    assert status == 201
    assert float(order_dyn['amount_inr']) == 160.00
    assert order_dyn['coins'] == 250
    assert order_dyn['bonus_coins'] == 75
    assert order_dyn['total_coins'] == 325
    print(f"[PASS] Order created with updated dynamic pricing: Rs {order_dyn['amount_inr']}, Total Coins: {order_dyn['total_coins']}")

    # 9c. Admin toggles active status to False
    status, toggled = make_req(f"{BASE_URL}/admin/coin-packs/{pack_id}/toggle-status", token=admin_token, method='PATCH')
    assert status == 200
    assert toggled['is_active'] is False
    print("Admin deactivated coin pack.")

    # Verify inactive pack is no longer purchasable by user
    status, user_packs2 = make_req(f"{BASE_URL}/coin-packs")
    assert not any(p['code'] == new_pack_code for p in user_packs2), "Deactivated pack still shown to user!"

    status, order_fail = make_req(f"{BASE_URL}/coin-packs/orders", {
        'pack_code': new_pack_code
    }, token=cust_token)
    assert status in (400, 404), f"Ordering inactive pack should fail: {order_fail}"
    print(f"[PASS] Deactivated pack hidden from users and rejected for orders (returned {status}).")

    # 9d. Admin soft deletes pack
    status, del_res = make_req(f"{BASE_URL}/admin/coin-packs/{pack_id}", token=admin_token, method='DELETE')
    assert status == 200
    print(f"Admin deleted pack: {del_res}")

    # 9e. Admin views all payment orders
    status, admin_orders = make_req(f"{BASE_URL}/admin/orders?page=1&limit=20", token=admin_token)
    assert status == 200
    assert admin_orders['total'] >= 3
    print(f"Admin orders overview: {admin_orders['total']} total order(s) listed.")
    print("[PASS] Admin management & synchronization completely verified.")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY! (9/9 Test Suites)")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
