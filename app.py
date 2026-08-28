import streamlit as st
import datetime
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
import os

# pykrx 모듈 가져오기
from pykrx import stock
from pykrx.website.krx.market.ticker import StockTicker
from pykrx.website.comm.auth import build_krx_session, set_auth_session

# .env 파일 로드
load_dotenv()

# 웹 페이지 레이아웃 설정
st.set_page_config(page_title="한국증시 투자자 거래실적 대시보드", layout="wide")

# -----------------------------------------------------------------------------
# 1. 날짜 연산 함수
# -----------------------------------------------------------------------------
def calculate_dates(period):
    today = datetime.date.today()
    
    if period == "1W":
        start_date = today - datetime.timedelta(weeks=1)
    elif period == "2W":
        start_date = today - datetime.timedelta(weeks=2)
    elif period == "1M":
        start_date = today - relativedelta(months=1)
    elif period == "3M":
        start_date = today - relativedelta(months=3)
    elif period == "6M":
        start_date = today - relativedelta(months=6)
    elif period == "1Y":
        start_date = today - relativedelta(years=1)
    elif period == "YTD":
        start_date = datetime.date(today.year, 1, 1)
    else:
        start_date = today - datetime.timedelta(weeks=1)
        
    return start_date.strftime("%Y%m%d"), today.strftime("%Y%m%d")

# -----------------------------------------------------------------------------
# 2. KRX 로그인 세션 초기화 및 상태 관리
# -----------------------------------------------------------------------------
def try_krx_login(login_id, login_pw):
    """세션 갱신을 수행하고 session state에 보관"""
    if not login_id or not login_pw:
        return False
        
    try:
        # 이전에 성공한 세션이 있고 유효하다면 로그인 건너뜀
        if "krx_session" in st.session_state and st.session_state.krx_session.is_valid():
            set_auth_session(st.session_state.krx_session)
            return True
            
        # 신규 로그인 시도
        session = build_krx_session(login_id, login_pw)
        if session and session.is_authenticated:
            st.session_state.krx_session = session
            set_auth_session(session)
            return True
    except Exception as e:
        st.error(f"로그인 중 에러 발생: {e}")
        
    return False

# -----------------------------------------------------------------------------
# 3. 데이터 로드 및 정제 모듈 (캐싱 지원)
# -----------------------------------------------------------------------------
@st.cache_data
def load_stock_tickers():
    """상장 종목 전체 리스트 가져오기 (비로그인 상태로도 작동 가능)"""
    try:
        st_ticker = StockTicker()
        df = st_ticker.listed
        return df
    except Exception as e:
        st.error(f"종목 리스트 로드 실패: {e}")
        return pd.DataFrame()

def fetch_and_process_data(start_date, end_date, ticker):
    """주가 데이터와 투자자 거래실적 데이터를 병합하여 반환"""
    try:
        # 1. 주가 데이터 (OHLCV) 가져오기
        df_price = stock.get_market_ohlcv_by_date(start_date, end_date, ticker)
        if df_price.empty:
            return pd.DataFrame(), None, "주가 데이터가 존재하지 않습니다."
            
        # 2. 투자자별 순매수 거래대금 가져오기
        df_trading = stock.get_market_trading_value_by_date(start_date, end_date, ticker, detail=True)
        if df_trading.empty:
            return pd.DataFrame(), None, "투자자 순매수 데이터가 존재하지 않습니다. 로그인이 정상적으로 되었는지 확인하세요."
            
        # 데이터 수집 범위 메시지 생성
        price_range = f"{df_price.index[0].strftime('%Y-%m-%d')} ~ {df_price.index[-1].strftime('%Y-%m-%d')}"
        trading_range = f"{df_trading.index[0].strftime('%Y-%m-%d')} ~ {df_trading.index[-1].strftime('%Y-%m-%d')}"
        info_msg = f"📈 **주가 범위**: `{price_range}` &nbsp;|&nbsp; 💰 **수급 범위**: `{trading_range}`"
        
        # 3. 데이터 인덱스 포맷 맞추기 (datetime)
        df_price.index = pd.to_datetime(df_price.index)
        df_trading.index = pd.to_datetime(df_trading.index)
        
        # 4. 기관합계 계산 (상세 항목들의 합)
        기관_항목 = ["금융투자", "보험", "투신", "사모", "은행", "기타금융", "연기금"]
        exist_cols = [c for c in 기관_항목 if c in df_trading.columns]
        if exist_cols:
            df_trading["기관합계"] = df_trading[exist_cols].sum(axis=1)
            
        # 5. 거래대금 단위를 원 -> 억원 단위로 변환
        for col in df_trading.columns:
            df_trading[col] = df_trading[col] / 100_000_000.0
            
        # 6. 두 데이터프레임 조인
        df_combined = df_price[['종가']].join(df_trading, how='inner')
        df_combined.rename(columns={'종가': '주가'}, inplace=True)
        
        return df_combined, info_msg, None
    except Exception as e:
        return pd.DataFrame(), None, f"데이터 로드 중 예외가 발생했습니다: {e}"

