"""
Management command to seed demo help pages and FAQs.
"""
from django.core.management.base import BaseCommand
from apps.help.models import HelpPage, FAQ


class Command(BaseCommand):
    help = 'Seed demo help pages and FAQs in English and Hindi'
    
    def handle(self, *args, **kwargs):
        """Seed demo help content."""
        
        # Help Pages
        help_pages_data = [
            {
                'slug': 'getting-started',
                'title': 'Getting Started',
                'content_html': '<h2>Welcome to HunarMitra</h2><p>Find skilled workers near you easily...</p>',
                'lang': 'en',
                'order': 1
            },
            {
                'slug': 'shuruat-kaise-karen',
                'title': 'शुरुआत कैसे करें',
                'content_html': '<h2>हुनरमित्र में आपका स्वागत है</h2><p>अपने आस-पास कुशल कारीगर आसानी से खोजें...</p>',
                'lang': 'hi',
                'order': 1
            },
            {
                'slug': 'booking-service',
                'title': 'How to Book a Service',
                'content_html': '<h2>Booking Process</h2><p>1. Browse services<br>2. Select a worker<br>3. Confirm booking</p>',
                'lang': 'en',
                'order': 2
            },
            {
                'slug': 'seva-book-kaise-karen',
                'title': 'सेवा कैसे बुक करें',
                'content_html': '<h2>बुकिंग प्रक्रिया</h2><p>1. सेवाएं देखें<br>2. कारीगर चुनें<br>3. बुकिंग की पुष्टि करें</p>',
                'lang': 'hi',
                'order': 2
            },
            {
                'slug': 'payment-info',
                'title': 'Payment Information',
                'content_html': '<h2>Payment Methods</h2><p>We accept cash, UPI, and digital payments...</p>',
                'lang': 'en',
                'order': 3
            },
            {
                'slug': 'bhugtan-jaankari',
                'title': 'भुगतान जानकारी',
                'content_html': '<h2>भुगतान के तरीके</h2><p>हम नकद, UPI और डिजिटल पेमेंट स्वीकार करते हैं...</p>',
                'lang': 'hi',
                'order': 3
            },
        ]
        
        # FAQs
        faqs_data = [
            {
                'question': 'How do I find workers near me?',
                'answer': 'Open the app, enable location services, and browse workers sorted by distance.',
                'lang': 'en',
                'order': 1
            },
            {
                'question': 'मुझे अपने पास कारीगर कैसे मिलेंगे?',
                'answer': 'ऐप खोलें, लोकेशन सर्विस चालू करें, और दूरी के अनुसार कारीगर देखें।',
                'lang': 'hi',
                'order': 1
            },
            {
                'question': 'What services are available?',
                'answer': 'Plumbing, electrical work, painting, carpentry, and more.',
                'lang': 'en',
                'order': 2
            },
            {
                'question': 'कौन सी सेवाएं उपलब्ध हैं?',
                'answer': 'प्लंबिंग, बिजली का काम, पेंटिंग, बढ़ईगिरी और बहुत कुछ।',
                'lang': 'hi',
                'order': 2
            },
            {
                'question': 'How do I make a payment?',
                'answer': 'You can pay via cash, UPI, or any digital payment method.',
                'lang': 'en',
                'order': 3
            },
            {
                'question': 'भुगतान कैसे करें?',
                'answer': 'आप नकद, UPI या किसी भी डिजिटल पेमेंट विधि से भुगतान कर सकते हैं।',
                'lang': 'hi',
                'order': 3
            },
        ]
        
        # Seed Help Pages
        created_pages = 0
        updated_pages = 0
        
        for page_data in help_pages_data:
            page, created = HelpPage.objects.update_or_create(
                slug=page_data['slug'],
                defaults=page_data
            )
            
            if created:
                created_pages += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created help page: {page.title}')
                )
            else:
                updated_pages += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Updated help page: {page.title}')
                )
        
        # Seed FAQs
        created_faqs = 0
        updated_faqs = 0
        
        for faq_data in faqs_data:
            # Use question + lang as unique key
            faq, created = FAQ.objects.update_or_create(
                question=faq_data['question'],
                lang=faq_data['lang'],
                defaults=faq_data
            )
            
            if created:
                created_faqs += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created FAQ: {faq.question[:50]}...')
                )
            else:
                updated_faqs += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Updated FAQ: {faq.question[:50]}...')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Seeding complete:\n'
                f'  Help Pages: {created_pages} created, {updated_pages} updated\n'
                f'  FAQs: {created_faqs} created, {updated_faqs} updated'
            )
        )
