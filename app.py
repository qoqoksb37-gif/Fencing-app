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
        players_df = pd.read_csv(PLAYER_FILE)
        if '소속팀' not in players_df.columns:
            players_df['소속팀'] = '소속없음'
            players_df.to_csv(PLAYER_FILE, index=False, encoding='utf-8-sig')
    else:
        players_df = pd.DataFrame({'선수명': ['오상욱', '구본길', '김정환', '아론 실라지'], '소속팀': ['대전광역시청', '국민체육진흥공단', '국민체육진흥공단', '헝가리 국가대표']})
        players_df.to_csv(PLAYER_FILE, index=False, encoding='utf-8-sig')
    
    players = players_df['선수명'].tolist()
    if os.path.exists(MATCH_FILE): matches_df = pd.read_csv(MATCH_FILE)
    else:
        matches_df = pd.DataFrame(columns=["매치ID", "날짜", "대회명", "종목", "경기유형", "타겟점수", "선수A", "선수B", "득점A", "득점B", "승자"])
        matches_df.to_csv(MATCH_FILE, index=False, encoding='utf-8-sig')
        
    if os.path.exists(ACTION_FILE): actions_df = pd.read_csv(ACTION_FILE)
    else:
        # 💡 팀 컬럼 추가 보완
        actions_df = pd.DataFrame(columns=["매치ID", "경기유형", "팀", "득점자", "기술분류", "타겟부위"])
        actions_df.to_csv(ACTION_FILE, index=False, encoding='utf-8-sig')
        
    return players_df, players, matches_df, actions_df

players_df, players, matches_df, actions_df = load_data()
if 'current_actions' not in st.session_state: st.session_state.current_actions = []

# ==========================================
# 🧭 2. 사이드바 네비게이션
# ==========================================
st.sidebar.title("🤺 펜싱 시스템 메뉴")
menu = st.sidebar.radio(
    "이동할 메뉴를 선택하세요", 
    ["👤 선수 및 소속팀 관리", "📝 경기 결과 입력 (결과/세부)", "⚔️ 전적 분석 (선수/팀)", "🧠 스마트 역량 분석 (PPI)", "🎯 세부 전술/기술 분석"]
)

# ==========================================
# 📌 3. 화면별 전체 UI 및 로직
# ==========================================

