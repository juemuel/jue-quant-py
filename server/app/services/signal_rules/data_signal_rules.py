from typing import Dict, Optional, List, Callable
from functools import partial
import pandas as pd
import numpy as np
from dataclasses import dataclass
from datetime import datetime
# 更新规则名称字典，区分固定和参数化版本
RULE_NAMES = {
    'adaptive_ma_crossover_rule': '自适应均线交叉规则(固定参数)',
    'multi_confirmation_rsi_rule': '多重确认RSI规则(固定参数)', 
    'trend_strength_filter_rule': '趋势强度过滤规则(固定参数)',
    'support_resistance_breakout_rule': '支撑阻力突破规则(固定参数)',
    'adaptive_ma_crossover_rule_with_params': '自适应均线交叉规则(参数化)',
    'multi_confirmation_rsi_rule_with_params': '多重确认RSI规则(参数化)',
}
@dataclass
class TechnicalSignalContext:
    """技术信号上下文"""
    symbol: str
    timestamp: datetime
    price: float
    volume: float
    indicators: Dict[str, float]  # 技术指标值
    market_context: Dict[str, float]  # 市场环境

# 动态均线交叉规则
def adaptive_ma_crossover_rule(context: TechnicalSignalContext) -> Optional[Dict]:
    """自适应均线交叉规则（固定参数版本）"""
    return adaptive_ma_crossover_rule_with_params(context, volatility_threshold=0.3, adaptive=False)
def adaptive_ma_crossover_rule_with_params(context: TechnicalSignalContext,
                                         short_period: int = 5,
                                         long_period: int = 20,
                                         volatility_threshold: float = 0.3,
                                         adaptive: bool = False) -> Optional[Dict]:
    """
    参数化的自适应均线交叉规则
    :param context: TechnicalSignalContext, 技术指标上下文
    :param short_period: 短均线周期
    :param long_period: 长均线周期
    :param volatility_threshold: 波动率阈值
    :param adaptive: 是否自适应（默认不开启）
    """
    indicators = context.indicators
    
    if adaptive:
        # 自适应逻辑
        available_mas = [key for key in indicators.keys() if key.startswith('MA')]
        if len(available_mas) < 2:
            return None
        
        volatility = context.market_context.get('volatility', 0.2)
        if volatility > volatility_threshold and 'MA3' in available_mas and 'MA10' in available_mas:
            short_ma_key, long_ma_key = 'MA3', 'MA10'
        elif f'MA{short_period}' in available_mas and f'MA{long_period}' in available_mas:
            short_ma_key, long_ma_key = f'MA{short_period}', f'MA{long_period}'
        else:
            # 使用可用的最短和最长周期
            periods = [int(ma[2:]) for ma in available_mas]
            periods.sort()
            short_ma_key, long_ma_key = f'MA{periods[0]}', f'MA{periods[-1]}'
    else:
        # 固定周期
        short_ma_key, long_ma_key = f'MA{short_period}', f'MA{long_period}'
    
    if short_ma_key not in indicators or long_ma_key not in indicators:
        return None
    
    short_ma = indicators[short_ma_key]
    long_ma = indicators[long_ma_key]
    short_ma_prev = indicators.get(f'{short_ma_key}_prev', short_ma)
    long_ma_prev = indicators.get(f'{long_ma_key}_prev', long_ma)
    
    # 确保所有均线值都不是None或NaN
    if (short_ma is None or pd.isna(short_ma) or 
        long_ma is None or pd.isna(long_ma) or 
        short_ma_prev is None or pd.isna(short_ma_prev) or 
        long_ma_prev is None or pd.isna(long_ma_prev) or
        long_ma == 0):  # 避免除零错误
        return None
    
    # 金叉买入
    if short_ma > long_ma and short_ma_prev <= long_ma_prev:
        strength = min((short_ma - long_ma) / long_ma, 1.0)
        return {
            'symbol': context.symbol,
            'signal': 1,
            'strength': strength,
            'reason': f'均线金叉{short_ma_key}>{long_ma_key}({short_ma:.2f}>{long_ma:.2f}),参数({short_period}/{long_period})',
            'timestamp': context.timestamp,
            'indicators_used': [short_ma_key, long_ma_key]
        }
    
    # 死叉卖出
    elif short_ma < long_ma and short_ma_prev >= long_ma_prev:
        strength = min((long_ma - short_ma) / long_ma, 1.0)
        return {
            'symbol': context.symbol,
            'signal': -1,
            'strength': strength,
            'reason': f'均线死叉{short_ma_key}<{long_ma_key}({short_ma:.2f}<{long_ma:.2f}),参数({short_period}/{long_period})',
            'timestamp': context.timestamp,
            'indicators_used': [short_ma_key, long_ma_key]
        }
    return None

