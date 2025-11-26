import streamlit as st
from modules.user_profile import get_user_profile
from modules.nutrition import analyze_nutrition, recommend_meals
from modules.recommendation import personalized_plan
from modules.restaurant_ads import recommend_restaurant_with_ads

st.set_page_config(page_title="Healicious", layout="wide")

st.title("🥗 Healicious – AI 건강 식단 추천 시스템")

st.header("1️⃣ 사용자 정보 입력")
user_info = get_user_profile()

if user_info is None:
    st.warning("사용자 정보를 모두 입력해주십시오.")
    st.stop()

st.header("2️⃣ 오늘의 건강 분석 및 식단 추천")
nutrition_result = analyze_nutrition(user_info)

st.subheader("🔍 사용자의 건강 분석 결과")
st.write(nutrition_result)

meal_recommend = recommend_meals(user_info, nutrition_result)

st.subheader("🍱 추천 식단")
for meal in meal_recommend:
    st.info(f"• {meal}")

st.header("3️⃣ 개인 맞춤형 식단 계획")
plan = personalized_plan(user_info, nutrition_result, meal_recommend)
st.success(plan)

st.header("4️⃣ 음식점 추천 + 광고 연결 🔥(수익 모델)")
restaurant, ad = recommend_restaurant_with_ads(user_info, meal_recommend)

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📍 추천 음식점")
    st.write(f"**{restaurant['name']}**")
    st.write(f"📍 위치: {restaurant['location']}")
    st.write(f"⭐ 평점: {restaurant['rating']}")
    st.write(f"💬 추천 이유: {restaurant['reason']}")

with col2:
    st.subheader("💰 광고 제휴 식당")
    st.image(ad["image_url"])
    st.write(f"### {ad['restaurant_name']}")
    st.write(ad["ad_text"])
    st.link_button("광고 식당 자세히 보기", ad["link"])

st.success("Healicious가 사용자 맞춤형 식단 + 주변 음식점 + 광고를 연결해 최적의 경험을 제공합니다!")