# ---------------------------------------------------------
# [메뉴 1] 선수 및 소속팀 관리 (💡 등록/수정/삭제 탭 기능 추가!)
# ---------------------------------------------------------
if menu == "👤 선수 및 소속팀 관리":
    st.title("👤 선수 및 소속팀 명단 관리")
    
    # 💡 깔끔한 관리를 위해 3개의 탭(Tab)으로 분리
    tab1, tab2, tab3 = st.tabs(["➕ 선수 등록", "✏️ 선수 정보 수정", "🗑️ 선수 삭제"])
    
    # --- [탭 1] 선수 등록 ---
    with tab1:
        st.subheader("새 선수 등록")
        col_add1, col_add2 = st.columns(2)
        with col_add1:
            new_player = st.text_input("추가할 선수 이름")
        with col_add2:
            new_team = st.text_input("소속팀 (선택사항)", placeholder="예: 대전광역시청")
        
        if st.button("선수 추가", type="primary"):
            if new_player == "": st.warning("이름을 입력해주세요.")
            elif new_player in players: st.warning("이미 등록된 선수입니다.")
            else:
                team_name = new_team if new_team else "소속없음"
                new_row = pd.DataFrame([{'선수명': new_player, '소속팀': team_name}])
                pd.concat([players_df, new_row], ignore_index=True).to_csv(PLAYER_FILE, index=False, encoding='utf-8-sig')
                st.success(f"'{new_player}' ({team_name}) 추가 완료!"); st.rerun()

    # --- [탭 2] 선수 정보 수정 (💡 신규 추가) ---
    with tab2:
        st.subheader("선수 정보 및 소속팀 수정")
        if players:
            col_edit1, col_edit2 = st.columns(2)
            with col_edit1:
                player_to_edit = st.selectbox("수정할 선수 선택", players, key="edit_select")
                current_team = players_df[players_df['선수명'] == player_to_edit]['소속팀'].values[0]
            
            with st.form("edit_form"):
                st.info("💡 이름을 수정하면 과거에 저장된 모든 경기 기록 및 세부 기술 데이터의 이름도 함께 100% 자동 업데이트됩니다.")
                e_col1, e_col2 = st.columns(2)
                new_player_name = e_col1.text_input("선수 이름 수정", value=player_to_edit)
                new_team_name = e_col2.text_input("소속팀 수정", value=current_team)
                
                if st.form_submit_button("정보 수정 적용"):
                    if new_player_name == "":
                        st.error("이름을 비울 수 없습니다.")
                    elif new_player_name != player_to_edit and new_player_name in players:
                        st.error("이미 존재하는 다른 선수의 이름으로 변경할 수 없습니다.")
                    else:
                        # 1. players_df 업데이트
                        players_df.loc[players_df['선수명'] == player_to_edit, '선수명'] = new_player_name
                        players_df.loc[players_df['선수명'] == new_player_name, '소속팀'] = new_team_name
                        players_df.to_csv(PLAYER_FILE, index=False, encoding='utf-8-sig')
                        
                        # 2. 이름이 변경된 경우 과거 DB 전체 연쇄 업데이트 (Cascade Update)
                        if new_player_name != player_to_edit:
                            if not matches_df.empty:
                                matches_df['선수A'] = matches_df['선수A'].replace(player_to_edit, new_player_name)
                                matches_df['선수B'] = matches_df['선수B'].replace(player_to_edit, new_player_name)
                                matches_df['승자'] = matches_df['승자'].replace(player_to_edit, new_player_name)
                                matches_df['매치ID'] = matches_df['매치ID'].str.replace(player_to_edit, new_player_name)
                                matches_df.to_csv(MATCH_FILE, index=False, encoding='utf-8-sig')
                            
                            if not actions_df.empty:
                                actions_df['득점자'] = actions_df['득점자'].replace(player_to_edit, new_player_name)
                                if '팀' in actions_df.columns:
                                    actions_df['팀'] = actions_df['팀'].replace(player_to_edit, new_player_name)
                                actions_df['매치ID'] = actions_df['매치ID'].str.replace(player_to_edit, new_player_name)
                                actions_df.to_csv(ACTION_FILE, index=False, encoding='utf-8-sig')
                            
                        st.success(f"'{player_to_edit}' 선수의 정보가 성공적으로 수정되었습니다!"); st.rerun()
        else:
            st.info("등록된 선수가 없습니다.")

    # --- [탭 3] 선수 삭제 ---
    with tab3:
        st.subheader("선수 강제 삭제")
        if players:
            player_to_delete = st.selectbox("삭제할 선수 선택", players, key="del_select")
            has_matches = not matches_df[(matches_df['선수A'] == player_to_delete) | (matches_df['선수B'] == player_to_delete)].empty
            
            if has_matches:
                st.warning(f"⚠️ '{player_to_delete}' 선수는 이미 저장된 경기 기록이 있습니다.")
                force_delete = st.checkbox("해당 선수의 모든 경기 기록 및 세부 기술 데이터를 함께 영구 삭제함에 동의합니다.")
                if st.button("선수 강제 삭제", type="primary"):
                    if force_delete:
                        updated_players_df = players_df[players_df['선수명'] != player_to_delete]
                        updated_players_df.to_csv(PLAYER_FILE, index=False, encoding='utf-8-sig')
                        matches_df[(matches_df['선수A'] != player_to_delete) & (matches_df['선수B'] != player_to_delete)].to_csv(MATCH_FILE, index=False, encoding='utf-8-sig')
                        if not actions_df.empty:
                            actions_df[~actions_df['매치ID'].str.contains(player_to_delete)].to_csv(ACTION_FILE, index=False, encoding='utf-8-sig')
                        st.success(f"삭제 완료!"); st.rerun()
                    else: st.error("삭제하려면 위 체크박스에 먼저 체크해야 합니다.")
            else:
                if st.button("선수 삭제"):
                    players_df[players_df['선수명'] != player_to_delete].to_csv(PLAYER_FILE, index=False, encoding='utf-8-sig')
                    st.success("삭제 완료!"); st.rerun()

    st.markdown("---")
    st.subheader("📋 현재 등록된 선수 명단")
    display_df = players_df.copy(); display_df.index = display_df.index + 1
    st.dataframe(display_df, use_container_width=True)

