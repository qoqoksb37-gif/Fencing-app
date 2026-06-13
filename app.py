import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import date

# ==========================================
# ⚙️ 1. 기본 설정 및 데이터 로드
# ==========================================
st.set_page_config(page_title="펜싱 스마트 분석 시스템", page_icon="🤺", layout="wide")

PLAYER_FILE = "players.csv"
MATCH_FILE = "matches.csv"
ACTION_FILE = "actions.csv" 

def load_data():
    if os.path.exists(PLAYER_FILE):
        players = pd.read_csv(PLAYER_FILE)['선수명'].tolist()
    else:
        players = ['오상욱', '구본길', '김정환', '아론 실라지']
        pd.DataFrame({'선수명': players}).to_csv(PLAYER_FILE, index=False, encoding='utf-8-sig')

    if os.path.exists(MATCH_FILE):
        matches_df = pd.read_csv(MATCH_FILE)
    else:
        matches_df = pd.DataFrame(columns=["매치ID", "날짜", "대회명", "종목", "경기유형", "타겟점수", "선수A", "선수B", "득점A", "득점B", "승자"])
        matches_df.to_csv(MATCH_FILE, index=False, encoding='utf-8-sig')
        
    if os.path.exists(ACTION_FILE):
        actions_df = pd.read_csv(ACTION_FILE)
    else:
        actions_df = pd.DataFrame(columns=["매치ID", "경기유형", "득점자", "기술분류", "타겟부위"])
        actions_df.to_csv(ACTION_FILE, index=False, encoding='utf-8-sig')
        
    return players, matches_df, actions_df

players, matches_df, actions_df = load_data()

if 'current_actions' not in st.session_state:
    st.session_state.current_actions = []

# ==========================================
# 🧭 2. 사이드바 네비게이션
# ==========================================
st.sidebar.title("🤺 펜싱 시스템 메뉴")
menu = st.sidebar.radio(
    "이동할 메뉴를 선택하세요", 
    [
        "👤 선수 관리", 
        "📝 경기 결과 입력 (결과/세부)", 
        "⚔️ 선수 vs 선수 전적", 
        "🧠 스마트 역량 분석 (PPI)", 
        "🎯 세부 전술/기술 분석"
    ]
)

# ==========================================
# 📌 3. 화면별 전체 UI 및 로직
# ==========================================

# ---------------------------------------------------------
# [메뉴 1] 선수 관리
# ---------------------------------------------------------
if menu == "👤 선수 관리":
    st.title("👤 선수 명단 관리")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("새 선수 등록")
        new_player = st.text_input("추가할 선수 이름")
        if st.button("선수 추가"):
            if new_player == "": st.warning("이름을 입력해주세요.")
            elif new_player in players: st.warning("이미 등록된 선수입니다.")
            else:
                players.append(new_player)
                pd.DataFrame({'선수명': players}).to_csv(PLAYER_FILE, index=False, encoding='utf-8-sig')
                st.success(f"'{new_player}' 추가 완료!")
                st.rerun()

    with col2:
        st.subheader("선수 삭제")
        if players:
            player_to_delete = st.selectbox("삭제할 선수", players)
            if st.button("선수 삭제"):
                has_matches = not matches_df[(matches_df['선수A'] == player_to_delete) | (matches_df['선수B'] == player_to_delete)].empty
                if has_matches:
                    st.error("경기 기록이 존재하여 삭제할 수 없습니다. (데이터 보호)")
                else:
                    players.remove(player_to_delete)
                    pd.DataFrame({'선수명': players}).to_csv(PLAYER_FILE, index=False, encoding='utf-8-sig')
                    st.success("삭제 완료!")
                    st.rerun()

