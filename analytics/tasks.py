from celery import shared_task
import requests
from datetime import datetime
from .models import Company, StockPriceHistory, FinancialReport
from analytics.utils import clean_number



@shared_task
def fetch_company_market_data(company_id):
    """
    Ye function background worker chalayega.
    Input: company_id (Integer)
    """
    try:
        
        company = Company.objects.get(company_id=company_id)
        ticker_symbol = company.ticker

        
        url = f"https://api.askanalyst.com.pk/api/sharepricedatanew/{company_id}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, dict):
                # 1. Date Logic
                raw_date = data.get('date')
                date_obj = datetime.now().date() # Fallback
                if raw_date:
                    try:
                        # Format: "20 January 2026 03:05:56"
                        dt = datetime.strptime(raw_date, "%d %B %Y %H:%M:%S")
                        date_obj = dt.date()
                    except Exception:
                        pass 

                # 2. Values Extraction (Exact Logic)
                val_close = clean_number(data.get('current') or data.get('close'))
                val_open = clean_number(data.get('open'))
                val_high = clean_number(data.get('high'))
                val_low = clean_number(data.get('low'))
                val_vol = int(clean_number(data.get('volume')))
                
                val_pe = clean_number(data.get('pe'))
                val_mcap = int(clean_number(data.get('market_cap')))

                # 3. Save to DB
                obj, created = StockPriceHistory.objects.update_or_create(
                    company=company,
                    date=date_obj,
                    defaults={
                        'close': val_close,
                        'open_val': val_open,
                        'high': val_high,
                        'low': val_low,
                        'volume': val_vol,
                        'pe_live': val_pe,
                        'market_cap': val_mcap
                    }
                )
                
                status = "Created ✅" if created else "Updated 🔄"
                return f"{ticker_symbol}: {status}"
            
            return f"{ticker_symbol}: Skipped (Not a Dict)"
        
        return f"{ticker_symbol}: Failed ({response.status_code})"
    
    except Exception as e:
        return f"Error {company_id}: {str(e)}"
    


# --- Task 2: Balance Sheet 
def process_bs_period(company, period_name, data_list):
    """ Helper specifically for Balance Sheet Nested Logic """
    if not data_list: return 0

    data_by_year = {}

    for group in data_list:
        metrics_list = group.get('data', [])
        for metric in metrics_list:
            label = metric.get('label', 'Unknown').strip()
            points = metric.get('data', [])

            for point in points:
                year_raw = point.get('year')
                val = point.get('value')
                
                try:
                    if period_name == "ANNUAL":
                        year_int = int(year_raw)
                    else:
                        parts = year_raw.split('-')
                        if len(parts) == 2:
                            year_int = 2000 + int(parts[1])
                        else: continue
                except: continue

                if year_int not in data_by_year:
                    data_by_year[year_int] = {}

                # Use Universal clean_number
                data_by_year[year_int][label] = clean_number(val)
    
    saved = 0 
    for year, metrics in data_by_year.items():
        try:
            FinancialReport.objects.update_or_create(
                company=company,
                year=year,
                report_type='BALANCE_SH', 
                period=period_name,
                defaults={'details': metrics}
            )
            saved += 1
        except: continue
    return saved

@shared_task
def fetch_company_balance_sheet(company_id):
    try:
        company = Company.objects.get(company_id=company_id)
        url = f"https://api.askanalyst.com.pk/api/bs/{company_id}"
        headers = {'User-Agent': 'Mozilla/5.0'}

        response = requests.get(url, headers=headers, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            c1 = process_bs_period(company, 'ANNUAL', data.get('annual', []))
            c2 = process_bs_period(company, 'QUARTERLY', data.get('quarter', []))
            return f"{company.ticker}: BS Saved (Ann:{c1}, Qtr:{c2})"
        return f"{company.ticker}: BS Failed"
    except Exception as e:
        return f"Error {company_id}: {str(e)}"
    

# --- Task 3: Income Statement  ---

def process_is_period(company, period_name, data_list):
    """ Helper to process Income Statement Data (Annual/Quarterly) """
    if not data_list: return 0

    data_by_year = {}

    for item in data_list:
        label = item.get('label', 'Unknown').strip()
        points = item.get('data', [])

        for point in points:
            year_raw = point.get('year')
            val = point.get('value')
            
            try:
                if period_name == "ANNUAL":
                    year_int = int(year_raw)
                else:
                    # Quarterly: "Sep-24" -> 2024
                    parts = year_raw.split('-')
                    if len(parts) == 2:
                        year_int = 2000 + int(parts[1])
                    else:
                        continue
            except:
                continue
            
            if year_int not in data_by_year:
                data_by_year[year_int] = {}

            
            data_by_year[year_int][label] = clean_number(val)
        
    saved_count = 0 

    for year, metrics in data_by_year.items():
        try:
            # --- MAPPING LOGIC ---
            rev = 0
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
                period=period_name, 
                defaults={
                    'revenue': int(rev),
                    'net_profit': int(profit),
                    'eps': eps,
                    'details': metrics # Full JSON
                }
            )
            saved_count += 1
        except Exception:
            continue
    return saved_count

