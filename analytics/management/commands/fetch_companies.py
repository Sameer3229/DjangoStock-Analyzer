import requests 
from django.core.management.base import BaseCommand
from analytics.models import Company, Sector


class Command(BaseCommand):
    help = 'Fetches Companies and Sectors from API 8'
    
    def handle(self, *args, **kwargs):
        self.stdout.write("Fetching Company List")

        url = "https://api.askanalyst.com.pk/api/companylistwithids"
        headers = {'User-Agent': 'Mozilla/5.0'}

        try:
            response = requests.get(url, headers=headers)
            if response.status_code !=200:
                self.stdout.write(self.style.ERROR(f"❌ API Error: {response.status_code}"))
                return
            
            data = response.json()
            total = len(data)
            self.stdout.write(f"📦 Found {total} companies. Processing...")

            for item in data:
                sector_obj = None
                s_id = item.get('sector_id')
                s_name = item.get('sector')

                if s_id:
                    sector_obj, created = Sector.objects.update_or_create(
                        sector_id = s_id,
                        defaults={'name':s_name}
                    )
                c_id = item.get('id')
                c_ticker = item.get('label2') 
                c_name = item.get('name')
                c_logo = item.get('image')

                
                Company.objects.update_or_create(
                    company_id=c_id,
                    defaults={
                        'ticker': c_ticker,
                        'name': c_name,
                        'sector': sector_obj, # Foreign Key Link
                        'logo_url': c_logo
                    }
                )
            self.stdout.write(self.style.SUCCESS(f"✅ Successfully loaded {total} companies!"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"💥 Error: {str(e)}"))