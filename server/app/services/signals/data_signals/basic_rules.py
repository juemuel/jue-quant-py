from typing import Dict, Optional
from .core import TechnicalSignalContext, SignalType, SignalStrength, RuleType

class BasicSignalRules:
    """基础信号规则集合"""
    
    @staticmethod
    def ma_crossover_rule(context: TechnicalSignalContext) -> Optional[Dict]:
        """均线交叉规则"""
        ma_5 = context.indicators.get('ma_5', 0)
        ma_20 = context.indicators.get('ma_20', 0)
        
        if ma_5 == 0 or ma_20 == 0:
            return None
        
        # 金叉：短期均线上穿长期均线
        if ma_5 > ma_20:
            crossover_strength = min((ma_5 - ma_20) / ma_20, 0.1) * 10
            return {
                'symbol': context.symbol,
                'signal': SignalType.BUY,
                'strength': min(crossover_strength, SignalStrength.STRONG),
                'reason': f'MA金叉: MA5({ma_5:.2f}) > MA20({ma_20:.2f})',
                'timestamp': context.timestamp,
                'rule_name': '基础均线交叉规则',
                'category': RuleType.TREND_FOLLOWING
            }
        
        # 死叉：短期均线下穿长期均线
        elif ma_5 < ma_20:
            crossover_strength = min((ma_20 - ma_5) / ma_20, 0.1) * 10
            return {
                'symbol': context.symbol,
                'signal': SignalType.SELL,
                'strength': min(crossover_strength, SignalStrength.STRONG),
                'reason': f'MA死叉: MA5({ma_5:.2f}) < MA20({ma_20:.2f})',
                'timestamp': context.timestamp,
                'rule_name': '基础均线交叉规则',
                'category': RuleType.TREND_FOLLOWING

            }
        # 均线平行，观望
        else:
            return {
                'symbol': context.symbol,
                'signal': SignalType.HOLD,
                'strength': 0.0,
                'reason': f'MA平行: MA5({ma_5:.2f}) ≈ MA20({ma_20:.2f})',
                'timestamp': context.timestamp,
                'rule_name': '基础均线交叉规则',
                'category': RuleType.TREND_FOLLOWING
            }
        
        return None
    
    @staticmethod
    def rsi_rule(context: TechnicalSignalContext) -> Optional[Dict]:
        """RSI规则"""
        rsi = context.indicators.get('rsi_14', 50)
        
        # RSI超卖区域
        if rsi < 30:
            return {
                'symbol': context.symbol,
                'signal': SignalType.BUY,
                'strength': min((30 - rsi) / 30, 1.0),
                'reason': f'RSI超卖: {rsi:.2f}',
                'timestamp': context.timestamp,
                'rule_name': '基础RSI规则',
                'category': RuleType.MOMENTUM

            }
        
        # RSI超买区域
        elif rsi > 70:
            return {
                'symbol': context.symbol,
                'signal': SignalType.SELL,
                'strength': min((rsi - 70) / 30, 1.0),
                'reason': f'RSI超买: {rsi:.2f}',
                'timestamp': context.timestamp,
                'rule_name': '基础RSI规则',
                'category': RuleType.MOMENTUM

            }
        # RSI在正常区间，观望
        else:
            return {
                'symbol': context.symbol,
                'signal': SignalType.HOLD,
                'strength': 0.0,
                'reason': f'RSI正常: {rsi:.2f} (30-70区间)',
                'timestamp': context.timestamp,
                'rule_name': '基础RSI规则',
                'category': RuleType.MOMENTUM

            }
    
    @staticmethod
    def trend_strength_rule(context: TechnicalSignalContext) -> Optional[Dict]:
        """趋势强度规则"""
        ma_5 = context.indicators.get('ma_5', 0)
        ma_20 = context.indicators.get('ma_20', 0)
        ma_50 = context.indicators.get('ma_50', 0)
        
        if not all([ma_5, ma_20, ma_50]):
            return None
        
        # 多头排列：MA5 > MA20 > MA50
        if ma_5 > ma_20 > ma_50:
            trend_strength = min((ma_5 - ma_50) / ma_50, 0.2) * 5
            return {
                'symbol': context.symbol,
                'signal': SignalType.BUY,
                'strength': min(trend_strength, SignalStrength.STRONG),
                'reason': f'多头排列: MA5({ma_5:.2f}) > MA20({ma_20:.2f}) > MA50({ma_50:.2f})',
                'timestamp': context.timestamp,
                'rule_name': '基础趋势强度规则',
                'category': RuleType.TREND_FOLLOWING

            }
        
        # 空头排列：MA5 < MA20 < MA50
        elif ma_5 < ma_20 < ma_50:
            trend_strength = min((ma_50 - ma_5) / ma_50, 0.2) * 5
            return {
                'symbol': context.symbol,
                'signal': SignalType.SELL,
                'strength': min(trend_strength, SignalStrength.STRONG),
                'reason': f'空头排列: MA5({ma_5:.2f}) < MA20({ma_20:.2f}) < MA50({ma_50:.2f})',
                'timestamp': context.timestamp,
                'rule_name': '基础趋势强度规则',
                'category': RuleType.TREND_FOLLOWING

            }
        # 趋势平行，观望
        else:
            return {
                'symbol': context.symbol,
                'signal': SignalType.HOLD,
                'strength': 0.0,
                'reason': f'趋势平行: MA5({ma_5:.2f}) ≈ MA20({ma_20:.2f}) ≈ MA50({ma_50:.2f})',
                'timestamp': context.timestamp,
                'rule_name': '基础趋势强度规则',
                'category': RuleType.TREND_FOLLOWING

            }

        
        return None
    
    @staticmethod
    def support_resistance_breakout_rule(context: TechnicalSignalContext) -> Optional[Dict]:
        """支撑阻力突破规则"""
        price = context.price
        high_20 = context.market_context.get('high_20', 0)
        low_20 = context.market_context.get('low_20', 0)
        
        if not all([high_20, low_20]):
            return None
        
        # 突破阻力位
        if price > high_20:
            breakout_strength = min((price - high_20) / high_20, 0.1) * 10
            return {
                'symbol': context.symbol,
                'signal': SignalType.BUY,
                'strength': min(breakout_strength, SignalStrength.STRONG),
                'reason': f'突破阻力位: 价格({price:.2f}) > 20日高点({high_20:.2f})',
                'timestamp': context.timestamp,
                'rule_name': '基础支撑阻力突破规则',
                'category': RuleType.SUPPORT_RESISTANCE

            }
        
        # 跌破支撑位
        elif price < low_20:
            breakdown_strength = min((low_20 - price) / low_20, 0.1) * 10
            return {
                'symbol': context.symbol,
                'signal': SignalType.SELL,
                'strength': min(breakdown_strength, SignalStrength.STRONG),
                'reason': f'跌破支撑位: 价格({price:.2f}) < 20日低点({low_20:.2f})',
                'timestamp': context.timestamp,
                'rule_name': '基础支撑阻力突破规则',
                'category': RuleType.SUPPORT_RESISTANCE

            }
        # 支撑阻力突破，观望
        else:
            return {
                'symbol': context.symbol,
                'signal': SignalType.HOLD,
                'strength': 0.0,
                'reason': f'支撑阻力突破: 价格({price:.2f}) ≈ 20日高点({high_20:.2f}) ≈ 20日低点({low_20:.2f})',
                'timestamp': context.timestamp,
                'rule_name': '基础支撑阻力突破规则',
                'category': RuleType.SUPPORT_RESISTANCE

            }

        return None

