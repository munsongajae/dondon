from datetime import datetime

import pandas as pd
import streamlit as st

from reporting.exchange_fetcher import (
    format_datetime,
    load_exchange_rates as fetch_exchange_rates,
)

# 페이지 설정
st.set_page_config(
    page_title="환율 정보",
    page_icon="💱",
    layout="wide"
)

@st.cache_data(ttl=60)
def load_exchange_rates():
    """환율 데이터 로딩 (1분 캐시)"""
    return fetch_exchange_rates()

# 데이터 로드
with st.spinner('환율 데이터 조회 중...'):
    bank_data, investing_data, bithumb_data, btc_data = load_exchange_rates()

# 헤더 영역 - Investing.com 환율
st.title("💱 환율 정보")

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
    has_previous_data = 'is_previous' in df.columns and df['is_previous'].any()
    
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
    if has_previous_data:
        st.caption("※ 일부 은행 데이터는 전 영업일(또는 가장 최근 영업일) 기준입니다.")
else:
    st.warning("데이터를 가져올 수 없습니다.")