# ---------------------------------------------------------
# [메뉴 2] 경기 결과 입력
# ---------------------------------------------------------
elif menu == "📝 경기 결과 입력 (결과/세부)":
    st.title("📝 경기 기록")
    
    st.markdown("### 🏆 대회 기본 정보")
    match_type_selection = st.radio("경기 유형 선택", ["예선 풀 (5점)", "본선 토너먼트 (15점)", "단체전 (45점)"], horizontal=True)
    
    if match_type_selection == "예선 풀 (5점)": 
        target_score = 5; match_type_str = "예선(Poule)"
    elif match_type_selection == "본선 토너먼트 (15점)": 
        target_score = 15; match_type_str = "본선(ED)"
    else: 
        target_score = 45; match_type_str = "단체전(Team)"
    
    teams = list(players_df['소속팀'].unique())
    if "소속없음" in teams: teams.remove("소속없음")
    if len(teams) < 2: teams = ["팀 A", "팀 B", "팀 C"] + teams
    
    col1, col2 = st.columns(2)
    with col1:
        match_date = st.date_input("날짜", date.today())
        tournament = st.text_input("대회명")
        weapon = st.selectbox("종목", ["사브르", "에페", "플뢰레"])
    with col2:
        if "단체전" in match_type_selection:
            st.info("💡 단체전은 소속팀 기준으로 기록됩니다.")
            entity_a = st.selectbox("Team A (Red)", teams)
            entity_b = st.selectbox("Team B (Green)", teams, index=1 if len(teams)>1 else 0)
        else:
            if len(players) < 2: st.error("선수가 2명 이상 필요합니다."); st.stop()
            entity_a = st.selectbox("선수 A (Red)", players)
            entity_b = st.selectbox("선수 B (Green)", players, index=1)
            
    match_id = f"{match_date}_{tournament}_{entity_a}_vs_{entity_b}"
    
    st.markdown("---")
    
    if "단체전" in match_type_selection:
        input_mode = st.radio("기록 방식 선택", ["단순 결과만 저장", "단체전 9바우트 스코어 기록", "세부 기술(액션) 포인트 기록"], horizontal=True)
    else:
        input_mode = st.radio("기록 방식 선택", ["단순 결과만 저장", "세부 기술(액션) 포인트 기록"], horizontal=True)

    # 1. 단순 기록 모드
    if input_mode == "단순 결과만 저장":
        with st.form("quick"):
            c1, c2 = st.columns(2)
            score_a = c1.number_input("A 득점", min_value=0, max_value=target_score, value=0)
            score_b = c2.number_input("B 득점", min_value=0, max_value=target_score, value=0)
            if st.form_submit_button("결과 저장"):
                if entity_a == entity_b or score_a == score_b or not tournament:
                    st.error("입력 오류 (동일대상/동점/대회명누락)")
                else:
                    winner = entity_a if score_a > score_b else entity_b
                    new_match = pd.DataFrame([{"매치ID": match_id, "날짜": str(match_date), "대회명": tournament, "종목": weapon, "경기유형": match_type_str, "타겟점수": target_score, "선수A": entity_a, "선수B": entity_b, "득점A": score_a, "득점B": score_b, "승자": winner}])
                    pd.concat([matches_df, new_match], ignore_index=True).to_csv(MATCH_FILE, index=False, encoding='utf-8-sig')
                    st.success(f"{match_type_str} 결과가 성공적으로 저장되었습니다!")

    # 2. 단체전 9바우트 모드
    elif input_mode == "단체전 9바우트 스코어 기록":
        st.markdown("### 🤝 단체전 9릴레이 스코어 기록")
        with st.form("team_relay_form"):
            bouts = []
            for i in range(1, 10):
                st.markdown(f"**[{i} 바우트]**")
                c1, c2, c3, c4, c5 = st.columns([2, 1, 0.2, 1, 2])
                p_a = c1.selectbox(f"A팀 출전선수 (Bout {i})", players, key=f"ta_{i}")
                s_a = c2.number_input(f"A 득점", min_value=0, max_value=15, value=0, key=f"sa_{i}")
                c3.markdown("<div style='text-align:center; padding-top:30px;'>vs</div>", unsafe_allow_html=True)
                s_b = c4.number_input(f"B 득점", min_value=0, max_value=15, value=0, key=f"sb_{i}")
                p_b = c5.selectbox(f"B팀 출전선수 (Bout {i})", players, index=1, key=f"tb_{i}")
                bouts.append((p_a, s_a, p_b, s_b))
                st.markdown("---")
                
            if st.form_submit_button("단체전 9바우트 일괄 저장", type="primary"):
                if not tournament: st.error("대회명을 상단에 입력해주세요.")
                else:
                    new_matches = []
                    for idx, (p_a, s_a, p_b, s_b) in enumerate(bouts):
                        if s_a == 0 and s_b == 0: continue
                        b_match_id = f"{match_date}_{tournament}_Team_Bout{idx+1}_{p_a}_vs_{p_b}"
                        winner = p_a if s_a > s_b else (p_b if s_b > s_a else "무승부(Draw)")
                        new_matches.append({
                            "매치ID": b_match_id, "날짜": str(match_date), "대회명": tournament, "종목": weapon,
                            "경기유형": "단체전(Team)", "타겟점수": 5, 
                            "선수A": p_a, "선수B": p_b, "득점A": s_a, "득점B": s_b, "승자": winner
                        })
                    if new_matches:
                        pd.concat([matches_df, pd.DataFrame(new_matches)], ignore_index=True).to_csv(MATCH_FILE, index=False, encoding='utf-8-sig')
                        st.success("단체전 9바우트 개별 데이터가 성공적으로 저장되었습니다!")
                    else:
                        st.warning("입력된 점수가 없어 저장되지 않았습니다.")

    # 3. 세부 기술 모드
    elif input_mode == "세부 기술(액션) 포인트 기록":
        st.markdown("### 🤺 포인트 세부 액션 기록")
        if entity_a == entity_b: st.error("대상을 다르게 선택하세요."); st.stop()
        
        if "단체전" in match_type_selection:
            st.info("단체전은 득점한 **팀**과 실제 기술을 쓴 **선수**를 함께 선택하세요.")
            scoring_team = st.radio("어느 팀이 득점했나요?", [entity_a, entity_b], horizontal=True)
            c1, c2, c3 = st.columns(3)
            scorer = c1.selectbox("실제 득점 선수", players)
        else:
            scoring_team = None
            c1, c2, c3 = st.columns(3)
            scorer = c1.selectbox("득점자", [entity_a, entity_b])
            
        action_type = c2.selectbox("기술분류", ["공격 (선제 팡트/플뢰쉬)", "파라드 리포스트 (막고 반격)", "콩트르 아따끄 (받아치기)", "르미즈 (재차 공격)", "기타 (페널티 등)"])
        target = c3.selectbox("타겟부위", ["머리", "몸통", "팔/손목", "하체(에페)"])
        
        col_btn1, col_btn2 = st.columns([1, 3])
        with col_btn1:
            if st.button("➕ 액션 기록 추가"):
                st.session_state.current_actions.append({
                    "팀": scoring_team if scoring_team else scorer, 
                    "득점자": scorer, "기술분류": action_type, "타겟부위": target
                })
                st.success("득점 인정!")
        with col_btn2:
            if st.button("🔄 기록 초기화"): st.session_state.current_actions = []; st.rerun()
            
        if st.session_state.current_actions:
            temp_df = pd.DataFrame(st.session_state.current_actions)
            cur_a = len(temp_df[temp_df['팀'] == entity_a])
            cur_b = len(temp_df[temp_df['팀'] == entity_b])
            st.markdown(f"**진행 스코어: {entity_a} [{cur_a} : {cur_b}] {entity_b}**")
            
            display_df = temp_df[["팀", "득점자", "기술분류", "타겟부위"]] if "단체전" in match_type_selection else temp_df[["득점자", "기술분류", "타겟부위"]]
            st.dataframe(display_df, use_container_width=True)
            
            if st.button("💾 매치 및 세부기록 최종 저장", type="primary"):
                if not tournament or cur_a == cur_b: st.error("대회명 누락 혹은 스코어가 동점인지 확인하세요.")
                else:
                    winner = entity_a if cur_a > cur_b else entity_b
                    new_match = pd.DataFrame([{
                        "매치ID": match_id, "날짜": str(match_date), "대회명": tournament, "종목": weapon,
                        "경기유형": match_type_str, "타겟점수": target_score, "선수A": entity_a, "선수B": entity_b, "득점A": cur_a, "득점B": cur_b, "승자": winner
                    }])
                    pd.concat([matches_df, new_match], ignore_index=True).to_csv(MATCH_FILE, index=False, encoding='utf-8-sig')
                    
                    temp_df['매치ID'] = match_id; temp_df['경기유형'] = match_type_str
                    temp_df = temp_df[["매치ID", "경기유형", "팀", "득점자", "기술분류", "타겟부위"]] if '팀' in temp_df.columns else temp_df[["매치ID", "경기유형", "득점자", "기술분류", "타겟부위"]]
                    pd.concat([actions_df, temp_df], ignore_index=True).to_csv(ACTION_FILE, index=False, encoding='utf-8-sig')
                    
                    st.session_state.current_actions = []; st.success("저장 완료!"); st.rerun()

