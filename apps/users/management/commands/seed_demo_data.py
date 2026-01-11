"""
Management command to seed demo data (users, jobs, theme, banners).
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.contractors.models import ContractorProfile
from apps.core.models import Banner, Theme
from apps.jobs.models import Job
from apps.services.models import Service
from apps.users.models import User
from apps.workers.models import WorkerProfile


class Command(BaseCommand):
    help = "Seed demo data for development (users, jobs, theme, banners)"

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding demo data...")

        # 1. Create Demo Users
        users_data = [
            {
                "phone": "+919876543210",
                "role": "worker",
                "first_name": "Raju",
                "last_name": "Kumar",
                "language_preference": "hi",
            },
            {
                "phone": "+919876543211",
                "role": "contractor",
                "first_name": "Vikram",
                "last_name": "Singh",
                "language_preference": "en",
            },
            {
                "phone": "+919876543212",
                "role": "worker",
                "first_name": "Sunil",
                "last_name": "Yadav",
                "language_preference": "mr",
            },
        ]

        created_users = {}

        for u_data in users_data:
            user, created = User.objects.get_or_create(
                phone=u_data["phone"],
                defaults={
                    "role": u_data["role"],
                    "first_name": u_data["first_name"],
                    "last_name": u_data["last_name"],
                    "language_preference": u_data["language_preference"],
                    "is_active": True,
                },
            )
            created_users[u_data["role"]] = user

            if created:
                self.stdout.write(f"Created user: {user.phone} ({user.role})")
                # Set password for admin login if needed (optional)
                user.set_password("demo1234")
                user.save()

        # 2. Create Profiles
        # Worker Profile for Raju
        worker_user = User.objects.get(phone="+919876543210")
        worker_profile, created = WorkerProfile.objects.get_or_create(
            user=worker_user,
            defaults={
                "availability_status": "available",
                "experience_years": 5,
                "bio": "Expert plumber with 5 years experience",
                "rating": 4.5,
                "price_amount": 600.00,  # ₹600 per day
                "price_currency": "INR",
                "price_type": "per_day",
                "min_charge": 300.00,  # ₹300 minimum
            },
        )

        # Add services to worker
        plumbing = Service.objects.filter(slug="plumbing").first()
        if plumbing and created:
            worker_profile.services.add(plumbing)

        # Worker Profile for Sunil
        worker2_user = User.objects.get(phone="+919876543212")
        worker2_profile, created = WorkerProfile.objects.get_or_create(
            user=worker2_user,
            defaults={
                "availability_status": "busy",
                "experience_years": 3,
                "bio": "Experienced electrician",
                "rating": 4.2,
                "price_amount": 500.00,
                "price_currency": "INR",
                "price_type": "per_day",
            },
        )
        
        electrician = Service.objects.filter(slug="electrician").first()
        if electrician and created:
            worker2_profile.services.add(electrician)

        # Contractor Profile for Vikram
        contractor_user = User.objects.get(phone="+919876543211")
        ContractorProfile.objects.get_or_create(
            user=contractor_user,
            defaults={
                "company_name": "Vikram Constructions",
                "license_number": "LIC-2024-001",
                "city": "Mumbai",
            },
        )

        # 3. Create Demo Jobs
        if plumbing:
            Job.objects.get_or_create(
                poster=contractor_user,
                title="Fix leaking tap in kitchen",
                defaults={
                    "service": plumbing,
                    "description": "Kitchen tap is leaking continuously. Need urgent fix.",
                    "status": "open",
                    "location": "Andheri West, Mumbai",
                    "budget": 500.00,
                },
            )

            Job.objects.get_or_create(
                poster=contractor_user,
                title="Bathroom Pipe Installation",
                defaults={
                    "service": plumbing,
                    "description": "Full piping for new bathroom renovation.",
                    "status": "open",
                    "location": "Bandra, Mumbai",
                    "budget": 5000.00,
                },
            )
            self.stdout.write("Created demo jobs")

        # 4. Create Theme
        theme, created = Theme.objects.get_or_create(
            name="HunarMitra Default",
            defaults={
                "primary_color": "#2563EB",
                "accent_color": "#F59E0B",
                "background_color": "#F9FAFB",
                "logo_s3_key": "static/logo.png",
                "fonts": [
                    {"family": "Inter", "s3_key": "static/fonts/default.woff"},
                    {"family": "Roboto", "s3_key": "static/fonts/roboto.woff"},
                ],
                "active": True,
                "metadata": {
                    "dark_mode_support": True,
                    "rtl_support": False,
                },
            },
        )
        if created:
            self.stdout.write("Created default theme")

        # 5. Create Banners
        banner_data = [
            {
                "title": "Welcome to HunarMitra",
                "subtitle": "Find skilled workers near you",
                "image_s3_key": "static/banners/welcome.png",
                "action": {"type": "route", "value": "/services"},
                "display_order": 1,
            },
            {
                "title": "Special Offer!",
                "subtitle": "Get 10% off on first booking",
                "image_s3_key": "static/banners/offer.png",
                "action": {"type": "url", "value": "https://hunarmitra.com/offers"},
                "display_order": 2,
            },
        ]

        for b_data in banner_data:
            banner, created = Banner.objects.get_or_create(
                title=b_data["title"],
                defaults={
                    "subtitle": b_data["subtitle"],
                    "image_s3_key": b_data["image_s3_key"],
                    "action": b_data["action"],
                    "display_order": b_data["display_order"],
                    "active": True,
                },
            )
            if created:
                self.stdout.write(f"Created banner: {banner.title}")

        # 6. Create Bookings
        from apps.bookings.models import Booking
        
        # User who needs a worker
        client_user, created = User.objects.get_or_create(
            phone="+919000000001",
            defaults={
                "role": "employer",
                "first_name": "Amit",
                "last_name": "Verma"
            }
        )
        
        # Booking 1: Requested
        Booking.objects.get_or_create(
            user=client_user,
            service=plumbing,
            address="Flat 402, Green Valley Apts, Powai",
            defaults={
                "lat": 19.1136,
                "lng": 72.8697,
                "status": Booking.STATUS_REQUESTED,
                "notes": "Tap leaking heavily",
                "estimated_price": 500.00
            }
        )
        
        # Booking 2: Confirmed with Worker
        Booking.objects.get_or_create(
            user=client_user,
            service=plumbing,
            address="Shop 10, Main Market, Andheri",
            defaults={
                "lat": 19.1197,
                "lng": 72.8464,
                "status": Booking.STATUS_CONFIRMED,
                "worker": worker_profile, # Assigned to Raju
                "notes": "Pipe installation pending",
                "estimated_price": 2500.00
            }
        )
        
        # 7. Create Construction Sites
        from apps.contractors.models import Site, SiteAssignment, SiteAttendance
        from datetime import timedelta
        
        site1, created = Site.objects.get_or_create(
            name="Green Valley Construction Site",
            contractor=contractor_user.contractor_profile,
            defaults={
                "address": "Plot 42, Sector 15, Gomti Nagar, Lucknow",
                "lat": 26.8500,
                "lng": 80.9500,
                "phone": "+919876543200",
                "is_active": True,
                "start_date": timezone.now().date() - timedelta(days=30)
            }
        )
        
        site2, created = Site.objects.get_or_create(
            name="Blue Heights Residential Project",
            contractor=contractor_user.contractor_profile,
            defaults={
                "address": "Gomti Nagar Extension, Lucknow",
                "lat": 26.8400,
                "lng": 80.9400,
                "is_active": True,
                "start_date": timezone.now().date() - timedelta(days=15)
            }
        )
        
        # Assign workers to sites
        SiteAssignment.objects.get_or_create(
            site=site1,
            worker=worker_profile,
            defaults={
                "assigned_by": contractor_user,
                "role_on_site": "Plumber",
                "is_active": True
            }
        )
        
        SiteAssignment.objects.get_or_create(
            site=site1,
            worker=worker2_profile,
            defaults={
                "assigned_by": contractor_user,
                "role_on_site": "Electrician",
                "is_active": True
            }
        )
        
        # Create attendance for last 7 days
        for i in range(7):
            date = timezone.now().date() - timedelta(days=i)
            
            # Worker 1 attendance (mostly present)
            status1 = 'present' if i < 5 else ('absent' if i == 5 else 'half_day')
            checkin1 = timezone.now().replace(hour=9, minute=0) - timedelta(days=i) if status1 in ['present', 'half_day'] else None
            
            SiteAttendance.objects.get_or_create(
                site=site1,
                worker=worker_profile,
                attendance_date=date,
                defaults={
                    "status": status1,
                    "checkin_time": checkin1,
                    "marked_by": contractor_user
                }
            )
            
            # Worker 2 attendance (mix of present/absent)
            status2 = 'present' if i % 2 == 0 else 'absent'
            checkin2 = timezone.now().replace(hour=9, minute=30) - timedelta(days=i) if status2 == 'present' else None
            
            SiteAttendance.objects.get_or_create(
                site=site1,
                worker=worker2_profile,
                attendance_date=date,
                defaults={
                    "status": status2,
                    "checkin_time": checkin2,
                    "marked_by": contractor_user
                }
            )
        
        self.stdout.write(self.style.SUCCESS("Successfully seeded demo data (including sites and attendance)"))
