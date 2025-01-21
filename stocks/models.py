from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Game(models.Model):
    """
    각 모의투자 게임을 나타내는 모델.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="games")
    name = models.CharField(max_length=100, default="My Investment Game")
    capital = models.FloatField(default=1000000)
    profit_rate = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Game {self.id} by {self.user.username}"

    def update_profit_rate(self):
        """
        자본(capital)에 따라 현재 수익률을 갱신.
        초기 자본 대비 현재 자본 기준 계산:
            수익률(%) = ((현재 자본 - 초기 자본) / 초기 자본) * 100
        """
        initial_capital = 1000000  # 초기 자본 값
        self.profit_rate = ((self.capital - initial_capital) / initial_capital) * 100
        self.save()


# Create your models here.
class StockSymbol(models.Model):
    """
    10개 종목 (예: 삼성전자, SK하이닉스, ...)
    """
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class UserStockHolding(models.Model):
    """
    유저가 특정 게임에서 특정 종목을 몇 주(수량) 보유하고 있는지를 나타냄
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stock_holdings')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='stock_holdings')
    stock = models.ForeignKey(StockSymbol, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('user', 'game', 'stock')

    def __str__(self):
        return f"{self.user.username} / {self.game.name} / {self.stock.name} : {self.quantity}"

class StockDailyData(models.Model):
    """
    각 종목의 특정 날짜(date)에 대한 주가 정보
    - 시가(open_price), 종가(close_price), 상한가(upper_limit), 하한가(lower_limit)
    - 실제로는 거래량, 고가, 저가 등 더 많은 필드 가능
    """
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="stocks")
    stock = models.ForeignKey(StockSymbol, on_delete=models.CASCADE, related_name='daily_data')
    date = models.DateField()  # "2023-01-01" 형태
    open_price = models.FloatField()
    close_price = models.FloatField()
    upper_limit = models.FloatField()
    lower_limit = models.FloatField()

    class Meta:
        unique_together = ('game','stock', 'date')

    def __str__(self):
        return f"{self.stock.name} @ {self.date}"

class TradeLog(models.Model):
    """
    매수/매도 로그를 기록(선택 사항)
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="trades")
    stock = models.ForeignKey(StockSymbol, on_delete=models.CASCADE)
    date = models.DateField()
    price = models.FloatField()
    quantity = models.IntegerField()
    is_buy = models.BooleanField()  # 매수(True) or 매도(False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.stock.name} - {self.date} - {'BUY' if self.is_buy else 'SELL'}"