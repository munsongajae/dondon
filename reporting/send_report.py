from __future__ import annotations

import argparse
import asyncio
import json
import os
from datetime import datetime
from typing import List

import requests
from telegram import Bot

from reporting.exchange_fetcher import format_datetime, load_exchange_rates


KAKAO_MEMO_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
STREAMLIT_APP_URL = "https://dondon.streamlit.app/"


def build_report_lines() -> List[str]:
    bank_data, investing_data, bithumb_data, btc_data = load_exchange_rates()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [f"[실시간 환율] {now_str}"]

    usd_base = investing_data['USD_KRW'] if investing_data else None
    jpy_base = investing_data['JPY_KRW'] if investing_data else None

    if investing_data:
        lines.append("")
        lines.append(f"{investing_data['USD_KRW']:,.2f}")
        lines.append(f"{investing_data['JPY_KRW']:,.2f}")

    # Helper to find bank entries
    def find_bank(bank_name: str):
        for item in bank_data:
            if item['은행'] == bank_name:
                return item
        return None

    lines.append("")
    lines.append("[달러 환율]")
    for bank in ["신한은행", "국민은행", "하나은행"]:
        item = find_bank(bank)
        if not item:
            lines.append(f"{bank.split('은행')[0]}  -")
            continue
        diff_text = ""
        if usd_base:
            diff = usd_base - item['USD_raw']
            diff_text = f" ({diff:+.2f})"
        lines.append(
            f"{bank.split('은행')[0]}  {item['USD_raw']:,.2f}{diff_text} {item['고시회차']}"
        )

    lines.append("")
    lines.append("[엔화 환율]")
    for bank in ["신한은행", "국민은행", "하나은행"]:
        item = find_bank(bank)
        if not item:
            lines.append(f"{bank.split('은행')[0]}  -")
            continue
        diff_text = ""
        if jpy_base:
            diff = jpy_base - item['JPY_raw']
            diff_text = f" ({diff:+.2f})"
        lines.append(
            f"{bank.split('은행')[0]} {item['JPY_raw']:,.2f}{diff_text} {item['고시회차']}"
        )

    lines.append("")
    lines.append("[테더]")
    if bithumb_data:
        kimchi_text = ""
        if usd_base:
            kimchi = ((bithumb_data['price'] - usd_base) / usd_base) * 100
            kimchi_text = f" (김프 {kimchi:+.2f}%)"
        lines.append(f"{bithumb_data['price']:,.0f}{kimchi_text}")
    else:
        lines.append("-")

    lines.append("")
    lines.append("[비트]")
    if btc_data:
        lines.append(f"{btc_data['price']:,.0f}")
    else:
        lines.append("-")

    lines.append("")
    lines.append(f"상세: {STREAMLIT_APP_URL}")
    return lines


def format_datetime_str(value: str | None) -> str:
    if not value or value == "-":
        return "-"
    return value


def refresh_access_token(refresh_token: str) -> str:
    """refresh token을 사용해 새로운 access token 발급"""
    response = requests.post(
        KAKAO_TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "client_id": os.getenv("KAKAO_REST_API_KEY", ""),
            "refresh_token": refresh_token,
        },
        timeout=10,
    )
    if response.status_code != 200:
        raise RuntimeError(f"토큰 갱신 실패: {response.status_code} {response.text}")
    data = response.json()
    return data["access_token"]


def send_kakao_message(message: str, *, dry_run: bool = False):
    if dry_run:
        print(message)
        return

    access_token = os.getenv("KAKAO_ACCESS_TOKEN")
    refresh_token = os.getenv("KAKAO_REFRESH_TOKEN")
    
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

    # access token이 만료된 경우 refresh token으로 갱신 후 재시도
    if response.status_code == 401 and refresh_token:
        try:
            new_access_token = refresh_access_token(refresh_token)
            # 갱신된 토큰으로 재시도
            response = requests.post(
                KAKAO_MEMO_URL,
                headers={
                    "Authorization": f"Bearer {new_access_token}",
                    "Content-type": "application/x-www-form-urlencoded;charset=utf-8",
                },
                data={
                    "template_object": json.dumps(payload, ensure_ascii=False),
                },
                timeout=10,
            )
            if response.status_code == 200:
                print(f"[알림] Access token이 자동으로 갱신되었습니다. 다음 실행을 위해 환경 변수 KAKAO_ACCESS_TOKEN을 업데이트하세요: {new_access_token}")
        except Exception as e:
            raise RuntimeError(f"토큰 갱신 후 재시도 실패: {e}")

    if response.status_code != 200:
        raise RuntimeError(f"Kakao API 오류: {response.status_code} {response.text}")


async def send_telegram_message_async(message: str, *, dry_run: bool = False):
    """텔레그램 봇을 통해 메시지 전송 (비동기)"""
    if dry_run:
        print("[텔레그램] " + message)
        return

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token:
        raise RuntimeError("환경 변수 TELEGRAM_BOT_TOKEN이 필요합니다. BotFather에서 발급받은 봇 토큰을 설정하세요.")
    if not chat_id:
        raise RuntimeError("환경 변수 TELEGRAM_CHAT_ID가 필요합니다. 봇에게 메시지를 보낼 사용자의 chat_id를 설정하세요.")

    # 텔레그램은 마크다운 형식 지원, 링크는 HTML 형식으로
    message_with_link = f"{message}\n\n상세: {STREAMLIT_APP_URL}"
    
    bot = Bot(token=bot_token)
    try:
        await bot.send_message(
            chat_id=int(chat_id),
            text=message_with_link,
            parse_mode="HTML",
            disable_web_page_preview=False,
        )
    except Exception as e:
        raise RuntimeError(f"텔레그램 API 오류: {e}")


def send_telegram_message(message: str, *, dry_run: bool = False):
    """텔레그램 봇을 통해 메시지 전송 (동기 래퍼)"""
    if os.name == 'nt':  # Windows
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(send_telegram_message_async(message, dry_run=dry_run))


def main():
    parser = argparse.ArgumentParser(description="환율 정보를 카카오톡/텔레그램으로 전송합니다.")
    parser.add_argument("--dry-run", action="store_true", help="메시지를 전송하지 않고 출력만 합니다.")
    parser.add_argument("--kakao", action="store_true", help="카카오톡으로 전송합니다.")
    parser.add_argument("--telegram", action="store_true", help="텔레그램으로 전송합니다.")
    parser.add_argument("--all", action="store_true", help="카카오톡과 텔레그램 모두로 전송합니다.")
    args = parser.parse_args()

    lines = build_report_lines()
    message = "\n".join(lines)

    # 옵션이 없으면 기본적으로 카카오톡으로 전송 (하위 호환성)
    if not args.kakao and not args.telegram and not args.all:
        args.kakao = True

    if args.all or args.kakao:
        try:
            send_kakao_message(message, dry_run=args.dry_run)
        except Exception as e:
            print(f"[카카오톡 전송 실패] {e}")

    if args.all or args.telegram:
        try:
            send_telegram_message(message, dry_run=args.dry_run)
        except Exception as e:
            print(f"[텔레그램 전송 실패] {e}")


if __name__ == "__main__":
    main()

