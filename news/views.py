import requests
from bs4 import BeautifulSoup
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import html
import re

# 네이버 API 정보
API_URL = 'https://openapi.naver.com/v1/search/news.json'
CLIENT_ID = 'VqHVz3Tfx4sHK9ebjLh0'
CLIENT_SECRET = 'S0nCIcmrWG'


def search_news(query="주식", display=5, start=1, sort="sim"):
    """네이버 뉴스 API를 호출하여 뉴스 데이터를 가져오는 함수"""
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET
    }

    params = {
        "query": query,
        "display": display,
        "start": start,
        "sort": sort
    }

    try:
        response = requests.get(API_URL, headers=headers, params=params)
        response.raise_for_status()
        return response.json().get("items", [])
    except requests.exceptions.RequestException as e:
        print(f"⚠️ 네이버 API 요청 실패: {e}")
        return []


def clean_html_tags(text):
    """HTML 태그 및 특수 문자 제거"""
    text = html.unescape(text)  # HTML 엔티티 디코딩
    text = re.sub(r"<[^>]+>", "", text)  # HTML 태그 제거
    return text.strip()


def fetch_news_image(news_url):
    """뉴스 기사 원본 페이지에서 대표 이미지를 가져오는 함수"""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}  # 일부 웹사이트는 User-Agent 필요
        response = requests.get(news_url, headers=headers, timeout=5)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # <meta property="og:image"> 태그에서 대표 이미지 가져오기
        image_tag = soup.find("meta", property="og:image")
        if image_tag and image_tag["content"]:
            return image_tag["content"]

    except requests.exceptions.RequestException as e:
        print(f"⚠️ 이미지 크롤링 실패: {e}")

    return ""  # 기본값


@csrf_exempt
def get_news(request):
    """React에서 요청하면 뉴스 기사 타이틀, URL 및 대표 이미지 반환"""
    query = request.GET.get('query', '주식')
    print(f"📝 API 요청 받음: query={query}")

    news_items = search_news(query=query, display=5, sort="date")

    if not news_items:
        return JsonResponse({"error": "No news found"}, status=404)

    # 뉴스 데이터 구성 (대표 이미지 포함)
    news_data = []
    for item in news_items:
        title = clean_html_tags(item.get("title", "No Title"))
        link = item.get("link", "#")
        image_url = fetch_news_image(link)  # 대표 이미지 크롤링

        news_data.append({
            "title": title,
            "link": link,
            "image": image_url if image_url else "https://source.unsplash.com/featured/?news"
        })

    return JsonResponse(news_data, safe=False)