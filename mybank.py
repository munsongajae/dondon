"""
신한은행, 국민은행, Investing.com 환율 정보 통합 크롤러

참고:
- 신한은행: 공식 API 사용
- 국민은행: HTML 파싱
- 하나은행: AJAX POST 요청 사용
- Investing.com: 참고용
"""
import requests
import json
import re
from datetime import datetime
from bs4 import BeautifulSoup


def get_shinhan_exchange_rate():
    """
    신한은행 API에서 환율 정보 조회
    """
    url = 'https://bank.shinhan.com/serviceEndpoint/httpDigital'

    headers = {
        'Accept': 'application/json',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json; charset="UTF-8"',
        'Origin': 'https://bank.shinhan.com',
        'Referer': 'https://bank.shinhan.com/index.jsp',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
        'submissionid': 'sbm_F3730'
    }

    # 오늘 날짜 (YYYYMMDD)
    today_str = datetime.now().strftime('%Y%m%d')

    data = {
        "dataBody": {
            "ricInptRootInfo": {
                "serviceType": "GU",
                "serviceCode": "F3730",
                "nextServiceCode": "",
                "pkcs7Data": "",
                "signCode": "",
                "signData": "",
                "useSign": "",
                "useCert": "",
                "permitMultiTransaction": "",
                "keepTransactionSession": "",
                "skipErrorMsg": "",
                "mode": "",
                "language": "ko",
                "exe2e": "",
                "hideProcess": "",
                "clearTarget": "",
                "callBack": "shbObj.fncF3730Callback",
                "exceptionCallback": "",
                "requestMessage": "",
                "responseMessage": "",
                "serviceOption": "",
                "pcLog": "",
                "preInqForMulti": "",
                "makesum": "",
                "removeIndex": "",
                "redirectUrl": "",
                "preInqKey": "",
                "_multi_transfer_": "",
                "_multi_transfer_count_": "",
                "_multi_transfer_amt_": "",
                "userCallback": "",
                "menuCode": "",
                "certtype": "",
                "fromMulti": "",
                "fromMultiIdx": "",
                "isRule": "N",
                "webUri": "/index.jsp",
                "gubun": "",
                "tmpField2": ""
            },
            "조회구분": "",
            "조회일자": today_str,
            "고시회차": 0,
            "조회일자_display": "",
            "startPoint": "",
            "endPoint": ""
        },
        "dataHeader": {
            "trxCd": "RSHRC0213A01",
            "language": "ko",
            "subChannel": "49",
            "channelGbn": "D0"
        }
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        data_body = result.get('dataBody', {})
        
        # 기본 정보 추출
        announce_date = data_body.get('고시일자', '')
        announce_time = data_body.get('고시시간', '')
        announce_round = data_body.get('고시회차', '')
        
        rates_list = data_body.get('R_RIBF3730_1', [])
        
        usd_rate = None
        jpy_rate = None
        
        for item in rates_list:
            currency_code = item.get('통화CODE')
            if currency_code == 'USD':
                usd_rate = item.get('매매기준환율')
            elif currency_code == 'JPY':
                jpy_rate = item.get('매매기준환율')
        
        return {
            'bank': '신한은행',
            'date': announce_date,
            'time': announce_time,
            'round': announce_round,
            'USD': usd_rate,
            'JPY': jpy_rate
        }

    except Exception as e:
        print(f"신한은행 조회 오류: {e}")
        return None


def get_kbstar_exchange_rate():
    """
    국민은행(KB Star) 환율 정보 크롤링
    """
    url = "https://obank.kbstar.com/quics?page=C101423"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 환율등록일시(회차) 추출 - 4번째 테이블
        announce_datetime = None
        announce_time = None
        announce_round = None
        
        tables = soup.find_all('table')
        
        # 4번째 테이블 (인덱스 3)에서 날짜/시간 정보 추출
        if len(tables) >= 4:
            datetime_table = tables[3]  # 4번째 테이블
            tbody = datetime_table.find('tbody')
            if tbody:
                first_tr = tbody.find('tr')
                if first_tr:
                    first_td = first_tr.find('td')
                    if first_td:
                        # 예: "2025.11.27 19:27:13 (584회차)"
                        text = first_td.text.strip()
                        import re
                        match = re.match(r'(\d{4})\.(\d{2})\.(\d{2})\s+(\d{2}):(\d{2}):(\d{2})\s+\((\d+)회차\)', text)
                        if match:
                            year, month, day, hour, minute, second, round_num = match.groups()
                            announce_datetime = f"{year}{month}{day}"
                            announce_time = f"{hour}{minute}{second}"
                            announce_round = round_num
        
        # USD, JPY 환율 추출 - 5번째 테이블
        usd_rate = None
        jpy_rate = None
        
        if len(tables) >= 5:
            rate_table = tables[4]  # 5번째 테이블
            tbody = rate_table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
                for row in rows:
                    tds = row.find_all('td')
                    if len(tds) >= 3:
                        # 첫 번째 td에서 통화 코드 찾기
                        currency_code = tds[0].text.strip()
                        if currency_code == 'USD':
                            # 매매기준율은 3번째 td (인덱스 2)
                            usd_rate = tds[2].text.strip().replace(',', '')
                        elif currency_code == 'JPY':
                            jpy_rate = tds[2].text.strip().replace(',', '')
        
        return {
            'bank': '국민은행',
            'date': announce_datetime,
            'time': announce_time,
            'round': announce_round,
            'USD': float(usd_rate) if usd_rate else None,
            'JPY': float(jpy_rate) if jpy_rate else None
        }
        
    except Exception as e:
        print(f"국민은행 조회 오류: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_hanabank_exchange_rate():
    """
    하나은행 환율 정보 크롤링 (POST 요청 사용)
    """
    url = "https://www.kebhana.com/cms/rate/wpfxd651_01i_01.do"
    
    headers = {
        'Accept': 'text/javascript, text/html, application/xml, text/xml, */*',
        'Accept-Language': 'ko-KR,ko;q=0.9',
        'Connection': 'keep-alive',
        'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://www.kebhana.com',
        'Referer': 'https://www.kebhana.com/cms/rate/index.do?contentUrl=/cms/rate/wpfxd651_01i.do',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'X-Prototype-Version': '1.5.1.1',
        'X-Requested-With': 'XMLHttpRequest',
    }
    
    today = datetime.now()
    date_str = today.strftime('%Y%m%d')
    date_formatted = today.strftime('%Y-%m-%d')
    
    data = {
        'ajax': 'true',
        'curCd': '',
        'tmpInqStrDt': date_formatted,
        'pbldDvCd': '3',  # 3 = 현재/최종
        'pbldSqn': '',
        'inqStrDt': date_str,
        'inqKindCd': '1',
        'hid_key_data': '',
        'hid_enc_data': '',
        'requestTarget': 'searchContentDiv'
    }
    
    try:
        response = requests.post(url, headers=headers, data=data, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 고시일시/회차 추출
        announce_datetime = None
        announce_time = None
        announce_round = None
        
        # 고시일시 패턴: "2025년11월27일 19시36분00초 (731회차)"
        datetime_pattern = r'(\d{4})년(\d{2})월(\d{2})일.*?(\d{2})시(\d{2})분(\d{2})초.*?\((\d+)회차\)'
        matches = re.findall(datetime_pattern, response.text, re.DOTALL)
        if matches:
            year, month, day, hour, minute, second, round_num = matches[0]
            announce_datetime = f"{year}{month}{day}"
            announce_time = f"{hour}{minute}{second}"
            announce_round = round_num
        
        # USD, JPY 환율 추출
        usd_rate = None
        jpy_rate = None
        
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if not cells or len(cells) < 9:
                    continue
                
                # 첫 번째 셀에서 통화 확인
                first_cell = cells[0].text.strip()
                
                # 매매기준율은 9번째 셀 (인덱스 8)
                if '미국 USD' in first_cell or first_cell == '미국 USD':
                    rate_text = cells[8].text.strip().replace(',', '')
                    try:
                        usd_rate = float(rate_text)
                    except:
                        pass
                
                elif '일본 JPY' in first_cell or 'JPY (100)' in first_cell:
                    rate_text = cells[8].text.strip().replace(',', '')
                    try:
                        jpy_rate = float(rate_text)
                    except:
                        pass
        
        return {
            'bank': '하나은행',
            'date': announce_datetime,
            'time': announce_time,
            'round': announce_round,
            'USD': usd_rate,
            'JPY': jpy_rate
        }
        
    except Exception as e:
        print(f"하나은행 조회 오류: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_investing_exchange_rate():
    """
    Investing.com에서 환율 정보 크롤링
    """
    url = "https://kr.investing.com/currencies/exchange-rates-table"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 환율표 테이블 찾기
        table = soup.find('table', {'id': 'exchange_rates_1'})
        
        if not table:
            print("환율 테이블을 찾을 수 없습니다.")
            return None
        
        # USD/KRW 환율
        usd_row = table.find('tr', {'id': 'pair_12'})
        usd_krw = None
        if usd_row:
            usd_krw_td = usd_row.find('td', {'id': 'last_12_28'})
            if usd_krw_td:
                usd_krw = usd_krw_td.text.strip().replace(',', '')
        
        # JPY/KRW 환율 (100엔 기준)
        jpy_row = table.find('tr', {'id': 'pair_2'})
        jpy_krw = None
        if jpy_row:
            jpy_krw_td = jpy_row.find('td', {'id': 'last_2_28'})
            if jpy_krw_td:
                jpy_krw = jpy_krw_td.text.strip().replace(',', '')
        
        # 현재 시간
        current_time = datetime.now()
        
        return {
            'source': 'Investing.com',
            'date': current_time.strftime('%Y%m%d'),
            'time': current_time.strftime('%H%M%S'),
            'USD_KRW': float(usd_krw) if usd_krw else None,
            'JPY_KRW': float(jpy_krw) if jpy_krw else None
        }
        
    except Exception as e:
        print(f"Investing.com 조회 오류: {e}")
        return None


def main():
    """
    메인 함수 - 신한은행, 국민은행, 하나은행, Investing.com 환율 정보 출력
    """
    print("=" * 60)
    print("환율 정보 조회")
    print("=" * 60)
    
    # 신한은행 환율 조회
    print("\n[신한은행]")
    shinhan_data = get_shinhan_exchange_rate()
    if shinhan_data:
        print(f"고시날짜: {shinhan_data['date']}")
        print(f"고시시간: {shinhan_data['time']}")
        print(f"고시회차: {shinhan_data['round']}")
        print(f"USD 매매기준환율: {shinhan_data['USD']:,.2f}")
        print(f"JPY(100엔) 매매기준환율: {shinhan_data['JPY']:,.2f}")
    
    # 국민은행 환율 조회
    print("\n[국민은행]")
    kbstar_data = get_kbstar_exchange_rate()
    if kbstar_data:
        print(f"고시날짜: {kbstar_data['date']}")
        print(f"고시시간: {kbstar_data['time']}")
        print(f"고시회차: {kbstar_data['round']}회차")
        if kbstar_data['USD']:
            print(f"USD 매매기준환율: {kbstar_data['USD']:,.2f}")
        if kbstar_data['JPY']:
            print(f"JPY(100엔) 매매기준환율: {kbstar_data['JPY']:,.2f}")
    
    # 하나은행 환율 조회
    print("\n[하나은행]")
    hana_data = get_hanabank_exchange_rate()
    if hana_data:
        print(f"고시날짜: {hana_data['date']}")
        print(f"고시시간: {hana_data['time']}")
        print(f"고시회차: {hana_data['round']}회차")
        if hana_data['USD']:
            print(f"USD 매매기준환율: {hana_data['USD']:,.2f}")
        if hana_data['JPY']:
            print(f"JPY(100엔) 매매기준환율: {hana_data['JPY']:,.2f}")
    
    # Investing.com 환율 조회
    print("\n[Investing.com]")
    investing_data = get_investing_exchange_rate()
    if investing_data:
        print(f"조회 시간: {investing_data['date']} {investing_data['time']}")
        print(f"USD/KRW: {investing_data['USD_KRW']:,.4f}")
        print(f"JPY(100엔)/KRW: {investing_data['JPY_KRW']:,.4f}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