# ---------------------------------------------------------
# [메뉴 3] 상대 전적 분석
# ---------------------------------------------------------
elif menu == "⚔️ 전적 분석 (선수/팀)":
    st.title("⚔️ 스마트 상대 전적 분석")
    
    all_entities = sorted(list(set(matches_df['선수A'].tolist() + matches_df['선수B'].tolist() + players)))
    if len(all_entities) < 2: st.info("충분한 기록이 없습니다."); st.stop()
    
    c1, c2 = st.columns(2)
    p1 = c1.selectbox("기준 선수 또는 팀", all_entities)
    p2 = c2.selectbox("상대 선수 또는 팀", all_entities, index=1 if len(all_entities)>1 else 0)
    
    if p1 != p2:
        h2h_filter = st.radio("🔍 분석할 경기 유형", ["전체 경기 통합", "예선(Poule)만", "본선(ED)만", "단체전(Team)만"], horizontal=True)
        st.markdown("---")
        h2h_df = matches_df[((matches_df['선수A'] == p1) & (matches_df['선수B'] == p2)) | ((matches_df['선수A'] == p2) & (matches_df['선수B'] == p1))].copy().sort_values(by='날짜')
        
        if "예선" in h2h_filter: h2h_df = h2h_df[h2h_df['경기유형'].str.contains('예선', na=False)]
        elif "본선" in h2h_filter: h2h_df = h2h_df[h2h_df['경기유형'].str.contains('본선', na=False)]
        elif "단체전" in h2h_filter: h2h_df = h2h_df[h2h_df['경기유형'].str.contains('단체', na=False)]
        
        if not h2h_df.empty:
            total = len(h2h_df)
            p1_wins = len(h2h_df[h2h_df['승자'] == p1])
            m1, m2, m3 = st.columns(3)
            m1.metric("맞대결 횟수", f"{total}전")
            m2.metric(f"{p1} 우위(승리)", f"{p1_wins}번")
            m3.metric(f"{p2} 우위(승리)", f"{total-p1_wins}번")
            
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
            st.info("해당 조건의 맞대결 전적이 없습니다.")

