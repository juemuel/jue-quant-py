from typing import Dict, List, Optional, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
from core.logger import logger
from .models import Portfolio, Position, Trade

class PortfolioService:
    """投资组合管理服务"""
    
    def __init__(self, initial_capital: float = 1000000):
        self.portfolio = Portfolio(cash=initial_capital)
        self.trade_history: List[Trade] = []
        self.portfolio_history: List[Dict] = []
        
    def buy_stock(self, symbol: str, shares: float, price: float, 
                  trading_cost: float = 0, reason: str = "") -> bool:
        """买入股票"""
        try:
            total_cost = shares * price + trading_cost
            
            # 检查现金是否足够
            if total_cost > self.portfolio.cash:
                logger.warning(f"现金不足: 需要{total_cost:.2f}, 可用{self.portfolio.cash:.2f}")
                return False
            
            # 扣除现金
            self.portfolio.cash -= total_cost
            
            # 更新持仓
            if symbol in self.portfolio.positions:
                self.portfolio.positions[symbol].add_shares(shares, price)
            else:
                self.portfolio.positions[symbol] = Position(
                    symbol=symbol,
                    shares=shares,
                    avg_price=price,
                    current_price=price
                )
                self.portfolio.positions[symbol].update_price(price)
            
            # 记录交易
            trade = Trade(
                symbol=symbol,
                action='buy',
                shares=shares,
                price=price,
                amount=total_cost,
                trading_cost=trading_cost,
                reason=reason
            )
            self.trade_history.append(trade)
            
            logger.info(f"买入成功: {symbol} {shares}股 @{price:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"买入失败: {e}")
            return False
    
    def sell_stock(self, symbol: str, shares: float, price: float,
                   trading_cost: float = 0, reason: str = "") -> bool:
        """卖出股票"""
        try:
            # 检查持仓是否足够
            if symbol not in self.portfolio.positions:
                logger.warning(f"无持仓: {symbol}")
                return False
            
            position = self.portfolio.positions[symbol]
            if shares > position.shares:
                logger.warning(f"持仓不足: 需要{shares}, 持有{position.shares}")
                return False
            
            # 计算收入
            proceeds = shares * price - trading_cost
            
            # 增加现金
            self.portfolio.cash += proceeds
            
            # 更新持仓
            realized_pnl = position.reduce_shares(shares, price)
            
            # 如果持仓为0，删除该持仓
            if position.shares == 0:
                del self.portfolio.positions[symbol]
            
            # 记录交易
            trade = Trade(
                symbol=symbol,
                action='sell',
                shares=shares,
                price=price,
                amount=proceeds,
                trading_cost=trading_cost,
                reason=reason
            )
            self.trade_history.append(trade)
            
            logger.info(f"卖出成功: {symbol} {shares}股 @{price:.2f}, 已实现盈亏: {realized_pnl:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"卖出失败: {e}")
            return False
    
    def update_prices(self, price_data: Dict[str, float]) -> None:
        """批量更新股票价格"""
        for symbol, price in price_data.items():
            if symbol in self.portfolio.positions:
                self.portfolio.positions[symbol].update_price(price)
        
        # 更新组合总价值和权重
        self.portfolio.calculate_total_value()
        self.portfolio.calculate_weights()
        self.portfolio.last_updated = datetime.now()
    
    def get_portfolio_summary(self) -> Dict:
        """获取投资组合摘要"""
        self.portfolio.calculate_total_value()
        weights = self.portfolio.calculate_weights()
        
        # 计算总盈亏
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.portfolio.positions.values())
        total_realized_pnl = sum(pos.realized_pnl for pos in self.portfolio.positions.values())
        
        return {
            'total_value': self.portfolio.total_value,
            'cash': self.portfolio.cash,
            'cash_weight': self.portfolio.get_cash_weight(),
            'positions_count': len(self.portfolio.positions),
            'total_unrealized_pnl': total_unrealized_pnl,
            'total_realized_pnl': total_realized_pnl,
            'total_pnl': total_unrealized_pnl + total_realized_pnl,
            'positions': {
                symbol: {
                    'shares': pos.shares,
                    'avg_price': pos.avg_price,
                    'current_price': pos.current_price,
                    'market_value': pos.market_value,
                    'unrealized_pnl': pos.unrealized_pnl,
                    'weight': pos.weight
                } for symbol, pos in self.portfolio.positions.items()
            },
            'weights': weights,
            'last_updated': self.portfolio.last_updated
        }
    
    def get_trade_history(self) -> List[Dict]:
        """获取交易历史"""
        return [{
            'symbol': trade.symbol,
            'action': trade.action,
            'shares': trade.shares,
            'price': trade.price,
            'amount': trade.amount,
            'trading_cost': trade.trading_cost,
            'timestamp': trade.timestamp,
            'reason': trade.reason
        } for trade in self.trade_history]