import requests
from django.core.management.base import BaseCommand
from analytics.models import Company, FinancialReport

class Command(BaseCommand):
    help = 'Fetches Income Statement (API 6) and Pivots data for DB'

    def clean_number(self, value):
        if value is None or value == "": return 0.0
        if isinstance(value, (int, float)): return float(value)
        if isinstance(value, str):
            clean_val = value.replace(",", "").replace("%", "")
            if "(" in clean_val and ")" in clean_val:
                clean_val = "-" + clean_val.replace("(", "").replace(")", "")
            try:
                return float(clean_val)
            except:
                return 0.0
        return 0.0
    

    def process_period_data(self, company, period_name, data_list):
        if not data_list: return 0

        data_by_year = {}

        for item in data_list:
            label = item.get('label','Unknown').strip()
            points = item.get('data',[])

            for point in points:
                year_raw = point.get('year')
                val = point.get('value')
                
                try:
                    if period_name == "ANNUAL":
                        year_int = int(year_raw)
                    else:
                        parts = year_raw.split('-')
                        if len(parts)==2:
                            year_int = 2000 + int(parts[1])
                        else:
                            continue

                except:
                    continue

                
                if year_int not in data_by_year:
                    data_by_year[year_int]={}

                data_by_year[year_int][label] = self.clean_number(val)
            
        saved_count = 0 

        for year, metrics, in data_by_year.items():
            try:
                rev=0
                if 'Net sales' in metrics: rev = metrics['Net sales']
                elif 'Sales' in metrics: rev = metrics['Sales']
                elif 'Revenue' in metrics: rev = metrics['Revenue']

                profit = 0
                if 'Profit after tax' in metrics: profit = metrics['Profit after tax']
                elif 'Net Profit' in metrics: profit = metrics['Net Profit']
                elif 'Profit for the year' in metrics: profit = metrics['Profit for the year']

                eps = 0.0
                if 'EPS - Basic' in metrics: eps = metrics['EPS - Basic']
                elif 'Earning Per Share' in metrics: eps = metrics['Earning Per Share']

                FinancialReport.objects.update_or_create(
                    company=company,
                    year=year,
                    report_type='INCOME_ST', 
                    period=period_name, # ANNUAL or QUARTERLY
                    defaults={
                        'revenue': int(rev),
                        'net_profit': int(profit),
                        'eps': eps,
                        'details': metrics # Full JSON
                    }
                )
                saved_count += 1
            except Exception as e:
                continue
        return saved_count
    
    def handle(self, *args, **kwargs):
        companies = Company.objects.all()
        total = companies.count()
        
        self.stdout.write(f"🚀 Starting Income Statement Fetch for {total} companies...")

        for index, company in enumerate(companies):
            ticker_id = company.company_id # Use ID for API 6 based on your pattern
            ticker_symbol = company.ticker 
            
            self.stdout.write(f"⏳ [{index + 1}/{total}] {ticker_symbol}...", ending='')

            url = f"https://api.askanalyst.com.pk/api/is/{ticker_id}"

            headers = {'User-Agent': 'Mozilla/5.0'}

            try:
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()

                    c1 = self.process_period_data(company, 'ANNUAL', data.get('annual', []))

                    c2 = self.process_period_data(company, 'QUARTERLY', data.get('quarter', []))

                    self.stdout.write(self.style.SUCCESS(f" Saved (Ann: {c1}, Qtr: {c2})"))

                else:
                    self.stdout.write(self.style.WARNING(f" Failed ({response.status_code})"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f" Error"))

        self.stdout.write(self.style.SUCCESS("✅ Complete!"))


        