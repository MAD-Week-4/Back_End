import random
import datetime

def generate_random_stock_data(stock, days):
    """
    특정 종목에 대해 지정된 일 수(days)만큼 랜덤 데이터를 생성합니다.
    """
    today = datetime.date.today()
    random_data = []

    for day in range(days):
        date = today - datetime.timedelta(days=day)
        open_price = random.uniform(90, 110)
        close_price = open_price * random.uniform(0.95, 1.05)
        lower_limit = min(open_price, close_price) * 0.9
        upper_limit = max(open_price, close_price) * 1.1

        random_data.append({
            "stock": stock,
            "date": date,
            "open_price": round(open_price, 2),
            "close_price": round(close_price, 2),
            "upper_limit": round(upper_limit, 2),
            "lower_limit": round(lower_limit, 2),
        })

    return random_data
