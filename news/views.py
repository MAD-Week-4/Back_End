import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# 네이버 API 정보
API_URL = 'https://openapi.naver.com/v1/search/news.json'
CLIENT_ID = 'VqHVz3Tfx4sHK9ebjLh0'  # 네이버 개발자 센터에서 발급받은 Client ID
CLIENT_SECRET = 'S0nCIcmrWG'  # 네이버 개발자 센터에서 발급받은 Client Secret

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
        response.raise_for_status()  # HTTP 오류 발생 시 예외 발생
        return response.json().get("items", [])
    except requests.exceptions.RequestException as e:
        print(f"⚠️ 네이버 API 요청 실패: {e}")
        return []

@csrf_exempt
def get_news(request):
    """React에서 요청하면 뉴스 기사 타이틀 & URL만 반환하는 API"""
    query = request.GET.get('query', '주식')  # 기본 검색어 '주식'
    print(f"📝 API 요청 받음: query={query}")

    news_items = search_news(query=query, display=5, sort="date")  # 최신 뉴스 5개 가져오기

    if not news_items:
        return JsonResponse({"error": "No news found"}, status=404)

    # 🔹 뉴스 기사 제목 & URL만 포함
    news_data = [{"title": item.get("title", "No Title"), "link": item.get("link", "#")} for item in news_items]

    return JsonResponse(news_data, safe=False)
