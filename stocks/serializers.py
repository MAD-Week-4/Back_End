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
    stock = StockSymbolSerializer(read_only=True)

    class Meta:
        model = AiTradeLog
        fields = ['game','stock', 'date', 'price', 'quantity', 'is_buy', 'created_at']