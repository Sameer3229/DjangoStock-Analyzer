from django.contrib import admin
from .models import Sector, Company, StockPriceHistory, FinancialReport

# 1. Sector Admin
@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ('name', 'sector_id')  # Columns jo dikhenge
    search_fields = ('name',)             # Search bar enable karega
    ordering = ('name',)                  # A-Z sort karega

# 2. Company Admin
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('ticker', 'name', 'sector', 'company_id')
    list_filter = ('sector',)             # Right side pe filter panel aayega
    search_fields = ('ticker', 'name')    # Ticker ya Name se search karo
    ordering = ('ticker',)
    
    # Optimization: Dropdown mein 1000 items load honay se bachanay k liye
    search_fields = ['ticker', 'name'] 

# 3. Stock Price Admin (Heavy Data)
@admin.register(StockPriceHistory)
class StockPriceHistoryAdmin(admin.ModelAdmin):
    list_display = ('company', 'date', 'close', 'volume', 'market_cap')
    list_filter = ('date',)               # Date wise filter
    search_fields = ('company__ticker', 'company__name') # Foreign Key search
    
    # Ye bohot zaroori hai: 
    # Dropdown ki jagah Search Box dega company select krne k liye
    # (Performance k liye best hai)
    autocomplete_fields = ['company'] 

# 4. Financial Report Admin
@admin.register(FinancialReport)
class FinancialReportAdmin(admin.ModelAdmin):
    list_display = ('company', 'year', 'report_type', 'period', 'revenue', 'eps')
    list_filter = ('year', 'report_type', 'period')
    search_fields = ('company__ticker',)
    autocomplete_fields = ['company']