# ---------------------------------------------------------
# [메뉴 2] 경기 결과 입력
# ---------------------------------------------------------
elif menu == "📝 경기 결과 입력 (결과/세부)":
    st.title("📝 경기 기록")
    input_mode = st.radio("기록 방식 선택", ["단순 결과만 저장", "세부 기술(포인트별) 기록"], horizontal=True)
    
    st.markdown("### 기본 매치 정보")
    match_type_selection = st.radio("경기 유형", ["예선 풀 (5점)", "본선 토너먼트 (15점)"], horizontal=True)
    target_score = 5 if match_type_selection == "예선 풀 (5점)" else 15
    match_type_str = "예선(Poule)" if match_type_selection == "예선 풀 (5점)" else "본선(ED)"
    
    col1, col2 = st.columns(2)
    with col1:
        match_date = st.date_input("날짜", date.today())
        tournament = st.text_input("대회명")
        weapon = st.selectbox("종목", ["사브르", "에페", "플뢰레"])
    with col2:
        if len(players) < 2: st.error("선수가 2명 이상 필요합니다."); st.stop()
        player_a = st.selectbox("선수 A (Red)", players)
        player_b = st.selectbox("선수 B (Green)", players, index=1)
        
    match_id = f"{match_date}_{tournament}_{player_a}_vs_{player_b}"
    
    if "단순" in input_mode:
        with st.form("quick"):
            c1, c2 = st.columns(2)
            score_a = c1.number_input("A 득점", 0, target_score, 0)
            score_b = c2.number_input("B 득점", 0, target_score, 0)
            if st.form_submit_button("결과 저장"):
                if player_a == player_b or score_a == score_b or not tournament:
                    st.error("입력값을 확인하세요 (동일선수/동점/대회명 누락).")
                else:
                    winner = player_a if score_a > score_b else player_b
                    new_match = pd.DataFrame([{"매치ID": match_id, "날짜": str(match_date), "대회명": tournament, "종목": weapon, "경기유형": match_type_str, "타겟점수": target_score, "선수A": player_a, "선수B": player_b, "득점A": score_a, "득점B": score_b, "승자": winner}])
                    pd.concat([matches_df, new_match], ignore_index=True).to_csv(MATCH_FILE, index=False, encoding='utf-8-sig')
                    st.success("저장 완료!")

    elif "세부" in input_mode:
        st.markdown("---")
        st.markdown(f"### 🤺 포인트 세부 기록 현황 ({match_type_str})")
        if player_a == player_b: st.error("선수를 다르게 선택하세요."); st.stop()
            
        c1, c2, c3 = st.columns(3)
        scorer = c1.selectbox("득점자", [player_a, player_b])
        action_type = c2.selectbox("기술분류", ["공격 (선제 팡트/플뢰쉬)", "파라드 리포스트 (막고 반격)", "콩트르 아따끄 (받아치기)", "르미즈 (재차 공격)", "기타 (페널티 등)"])
        target = c3.selectbox("타겟부위", ["머리", "몸통", "팔/손목", "하체(에페)"])
        
        col_btn1, col_btn2 = st.columns([1, 3])
        with col_btn1:
            if st.button("➕ 기록 추가"):
                st.session_state.current_actions.append({"득점자": scorer, "기술분류": action_type, "타겟부위": target})
                st.success(f"{scorer} 득점 인정!")
        with col_btn2:
            if st.button("🔄 기록 초기화"):
                st.session_state.current_actions = []
                st.rerun()
            
        if st.session_state.current_actions:
            temp_df = pd.DataFrame(st.session_state.current_actions)
            cur_a = len(temp_df[temp_df['득점자'] == player_a])
            cur_b = len(temp_df[temp_df['득점자'] == player_b])
            st.markdown(f"**진행 스코어: {player_a} [{cur_a} : {cur_b}] {player_b}**")
            st.dataframe(temp_df, use_container_width=True)
            
            if st.button("💾 최종 저장", type="primary"):
                if not tournament or cur_a == cur_b: st.error("대회명 누락 혹은 동점 확인.")
                else:
                    winner = player_a if cur_a > cur_b else player_b
                    new_match = pd.DataFrame([{"매치ID": match_id, "날짜": str(match_date), "대회명": tournament, "종목": weapon, "경기유형": match_type_str, "타겟점수": target_score, "선수A": player_a, "선수B": player_b, "득점A": cur_a, "득점B": cur_b, "승자": winner}])
                    pd.concat([matches_df, new_match], ignore_index=True).to_csv(MATCH_FILE, index=False, encoding='utf-8-sig')
                    temp_df['매치ID'] = match_id; temp_df['경기유형'] = match_type_str
                    temp_df = temp_df[["매치ID", "경기유형", "득점자", "기술분류", "타겟부위"]]
                    pd.concat([actions_df, temp_df], ignore_index=True).to_csv(ACTION_FILE, index=False, encoding='utf-8-sig')
                    st.session_state.current_actions = []
                    st.success("저장 성공!"); st.rerun()