# -----------------------------------------------------------------------------
# 4. 메인 화면 구성
# -----------------------------------------------------------------------------
st.markdown("<h1 style='color: #8AB4F8; margin-bottom: 10px;'>한국증시 종목 투자자별 매매동향</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #BDC1C6; font-size: 1.0rem; margin-bottom: 20px;'>KRX 거래소 계정 정보를 이용하여 개별 종목의 투자자별 거래대금 추이를 분석합니다.</p>", unsafe_allow_html=True)

# 사이드바 설정
st.sidebar.header("🔑 KRX 로그인 설정")

# env 로드 값
env_id = os.getenv("KRX_ID", "")
env_pw = os.getenv("KRX_PW", "")

# 사이드바 입력창
krx_id = st.sidebar.text_input("KRX ID", value=env_id, help="data.krx.co.kr 로그인 아이디")
krx_pw = st.sidebar.text_input("KRX Password", value=env_pw, type="password", help="data.krx.co.kr 로그인 비밀번호")

login_success = False
if krx_id and krx_pw:
    login_success = try_krx_login(krx_id, krx_pw)
    if login_success:
        st.sidebar.success("✔️ KRX 로그인 성공")
    else:
        st.sidebar.error("❌ KRX 로그인 실패 (계정을 확인해 주세요)")
else:
    st.sidebar.warning("⚠️ KRX 로그인 정보 입력이 필요합니다.")

st.sidebar.markdown("---")
st.sidebar.header("🔍 조회 조건")

# 종목 로드
tickers_df = load_stock_tickers()
if not tickers_df.empty:
    # selectbox 표시용 포맷팅: 종목명 (티커)
    tickers_df['display_name'] = tickers_df['종목'] + " (" + tickers_df.index + ")"
    display_names = sorted(tickers_df['display_name'].tolist())
    
    # 디폴트 종목: 삼성전자
    default_idx = 0
    for idx, name in enumerate(display_names):
        if "삼성전자" in name:
            default_idx = idx
            break
            
    selected_display = st.sidebar.selectbox("종목 선택", display_names, index=default_idx)
    # 티커 코드 추출 (마지막 괄호 안의 6자리 문자)
    selected_ticker = selected_display.split("(")[-1].replace(")", "").strip()
    selected_name = tickers_df.loc[selected_ticker, '종목']
else:
    st.sidebar.error("종목 정보를 로드할 수 없습니다.")
    st.stop()

# 기간 선택
periods = ["1W", "2W", "1M", "3M", "6M", "1Y", "YTD"]
selected_period = st.sidebar.selectbox("조회 기간", periods, index=0)

# 투자자 선택
investors = ["외국인", "투신", "사모", "연기금", "기관합계"]
selected_investor = st.sidebar.selectbox("분석 투자자", investors, index=0)

# 조회 버튼
st.sidebar.markdown("")
submit_button = st.sidebar.button("📊 조회하기", use_container_width=True)

