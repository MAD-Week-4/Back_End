from rest_framework import serializers
from .models import StockSymbol, StockDailyData, TradeLog, AiTradeLog, UserStockHolding

class StockSymbolSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockSymbol
        fields = ['id', 'name']

class StockDailyDataSerializer(serializers.ModelSerializer):
    stock = StockSymbolSerializer(read_only=True)

    class Meta:
        model = StockDailyData
        fields = [
            'game','stock', 'date', 'open_price',
            'close_price', 'upper_limit', 'lower_limit'
        ]

class TradeLogSerializer(serializers.ModelSerializer):
    stock = StockSymbolSerializer(read_only=True)
    class Meta:
        model = TradeLog
        fields = ['id','user','game' ,'stock', 'date', 'price', 'quantity', 'is_buy', 'created_at', 'profit']


class AiTradeLogSerializer(serializers.ModelSerializer):
    stock = StockSymbolSerializer(read_only=True)

    class Meta:
        model = AiTradeLog
        fields = ['game','stock', 'date', 'price', 'quantity', 'is_buy', 'created_at', 'profit']
        
class UserStockHoldingSerializer(serializers.ModelSerializer):
    """
    UserStockHolding 모델을 JSON으로 직렬화하는 Serializer
    """
    user = serializers.CharField(source='user.username', read_only=True)  # 유저 이름 표시
    game = serializers.CharField(source='game.name', read_only=True)  # 게임 이름 표시
    stock = serializers.CharField(source='stock.name', read_only=True)  # 주식 종목 이름 표시

    class Meta:
        model = UserStockHolding  # 직렬화할 모델 지정
        fields = ['user', 'game', 'stock', 'quantity']  # 노출할 필드 지정