# ---------------------------------------------------------
# [메뉴 3] 상대 전적 분석 (💡 경기 유형 필터 추가)
# ---------------------------------------------------------
elif menu == "⚔️ 선수 vs 선수 전적":
    st.title("⚔️ 스마트 상대 전적 분석")
    if len(players) < 2: st.stop()
    
    c1, c2 = st.columns(2)
    p1 = c1.selectbox("기준 선수", players)
    p2 = c2.selectbox("상대 선수", players, index=1)
    
    if p1 != p2:
        # 💡 예선/본선 필터 UI
        h2h_filter = st.radio("🔍 분석할 경기 유형을 선택하세요", ["전체 경기 통합", "예선(Poule)만", "본선(ED)만"], horizontal=True)
        st.markdown("---")
        
        h2h_df = matches_df[((matches_df['선수A'] == p1) & (matches_df['선수B'] == p2)) | ((matches_df['선수A'] == p2) & (matches_df['선수B'] == p1))].copy().sort_values(by='날짜')
        
        # 필터 적용
        if "예선" in h2h_filter: h2h_df = h2h_df[h2h_df['경기유형'] == '예선(Poule)']
        elif "본선" in h2h_filter: h2h_df = h2h_df[h2h_df['경기유형'] == '본선(ED)']
        
        if not h2h_df.empty:
            total = len(h2h_df)
            p1_wins = len(h2h_df[h2h_df['승자'] == p1])
            m1, m2, m3 = st.columns(3)
            m1.metric(f"맞대결 횟수 ({h2h_filter.split()[0]})", f"{total}전")
            m2.metric(f"{p1} 승리", f"{p1_wins}승")
            m3.metric(f"{p2} 승리", f"{total-p1_wins}승")
            
            st.markdown("### 🎢 역대 마진(점수차) 히스토리")
            margins, labels, colors = [], [], []
            for _, row in h2h_df.iterrows():
                margin = row['득점A'] - row['득점B'] if row['선수A'] == p1 else row['득점B'] - row['득점A']
                margins.append(margin); labels.append(f"{row['날짜']} ({row['경기유형']})")
                colors.append('#2ECC71' if margin > 0 else '#E74C3C')
                
            fig = go.Figure(go.Bar(x=labels, y=margins, marker_color=colors, text=[f"+{m}" if m>0 else m for m in margins], textposition='outside'))
            fig.add_hline(y=0, line_color="black")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"선택하신 '{h2h_filter}' 조건에 해당하는 맞대결 전적이 없습니다.")

