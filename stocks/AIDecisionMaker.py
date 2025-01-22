from .models import StockDailyData
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import numpy as np


class AIDecisionMaker:
    """
    AI가 주식 데이터를 학습하여 거래 결정을 내리고 기록하는 클래스.
    """

    def __init__(self, game):
        self.game = game
        self.ai_capital = 1000000  # AI 초기 자본
        self.ai_holding = {}  # 주식 보유 상태 {stock_id: quantity}

    def decide_action(self, stock_data):
        """
        간단한 매수/매도/유지 결정 로직:
        1. 'BUY': 종가가 시가 대비 하락했을 때 매수
        2. 'SELL': 종가가 시가 대비 상승했을 때 매도
        3. 'HOLD': 아무것도 하지 않음
        """
        if stock_data.close_price < stock_data.open_price * 0.95:
            return "BUY"
        elif stock_data.close_price > stock_data.open_price * 1.05:
            return "SELL"
        return "HOLD"

    def calculate_profit_rate(self):
        """
        AI의 현재 수익률 계산.
        초기 자본: 1000000
        """
        current_stock_value = 0
        for stock_id, quantity in self.ai_holding.items():
            if quantity > 0:
                latest_data = StockDailyData.objects.filter(
                    game=self.game, stock_id=stock_id
                ).latest('date')
                current_stock_value += latest_data.close_price * quantity

        total_assets = self.ai_capital + current_stock_value
        return ((total_assets - 1000000) / 1000000) * 100

    def decide_lstm_based_action(self, stock_data):
        """
        RandomForestRegressor를 사용해 주어진 주식 데이터를 기반으로 모델을 학습하고
        즉시 예측하여 거래 결정을 내린다.
        :param stock_data: StockDailyData QuerySet (전체 데이터, 최신 날짜부터 과거로 정렬된 데이터)
        :return: "BUY", "SELL", "HOLD" 중 하나
        """
        if len(stock_data) < 10:  # 최소 10일 데이터가 필요
            return "HOLD"  # 데이터가 충분하지 않을 경우 관망

        # 데이터프레임 변환 및 날짜순 정렬
        stock_data_df = pd.DataFrame(list(stock_data.values()))
        stock_data_df = stock_data_df.sort_values(by="date")  # 날짜 오름차순 정렬

        # 1) 데이터 준비
        prices = stock_data_df['close_price'].values  # 종가 데이터만 추출
        X = [prices[i:i + 5] for i in range(len(prices) - 5)]  # 최근 5일 데이터를 feature로 사용
        y = prices[5:]  # 그 다음 날 종가를 타겟 데이터로 설정
        X, y = np.array(X), np.array(y)

        # 최근 5일 데이터를 예측용 입력으로 준비
        X_input = X[-1].reshape(1, -1)

        # 2) 모델 학습
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)  # Train-Test split
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)  # 모델 학습

        # 3) 예측
        predicted_price = model.predict(X_input)[0]  # RandomForest로 종가 예측

        # 4) 결정 로직
        last_close_price = prices[-1]  # 마지막 날 종가
        predicted_price_delta = predicted_price - last_close_price

        if predicted_price_delta > last_close_price * 0.02:  # 5% 이상 상승 예측 시 매도
            return "BUY"
        elif predicted_price_delta < -last_close_price * 0.02:  # 5% 이상 하락 예측 시 매수
            return "SELL"
        else:
            return "HOLD"  # 5% 이내의 가격 변화는 관망

