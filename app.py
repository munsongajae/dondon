import streamlit as st
import pandas as pd
from datetime import datetime

# mybank.py에서 함수들 import
from mybank import (
    get_shinhan_exchange_rate,
    get_kbstar_exchange_rate,
    get_hanabank_exchange_rate,
    get_investing_exchange_rate
)

# bithumb_usdt.py에서 함수 import
from bithumb_usdt import get_bithumb_usdt, get_bithumb_btc

# 페이지 설정
st.set_page_config(
    page_title="실시간 환율 정보",
    page_icon="💱",
    layout="wide"
)

# 시간 포맷 함수
def format_datetime(date_str, time_str):
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
        except:
            return f"{date_str} {time_str}"
    return "-"

# 데이터 로딩 함수
@st.cache_data(ttl=60)
def load_exchange_rates():
    """환율 데이터 로딩 (1분 캐시)"""
    bank_data = []
    investing_data = None
    bithumb_data = None
    
    with st.spinner('신한은행 조회 중...'):
        shinhan = get_shinhan_exchange_rate()
        if shinhan:
            bank_data.append({
                '은행': '신한은행',
                '조회일시': format_datetime(shinhan['date'], shinhan['time']),
                '고시회차': f"{shinhan['round']}회차",
                'USD_raw': shinhan['USD'],
                'JPY_raw': shinhan['JPY']
            })
    
    with st.spinner('국민은행 조회 중...'):
        kbstar = get_kbstar_exchange_rate()
        if kbstar:
            bank_data.append({
                '은행': '국민은행',
                '조회일시': format_datetime(kbstar['date'], kbstar['time']),
                '고시회차': f"{kbstar['round']}회차",
                'USD_raw': kbstar['USD'],
                'JPY_raw': kbstar['JPY']
            })
    
    with st.spinner('하나은행 조회 중...'):
        hana = get_hanabank_exchange_rate()
        if hana:
            bank_data.append({
                '은행': '하나은행',
                '조회일시': format_datetime(hana['date'], hana['time']),
                '고시회차': f"{hana['round']}회차",
                'USD_raw': hana['USD'],
                'JPY_raw': hana['JPY']
            })
    
    with st.spinner('Investing.com 조회 중...'):
        investing = get_investing_exchange_rate()
        if investing:
            investing_data = {
                'datetime': format_datetime(investing['date'], investing['time']),
                'USD_KRW': investing['USD_KRW'],
                'JPY_KRW': investing['JPY_KRW'] * 100  # 100엔당으로 변환
            }
    
    with st.spinner('빗썸 USDT 조회 중...'):
        bithumb = get_bithumb_usdt()
        if bithumb:
            bithumb_data = {
                'price': bithumb['price'],
                'change_rate': bithumb['change_rate'],
                'change_amount': bithumb['change_amount']
            }
    
    with st.spinner('빗썸 BTC 조회 중...'):
        btc = get_bithumb_btc()
        btc_data = None
        if btc:
            btc_data = {
                'price': btc['price'],
                'change_rate': btc['change_rate'],
                'change_amount': btc['change_amount']
            }
    
    return bank_data, investing_data, bithumb_data, btc_data

# 데이터 로드
bank_data, investing_data, bithumb_data, btc_data = load_exchange_rates()

# 헤더 영역 - Investing.com 환율
st.title("💱 실시간 환율 정보")

