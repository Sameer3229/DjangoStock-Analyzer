# import requests
# from django.core.management.base import BaseCommand
# from analytics.models import Company, StockPriceHistory
# from datetime import datetime
# import time

# class Command(BaseCommand):
#     help = 'Fetches LIVE Stock Price Data using User Logic'

#     def clean_decimal(self, value):
#         """ Aapka clean_number function adapted for Django """
#         if value is None or value == "": return 0.0
#         if isinstance(value, (int, float)): return float(value)
#         if isinstance(value, str):
            
#             clean_val = value.replace(",", "").replace("%", "")
#             try:
#                 return float(clean_val)
#             except ValueError:
#                 return 0.0
#         return 0.0

#     def handle(self, *args, **kwargs):
#         companies = Company.objects.all()
#         total = companies.count()
        
#         self.stdout.write(f"🚀 Starting Fetch for {total} companies (Using Logic 2)...")

#         for index, company in enumerate(companies):
#             ticker_id = company.company_id
#             ticker_symbol = company.ticker
            
#             # Progress Print
#             self.stdout.write(f"⏳ [{index + 1}/{total}] {ticker_symbol}...", ending='')

            
#             url = f"https://api.askanalyst.com.pk/api/sharepricedatanew/{ticker_id}"
#             headers = {'User-Agent': 'Mozilla/5.0'}

#             try:
#                 response = requests.get(url, headers=headers, timeout=10)
                
#                 if response.status_code == 200:
#                     data = response.json()
#                     # print(data)

                    
#                     if isinstance(data, dict):
                        
#                         # 1. Date Parse Karo: "20 January 2026 03:05:56"
#                         raw_date = data.get('date')
#                         date_obj = datetime.now().date() # Default fallback
                        
#                         if raw_date:
#                             try:
#                                 # Format: 20 January 2026 03:05:56
#                                 dt = datetime.strptime(raw_date, "%d %B %Y %H:%M:%S")
#                                 date_obj = dt.date()
#                             except Exception:
#                                 pass 

                        
#                         val_close = self.clean_decimal(data.get('current') or data.get('close'))
#                         val_open = self.clean_decimal(data.get('open'))
#                         val_high = self.clean_decimal(data.get('high'))
#                         val_low = self.clean_decimal(data.get('low'))
#                         val_vol = int(self.clean_decimal(data.get('volume')))
                        
                        
#                         val_pe = self.clean_decimal(data.get('pe'))
#                         val_mcap = int(self.clean_decimal(data.get('market_cap')))

#                         # 3. Save to DB
#                         obj, created = StockPriceHistory.objects.update_or_create(
#                             company=company,
#                             date=date_obj,
#                             defaults={
#                                 'close': val_close,
#                                 'open_val': val_open,
#                                 'high': val_high,
#                                 'low': val_low,
#                                 'volume': val_vol,
#                                 'pe_live': val_pe,
#                                 'market_cap': val_mcap
#                             }
#                         )
                        
#                         if created:
#                             self.stdout.write(self.style.SUCCESS(" Created ✅"))
#                         else:
#                             self.stdout.write(self.style.SUCCESS(" Updated 🔄"))
                    
#                     else:
#                         # Agar data list [] hua (kuch cases mein)
#                         self.stdout.write(self.style.WARNING(" Skipped (Not a Dict)"))

#                 else:
#                     self.stdout.write(self.style.WARNING(f" Failed ({response.status_code})"))

#             except Exception as e:
#                 self.stdout.write(self.style.ERROR(f" Error: {str(e)}"))

#         self.stdout.write(self.style.SUCCESS("✅ Complete!"))




from django.core.management.base import BaseCommand
from analytics.models import Company
from analytics.tasks import fetch_company_market_data # Task Import

class Command(BaseCommand):
    help = 'Triggers Celery tasks for LIVE Market Data'

    def handle(self, *args, **kwargs):
        companies = Company.objects.all()
        count = companies.count()
        
        self.stdout.write(f"🚀 Dispatching {count} tasks to Celery...")

        for company in companies:
            
            fetch_company_market_data.delay(company.company_id)

        self.stdout.write(self.style.SUCCESS(f"✅ {count} Tasks added to Queue! Check Worker Terminal."))