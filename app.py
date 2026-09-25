import socket
socket.setdefaulttimeout(5.0)

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
st.set_page_config(page_title="개별종목 투자자별 매매동향", layout="wide", initial_sidebar_state="expanded")

# 사이드바 접기/펼치기 버튼 상시 표시 및 모바일 대비 강화 CSS
st.markdown("""
<style>
    /* 메인 콘텐츠 상단 여백 규격화 */
    .main .block-container,
    [data-testid="stMainBlockContainer"],
    .block-container {
        padding-top: 2.0rem !important;
    }

    /* Headers & Main Title (00 Bookmarks 테마 일치) */
    h1, .main h1, [data-testid="stHeadingWithActionElements"] h1, .main-title {
        color: #8AB4F8 !important;
        -webkit-text-fill-color: #8AB4F8 !important;
        font-size: 2.0rem !important;
        font-weight: 800 !important;
        text-align: center !important;
    }

    /* Button Styling (39 DividendStock 표준 스타일 일치) */
    .stButton button[kind="primary"],
    .stButton > button[kind="primary"],
    section[data-testid="stSidebar"] button[kind="primary"] {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border: none !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
        transition: all 0.2s ease !important;
    }
    .stButton button[kind="primary"]:hover,
    .stButton > button[kind="primary"]:hover,
    section[data-testid="stSidebar"] button[kind="primary"]:hover {
        background-color: #1d4ed8 !important;
        box-shadow: 0 0 10px rgba(37, 99, 235, 0.4) !important;
    }

    /* 다운로드 버튼 공통 통일 스타일 */
    div[data-testid="stDownloadButton"] > button,
    .stDownloadButton > button {
        background-color: #334155 !important;
        color: #f8fafc !important;
        border: 1px solid #475569 !important;
        border-radius: 6px !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        height: 38px !important;
        min-height: 38px !important;
        max-height: 38px !important;
        line-height: 36px !important;
        padding: 0 16px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        transition: all 0.2s ease-in-out !important;
        box-sizing: border-box !important;
    }
    div[data-testid="stDownloadButton"] > button:hover,
    .stDownloadButton > button:hover {
        background-color: #475569 !important;
        border-color: #38bdf8 !important;
        color: #ffffff !important;
        box-shadow: 0 0 10px rgba(56, 189, 248, 0.25) !important;
    }
    div[data-testid="stDownloadButton"] > button:active,
    .stDownloadButton > button:active {
        background-color: #1e293b !important;
        border-color: #0284c7 !important;
    }
    div[data-testid="stDownloadButton"] > button p,
    div[data-testid="stDownloadButton"] > button span,
    .stDownloadButton > button p,
    .stDownloadButton > button span {
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        color: inherit !important;
        line-height: inherit !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* 사이드바 스타일링 */
    section[data-testid="stSidebar"], [data-testid="stSidebar"] {
        background-color: #1e293b !important;
        border-right: 1px solid #334155 !important;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #f8fafc !important;
        -webkit-text-fill-color: #f8fafc !important;
    }

    /* =========================================================
       사이드바 접기(<<) 및 펼치기(>>) 버튼 항상 표시 및 시인성/대비 강화
       ========================================================= */
    /* 1. 사이드바가 열려 있을 때 접기 버튼 (<<) 상시 표시 */
    [data-testid="stSidebarCollapseButton"] {
        visibility: visible !important;
        opacity: 1 !important;
        display: inline-flex !important;
    }
    
    [data-testid="stSidebarCollapseButton"] button {
        visibility: visible !important;
        opacity: 1 !important;
        background-color: #1e293b !important;       /* 진한 네이비 배경 */
        border: 1.5px solid #38bdf8 !important;     /* 선명한 스카이블루 테두리로 상자 명확화 */
        border-radius: 8px !important;
        width: 38px !important;
        height: 38px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4), 0 0 6px rgba(56, 189, 248, 0.2) !important;
        transition: all 0.2s ease !important;
    }
    
    /* 상자 내부의 << 아이콘(Material Icon span/svg/문자)을 순백색으로 강제하여 상자와 극명한 대비 구현 */
    [data-testid="stSidebarCollapseButton"] button *,
    [data-testid="stSidebarCollapseButton"] span,
    [data-testid="stSidebarCollapseButton"] [data-testid="stIconMaterial"],
    [data-testid="stSidebarCollapseButton"] svg {
        color: #ffffff !important;
        fill: #ffffff !important;
        opacity: 1 !important;
        visibility: visible !important;
        font-size: 1.35rem !important;
        font-weight: 700 !important;
    }
    
    /* 호버(PC) 및 터치 시 반전 효과 */
    [data-testid="stSidebarCollapseButton"] button:hover {
        background-color: #38bdf8 !important;
        border-color: #38bdf8 !important;
    }
    [data-testid="stSidebarCollapseButton"] button:hover * {
        color: #0f172a !important;
        fill: #0f172a !important;
    }

    /* 2. 사이드바 헤더 영역 패딩 및 정렬 보정 */
    [data-testid="stSidebarHeader"] {
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
    }

    /* 3. 사이드바가 닫혔을 때 다시 여는 버튼 (>>) 시인성 강화 */
    [data-testid="stSidebarCollapsedControl"] {
        visibility: visible !important;
        opacity: 1 !important;
    }
    
    [data-testid="stSidebarCollapsedControl"] button {
        background-color: #1e293b !important;
        border: 1.5px solid #38bdf8 !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4), 0 0 6px rgba(56, 189, 248, 0.2) !important;
    }
    
    [data-testid="stSidebarCollapsedControl"] button *,
    [data-testid="stSidebarCollapsedControl"] span,
    [data-testid="stSidebarCollapsedControl"] [data-testid="stIconMaterial"],
    [data-testid="stSidebarCollapsedControl"] svg {
        color: #38bdf8 !important;
        fill: #38bdf8 !important;
        opacity: 1 !important;
        visibility: visible !important;
        font-size: 1.35rem !important;
    }

</style>
""", unsafe_allow_html=True)


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
        start_date = today - relativedelta(months=3)
        
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
@st.cache_data(ttl=86400)
def load_stock_tickers():
    """상장 종목 전체 리스트 가져오기 (로컬 CSV -> pykrx StockTicker -> FDR -> 내장 대표주)"""
    csv_path = os.path.join(os.path.dirname(__file__), "krx_tickers.csv")

    # 1. 로컬 krx_tickers.csv 최우선 로드 (해외 IP 차단/네트워크 지연 원천 차단)
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path, dtype={'티커': str}, index_col='티커')
            if not df.empty and '종목' in df.columns:
                return df
        except Exception:
            pass

    # 2. pykrx StockTicker 시도
    try:
        st_ticker = StockTicker()
        df = st_ticker.listed
        if not df.empty and '종목' in df.columns:
            try:
                df.to_csv(csv_path, encoding='utf-8-sig')
            except Exception:
                pass
            return df
    except Exception:
        pass

    # 3. Fallback to FinanceDataReader
    try:
        import FinanceDataReader as fdr
        df = fdr.StockListing('KRX')
        df = df.set_index('Code')
        df['종목'] = df['Name']
        return df
    except Exception:
        pass

    # 4. 내장 대표 32개 우량주 fallback (최악의 오프라인/네트워크 차단 환경 대비)
    fallback_data = {
        '005930': '삼성전자', '000660': 'SK하이닉스', '373220': 'LG에너지솔루션',
        '207940': '삼성바이오로직스', '005380': '현대차', '000270': '기아',
        '068270': '셀트리온', '105560': 'KB금융', '055550': '신한지주',
        '035420': 'NAVER', '005490': 'POSCO홀딩스', '012330': '현대모비스',
        '035720': '카카오', '028260': '삼성물산', '051910': 'LG화학',
        '086520': '에코프로', '247540': '에코프로비엠', '196170': '알테오젠',
        '036930': '주성엔지니어링', '006400': '삼성SDI', '032830': '삼성생명',
        '015760': '한국전력', '329180': 'HD현대중공업', '010130': '고려아연',
        '033780': 'KT&G', '003550': 'LG', '018260': '삼성에스디에스',
        '017670': 'SK텔레콤', '030200': 'KT', '034730': 'SK',
        '323410': '카카오뱅크', '259960': '크래프톤'
    }
    return pd.DataFrame(list(fallback_data.items()), columns=['티커', '종목']).set_index('티커')

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
        info_msg = f'<div style="font-size: 0.8rem; color: #BDC1C6; line-height: 1.4; margin-bottom: 5px;">📈 <b>주가 범위</b>: {price_range}<br/>💰 <b>수급 범위</b>: {trading_range}</div>'
        
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
st.markdown("<h1 class='main-title' style='text-align: center; font-size: 2.0rem !important; font-weight: 800 !important; color: #8AB4F8 !important; -webkit-text-fill-color: #8AB4F8 !important; margin-bottom: 10px;'><span style='color: #8AB4F8 !important; -webkit-text-fill-color: #8AB4F8 !important;'>한국증시 종목 투자자별 매매동향</span></h1>", unsafe_allow_html=True)
st.markdown("<div style='text-align: center; color: #BDC1C6; font-size: 0.9rem; margin-bottom: 20px; line-height: 1.6;'>KRX 거래소 계정 정보를 이용하여 개별 종목의 투자자별 거래대금 추이를 분석합니다.</div>", unsafe_allow_html=True)
st.markdown("<hr style='border: 0; height: 1px; background-color: #334155; margin-bottom: 22px;'>", unsafe_allow_html=True)

