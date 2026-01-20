import requests
from django.core.management.base import BaseCommand
from analytics.models import Company, FinancialReport

class Command(BaseCommand):
    help = 'Fetches Financial Ratios (API 1) - Flat List Structure'

    def clean_number(self, value):
        """ Handles '40.37', '27.44', '(5.0)' etc """
        if value is None or value == "": return 0.0
        if isinstance(value, (int, float)): return float(value)
        if isinstance(value, str):
            # Remove comma, percent. Handle negative in ()
            clean_val = value.replace(",", "").replace("%", "")
            if "(" in clean_val and ")" in clean_val:
                clean_val = "-" + clean_val.replace("(", "").replace(")", "")
            try:
                return float(clean_val)
            except:
                return 0.0
        return 0.0

    def handle(self, *args, **kwargs):
        companies = Company.objects.all()
        total = companies.count()
        
        self.stdout.write(f"🚀 Starting Ratios Fetch (API 1)...")

        for index, company in enumerate(companies):
            ticker_id = company.company_id
            ticker_symbol = company.ticker
            
            self.stdout.write(f"⏳ [{index + 1}/{total}] {ticker_symbol}...", ending='')

            # --- URL Updated based on your input ---
            url = f"https://api.askanalyst.com.pk/api/companyfinancialnew/{ticker_id}?companyfinancial=true&&test=true"
            headers = {'User-Agent': 'Mozilla/5.0'}

            try:
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if data is a List (As per your JSON)
                    if not isinstance(data, list):
                        self.stdout.write(self.style.WARNING(" Skipped (Not a List)"))
                        continue

                    if not data:
                        self.stdout.write(self.style.WARNING(" No Data"))
                        continue

                    # --- 1. PIVOT LOGIC ---
                    # Convert: Label -> [Years]  TO  Year -> {Labels}
                    data_by_year = {}

                    for metric_item in data:
                        label = metric_item.get('label', 'Unknown').strip() # e.g. "EPS", "ROE"
                        points = metric_item.get('data', [])

                        for point in points:
                            year_raw = point.get('year') # "2021"
                            val = point.get('value')
                            
                            try:
                                # Ratios usually Annual hotay hain is format main
                                year_int = int(year_raw) 
                            except:
                                continue

                            if year_int not in data_by_year:
                                data_by_year[year_int] = {}

                            # Store value
                            data_by_year[year_int][label] = self.clean_number(val)

                    # --- 2. SAVE TO DB ---
                    saved_count = 0
                    for year, metrics in data_by_year.items():
                        try:
                            # Extract Core Columns for Sorting/Filtering
                            eps_val = metrics.get('EPS', 0.0)
                            roe_val = metrics.get('ROE', 0.0)

                            FinancialReport.objects.update_or_create(
                                company=company,
                                year=year,
                                report_type='RATIOS', # Fixed
                                period='ANNUAL',      # Defaulting to Annual based on JSON
                                defaults={
                                    'eps': eps_val,
                                    'roe': roe_val,
                                    'revenue': None,    # Not applicable
                                    'net_profit': None, # Not applicable
                                    'details': metrics  # Full JSON (PE, PBV, Margins etc)
                                }
                            )
                            saved_count += 1
                        except Exception as e:
                            continue

                    self.stdout.write(self.style.SUCCESS(f" Saved {saved_count} Years"))

                else:
                    self.stdout.write(self.style.WARNING(f" Failed ({response.status_code})"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f" Error: {str(e)}"))

        self.stdout.write(self.style.SUCCESS("✅ Ratios Fetch Complete!"))