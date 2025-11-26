# main.py
# Healicious single-file 통합 버전
# Streamlit만 필요 (외부 모듈/CSV 불필요)
# 실행: streamlit run main.py

import streamlit as st
import random
import json
from datetime import date

st.set_page_config(page_title="Healicious", layout="wide")

# ---------- 스타일 ----------
st.markdown("""
    <style>
    .title {font-size:30px; font-weight:700;}
    .muted {color:#6b7280;}
    .card {background:#ffffff; padding:12px; border-radius:10px; box-shadow:0 4px 12px rgba(0,0,0,0.04);}
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">🥗 Healicious — 개인 맞춤 영양식 설계</div>', unsafe_allow_html=True)
st.markdown('<div class="muted">사용자 정보 기반 맞춤 식단 + 주변 음식점 추천(광고 연계) 데모</div>', unsafe_allow_html=True)
st.write("")

# ---------- 샘플 데이터 (내장) ----------
SAMPLE_RESTAURANTS = [
    {"id":1, "name":"그린밸런스 한식", "category":"한식", "location":"역삼동", "rating":4.5, "tags":["채식","저염"]},
    {"id":2, "name":"오사카 스시", "category":"일식", "location":"강남역", "rating":4.6, "tags":["해산물"]},
    {"id":3, "name":"헬씨치킨", "category":"양식", "location":"홍대", "rating":4.2, "tags":["단백질","저탄수"]},
    {"id":4, "name":"비건플레이스", "category":"채식", "location":"종로", "rating":4.7, "tags":["비건","유기농"]},
    {"id":5, "name":"간편도시락", "category":"간편식", "location":"선릉", "rating":4.0, "tags":["테이크아웃","다이어트"]},
]

SAMPLE_ADS = [
    {"ad_id":101, "restaurant_id":1, "restaurant_name":"그린밸런스 한식", "category":"한식",
     "ad_text":"첫 주문 10% 할인! 균형 잡힌 한식 도시락을 만나보십시오.", "link":"https://example.com/greenbalance", "image_url":""},
    {"ad_id":102, "restaurant_id":3, "restaurant_name":"헬씨치킨", "category":"양식",
     "ad_text":"단백질 보충엔 헬씨치킨! 단백질 증정 이벤트 중.", "link":"https://example.com/healthychicken", "image_url":""},
    {"ad_id":103, "restaurant_id":4, "restaurant_name":"비건플레이스", "category":"채식",
     "ad_text":"비건 처음이세요? 입문자용 세트 15% 할인.", "link":"https://example.com/veganplace", "image_url":""},
]

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
        return int(tdee * 0.82)
    elif goal == "체중 증가":
        return int(tdee * 1.12)
    else:
        return int(tdee)

def macro_targets(calories, weight_kg, protein_pref="보통"):
    fat_cal = calories * 0.25
    fat_g = int(fat_cal / 9)
    if protein_pref == "높게":
        prot_g = int(weight_kg * 1.8)
    elif protein_pref == "낮게":
        prot_g = int(weight_kg * 1.0)
    else:
        prot_g = int(weight_kg * 1.4)
    prot_cal = prot_g * 4
    carb_cal = max(0, calories - prot_cal - fat_cal)
    carb_g = int(carb_cal / 4)
    return {"calories": calories, "protein_g": prot_g, "carb_g": carb_g, "fat_g": fat_g}

def score_recipe_for_user(recipe, prefs):
    score = 0
    for p in prefs["likes"]:
        if p and p.lower() in recipe["name"].lower():
            score += 12
    for a in prefs["allergies"]:
        if a and a.lower() in recipe["ingredients_text"].lower():
            return -999
    for d in prefs["dislikes"]:
        if d and d.lower() in recipe["ingredients_text"].lower():
            score -= 20
    for vit in prefs["vitamins_wanted"]:
        if vit in recipe["vitamins"]:
            score += 4
    if recipe["calories"] <= prefs["calories_per_meal"] * 1.2:
        score += 6
    score += random.uniform(0,3)
    return score

def pick_meals_for_day(recipes_db, prefs):
    chosen = {"아침": None, "점심": None, "저녁": None, "간식": []}
    distribution = {"아침": 0.25, "점심": 0.35, "저녁": 0.30}
    for meal, frac in distribution.items():
        prefs["calories_per_meal"] = int(prefs["daily_calories"] * frac)
        candidates = []
        for r in recipes_db:
            s = score_recipe_for_user(r, prefs)
            if s > -100:
                candidates.append((s, r))
        if not candidates:
            chosen[meal] = None
            continue
        candidates.sort(key=lambda x: x[0], reverse=True)
        top_candidates = [c for c in candidates if c[0] >= candidates[0][0] - 6]
        sel = random.choice(top_candidates)[1]
        chosen[meal] = sel
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

def recommend_restaurant_with_ads(user_pref_category):
    # 음식점 우선 추천 -> 같은 카테고리 광고 우선 노출
    candidates = [r for r in SAMPLE_RESTAURANTS if r["category"] == user_pref_category]
    if candidates:
        rest = random.choice(candidates)
    else:
        rest = random.choice(SAMPLE_RESTAURANTS)
    # 광고 매칭
    ad_candidates = [a for a in SAMPLE_ADS if a["category"] == user_pref_category]
    if ad_candidates:
        ad = random.choice(ad_candidates)
    else:
        ad = random.choice(SAMPLE_ADS)
    return rest, ad

# ---------- 간단한 레시피 DB (내장) ----------
RECIPES = [
    {"name":"그릭 요거트 볼 (과일, 견과)", "type":"아침", "calories":380, "protein_g":20, "carb_g":45, "fat_g":12, "vitamins":["B","C"], "ingredients_text":"요거트, 블루베리, 바나나, 아몬드, 꿀"},
    {"name":"오트밀(우유) & 바나나", "type":"아침", "calories":330, "protein_g":12, "carb_g":55, "fat_g":6, "vitamins":["B"], "ingredients_text":"오트, 우유, 바나나"},
    {"name":"현미 비빔밥(닭가슴살)", "type":"점심", "calories":650, "protein_g":35, "carb_g":85, "fat_g":15, "vitamins":["A","C","B"], "ingredients_text":"현미, 닭가슴살, 야채"},
    {"name":"연어 샐러드 & 통곡물빵", "type":"점심", "calories":540, "protein_g":30, "carb_g":42, "fat_g":22, "vitamins":["D","B"], "ingredients_text":"연어, 샐러드채소, 올리브오일"},
    {"name":"닭가슴살 스테이크 & 구운야채", "type":"저녁", "calories":620, "protein_g":45, "carb_g":30, "fat_g":28, "vitamins":["B"], "ingredients_text":"닭가슴살, 브로콜리"},
    {"name":"두부야채 볶음밥", "type":"저녁", "calories":580, "protein_g":25, "carb_g":78, "fat_g":16, "vitamins":["A","C"], "ingredients_text":"두부, 채소, 현미밥"},
    {"name":"아몬드 한줌 + 사과", "type":"간식", "calories":220, "protein_g":6, "carb_g":20, "fat_g":14, "vitamins":["E","C"], "ingredients_text":"아몬드, 사과"},
    {"name":"단백질 쉐이크 (우유기반)", "type":"간식", "calories":240, "protein_g":25, "carb_g":18, "fat_g":6, "vitamins":["B"], "ingredients_text":"단백질파우더, 우유, 바나나"},
    {"name":"당근 스틱 + 후무스", "type":"간식", "calories":180, "protein_g":5, "carb_g":20, "fat_g":8, "vitamins":["A","C"], "ingredients_text":"당근, 후무스"},
]

# ---------- UI: 사용자 입력 ----------
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("1) 사용자 기본 정보 입력")
    col1, col2, col3 = st.columns(3)
    with col1:
        user_name = st.text_input("이름 (선택)", "")
        age = st.number_input("나이", value=30, min_value=10, max_value=100)
        sex = st.selectbox("성별", ("남성", "여성"))
    with col2:
        height = st.number_input("키 (cm)", value=170, min_value=100, max_value=230)
        weight = st.number_input("몸무게 (kg)", value=68.0, min_value=30.0, max_value=200.0, step=0.1)
        activity = st.selectbox("활동 수준", ("거의 활동 없음", "가벼운 활동 (주 1-3회)", "보통 활동 (주 3-5회)", "높은 활동 (주 6-7회)"))
    with col3:
        goal = st.selectbox("목표", ("체중 유지", "체중 감량", "체중 증가"))
        protein_pref = st.selectbox("단백질 선호량", ("보통", "높게", "낮게"))
        likes = st.multiselect("선호 음식(카테고리)", ["한식","일식","중식","양식","채식","간편식"], default=["한식","채식"])
    st.markdown('</div>', unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("2) 제약/기호 입력")
    col1, col2 = st.columns(2)
    with col1:
        allergies = st.text_input("알레르기 (쉼표로 구분, 예: 땅콩, 우유)", "")
        dislikes = st.text_input("싫어하는 재료 (쉼표로 구분)", "")
    with col2:
        vit_wanted = st.multiselect("특히 챙기고 싶은 영양소", ["A","B","C","D","E","칼슘","철분"], default=["B","C"])
        religion = st.selectbox("종교/식이제약", ["없음","채식주의","할랄","힌두식"])
    st.markdown('</div>', unsafe_allow_html=True)

# parse lists
likes_list = likes
allergies_list = [x.strip() for x in allergies.split(",") if x.strip()]
dislikes_list = [x.strip() for x in dislikes.split(",") if x.strip()]

# ---------- 영양 계산 ----------
bmr = calc_bmr(sex, weight, height, age)
tdee = int(bmr * activity_multiplier(activity))
daily_cal = calorie_target(tdee, goal)
macros = macro_targets(daily_cal, weight, protein_pref)

# Sidebar summary
with st.sidebar:
    st.markdown("### 요약")
    st.write(f"BMR: **{int(bmr):,} kcal**")
    st.write(f"TDEE: **{tdee:,} kcal**")
    st.write(f"추천 칼로리: **{daily_cal:,} kcal**")
    st.write(f"단백질 목표: **{macros['protein_g']} g**")
    st.write(f"탄수화물 목표: **{macros['carb_g']} g**")
    st.write(f"지방 목표: **{macros['fat_g']} g**")
    st.write("---")
    st.write("선호/제약")
    st.write(f"- 선호: {', '.join(likes_list)}")
    st.write(f"- 알레르기: {', '.join(allergies_list) if allergies_list else '없음'}")
    st.write(f"- 싫어함: {', '.join(dislikes_list) if dislikes_list else '없음'}")

# ---------- 추천 생성 ----------
prefs = {
    "likes": [l.lower() for l in likes_list],
    "allergies": [a.lower() for a in allergies_list],
    "dislikes": [d.lower() for d in dislikes_list],
    "vitamins_wanted": vit_wanted,
    "daily_calories": daily_cal,
    "calories_per_meal": int(daily_cal * 0.3),
}

st.header("3) 맞춤 식단 추천 결과")
if st.button("추천 식단 생성"):
    plan = pick_meals_for_day(RECIPES, prefs)
    st.session_state["plan"] = plan
    st.success("추천 식단이 생성되었습니다. 아래를 확인하십시오. ✅")

plan = st.session_state.get("plan", None)
if plan:
    col_a, col_b = st.columns([2,1])
    with col_a:
        for meal in ["아침","점심","저녁"]:
            st.subheader(f"🟢 {meal}")
            item = plan.get(meal)
            if item:
                st.markdown(f"**{item['name']}** — {item['calories']} kcal | 단백질 {item['protein_g']}g")
                st.markdown(f"_재료_: {item['ingredients_text']}")
                if item.get("vitamins"):
                    st.caption("영양 포함: " + ", ".join(item["vitamins"]))
            else:
                st.info(f"{meal}에 적합한 추천을 찾지 못했습니다.")
        st.subheader("🟡 간식")
        for s in plan.get("간식", []):
            st.markdown(f"- {s['name']} ({s['calories']} kcal)")
    with col_b:
        # 요약 지표
        tot_cals = sum([v["calories"] for k,v in plan.items() if v and isinstance(v, dict)])
        tot_prot = sum([v["protein_g"] for k,v in plan.items() if v and isinstance(v, dict)])
        for s in plan.get("간식", []):
            tot_cals += s["calories"]; tot_prot += s["protein_g"]
        st.metric("추천 총 칼로리", f"{tot_cals:,} kcal", delta=f"{tot_cals - daily_cal:+,} kcal")
        st.metric("단백질 (g)", f"{tot_prot} g", delta=f"{tot_prot - macros['protein_g']:+} g")

    # 음식점 추천 + 광고 연결
    # 사용자의 첫 선호 카테고리를 기준으로 추천
    pref_cat = likes_list[0] if likes_list else "한식"
    restaurant, ad = recommend_restaurant_with_ads(pref_cat)
    st.markdown("---")
    st.header("4) 추천 음식점 (광고 연계)")
    st.subheader("추천 음식점")
    st.write(f"**{restaurant['name']}** — {restaurant['location']} | 평점 {restaurant['rating']}")
    st.write("추천 이유: 선호 카테고리와 근접한 메뉴 보유")

    st.subheader("제휴 광고")
    st.write(f"**{ad['restaurant_name']}**")
    st.write(ad["ad_text"])
    st.write(f"[광고 링크] {ad['link']}")

    # 다운로드(JSON)
    export_obj = {
        "user": {"name": user_name, "age": age, "height_cm": height, "weight_kg": weight, "goal": goal},
        "targets": macros,
        "plan": plan,
        "recommended_restaurant": restaurant,
        "ad": ad
    }
    export_str = json.dumps(export_obj, ensure_ascii=False, indent=2)
    st.download_button("식단 및 추천 JSON 다운로드", data=export_str, file_name="healicious_plan.json", mime="application/json")
else:
    st.info("추천 식단을 생성하려면 위에서 '추천 식단 생성' 버튼을 누르십시오.")

st.markdown("---")
st.caption("Healicious 데모 — 교육/시연용. 실제 서비스시에는 광고 계약, 결제, 개인정보 보호 정책을 반드시 구현하십시오.")