if investing_data:
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
    
    with col1:
        st.metric(
            label="📊 Investing.com - USD/KRW",
            value=f"₩{investing_data['USD_KRW']:,.2f}",
            delta=None
        )
    
    with col2:
        st.metric(
            label="📊 Investing.com - JPY(100엔)/KRW",
            value=f"₩{investing_data['JPY_KRW']:,.2f}",
            delta=None
        )
    
    with col3:
        if bithumb_data:
            # 김치프리미엄 계산: ((빗썸 USDT - Investing USD) / Investing USD) * 100
            kimchi_premium = ((bithumb_data['price'] - investing_data['USD_KRW']) / investing_data['USD_KRW']) * 100
            
            st.metric(
                label="💰 빗썸 USDT",
                value=f"₩{bithumb_data['price']:,.0f}",
                delta=f"{bithumb_data['change_rate']:+.2f}%",
                delta_color="inverse"  # 상승=빨간색, 하락=녹색
            )
            
            # 김치프리미엄 색상 표시
            if kimchi_premium > 0:
                kimchi_color = "🔴"
                kimchi_text = f"+{kimchi_premium:.2f}%"
            elif kimchi_premium < 0:
                kimchi_color = "🔵"
                kimchi_text = f"{kimchi_premium:.2f}%"
            else:
                kimchi_color = "⚪"
                kimchi_text = "0.00%"
            
            st.caption(f"{kimchi_color} 김치프리미엄: **{kimchi_text}**")
    
    with col4:
        if btc_data:
            st.metric(
                label="₿ 빗썸 BTC",
                value=f"₩{btc_data['price']:,.0f}",
                delta=f"{btc_data['change_rate']:+.2f}%",
                delta_color="inverse"  # 상승=빨간색, 하락=녹색
            )
    
    with col5:
        st.caption(f"🕐 조회일시")
        st.caption(f"**{investing_data['datetime']}**")

    st.divider()

# 새로고침 버튼
if st.button("🔄 새로고침"):
    st.rerun()

# 은행별 환율 비교표
st.subheader("🏦 은행별 환율 비교")

if bank_data:
    df = pd.DataFrame(bank_data)
    
    # Investing.com 환율과 비교하여 차이 계산
    if investing_data:
        investing_usd = investing_data['USD_KRW']
        investing_jpy = investing_data['JPY_KRW']
        
        # USD 차이 계산 (Investing.com - 은행)
        df['USD_diff'] = investing_usd - df['USD_raw']
        df['USD'] = df.apply(
            lambda row: f"{row['USD_raw']:,.2f} ({row['USD_diff']:+.2f})", 
            axis=1
        )
        
        # JPY 차이 계산 (Investing.com - 은행)
        df['JPY_diff'] = investing_jpy - df['JPY_raw']
        df['JPY(100엔)'] = df.apply(
            lambda row: f"{row['JPY_raw']:,.2f} ({row['JPY_diff']:+.2f})", 
            axis=1
        )
    else:
        # Investing.com 데이터가 없으면 기본 포맷
        df['USD'] = df['USD_raw'].apply(lambda x: f"{x:,.2f}")
        df['JPY(100엔)'] = df['JPY_raw'].apply(lambda x: f"{x:,.2f}")
        df['USD_diff'] = 0
        df['JPY_diff'] = 0
    
    # 조회일시 순으로 오름차순 정렬
    df = df.sort_values('조회일시', ascending=True)
    
    # 표시용 컬럼만 선택
    display_df = df[['은행', 'USD', 'JPY(100엔)', '조회일시', '고시회차']]
    
    # 스타일 함수 정의
    def color_diff(val):
        """차이에 따라 색상 지정"""
        if '(' not in str(val):
            return ''
        
        # 괄호 안의 숫자 추출
        try:
            diff_str = str(val).split('(')[1].split(')')[0]
            diff = float(diff_str)
            
            if diff < 0:
                # 마이너스 (은행이 낮음, 유리) - 파란색
                return 'color: #0066cc; font-weight: bold'
            elif diff > 0:
                # 플러스 (은행이 높음, 불리) - 빨간색
                return 'color: #cc0000; font-weight: bold'
            else:
                return ''
        except:
            return ''
    
    # 스타일 적용
    styled_df = display_df.style.applymap(
        color_diff, 
        subset=['USD', 'JPY(100엔)']
    )
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True
    )
    
    # 업데이트 시간 표시
    st.caption(f"마지막 업데이트: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}")
    st.caption("💡 🔵 파란색 (외화 매도) | 🔴 빨간색 (외화 매수)")
else:
    st.warning("데이터를 가져올 수 없습니다.")