# 사이드바 설정
with st.sidebar:
    st.markdown(
        """
        <div style='padding: 2px 0 12px 0;'>
            <div style='font-size: 1.25rem; font-weight: 700; color: #f8fafc; letter-spacing: -0.01em; display: flex; align-items: center; gap: 8px;'>
                <span>🔑</span> KRX 로그인 및 분석 설정
            </div>
            <div style='font-size: 0.82rem; color: #94a3b8; margin-top: 4px; line-height: 1.4;'>
                KRX 계정 연동 및 투자자별 매매동향 조회 조건을 설정합니다.
            </div>
        </div>
        <hr style='border: 0; height: 1px; background-color: #334155; margin: 10px 0 16px 0;'>
        """,
        unsafe_allow_html=True
    )

    # env 로드 값
    env_id = os.getenv("KRX_ID", "")
    env_pw = os.getenv("KRX_PW", "")

    # 사이드바 입력창
    krx_id = st.text_input("KRX ID", value=env_id, help="data.krx.co.kr 로그인 아이디")
    krx_pw = st.text_input("KRX Password", value=env_pw, type="password", help="data.krx.co.kr 로그인 비밀번호")

    login_success = False
    if krx_id and krx_pw:
        login_success = try_krx_login(krx_id, krx_pw)
        if login_success:
            st.success("✔️ KRX 로그인 성공")
        else:
            st.error("❌ KRX 로그인 실패 (계정을 확인해 주세요)")
    else:
        st.warning("⚠️ KRX 로그인 정보 입력이 필요합니다.")

    st.markdown("<hr style='border: 0; height: 1px; background-color: #334155; margin: 16px 0;'>", unsafe_allow_html=True)
    st.subheader("🎯 조회 조건")

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
                
        selected_display = st.selectbox("종목 선택", display_names, index=default_idx)
        # 티커 코드 추출 (마지막 괄호 안의 6자리 문자)
        selected_ticker = selected_display.split("(")[-1].replace(")", "").strip()
        selected_name = tickers_df.loc[selected_ticker, '종목']
    else:
        st.error("종목 정보를 로드할 수 없습니다.")
        st.stop()

    # 조회 기간
    periods = ["1W", "2W", "1M", "3M", "6M", "1Y", "YTD"]
    selected_period = st.selectbox("조회 기간", periods, index=periods.index("3M"))

    # 투자자 선택
    investors = ["외국인", "투신", "사모", "연기금", "기관합계", "개인"]
    selected_investor = st.selectbox("분석 투자자", investors, index=0)

    # 액션 버튼 (Update & 조회)
    st.markdown("")
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        btn_update = st.button("🔄 Update", use_container_width=True, help="캐시를 초기화하고 최신 KRX 수급 데이터를 다시 수집합니다.")
    with col_btn2:
        submit_button = st.button("🔍 조회", type="primary", use_container_width=True, help="선택한 조건으로 대시보드를 새로고침합니다.")

    if btn_update:
        st.cache_data.clear()
        st.rerun()

