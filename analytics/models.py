from django.db import models

class Sector(models.Model):
    sector_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=100)

    def __str__(self): return self.name

class Company(models.Model):
    company_id = models.IntegerField(unique=True, db_index=True)
    ticker = models.CharField(max_length=30, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    sector = models.ForeignKey(Sector, on_delete=models.SET_NULL, null=True, related_name='companies')
    logo_url = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self): return self.ticker

class StockPriceHistory(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='prices')
    date = models.DateField(db_index=True)
    
    # API 2 (Live) aur API 5 (History) 
    close = models.DecimalField(max_digits=12, decimal_places=2)
    open_val = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    high = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    low = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)
    
    # API 2 
    market_cap = models.BigIntegerField(null=True, blank=True)
    pe_live = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ('company', 'date') # Duplicate dates avoid karega
        ordering = ['-date']

class FinancialReport(models.Model):
    REPORT_TYPES = [
        ('RATIOS', 'Financial Ratios'),       # API 1
        ('GROWTH', 'Growth Metrics'),         # API 3
        ('INDUSTRY', 'Industry Benchmarks'),  # API 4
        ('INCOME_ST', 'Income Statement'),    # API 6
        ('BALANCE_SH', 'Balance Sheet'),      # API 7
    ]
    PERIOD_TYPES = [
        ('ANNUAL', 'Annual'),
        ('QUARTERLY', 'Quarterly'),
        ('TTM', 'Trailing Twelve Months'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='reports')
    year = models.IntegerField(db_index=True) # 2023, 2024
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES, db_index=True)
    period = models.CharField(max_length=20, choices=PERIOD_TYPES, default='ANNUAL')
    
    #  API 1 aur API 6 
    revenue = models.BigIntegerField(null=True, blank=True)      # From API 6 & 3
    net_profit = models.BigIntegerField(null=True, blank=True)   # From API 6
    eps = models.FloatField(null=True, blank=True)               # From API 1
    roe = models.FloatField(null=True, blank=True)               # From API 1
    
    # API 6/7 ki puri hierarchy aur API 4/3 ka extra data yahan JSON ban kar jayega.
    # No data loss!
    details = models.JSONField(default=dict, blank=True) 

    class Meta:
        unique_together = ('company', 'year', 'report_type', 'period')
        indexes = [
            models.Index(fields=['company', 'report_type', 'year']),
        ]    