# 多重确认RSI规则
def multi_confirmation_rsi_rule(context: TechnicalSignalContext) -> Optional[Dict]:
    """多重确认RSI规则（固定参数版本）"""
    return multi_confirmation_rsi_rule_with_params(context, oversold=30, overbought=70, 
                                                  volume_confirmation=False)
def multi_confirmation_rsi_rule_with_params(context: TechnicalSignalContext,
                                           period: int = 14,
                                           oversold: float = 30,
                                           overbought: float = 70,
                                           volume_confirmation: bool = False) -> Optional[Dict]:
    """
    参数化的多重确认RSI规则
    :param context: TechnicalSignalContext对象
    :param period: RSI周期
    :param oversold: 超卖阈值
    :param overbought: 超买阈值
    :param volume_confirmation: 是否需要成交量确认（默认不开启）
    """
    indicators = context.indicators
    
    if 'RSI' not in indicators:
        return None
    
    rsi = indicators['RSI']
    price = context.price
    volume = context.volume
    avg_volume = context.market_context.get('avg_volume', 0)
    
    # 确保所有数值都不是None或NaN
    if (rsi is None or pd.isna(rsi) or 
        price is None or pd.isna(price) or
        volume is None or pd.isna(volume)):
        return None
    
    # RSI超卖买入
    if rsi < oversold:
        # 成交量确认
        if volume_confirmation and volume <= avg_volume:
            return None
        
        strength = (oversold - rsi) / oversold
        return {
            'symbol': context.symbol,
            'signal': 1,
            'strength': min(strength, 1.0),
            'reason': f'RSI超卖买入({rsi:.1f}<{oversold}),参数({period}/{oversold}/{overbought})',
            'timestamp': context.timestamp,
            'indicators_used': ['RSI']
        }
    
    # RSI超买卖出
    elif rsi > overbought:
        # 成交量确认
        if volume_confirmation and volume <= avg_volume:
            return None
        
        strength = (rsi - overbought) / (100 - overbought)
        return {
            'symbol': context.symbol,
            'signal': -1,
            'strength': min(strength, 1.0),
            'reason': f'RSI超买卖出({rsi:.1f}>{overbought}),参数({period}/{oversold}/{overbought})',
            'timestamp': context.timestamp,
            'indicators_used': ['RSI']
        }
    
    return None

# 趋势强度过滤规则(TODO)
def trend_strength_filter_rule(context: TechnicalSignalContext) -> Optional[Dict]:
    """趋势强度过滤规则"""
    indicators = context.indicators
    
    # 需要MACD和ADX指标
    if 'MACD' not in indicators or 'ADX' not in indicators:
        return None
    
    macd = indicators['MACD']
    adx = indicators['ADX']
    
    # 确保指标值不是None或NaN
    if (macd is None or pd.isna(macd) or 
        adx is None or pd.isna(adx)):
        return None
    
    # 只在强趋势中生成信号
    if adx > 25:  # 强趋势
        if macd > 0:  # 上升趋势
            return {
                'symbol': context.symbol,
                'signal': 1,
                'strength': min(adx / 50, 1.0),
                'reason': f'强势上升趋势 (MACD:{macd:.3f}>0, ADX:{adx:.1f}>25)',
                'timestamp': context.timestamp,
                'indicators_used': ['MACD', 'ADX']
            }
        elif macd < 0:  # 下降趋势
            return {
                'symbol': context.symbol,
                'signal': -1,
                'strength': min(adx / 50, 1.0),
                'reason': f'强势下降趋势 (MACD:{macd:.3f}<0, ADX:{adx:.1f}>25)',
                'timestamp': context.timestamp,
                'indicators_used': ['MACD', 'ADX']
            }
    
    return None
