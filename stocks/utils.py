import random
import datetime

def generate_random_stock_data(stock, days, start_price=100.0):
    """
    특정 종목에 대해 지정된 일 수(days)만큼 랜덤 데이터를 생성합니다.
    추세와 변동성을 고려해 현실적인 시계열 데이터를 생성합니다.

    Args:
        stock (str): 종목 이름.
        days (int): 생성할 데이터 일 수.
        start_price (float): 시작 가격 (기본값: 100.0).

    Returns:
        list: 생성된 주식 데이터 리스트.
    """
    today = datetime.date.today()
    random_data = []
    prev_close = start_price  # 시작 가격

    # 추세 및 변동성 초기값
    trend = 0  # 추세 (양수: 상승, 음수: 하락)
    volatility = 0.03  # 초기 변동성 (3%)로 확대

    for day in range(days):
        date = today - datetime.timedelta(days=day)

        # 추세와 변동성을 기반으로 하루 변동률 계산
        daily_trend = random.gauss(trend, volatility)
        close_price = prev_close * (1 + daily_trend)

        # 음수가 되지 않도록 최소값 제한
        close_price = max(close_price, 1.0)

        # 봉의 크기 조정: 시가와 종가 차이를 더 크게 설정
        amplitude_factor = abs(trend) + 1.5  # 추세의 절대값에 따라 더 큰 증가
        if trend >= 0:  # 상승 추세
            open_price = close_price * random.uniform(1 - 0.02 * amplitude_factor, 1 + 0.03 * amplitude_factor)
        else:  # 하락 추세
            open_price = close_price * random.uniform(1 - 0.03 * amplitude_factor, 1 + 0.02 * amplitude_factor)


        # 시가와 종가의 차이를 강제로 확대하여 봉 크기를 키움
        if abs(open_price - close_price) < 1.0:  # 최소 차이를 보장
            if open_price > close_price:
                open_price += 1.0
            else:
                close_price += 1.0

        # 꼬리 길이에 랜덤 변화를 추가 (추세에 따라 꼬리 길이도 변화)
        tail_factor = random.uniform(1 - 0.02 * amplitude_factor, 1 + 0.02 * amplitude_factor)
        lower_limit = min(open_price, close_price) * tail_factor * 0.95
        upper_limit = max(open_price, close_price) * tail_factor * 1.05

        # 상한가와 하한가가 너무 멀지 않도록 제한
        lower_limit = max(lower_limit, close_price * 0.8)
        upper_limit = min(upper_limit, close_price * 1.2)

        random_data.append({
            "stock": stock,
            "date": date,
            "open_price": round(open_price, 2),
            "close_price": round(close_price, 2),
            "upper_limit": round(upper_limit, 2),
            "lower_limit": round(lower_limit, 2),
        })

        # 추세 업데이트: 상승/하락 지속성 추가
        if random.random() < 0.1:  # 10% 확률로 추세 방향 변경
            trend = random.uniform(-0.05, 0.05)  # 추세를 변경 (약 ±5%)
        else:
            trend *= random.uniform(0.9, 1.2)  # 현재 추세 지속

        # 변동성 업데이트: 추세가 강할수록 변동성 증가
        if abs(trend) > 0.03:
            volatility = min(volatility * 1.2, 0.15)  # 최대 변동성 15%
        else:
            volatility = max(volatility * 0.9, 0.02)  # 최소 변동성 2%

        # 다음 날의 prev_close를 현재 close_price로 갱신
        prev_close = close_price

    return random_data