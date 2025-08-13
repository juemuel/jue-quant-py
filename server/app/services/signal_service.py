from core.logger import logger
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime

# 导入数据驱动相关
from .signal_rules.data_signal_rules import (
    TechnicalSignalContext,
    adaptive_ma_crossover_rule,
    multi_confirmation_rsi_rule,
    trend_strength_filter_rule,
    support_resistance_breakout_rule
)

# 导入事件驱动相关
from .event_service import MarketEvent, EventType, EventSeverity
from .signal_rules.event_signal_rules import (
    news_sentiment_rule,
    earnings_anticipation_rule,
    keyword_trigger_rule
)

# ============ 数据驱动信号生成器 ============
class DataSignalGenerator:
    """数据驱动信号生成器"""
    
    def __init__(self):
        self.signal_rules = []
        self.filter_rules = []
        self.weight_rules = []
    
    def add_signal_rule(self, rule_func):
        """添加信号生成规则"""
        self.signal_rules.append(rule_func)
    
    def add_filter_rule(self, filter_func):
        """添加信号过滤规则"""
        self.filter_rules.append(filter_func)
    
    def add_weight_rule(self, weight_func):
        """添加信号权重规则"""
        self.weight_rules.append(weight_func)
    
    def generate_signals(self, df: pd.DataFrame, indicators: Dict[str, pd.Series]) -> List[Dict]:
        """生成技术信号"""
        signals = []
        
        for i in range(1, len(df)):  # 从第二行开始，确保有前一期数据
            row = df.iloc[i]
            prev_row = df.iloc[i-1]
            
            # 构建技术信号上下文
            context = TechnicalSignalContext(
                symbol=row.get('symbol', 'UNKNOWN'),
                timestamp=row.get('date', pd.Timestamp.now()),
                price=row.get('close', row.get('收盘', 0)),
                volume=row.get('volume', row.get('成交量', 0)),
                indicators=self._extract_indicators(indicators, i, prev_row),
                market_context=self._calculate_market_context(df, i)
            )
            
            # 应用所有信号规则
            for rule in self.signal_rules:
                signal = rule(context)
                if signal:
                    # 应用过滤规则
                    if self._apply_filters(signal, context):
                        # 应用权重规则
                        signal = self._apply_weights(signal, context)
                        signals.append(signal)
        
        return signals
    
    def _extract_indicators(self, indicators: Dict, index: int, prev_row) -> Dict[str, float]:
        """提取当前时点的指标值"""
        result = {}
        for name, series in indicators.items():
            if index < len(series):
                result[name] = series.iloc[index]
                if index > 0:
                    result[f'{name}_prev'] = series.iloc[index-1]
        return result
    
    def _calculate_market_context(self, df: pd.DataFrame, index: int) -> Dict[str, float]:
        """计算市场环境上下文"""
        # 计算最近20期的波动率
        start_idx = max(0, index - 20)
        recent_data = df.iloc[start_idx:index+1]
        
        if len(recent_data) > 1:
            returns = recent_data['close'].pct_change().dropna()
            volatility = returns.std() if len(returns) > 0 else 0.2
        else:
            volatility = 0.2
        
        # 计算平均成交量
        avg_volume = recent_data.get('volume', recent_data.get('成交量', pd.Series([0]))).mean()
        
        return {
            'volatility': volatility,
            'avg_volume': avg_volume
        }
    
    def _apply_filters(self, signal: Dict, context: TechnicalSignalContext) -> bool:
        """应用过滤规则"""
        for filter_rule in self.filter_rules:
            if not filter_rule(signal, context):
                return False
        return True
    
    def _apply_weights(self, signal: Dict, context: TechnicalSignalContext) -> Dict:
        """应用权重规则"""
        for weight_rule in self.weight_rules:
            signal = weight_rule(signal, context)
        return signal

# ============ 事件驱动信号生成器 ============
class EventSignalGenerator:
    def __init__(self):
        self.signal_rules = []
    
    def add_rule(self, rule_func):
        """添加信号生成规则"""
        self.signal_rules.append(rule_func)
    
    def generate_signals(self, events: List[MarketEvent]) -> List[Dict]:
        """根据事件生成交易信号"""
        signals = []
        
        for event in events:
            for rule_func in self.signal_rules:
                signal = rule_func(event)
                if signal:
                    signals.append(signal)
        
        return signals

# ============ 统一信号管理器 ============
class UnifiedSignalManager:
    """统一信号管理器 - 整合数据驱动和事件驱动信号"""
    
    def __init__(self):
        self.data_generator = DataSignalGenerator()
        self.event_generator = EventSignalGenerator()
    
    def generate_combined_signals(self, 
                                price_data: pd.DataFrame, 
                                indicators: Dict[str, pd.Series],
                                events: List[MarketEvent]) -> Dict[str, List[Dict]]:
        """生成综合信号"""
        return {
            'data_signals': self.data_generator.generate_signals(price_data, indicators),
            'event_signals': self.event_generator.generate_signals(events)
        }
    
    def create_default_data_generator(self):
        """创建默认数据信号生成器"""
        self.data_generator.add_signal_rule(adaptive_ma_crossover_rule)
        self.data_generator.add_signal_rule(multi_confirmation_rsi_rule)
        self.data_generator.add_filter_rule(trend_strength_filter_rule)
        return self.data_generator
    
    def create_default_event_generator(self):
        """创建默认事件信号生成器"""
        self.event_generator.add_rule(news_sentiment_rule)
        self.event_generator.add_rule(keyword_trigger_rule)
        return self.event_generator