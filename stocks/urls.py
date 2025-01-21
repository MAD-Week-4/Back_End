from django.urls import path
from .views import (
    StartGameView, NextDayDataView,
    BuyStockView, SellStockView, NetWorthView, GetGameStockDataView, UserTradeLogView
)

urlpatterns = [
    path('start-game/', StartGameView.as_view(), name='start_game'),
    path('<int:game_id>/next-day/', NextDayDataView.as_view(), name='next_day'),
    path('<int:game_id>/buy/', BuyStockView.as_view(), name='buy_stock'),
    path('<int:game_id>/sell/', SellStockView.as_view(), name='sell_stock'),

    path('<int:game_id>/net-worth/', NetWorthView.as_view(), name='net_worth'),

    path('<int:game_id>/get-stock/', GetGameStockDataView.as_view(), name='get_stock'),

    path('trade-logs/', UserTradeLogView.as_view(), name='trade_logs' ),
]
