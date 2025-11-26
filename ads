import pandas as pd
import random

def recommend_restaurant_with_ads(user, meals):
    restaurants = pd.read_csv("data/restaurant_list.csv")
    ads = pd.read_csv("data/ads.csv")

    # 사용자의 선호 기반 음식점 선택
    pref = user["preference"][0]
    candidates = restaurants[restaurants["category"] == pref]

    if candidates.empty:
        restaurant = restaurants.sample(1).iloc[0]
    else:
        restaurant = candidates.sample(1).iloc[0]

    # 광고는 같은 카테고리 우선 노출
    ad_candidates = ads[ads["category"] == pref]

    if ad_candidates.empty:
        ad = ads.sample(1).iloc[0]
    else:
        ad = ad_candidates.sample(1).iloc[0]

    return restaurant, ad
