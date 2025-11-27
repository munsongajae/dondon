import requests
from bs4 import BeautifulSoup
import json

def get_bithumb_usdt():
    """
    빗썸에서 테더(USDT) 가격과 변동률 조회
    """
    # 빗썸 공개 API 사용
    url = "https://api.bithumb.com/public/ticker/USDT_KRW"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data['status'] == '0000':
            ticker_data = data['data']
            
            # 현재가
            closing_price = float(ticker_data['closing_price'])
            
            # 전일대비 변동률 계산
            prev_closing_price = float(ticker_data['prev_closing_price'])
            if prev_closing_price > 0:
                change_rate = ((closing_price - prev_closing_price) / prev_closing_price) * 100
            else:
                change_rate = 0
            
            # 변동액
            change_amount = closing_price - prev_closing_price
            
            return {
                'price': closing_price,
                'change_rate': change_rate,
                'change_amount': change_amount,
                'prev_price': prev_closing_price,
                'high_price': float(ticker_data['max_price']),
                'low_price': float(ticker_data['min_price']),
                'volume': float(ticker_data['units_traded_24H'])
            }
        else:
            print(f"빗썸 API 오류: {data.get('message', '알 수 없는 오류')}")
            return None
            
    except Exception as e:
        print(f"빗썸 조회 오류: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_bithumb_btc():
    """
    빗썸에서 비트코인(BTC) 가격과 변동률 조회
    """
    url = "https://api.bithumb.com/public/ticker/BTC_KRW"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data['status'] == '0000':
            ticker_data = data['data']
            
            # 현재가
            closing_price = float(ticker_data['closing_price'])
            
            # 전일대비 변동률 계산
            prev_closing_price = float(ticker_data['prev_closing_price'])
            if prev_closing_price > 0:
                change_rate = ((closing_price - prev_closing_price) / prev_closing_price) * 100
            else:
                change_rate = 0
            
            # 변동액
            change_amount = closing_price - prev_closing_price
            
            return {
                'price': closing_price,
                'change_rate': change_rate,
                'change_amount': change_amount,
                'prev_price': prev_closing_price,
                'high_price': float(ticker_data['max_price']),
                'low_price': float(ticker_data['min_price']),
                'volume': float(ticker_data['units_traded_24H'])
            }
        else:
            print(f"빗썸 BTC API 오류: {data.get('message', '알 수 없는 오류')}")
            return None
            
    except Exception as e:
        print(f"빗썸 BTC 조회 오류: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("=== 빗썸 USDT 가격 조회 ===\n")
    
    usdt_data = get_bithumb_usdt()
    
    if usdt_data:
        print(f"💵 테더(USDT) 가격: ₩{usdt_data['price']:,.0f}")
        print(f"📊 변동률: {usdt_data['change_rate']:+.2f}%")
        print(f"📈 변동액: {usdt_data['change_amount']:+,.0f}원")
        print(f"📅 전일종가: ₩{usdt_data['prev_price']:,.0f}")
        print(f"🔺 최고가: ₩{usdt_data['high_price']:,.0f}")
        print(f"🔻 최저가: ₩{usdt_data['low_price']:,.0f}")
        print(f"📦 24시간 거래량: {usdt_data['volume']:,.2f} USDT")
    
    print("\n=== 빗썸 BTC 가격 조회 ===\n")
    
    btc_data = get_bithumb_btc()
    
    if btc_data:
        print(f"₿ 비트코인(BTC) 가격: ₩{btc_data['price']:,.0f}")
        print(f"📊 변동률: {btc_data['change_rate']:+.2f}%")
        print(f"📈 변동액: {btc_data['change_amount']:+,.0f}원")
        print(f"📅 전일종가: ₩{btc_data['prev_price']:,.0f}")
        print(f"🔺 최고가: ₩{btc_data['high_price']:,.0f}")
        print(f"🔻 최저가: ₩{btc_data['low_price']:,.0f}")
        print(f"📦 24시간 거래량: {btc_data['volume']:,.4f} BTC")
