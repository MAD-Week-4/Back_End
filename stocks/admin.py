from django.contrib import admin
from .models import Game, StockSymbol, UserStockHolding, StockDailyData, TradeLog

# Register your models here.
admin.site.register(Game)
admin.site.register(StockSymbol)
admin.site.register(UserStockHolding)
admin.site.register(StockDailyData)
admin.site.register(TradeLog)