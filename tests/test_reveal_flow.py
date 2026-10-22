import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import urllib.request
import json
import uuid
from app.models.wallet import Wallet

def make_req(url, data=None, token=None, method=None, headers=None):
    hdrs = headers or {}
    if token:
        hdrs['Authorization'] = f'Bearer {token}'
    if data is not None:
        hdrs['Content-Type'] = 'application/json'
        body = json.dumps(data).encode()
    else:
        body = None
    req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
    try:
        resp = urllib.request.urlopen(req)
        return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        try:
            parsed = json.loads(err_body)
        except Exception:
            parsed = err_body
        return e.code, parsed

def run_tests():
    print("=== Testing Worker Reveal & Contact Status APIs ===")

    # 1. Register fresh customer
    test_phone = f"+9177777{str(uuid.uuid4().int)[:5]}"
    status, reg = make_req('http://127.0.0.1:8000/api/v1/auth/register', {
        'phone_number': test_phone,
        'full_name': 'Test Reveal Customer',
        'language_preference': 'English',
        'role': 'customer'
    })
    assert status == 201, f"Registration failed: {reg}"

    status, login_res = make_req('http://127.0.0.1:8000/api/v1/auth/verify-otp', {
        'phone_number': test_phone,
        'otp': '123456'
    })
    assert status == 200, f"Login failed: {login_res}"
    token = login_res['access_token']
    print(f"Customer registered: {test_phone}")

    # 2. Check initial wallet
    status, wallet = make_req('http://127.0.0.1:8000/wallet', token=token)
    print(f"Initial wallet coins: {wallet['total_coins']} (purchased={wallet['purchased_coins']}, earned={wallet['earned_coins']})")
    assert wallet['total_coins'] == 50

    # 3. Get list of available workers
    status, workers = make_req('http://127.0.0.1:8000/workers', token=token)
    assert status == 200
    print(f"Found {len(workers)} workers.")
    assert len(workers) >= 4, "Expected at least 4 workers in database."

    # Verify privacy: no phone numbers in worker listing or detail
    for w in workers:
        assert 'phone_number' not in w['user'], f"Privacy violation: phone_number found in worker listing: {w['user']}"

    status, detail = make_req(f"http://127.0.0.1:8000/workers/{workers[0]['id']}", token=token)
    assert 'phone_number' not in detail['user'], f"Privacy violation: phone_number found in worker detail: {detail['user']}"
    print("PRIVACY PASS: Worker list and detail APIs do NOT expose phone numbers.")

    # 4. Test contact-status before reveal
    w0_id = workers[0]['id']
    status, cs0 = make_req(f"http://127.0.0.1:8000/workers/{w0_id}/contact-status", token=token)
    assert status == 200
    assert cs0['is_revealed'] is False
    assert cs0['contact_phone'] is None
    assert cs0['free_contacts_total'] == 5
    assert cs0['free_contacts_used'] == 0
    assert cs0['free_contacts_remaining'] == 5
    assert cs0['coins_required'] == 0
    assert cs0['can_reveal'] is True
    print("STATUS PASS: Contact status before reveal correctly shows 5 free remaining and coins_required=0.")

    # 5. Reveal worker 0 (Free contact #1)
    status, r0 = make_req(f"http://127.0.0.1:8000/workers/{w0_id}/reveal", data={}, token=token)
    assert status == 200, f"Reveal failed: {r0}"
    assert r0['is_already_revealed'] is False
    assert r0['is_free_reveal'] is True
    assert r0['coins_deducted'] == 0
    assert r0['remaining_free_contacts'] == 4
    assert r0['contact_phone'] is not None
    print(f"REVEAL 1 PASS: Free reveal #1 succeeded (phone={r0['contact_phone']}, coins_deducted=0, remaining=4).")

    # 6. Test repeated reveal on worker 0 (Idempotency - must NOT charge again)
    status, r0_repeat = make_req(f"http://127.0.0.1:8000/workers/{w0_id}/reveal", data={}, token=token)
    assert status == 200
    assert r0_repeat['is_already_revealed'] is True
    assert r0_repeat['coins_deducted'] == 0
    assert r0_repeat['remaining_free_contacts'] == 4
    assert r0_repeat['contact_phone'] == r0['contact_phone']
    print("IDEMPOTENCY PASS: Repeated reveal did not charge coins and returned the same phone number.")

    # 7. Test contact status on worker 0 after reveal
    status, cs0_after = make_req(f"http://127.0.0.1:8000/workers/{w0_id}/contact-status", token=token)
    assert status == 200
    assert cs0_after['is_revealed'] is True
    assert cs0_after['contact_phone'] == r0['contact_phone']
    assert cs0_after['coins_required'] == 0
    print("STATUS PASS: Contact status after reveal shows is_revealed=True and returns contact phone.")

    # We need 6 unique workers to test the transition from 5 free contacts to 10 coins deduction.
    # Let's check how many workers we have or create additional test workers if needed.
    from app.core.database import SessionLocal
    from app.models.user import User
    from app.models.worker import Worker, AvailabilityStatus, KycStatus
    from decimal import Decimal

    db = SessionLocal()
    existing_workers = db.query(Worker).filter(Worker.is_deleted == False).all()
    print(f"Total existing workers in DB: {len(existing_workers)}")
    while len(existing_workers) < 6:
        idx = len(existing_workers) + 1
        new_u = User(
            phone_number=f"+9198765{idx:05d}",
            full_name=f"Auto Worker {idx}",
            language_preference="English",
            is_verified=True
        )
        db.add(new_u)
        db.commit()
        db.refresh(new_u)

        new_w = Worker(
            user_id=new_u.id,
            category="Plumber",
            experience_years=3,
            pricing_per_hour=Decimal("150.00"),
            bio=f"Test Artisan {idx}",
            kyc_status=KycStatus.approved,
            availability_status=AvailabilityStatus.available_now
        )
        db.add(new_w)
        db.commit()
        db.refresh(new_w)
        existing_workers.append(new_w)
    db.close()

    status, all_workers = make_req('http://127.0.0.1:8000/workers', token=token)
    w_list = all_workers[:6]

    # Reveal workers 1, 2, 3, 4 (Free contacts #2, #3, #4, #5)
    for i in range(1, 5):
        w_curr = w_list[i]
        status, rev = make_req(f"http://127.0.0.1:8000/workers/{w_curr['id']}/reveal", data={}, token=token)
        assert status == 200
        assert rev['is_free_reveal'] is True
        assert rev['coins_deducted'] == 0
        expected_remaining = 5 - (i + 1)
        assert rev['remaining_free_contacts'] == expected_remaining
        print(f"REVEAL {i+1} PASS: Free reveal #{i+1} succeeded (coins_deducted=0, remaining={expected_remaining}).")

    # Check contact status on worker 5 (6th worker) BEFORE reveal
    # All 5 free contacts used, so coins_required must be 10!
    w5_id = w_list[5]['id']
    status, cs5 = make_req(f"http://127.0.0.1:8000/workers/{w5_id}/contact-status", token=token)
    assert status == 200
    assert cs5['is_revealed'] is False
    assert cs5['free_contacts_used'] == 5
    assert cs5['free_contacts_remaining'] == 0
    assert cs5['coins_required'] == 10
    assert cs5['can_reveal'] is True  # User has 20 coins
    print("STATUS PASS: 6th worker contact status shows free_contacts_remaining=0, coins_required=10.")

    # Reveal 6th worker (should deduct 10 coins!)
    status, wallet_before = make_req('http://127.0.0.1:8000/wallet', token=token)
    coins_before = wallet_before['total_coins']

    status, r5 = make_req(f"http://127.0.0.1:8000/workers/{w5_id}/reveal", data={}, token=token)
    assert status == 200
    assert r5['is_free_reveal'] is False
    assert r5['coins_deducted'] == 10
    assert r5['remaining_free_contacts'] == 0
    assert r5['contact_phone'] is not None

    status, wallet_after = make_req('http://127.0.0.1:8000/wallet', token=token)
    coins_after = wallet_after['total_coins']
    assert coins_after == coins_before - 10, f"Expected {coins_before - 10} coins, got {coins_after}"
    print(f"CHARGED REVEAL PASS: 6th worker reveal successfully deducted 10 coins (before={coins_before}, after={coins_after}).")

    # Repeated reveal on 6th worker (must NOT charge again)
    status, r5_repeat = make_req(f"http://127.0.0.1:8000/workers/{w5_id}/reveal", data={}, token=token)
    assert status == 200
    assert r5_repeat['is_already_revealed'] is True
    assert r5_repeat['coins_deducted'] == 0
    status, wallet_repeat = make_req('http://127.0.0.1:8000/wallet', token=token)
    assert wallet_repeat['total_coins'] == coins_after
    print("REPEAT CHARGED REVEAL PASS: Repeated reveal on paid contact did not charge again.")

    # Test Refund API on 6th worker's reveal
    eng_id = r5['engagement_id']
    status, ref = make_req(f"http://127.0.0.1:8000/engagements/{eng_id}/refund?reason=Unreachable", method='POST', token=token)
    assert status == 200, f"Refund failed: {ref}"
    assert ref['refund_status'] == "REFUNDED"
    assert ref['coins_refunded'] == 10

    status, wallet_refunded = make_req('http://127.0.0.1:8000/wallet', token=token)
    assert wallet_refunded['total_coins'] == coins_before, f"Expected {coins_before} coins after refund, got {wallet_refunded['total_coins']}"
    print(f"REFUND PASS: Successfully refunded 10 coins back to wallet (balance={wallet_refunded['total_coins']}).")

    # Test repeated refund (must fail with 400)
    status, ref_err = make_req(f"http://127.0.0.1:8000/engagements/{eng_id}/refund", method='POST', token=token)
    assert status == 400, f"Expected 400 for duplicate refund, got {status}: {ref_err}"
    print("REFUND IDEMPOTENCY PASS: Duplicate refund rejected with HTTP 400.")

    # 8. Test Insufficient Balance Failure on 6th reveal when wallet has 0 coins
    phone_zero = f"+9177778{str(uuid.uuid4().int)[:5]}"
    make_req('http://127.0.0.1:8000/api/v1/auth/register', {
        'phone_number': phone_zero,
        'full_name': 'Zero Coin Customer',
        'role': 'customer'
    })
    _, login_zero = make_req('http://127.0.0.1:8000/api/v1/auth/verify-otp', {'phone_number': phone_zero, 'otp': '123456'})
    token_zero = login_zero['access_token']

    # Drain wallet coins
    db = SessionLocal()
    u_zero = db.query(User).filter(User.phone_number == phone_zero).first()
    w_zero = db.query(Wallet).filter(Wallet.user_id == u_zero.id).first()
    w_zero.earned_coins = 0
    w_zero.purchased_coins = 0
    db.commit()
    db.close()

    # Exhaust 5 free reveals
    for i in range(5):
        wid = w_list[i]['id']
        c_code, c_res = make_req(f"http://127.0.0.1:8000/workers/{wid}/reveal", data={}, token=token_zero)
        assert c_code == 200

    # 6th reveal should fail with 400
    wid5 = w_list[5]['id']
    fail_code, fail_res = make_req(f"http://127.0.0.1:8000/workers/{wid5}/reveal", data={}, token=token_zero)
    assert fail_code == 400, f"Expected 400 for insufficient coins, got {fail_code}: {fail_res}"
    assert "Insufficient" in fail_res['detail']
    print(f"INSUFFICIENT BALANCE PASS: 6th reveal correctly rejected with 400: '{fail_res['detail']}'")

    print("\nALL WORKER REVEAL & CONTACT-STATUS TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
