# import requests
# from django.core.management.base import BaseCommand
# from analytics.models import Company, FinancialReport

# class Command(BaseCommand):
#     help = 'Fetches Financial Ratios (API 1) - Flat List Structure'

#     def clean_number(self, value):
#         """ Handles '40.37', '27.44', '(5.0)' etc """
#         if value is None or value == "": return 0.0
#         if isinstance(value, (int, float)): return float(value)
#         if isinstance(value, str):
            
#             clean_val = value.replace(",", "").replace("%", "")
#             if "(" in clean_val and ")" in clean_val:
#                 clean_val = "-" + clean_val.replace("(", "").replace(")", "")
#             try:
#                 return float(clean_val)
#             except:
#                 return 0.0
#         return 0.0

#     def handle(self, *args, **kwargs):
#         companies = Company.objects.all()
#         total = companies.count()
        
#         self.stdout.write(f"🚀 Starting Ratios Fetch (API 1)...")

#         for index, company in enumerate(companies):
#             ticker_id = company.company_id
#             ticker_symbol = company.ticker
            
#             self.stdout.write(f"⏳ [{index + 1}/{total}] {ticker_symbol}...", ending='')

            
#             url = f"https://api.askanalyst.com.pk/api/companyfinancialnew/{ticker_id}?companyfinancial=true&&test=true"
#             headers = {'User-Agent': 'Mozilla/5.0'}

#             try:
#                 response = requests.get(url, headers=headers, timeout=10)
                
#                 if response.status_code == 200:
#                     data = response.json()
                    
                    
#                     if not isinstance(data, list):
#                         self.stdout.write(self.style.WARNING(" Skipped (Not a List)"))
#                         continue

#                     if not data:
#                         self.stdout.write(self.style.WARNING(" No Data"))
#                         continue

                    
#                     data_by_year = {}

#                     for metric_item in data:
#                         label = metric_item.get('label', 'Unknown').strip() # e.g. "EPS", "ROE"
#                         points = metric_item.get('data', [])

#                         for point in points:
#                             year_raw = point.get('year') # "2021"
#                             val = point.get('value')
                            
#                             try:
                                
#                                 year_int = int(year_raw) 
#                             except:
#                                 continue

#                             if year_int not in data_by_year:
#                                 data_by_year[year_int] = {}

#                             # Store value
#                             data_by_year[year_int][label] = self.clean_number(val)

#                     # --- 2. SAVE TO DB ---
#                     saved_count = 0
#                     for year, metrics in data_by_year.items():
#                         try:
                           
#                             eps_val = metrics.get('EPS', 0.0)
#                             roe_val = metrics.get('ROE', 0.0)

#                             FinancialReport.objects.update_or_create(
#                                 company=company,
#                                 year=year,
#                                 report_type='RATIOS', 
#                                 period='ANNUAL',      
#                                 defaults={
#                                     'eps': eps_val,
#                                     'roe': roe_val,
#                                     'revenue': None,    
#                                     'net_profit': None, 
#                                     'details': metrics  
#                                 }
#                             )
#                             saved_count += 1
#                         except Exception as e:
#                             continue

#                     self.stdout.write(self.style.SUCCESS(f" Saved {saved_count} Years"))

#                 else:
#                     self.stdout.write(self.style.WARNING(f" Failed ({response.status_code})"))

#             except Exception as e:
#                 self.stdout.write(self.style.ERROR(f" Error: {str(e)}"))

#         self.stdout.write(self.style.SUCCESS("✅ Ratios Fetch Complete!"))


from django.core.management.base import BaseCommand
from analytics.models import Company
from analytics.tasks import fetch_company_ratios 

class Command(BaseCommand):
    help = 'Triggers Celery tasks for Financial Ratios (API 1)'

    def handle(self, *args, **kwargs):
        companies = Company.objects.all()
        count = companies.count()
        
        self.stdout.write(f"🚀 Dispatching {count} Ratio tasks to Celery...")

        for company in companies:
            # Send to Queue
            fetch_company_ratios.delay(company.company_id)

        self.stdout.write(self.style.SUCCESS(f"✅ All {count} tasks added to Queue!"))