@shared_task
def fetch_company_income_statement(company_id):
    """
    Worker Task for API 6 (Income Statement)
    """
    try:
        company = Company.objects.get(company_id=company_id)
        ticker = company.ticker
        
        # API 6 URL
        url = f"https://api.askanalyst.com.pk/api/is/{company_id}"
        headers = {'User-Agent': 'Mozilla/5.0'}

        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            # Annual
            c1 = process_is_period(company, 'ANNUAL', data.get('annual', []))
            # Quarterly
            c2 = process_is_period(company, 'QUARTERLY', data.get('quarter', []))

            return f"{ticker}: IS Saved (Ann:{c1}, Qtr:{c2})"
        
        return f"{ticker}: IS Failed ({response.status_code})"

    except Exception as e:
        return f"Error {company_id}: {str(e)}"
    


# --- Task 4: Financial Ratios 

@shared_task
def fetch_company_ratios(company_id):
    """
    Worker Task for API 1 (Financial Ratios)
    """
    try:
        company = Company.objects.get(company_id=company_id)
        ticker = company.ticker
        
        # API 1 URL
        url = f"https://api.askanalyst.com.pk/api/companyfinancialnew/{company_id}?companyfinancial=true&&test=true"
        headers = {'User-Agent': 'Mozilla/5.0'}

        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validation check
            if not isinstance(data, list):
                return f"{ticker}: Skipped (Not a List)"
            
            if not data:
                return f"{ticker}: No Data"

            
            data_by_year = {}

            for metric_item in data:
                label = metric_item.get('label', 'Unknown').strip()
                points = metric_item.get('data', [])

                for point in points:
                    year_raw = point.get('year')
                    val = point.get('value')
                    
                    try:
                        year_int = int(year_raw)
                    except:
                        continue

                    if year_int not in data_by_year:
                        data_by_year[year_int] = {}

                    
                    data_by_year[year_int][label] = clean_number(val)

            # --- SAVE TO DB ---
            saved_count = 0
            for year, metrics in data_by_year.items():
                try:
                    
                    eps_val = metrics.get('EPS', 0.0)
                    roe_val = metrics.get('ROE', 0.0)

                    FinancialReport.objects.update_or_create(
                        company=company,
                        year=year,
                        report_type='RATIOS', 
                        period='ANNUAL',
                        defaults={
                            'eps': eps_val,
                            'roe': roe_val,
                            'revenue': None,    
                            'net_profit': None, 
                            'details': metrics  # Full JSON
                        }
                    )
                    saved_count += 1
                except Exception:
                    continue

            return f"{ticker}: Ratios Saved ({saved_count} Years)"

        return f"{ticker}: Failed ({response.status_code})"

    except Exception as e:
        return f"Error {company_id}: {str(e)}"
    

# --- Task 5: Industry Benchmarks (Converted) ---

@shared_task
def fetch_company_industry(company_id):
    """
    Worker Task for API 4 (Industry Benchmarks)
    Current Snapshot Data (Saved with Current Year)
    """
    try:
        company = Company.objects.get(company_id=company_id)
        ticker = company.ticker
        
        
        current_year = datetime.now().year 

        # API 4 URL
        url = f"https://api.askanalyst.com.pk/api/industrynew/{company_id}"
        headers = {'User-Agent': 'Mozilla/5.0'}

        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validation
            if not isinstance(data, list) or not data:
                return f"{ticker}: Industry Skipped (Invalid Data)"

            
            industry_metrics = {}
            for item in data:
                label = item.get('label', 'Unknown').strip()
                val = item.get('value')
                
                industry_metrics[label] = clean_number(val)

            # --- SAVE TO DB ---
            FinancialReport.objects.update_or_create(
                company=company,
                year=current_year,
                report_type='INDUSTRY', 
                period='ANNUAL',        
                defaults={
                    'revenue': None,
                    'net_profit': None,
                    'eps': None,
                    'details': industry_metrics 
                }
            )
            
            return f"{ticker}: Industry Updated ✅"

        return f"{ticker}: Industry Failed ({response.status_code})"

    except Exception as e:
        return f"Error {company_id}: {str(e)}"