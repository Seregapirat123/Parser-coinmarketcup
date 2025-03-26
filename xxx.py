import scrapy
from scrapy.crawler import CrawlerProcess
import csv
import os
import logging
from scrapy.utils.project import get_project_settings

class CoinMarketCapSpider(scrapy.Spider):
    name = 'coinmarketcap'
    start_urls = ['https://coinmarketcap.com/']
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 1,
        'FEEDS': {
            'cryptocurrencies.csv': {
                'format': 'csv',
                'fields': ['rank', 'name', 'symbol', 'price', 'change_1h', 'change_24h',
                         'change_7d', 'market_cap', 'volume_24h', 'circulating_supply'],
                'overwrite': True
            }
        },
        'LOG_ENABLED': False,  # Полностью отключаем логирование
        'ROBOTSTXT_OBEY': False,
        'HTTPCACHE_ENABLED': False,
        'RETRY_TIMES': 3,
        'COOKIES_ENABLED': True,
    }
    
    def start_requests(self):
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/'
        }
        
        for url in self.start_urls:
            yield scrapy.Request(url, headers=headers, callback=self.parse)
    
    def parse(self, response):
        rows = response.css('table tbody tr')
        
        for row in rows[:100]:
            try:
                yield {
                    'rank': row.css('td:nth-child(2)::text').get('').strip(),
                    'name': row.css('td:nth-child(3) p:first-child::text').get('').strip(),
                    'symbol': row.css('td:nth-child(3) p:last-child::text').get('').strip(),
                    'price': row.css('td:nth-child(4) span::text').get('').strip(),
                    'change_1h': row.css('td:nth-child(5) span::text').get('').strip(),
                    'change_24h': row.css('td:nth-child(6) span::text').get('').strip(),
                    'change_7d': row.css('td:nth-child(7) span::text').get('').strip(),
                    'market_cap': row.css('td:nth-child(8) p::text').get('').strip(),
                    'volume_24h': row.css('td:nth-child(9) p::text').get('').strip(),
                    'circulating_supply': row.css('td:nth-child(10) p::text').get('').strip(),
                }
            except Exception as e:
                continue

def print_first_10_records():
    """Выводит первые 10 записей из CSV файла"""
    if not os.path.exists('cryptocurrencies.csv'):
        print("Файл cryptocurrencies.csv не найден!")
        return
        
    with open('cryptocurrencies.csv', 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        data = list(reader)
        
    print(f"\nНайдено {len(data)} криптовалют. Первые 10:\n")
    
    for i, coin in enumerate(data[:10]):
        print(f"{coin.get('rank', 'N/A')}. {coin.get('name', 'N/A')} ({coin.get('symbol', 'N/A')})")
        print(f"Цена: {coin.get('price', 'N/A')}")
        print(f"Изменение (1ч/24ч/7д): {coin.get('change_1h', 'N/A')} / {coin.get('change_24h', 'N/A')} / {coin.get('change_7d', 'N/A')}")
        print(f"Рыночная капитализация: {coin.get('market_cap', 'N/A')}")
        print(f"Объем (24ч): {coin.get('volume_24h', 'N/A')}")
        print(f"Обращающееся предложение: {coin.get('circulating_supply', 'N/A')}")
        print("-" * 50)

def main():
    # Отключаем логирование Scrapy полностью
    logging.getLogger('scrapy').propagate = False
    
    # Удаляем старый CSV файл, если он существует
    if os.path.exists('cryptocurrencies.csv'):
        os.remove('cryptocurrencies.csv')
    
    # Настройки для Scrapy
    settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'DOWNLOAD_DELAY': 3,
        'LOG_ENABLED': False  # Дублируем отключение логов для надёжности
    }
    
    # Запускаем паука
    process = CrawlerProcess(settings=settings)
    process.crawl(CoinMarketCapSpider)
    process.start()
    
    # Выводим первые 10 записей
    print_first_10_records()

if __name__ == "__main__":
    main()