# ---------------------------------------------------------
# [메뉴 4] 스마트 역량 분석 (PPI)
# ---------------------------------------------------------
elif menu == "🧠 스마트 역량 분석 (PPI)":
    st.title("🧠 폼(Form) 및 역량 분석")
    if not players: st.stop()
    
    col1, col2 = st.columns([1, 2])
    with col1: target_player = st.selectbox("분석할 선수", players)
        
    player_matches = matches_df[(matches_df['선수A'] == target_player) | (matches_df['선수B'] == target_player)].copy()
    
    if not player_matches.empty:
        player_matches['날짜'] = pd.to_datetime(player_matches['날짜']).dt.date
        min_date = player_matches['날짜'].min(); max_date = player_matches['날짜'].max()
        
        with col2: date_range = st.date_input("🗓️ 분석 기간(Date Range) 설정", [min_date, max_date], min_value=min_date, max_value=max_date)
            
        if len(date_range) == 2:
            start_date, end_date = date_range
            filtered_matches = player_matches[(player_matches['날짜'] >= start_date) & (player_matches['날짜'] <= end_date)].sort_values(by='날짜')
            
            if filtered_matches.empty: st.warning("선택한 기간에 경기 데이터가 없습니다.")
            else:
                total = len(filtered_matches)
                wins = len(filtered_matches[filtered_matches['승자'] == target_player])
                n_att, n_def, margins, c_wins, c_total, team_margins = [], [], [], 0, 0, []
                
                for _, row in filtered_matches.iterrows():
                    ts = row['타겟점수']
                    scored = row['득점A'] if row['선수A'] == target_player else row['득점B']
                    conceded = row['득점B'] if row['선수A'] == target_player else row['득점A']
                    margin = scored - conceded
                    
                    if ts > 0: 
                        n_att.append((scored/ts)*100)
                        n_def.append(((ts-conceded)/ts)*100)
                    margins.append(margin)
                    
                    if abs(margin) <= 2: c_total += 1; c_wins += (1 if margin > 0 else 0)
                    if '단체' in str(row['경기유형']): team_margins.append(margin)
                        
                filtered_matches['마진'] = margins
                a_att = sum(n_att)/total if total > 0 else 0
                a_def = sum(n_def)/total if total > 0 else 0
                c_rate = (c_wins/c_total*100) if c_total > 0 else 50
                dom = min(100, max(0, 50 + (sum(margins)/total*10))) if total > 0 else 50
                
                st.markdown("---")
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("#### 📈 종합 역량 (Radar)")
                    fig = go.Figure(go.Scatterpolar(r=[a_att, a_def, wins/total*100, dom, c_rate, a_att], theta=['공격력', '방어력', '전체 승률', '경기 주도력', '위기관리(Clutch)', '공격력'], fill='toself', line_color='#E74C3C'))
                    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100]))); st.plotly_chart(fig, use_container_width=True)
                with c2:
                    st.markdown("#### 🎢 폼(Form) 트렌드")
                    recent = filtered_matches.copy()
                    recent['결과'] = recent['마진'].apply(lambda x: '승/우위' if x>0 else ('무승부' if x==0 else '패/열세'))
                    recent['날짜표기'] = recent['날짜'].astype(str) + " (" + recent['경기유형'] + ")"
                    fig2 = px.bar(recent, x='날짜표기', y='마진', color='결과', color_discrete_map={'승/우위':'#2ECC71', '무승부':'gray', '패/열세':'#E74C3C'}, text='마진')
                    fig2.update_traces(textposition='outside'); st.plotly_chart(fig2, use_container_width=True)

                ind_matches = filtered_matches[~filtered_matches['경기유형'].str.contains('단체', na=False)]
                if not ind_matches.empty:
                    st.markdown("---")
                    st.markdown(f"### 🤺 개인전 (예선/본선) 수행 능력 리포트")
                    
                    ind_total = len(ind_matches)
                    ind_wins = len(ind_matches[ind_matches['승자'] == target_player])
                    ind_win_rate = (ind_wins / ind_total) * 100
                    
                    poule_m = ind_matches[ind_matches['경기유형'].str.contains('예선', na=False)]
                    ed_m = ind_matches[ind_matches['경기유형'].str.contains('본선', na=False)]
                    
                    poule_win_rate = (len(poule_m[poule_m['승자'] == target_player]) / len(poule_m) * 100) if not poule_m.empty else 0
                    ed_win_rate = (len(ed_m[ed_m['승자'] == target_player]) / len(ed_m) * 100) if not ed_m.empty else 0
                    
                    if ind_win_rate >= 70: ind_eval = "🏅 **[메달권 스트라이커]** 개인전에서 압도적인 승률을 자랑하며 상위권 진출이 유력한 탑 티어 기량을 보여줍니다."
                    elif ind_win_rate >= 50: ind_eval = "🛡️ **[본선 단골 랭커]** 안정적인 1:1 교전 능력으로 꾸준히 승리를 챙기며 본선 무대에서 활약하는 선수입니다."
                    else: ind_eval = "🌱 **[성장 잠재력]** 개인전 승률을 높이기 위해 공격 성공률과 위기 관리(Clutch) 능력을 한 단계 끌어올릴 필요가 있습니다."
                    
                    st.info(ind_eval)
                    
                    ic1, ic2, ic3, ic4 = st.columns(4)
                    ic1.metric("개인전 총 전적", f"{ind_total}전 {ind_wins}승")
                    ic2.metric("개인전 총 승률", f"{ind_win_rate:.1f}%")
                    ic3.metric("예선(Poule) 승률", f"{poule_win_rate:.1f}%" if not poule_m.empty else "기록 없음")
                    ic4.metric("본선(ED) 승률", f"{ed_win_rate:.1f}%" if not ed_m.empty else "기록 없음")

                if len(team_margins) > 0:
                    st.markdown("---")
                    st.markdown(f"### 🤝 단체전 팀 공헌도 (Team Contribution) 리포트")
                    avg_team_margin = sum(team_margins) / len(team_margins)
                    max_margin = max(team_margins)
                    plus_bouts = len([m for m in team_margins if m > 0])
                    bout_win_rate = (plus_bouts / len(team_margins)) * 100
                    
                    if avg_team_margin >= 2.0: eval_text = "🔥 **[압도적 에이스]** 출전하는 바우트마다 상대와의 격차를 크게 벌리며 팀 승리를 이끕니다."
                    elif avg_team_margin > 0: eval_text = "✨ **[안정적 득점원]** 꾸준하게 플러스(+) 마진을 기록하며 팀에 기여하는 든든한 선수입니다."
                    elif avg_team_margin == 0: eval_text = "⚖️ **[현상 유지형]** 득점과 실점이 비슷하여, 팀의 점수 차를 유지하는 역할을 수행합니다."
                    else: eval_text = "⚠️ **[전술 보완 필요]** 단체전에서 마이너스(-) 마진 비율이 높습니다. 수비적 전술 보완이 필요합니다."
                        
                    st.info(eval_text)
                    tc1, tc2, tc3, tc4 = st.columns(4)
                    tc1.metric("출전 바우트 수", f"{len(team_margins)}회")
                    tc2.metric("바우트 당 평균 마진", f"{avg_team_margin:+.1f}점")
                    tc3.metric("플러스 마진 달성률", f"{bout_win_rate:.1f}%")
                    tc4.metric("최고 캐리 (최대 마진)", f"+{max_margin}점")
    else:
        st.info("해당 선수의 경기 데이터가 없습니다.")

