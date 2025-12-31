import requests

def get_crypto_price(symbol):
    try:
        # استفاده از API رایگان برای گرفتن قیمت لحظه‌ای
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol.upper()}USDT"
        response = requests.get(url)
        data = response.json()
        # تبدیل به float و گرد کردن برای خوانایی بهتر
        return round(float(data['price']), 2)
    except Exception:
        return None

def handle_trader_request(text):
    if "قیمت" in text:
        if "بیت" in text or "btc" in text.lower():
            price = get_crypto_price("BTC")
            return f"📈 قیمت لحظه‌ای بیت‌کوین: ${price:,}" if price else "خطا در دریافت قیمت BTC."
        
        if "اتریوم" in text or "eth" in text.lower():
            price = get_crypto_price("ETH")
            return f"💎 قیمت لحظه‌ای اتریوم: ${price:,}" if price else "خطا در دریافت قیمت ETH."

    return "📊 برای تحلیل دقیق‌تر، لطفاً جفت ارز مورد نظر را اعلام کنید. من می‌توانم قیمت‌های لحظه‌ای را از صرافی‌های جهانی استخراج کنم."
