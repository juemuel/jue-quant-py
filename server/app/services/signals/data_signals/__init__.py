"""数据驱动信号模块统一入口"""

from .core import TechnicalSignalContext, SignalType, SignalStrength
from .basic_rules import BasicSignalRules, BASIC_RULES_METADATA
from .parameterized_rules import ParameterizedRuleFactory, PARAMETERIZED_RULE_CREATORS
from .filter_rules import FilterRules, ParameterizedFilterFactory, DEFAULT_FILTERS, STRICT_FILTERS
from .registry import SignalRuleRegistry, rule_registry

# 向后兼容的导出
__all__ = [
    'TechnicalSignalContext',
    'SignalType',
    'SignalStrength',
    'BasicSignalRules',
    'ParameterizedRuleFactory',
    'FilterRules',
    'ParameterizedFilterFactory',
    'SignalRuleRegistry',
    'rule_registry',
    'DEFAULT_FILTERS',
    'STRICT_FILTERS'
]

# 为了保持向后兼容，导出原有的函数名
default_ma_crossover_rule = BasicSignalRules.ma_crossover_rule
default_rsi_rule = BasicSignalRules.rsi_rule
trend_strength_filter_rule = BasicSignalRules.trend_strength_rule
support_resistance_breakout_rule = BasicSignalRules.support_resistance_breakout_rule

# 导出过滤规则
volume_confirmation_filter = FilterRules.volume_confirmation_filter
volatility_filter = FilterRules.volatility_filter
trend_strength_filter = FilterRules.trend_strength_filter
signal_strength_filter = FilterRules.signal_strength_filter
price_momentum_filter = FilterRules.price_momentum_filter

# 导出参数化过滤器创建函数
create_parameterized_volatility_filter = ParameterizedFilterFactory.create_volatility_filter
create_parameterized_volume_filter = ParameterizedFilterFactory.create_volume_filter
create_parameterized_signal_strength_filter = ParameterizedFilterFactory.create_signal_strength_filter