# ---------------------------------------------------------
# [메뉴 5] 세부 전술/기술 분석
# ---------------------------------------------------------
elif menu == "🎯 세부 전술/기술 분석":
    st.title("🎯 경기 유형별 전술/성향 분석")
    if actions_df.empty: st.info("기록된 세부 액션 데이터가 없습니다.")
    else:
        col1, col2 = st.columns([1, 2])
        with col1: target_player = st.selectbox("분석할 선수", players)
        with col2: filter_type = st.radio("데이터 필터", ["전체 경기 통합", "예선(Poule)만", "본선(ED)만", "단체전(Team)만"], horizontal=True)
        
        player_actions = actions_df[actions_df['득점자'] == target_player]
        if "예선" in filter_type: player_actions = player_actions[player_actions['경기유형'].str.contains('예선', na=False)]
        elif "본선" in filter_type: player_actions = player_actions[player_actions['경기유형'].str.contains('본선', na=False)]
        elif "단체전" in filter_type: player_actions = player_actions[player_actions['경기유형'].str.contains('단체', na=False)]
        
        if player_actions.empty: st.warning("해당 조건의 데이터가 없습니다.")
        else:
            total_points = len(player_actions)
            st.markdown(f"#### 💡 분석 대상 누적 득점: 총 {total_points}점 ({filter_type})")
            
            c3, c4 = st.columns(2)
            with c3:
                action_counts = player_actions['기술분류'].value_counts().reset_index()
                action_counts.columns = ['기술', '비율']
                fig_action = px.pie(action_counts, values='비율', names='기술', hole=0.4, title="주력 득점 기술")
                st.plotly_chart(fig_action, use_container_width=True)
            with c4:
                target_counts = player_actions['타겟부위'].value_counts().reset_index()
                target_counts.columns = ['타겟', '비율']
                fig_target = px.pie(target_counts, values='비율', names='타겟', hole=0.4, title="주력 타겟 부위")
                st.plotly_chart(fig_target, use_container_width=True)
