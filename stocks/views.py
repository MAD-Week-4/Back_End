from django.shortcuts import render

from .AIDecisionMaker import AIDecisionMaker
from .models import StockSymbol, StockDailyData,TradeLog, Game, UserStockHolding, AiStockHolding, AiTradeLog
from accounts.models import Profile
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from .utils import generate_random_stock_data
from datetime import date, timedelta
import random

from .serializers import StockDailyDataSerializer, StockSymbolSerializer, TradeLogSerializer, AiTradeLogSerializer

class StartGameView(APIView):
    """
    새로운 게임을 생성하고 10개 종목에 대해 30일치 데이터를 초기화합니다.
    """
    def post(self, request):
        user = request.user
        game_name = request.data.get("name", "My Investment Game")


        # 새로운 게임 생성
        with transaction.atomic():
            game = Game.objects.create(user=user, name=game_name)
            symbols = StockSymbol.objects.all()
            all_data = []
            # 각 종목에 대해 30일치 랜덤 데이터 생성
            for symbol in symbols:
                random_data = generate_random_stock_data(symbol, 500)
                for daily in random_data:
                    StockDailyData.objects.create(
                        game=game,
                        stock=daily["stock"],
                        date=daily["date"],
                        open_price=daily["open_price"],
                        close_price=daily["close_price"],
                        upper_limit=daily["upper_limit"],
                        lower_limit=daily["lower_limit"],
                    )

                # 응답용 처리: 모델 인스턴스 -> 문자열(예: symbol.name)
                # => JSON 직렬화 에러 방지
                data_for_response = []
                for d in random_data:
                    data_for_response.append({
                        "stock": d["stock"].name,
                        "date": d["date"],
                        "open_price": d["open_price"],
                        "close_price": d["close_price"],
                        "upper_limit": d["upper_limit"],
                        "lower_limit": d["lower_limit"]
                    })

                all_data.append({
                    "stock": symbol.name,
                    "stock_id": symbol.id,
                    "data": data_for_response
                })

        return Response({
            "message": "Game started.",
            "game_id": game.id,
            "game_name": game.name,
            "initial_capital": game.capital,
            "data": all_data
        }, status=status.HTTP_200_OK)

class GetGameStockDataView(APIView):
    """
    특정 game_id에 해당하는 StockDailyData를 종목별로 가져옵니다.
    """
    def get(self, request, game_id):
        try:
            # 게임이 존재하는지 확인
            game = Game.objects.get(id=game_id)
        except Game.DoesNotExist:
            return Response({"message": "Game not found."}, status=status.HTTP_404_NOT_FOUND)

        # StockDailyData에서 가장 최신 날짜 가져오기
        latest_stock_date = StockDailyData.objects.filter(game=game).order_by('-date').first()

        if latest_stock_date:
            # 게임 생성일과 비교한 경과 날짜 계산
            days_elapsed = (latest_stock_date.date - game.created_at.date()).days
        else:
            # StockDailyData가 없는 경우 경과 날짜는 0
            days_elapsed = 0

        all_data = []

        # 모든 종목 가져오기
        symbols = StockSymbol.objects.all()

        # 각 종목에 대한 데이터 가져오기
        for symbol in symbols:
            stock_data = StockDailyData.objects.filter(game=game, stock=symbol).order_by('date')
            data_for_response = []

            for daily in stock_data:
                data_for_response.append({
                    "stock": daily.stock.name,
                    "date": daily.date,
                    "open_price": daily.open_price,
                    "close_price": daily.close_price,
                    "upper_limit": daily.upper_limit,
                    "lower_limit": daily.lower_limit
                })

            if data_for_response:  # 해당 종목에 데이터가 있을 경우만 추가
                all_data.append({
                    "stock": symbol.name,
                    "stock_id": symbol.id,
                    "data": data_for_response
                })

        return Response({
            "message": "Stock data for the game retrieved successfully.",
            "days_elapsed": days_elapsed,
            "data": all_data
        }, status=status.HTTP_200_OK)

