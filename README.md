# 💱 dondon

스트림릿으로 구현한 실시간 환율 대시보드입니다. 신한·국민·하나은행의 매매기준 환율과 Investing.com, 빗썸(USDT/BTC) 시세를 동시에 조회하고, 은행 환율과 해외 시세 간의 차이를 한눈에 파악할 수 있습니다.

## 주요 기능
- Investing.com 기준 USD/KRW, JPY/KRW(100엔) 시세 표시
- 신한/국민/하나은행 환율을 크롤링하여 조회일시·고시회차와 함께 비교
- 빗썸 USDT, BTC 가격 및 변동률 표시
- 빗썸 USDT와 해외 시세를 비교해 김치 프리미엄 계산
- `st.cache_data`를 활용한 1분 캐시와 새로고침 버튼 제공

## 실행 방법
```bash
pip install -r requirements.txt
streamlit run app.py
```

## 환경 변수
- 별도의 인증 토큰이 필요하지 않지만, 프록시나 기업망에서는 각 대상 사이트에 접근할 수 있도록 방화벽 예외가 필요할 수 있습니다.

## 자동 리포트 전송

### 카카오톡 설정
#### 1. 액세스 토큰 준비
- [카카오 디벨로퍼스](https://developers.kakao.com)에서 REST 앱을 만들고, 계정으로 로그인한 뒤 “나에게 보내기” 권한을 가진 `access_token`과 `refresh_token`을 발급합니다.
- Windows 환경 변수에 저장:
  ```cmd
  setx KAKAO_ACCESS_TOKEN "발급받은_access_token"
  setx KAKAO_REFRESH_TOKEN "발급받은_refresh_token"
  setx KAKAO_REST_API_KEY "앱의_REST_API_KEY"
  ```

### 텔레그램 설정
#### 1. 봇 생성 및 토큰 발급
- 텔레그램에서 [@BotFather](https://t.me/botfather)를 검색하고 `/newbot` 명령으로 봇을 생성합니다.
- BotFather가 제공하는 봇 토큰을 복사합니다.

#### 2. Chat ID 확인
- 봇에게 메시지를 보낼 사용자의 chat_id를 확인합니다:
  - 봇에게 `/start` 메시지를 보냅니다.
  - `https://api.telegram.org/bot{봇토큰}/getUpdates`를 브라우저에서 열어 응답 JSON에서 `chat.id` 값을 확인합니다.

#### 3. 환경 변수 설정
```cmd
setx TELEGRAM_BOT_TOKEN "BotFather에서_받은_토큰"
setx TELEGRAM_CHAT_ID "사용자의_chat_id"
```

### 리포트 스크립트 사용법
```bash
cd C:\webapp\dondon
# 드라이런 (메시지 확인만)
python -m reporting.send_report --dry-run

# 카카오톡만 전송 (기본값)
python -m reporting.send_report --kakao

# 텔레그램만 전송
python -m reporting.send_report --telegram

# 카카오톡과 텔레그램 모두 전송
python -m reporting.send_report --all
```

### 작업 스케줄러 등록
1. 예: `run_report.bat`
    ```bat
    @echo off
    cd /d C:\webapp\dondon
    call %LOCALAPPDATA%\Programs\Python\Python310\python.exe -m reporting.send_report --all >> report.log 2>&1
    ```
2. Windows 작업 스케줄러 → 작업 만들기 → 실행 프로그램에 `run_report.bat`를 지정하고 원하는 시간을 설정합니다.

## 참고
- 크롤링 대상 페이지 구조가 변경되면 파싱 로직 조정이 필요합니다.

