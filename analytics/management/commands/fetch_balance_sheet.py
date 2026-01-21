# import requests
# from django.core.management.base import BaseCommand
# from analytics.models import Company, FinancialReport

# class Command(BaseCommand):
#     help = 'Fetches Balance Sheet (API 7) handling Nested Groups'

#     def clean_number(self, value):
#         if value is None or value == "": return 0.0
#         if isinstance(value, (int, float)): return float(value)
#         if isinstance(value, str):
#             clean_val = value.replace(",", "").replace("%", "")
#             if "(" in clean_val and ")" in clean_val:
#                 clean_val = "-" + clean_val.replace("(", "").replace(")", "")
#             try: return float(clean_val)
#             except: return 0.0
#         return 0.0

#     def process_period_data(self, company, period_name, data_list):
#         if not data_list: return 0

#         data_by_year = {}

#         # --- LEVEL 1: Groups (e.g., "Current Assets", "Equity") ---
#         for group in data_list:
#             # Balance sheet main data 'group' k andar hota hai
#             # Hum group['data'] uthayenge jo metrics ki list hai
#             metrics_list = group.get('data', [])

#             # --- LEVEL 2: Metrics (e.g., "Cash", "Trade Debts") ---
#             for metric in metrics_list:
#                 label = metric.get('label', 'Unknown').strip()
#                 points = metric.get('data', [])

#                 # --- LEVEL 3: Years & Values ---
#                 for point in points:
#                     year_raw = point.get('year')
#                     val = point.get('value')
                    
#                     try:
#                         if period_name == "ANNUAL":
#                             year_int = int(year_raw)
#                         else:
#                             # Quarterly: "Sep-24"
#                             parts = year_raw.split('-')
#                             if len(parts) == 2:
#                                 year_int = 2000 + int(parts[1]) # Logic correct
#                             else:
#                                 continue
#                     except:
#                         continue

#                     if year_int not in data_by_year:
#                         data_by_year[year_int] = {}

#                     # Store value
#                     data_by_year[year_int][label] = self.clean_number(val)
        
#         # --- SAVE TO DB ---
#         saved_count = 0 
#         for year, metrics in data_by_year.items():
#             try:
#                 # Balance Sheet main sirf details JSON save hoga
#                 # Revenue/Profit/EPS yahan applicable nahi hain
#                 FinancialReport.objects.update_or_create(
#                     company=company,
#                     year=year,
#                     report_type='BALANCE_SH', 
#                     period=period_name,
#                     defaults={
#                         'revenue': None,
#                         'net_profit': None,
#                         'eps': None,
#                         'details': metrics # Pura Assets/Liabilities structure yahan
#                     }
#                 )
#                 saved_count += 1
#             except Exception as e:
#                 continue
        
#         return saved_count
    
#     def handle(self, *args, **kwargs):
#         companies = Company.objects.all()
#         total = companies.count()
        
#         self.stdout.write(f"🚀 Starting Balance Sheet Fetch (Nested Logic)...")

#         for index, company in enumerate(companies):
#             ticker_id = company.company_id
#             ticker_symbol = company.ticker 
            
#             self.stdout.write(f"⏳ [{index + 1}/{total}] {ticker_symbol}...", ending='')

#             # API 7 URL
#             url = f"https://api.askanalyst.com.pk/api/bs/{ticker_id}"
#             headers = {'User-Agent': 'Mozilla/5.0'}

#             try:
#                 response = requests.get(url, headers=headers, timeout=10)
                
#                 if response.status_code == 200:
#                     data = response.json()
                    
#                     # Annual Process
#                     c1 = self.process_period_data(company, 'ANNUAL', data.get('annual', []))
                    
#                     # Quarterly Process
#                     c2 = self.process_period_data(company, 'QUARTERLY', data.get('quarter', []))

#                     self.stdout.write(self.style.SUCCESS(f" Saved (Ann: {c1}, Qtr: {c2})"))

#                 else:
#                     self.stdout.write(self.style.WARNING(f" Failed ({response.status_code})"))

#             except Exception as e:
#                 self.stdout.write(self.style.ERROR(f" Error"))

#         self.stdout.write(self.style.SUCCESS("✅ Balance Sheet Complete!"))


from django.core.management.base import BaseCommand
from analytics.models import Company
from analytics.tasks import fetch_company_balance_sheet 

class Command(BaseCommand):
    help = 'Triggers Celery tasks for Balance Sheet (API 7)'

    def handle(self, *args, **kwargs):
        companies = Company.objects.all()
        count = companies.count()
        
        self.stdout.write(f"🚀 Dispatching {count} Balance Sheet tasks to Celery...")

        for company in companies:
            # Send to Queue
            fetch_company_balance_sheet.delay(company.company_id)

        self.stdout.write(self.style.SUCCESS(f"✅ All {count} tasks added to Queue!"))