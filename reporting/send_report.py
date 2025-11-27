from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from typing import List

import requests

from reporting.exchange_fetcher import format_datetime, load_exchange_rates


KAKAO_MEMO_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
STREAMLIT_APP_URL = "https://dondon.streamlit.app/"


def build_report_lines() -> List[str]:
    bank_data, investing_data, bithumb_data, btc_data = load_exchange_rates()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [f"[환율 리포트] {now_str} 기준"]

    if investing_data:
        lines.append(
            f"- Investing USD: ₩{investing_data['USD_KRW']:,.2f}, "
            f"JPY(100엔): ₩{investing_data['JPY_KRW']:,.2f}"
        )

    if bithumb_data and investing_data and investing_data['USD_KRW']:
        kimchi = ((bithumb_data['price'] - investing_data['USD_KRW']) / investing_data['USD_KRW']) * 100
        lines.append(
            f"- 빗썸 USDT: ₩{bithumb_data['price']:,.0f} ({bithumb_data['change_rate']:+.2f}%), "
            f"김치프리미엄 {kimchi:+.2f}%"
        )
    elif bithumb_data:
        lines.append(
            f"- 빗썸 USDT: ₩{bithumb_data['price']:,.0f} ({bithumb_data['change_rate']:+.2f}%)"
        )

    if btc_data:
        lines.append(
            f"- 빗썸 BTC: ₩{btc_data['price']:,.0f} ({btc_data['change_rate']:+.2f}%)"
        )

    if bank_data:
        lines.append("은행별 매매기준환율")
        for item in bank_data:
            marker = " (전영업일)" if item.get("is_previous") else ""
            usd = f"{item['USD_raw']:,.2f}"
            jpy = f"{item['JPY_raw']:,.2f}"
            timestamp = format_datetime_str(item.get("조회일시")) or "-"
            lines.append(
                f"· {item['은행']}{marker}: USD {usd}, JPY(100엔) {jpy} / {timestamp} {item['고시회차']}"
            )
    else:
        lines.append("은행 환율 데이터를 가져오지 못했습니다.")

    lines.append(f"상세보기: {STREAMLIT_APP_URL}")
    return lines


def format_datetime_str(value: str | None) -> str:
    if not value or value == "-":
        return "-"
    return value


def send_kakao_message(message: str, *, dry_run: bool = False):
    if dry_run:
        print(message)
        return

    access_token = os.getenv("KAKAO_ACCESS_TOKEN")
    if not access_token:
        raise RuntimeError("환경 변수 KAKAO_ACCESS_TOKEN이 필요합니다. Kakao OAuth로 발급한 사용자의 액세스 토큰을 설정하세요.")

    payload = {
        "object_type": "text",
        "text": message,
        "link": {
            "web_url": STREAMLIT_APP_URL,
            "mobile_web_url": STREAMLIT_APP_URL,
        },
        "button_title": "환율 정보 보기",
    }

    response = requests.post(
        KAKAO_MEMO_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-type": "application/x-www-form-urlencoded;charset=utf-8",
        },
        data={
            "template_object": json.dumps(payload, ensure_ascii=False),
        },
        timeout=10,
    )

    if response.status_code != 200:
        raise RuntimeError(f"Kakao API 오류: {response.status_code} {response.text}")


def main():
    parser = argparse.ArgumentParser(description="환율 정보를 카카오톡으로 전송합니다.")
    parser.add_argument("--dry-run", action="store_true", help="메시지를 전송하지 않고 출력만 합니다.")
    args = parser.parse_args()

    lines = build_report_lines()
    message = "\n".join(lines)
    send_kakao_message(message, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

