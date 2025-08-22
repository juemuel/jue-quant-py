from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

@dataclass
class Position:
    """持仓信息"""
    symbol: str                    # 股票代码
    shares: float                  # 持仓数量
    avg_price: float              # 平均成本价
    current_price: float = 0      # 当前价格
    market_value: float = 0       # 市值
    unrealized_pnl: float = 0     # 浮动盈亏
    realized_pnl: float = 0       # 已实现盈亏
    weight: float = 0             # 持仓权重
    last_updated: datetime = field(default_factory=datetime.now)
    
    def update_price(self, new_price: float) -> None:
        """更新价格和相关指标"""
        self.current_price = new_price
        self.market_value = self.shares * new_price
        self.unrealized_pnl = (new_price - self.avg_price) * self.shares
        self.last_updated = datetime.now()
    
    def add_shares(self, shares: float, price: float) -> None:
        """增加持仓（更新平均成本）"""
        total_cost = self.shares * self.avg_price + shares * price
        self.shares += shares
        self.avg_price = total_cost / self.shares if self.shares > 0 else 0
        self.update_price(self.current_price or price)
    
    def reduce_shares(self, shares: float, price: float) -> float:
        """减少持仓，返回已实现盈亏"""
        if shares > self.shares:
            raise ValueError(f"减仓数量({shares})超过持仓数量({self.shares})")
        
        realized_pnl = (price - self.avg_price) * shares
        self.realized_pnl += realized_pnl
        self.shares -= shares
        
        if self.shares == 0:
            self.avg_price = 0
            self.market_value = 0
            self.unrealized_pnl = 0
        else:
            self.update_price(price)
        
        return realized_pnl

@dataclass
class Portfolio:
    """投资组合"""
    cash: float                           # 现金
    positions: Dict[str, Position] = field(default_factory=dict)  # 持仓
    total_value: float = 0               # 总价值
    total_cost: float = 0                # 总成本
    total_pnl: float = 0                 # 总盈亏
    last_updated: datetime = field(default_factory=datetime.now)
    
    def calculate_total_value(self) -> float:
        """计算总价值"""
        positions_value = sum(pos.market_value for pos in self.positions.values())
        self.total_value = self.cash + positions_value
        return self.total_value
    
    def calculate_weights(self) -> Dict[str, float]:
        """计算持仓权重"""
        if self.total_value <= 0:
            return {}
        
        weights = {}
        for symbol, position in self.positions.items():
            weights[symbol] = position.market_value / self.total_value
            position.weight = weights[symbol]
        
        return weights
    
    def get_cash_weight(self) -> float:
        """获取现金权重"""
        return self.cash / self.total_value if self.total_value > 0 else 1.0

@dataclass
class Trade:
    """交易记录"""
    symbol: str
    action: str  # 'buy' or 'sell'
    shares: float
    price: float
    amount: float
    trading_cost: float = 0
    timestamp: datetime = field(default_factory=datetime.now)
    reason: str = ""