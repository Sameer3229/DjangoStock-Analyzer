from django.shortcuts import render, get_object_or_404
from .models import Company, FinancialReport, StockPriceHistory
import json


def pivot_financial_data(reports):
    
    if not reports: return {}
    
    
    years = sorted(list(set(r.year for r in reports)), reverse=True)
    
   
    latest_report = reports.filter(year=years[0]).first()
    if not latest_report: return {}
    
    metrics = list(latest_report.details.keys())
    
    
    matrix = {}
    
    
    report_map = {r.year: r.details for r in reports}
    
    for metric in metrics:
        row_values = []
        for year in years:
            val = report_map.get(year, {}).get(metric, "-")
            row_values.append(val)
        matrix[metric] = row_values
        
    return {'years': years, 'rows': matrix}

def company_dashboard(request, ticker_symbol):
    company = get_object_or_404(Company, ticker=ticker_symbol)
    
    
    latest_price = StockPriceHistory.objects.filter(company=company).order_by('-date').first()
    
   
    income_reports = FinancialReport.objects.filter(company=company, report_type='INCOME_ST', period='ANNUAL')
    balance_reports = FinancialReport.objects.filter(company=company, report_type='BALANCE_SH', period='ANNUAL')
    ratio_reports = FinancialReport.objects.filter(company=company, report_type='RATIOS', period='ANNUAL')
    industry_data = FinancialReport.objects.filter(company=company, report_type='INDUSTRY').last()
    
    
    income_data = pivot_financial_data(income_reports)
    balance_data = pivot_financial_data(balance_reports)
    ratio_data = pivot_financial_data(ratio_reports)
    
    context = {
        'company': company,
        'price': latest_price,
        'income_data': income_data,
        'balance_data': balance_data,
        'ratio_data': ratio_data,
        'industry': industry_data.details if industry_data else {},
    }
    return render(request, 'dashboard.html', context)