class NextDayDataView(APIView):
    """
    가장 최근 StockDailyData 날짜 + 1일짜리 데이터를 생성하고 DB에 추가한 뒤 반환.
    """

    def post(self, request, game_id):
        user = request.user
        try:
            game = Game.objects.get(id=game_id, user=request.user)
        except Game.DoesNotExist:
            return Response({"detail": "Game not found."}, status=status.HTTP_404_NOT_FOUND)

        # 1) 이 게임에서 가장 최근 date를 구함
        latest_data = StockDailyData.objects.filter(game=game).order_by('-date').first()

        if latest_data:
            # 이미 데이터가 있을 경우: "가장 최근 날짜 + 1일"
            next_day = latest_data.date + timedelta(days=1)
        else:
            # 게임에 아직 StockDailyData가 없는 경우: 오늘(date.today())로 시작
            next_day = date.today()

        symbols = StockSymbol.objects.all()
        created_data = []

        # 2) 과거 데이터를 기반으로 AI의 행동 결정 수행
        ai_decision_maker = AIDecisionMaker(game=game)
        decisions = []

        with transaction.atomic():
            # 기존 데이터를 AI가 분석하고 행동을 결정
            for symbol in symbols:
                # 과거 데이터를 가져옴
                stock_data = StockDailyData.objects.filter(
                    game=game, stock=symbol
                ).order_by('date')  # 과거 데이터를 정렬 (오름차순)

                if stock_data.exists():
                    # LSTM 기반 결정 (현재까지의 데이터를 사용)
                    action = ai_decision_maker.decide_lstm_based_action(stock_data=stock_data)
                else:
                    action = "HOLD"  # 데이터가 없는 경우 관망

                # AI 주식 보유 상태 가져오기
                ai_holding, _ = AiStockHolding.objects.get_or_create(game=game, stock=symbol)

                if action == "BUY":
                    # 매수 가능한 최대 주식 수 계산
                    max_buy_quantity = int(game.ai_capital // stock_data.last().close_price)
                    buy_quantity = random.randint(1, max_buy_quantity)  # 1 ~ 10주 사이 랜덤 매수
                    if buy_quantity > 0 and game.ai_capital >= buy_quantity * stock_data.last().close_price:
                        game.ai_capital -= buy_quantity * stock_data.last().close_price
                        ai_holding.quantity += buy_quantity
                        ai_holding.save()

                        # 거래 내역 기록
                        AiTradeLog.objects.create(
                            game=game,
                            stock=symbol,
                            date=latest_data.date if latest_data else next_day,
                            price=stock_data.last().close_price,
                            quantity=buy_quantity,
                            is_buy=True,
                            profit=game.ai_profit_rate
                        )

                elif action == "SELL":
                    # 매도 가능한 최대 주식 수 계산
                    max_sell_quantity = ai_holding.quantity
                    sell_quantity = 0
                    if max_sell_quantity > 0:  # 매도 가능한 주식이 있는지 확인
                        sell_quantity = random.randint(1, max_sell_quantity)  # 1 ~ 10주 사이 랜덤 매도
                        if ai_holding.quantity >= sell_quantity:
                            game.ai_capital += sell_quantity * stock_data.last().close_price
                            ai_holding.quantity -= sell_quantity
                            ai_holding.save()

                            # 거래 내역 기록
                            AiTradeLog.objects.create(
                                game=game,
                                stock=symbol,
                                date=latest_data.date if latest_data else next_day,
                                price=stock_data.last().close_price,
                                quantity=sell_quantity,
                                is_buy=False,
                                profit=game.ai_profit_rate
                            )
                        else:
                            sell_quantity = 0  # 매도 실패 시 기록용

                decisions.append({
                    "stock": symbol.name,
                    "action": action,
                    "quantity": buy_quantity if action == "BUY" else (sell_quantity if action == "SELL" else 0)
                })

            # 새로운 날의 주가 데이터를 생성
            for symbol in symbols:
                # 기존 데이터를 가져오기
                stock_data = StockDailyData.objects.filter(
                    game=game, stock=symbol
                ).order_by('date')

                # 이전 종가를 기준으로 다음 날 데이터 생성
                if stock_data.exists():
                    prev_close_price = stock_data.last().close_price
                else:
                    prev_close_price = 100.0  # 기본 시작 가격

                # 현실적인 랜덤 데이터를 생성
                trend = random.uniform(-0.03, 0.03)  # 소폭 상승/하락 추세
                volatility = 0.02  # 초깃값 변동성
                daily_trend = random.gauss(trend, volatility)
                close_price = prev_close_price * (1 + daily_trend)
                close_price = max(close_price, 1.0)  # 음수 방지

                # open_price 계산
                amplitude_factor = abs(trend) + 1.5  # 추세 영향을 고려
                if trend >= 0:  # 상승 추세
                    open_price = close_price * random.uniform(1 - 0.02 * amplitude_factor, 1 + 0.03 * amplitude_factor)
                else:  # 하락 추세
                    open_price = close_price * random.uniform(1 - 0.03 * amplitude_factor, 1 + 0.02 * amplitude_factor)

                # 최소 시가/종가 차이를 보장
                if abs(open_price - close_price) < 1.0:
                    if open_price > close_price:
                        open_price += 1.0
                    else:
                        close_price += 1.0

                # 상한가 및 하한가 계산
                tail_factor = random.uniform(1 - 0.02 * amplitude_factor, 1 + 0.02 * amplitude_factor)
                lower_limit = min(open_price, close_price) * tail_factor * 0.95
                upper_limit = max(open_price, close_price) * tail_factor * 1.05

                # 상한가와 하한가 범위 제한
                lower_limit = max(lower_limit, close_price * 0.8)
                upper_limit = min(upper_limit, close_price * 1.2)

                # 데이터 저장
                daily_data = StockDailyData.objects.create(
                    game=game,
                    stock=symbol,
                    date=next_day,
                    open_price=round(open_price, 2),
                    close_price=round(close_price, 2),
                    upper_limit=round(upper_limit, 2),
                    lower_limit=round(lower_limit, 2),
                )
                created_data.append(daily_data)

        game.update_profit_rate()
        game.update_ai_profit_rate()
        serializer = StockDailyDataSerializer(created_data, many=True)
        return Response({
            "message": "Next day data generated.",
            "next_day": str(next_day),
            "stocks": serializer.data,
            "ai_decisions": decisions,
            "user_profit_rate": game.profit_rate,
            "ai_profit_rate": game.ai_profit_rate,
        }, status=status.HTTP_200_OK)



class BuyStockView(APIView):
    """
    매수 처리
    요청 형식:
    {
        "stock_id": 1,
        "quantity": 10,
    }
    """
    def post(self, request, game_id):

        user = request.user

        try:
            game = Game.objects.get(id=game_id, user=request.user)
        except Game.DoesNotExist:
            return Response({"detail": "Game not found."}, status=status.HTTP_404_NOT_FOUND)

        stock_id = request.data.get('stock_id')
        quantity = int(request.data.get('quantity', 0))

        # 가장 최근 StockDailyData 가져오기
        try:
            stock = StockSymbol.objects.get(id=stock_id)
            latest_data = StockDailyData.objects.filter(game=game, stock=stock).latest('date')
        except (StockSymbol.DoesNotExist, StockDailyData.DoesNotExist):
            return Response({"detail": "Stock or data not found."}, status=status.HTTP_404_NOT_FOUND)

        price = latest_data.close_price
        date_str = latest_data.date

        if not (stock_id and price > 0 and quantity > 0 and date_str):
            return Response({"detail": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)

        cost = price * quantity
        if game.capital < cost:
            return Response({"detail": "Not enough assets"}, status=status.HTTP_400_BAD_REQUEST)

        # 자본 차감
        game.capital -= cost
        game.save()

        # 보유 종목 수량 증가
        stock = StockSymbol.objects.get(id=stock_id)
        holding, created = UserStockHolding.objects.get_or_create(
            user=user, game=game, stock=stock
        )
        holding.quantity += quantity
        holding.save()

        # 매수 로그 기록
        TradeLog.objects.create(
            user=user,
            game=game,
            stock=stock,
            date=date_str,
            price=price,
            quantity=quantity,
            is_buy=True,
            profit=game.profit_rate
        )

        game.update_profit_rate()

        return Response({
            "message": "Buy success",
            "capital_after_buy": game.capital,
            "profit_rate": game.profit_rate,
            "holding_quantity": holding.quantity,
            "stock_id": stock_id,
        }, status=status.HTTP_200_OK)

class SellStockView(APIView):
    """
    매도 처리
    요청 형식:
    {
        "stock_id": 1,
        "price": 100,
        "quantity": 10,
        "date": "2023-09-05"
    }
    """
    def post(self, request, game_id):
        user = request.user
        try:
            game = Game.objects.get(id=game_id, user=user)
        except Game.DoesNotExist:
            return Response({"detail": "Game not found"}, status=404)

        stock_id = request.data.get('stock_id')
        quantity = int(request.data.get('quantity', 0))

        # 가장 최근 StockDailyData 가져오기
        try:
            stock = StockSymbol.objects.get(id=stock_id)
            latest_data = StockDailyData.objects.filter(game=game, stock=stock).latest('date')
        except (StockSymbol.DoesNotExist, StockDailyData.DoesNotExist):
            return Response({"detail": "Stock or data not found."}, status=status.HTTP_404_NOT_FOUND)

        price = latest_data.close_price
        date_str = latest_data.date

        if not (stock_id and price > 0 and quantity > 0 and date_str):
            return Response({"detail": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)

        # 보유 수량 확인

        stock = StockSymbol.objects.get(id=stock_id)
        try:
            holding = UserStockHolding.objects.get(user=user, game=game, stock=stock)
        except UserStockHolding.DoesNotExist:
            return Response({"detail": "No holding for this stock"}, status=400)

        if holding.quantity < quantity:
            return Response({"detail": "Not enough shares to sell"}, status=400)

        # 매도 -> 수량 감소
        holding.quantity -= quantity
        holding.save()

        # 현금 증가
        revenue = price * quantity
        game.capital += revenue
        game.save()

        # TradeLog
        TradeLog.objects.create(
            user=user,
            game=game,
            stock=stock,
            date=date_str,
            price=price,
            quantity=quantity,
            is_buy=False,
            profit=game.profit_rate,
        )

        game.update_profit_rate()

        return Response({
            "message": "Sell success",
            "capital_after_sell": game.capital,
            "profit_rate": game.profit_rate,
            "holding_quantity": holding.quantity,
            "stock_id": stock_id,
        }, status=200)



class NetWorthView(APIView):
    def get(self, request, game_id):
        user = request.user
        try:
            game = Game.objects.get(id=game_id, user=user)
        except Game.DoesNotExist:
            return Response({"detail": "Game not found"}, status=404)

        # 가장 최근 날짜 or 원하는 날짜를 기준으로 주가 조회
        from django.db.models import Max
        latest_date = StockDailyData.objects.filter(game=game).aggregate(Max('date'))['date__max']

        total_shares_value = 0
        holdings = UserStockHolding.objects.filter(user=user, game=game)
        for hold in holdings:
            # 해당 종목의 최신 주가 (close_price 기준)
            latest_data = StockDailyData.objects.filter(
                game=game, stock=hold.stock, date=latest_date
            ).first()
            if latest_data:
                total_shares_value += latest_data.close_price * hold.quantity

        net_worth = game.capital + total_shares_value

        # AI의 주식 가치 계산
        ai_total_shares_value = 0
        ai_holdings = AiStockHolding.objects.filter(game=game)  # AI 보유 주식
        for ai_hold in ai_holdings:
            # 해당 종목의 최신 주가 (close_price 기준)
            latest_data = StockDailyData.objects.filter(
                game=game, stock=ai_hold.stock, date=latest_date
            ).first()
            if latest_data:
                ai_total_shares_value += latest_data.close_price * ai_hold.quantity

        # AI 총 자산 가치 = 현금 + 주식 가치
        ai_net_worth = game.ai_capital + ai_total_shares_value

        return Response({
            "latest_date": str(latest_date),
            "capital": game.capital,
            "stock_value": total_shares_value,
            "profit_rate": game.profit_rate,
            "net_worth": net_worth,
            # AI 관련 정보 추가
            "ai_capital": game.ai_capital,
            "ai_stock_value": ai_total_shares_value,
            "ai_net_worth": ai_net_worth,
            "ai_profit_rate": game.ai_profit_rate
        })

class UserTradeLogView(APIView):
    """
    로그인한 유저의 TradeLog를 게임별로 반환하는 View
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # 유저가 참여한 모든 게임 가져오기
        games = Game.objects.filter(user=user)

        # 게임별로 TradeLog 데이터를 그룹화
        all_trade_logs = []
        for game in games:
            trade_logs = TradeLog.objects.filter(user=user, game=game)
            serialized_logs = TradeLogSerializer(trade_logs, many=True).data

            all_trade_logs.append({
                "game_id": game.id,
                "game_name": game.name,
                "game_start_data": game.created_at.date(),
                "profit_rate": game.profit_rate,
                "logs": serialized_logs
            })

        return Response({
            "message": "User's trade logs organized by game.",
            "trade_logs": all_trade_logs
        })

class AiTradeLogView(APIView):
    """
    AI의 TradeLog를 게임별로 반환하는 View
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # 유저가 참여한 모든 게임 가져오기
        games = Game.objects.filter(user=user)

        # 게임별로 AiTradeLog 데이터를 그룹화
        all_ai_trade_logs = []
        for game in games:
            ai_trade_logs = AiTradeLog.objects.filter(game=game)
            serialized_logs = AiTradeLogSerializer(ai_trade_logs, many=True).data

            all_ai_trade_logs.append({
                "game_id": game.id,
                "game_name": game.name,
                "game_start_date": game.created_at.date(),
                "ai_profit_rate": game.ai_profit_rate,
                "logs": serialized_logs
            })

        return Response({
            "message": "AI's trade logs organized by game.",
            "ai_trade_logs": all_ai_trade_logs
        })
        
class UserStockHoldingsView(APIView):
    """
    특정 게임 ID에 해당하는 유저의 보유 주식 데이터를 반환하는 View
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, game_id):
        user = request.user

        # URL에서 받은 game_id에 해당하는 Game 인스턴스 가져오기
        try:
            game = Game.objects.get(id=game_id, user=user)
        except Game.DoesNotExist:
            return Response({"message": "Game not found or you don't have permission to access this game."}, status=404)

        # 해당 게임에서 유저의 보유 주식 데이터를 가져오기
        user_holdings = UserStockHolding.objects.filter(game=game, user=user)
        if not user_holdings.exists():
            return Response({"message": f"No stock holdings found for the game (ID: {game_id})."}, status=200)

        # 보유 주식 데이터를 정리해서 반환
        holdings = []
        for holding in user_holdings:
            holdings.append({
                "stock_name": holding.stock.name,
                "quantity": holding.quantity
            })

        return Response({
            "message": f"Stock holdings for game '{game.name}' retrieved successfully.",
            "game_id": game.id,
            "game_name": game.name,
            "capital": game.capital,
            "profit_rate": game.profit_rate,
            "holdings": holdings
        }, status=200)
