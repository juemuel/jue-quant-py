from typing import Dict, Optional, List
import pandas as pd
import numpy as np
from dataclasses import dataclass
from datetime import datetime
RULE_NAMES = {
    'adaptive_ma_crossover_rule': '自适应均线交叉规则',
    'multi_confirmation_rsi_rule': '多重确认RSI规则', 
    'trend_strength_filter_rule': '趋势强度过滤规则',
    'support_resistance_breakout_rule': '支撑阻力突破规则'
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
    """自适应均线交叉规则"""
    indicators = context.indicators
     # 根据可用的指标选择最佳组合，而不是固定选择
    available_mas = [key for key in indicators.keys() if key.startswith('MA')]
    if len(available_mas) < 2:
        return None
     # 根据市场波动率和可用指标选择最佳组合
    volatility = context.market_context.get('volatility', 0.2)
    if volatility > 0.3 and 'MA3' in available_mas and 'MA10' in available_mas:
        short_ma_key, long_ma_key = 'MA3', 'MA10'
    elif 'MA5' in available_mas and 'MA20' in available_mas:
        short_ma_key, long_ma_key = 'MA5', 'MA20'
    else:
        # 使用可用的最短和最长周期
        periods = [int(ma[2:]) for ma in available_mas]
        periods.sort()
        short_ma_key, long_ma_key = f'MA{periods[0]}', f'MA{periods[-1]}'

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
        # 信号强度基于价格距离均线的程度
        strength = min((short_ma - long_ma) / long_ma, 1.0)
        return {
            'symbol': context.symbol,
            'signal': 1, # 1表示买入
            'strength': strength,
            'reason': f'自适应均线金叉{short_ma_key}>{long_ma_key}({short_ma:.2f}>{long_ma:.2f}),年化波动率{volatility:.3f}',
            'timestamp': context.timestamp,
            'indicators_used': [short_ma_key, long_ma_key]
        }
    
    # 死叉卖出
    elif short_ma < long_ma and short_ma_prev >= long_ma_prev:
        strength = min((long_ma - short_ma) / long_ma, 1.0)
        return {
            'symbol': context.symbol,
            'signal': -1, # -1表示卖出
            'strength': strength,
            'reason': f'自适应均线死叉{short_ma_key}<{long_ma_key} ({short_ma:.2f}<{long_ma:.2f}),年化波动率{volatility:.3f}',
            'timestamp': context.timestamp,
            'indicators_used': [short_ma_key, long_ma_key]
        }
    return None
# 多重确认RSI规则
def multi_confirmation_rsi_rule(context: TechnicalSignalContext) -> Optional[Dict]:
    """多重确认RSI规则"""
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
    
    if avg_volume is None or pd.isna(avg_volume):
        avg_volume = 0
    
    # 动态调整RSI阈值
    volatility = context.market_context.get('volatility', 0.2)
    if volatility > 0.3:  # 高波动市场，更严格的阈值
        oversold, overbought = 25, 75
    else:  # 低波动市场，标准阈值
        oversold, overbought = 30, 70

    volume_ratio = volume / avg_volume if avg_volume > 0 else 0
    # 超卖买入（需要成交量确认）
    if rsi < oversold and volume > avg_volume * 1.2:
        strength = (oversold - rsi) / oversold
        return {
            'symbol': context.symbol,
            'signal': 1,
            'strength': strength,
            'reason': f'RSI超卖+成交量确认 (RSI:{rsi:.1f}<{oversold}, 成交量:{volume_ratio:.1f}x, 波动率:{volatility:.3f})',
            'timestamp': context.timestamp,
            'indicators_used': ['RSI', 'Volume']
        }
    
    # 超买卖出（需要成交量确认）
    elif rsi > overbought and volume > avg_volume * 1.2:
        strength = (rsi - overbought) / (100 - overbought)
        return {
            'symbol': context.symbol,
            'signal': -1,
            'strength': strength,
            'reason': f'RSI超买+成交量确认 (RSI:{rsi:.1f}>{overbought}, 成交量:{volume_ratio:.1f}x, 波动率:{volatility:.3f})',
            'timestamp': context.timestamp,
            'indicators_used': ['RSI', 'Volume']
        }
    
    return None
# 趋势强度过滤规则
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
# 支撑阻力突破规则
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

adaptive_ma_crossover_rule.chinese_name = '自适应均线交叉规则'
multi_confirmation_rsi_rule.chinese_name = '多重确认RSI规则'
trend_strength_filter_rule.chinese_name = '趋势强度过滤规则'
support_resistance_breakout_rule.chinese_name = '支撑阻力突破规则'