# ---------------------------------------------------------
# [메뉴 4] 스마트 역량 분석 (💡 날짜 구간 필터 추가)
# ---------------------------------------------------------
elif menu == "🧠 스마트 역량 분석 (PPI)":
    st.title("🧠 폼(Form) 및 역량 분석")
    if not players: st.stop()
    
    col1, col2 = st.columns([1, 2])
    with col1:
        target_player = st.selectbox("분석할 선수", players)
        
    player_matches = matches_df[(matches_df['선수A'] == target_player) | (matches_df['선수B'] == target_player)].copy()
    
    if not player_matches.empty:
        # 날짜 형식 변환 및 최소/최대 날짜 추출
        player_matches['날짜'] = pd.to_datetime(player_matches['날짜']).dt.date
        min_date = player_matches['날짜'].min()
        max_date = player_matches['날짜'].max()
        
        # 💡 날짜 구간 선택 UI
        with col2:
            date_range = st.date_input("🗓️ 분석할 기간(Date Range) 설정", [min_date, max_date], min_value=min_date, max_value=max_date)
            
        # 두 날짜가 모두 선택되었을 때만 필터링 진행
        if len(date_range) == 2:
            start_date, end_date = date_range
            player_matches = player_matches[(player_matches['날짜'] >= start_date) & (player_matches['날짜'] <= end_date)].sort_values(by='날짜')
            
            if player_matches.empty:
                st.warning("선택한 기간 내에 경기 데이터가 없습니다.")
            else:
                total = len(player_matches)
                wins = len(player_matches[player_matches['승자'] == target_player])
                n_att, n_def, margins, c_wins, c_total = [], [], [], 0, 0
                
                for _, row in player_matches.iterrows():
                    ts = row['타겟점수']
                    scored = row['득점A'] if row['선수A'] == target_player else row['득점B']
                    conceded = row['득점B'] if row['선수A'] == target_player else row['득점A']
                    margin = scored - conceded
                    
                    n_att.append((scored/ts)*100); n_def.append(((ts-conceded)/ts)*100); margins.append(margin)
                    if abs(margin) <= 2:
                        c_total += 1
                        if margin > 0: c_wins += 1
                        
                player_matches['마진'] = margins
                a_att = sum(n_att)/total; a_def = sum(n_def)/total
                c_rate = (c_wins/c_total*100) if c_total > 0 else 50
                dom = min(100, max(0, 50 + (sum(margins)/total*10)))
                
                st.markdown("---")
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"#### 📈 {start_date} ~ {end_date} 종합 역량")
                    fig = go.Figure(go.Scatterpolar(r=[a_att, a_def, wins/total*100, dom, c_rate, a_att], theta=['공격력', '방어력', '전체 승률', '경기 주도력', '위기관리(Clutch)', '공격력'], fill='toself', line_color='#E74C3C'))
                    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])))
                    st.plotly_chart(fig, use_container_width=True)
                    
                with c2:
                    st.markdown("#### 🎢 해당 기간 폼(Form) 트렌드")
                    recent = player_matches.copy()
                    recent['결과'] = recent['마진'].apply(lambda x: '승' if x>0 else '패')
                    recent['날짜표기'] = recent['날짜'].astype(str)
                    fig2 = px.bar(recent, x='날짜표기', y='마진', color='결과', color_discrete_map={'승':'#2ECC71', '패':'#E74C3C'}, text='마진')
                    fig2.update_traces(textposition='outside')
                    st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("이 선수의 경기 데이터가 없습니다.")

# ---------------------------------------------------------
# [메뉴 5] 세부 전술/기술 분석
# ---------------------------------------------------------
elif menu == "🎯 세부 전술/기술 분석":
    st.title("🎯 예선 vs 본선 전술/성향 분석")
    if actions_df.empty:
        st.info("기록된 세부 액션 데이터가 없습니다.")
    else:
        col1, col2 = st.columns([1, 2])
        with col1: target_player = st.selectbox("분석할 선수", players)
        with col2: filter_type = st.radio("데이터 필터", ["전체 경기 통합", "예선(Poule)만 분석", "본선(ED)만 분석"], horizontal=True)
        
        player_actions = actions_df[actions_df['득점자'] == target_player]
        if "예선" in filter_type: player_actions = player_actions[player_actions['경기유형'] == '예선(Poule)']
        elif "본선" in filter_type: player_actions = player_actions[player_actions['경기유형'] == '본선(ED)']
        
        if player_actions.empty:
            st.warning(f"선택한 조건({filter_type})에 해당하는 득점 데이터가 없습니다.")
        else:
            total_points = len(player_actions)
            st.markdown(f"#### 💡 분석 대상 득점: 총 {total_points}점 ({filter_type})")
            
            c1, c2 = st.columns(2)
            with c1:
                action_counts = player_actions['기술분류'].value_counts().reset_index()
                action_counts.columns = ['기술', '비율']
                fig_action = px.pie(action_counts, values='비율', names='기술', hole=0.4, title="주력 득점 기술 분포")
                st.plotly_chart(fig_action, use_container_width=True)
            with c2:
                target_counts = player_actions['타겟부위'].value_counts().reset_index()
                target_counts.columns = ['타겟', '비율']
                fig_target = px.pie(target_counts, values='비율', names='타겟', hole=0.4, title="주력 타겟 부위")
                st.plotly_chart(fig_target, use_container_width=True)
