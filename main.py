# app.py
# Streamlit 앱: 개인 맞춤 영양식 설계 데모
# 외부 라이브러리 없음(표준 라이브러리 + streamlit만 사용).
# 사용법: streamlit run app.py

import streamlit as st
import math
import random
import io
import json
from datetime import date

st.set_page_config(page_title="스마트 영양식 설계사 🍽️", layout="wide")

# ---------- 스타일(간단한 CSS) ----------
st.markdown(
    """
    <style>
    .big-title {font-size:32px; font-weight:700;}
    .secondary {color: #6b7280;}
    .card {background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%); padding:16px; border-radius:12px; box-shadow: 0 4px 12px rgba(16,24,40,0.06);}
    .muted {color:#6b7280; font-size:14px;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="big-title">🍏 스마트 영양식 설계사</div>', unsafe_allow_html=True)
st.markdown('<div class="secondary">사용자 정보와 기호를 반영한 하루 식단 추천을 제공합니다. 친절한 안내와 함께 결과를 확인하십시오. 😊</div>', unsafe_allow_html=True)
st.write("")

# ---------- 헬퍼 함수 ----------
def calc_bmr(sex, weight_kg, height_cm, age):
    # Mifflin-St Jeor
    if sex == "남성":
        return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

def activity_multiplier(level):
    mapping = {
        "거의 활동 없음": 1.2,
        "가벼운 활동 (주 1-3회)": 1.375,
        "보통 활동 (주 3-5회)": 1.55,
        "높은 활동 (주 6-7회)": 1.725,
        "매우 높은 활동 (육체노동 등)": 1.9
    }
    return mapping.get(level, 1.2)

def calorie_target(tdee, goal):
    if goal == "체중 감량":
        return int(tdee * 0.82)  # -18% 감량(데모용 안전수치)
    elif goal == "체중 증가":
        return int(tdee * 1.12)  # +12% 증가
    else:
        return int(tdee)

def macro_targets(calories, protein_pref="보통"):
    # 단백질 목표: 체중(kg) * factor (1.2~2.0) depending preference
    # 탄수화물: 나머지 열량에서 지방(25%)과 단백질(4kcal/g) 제외
    # 지방: 총열량의 25% (대략)
    fat_cal = calories * 0.25
    fat_g = int(fat_cal / 9)
    if protein_pref == "높게":
        prot_g = int(user_weight_kg * 1.8)
    elif protein_pref == "낮게":
        prot_g = int(user_weight_kg * 1.0)
    else:
        prot_g = int(user_weight_kg * 1.4)
    prot_cal = prot_g * 4
    carb_cal = max(0, calories - prot_cal - fat_cal)
    carb_g = int(carb_cal / 4)
    return {"calories": calories, "protein_g": prot_g, "carb_g": carb_g, "fat_g": fat_g}

def score_recipe_for_user(recipe, prefs):
    # 높은 점수: 선호 포함, 알레르기 제외, 비선호 제외, 비타민 채움 고려
    score = 0
    # 선호 음식 포함시 보너스
    for p in prefs["likes"]:
        if p and p.lower() in recipe["name"].lower():
            score += 15
    # 알레르기/싫어함 있으면 큰 패널티
    for a in prefs["allergies"]:
        if a and a.lower() in recipe["ingredients_text"].lower():
            return -999  # 완전 제외
    for d in prefs["dislikes"]:
        if d and d.lower() in recipe["ingredients_text"].lower():
            score -= 20
    # 비타민 포함 여부
    for vit in prefs["vitamins_wanted"]:
        if vit in recipe["vitamins"]:
            score += 5
    # 칼로리 적합성(너무 크면 감점)
    if recipe["calories"] <= prefs["calories_per_meal"] * 1.2:
        score += 8
    # 랜덤 소량 가산으로 다양성
    score += random.uniform(0,4)
    return score

def pick_meals_for_day(recipes_db, prefs):
    # 세 끼 + 1-2 간식을 추천 (간단한 탐색: greedy)
    chosen = {"아침": None, "점심": None, "저녁": None, "간식": []}
    remaining_cal = prefs["daily_calories"]
    # 각 끼 당 목표칼로리(비율)
    distribution = {"아침": 0.25, "점심": 0.35, "저녁": 0.30}
    for meal, frac in distribution.items():
        prefs["calories_per_meal"] = int(prefs["daily_calories"] * frac)
        # 후보 필터링
        candidates = []
        for r in recipes_db:
            s = score_recipe_for_user(r, prefs)
            if s > -100:
                candidates.append((s, r))
        if not candidates:
            chosen[meal] = None
            continue
        candidates.sort(key=lambda x: x[0], reverse=True)
        # 상위 후보 중 하나 선택(다양성 위해 약간 무작위)
        top_candidates = [c for c in candidates if c[0] >= candidates[0][0] - 6]
        sel = random.choice(top_candidates)[1]
        chosen[meal] = sel
        remaining_cal -= sel["calories"]
    # 간식: 남은 칼로리에서 한두개 고르기
    snack_pool = [r for r in recipes_db if r["type"] == "간식"]
    snacks = []
    snack_budget = max(150, int(prefs["daily_calories"] * 0.10))
    random.shuffle(snack_pool)
    for s in snack_pool:
        if s["calories"] <= snack_budget:
            snacks.append(s)
            snack_budget -= s["calories"]
        if len(snacks) >= 2 or snack_budget <= 100:
            break
    chosen["간식"] = snacks
    return chosen

# ---------- 간단한 '레시피 데이터베이스' (데모용) ----------
# 각 항목은 name, type, calories, protein_g, carb_g, fat_g, vitamins(list), ingredients_text
RECIPES = [
    {"name":"그릭 요거트 볼 (과일, 견과)", "type":"아침", "calories":380, "protein_g":20, "carb_g":45, "fat_g":12,
     "vitamins":["B","C"], "ingredients_text":"요거트, 블루베리, 바나나, 아몬드, 꿀"},
    {"name":"오트밀(우유) & 바나나", "type":"아침", "calories":330, "protein_g":12, "carb_g":55, "fat_g":6,
     "vitamins":["B"], "ingredients_text":"오트, 우유, 바나나, 시나몬"},
    {"name":"현미 비빔밥(닭가슴살 토핑)", "type":"점심", "calories":650, "protein_g":35, "carb_g":85, "fat_g":15,
     "vitamins":["A","C","B"], "ingredients_text":"현미, 닭가슴살, 야채, 고추장(약간)"},
    {"name":"연어 샐러드 & 통곡물빵", "type":"점심", "calories":540, "protein_g":30, "carb_g":42, "fat_g":22,
     "vitamins":["D","B"], "ingredients_text":"연어, 샐러드채소, 올리브오일, 통곡물빵"},
    {"name":"닭가슴살 스테이크 & 구운야채", "type":"저녁", "calories":620, "protein_g":45, "carb_g":30, "fat_g":28,
     "vitamins":["B"], "ingredients_text":"닭가슴살, 브로콜리, 당근, 올리브오일"},
    {"name":"두부야채 볶음밥(적당량)", "type":"저녁", "calories":580, "protein_g":25, "carb_g":78, "fat_g":16,
     "vitamins":["A","C"], "ingredients_text":"두부, 채소, 현미밥, 간장"},
    {"name":"아몬드 한줌 + 사과", "type":"간식", "calories":220, "protein_g":6, "carb_g":20, "fat_g":14,
     "vitamins":["E","C"], "ingredients_text":"아몬드, 사과"},
    {"name":"단백질 쉐이크 (우유기반)", "type":"간식", "calories":240, "protein_g":25, "carb_g":18, "fat_g":6,
     "vitamins":["B"], "ingredients_text":"단백질파우더, 우유, 바나나"},
    {"name":"당근 스틱 + 후무스", "type":"간식", "calories":180, "protein_g":5, "carb_g":20, "fat_g":8,
     "vitamins":["A","C"], "ingredients_text":"당근, 후무스(병아리콩)"},
    {"name":"바나나 팬케이크 (통밀)", "type":"아침", "calories":400, "protein_g":14, "carb_g":60, "fat_g":10,
     "vitamins":["B"], "ingredients_text":"통밀가루, 바나나, 계란, 우유"},
]

# ---------- 사용자 입력 UI ----------
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("1) 기본 정보 입력")
    col1, col2, col3 = st.columns(3)
    with col1:
        user_name = st.text_input("이름 (선택)", value="")
        today = date.today().isoformat()
        age = st.number_input("나이", value=25, min_value=10, max_value=100, step=1)
        sex = st.selectbox("성별", ("남성", "여성"))
    with col2:
        user_height_cm = st.number_input("키 (cm)", value=170, min_value=100, max_value=230, step=1)
        user_weight_kg = st.number_input("몸무게 (kg)", value=65.0, min_value=30.0, max_value=200.0, step=0.1)
        activity = st.selectbox("활동 수준", ("거의 활동 없음", "가벼운 활동 (주 1-3회)", "보통 활동 (주 3-5회)", "높은 활동 (주 6-7회)", "매우 높은 활동 (육체노동 등)"))
    with col3:
        goal = st.selectbox("목표", ("체중 유지", "체중 감량", "체중 증가"))
        protein_pref = st.selectbox("단백질 선호량", ("보통", "높게", "낮게"))
        veg_pref = st.multiselect("선호 음식(예시) - 기호에 맞춰 선택", ["해산물","닭고기","소고기","채소","견과류","과일","유제품","통곡물"], default=["채소","통곡물"])
    st.markdown('</div>', unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("2) 식습관 / 제약 입력")
    col1, col2 = st.columns(2)
    with col1:
        allergies = st.text_input("알레르기(쉼표로 구분, 예: 땅콩, 우유) - 비어있어도 됨", value="")
        dislikes_text = st.text_input("싫어하는 음식(쉼표로 구분, 예: 굴, 버섯)")
    with col2:
        vit_wanted = st.multiselect("특히 챙기고 싶은 영양(선택)", ["A","B","C","D","E","칼슘","철분"], default=["B","C"])
        meal_style = st.selectbox("끼니 스타일 선호", ("가벼운 식사", "포만감 있는 식사", "단백질 중심", "채소 중심"))
    st.markdown('</div>', unsafe_allow_html=True)

# parse lists
likes = veg_pref
allergies_list = [x.strip() for x in allergies.split(",") if x.strip()]
dislikes_list = [x.strip() for x in dislikes_text.split(",") if x.strip()]

# ---------- 계산 ----------
user_bmr = calc_bmr(sex, user_weight_kg, user_height_cm, age)
tdee = int(user_bmr * activity_multiplier(activity))
daily_cal = calorie_target(tdee, goal)
macros = macro_targets(daily_cal, protein_pref)

# Sidebar summary
with st.sidebar:
    st.markdown("### 요약")
    st.write(f"추정 BMR: **{int(user_bmr):,} kcal**")
    st.write(f"TDEE(활동 반영): **{tdee:,} kcal**")
    st.write(f"추천 칼로리 (목표 반영): **{daily_cal:,} kcal**")
    st.write(f"단백질 목표: **{macros['protein_g']} g**")
    st.write(f"탄수화물 목표: **{macros['carb_g']} g**")
    st.write(f"지방 목표: **{macros['fat_g']} g**")
    st.write("---")
    st.write("기호 및 제약:")
    st.write(f"- 선호: {', '.join(likes) if likes else '없음'}")
    st.write(f"- 알레르기: {', '.join(allergies_list) if allergies_list else '없음'}")
    st.write(f"- 싫어함: {', '.join(dislikes_list) if dislikes_list else '없음'}")

# ---------- 추천 생성 ----------
prefs = {
    "likes": [l.lower() for l in likes],
    "allergies": [a.lower() for a in allergies_list],
    "dislikes": [d.lower() for d in dislikes_list],
    "vitamins_wanted": vit_wanted,
    "daily_calories": daily_cal,
    "calories_per_meal": int(daily_cal * 0.3),  # temp, will be set in pick_meals
}

st.header("3) 맞춤 식단 추천 👩‍⚕️🍽️")
st.markdown("아래 버튼을 눌러 사용자의 정보에 맞춘 하루 권장 식단을 생성하십시오.")

if st.button("추천 식단 생성 🔍"):
    plan = pick_meals_for_day(RECIPES, prefs)
    st.session_state["last_plan"] = plan
    st.success("추천 식단이 생성되었습니다. 아래를 확인하십시오. ✅")

# Show if exists
plan = st.session_state.get("last_plan", None)
if plan:
    col_a, col_b = st.columns([2,1])
    with col_a:
        for meal in ["아침","점심","저녁"]:
            st.subheader(f"🟢 {meal}")
            item = plan.get(meal)
            if item:
                st.markdown(f"**{item['name']}**  — {item['calories']} kcal  | 단백질 {item['protein_g']} g  | 탄수 {item['carb_g']} g  | 지방 {item['fat_g']} g")
                st.markdown(f"_주요 재료_: {item['ingredients_text']}")
                if item.get("vitamins"):
                    st.caption("함유 영양: " + ", ".join(item["vitamins"]))
            else:
                st.info(f"{meal}에 적합한 추천을 찾지 못했습니다.")
        st.subheader("🟡 간식")
        snacks = plan.get("간식", [])
        if snacks:
            for s in snacks:
                st.markdown(f"- {s['name']} ({s['calories']} kcal)")
        else:
            st.info("추천 간식이 없습니다.")
    with col_b:
        st.markdown("### 오늘 목표와의 차이")
        # Sum macros
        tot_cals = 0; tot_prot=0; tot_carb=0; tot_fat=0
        for m in ["아침","점심","저녁"]:
            it = plan.get(m)
            if it:
                tot_cals += it["calories"]; tot_prot += it["protein_g"]; tot_carb += it["carb_g"]; tot_fat += it["fat_g"]
        for s in plan.get("간식", []):
            tot_cals += s["calories"]; tot_prot += s["protein_g"]; tot_carb += s["carb_g"]; tot_fat += s["fat_g"]
        st.metric("추천된 총 칼로리", f"{tot_cals:,} kcal", delta=f"{tot_cals - daily_cal:+,} kcal")
        st.metric("단백질 (g)", f"{tot_prot} g", delta=f"{tot_prot - macros['protein_g']:+} g")
        st.metric("탄수화물 (g)", f"{tot_carb} g", delta=f"{tot_carb - macros['carb_g']:+} g")
        st.metric("지방 (g)", f"{tot_fat} g", delta=f"{tot_fat - macros['fat_g']:+} g")
        # Progress bars
        st.write("진행률(목표 대비)")
        st.progress(min(1.0, tot_prot / max(1, macros['protein_g'])))
        st.progress(min(1.0, tot_carb / max(1, macros['carb_g'])))
        st.progress(min(1.0, tot_fat / max(1, macros['fat_g'])))
        st.write("---")
        st.markdown("#### 조언")
        if tot_prot < macros["protein_g"]:
            st.info("단백질이 부족합니다. 간식으로 단백질 쉐이크나 두부, 견과를 추가하십시오. 🥛")
        if tot_carb < macros["carb_g"]:
            st.info("탄수화물도 약간 부족합니다. 통곡물 빵 또는 감자류를 추가 권장합니다. 🍠")
        if tot_fat < macros["fat_g"]:
            st.info("건강한 지방(아보카도, 견과, 올리브유)를 소량 추가하면 균형이 좋아집니다. 🥑")

    # 다운로드(텍스트)
    export_text = {
        "user": {"name": user_name, "age": age, "height_cm": user_height_cm, "weight_kg": user_weight_kg, "goal": goal},
        "daily_targets": macros,
        "plan": plan
    }
    buf = io.StringIO()
    buf.write(json.dumps(export_text, ensure_ascii=False, indent=2))
    buf.seek(0)
    st.download_button("식단 JSON 다운로드 💾", data=buf, file_name="my_meal_plan.json", mime="application/json")

else:
    st.info("먼저 '추천 식단 생성' 버튼을 눌러 식단을 생성하십시오. 🙂")

# ---------- 하단 안내 ----------
st.markdown("---")
st.markdown("**배포 안내**: 이 파일을 GitHub 저장소에 올리고 Streamlit Cloud(또는 Streamlit Community Cloud)에 연결하면 바로 배포됩니다.  \n간략한 절차:  \n1) GitHub 저장소 생성 → `app.py` 업로드.  \n2) https://share.streamlit.io 에 접속 → 'New app' → GitHub repo 선택 → main 브랜치와 `app.py` 파일 선택 → Deploy.  \n3) 배포 후 공개 URL을 통해 앱 접속 가능.  \n\n원하시면 제가 배포용 README(깃허브용)와 깔끔한 README 설명을 만들어 드리겠습니다. 😊")

