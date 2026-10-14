import sys
from datetime import datetime
from app.core.database import SessionLocal
from app.models.legal_document import LegalDocument

privacy_policy_content = """<h2>Privacy Policy</h2>
<p><strong>Effective Date:</strong> October 12, 2026 | <strong>Last Updated:</strong> October 12, 2026</p>
<p>Welcome to <strong>Hunar Mitra</strong> ("Platform", "we", "us", or "our"). We are dedicated to empowering blue-collar artisans, skilled workers (electricians, plumbers, carpenters, beauticians, mechanics, painters, and general technicians), civil contractors, and service consumers across India. This Privacy Policy outlines our transparent practices concerning the collection, storage, verification, use, and disclosure of personal, professional, and transactional information when you access or use the Hunar Mitra mobile applications, web platforms, and associated services.</p>

<h3>1. Information We Collect</h3>
<p>To deliver a verified, reliable, and secure hyper-local marketplace, we collect information across three user categories (Customers, Workers, and Contractors):</p>
<ul>
  <li><strong>Identity & Profile Information:</strong> Full name, phone number, gender, date of birth, profile photograph, and language preferences (e.g. Hindi, English, regional dialects).</li>
  <li><strong>KYC & Regulatory Verification Documents:</strong> For Workers (Artisans) and Contractors, we collect Government-issued identity proofs (Aadhaar number, PAN card, Voter ID, Driving License) and trade certificates to conduct mandatory background checks and skill verification.</li>
  <li><strong>Location & Geodata:</strong> Real-time and approximate GPS coordinates, locality, pincode, and complete service addresses. Geolocation is used solely to match customers with nearest available service professionals and optimize travel radius.</li>
  <li><strong>Booking & Service Transactions:</strong> Service category selected, appointment schedule, booking status history, completion confirmations, OTPs, and customer reviews/ratings.</li>
  <li><strong>Wallet & Financial Records:</strong> Wallet recharge history, payment gateway transaction IDs, earned commission deductions, cash settlement confirmations, and bank account/UPI details for worker withdrawal settlements. <em>Note: Sensitive debit/credit card credentials are processed directly via RBI-authorized PCI-DSS compliant payment aggregators and are never stored on our servers.</em></li>
  <li><strong>Device & Telemetry Data:</strong> IP address, device model, operating system version, push notification tokens, and application crash diagnostics.</li>
</ul>

<h3>2. How We Use Your Information</h3>
<p>The information collected is strictly utilized for core operational, safety, and marketplace enablement purposes:</p>
<ul>
  <li><strong>Service Facilitation & Dispatch:</strong> Connecting customers with verified local workers and contractors based on skills, geographical proximity, and real-time availability.</li>
  <li><strong>Trust, Safety & KYC Verification:</strong> Verifying the authenticity of artisans and trade contractors before granting platform work permissions, thereby safeguarding household clients and project sites.</li>
  <li><strong>Secure Two-Factor Authentication & Verification:</strong> Issuing one-time passwords (OTP) for phone number logins, account security, and service commencement/completion verifications.</li>
  <li><strong>Integrated Digital Wallet Management:</strong> Facilitating platform fee collections, wallet top-ups, referral bonuses, and transparent artisan payout settlements.</li>
  <li><strong>Dispute Resolution & Customer Support:</strong> Addressing call-outs, work quality complaints, cancellation appeals, and emergency on-site assistance.</li>
  <li><strong>Service Improvement & Fraud Prevention:</strong> Detecting fraudulent registrations, spam bookings, fee circumvention, and enhancing localized search algorithms.</li>
</ul>

<h3>3. Data Sharing and Third-Party Disclosures</h3>
<p>We respect your privacy and never sell or rent your personal data to third-party advertisers. Data sharing is limited to legitimate marketplace operations:</p>
<ul>
  <li><strong>Between Marketplace Participants:</strong> When a booking is initiated, relevant details (e.g. customer name, service address, contact number) are shared with the assigned worker/contractor. Similarly, the worker's verified name, photo, skill trade, and average customer rating are shared with the customer.</li>
  <li><strong>Payment Gateways & Banking Partners:</strong> Encrypted transaction values and tokens are processed by RBI-licensed payment processors to execute wallet and payout transactions.</li>
  <li><strong>SMS & Notification Infrastructure:</strong> Cloud communication providers to transmit critical transactional SMS, OTPs, and real-time booking updates.</li>
  <li><strong>Legal & Regulatory Mandates:</strong> Disclosure to law enforcement or statutory authorities only when officially requested under prevailing Indian cyber laws (Information Technology Act, 2000 and Digital Personal Data Protection Act, 2023).</li>
</ul>

<h3>4. Data Security & Storage Standards</h3>
<p>We implement robust organizational, technical, and physical security measures:</p>
<ul>
  <li>All data transmissions between client devices and our cloud backend are encrypted using Transport Layer Security (TLS 1.3 / SSL).</li>
  <li>User authentication tokens and sensitive identification credentials are encrypted using industry-standard hashing algorithms (bcrypt/Argon2).</li>
  <li>Access to internal administration dashboards and user records is restricted through strict Role-Based Access Controls (RBAC), multi-factor verification, and audit logs.</li>
</ul>

<h3>5. User Rights & Data Retention</h3>
<p>You have full ownership and discretion over your personal information on Hunar Mitra:</p>
<ul>
  <li><strong>Profile Review & Updates:</strong> You can review, update, or correct your personal information directly through your platform profile settings.</li>
  <li><strong>Consent Revocation & Account Deletion:</strong> You may request the deletion of your account and purging of personal data via the app or by writing to our support team, subject to the retention of statutory audit and ledger records as required by Indian financial regulations.</li>
  <li><strong>Retention Timelines:</strong> We retain account records as long as your profile remains active. KYC records are retained in compliance with applicable regulatory periods.</li>
</ul>

<h3>6. Grievance Officer & Contact Information</h3>
<p>In accordance with the Information Technology Act, 2000 and applicable IT (Intermediary Guidelines and Digital Media Ethics Code) Rules, the contact details of the Grievance Officer for Hunar Mitra are provided below:</p>
<ul>
  <li><strong>Platform Operator:</strong> Hunar Mitra Services Private Limited</li>
  <li><strong>Designation:</strong> Grievance Redressal & Compliance Officer</li>
  <li><strong>Email:</strong> support@hunarmitra.com / compliance@hunarmitra.com</li>
  <li><strong>Operating Address:</strong> Lucknow, Uttar Pradesh, India</li>
  <li><strong>Response Window:</strong> All valid grievances will be acknowledged within 24 hours and addressed within 15 business days.</li>
</ul>"""

