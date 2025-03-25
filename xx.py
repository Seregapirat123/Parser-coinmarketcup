import requests
from bs4 import BeautifulSoup
import os

def save_coinmarketcap_html(url, filename='coinmarketcap.html'):
    """Сохраняет HTML страницу CoinMarketCap в файл"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"HTML успешно сохранен в файл {filename}")
        return True
    except Exception as e:
        print(f"Ошибка при сохранении HTML: {e}")
        return False

def parse_coinmarketcap_from_file(filename='coinmarketcap.html', limit=100):
    """Парсит данные о криптовалютах из сохраненного HTML файла"""
    if not os.path.exists(filename):
        print(f"Файл {filename} не найден!")
        return []
    
    with open(filename, 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'html.parser')
    rows = soup.select('tbody tr')
    
    cryptocurrencies = []
    count = 0
    
    for row in rows:
        # Пропускаем строки с классом sc-902a96b4-0 (это дополнительные строки)
        if 'sc-902a96b4-0' in row.get('class', []):
            continue
            
        try:
            # Извлекаем данные из строки
            rank = row.select_one('td:nth-of-type(2) p').text.strip()
            
            name_tag = row.select_one('.coin-item-name')
            symbol_tag = row.select_one('.coin-item-symbol')
            name = name_tag.text.strip() if name_tag else None
            symbol = symbol_tag.text.strip() if symbol_tag else None
            
            price = row.select_one('td:nth-of-type(4) div span').text.strip()
            
            # Изменение цены за 1ч, 24ч и 7д
            change_1h = row.select_one('td:nth-of-type(5) span').text.strip()
            change_24h = row.select_one('td:nth-of-type(6) span').text.strip()
            change_7d = row.select_one('td:nth-of-type(7) span').text.strip()
            
            market_cap = row.select_one('td:nth-of-type(8) p span.sc-11478e5d-0').text.strip()
            
            volume_24h = row.select_one('td:nth-of-type(9) a p').text.strip()
            volume_24h_coin = row.select_one('td:nth-of-type(9) div p').text.strip()
            
            circulating_supply = row.select_one('.circulating-supply-value').text.strip().split()[0]
            
            cryptocurrencies.append({
                'rank': rank,
                'name': name,
                'symbol': symbol,
                'price': price,
                'change_1h': change_1h,
                'change_24h': change_24h,
                'change_7d': change_7d,
                'market_cap': market_cap,
                'volume_24h': volume_24h,
                'volume_24h_coin': volume_24h_coin,
                'circulating_supply': circulating_supply
            })
            
            count += 1
            if count >= limit:
                break
                
        except Exception as e:
            # Пропускаем строки, которые не удалось распарсить
            continue
    
    return cryptocurrencies

def save_to_csv(data, filename='cryptocurrencies.csv'):
    """Сохраняет данные в CSV файл"""
    import csv
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['rank', 'name', 'symbol', 'price', 'change_1h', 'change_24h', 
                     'change_7d', 'market_cap', 'volume_24h', 'volume_24h_coin', 'circulating_supply']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for coin in data:
            writer.writerow(coin)
    
    print(f"Данные сохранены в {filename}")

def main():
    # URL страницы CoinMarketCap
    url = 'https://coinmarketcap.com'
    
    # 1. Сохраняем HTML страницу в файл
    if save_coinmarketcap_html(url):
        # 2. Парсим данные из сохраненного файла (100 криптовалют)
        data = parse_coinmarketcap_from_file(limit=100)
        
        # 3. Сохраняем в CSV
        save_to_csv(data)
        
        # 4. Выводим первые 10 записей для примера
        print(f"\nНайдено {len(data)} криптовалют. Первые 10:\n")
        
        for i, coin in enumerate(data[:10]):
            print(f"{coin['rank']}. {coin['name']} ({coin['symbol']})")
            print(f"Цена: {coin['price']}")
            print(f"Изменение (1ч/24ч/7д): {coin['change_1h']} / {coin['change_24h']} / {coin['change_7d']}")
            print(f"Рыночная капитализация: {coin['market_cap']}")
            print(f"Объем (24ч): {coin['volume_24h']} ({coin['volume_24h_coin']})")
            print(f"Обращающееся предложение: {coin['circulating_supply']} {coin['symbol']}")
            print("-" * 50)

if __name__ == "__main__":
    main()