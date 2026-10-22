import os
import sys
import uuid
import json
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

def login_admin():
    status, login = make_req(f"{BASE_URL}/api/v1/auth/verify-otp", {
        'phone_number': '+919999999900',
        'otp': '123456'
    })
    assert status == 200, f"Admin login failed: {login}"
    return login['access_token']

def register_customer(name="Signup Reward Tester"):
    phone = f"+91981{str(uuid.uuid4().int)[:7]}"
    status, reg = make_req(f"{BASE_URL}/api/v1/auth/register", {
        'phone_number': phone,
        'full_name': name,
        'language_preference': 'English',
        'role': 'customer'
    })
    assert status == 201, f"Customer register failed: {reg}"

    status, login = make_req(f"{BASE_URL}/api/v1/auth/verify-otp", {
        'phone_number': phone,
        'otp': '123456'
    })
    assert status == 200, f"Customer login failed: {login}"
    return login['access_token'], phone, reg['id']

def run_tests():
    print("=" * 70)
    print("=== HunarMitra First-Time Customer Signup Reward Integration Tests ===")
    print("=" * 70)

    admin_token = login_admin()
    print("Admin logged in successfully.")

    # -------------------------------------------------------------------------
    # Baseline setup: Ensure signup_bonus_enabled = True and signup_bonus_coins = 50
    # -------------------------------------------------------------------------
    status, baseline = make_req(f"{BASE_URL}/admin/configs", {
        'signup_bonus_enabled': True,
        'signup_bonus_coins': 50,
        'reveal_rate_limit_per_minute': 20
    }, token=admin_token, method='PUT')
    assert status == 200, f"Failed setting baseline config: {baseline}"
    print("[SETUP] Config set: signup_bonus_enabled=True, signup_bonus_coins=50.")

    # -------------------------------------------------------------------------
    # 1. First-time customer signs up: receives 50 earned coins immediately
    # -------------------------------------------------------------------------
    print("\n--- Test 1: First-time Customer Signup Bonus (50 Coins) ---")
    cust_token, cust_phone, cust_id = register_customer("P1 First Time User")
    print(f"Customer registered: {cust_phone}")

    # Immediately query customer wallet API
    status, wallet = make_req(f"{BASE_URL}/wallet", token=cust_token)
    assert status == 200, f"GET /wallet failed: {wallet}"
    assert wallet['purchased_coins'] == 0, f"Expected 0 purchased, got {wallet['purchased_coins']}"
    assert wallet['earned_coins'] == 50, f"Expected 50 earned coins, got {wallet['earned_coins']}"
    assert wallet['total_coins'] == 50, f"Expected 50 total coins, got {wallet['total_coins']}"
    print(f"Wallet API response: purchased={wallet['purchased_coins']}, earned={wallet['earned_coins']}, total={wallet['total_coins']}")
    print("[PASS] 50 earned coins credited immediately upon first-time signup.")

    # Check coin ledger entry
    status, txs = make_req(f"{BASE_URL}/wallet/transactions?page=1&limit=10", token=cust_token)
    assert status == 200, f"GET /wallet/transactions failed: {txs}"
    assert txs['total'] >= 1
    signup_tx = [t for t in txs['items'] if t['transaction_type'] == 'SIGNUP_BONUS']
    assert len(signup_tx) == 1, f"Expected exactly 1 SIGNUP_BONUS transaction, found {len(signup_tx)}"
    entry = signup_tx[0]
    assert entry['action'] == 'CREDIT', f"Expected CREDIT action, got {entry['action']}"
    assert entry['coin_type'] == 'earned', f"Expected earned coin_type, got {entry['coin_type']}"
    assert entry['amount'] == 50, f"Expected 50 coins, got {entry['amount']}"
    assert entry['description'] == 'Signup Bonus', f"Expected 'Signup Bonus' reason, got '{entry['description']}'"
    print(f"Ledger record verified: {entry['transaction_type']} | {entry['action']} | {entry['amount']} {entry['coin_type']} | '{entry['description']}'")
    print("[PASS] Coin ledger accurately records 'Signup Bonus' as requested.")

    # -------------------------------------------------------------------------
    # 2. Idempotency & Repeat Request Protection
    # -------------------------------------------------------------------------
    print("\n--- Test 2: Idempotency Protection ---")
    # Calling GET /wallet repeatedly must never duplicate the bonus
    for _ in range(3):
        status, repeat_wallet = make_req(f"{BASE_URL}/wallet", token=cust_token)
        assert status == 200
        assert repeat_wallet['earned_coins'] == 50
        assert repeat_wallet['total_coins'] == 50

    status, repeat_txs = make_req(f"{BASE_URL}/wallet/transactions?page=1&limit=10", token=cust_token)
    signup_txs = [t for t in repeat_txs['items'] if t['transaction_type'] == 'SIGNUP_BONUS']
    assert len(signup_txs) == 1, "Duplicate SIGNUP_BONUS entries detected!"
    print("[PASS] Subsequent wallet queries and idempotent checks do not re-credit.")

    # Retrying register with same phone must be rejected
    status, dup_reg = make_req(f"{BASE_URL}/api/v1/auth/register", {
        'phone_number': cust_phone,
        'full_name': 'Duplicate Attempt',
        'role': 'customer'
    })
    assert status == 400, f"Expected 400 for duplicate registration, got {status}"
    print("[PASS] Repeated registration request with same phone rejected.")

    # -------------------------------------------------------------------------
    # 3. Using Earned Signup Coins for Contact Reveals
    # -------------------------------------------------------------------------
    print("\n--- Test 3: Use Signup Coins for Contact Reveals ---")
    status, workers = make_req(f"{BASE_URL}/workers", token=cust_token)
    assert status == 200 and len(workers) >= 6, "Need at least 6 workers in DB"

    # Exhaust 5 free contacts
    for i in range(5):
        w_id = workers[i]['id']
        status, rev = make_req(f"{BASE_URL}/workers/{w_id}/reveal", data={}, token=cust_token)
        assert status == 200
        assert rev['is_free_reveal'] is True
        assert rev['coins_deducted'] == 0

    # 6th contact unlock requires coins (10 coins)
    w5_id = workers[5]['id']
    status, cs5 = make_req(f"{BASE_URL}/workers/{w5_id}/contact-status", token=cust_token)
    assert status == 200
    assert cs5['free_contacts_remaining'] == 0
    assert cs5['coins_required'] == 10
    assert cs5['can_reveal'] is True # Because customer has 50 earned coins!

    # Unlock 6th contact using signup bonus earned coins
    status, rev5 = make_req(f"{BASE_URL}/workers/{w5_id}/reveal", data={}, token=cust_token)
    assert status == 200, f"Paid reveal failed: {rev5}"
    assert rev5['is_free_reveal'] is False
    assert rev5['coins_deducted'] == 10
    assert rev5['contact_phone'] is not None

    # Verify wallet has 40 earned coins remaining (50 - 10)
    status, wallet_after_reveal = make_req(f"{BASE_URL}/wallet", token=cust_token)
    assert wallet_after_reveal['earned_coins'] == 40, f"Expected 40 earned coins, got {wallet_after_reveal['earned_coins']}"
    assert wallet_after_reveal['total_coins'] == 40
    print(f"6th reveal deducted 10 earned coins. Wallet balance: {wallet_after_reveal['total_coins']} coins remaining.")
    print("[PASS] Customer successfully used signup bonus coins to unlock worker contact.")

    # -------------------------------------------------------------------------
    # 4. Admin Dynamic Config: Update Reward Amount to 75 Coins
    # -------------------------------------------------------------------------
    print("\n--- Test 4: Dynamic Admin Configuration (75 Coins) ---")
    status, cfg_update = make_req(f"{BASE_URL}/admin/configs", {
        'signup_bonus_coins': 75
    }, token=admin_token, method='PUT')
    assert status == 200

    # Verify public /config/coins reflects the new amount
    status, pub_cfg = make_req(f"{BASE_URL}/config/coins")
    assert status == 200
    assert pub_cfg['signup_bonus_coins'] == 75

    # Register a new customer
    cust2_token, cust2_phone, _ = register_customer("P1 75 Coin User")
    status, wallet2 = make_req(f"{BASE_URL}/wallet", token=cust2_token)
    assert status == 200
    assert wallet2['earned_coins'] == 75, f"Expected 75 earned coins, got {wallet2['earned_coins']}"
    assert wallet2['total_coins'] == 75
    print(f"Customer {cust2_phone} received updated signup reward: {wallet2['total_coins']} coins.")
    print("[PASS] Updating reward amount dynamically to 75 coins takes effect immediately.")

    # -------------------------------------------------------------------------
    # 5. Admin Dynamic Config: Disable Signup Reward
    # -------------------------------------------------------------------------
    print("\n--- Test 5: Dynamic Admin Configuration (Disable Reward) ---")
    status, cfg_disable = make_req(f"{BASE_URL}/admin/configs", {
        'signup_bonus_enabled': False
    }, token=admin_token, method='PUT')
    assert status == 200

    # Register another customer when disabled
    cust3_token, cust3_phone, _ = register_customer("P1 Disabled Bonus User")
    status, wallet3 = make_req(f"{BASE_URL}/wallet", token=cust3_token)
    assert status == 200
    assert wallet3['earned_coins'] == 0, f"Expected 0 earned coins when disabled, got {wallet3['earned_coins']}"
    assert wallet3['total_coins'] == 0
    print(f"Customer {cust3_phone} registered while disabled: {wallet3['total_coins']} coins.")
    print("[PASS] When signup reward is disabled, new customer receives 0 bonus coins.")

    # -------------------------------------------------------------------------
    # Clean up: Restore default 50 coins and enabled=True
    # -------------------------------------------------------------------------
    make_req(f"{BASE_URL}/admin/configs", {
        'signup_bonus_enabled': True,
        'signup_bonus_coins': 50
    }, token=admin_token, method='PUT')
    print("\n[CLEANUP] Restored default signup configuration (50 coins, enabled=True).")

    print("\n" + "=" * 70)
    print("ALL FIRST-TIME SIGNUP REWARD TESTS PASSED SUCCESSFULLY! (100%)")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