terms_and_conditions_content = """<h2>Terms and Conditions</h2>
<p><strong>Effective Date:</strong> October 12, 2026 | <strong>Last Updated:</strong> October 12, 2026</p>
<p>Please read these Terms and Conditions ("Terms", "Agreement") carefully before using the <strong>Hunar Mitra</strong> platform, including our mobile applications, customer portals, worker apps, and website (collectively, the "Platform"). This Agreement constitutes a legally binding contract between you ("User", "Customer", "Worker", "Artisan", or "Contractor") and <strong>Hunar Mitra Services Private Limited</strong> ("Hunar Mitra", "Company", "we", "us", or "our").</p>

<h3>1. Acceptance of Terms</h3>
<p>By registering on, downloading, accessing, or using the Platform, you acknowledge that you have read, understood, and agreed to be bound by these Terms and our Privacy Policy. If you do not accept these Terms, you must discontinue platform access and uninstall our applications immediately.</p>

<h3>2. Platform Scope and Intermediary Role</h3>
<p>Hunar Mitra operates an interactive digital marketplace and technology intermediary platform under Section 79 of the Information Technology Act, 2000:</p>
<ul>
  <li><strong>Connecting Bridge:</strong> The Platform enables service consumers ("Customers") to discover, connect with, and book independent skilled artisans and trade professionals ("Workers") and commercial service vendors ("Contractors").</li>
  <li><strong>Independent Contractor Status:</strong> Workers and Contractors are independent service providers and are NOT employees, agents, or partners of Hunar Mitra. Hunar Mitra does not control their working hours, work methods, or independent trade techniques.</li>
  <li><strong>Intermediary Warranty Disclaimer:</strong> While Hunar Mitra enforces rigorous KYC verification and customer feedback mechanisms, the final quality of physical labor and material installations performed on-site remains the responsibility of the contracted service provider.</li>
</ul>

<h3>3. User Accounts, Registration & Verification</h3>
<p>To access marketplace features, all participants must register with a valid phone number and maintain accurate account credentials:</p>
<ul>
  <li><strong>Eligibility:</strong> Users must be at least 18 years of age and legally competent to enter into enforceable contracts under Indian law.</li>
  <li><strong>Mandatory KYC for Workers & Contractors:</strong> Skilled workers and contractors must submit genuine government identification (Aadhaar, PAN, Voter ID), contact details, and trade qualifications before their profiles are approved and visible for public bookings.</li>
  <li><strong>Account Security:</strong> You are responsible for safeguarding your login OTPs and account activity. Any unauthorized access must be reported to Hunar Mitra support immediately.</li>
  <li><strong>Single Account Policy:</strong> Duplicate, deceptive, or proxy accounts created to manipulate ratings or bypass bans are strictly prohibited.</li>
</ul>

<h3>4. Service Bookings, Work Execution & OTP Verification</h3>
<p>The booking lifecycle on Hunar Mitra operates according to strict milestone protocols:</p>
<ul>
  <li><strong>Booking Request & Acceptance:</strong> Customers submit service requests detailing the work scope, address, and preferred time slot. Workers or Contractors may accept or decline based on availability.</li>
  <li><strong>Service Verification (Job Start & Completion OTP):</strong> To eliminate dispute and ensure physical service verification, jobs must be confirmed via platform-generated secure OTPs shared between Customer and Worker at the job premises.</li>
  <li><strong>On-Site Safety & Conduct:</strong> Both Customers and Workers agree to treat each other with dignity and mutual respect. Safe, non-hazardous working conditions must be provided at customer premises. Any misconduct, intoxication, harassment, or verbal abuse warrants immediate police reporting and permanent platform blacklisting.</li>
</ul>

<h3>5. Pricing, Payments, Wallet & Settlements</h3>
<p>Hunar Mitra provides a transparent fee framework to sustain marketplace infrastructure:</p>
<ul>
  <li><strong>Base Rates & Estimates:</strong> Service categories display standardized base inspection charges or hourly/work rates. Significant material costs or major structural overhauls must be explicitly mutually agreed before commencing work.</li>
  <li><strong>Hunar Mitra Digital Wallet:</strong> Customers and Workers utilize integrated digital wallets to facilitate smooth transactions, security hold deductions, and convenient top-ups.</li>
  <li><strong>Platform Commission:</strong> Hunar Mitra charges an nominal platform convenience fee/commission on completed jobs from workers or contractors to support software maintenance, verified customer generation, and dispute resolution.</li>
  <li><strong>Direct Cash Settlements:</strong> In offline cash settlements, customers pay the agreed service fee directly to the worker upon job completion OTP verification. The corresponding platform fee is settled via the worker's wallet balance.</li>
</ul>

<h3>6. Cancellation and Refund Policy</h3>
<p>We maintain equitable cancellation policies for all marketplace stakeholders:</p>
<ul>
  <li><strong>Customer Cancellations:</strong> Free cancellation is permitted before a worker has departed or within a specified grace window (typically 15 minutes from booking confirmation). Late cancellations after worker arrival may incur a standard nominal visit compensation fee.</li>
  <li><strong>Worker Cancellations:</strong> Frequent unexcused cancellations or no-shows by workers result in reduced profile ranking, temporary dispatch cooldowns, or permanent account deactivation.</li>
  <li><strong>Refunds:</strong> Eligible digital wallet refunds for cancelled or disputed prepaid bookings are processed back to the source payment method or credited to the platform wallet within 5-7 working days.</li>
</ul>

<h3>7. Prohibited Conduct & Account Termination</h3>
<p>Users agree NOT to engage in any of the following prohibited behaviors:</p>
<ul>
  <li>Off-platform collusion to deliberately circumvent platform safety protections or commission structures.</li>
  <li>Submission of fraudulent, forged, or unverified identification credentials during registration.</li>
  <li>Threatening, abusive, discriminatory, or unlawful behavior towards service workers, contractors, or customers.</li>
  <li>Attempting to reverse-engineer, scrape, inject malicious code, or compromise Platform API servers.</li>
  <li>Hunar Mitra reserves the unilateral right to suspend, terminate, or blacklist any user account found violating these conditions.</li>
</ul>

<h3>8. Limitation of Liability</h3>
<p>To the maximum extent permitted by applicable Indian law:</p>
<ul>
  <li>Hunar Mitra functions solely as a technology facilitator and shall not be held liable for indirect, incidental, punitive, or consequential damages resulting from independent on-site craftsmanship.</li>
  <li>Our cumulative aggregate liability for direct claims arising out of any booking shall not exceed the total platform fee collected by Hunar Mitra for that specific service transaction.</li>
</ul>

<h3>9. Governing Law and Dispute Jurisdiction</h3>
<p>These Terms shall be governed by, construed, and enforced exclusively in accordance with the laws of the Republic of India. Any legal dispute, arbitration claim, or proceeding arising out of or in connection with these Terms shall be subject to the exclusive jurisdiction of the competent courts in Lucknow, Uttar Pradesh, India.</p>

<h3>10. Platform Amendments & Notices</h3>
<p>Hunar Mitra may revise and update these Terms periodically to reflect legislative updates or new app capabilities. Updated Terms will be published on our public website with an updated Effective Date. Continued use of the Platform after such updates constitutes explicit acceptance of the revised Terms.</p>

<h3>11. Contact & Customer Support</h3>
<p>If you have any questions, clarifications, or feedback concerning these Terms and Conditions, please reach out to us:</p>
<ul>
  <li><strong>Entity:</strong> Hunar Mitra Services Private Limited</li>
  <li><strong>Support Helpdesk:</strong> support@hunarmitra.com</li>
  <li><strong>Website:</strong> https://hunarmitra.com</li>
  <li><strong>Location:</strong> Lucknow, Uttar Pradesh, India</li>
</ul>"""

