from __future__ import annotations

import inspect
from datetime import datetime, timedelta
from typing import Callable, Optional, Tuple

from bithumb_usdt import get_bithumb_btc, get_bithumb_usdt
from mybank import (
    get_hanabank_exchange_rate,
    get_investing_exchange_rate,
    get_kbstar_exchange_rate,
    get_shinhan_exchange_rate,
)

MAX_LOOKBACK_DAYS = 7


def format_datetime(date_str: Optional[str], time_str: Optional[str]) -> str:
    """YYYYMMDD와 HHMMSS를 읽기 쉬운 형식으로 변환"""
    if date_str and time_str:
        try:
            year = date_str[:4]
            month = date_str[4:6]
            day = date_str[6:8]
            hour = time_str[:2]
            minute = time_str[2:4]
            second = time_str[4:6]
            return f"{year}-{month}-{day} {hour}:{minute}:{second}"
        except Exception:
            return f"{date_str} {time_str}"
    return "-"


def iterate_business_days(start_date: datetime, max_days: int):
    """가까운 과거 영업일을 순회"""
    candidate = start_date
    yielded = 0
    while yielded < max_days:
        if candidate.weekday() < 5:  # 월(0)~금(4)
            yield candidate
            yielded += 1
        candidate = candidate - timedelta(days=1)


def supports_target_date(fetcher: Callable) -> bool:
    """주어진 fetcher가 target_date 인자를 지원하는지 확인"""
    try:
        sig = inspect.signature(fetcher)
    except (ValueError, TypeError):
        return False

    if 'target_date' in sig.parameters:
        return True

    params = list(sig.parameters.values())
    if not params:
        return False

    first = params[0]
    return first.kind in (
        inspect.Parameter.POSITIONAL_ONLY,
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
    )


def fetch_with_fallback(fetcher: Callable[[datetime], Optional[dict]], max_days: int = MAX_LOOKBACK_DAYS):
    """
    지정된 fetcher를 사용해 최근 영업일 순으로 조회하며,
    데이터가 없으면 전 영업일 데이터까지 탐색
    """
    today = datetime.now().date()

    if not supports_target_date(fetcher):
        try:
            result = fetcher()
        except Exception as exc:
            print(f"{fetcher.__name__} 조회 실패(현재일자): {exc}")
            return None

        if result:
            result['is_previous'] = False
        return result

    for target_date in iterate_business_days(datetime.now(), max_days):
        try:
            result = fetcher(target_date)
        except Exception as exc:
            print(f"{fetcher.__name__} 조회 실패({target_date.date()}): {exc}")
            continue

        has_rates = result and result.get('USD') and result.get('JPY')
        if has_rates:
            result['is_previous'] = target_date.date() != today
            return result
    return None


def load_exchange_rates() -> Tuple[list, Optional[dict], Optional[dict], Optional[dict]]:
    """환율 데이터 로딩"""
    bank_data = []
    investing_data = None
    bithumb_data = None

    shinhan = fetch_with_fallback(get_shinhan_exchange_rate)
    if shinhan:
        bank_data.append({
            '은행': '신한은행',
            '조회일시': format_datetime(shinhan['date'], shinhan['time']),
            '고시회차': f"{shinhan['round']}회차",
            'USD_raw': shinhan['USD'],
            'JPY_raw': shinhan['JPY'],
            'is_previous': shinhan.get('is_previous', False)
        })

    kbstar = fetch_with_fallback(get_kbstar_exchange_rate)
    if kbstar:
        bank_data.append({
            '은행': '국민은행',
            '조회일시': format_datetime(kbstar['date'], kbstar['time']),
            '고시회차': f"{kbstar['round']}회차",
            'USD_raw': kbstar['USD'],
            'JPY_raw': kbstar['JPY'],
            'is_previous': kbstar.get('is_previous', False)
        })

    hana = fetch_with_fallback(get_hanabank_exchange_rate)
    if hana:
        bank_data.append({
            '은행': '하나은행',
            '조회일시': format_datetime(hana['date'], hana['time']),
            '고시회차': f"{hana['round']}회차",
            'USD_raw': hana['USD'],
            'JPY_raw': hana['JPY'],
            'is_previous': hana.get('is_previous', False)
        })

    investing = get_investing_exchange_rate()
    if investing:
        investing_data = {
            'datetime': format_datetime(investing['date'], investing['time']),
            'USD_KRW': investing['USD_KRW'],
            'JPY_KRW': investing['JPY_KRW'] * 100  # 100엔당으로 변환
        }

    bithumb = get_bithumb_usdt()
    if bithumb:
        bithumb_data = {
            'price': bithumb['price'],
            'change_rate': bithumb['change_rate'],
            'change_amount': bithumb['change_amount']
        }

    btc_data = None
    btc = get_bithumb_btc()
    if btc:
        btc_data = {
            'price': btc['price'],
            'change_rate': btc['change_rate'],
            'change_amount': btc['change_amount']
        }

    return bank_data, investing_data, bithumb_data, btc_data

