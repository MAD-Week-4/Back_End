from rest_framework import serializers
from .models import StockSymbol, StockDailyData, TradeLog, AiTradeLog

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
        fields = ['id','user','game' ,'stock', 'date', 'price', 'quantity', 'is_buy', 'created_at']


class AiTradeLogSerializer(serializers.ModelSerializer):
    stock = serializers.CharField(source='stock.name')
    action = serializers.SerializerMethodField()

    class Meta:
        model = AiTradeLog
        fields = ['stock', 'date', 'price', 'quantity', 'action', 'created_at']

    def get_action(self, obj):
        return "BUY" if obj.is_buy else "SELL"