# 支撑阻力突破规则(TODO)
def support_resistance_breakout_rule(context: TechnicalSignalContext) -> Optional[Dict]:
    """支撑阻力突破规则"""
    indicators = context.indicators
    price = context.price
    volume = context.volume
    
    # 需要支撑阻力位数据
    support_level = indicators.get('support_level')
    resistance_level = indicators.get('resistance_level')
    avg_volume = context.market_context.get('avg_volume', 0)
    
    # 确保基础数值不是None或NaN
    if (price is None or pd.isna(price) or 
        volume is None or pd.isna(volume)):
        return None
    
    if avg_volume is None or pd.isna(avg_volume):
        avg_volume = 0
    
    # 确保支撑阻力位数据有效
    if (support_level and resistance_level and 
        not pd.isna(support_level) and not pd.isna(resistance_level)):
        
        # 突破阻力位（需要大成交量确认）
        if price > resistance_level * 1.01 and volume > avg_volume * 1.5:
            return {
                'symbol': context.symbol,
                'signal': 1,
                'strength': 0.8,
                'reason': f'突破阻力位 (价格:{price:.2f} > 阻力:{resistance_level:.2f})',
                'timestamp': context.timestamp,
                'indicators_used': ['resistance_level', 'volume']
            }
        
        # 跌破支撑位（需要大成交量确认）
        elif price < support_level * 0.99 and volume > avg_volume * 1.5:
            return {
                'symbol': context.symbol,
                'signal': -1,
                'strength': 0.8,
                'reason': f'跌破支撑位 (价格:{price:.2f} < 支撑:{support_level:.2f})',
                'timestamp': context.timestamp,
                'indicators_used': ['support_level', 'volume']
            }
    
    return None

# 创建规则
def create_parameterized_ma_rule(short_period: int = 5, long_period: int = 20, 
                                volatility_threshold: float = 0.3, adaptive: bool = False) -> callable:
    """创建参数化的MA交叉规则"""
    rule = partial(adaptive_ma_crossover_rule_with_params, 
                  short_period=short_period, long_period=long_period,
                  volatility_threshold=volatility_threshold, adaptive=adaptive)
    rule.chinese_name = f'自适应MA交叉规则(参数化:{short_period}/{long_period})'
    rule.__name__ = f'ma_crossover_rule_parameterized_{short_period}_{long_period}'
    return rule

def create_parameterized_rsi_rule(period: int = 14, oversold: int = 30, 
                                 overbought: int = 70, volume_confirmation: bool = False) -> callable:
    """创建参数化的RSI规则"""
    rule = partial(multi_confirmation_rsi_rule_with_params,
                  period=period, oversold=oversold, overbought=overbought,
                  volume_confirmation=volume_confirmation)
    rule.chinese_name = f'多重确认RSI规则(参数化:{period}/{oversold}/{overbought})'
    rule.__name__ = f'rsi_rule_parameterized_{period}_{oversold}_{overbought}'
    return rule

# 中文名称
adaptive_ma_crossover_rule.chinese_name = '自适应均线交叉规则(固定参数)'
multi_confirmation_rsi_rule.chinese_name = '多重确认RSI规则(固定参数)'
trend_strength_filter_rule.chinese_name = '趋势强度过滤规则(固定参数)'
support_resistance_breakout_rule.chinese_name = '支撑阻力突破规则(固定参数)'
adaptive_ma_crossover_rule_with_params.chinese_name = '自适应均线交叉规则(参数化)'
multi_confirmation_rsi_rule_with_params.chinese_name = '多重确认RSI规则(参数化)'