# 规则元数据
BASIC_RULES_METADATA = {
    'ma_crossover': {
        'func': BasicSignalRules.ma_crossover_rule,
        'chinese_name': '基础均线交叉规则',
        'required_indicators': ['ma_5', 'ma_20'],
        'optional_indicators': ['volume'],
        'category': RuleType.TREND_FOLLOWING,  # 使用常量
        'description': '基于MA5和MA20均线交叉的趋势跟踪信号。金叉时产生买入信号，死叉时产生卖出信号。信号强度基于均线间距离计算。'
    },
    'rsi': {
        'func': BasicSignalRules.rsi_rule,
        'chinese_name': '基础RSI规则',
        'required_indicators': ['rsi_14'],
        'optional_indicators': ['volume'],
        'category': RuleType.MOMENTUM,  # 使用常量
        'description': '基于14周期RSI指标的超买超卖信号。RSI<30时产生买入信号(超卖反弹)，RSI>70时产生卖出信号(超买回调)。'
    },
    'trend_strength': {
        'func': BasicSignalRules.trend_strength_rule,
        'chinese_name': '趋势强度规则',
        'required_indicators': ['ma_5', 'ma_20', 'ma_50'],
        'optional_indicators': ['volume'],
        'category': RuleType.TREND_FOLLOWING,  # 使用常量
        'description': '基于MA5、MA20、MA50多条均线排列的趋势强度信号。多头排列时产生强买入信号，空头排列时产生强卖出信号。'
    },
    'support_resistance_breakout': {
        'func': BasicSignalRules.support_resistance_breakout_rule,
        'chinese_name': '支撑阻力突破规则',
        'required_indicators': ['high', 'low', 'close'],
        'optional_indicators': ['volume'],
        'category': RuleType.BREAKOUT,  # 使用常量
        'description': '基于历史高低点形成的支撑阻力位突破信号。向上突破阻力位时产生买入信号，向下跌破支撑位时产生卖出信号。'
    }
}