def update_docs():
    db = SessionLocal()
    try:
        # Update Privacy Policy
        pp = db.query(LegalDocument).filter(LegalDocument.slug == "privacy-policy", LegalDocument.is_deleted == False).first()
        if pp:
            pp.title = "Privacy Policy"
            pp.content = privacy_policy_content
            pp.updated_at = datetime.utcnow()
            print(f"Updated Privacy Policy (Length: {len(pp.content)} chars)")
        else:
            pp = LegalDocument(title="Privacy Policy", slug="privacy-policy", content=privacy_policy_content)
            db.add(pp)
            print("Created Privacy Policy")

        # Update Terms and Conditions
        tc = db.query(LegalDocument).filter(LegalDocument.slug == "terms-and-conditions", LegalDocument.is_deleted == False).first()
        if tc:
            tc.title = "Terms and Conditions"
            tc.content = terms_and_conditions_content
            tc.updated_at = datetime.utcnow()
            print(f"Updated Terms and Conditions (Length: {len(tc.content)} chars)")
        else:
            tc = LegalDocument(title="Terms and Conditions", slug="terms-and-conditions", content=terms_and_conditions_content)
            db.add(tc)
            print("Created Terms and Conditions")

        db.commit()
        print("Successfully updated both legal documents in the database!")
    except Exception as e:
        db.rollback()
        print(f"Error updating legal documents: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    update_docs()
