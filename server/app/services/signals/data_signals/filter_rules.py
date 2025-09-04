from typing import Dict, Callable
from .core import TechnicalSignalContext, FilterRuleFunc, SignalType

class FilterRules:
    """过滤规则集合"""
    
    @staticmethod
    def volume_confirmation_filter(signal: Dict, context: TechnicalSignalContext) -> bool:
        """成交量确认过滤"""
        volume = context.volume
        avg_volume = context.market_context.get('avg_volume_20', 0)
        
        if avg_volume == 0:
            return True  # 无法计算时默认通过
        
        # 成交量需要超过20日均量的1.2倍
        volume_ratio = volume / avg_volume
        return volume_ratio > 1.2
    
    @staticmethod
    def volatility_filter(signal: Dict, context: TechnicalSignalContext) -> bool:
        """波动率过滤"""
        volatility = context.market_context.get('volatility', 0)
        
        # 过滤极端波动环境
        if volatility < 0.01 or volatility > 0.5:
            return False
        
        return True
    
    @staticmethod
    def trend_strength_filter(signal: Dict, context: TechnicalSignalContext) -> bool:
        """趋势强度过滤"""
        adx = context.indicators.get('ADX', 0)
        
        # ADX低于25时认为趋势不明显，过滤信号
        return adx >= 25
    
    @staticmethod
    def signal_strength_filter(signal: Dict, context: TechnicalSignalContext) -> bool:
        """信号强度过滤"""
        strength = signal.get('strength', 0)
        
        # 过滤强度低于0.5的弱信号
        return strength >= 0.5
    
    @staticmethod
    def price_momentum_filter(signal: Dict, context: TechnicalSignalContext) -> bool:
        """价格动量过滤"""
        price_change = context.market_context.get('price_momentum', 0)
        signal_type = signal.get('signal', 0)
        
        # 买入信号需要正动量支持
        if signal_type == SignalType.BUY:
            return price_change > 0.02
        
        # 卖出信号需要负动量支持
        elif signal_type == SignalType.SELL:
            return price_change < -0.02
        
        return True

class ParameterizedFilterFactory:
    """参数化过滤规则工厂"""
    
    @staticmethod
    def create_volatility_filter(min_volatility: float = 0.01, 
                               max_volatility: float = 0.5) -> FilterRuleFunc:
        """创建参数化波动率过滤器"""
        def filter_func(signal: Dict, context: TechnicalSignalContext) -> bool:
            volatility = context.market_context.get('volatility', 0)
            return min_volatility <= volatility <= max_volatility
        return filter_func
    
    @staticmethod
    def create_volume_filter(volume_multiplier: float = 1.2, 
                           lookback_days: int = 20) -> FilterRuleFunc:
        """创建参数化成交量过滤器"""
        def filter_func(signal: Dict, context: TechnicalSignalContext) -> bool:
            volume = context.volume
            avg_volume_key = f'avg_volume_{lookback_days}'
            avg_volume = context.market_context.get(avg_volume_key, 0)
            
            if avg_volume == 0:
                return True
            
            volume_ratio = volume / avg_volume
            return volume_ratio > volume_multiplier
        return filter_func
    
    @staticmethod
    def create_signal_strength_filter(min_strength: float = 0.5) -> FilterRuleFunc:
        """创建参数化信号强度过滤器"""
        def filter_func(signal: Dict, context: TechnicalSignalContext) -> bool:
            strength = signal.get('strength', 0)
            return strength >= min_strength
        return filter_func

    @staticmethod
    def create_trend_strength_filter(min_adx: float = 25) -> FilterRuleFunc:
        """创建参数化趋势强度过滤器"""
        def filter_func(signal: Dict, context: TechnicalSignalContext) -> bool:
            adx = context.indicators.get('ADX', 0)
            return adx >= min_adx
        return filter_func
# 过滤规则元数据
FILTER_RULES_METADATA = {
    'volume_confirmation': {
        'func': FilterRules.volume_confirmation_filter,
        'chinese_name': '成交量确认过滤',
        'category': 'volume_filter',
        'description': '要求信号伴随成交量放大确认'
    },
    'volatility': {
        'func': FilterRules.volatility_filter,
        'chinese_name': '波动率过滤',
        'category': 'volatility_filter',
        'description': '过滤极端波动环境下的信号'
    },
    'trend_strength': {
        'func': FilterRules.trend_strength_filter,
        'chinese_name': '趋势强度过滤',
        'category': 'trend_filter',
        'description': '要求明显趋势环境下的信号'
    },
    'signal_strength': {
        'func': FilterRules.signal_strength_filter,
        'chinese_name': '信号强度过滤',
        'category': 'strength_filter',
        'description': '过滤强度不足的弱信号'
    },
    'price_momentum': {
        'func': FilterRules.price_momentum_filter,
        'chinese_name': '价格动量过滤',
        'category': 'momentum_filter',
        'description': '要求价格动量与信号方向一致'
    }
}

# 预定义过滤规则组合
DEFAULT_FILTERS = [
    FilterRules.trend_strength_filter,
    FilterRules.volume_confirmation_filter,
    FilterRules.signal_strength_filter
]

STRICT_FILTERS = [
    FilterRules.trend_strength_filter,
    FilterRules.volume_confirmation_filter,
    FilterRules.signal_strength_filter,
    FilterRules.price_momentum_filter,
    FilterRules.volatility_filter
]