# -----------------------------------------------------------------------------
# 5. 데이터 조회 및 시각화 영역
# -----------------------------------------------------------------------------
if login_success:
    # 조회 날짜 계산
    start_date, end_date = calculate_dates(selected_period)
    
    # 데이터를 조회(조회 버튼 클릭 혹은 최초 로드 시)
    st.subheader(f"{selected_name} ({selected_ticker}) - {selected_period} 분석")
    
    # 데이터 패치 진행
    with st.spinner("KRX 데이터를 로드하고 있습니다..."):
        df, info_msg, err_msg = fetch_and_process_data(start_date, end_date, selected_ticker)
        
    if err_msg:
        st.error(err_msg)
        st.info("💡 팁: KRX 로그인 정보가 일치하지 않거나 세션이 만료된 경우 발생할 수 있습니다.")
    elif not df.empty:
        # 데이터 수집 범위 렌더링
        if info_msg:
            st.markdown(info_msg)
            st.markdown("")
        # 투자자 데이터 및 주가 데이터 확인
        if selected_investor not in df.columns:
            st.error(f"선택한 투자자({selected_investor}) 컬럼을 데이터에서 찾을 수 없습니다.")
            st.stop()
            
        # 메인 영역 레이아웃 분할
        col_left, col_right = st.columns([7, 3])
        
        with col_left:
            st.markdown(f"#### 📅 일별 추이 (선택한 투자자: {selected_investor})")
            
            # Plotly 이중 Y축 차트 그리기
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            # 1. 순매수 거래대금 (우측 Y축, 막대)
            # 양수/음수 색상 지정
            colors = np.where(df[selected_investor] >= 0, '#EF553B', '#636EFA') # 양수: 빨간색, 음수: 파란색
            
            fig.add_trace(
                go.Bar(
                    x=df.index.strftime('%Y-%m-%d'),
                    y=df[selected_investor],
                    name=f"{selected_investor} 순매수 (억원)",
                    marker_color=colors,
                    opacity=0.8,
                    hovertemplate='%{x} 순매수: %{y:.2f} 억원<extra></extra>'
                ),
                secondary_y=True
            )
            
            # 2. 주가 (좌측 Y축, 꺾은선)
            fig.add_trace(
                go.Scatter(
                    x=df.index.strftime('%Y-%m-%d'),
                    y=df['주가'],
                    name="주가 (종가)",
                    mode='lines+markers',
                    line=dict(color='#2CA02C', width=2),
                    marker=dict(size=6),
                    hovertemplate='%{x} 주가: %{y:,.0f} 원<extra></extra>'
                ),
                secondary_y=False
            )
            
            # 레이아웃 꾸미기
            fig.update_layout(
                title_text=f"{selected_name} 주가 및 {selected_investor} 순매수 거래대금 추이",
                title_x=0.5,
                title_xanchor="center",
                hovermode="x unified",
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.22,  # X축 날짜 라벨과 겹치지 않는 적당한 하단 오프셋
                    xanchor="center",
                    x=0.5
                ),
                margin=dict(l=20, r=20, t=60, b=80),  # 하단 범례를 위한 b 마진 80 확보
                height=500
            )
            
            fig.update_xaxes(title_text="날짜", type='category', tickangle=-45)
            fig.update_yaxes(title_text="주가 (원)", tickformat=",.0f", secondary_y=False)
            fig.update_yaxes(title_text="순매수 거래대금 (억원)", secondary_y=True)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 일별 데이터 상세 테이블
            st.markdown("#### 📝 일별 데이터 상세")
            df_display = df[['주가', selected_investor]].copy()
            df_display.rename(columns={selected_investor: f'{selected_investor} 순매수 (억원)'}, inplace=True)
            df_display.index = df_display.index.strftime('%Y-%m-%d')
            st.dataframe(df_display.sort_index(ascending=False), use_container_width=True)
            
        with col_right:
            st.markdown(f"#### 💰 {selected_period} 기간합계 요약")
            st.write(f"조회 기간: `{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}` ~ `{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}`")
            
            # 기간 합계 연산
            # 모든 투자자 항목 정의
            투자자_목록 = ["금융투자", "보험", "투신", "사모", "은행", "기타금융", "연기금", "기관합계", "개인", "외국인", "기타외국인", "전체"]
            
            # 실존 컬럼만 필터링
            exist_investors = [inv for inv in 투자자_목록 if inv in df.columns]
            
            # 합계 시리즈 생성
            sum_series = df[exist_investors].sum()
            
            # 테이블용 데이터프레임 변환
            df_summary = pd.DataFrame({
                '투자자 구분': sum_series.index,
                '순매수 합계 (억원)': sum_series.values
            })
            
            # 외국인, 기관합계, 개인 등 주요 항목 강조 스타일링 (배경색 대신 글자색 변경으로 다크테마/검정색 조화)
            def highlight_rows(row):
                val = row['투자자 구분']
                if val in ["외국인", "개인", "기관합계", "전체"]:
                    return ['font-weight: bold; color: #8AB4F8;'] * len(row)
                return [''] * len(row)
                
            # 소수점 2자리 포맷팅 고정 및 스타일 적용
            styled_summary = df_summary.style.apply(highlight_rows, axis=1).format({
                '순매수 합계 (억원)': '{:.2f}'
            })
            
            st.dataframe(styled_summary, use_container_width=True, height=500, hide_index=True)
            
            st.info("💡 모든 값은 억원 단위이며, 양수(+)는 순매수, 음수(-)는 순매도를 의미합니다.")
            
    else:
        st.warning("데이터가 비어 있습니다. 기간 설정 또는 종목을 변경해 다시 시도하세요.")
else:
    st.info("👈 대시보드 조회를 위해 사이드바에 KRX 로그인 정보를 입력해 주세요.")
    st.markdown("""
    ### 📌 시작 가이드
    1. 왼쪽 사이드바에 **KRX 정보데이터시스템(data.krx.co.kr)** 로그인 ID와 PW를 입력하세요.
    2. 로그인이 완료되면 자동으로 실시간 종목 리스트와 상세 매매동향을 가져올 수 있는 상태가 됩니다.
    3. 혹은 프로젝트 루트 디렉토리에 `.env` 파일을 생성하여 다음과 같이 계정을 미리 입력해 둘 수 있습니다.
    
    ```bash
    # .env 파일 예시
    KRX_ID=your_id
    KRX_PW=your_password
    ```
    """)
