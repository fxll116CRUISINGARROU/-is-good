import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

st.set_page_config(
    page_title="부산시 시내버스 종합분석",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main { padding-top: 2rem; }
    .metric-card { background-color: #f0f2f6; padding: 1.5rem; border-radius: 0.5rem; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """CSV 파일 로드 및 데이터 정제"""
    import os

    # 현재 스크립트가 있는 디렉토리
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "부산광역시_시내버스 업체별 연도별 버스 등록대수_20260330.csv")

    # 파일이 없으면 대안 경로 시도
    if not os.path.exists(file_path):
        alt_path = os.path.join(os.path.expanduser("~"), "OneDrive", "사진", "바탕 화면", "에이아이파이썬랩", "부산광역시_시내버스 업체별 연도별 버스 등록대수_20260330.csv")
        if os.path.exists(alt_path):
            file_path = alt_path

    df = pd.read_csv(file_path, encoding='cp949')
    df.columns = ['회사명', '노선번호', '버스ID', '타입1', '타입2', '타입3', '연료', '연도']
    return df

try:
    df = load_data()

    # ===== 헤더 =====
    st.markdown("# 🚌 부산광역시 시내버스 종합 분석 대시보드")
    st.markdown("**최종 업데이트:** 2026년 3월 30일")
    st.markdown("---")

    # ===== 사이드바 필터 =====
    st.sidebar.markdown("## 📋 필터 설정")

    year_min, year_max = int(df['연도'].min()), int(df['연도'].max())
    year_range = st.sidebar.slider(
        "📅 연도 범위",
        min_value=year_min,
        max_value=year_max,
        value=(year_min, year_max)
    )

    companies = sorted(df['회사명'].unique())
    selected_companies = st.sidebar.multiselect(
        "🏢 버스 회사",
        options=companies,
        default=companies,
        max_selections=None
    )

    fuels = sorted(df['연료'].unique())
    selected_fuels = st.sidebar.multiselect(
        "⛽ 연료 유형",
        options=fuels,
        default=fuels
    )

    # 필터 적용
    filtered_df = df[
        (df['연도'] >= year_range[0]) &
        (df['연도'] <= year_range[1]) &
        (df['회사명'].isin(selected_companies)) &
        (df['연료'].isin(selected_fuels))
    ]

    # ===== KPI 섹션 =====
    st.markdown("## 📊 주요 통계")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "총 버스 대수",
            f"{len(filtered_df):,}대",
            delta=f"{len(filtered_df) - len(df[df['연도'] == year_min])}" if year_min in df['연도'].values else None
        )

    with col2:
        st.metric("등록 회사", f"{filtered_df['회사명'].nunique()}개")

    with col3:
        st.metric("운행 노선", f"{filtered_df['노선번호'].nunique()}개")

    with col4:
        st.metric("연료 종류", f"{filtered_df['연료'].nunique()}종")

    with col5:
        avg_year = filtered_df['연도'].mean()
        st.metric("평균 등록년도", f"{avg_year:.1f}년")

    st.markdown("---")

    # ===== 탭 구성 =====
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["📈 주요지표", "🏆 회사순위", "📅 연도별", "⛽ 연료분석", "🚌 노선분석", "📋 데이터"]
    )

    # ===== 탭1: 주요 지표 =====
    with tab1:
        st.markdown("### 시각화 분석")

        col1, col2 = st.columns(2)

        with col1:
            # 연도별 버스 추이
            year_data = filtered_df.groupby('연도').size().reset_index(name='버스수')
            fig_year = px.line(
                year_data,
                x='연도',
                y='버스수',
                markers=True,
                title='📈 연도별 버스 등록 현황',
                line_shape='spline'
            )
            fig_year.update_traces(
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=8)
            )
            fig_year.update_layout(hovermode='x unified', height=400)
            st.plotly_chart(fig_year, use_container_width=True)

        with col2:
            # 연료별 분포
            fuel_data = filtered_df['연료'].value_counts().reset_index(name='개수')
            fuel_data.columns = ['연료', '개수']
            fig_fuel = px.pie(
                fuel_data,
                names='연료',
                values='개수',
                title='⛽ 연료 유형별 구성',
                hole=0.3
            )
            fig_fuel.update_layout(height=400)
            st.plotly_chart(fig_fuel, use_container_width=True)

        # 연도별 연료별 누적 지표
        year_fuel = filtered_df.groupby(['연도', '연료']).size().reset_index(name='버스수')
        fig_stacked = px.bar(
            year_fuel,
            x='연도',
            y='버스수',
            color='연료',
            title='📊 연도별 연료 유형 변화 (누적)',
            barmode='stack'
        )
        fig_stacked.update_layout(height=400)
        st.plotly_chart(fig_stacked, use_container_width=True)

    # ===== 탭2: 회사 순위 =====
    with tab2:
        st.markdown("### 버스 회사 순위")

        col1, col2 = st.columns([1, 2])

        with col1:
            company_count = filtered_df['회사명'].value_counts().head(15)
            st.dataframe(
                company_count.rename('버스 대수'),
                use_container_width=True,
                height=500
            )

        with col2:
            company_data = filtered_df['회사명'].value_counts().head(15).reset_index(name='버스수')
            company_data.columns = ['회사', '버스수']

            fig_company = px.bar(
                company_data,
                y='회사',
                x='버스수',
                orientation='h',
                title='🏢 상위 15개 버스 회사 보유 현황',
                text='버스수'
            )
            fig_company.update_traces(
                textposition='outside',
                marker_color='#2ecc71'
            )
            fig_company.update_layout(
                yaxis={'categoryorder': 'total ascending'},
                height=500
            )
            st.plotly_chart(fig_company, use_container_width=True)

        # 회사별 연료 분포
        company_fuel = filtered_df.groupby(['회사명', '연료']).size().reset_index(name='버스수')
        top_companies = filtered_df['회사명'].value_counts().head(10).index
        company_fuel_top = company_fuel[company_fuel['회사명'].isin(top_companies)]

        fig_cf = px.bar(
            company_fuel_top,
            x='회사명',
            y='버스수',
            color='연료',
            title='상위 10개 회사의 연료 유형별 구성',
            barmode='stack'
        )
        fig_cf.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig_cf, use_container_width=True)

    # ===== 탭3: 연도별 분석 =====
    with tab3:
        st.markdown("### 연도별 상세 분석")

        # 연도별 회사 수 변화
        col1, col2 = st.columns(2)

        with col1:
            year_company = filtered_df.groupby('연도')['회사명'].nunique().reset_index(name='회사수')
            fig_yc = px.line(
                year_company,
                x='연도',
                y='회사수',
                markers=True,
                title='연도별 운영 회사 수',
                line_shape='spline'
            )
            fig_yc.update_traces(line=dict(color='#e74c3c', width=3), marker=dict(size=8))
            fig_yc.update_layout(height=400)
            st.plotly_chart(fig_yc, use_container_width=True)

        with col2:
            year_route = filtered_df.groupby('연도')['노선번호'].nunique().reset_index(name='노선수')
            fig_yr = px.line(
                year_route,
                x='연도',
                y='노선수',
                markers=True,
                title='연도별 운행 노선 수',
                line_shape='spline'
            )
            fig_yr.update_traces(line=dict(color='#3498db', width=3), marker=dict(size=8))
            fig_yr.update_layout(height=400)
            st.plotly_chart(fig_yr, use_container_width=True)

        # 주요 회사의 연도별 추이
        top_5_companies = filtered_df['회사명'].value_counts().head(5).index
        company_year = filtered_df[filtered_df['회사명'].isin(top_5_companies)].groupby(['연도', '회사명']).size().reset_index(name='버스수')

        fig_cy = px.line(
            company_year,
            x='연도',
            y='버스수',
            color='회사명',
            title='상위 5개 회사의 연도별 버스 보유 추이',
            markers=True
        )
        fig_cy.update_layout(height=400, hovermode='x unified')
        st.plotly_chart(fig_cy, use_container_width=True)

    # ===== 탭4: 연료 분석 =====
    with tab4:
        st.markdown("### 연료 유형 상세 분석")

        # 연료별 통계 테이블
        fuel_stats = filtered_df.groupby('연료').agg({
            '회사명': 'nunique',
            '노선번호': 'nunique',
            '버스ID': 'count'
        }).rename(columns={
            '회사명': '회사수',
            '노선번호': '노선수',
            '버스ID': '버스대수'
        }).sort_values('버스대수', ascending=False)

        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown("**연료별 통계 요약**")
            st.dataframe(fuel_stats, use_container_width=True)

        with col2:
            # 연료별 버스수 막대 그래프
            fuel_count = filtered_df['연료'].value_counts().reset_index(name='버스수')
            fuel_count.columns = ['연료', '버스수']

            fig_fuel_bar = px.bar(
                fuel_count,
                x='연료',
                y='버스수',
                title='연료 유형별 버스 보유 현황',
                text='버스수',
                color='연료'
            )
            fig_fuel_bar.update_traces(textposition='outside')
            fig_fuel_bar.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig_fuel_bar, use_container_width=True)

        # 연료별 연도 분포
        fuel_year = filtered_df.groupby(['연료', '연도']).size().reset_index(name='버스수')
        fig_fy = px.line(
            fuel_year,
            x='연도',
            y='버스수',
            color='연료',
            title='연료별 연도 변화 추이',
            markers=True
        )
        fig_fy.update_layout(height=400, hovermode='x unified')
        st.plotly_chart(fig_fy, use_container_width=True)

    # ===== 탭5: 노선 분석 =====
    with tab5:
        st.markdown("### 노선 분석")

        # 노선별 버스 수
        route_data = filtered_df.groupby('노선번호').size().reset_index(name='버스수').sort_values('버스수', ascending=False).head(20)

        fig_route = px.bar(
            route_data,
            y='노선번호',
            x='버스수',
            orientation='h',
            title='🚌 상위 20개 노선의 버스 보유 현황',
            text='버스수'
        )
        fig_route.update_traces(textposition='outside', marker_color='#9b59b6')
        fig_route.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
        st.plotly_chart(fig_route, use_container_width=True)

        # 노선별 상세 정보
        col1, col2 = st.columns(2)

        with col1:
            route_companies = filtered_df.groupby('노선번호')['회사명'].nunique().reset_index(name='회사수').sort_values('회사수', ascending=False).head(10)
            st.markdown("**노선별 운영 회사 수 (상위 10)**")
            st.dataframe(route_companies, use_container_width=True)

        with col2:
            route_fuels = filtered_df.groupby('노선번호')['연료'].apply(lambda x: ', '.join(sorted(x.unique()))).reset_index(name='연료타입')
            route_fuels['노선번호'] = route_fuels['노선번호'].astype(str)
            st.markdown("**각 노선의 연료 구성 (상위 10)**")
            st.dataframe(
                route_fuels.head(10),
                use_container_width=True,
                hide_index=True
            )

    # ===== 탭6: 상세 데이터 =====
    with tab6:
        st.markdown("### 필터링된 데이터 조회")

        # 정렬 옵션
        col1, col2, col3 = st.columns(3)

        with col1:
            sort_by = st.selectbox("정렬 기준", ['회사명', '연도', '연료', '노선번호'])

        with col2:
            sort_order = st.radio("정렬 순서", ["⬆️ 오름차순", "⬇️ 내림차순"], horizontal=True)

        with col3:
            max_records = max(len(filtered_df), 10)
            default_records = min(100, max_records)
            records_to_show = st.number_input("표시 행 수", min_value=10, max_value=max_records, value=default_records)

        ascending = "오름" in sort_order
        display_df = filtered_df.sort_values(by=sort_by, ascending=ascending).head(records_to_show)

        st.dataframe(
            display_df[['회사명', '노선번호', '버스ID', '연료', '연도']],
            use_container_width=True,
            height=600
        )

        # 다운로드 버튼
        st.markdown("---")
        col1, col2, col3 = st.columns(3)

        with col1:
            csv_data = filtered_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 전체 데이터 (CSV)",
                data=csv_data,
                file_name="부산버스_전체데이터.csv",
                mime="text/csv"
            )

        with col2:
            csv_display = display_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📄 표시된 데이터 (CSV)",
                data=csv_display,
                file_name="부산버스_필터링데이터.csv",
                mime="text/csv"
            )

        with col3:
            st.metric("📊 총 레코드 수", f"{len(filtered_df):,}건")

    # ===== 푸터 =====
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray; font-size: 12px;'>
    📊 데이터 출처: 부산광역시_시내버스 업체별 연도별 버스 등록대수 (2026.03.30)<br>
    🔄 실시간 필터링 가능 | 📥 데이터 다운로드 지원
    </div>
    """, unsafe_allow_html=True)

except FileNotFoundError:
    st.error("❌ 파일을 찾을 수 없습니다.")
    st.info("'부산광역시_시내버스 업체별 연도별 버스 등록대수_20260330.csv' 파일이 현재 디렉토리에 있는지 확인하세요.")
except Exception as e:
    st.error(f"❌ 오류 발생: {str(e)}")
    st.info("데이터 형식이나 인코딩에 문제가 있을 수 있습니다.")
