from typing import Dict, Optional, List
import pandas as pd
import numpy as np
from dataclasses import dataclass
from datetime import datetime

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
    
    # 根据市场波动率调整均线周期
    volatility = context.market_context.get('volatility', 0.2)
    if volatility > 0.3:  # 高波动市场
        short_ma_key, long_ma_key = 'MA3', 'MA10'
    else:  # 低波动市场
        short_ma_key, long_ma_key = 'MA5', 'MA20'
    
    if short_ma_key not in indicators or long_ma_key not in indicators:
        return None
    
    short_ma = indicators[short_ma_key]
    long_ma = indicators[long_ma_key]
    short_ma_prev = indicators.get(f'{short_ma_key}_prev', short_ma)
    long_ma_prev = indicators.get(f'{long_ma_key}_prev', long_ma)
    
    # 金叉买入
    if short_ma > long_ma and short_ma_prev <= long_ma_prev:
        # 信号强度基于价格距离均线的程度
        strength = min((short_ma - long_ma) / long_ma, 1.0)
        return {
            'symbol': context.symbol,
            'signal': 1,
            'strength': strength,
            'reason': f'自适应均线金叉 ({short_ma_key}/{long_ma_key})',
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
            'reason': f'自适应均线死叉 ({short_ma_key}/{long_ma_key})',
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
    avg_volume = context.market_context.get('avg_volume', volume)
    
    # 动态调整RSI阈值
    volatility = context.market_context.get('volatility', 0.2)
    if volatility > 0.3:  # 高波动市场，更严格的阈值
        oversold, overbought = 25, 75
    else:  # 低波动市场，标准阈值
        oversold, overbought = 30, 70
    
    # 超卖买入（需要成交量确认）
    if rsi < oversold and volume > avg_volume * 1.2:
        strength = (oversold - rsi) / oversold
        return {
            'symbol': context.symbol,
            'signal': 1,
            'strength': strength,
            'reason': f'RSI超卖+成交量确认 (RSI:{rsi:.1f})',
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
            'reason': f'RSI超买+成交量确认 (RSI:{rsi:.1f})',
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
    
    # 只在强趋势中生成信号
    if adx > 25:  # 强趋势
        if macd > 0:  # 上升趋势
            return {
                'symbol': context.symbol,
                'signal': 1,
                'strength': min(adx / 50, 1.0),
                'reason': f'强上升趋势确认 (ADX:{adx:.1f}, MACD:{macd:.3f})',
                'timestamp': context.timestamp,
                'indicators_used': ['MACD', 'ADX']
            }
        elif macd < 0:  # 下降趋势
            return {
                'symbol': context.symbol,
                'signal': -1,
                'strength': min(adx / 50, 1.0),
                'reason': f'强下降趋势确认 (ADX:{adx:.1f}, MACD:{macd:.3f})',
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
    avg_volume = context.market_context.get('avg_volume', volume)
    
    if support_level and resistance_level:
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