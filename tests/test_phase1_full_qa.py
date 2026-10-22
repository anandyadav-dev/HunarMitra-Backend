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

def login_admin():
    status, login = make_req(f"{BASE_URL}/api/v1/auth/verify-otp", {
        'phone_number': '+919999999900',
        'otp': '123456'
    })
    assert status == 200, f"Admin login failed: {login}"
    return login['access_token']

def register_customer(name="QA Customer"):
    phone = f"+91987{str(uuid.uuid4().int)[:7]}"
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

def run_all_qa_tests():
    print("=" * 70)
    print(" HUNARMITRA PHASE 1 - COMPREHENSIVE END-TO-END QA TEST SUITE")
    print("=" * 70)

    admin_token = login_admin()
    cust_token, cust_phone, cust_user_id = register_customer("P1 Test Customer")
    print(f"Logged in Admin & Customer: {cust_phone}")

    # =========================================================================
    # Task 1: Backend Foundation & Configuration
    # =========================================================================
    print("\n[QA SUITE 1] Task 1: Backend Foundation & Configuration")
    status, config = make_req(f"{BASE_URL}/config/coins")
    assert status == 200, f"GET /config/coins failed: {config}"
    assert 'free_contacts_limit' in config
    assert 'contact_unlock_cost' in config
    assert 'feedback_rating_reward_coins' in config
    assert 'feedback_photo_reward_coins' in config
    assert 'refund_window_hours' in config
    print(f"Verified /config/coins: free_contacts={config['free_contacts_limit']}, unlock_cost={config['contact_unlock_cost']}")

    status, wallet = make_req(f"{BASE_URL}/wallet", token=cust_token)
    assert status == 200, f"GET /wallet failed: {wallet}"
    assert 'purchased_coins' in wallet
    assert 'earned_coins' in wallet
    assert 'total_coins' in wallet
    assert wallet['total_coins'] == wallet['purchased_coins'] + wallet['earned_coins']
    print(f"Verified /wallet balance separation: purchased={wallet['purchased_coins']}, earned={wallet['earned_coins']}, total={wallet['total_coins']}")
    print("[PASS] Task 1: Backend Foundation & Configuration verified.")

    # =========================================================================
    # Task 2: Admin Dynamic Coin Pack Management & Order Snapshot Preservation
    # =========================================================================
    print("\n[QA SUITE 2] Task 2: Admin Dynamic Coin Packs & Snapshot Preservation")
    pack_code = f"pack_qa_{uuid.uuid4().hex[:6]}"
    status, new_pack = make_req(f"{BASE_URL}/admin/coin-packs", {
        'name': 'QA Special Pack',
        'code': pack_code,
        'coins': 80,
        'bonus_coins': 20,
        'price_inr': 60.00,
        'is_popular': False,
        'badge_text': 'QA Promo',
        'description': 'QA Pack with 80+20 coins',
        'is_active': True
    }, token=admin_token)
    assert status == 201, f"Admin create pack failed: {new_pack}"
    pack_id = new_pack['id']

    # Customer orders this pack (price = 60.00, coins = 80, bonus = 20)
    status, order_snap = make_req(f"{BASE_URL}/coin-packs/orders", {
        'pack_code': pack_code
    }, token=cust_token)
    assert status == 201
    assert float(order_snap['amount_inr']) == 60.00
    assert order_snap['coins'] == 80
    assert order_snap['bonus_coins'] == 20
    assert order_snap['total_coins'] == 100
    snap_order_id = order_snap['order_id']
    print(f"Created Order #{snap_order_id} at snapshot price: Rs {order_snap['amount_inr']}, total coins: {order_snap['total_coins']}")

    # Admin updates the pack price and coins dynamically
    status, updated_pack = make_req(f"{BASE_URL}/admin/coin-packs/{pack_id}", {
        'price_inr': 75.00,
        'coins': 90,
        'bonus_coins': 30
    }, token=admin_token, method='PUT')
    assert status == 200
    assert float(updated_pack['price_inr']) == 75.00
    assert updated_pack['coins'] == 90
    print(f"Admin updated pack #{pack_id} to Rs {updated_pack['price_inr']} with {updated_pack['coins']}+{updated_pack['bonus_coins']} coins")

    # Verify existing order snapshot is strictly PRESERVED
    status, polled_old_order = make_req(f"{BASE_URL}/coin-packs/orders/{snap_order_id}", token=cust_token)
    assert status == 200
    assert float(polled_old_order['amount_inr']) == 60.00, "Old order snapshot price was modified!"
    assert polled_old_order['coins'] == 80, "Old order snapshot coins was modified!"
    assert polled_old_order['total_coins'] == 100
    print("[PASS] Previous order snapshot preserved original price (Rs 60.00) and coins (100).")

    # Verify new order uses the new price
    status, order_new = make_req(f"{BASE_URL}/coin-packs/orders", {
        'pack_code': pack_code
    }, token=cust_token)
    assert status == 201
    assert float(order_new['amount_inr']) == 75.00
    assert order_new['total_coins'] == 120
    print("[PASS] New order immediately reflects dynamic price (Rs 75.00) and coins (120).")

    # =========================================================================
    # Task 3: Payment Verification & Webhook Idempotency
    # =========================================================================
    print("\n[QA SUITE 3] Task 3: Payment Verification & Webhook Idempotency")
    wallet_before = make_req(f"{BASE_URL}/wallet", token=cust_token)[1]
    purchased_before = wallet_before['purchased_coins']
    earned_before = wallet_before['earned_coins']
    total_before = wallet_before['total_coins']

    # 3a. Invalid signature verification must fail (on separate order)
    status, bad_order = make_req(f"{BASE_URL}/coin-packs/orders", {
        'pack_code': pack_code
    }, token=cust_token)
    assert status == 201
    bad_order_id = bad_order['order_id']

    status, fail_verify = make_req(f"{BASE_URL}/coin-packs/orders/{bad_order_id}/verify", {
        'gateway_payment_id': 'pay_fake_123',
        'gateway_signature': 'tampered_signature_xyz'
    }, token=cust_token)
    assert status == 400, f"Expected 400 for bad signature, got {status}: {fail_verify}"
    wallet_after_fail = make_req(f"{BASE_URL}/wallet", token=cust_token)[1]
    assert wallet_after_fail['purchased_coins'] == purchased_before, "Failed verification credited coins!"
    print("[PASS] Tampered payment signature rejected with 400; wallet unchanged.")

    # 3b. Valid signature verification credits coins (80 purchased + 20 bonus = 100 total)
    fake_payment_id = f"pay_{uuid.uuid4().hex[:12]}"
    valid_sig = hmac.new(
        settings.PAYMENT_WEBHOOK_SECRET.encode('utf-8'),
        f"{snap_order_id}|{fake_payment_id}".encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    status, success_verify = make_req(f"{BASE_URL}/coin-packs/orders/{snap_order_id}/verify", {
        'gateway_payment_id': fake_payment_id,
        'gateway_signature': valid_sig
    }, token=cust_token)
    assert status == 200, f"Verification failed: {success_verify}"
    assert success_verify['coins_credited'] is True
    assert success_verify['coins_added'] == 100

    wallet_after_success = make_req(f"{BASE_URL}/wallet", token=cust_token)[1]
    assert wallet_after_success['purchased_coins'] == purchased_before + 80
    assert wallet_after_success['earned_coins'] == earned_before + 20
    assert wallet_after_success['total_coins'] == total_before + 100
    print(f"Payment verified. Wallet balance updated: purchased={wallet_after_success['purchased_coins']}, earned={wallet_after_success['earned_coins']}, total={wallet_after_success['total_coins']}.")

    # 3c. Duplicate verify call is idempotent
    status, dup_verify = make_req(f"{BASE_URL}/coin-packs/orders/{snap_order_id}/verify", {
        'gateway_payment_id': fake_payment_id,
        'gateway_signature': valid_sig
    }, token=cust_token)
    assert status == 200
    assert dup_verify['status'] == 'SUCCESS'
    wallet_after_dup = make_req(f"{BASE_URL}/wallet", token=cust_token)[1]
    assert wallet_after_dup['total_coins'] == wallet_after_success['total_coins'], "Duplicate verification double-credited coins!"
    print("[PASS] Duplicate verification is idempotent; no duplicate coins credited.")

    # =========================================================================
    # Task 4: Contact Reveal Privacy, Free Quotas & Priority Spending
    # =========================================================================
    print("\n[QA SUITE 4] Task 4: Contact Reveal Privacy & Coin Deductions")
    status, workers = make_req(f"{BASE_URL}/workers", token=cust_token)
    assert status == 200 and len(workers) >= 6, f"Need at least 6 workers in DB, found {len(workers)}"

    # Privacy Check
    for w in workers:
        assert 'phone_number' not in w['user'], f"Privacy violation: phone number exposed in worker list!"
    print("[PASS] Phone number privacy verified on public worker endpoints.")

    # Set baseline rate limit to 5 per minute to ensure clean testing
    make_req(f"{BASE_URL}/admin/configs", {'reveal_rate_limit_per_minute': 5}, token=admin_token, method='PUT')

    # Customer reveals worker 0 (Free contact #1)
    w0_id = workers[0]['id']
    status, r0 = make_req(f"{BASE_URL}/workers/{w0_id}/reveal", data={}, token=cust_token)
    assert status == 200
    assert r0['is_free_reveal'] is True
    assert r0['coins_deducted'] == 0
    assert r0['contact_phone'] is not None
    print(f"Free reveal #1: worker phone={r0['contact_phone']}, coins deducted=0, remaining free={r0['remaining_free_contacts']}")

    # Repeated reveal of same worker 0 is idempotent and free
    status, r0_repeat = make_req(f"{BASE_URL}/workers/{w0_id}/reveal", data={}, token=cust_token)
    assert status == 200
    assert r0_repeat['is_already_revealed'] is True
    assert r0_repeat['coins_deducted'] == 0
    print("[PASS] Repeated reveal is idempotent and free.")

    # Reveal workers 1, 2, 3, 4 (Exhausts remaining 4 free contacts)
    for i in range(1, 5):
        wi_id = workers[i]['id']
        status, r_i = make_req(f"{BASE_URL}/workers/{wi_id}/reveal", data={}, token=cust_token)
        assert status == 200
        assert r_i['is_free_reveal'] is True

    # Check contact status on 6th worker (worker 5): free quota must be exhausted!
    w5_id = workers[5]['id']
    status, cs5 = make_req(f"{BASE_URL}/workers/{w5_id}/contact-status", token=cust_token)
    assert status == 200
    assert cs5['free_contacts_remaining'] == 0
    assert cs5['coins_required'] == 10
    print(f"Free contacts exhausted. Coins required for 6th unlock: {cs5['coins_required']}")

    # 6th reveal exceeds reveal_rate_limit_per_minute (5 per minute): must return 429
    status, rate_limited = make_req(f"{BASE_URL}/workers/{w5_id}/reveal", data={}, token=cust_token)
    assert status == 429, f"Expected 429 Rate Limit for 6th reveal, got {status}: {rate_limited}"
    print("[PASS] Reveal rate limit per minute enforced (HTTP 429 Too Many Requests).")

    # Admin increases reveal_rate_limit_per_minute to 20 dynamically via PUT /admin/configs
    status, updated_cfg = make_req(f"{BASE_URL}/admin/configs", {
        'reveal_rate_limit_per_minute': 20
    }, token=admin_token, method='PUT')
    assert status == 200
    print("Admin increased reveal rate limit to 20/min via dynamic config.")

    # Retry 6th worker reveal: charges 10 coins. Earned coins spent before purchased!
    w_pre_reveal = make_req(f"{BASE_URL}/wallet", token=cust_token)[1]
    status, r5 = make_req(f"{BASE_URL}/workers/{w5_id}/reveal", data={}, token=cust_token)
    assert status == 200, f"Reveal failed after rate limit increase: {r5}"
    assert r5['is_free_reveal'] is False
    assert r5['coins_deducted'] == 10
    assert r5['contact_phone'] is not None

    w_post_reveal = make_req(f"{BASE_URL}/wallet", token=cust_token)[1]
    assert w_post_reveal['total_coins'] == w_pre_reveal['total_coins'] - 10
    # Confirm earned coins were spent first (earned should decrease by 10)
    assert w_post_reveal['earned_coins'] == w_pre_reveal['earned_coins'] - 10
    print(f"[PASS] 6th worker reveal deducted 10 coins. Earned coins spent first: {w_pre_reveal['earned_coins']} -> {w_post_reveal['earned_coins']}.")

    # Test Reveal Refund (Task 4) within refund window
    eng_id = r5['engagement_id']
    status, ref_res = make_req(f"{BASE_URL}/engagements/{eng_id}/refund?reason=Unreachable%20worker", method='POST', token=cust_token)
    assert status == 200, f"Refund failed: {ref_res}"
    assert ref_res['refund_status'] == "REFUNDED"
    assert ref_res['coins_refunded'] == 10

    w_post_refund = make_req(f"{BASE_URL}/wallet", token=cust_token)[1]
    assert w_post_refund['total_coins'] == w_pre_reveal['total_coins']
    print(f"[PASS] Contact refund granted within window. Balance restored: {w_post_refund['total_coins']}.")

    # Duplicate refund attempt must be rejected (HTTP 400)
    status, dup_ref = make_req(f"{BASE_URL}/engagements/{eng_id}/refund", method='POST', token=cust_token)
    assert status == 400
    print("[PASS] Duplicate refund rejected with HTTP 400.")

    # =========================================================================
    # Task 5: Admin Wallet & Transaction Management
    # =========================================================================
    print("\n[QA SUITE 5] Task 5: Admin Wallet & Audited Adjustments")
    # Fetch admin wallets list
    status, admin_wallets = make_req(f"{BASE_URL}/admin/wallets?page=1&limit=10", token=admin_token)
    assert status == 200
    assert admin_wallets['total'] >= 1
    target_wallet_id = admin_wallets['items'][0]['id']

    # Admin inspects wallet details
    status, wallet_details = make_req(f"{BASE_URL}/admin/wallets/{target_wallet_id}/details", token=admin_token)
    assert status == 200
    assert 'wallet' in wallet_details
    assert 'transactions' in wallet_details
    assert 'orders' in wallet_details
    print(f"Inspected Wallet #{target_wallet_id}: purchased={wallet_details['wallet']['purchased_coins']}, earned={wallet_details['wallet']['earned_coins']}")

    # Manual Coin Adjustment - Negative Case: Missing Reason
    status, adj_fail = make_req(f"{BASE_URL}/admin/wallets/{target_wallet_id}/adjust-coins", {
        'amount': 25,
        'action': 'credit',
        'coin_type': 'purchased',
        'reason': ''
    }, token=admin_token)
    assert status == 422 or status == 400, f"Expected validation failure for empty reason, got {status}"
    print("[PASS] Empty adjustment reason rejected.")

    # Manual Coin Adjustment - Positive Case: Valid Credit with Audit Reason
    wb = wallet_details['wallet']['purchased_coins']
    status, adj_success = make_req(f"{BASE_URL}/admin/wallets/{target_wallet_id}/adjust-coins", {
        'amount': 25,
        'action': 'credit',
        'coin_type': 'purchased',
        'reason': 'QA Goodwill Promotional Credit'
    }, token=admin_token)
    assert status == 200, f"Coin adjust failed: {adj_success}"
    assert adj_success['purchased_coins'] == wb + 25
    print(f"[PASS] Admin manual coin credit succeeded. Wallet balance: {wb} -> {adj_success['purchased_coins']}")

    # Manual Coin Adjustment - Debit
    status, adj_debit = make_req(f"{BASE_URL}/admin/wallets/{target_wallet_id}/adjust-coins", {
        'amount': 10,
        'action': 'debit',
        'coin_type': 'purchased',
        'reason': 'QA Test Reversal'
    }, token=admin_token)
    assert status == 200
    assert adj_debit['purchased_coins'] == wb + 25 - 10
    print(f"[PASS] Admin manual coin debit succeeded. Balance: {adj_debit['purchased_coins']}")

    # =========================================================================
    # Task 6: Admin Business Rules Configuration
    # =========================================================================
    print("\n[QA SUITE 6] Task 6: Admin Business Rules Configuration")
    status, orig_configs = make_req(f"{BASE_URL}/admin/configs", token=admin_token)
    assert status == 200
    print(f"Fetched {len(orig_configs)} business rules from DB.")

    # Admin updates a business rule dynamically
    status, updated_cfg = make_req(f"{BASE_URL}/admin/configs", {
        'refund_cap_per_month': 5,
        'feedback_photo_reward_coins': 8,
        'daily_reward_cap_coins': 200
    }, token=admin_token, method='PUT')
    assert status == 200, f"Update configs failed: {updated_cfg}"
    
    # Verify live update
    status, cfg_check = make_req(f"{BASE_URL}/config/coins")
    assert status == 200
    assert cfg_check['feedback_photo_reward_coins'] == 8
    assert cfg_check['refund_cap_per_month'] == 5
    assert cfg_check['daily_reward_cap_coins'] == 200
    print("[PASS] Business rules updated dynamically and exposed to clients without app release.")

    # =========================================================================
    # Task 7: Feedback Submission, Rewards & Photo Moderation
    # =========================================================================
    print("\n[QA SUITE 7] Task 7: Feedback Submission, Rewards & Moderation")
    w_target_id = workers[0]['id']
    cust_wallet_pre_fb = make_req(f"{BASE_URL}/wallet", token=cust_token)[1]
    earned_pre_fb = cust_wallet_pre_fb['earned_coins']

    test_photo_url = f"https://example.com/photos/work_proof_{uuid.uuid4().hex[:8]}.jpg"
    status, fb_res = make_req(f"{BASE_URL}/customer/feedback", {
        'worker_id': w_target_id,
        'rating': 5,
        'comments': 'Superb masonry and repair work! Very timely, polite, and professional service.',
        'photo_urls': [test_photo_url]
    }, token=cust_token)
    assert status == 201, f"Feedback submit failed: {fb_res}"
    assert fb_res['reward_granted'] is True
    assert fb_res['reward_coins'] > 0
    feedback_id = fb_res['id']
    print(f"Feedback submitted #{feedback_id}. Awarded {fb_res['reward_coins']} initial review coins.")

    # Verify wallet received earned coins for rating + remark
    cust_wallet_post_fb = make_req(f"{BASE_URL}/wallet", token=cust_token)[1]
    assert cust_wallet_post_fb['earned_coins'] == earned_pre_fb + fb_res['reward_coins']
    print(f"Earned coins updated: {earned_pre_fb} -> {cust_wallet_post_fb['earned_coins']}")

    # Verify attached photo is PENDING admin moderation
    status, photo_list = make_req(f"{BASE_URL}/admin/feedback-photos?status=PENDING", token=admin_token)
    assert status == 200
    matched_photos = [p for p in photo_list['items'] if p['photo_url'] == test_photo_url]
    assert len(matched_photos) == 1, "Uploaded photo not found in pending queue!"
    pending_photo = matched_photos[0]
    assert pending_photo['status'] == 'PENDING'
    assert pending_photo['reward_granted'] is False
    photo_id = pending_photo['id']
    print(f"Photo in pending queue: #{photo_id} (status=PENDING, reward_granted=False)")

    # Admin approves photo -> credits photo reward once
    status, approve_res = make_req(f"{BASE_URL}/admin/feedback-photos/{photo_id}/approve", token=admin_token, method='POST')
    assert status == 200, f"Photo approve failed: {approve_res}"
    assert approve_res['status'] == 'APPROVED'
    assert approve_res['reward_coins'] == 8 # As updated in Task 6!

    # Verify customer wallet received the 8 photo coins
    cust_wallet_post_photo = make_req(f"{BASE_URL}/wallet", token=cust_token)[1]
    assert cust_wallet_post_photo['earned_coins'] == cust_wallet_post_fb['earned_coins'] + 8
    print(f"[PASS] Photo approved! Awarded 8 coins to customer (earned balance: {cust_wallet_post_photo['earned_coins']}).")

    # Duplicate approve call is idempotent
    status, dup_approve = make_req(f"{BASE_URL}/admin/feedback-photos/{photo_id}/approve", token=admin_token, method='POST')
    assert status == 200
    assert dup_approve['status'] == 'APPROVED'
    cust_wallet_post_dup = make_req(f"{BASE_URL}/wallet", token=cust_token)[1]
    assert cust_wallet_post_dup['earned_coins'] == cust_wallet_post_photo['earned_coins'], "Duplicate photo approval double-credited coins!"
    print("[PASS] Duplicate photo approval is idempotent.")

    # Review Moderation: Hiding review
    status, hide_res = make_req(f"{BASE_URL}/admin/feedbacks/{feedback_id}/toggle-hide", {
        'is_hidden': True
    }, token=admin_token, method='PATCH')
    assert status == 200
    assert hide_res['is_hidden'] is True

    # Verify review is omitted from public worker reviews
    status, pub_reviews = make_req(f"{BASE_URL}/workers/{w_target_id}/reviews")
    assert status == 200
    assert not any(r['id'] == feedback_id for r in pub_reviews['items']), "Hidden review appeared in public listing!"

    # CRITICAL: Verify customer's earned coin rewards are NOT reversed when review is hidden
    cust_wallet_after_hide = make_req(f"{BASE_URL}/wallet", token=cust_token)[1]
    assert cust_wallet_after_hide['earned_coins'] == cust_wallet_post_photo['earned_coins'], "Review hiding reversed customer coins!"
    print("[PASS] Review hidden from public listing; customer earned coins preserved.")

    # Unhide review
    status, unhide_res = make_req(f"{BASE_URL}/admin/feedbacks/{feedback_id}/toggle-hide", {
        'is_hidden': False
    }, token=admin_token, method='PATCH')
    assert status == 200
    assert unhide_res['is_hidden'] is False
    print("[PASS] Review restored to public listing.")

    # =========================================================================
    # Task 8: Security & Automated Jobs
    # =========================================================================
    print("\n[QA SUITE 8] Task 8: Security & Automated Jobs")
    # Non-admin access to admin endpoint must return 403 Forbidden
    status, forbidden_res = make_req(f"{BASE_URL}/admin/configs", token=cust_token)
    assert status == 403, f"Expected 403 for non-admin on /admin/configs, got {status}"
    print("[PASS] Role-based access control verified (customer denied admin access).")

    # Run reconcile pending orders job
    status, job1 = make_req(f"{BASE_URL}/admin/jobs/reconcile-pending-orders?hours_threshold=1", token=admin_token, method='POST')
    assert status == 200
    print(f"[PASS] Reconcile orders job executed: {job1['message']}")

    # Run expire earned coins job
    status, job2 = make_req(f"{BASE_URL}/admin/jobs/expire-earned-coins", token=admin_token, method='POST')
    assert status == 200
    print(f"[PASS] Expire earned coins job executed: {job2['message']}")

    print("\n" + "=" * 70)
    print(" ALL 9 QA TEST SUITES COMPLETED AND PASSED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    run_all_qa_tests()
