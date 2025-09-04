from typing import Dict, Optional, List, Callable
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TechnicalSignalContext:
    """技术信号上下文数据类"""
    symbol: str
    timestamp: datetime
    price: float
    volume: float
    indicators: Dict[str, float]  # 技术指标值
    market_context: Dict[str, float]  # 市场环境

# 规则类型定义
SignalRuleFunc = Callable[[TechnicalSignalContext], Optional[Dict]]
FilterRuleFunc = Callable[[Dict, TechnicalSignalContext], bool]
ParameterizedRuleCreator = Callable[..., SignalRuleFunc]

# 信号类型枚举
class SignalType:
    BUY = 1
    SELL = -1
    HOLD = 0

# 信号强度等级
class SignalStrength:
    WEAK = 0.3
    MEDIUM = 0.6
    STRONG = 0.9

# 规则类型常量
class RuleType:
    # 数据信号规则类型
    TREND_FOLLOWING = "trend_following"      # 趋势跟踪
    MOMENTUM = "momentum"                    # 动量指标
    BREAKOUT = "breakout"                    # 突破策略
    MEAN_REVERSION = "mean_reversion"        # 均值回归
    VOLUME_ANALYSIS = "volume_analysis"      # 成交量分析
    VOLATILITY = "volatility"               # 波动率分析
    
    # 事件信号规则类型
    NEWS_SENTIMENT = "news_sentiment"        # 新闻情感
    EARNINGS = "earnings"                    # 财报事件
    KEYWORD_TRIGGER = "keyword_trigger"      # 关键词触发
    MARKET_ANOMALY = "market_anomaly"        # 市场异动
    MACRO_EVENT = "macro_event"              # 宏观事件
    CORPORATE_ACTION = "corporate_action"    # 公司行为