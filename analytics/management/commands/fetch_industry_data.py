# import requests
# from django.core.management.base import BaseCommand
# from analytics.models import Company, FinancialReport
# from datetime import datetime

# class Command(BaseCommand):
#     help = 'Fetches Industry Benchmarks (API 4) - Current Snapshot'

#     def clean_number(self, value):
#         """ Handles string to float conversion """
#         if value is None or value == "": return 0.0
#         if isinstance(value, (int, float)): return float(value)
#         if isinstance(value, str):
#             clean_val = value.replace(",", "").replace("%", "")
#             try: return float(clean_val)
#             except: return 0.0
#         return 0.0

#     def handle(self, *args, **kwargs):
#         companies = Company.objects.all()
#         total = companies.count()
        
        
#         current_year = datetime.now().year 

#         self.stdout.write(f"🚀 Starting Industry Data Fetch (Year: {current_year})...")

#         for index, company in enumerate(companies):
#             ticker_id = company.company_id
#             ticker_symbol = company.ticker
            
#             self.stdout.write(f"⏳ [{index + 1}/{total}] {ticker_symbol}...", ending='')

#             # API 4 URL
#             url = f"https://api.askanalyst.com.pk/api/industrynew/{ticker_id}"
#             headers = {'User-Agent': 'Mozilla/5.0'}

#             try:
#                 response = requests.get(url, headers=headers, timeout=10)
                
#                 if response.status_code == 200:
#                     data = response.json()
                    
#                     if not isinstance(data, list) or not data:
#                         self.stdout.write(self.style.WARNING(" No Data / Invalid Format"))
#                         continue

                    
                    
#                     industry_metrics = {}
#                     for item in data:
#                         label = item.get('label', 'Unknown').strip()
#                         val = item.get('value')
#                         industry_metrics[label] = self.clean_number(val)

                    
                    
#                     FinancialReport.objects.update_or_create(
#                         company=company,
#                         year=current_year,
#                         report_type='INDUSTRY', 
#                         period='ANNUAL',        # Default
#                         defaults={
#                             'details': industry_metrics 
#                         }
#                     )
                    
#                     self.stdout.write(self.style.SUCCESS(" Saved ✅"))

#                 else:
#                     self.stdout.write(self.style.WARNING(f" Failed ({response.status_code})"))

#             except Exception as e:
#                 self.stdout.write(self.style.ERROR(f" Error: {str(e)}"))

#         self.stdout.write(self.style.SUCCESS("✅ Industry Fetch Complete!"))


from django.core.management.base import BaseCommand
from analytics.models import Company
from analytics.tasks import fetch_company_industry 

class Command(BaseCommand):
    help = 'Triggers Celery tasks for Industry Benchmarks (API 4)'

    def handle(self, *args, **kwargs):
        companies = Company.objects.all()
        count = companies.count()
        
        self.stdout.write(f"🚀 Dispatching {count} Industry tasks to Celery...")

        for company in companies:
            # Send to Queue
            fetch_company_industry.delay(company.company_id)

        self.stdout.write(self.style.SUCCESS(f"✅ All {count} tasks added to Queue!"))