# -----------------------------------------------------------------------------
# 5. 데이터 조회 및 시각화 영역
# -----------------------------------------------------------------------------
if login_success:
    # 조회 날짜 계산
    start_date, end_date = calculate_dates(selected_period)
    
    # 데이터를 조회(조회 버튼 클릭 혹은 최초 로드 시)
    st.markdown(f"<h3 style='color: #BDC1C6; font-size: 1.25rem; font-weight: 600; margin-top: 10px; margin-bottom: 10px;'>{selected_name} ({selected_ticker}) - {selected_period} 분석</h3>", unsafe_allow_html=True)
    
    # 데이터 패치 진행
    with st.spinner("KRX 데이터를 로드하고 있습니다..."):
        df, info_msg, err_msg = fetch_and_process_data(start_date, end_date, selected_ticker)
        
    if err_msg:
        st.error(err_msg)
        st.info("💡 팁: KRX 로그인 정보가 일치하지 않거나 세션이 만료된 경우 발생할 수 있습니다.")
    elif not df.empty:
        # 데이터 수집 범위 렌더링
        if info_msg:
            st.markdown(info_msg, unsafe_allow_html=True)
            st.markdown("")
        # 투자자 데이터 및 주가 데이터 확인
        if selected_investor not in df.columns:
            st.error(f"선택한 투자자({selected_investor}) 컬럼을 데이터에서 찾을 수 없습니다.")
            st.stop()
            
        # 메인 영역 레이아웃 분할
        col_left, col_right = st.columns([7, 3])
        
        with col_left:
            st.markdown(f"<h4 style='color: #BDC1C6; font-size: 1.05rem; font-weight: 600; margin-top: 10px; margin-bottom: 10px;'>📅 일별 추이 (선택한 투자자: {selected_investor})</h4>", unsafe_allow_html=True)
            
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
            
            # 레이아웃 꾸미기 (고대비 Tailwind Slate 표준 테마)
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#1E293B",
                plot_bgcolor="#0F172A",
                title=dict(
                    text=f"<b>{selected_name} 주가 및 {selected_investor} 순매수 거래대금 추이</b>",
                    font=dict(color="#F8FAFC", size=15),
                    x=0.5,
                    xanchor="center"
                ),
                hovermode="x unified",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,  # 제목 바로 아래에 범례 배치
                    xanchor="center",
                    x=0.5,
                    bgcolor="rgba(30, 41, 59, 0.85)",
                    bordercolor="#334155",
                    borderwidth=1,
                    font=dict(color="#F8FAFC", size=11)
                ),
                margin=dict(l=20, r=20, t=80, b=20),
                height=450
            )
            
            fig.update_xaxes(title_text="날짜", type='category', tickangle=-45, gridcolor="#334155", linecolor="#475569", tickfont=dict(color="#cbd5e1"))
            fig.update_yaxes(title_text="주가 (원)", tickformat=",.0f", secondary_y=False, gridcolor="#334155", linecolor="#475569", tickfont=dict(color="#cbd5e1"))
            fig.update_yaxes(title_text="순매수 거래대금 (억원)", secondary_y=True, showgrid=False, linecolor="#475569", tickfont=dict(color="#cbd5e1"))
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 일별 데이터 상세 테이블
            st.markdown("<h4 style='color: #BDC1C6; font-size: 1.05rem; font-weight: 600; margin-top: 15px; margin-bottom: 10px;'>📝 일별 데이터 상세</h4>", unsafe_allow_html=True)
            df_display = df[['주가', selected_investor]].copy()
            df_display.rename(columns={selected_investor: f'{selected_investor} 순매수 (억원)'}, inplace=True)
            df_display.index = df_display.index.strftime('%Y-%m-%d')
            
            # 소수점 2자리 포맷 강제 적용
            styled_display = df_display.sort_index(ascending=False).style.format({
                '주가': '{:,.0f}',
                f'{selected_investor} 순매수 (억원)': '{:.2f}'
            })
            st.dataframe(styled_display, use_container_width=True)
            
        with col_right:
            st.markdown(f"<h4 style='color: #BDC1C6; font-size: 1.05rem; font-weight: 600; margin-top: 15px; margin-bottom: 10px;'>💰 {selected_period} 기간합계 요약</h4>", unsafe_allow_html=True)
            st.write(f"조회 기간: `{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}` ~ `{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}`")
            
            # 기간 합계 연산
            # 모든 투자자 항목 정의 (기타법인을 외국인 다음으로 이동)
            투자자_목록 = ["금융투자", "보험", "투신", "사모", "은행", "기타금융", "연기금", "기관합계", "개인", "외국인", "기타법인", "기타외국인", "전체"]
            
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

st.markdown("---")
st.markdown("<div style='text-align: center; color: #64748b; font-size: 0.8rem; margin-top: 8px; margin-bottom: 24px; line-height: 1.6;'>⚠️ 본 서비스에서 제공하는 모든 정보는 투자 참고용이며, 투자의 최종 결정과 책임은 투자자 본인에게 있습니다.</div>", unsafe_allow_html=True)
