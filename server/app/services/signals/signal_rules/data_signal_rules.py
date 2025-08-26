from typing import Dict, Optional, List, Callable
from functools import partial
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
# ============ 信号生成规则 ============
# 动态均线交叉规则（已完成）
# 固定参数
def default_ma_crossover_rule(context: TechnicalSignalContext) -> Optional[Dict]:
    """自适应均线交叉规则（固定参数版本）"""
    return adaptive_ma_crossover_rule_with_params(context, volatility_threshold=0.3, adaptive=False)
# 动态参数：创建规则（携带基础参数和过滤配置）->传入
def create_parameterized_ma_rule(short_period: int = 5, 
                                long_period: int = 20, 
                                volatility_threshold: float = 0.3, 
                                adaptive: bool = False,
                                filter_config: Optional[Dict] = None) -> Callable:
    """
    创建参数化的MA规则，支持独立的过滤规则配置
    """
    def ma_rule_with_filters(context: TechnicalSignalContext) -> Optional[Dict]:
        return adaptive_ma_crossover_rule_with_params(
            context, 
            short_period=short_period, 
            long_period=long_period,
            volatility_threshold=volatility_threshold,
            adaptive=adaptive,
            filter_config=filter_config
        )
    
    # 设置规则名称和描述
    filter_desc = ""
    if filter_config:
        enabled_filters = [k for k, v in filter_config.items() if v.get('enable', False)]
        filter_desc = f",过滤器:{','.join(enabled_filters)}"
    
    adaptive_desc = "自适应" if adaptive else "固定"
    ma_rule_with_filters.chinese_name = f'MA交叉规则({adaptive_desc},短:{short_period},长:{long_period}{filter_desc})'
    ma_rule_with_filters.__name__ = f'ma_rule_{short_period}_{long_period}_{adaptive}'
    
    return ma_rule_with_filters
def adaptive_ma_crossover_rule_with_params(context: TechnicalSignalContext,
                                         short_period: int = 5,
                                         long_period: int = 20,
                                         volatility_threshold: float = 0.3,
                                         adaptive: bool = False,
                                         filter_config: Optional[Dict] = None) -> Optional[Dict]:
    """
    参数化的自适应均线交叉规则，支持独立的过滤规则配置
    """
    # 保存原始配置参数
    original_short_period = short_period
    original_long_period = long_period
    original_volatility_threshold = volatility_threshold

    # 获取当前函数的规则名称
    indicators = context.indicators
    
    # 默认过滤规则配置
    if filter_config is None:
        filter_config = {
            'volatility_filter': {'enable': False, 'min_volatility': 0.3, 'max_volatility': 0.5},
            'volume_confirmation': {'enable': False, 'volume_multiplier': 1.1, 'lookback_days': 20},
            'trend_strength_filter': {'enable': False, 'min_adx': 25},
            'price_momentum_filter': {'enable': False,'momentum_threshold': 0.01,'lookback_periods': 3},
            'signal_strength_filter': {'enable': False,'min_strength': 0.6}
        }
    generation_details = []
    # 根据adaptive参数动态生成规则名称
    if adaptive:
        rule_name = '自适应均线交叉规则(参数化-自适应模式)'
    else:
        rule_name = '均线交叉规则(参数化-固定模式)'
    if adaptive:
        # 自适应逻辑
        available_mas = [key for key in indicators.keys() if key.startswith('MA')]
        if len(available_mas) < 2:
            return None
        
        volatility = context.market_context.get('volatility', 0.2)
        generation_details.append(f"启用自适应模式，当前市场波动率: {volatility:.3f}")

        if volatility > volatility_threshold and 'MA3' in available_mas and 'MA10' in available_mas:
            short_ma_key, long_ma_key = 'MA3', 'MA10'
            actual_short_period, actual_long_period = 3, 10
            generation_details.append(f"高波动市场(>{volatility_threshold})：选择敏感组合MA3/MA10")
        elif f'MA{short_period}' in available_mas and f'MA{long_period}' in available_mas:
            short_ma_key, long_ma_key = f'MA{short_period}', f'MA{long_period}'
            actual_short_period, actual_long_period = short_period, long_period
            generation_details.append(f"使用配置的基础周期组合MA{short_period}/MA{long_period}")
        else:
            # 使用可用的最短和最长周期
            periods = [int(ma[2:]) for ma in available_mas]
            periods.sort()
            short_ma_key, long_ma_key = f'MA{periods[0]}', f'MA{periods[-1]}'
            actual_short_period, actual_long_period = periods[0], periods[-1]
            generation_details.append(f"配置周期不可用，使用可用的最短/最长周期MA{actual_short_period}/MA{actual_long_period}")
    else:
        # 固定周期
        short_ma_key, long_ma_key = f'MA{short_period}', f'MA{long_period}'
        actual_short_period, actual_long_period = short_period, long_period
        generation_details.append(f"固定参数模式：使用MA{short_period}/MA{long_period}")
    
    if short_ma_key not in indicators or long_ma_key not in indicators:
        return None
    
    short_ma = indicators[short_ma_key]
    long_ma = indicators[long_ma_key]
    short_ma_prev = indicators.get(f'{short_ma_key}_prev', short_ma)
    long_ma_prev = indicators.get(f'{long_ma_key}_prev', long_ma)
    # generation_details.append(f"当前均线值: {short_ma_key}={short_ma:.2f}, {long_ma_key}={long_ma:.2f}")
    # generation_details.append(f"前期均线值: {short_ma_key}={short_ma_prev:.2f}, {long_ma_key}={long_ma_prev:.2f}")
    # 确保所有均线值都不是None或NaN
    if (short_ma is None or pd.isna(short_ma) or 
        long_ma is None or pd.isna(long_ma) or 
        short_ma_prev is None or pd.isna(short_ma_prev) or 
        long_ma_prev is None or pd.isna(long_ma_prev) or
        long_ma == 0):  # 避免除零错误
        return None
    
    signal = None
    # 金叉买入
    if short_ma > long_ma and short_ma_prev <= long_ma_prev:
        generation_details.append(f"触发金叉条件: 当前{short_ma:.2f}>{long_ma:.2f} 且 前期{short_ma_prev:.2f}<={long_ma_prev:.2f}")
        # 修复：使用更敏感的强度计算公式
        price_diff_ratio = abs(short_ma - long_ma) / long_ma
        if price_diff_ratio < 0.01:  # 差距小于1%
            strength = 0.3
        elif price_diff_ratio < 0.02:  # 差距小于2%
            strength = 0.5
        elif price_diff_ratio < 0.05:  # 差距小于5%
            strength = 0.7
        else:  # 差距大于5%
            strength = 1.0
        signal = {
            'symbol': context.symbol,
            'rule_name': rule_name,
            'signal': 1,
            'strength': strength,
            'generation_details': '; '.join(generation_details),
            'reason': f'均线金叉{short_ma_key}>{long_ma_key}({short_ma:.2f}>{long_ma:.2f}),参数({actual_short_period}/{actual_long_period})',
            'timestamp': context.timestamp,
            'indicators_used': [short_ma_key, long_ma_key],
            'fixed_params': {
                'short_period': original_short_period,
                'long_period': original_long_period,
            },
            'adaptive_params': {
                'short_period': actual_short_period,
                'long_period': actual_long_period,
                'volatility_threshold': volatility_threshold,
                'volatility': context.market_context.get('volatility', 0.2)
            } if adaptive else None
        }
    
    # 死叉卖出
    elif short_ma < long_ma and short_ma_prev >= long_ma_prev:
        generation_details.append(f"触发死叉条件: 当前{short_ma:.2f}<{long_ma:.2f} 且 前期{short_ma_prev:.2f}>={long_ma_prev:.2f}")
        # 修复：使用更敏感的强度计算公式
        price_diff_ratio = abs(short_ma - long_ma) / long_ma
        if price_diff_ratio < 0.01:  # 差距小于1%
            strength = 0.3
        elif price_diff_ratio < 0.02:  # 差距小于2%
            strength = 0.5
        elif price_diff_ratio < 0.05:  # 差距小于5%
            strength = 0.7
        else:  # 差距大于5%
            strength = 1.0
        signal = {
            'symbol': context.symbol,
            'rule_name': rule_name,
            'signal': -1,
            'strength': strength,
            'generation_details': '; '.join(generation_details),
            'reason': f'均线死叉{short_ma_key}<{long_ma_key}({short_ma:.2f}<{long_ma:.2f}),参数({actual_short_period}/{actual_long_period})',
            'timestamp': context.timestamp,
            'indicators_used': [short_ma_key, long_ma_key],
            'fixed_params': {
                'short_period': original_short_period,
                'long_period': original_long_period,
            },
            'adaptive_params': {
                'short_period': actual_short_period,
                'long_period': actual_long_period,
                'volatility_threshold': volatility_threshold,
                'volatility': context.market_context.get('volatility', 0.2)
            } if adaptive else None
        }
    else:
        generation_details.append(f"未触发交叉条件: 无金叉或死叉发生")
        return None

    if signal is None:
        return None
    
    # 应用过滤规则
    if not _apply_rule_filters(signal, context, filter_config):
        return None
    
    return signal

# RSI规则（已完成）
# 固定参数
def default_rsi_rule(context: TechnicalSignalContext) -> Optional[Dict]:
    """自适应RSI规则（固定参数版本）"""
    return adaptive_rsi_rule_with_params(context, oversold=30, overbought=70)
# 动态参数：创建规则（携带基础参数和过滤配置）->传入
def create_parameterized_rsi_rule(period: int = 14, 
                                 oversold: int = 30, 
                                 overbought: int = 70,
                                 adaptive: bool = False,  # 新增自适应参数 
                                 filter_config: Optional[Dict] = None) -> Callable:
    """
    创建参数化的RSI规则，支持独立的过滤规则配置
    """
    def rsi_rule_with_filters(context: TechnicalSignalContext) -> Optional[Dict]:
        return adaptive_rsi_rule_with_params(
            context, 
            base_period=period, 
            oversold=oversold, 
            overbought=overbought,
            adaptive=adaptive,  # 传递自适应参数
            filter_config=filter_config
        )
    
    # 设置规则名称和描述
    filter_desc = ""
    if filter_config:
        enabled_filters = [k for k, v in filter_config.items() if v.get('enable', False)]
        filter_desc = f",过滤器:{','.join(enabled_filters)}"
    
    adaptive_desc = "自适应" if adaptive else "固定"
    rsi_rule_with_filters.chinese_name = f'RSI规则({adaptive_desc},周期:{period},超卖:{oversold},超买:{overbought}{filter_desc})'
    rsi_rule_with_filters.__name__ = f'rsi_rule_{period}_{oversold}_{overbought}_{adaptive}'
    
    return rsi_rule_with_filters
    
def adaptive_rsi_rule_with_params(context: TechnicalSignalContext,
                                base_period: int = 14,
                                oversold: float = 30,
                                overbought: float = 70,
                                adaptive: bool = False,  # 新增自适应参数
                                filter_config: Optional[Dict] = None) -> Optional[Dict]:
    """
    参数化的自适应RSI规则，支持独立的过滤规则配置
    :param context: TechnicalSignalContext, 技术指标上下文
    :param base_period: RSI基础周期
    :param oversold: 超卖阈值
    :param overbought: 超买阈值
    :param adaptive: 是否启用自适应周期
    :param filter_config: 过滤规则配置
    """
    # 保存原始配置参数
    original_base_period = base_period
    original_oversold = oversold
    original_overbought = overbought

    indicators = context.indicators
    generation_details = []
    # 默认过滤规则配置
    if filter_config is None:
        filter_config = {
            'volume_confirmation': {
                'enable': False,
                'volume_multiplier': 1.2,
                'lookback_days': 20
            },
            'volatility_filter': {
                'enable': False,
                'min_volatility': 0.01,
                'max_volatility': 0.5
            },
            'signal_strength_filter': {
                'enable': False,
                'min_strength': 0.6
            }
        }
    # 动态生成精确的规则名称
    if adaptive:
        rule_name = '自适应RSI规则(参数化-自适应模式)'
    else:
        rule_name = f'固定参数RSI规则(参数化-固定模式)'
    # 自适应周期逻辑
    if adaptive:
        # 根据市场波动率调整RSI周期
        volatility = context.market_context.get('volatility', 0.2)
        generation_details.append(f"启用自适应模式，当前市场波动率: {volatility:.3f}")
        
        if volatility > 0.4:  # 高波动市场
            period = max(base_period - 4, 7)  # 缩短周期，更敏感
            # 调整阈值，高波动时更严格
            oversold = max(oversold - 5, 20)
            overbought = min(overbought + 5, 85)
            generation_details.append(f"高波动市场(>{0.4})：周期缩短至{period}，阈值调整为超卖{oversold}/超买{overbought}")
        elif volatility < 0.15:  # 低波动市场
            period = min(base_period + 7, 28)  # 延长周期，减少噪音
            # 调整阈值，低波动时更宽松
            oversold = min(oversold + 5, 40)
            overbought = max(overbought - 5, 60)
            generation_details.append(f"低波动市场(<{0.15})：周期延长至{period}，阈值调整为超卖{oversold}/超买{overbought}")
        else:  # 中等波动
            period = base_period
            generation_details.append(f"中等波动市场：使用基础周期{period}，阈值保持超卖{oversold}/超买{overbought}")
    else:
        period = base_period
        generation_details = [f"固定参数模式：周期{period}，超卖{oversold}/超买{overbought}"]
    
    # 获取RSI值
    rsi_column = f'RSI{period}'
    if rsi_column not in indicators:
        # 如果没有对应周期的RSI，尝试使用基础周期
        rsi_column = f'RSI{base_period}'
        if rsi_column not in indicators:
            return None
        generation_details.append(f"警告：未找到RSI{period}，使用{rsi_column}")
    else:
        generation_details.append(f"使用指标：{rsi_column}")
    rsi = indicators[rsi_column]
    if rsi is None or pd.isna(rsi):
        return None
    
    signal = None
    # 使用分段函数计算强度
    if rsi <= oversold:
        # 超卖程度越深，强度越高
        if rsi <= 20:  # 极度超卖
            strength = 1.0
        elif rsi <= 25:  # 严重超卖
            strength = 0.8
        else:  # 轻度超卖
            strength = 0.5
            
    elif rsi >= overbought:
        # 超买程度越深，强度越高
        if rsi >= 80:  # 极度超买
            strength = 1.0
        elif rsi >= 75:  # 严重超买
            strength = 0.8
        else:  # 轻度超买
            strength = 0.5
    # 生成基础信号
    if rsi <= oversold:
        generation_details.append(f"触发超卖条件: {rsi:.1f} <= {oversold}")
        signal = {
            'symbol': context.symbol,
            'rule_name': rule_name,
            'signal': 1,
            # 'strength': min((oversold - rsi) / oversold, 1.0),
            'strength': strength,
            'generation_details': '; '.join(generation_details),
            'reason': f'RSI{period}超卖信号 (RSI:{rsi:.1f}<={oversold})',  # 使用实际的period而不是base_period
            'timestamp': context.timestamp,
            'indicators_used': [f'RSI{period}'],  # 使用实际的period而不是base_period
            'fixed_params': {
                'period': original_base_period,  # 实际使用的周期
                'oversold': original_oversold,
                'overbought': original_overbought,
            },
            'adaptive_params': {
                'period': period,  # 使用实际的period而不是base_period
                'oversold': oversold,
                'overbought': overbought,
                'volatility': context.market_context.get('volatility', 0.2)
            } if adaptive else None
        }
    elif rsi >= overbought:
        generation_details.append(f"触发超买条件: {rsi:.1f} >= {overbought}")
        signal = {
            'symbol': context.symbol,
            'rule_name': rule_name,
            'signal': -1,
            # 'strength': min((rsi - overbought) / (100 - overbought), 1.0),
            'strength': strength,
            'generation_details': '; '.join(generation_details),
            'reason': f'RSI{period}超买信号 (RSI:{rsi:.1f}>={overbought})',  # 使用实际的period而不是base_period
            'timestamp': context.timestamp,
            'indicators_used': [f'RSI{period}'],  # 使用实际的period而不是base_period
            'fixed_params': {
                'period': original_base_period,  # 实际使用的周期
                'oversold': original_oversold,
                'overbought': original_overbought,
            },
            'adaptive_params': {
                'period': period,  # 使用实际的period而不是base_period
                'oversold': oversold,
                'overbought': overbought,
                'volatility': context.market_context.get('volatility', 0.2)
            } if adaptive else None
        }
    else:
        generation_details.append(f"未触发信号条件: {oversold} < {rsi:.1f} < {overbought}")
    
    # 如果没有生成信号，直接返回
    if signal is None:
        return None
    
    # 应用过滤规则
    if not _apply_rule_filters(signal, context, filter_config):
        return None
    
    return signal

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

# 设置中文名称
trend_strength_filter_rule.chinese_name = '趋势强度过滤规则(固定参数)'
support_resistance_breakout_rule.chinese_name = '支撑阻力突破规则(固定参数)'
default_rsi_rule.chinese_name = '默认周期RSI规则(固定参数)'
adaptive_rsi_rule_with_params.chinese_name = '自适应RSI规则(参数化)'
default_ma_crossover_rule.chinese_name = '自适应均线交叉规则(固定参数)'
adaptive_ma_crossover_rule_with_params.chinese_name = '自适应均线交叉规则(参数化)'
# 更新规则名称字典，区分固定和参数化版本
RULE_NAMES = {
    'default_ma_crossover_rule': '自适应均线交叉规则(固定参数)',
    'default_rsi_rule': '自适应RSI规则(固定参数)', 
    'trend_strength_filter_rule': '趋势强度过滤规则(固定参数)',
    'support_resistance_breakout_rule': '支撑阻力突破规则(固定参数)',
    'adaptive_ma_crossover_rule_with_params': '自适应均线交叉规则(参数化)',
    'adaptive_rsi_rule_with_params': '自适应RSI规则(参数化)',
}
# ============ 规则级内部过滤 ==============
# 内部过滤规则应用函数
def _apply_rule_filters(signal: Dict, context: TechnicalSignalContext, filter_config: Dict) -> bool:
    """
    应用规则内部的过滤规则配置
    :param signal: 生成的信号
    :param context: 技术指标上下文
    :param filter_config: 过滤规则配置
    :return: 是否通过过滤
    """
    # 成交量确认过滤
    if filter_config.get('volume_confirmation', {}).get('enable', False):
        vol_config = filter_config['volume_confirmation']
        # 创建临时的参数化过滤器
        volume_filter = create_parameterized_volume_filter(
            volume_multiplier=vol_config.get('volume_multiplier', 1.2),
            lookback_days=vol_config.get('lookback_days', 20)
        )
        if not volume_filter(signal, context):
            return False
    
    # 波动率过滤
    if filter_config.get('volatility_filter', {}).get('enable', False):
        vol_config = filter_config['volatility_filter']
        volatility_filter = create_parameterized_volatility_filter(
            min_volatility=vol_config.get('min_volatility', 0.01),
            max_volatility=vol_config.get('max_volatility', 0.5)
        )
        if not volatility_filter(signal, context):
            return False
    
    # 信号强度过滤
    if filter_config.get('signal_strength_filter', {}).get('enable', False):
        strength_config = filter_config['signal_strength_filter']
        min_strength = strength_config.get('min_strength', 0.5)
        if signal.get('strength', 0) < min_strength:
            return False
    
    # 趋势强度过滤
    if filter_config.get('trend_strength_filter', {}).get('enable', False):
        trend_config = filter_config['trend_strength_filter']
        min_adx = trend_config.get('min_adx', 25)
        adx = context.indicators.get('ADX', 0)
        if adx < min_adx:
            return False
    
    # 价格动量过滤
    if filter_config.get('price_momentum_filter', {}).get('enable', False):
        momentum_config = filter_config['price_momentum_filter']
        momentum_threshold = momentum_config.get('momentum_threshold', 0.02)
        price_change = context.market_context.get('price_momentum', 0)
        
        if signal.get('signal', 0) > 0:  # 买入信号
            if price_change < momentum_threshold:
                return False
        elif signal.get('signal', 0) < 0:  # 卖出信号
            if price_change > -momentum_threshold:
                return False
    
    return True
# ============ 独立的过滤规则 ============
# 过滤规则的函数签名：(signal: Dict, context: TechnicalSignalContext) -> bool
# 成交量确认过滤
def volume_confirmation_filter(signal: Dict, context: TechnicalSignalContext) -> bool:
    """
    成交量确认过滤规则
    只允许有成交量放大确认的信号通过
    """
    volume = context.volume
    avg_volume = context.market_context.get('avg_volume_20', 0)
    
    if avg_volume == 0:
        return True  # 无法计算时默认通过
    
    # 成交量需要超过20日均量的1.2倍
    volume_ratio = volume / avg_volume
    return volume_ratio > 1.2
# 波动率过滤
def volatility_filter(signal: Dict, context: TechnicalSignalContext) -> bool:
    """
    波动率过滤规则
    在极端波动环境中过滤信号
    """
    volatility = context.market_context.get('volatility', 0)
    
    # 波动率过高或过低时都过滤信号
    if volatility > 0.5:  # 波动率过高
        return False
    if volatility < 0.01:  # 波动率过低（可能是数据问题）
        return False
    
    return True
# 趋势强度过滤
def trend_strength_filter(signal: Dict, context: TechnicalSignalContext) -> bool:
    """
    趋势强度过滤规则
    只允许在强趋势环境中的信号通过
    """
    indicators = context.indicators
    
    # 需要MACD和ADX指标
    if 'MACD' not in indicators or 'ADX' not in indicators:
        return True  # 如果没有指标，默认通过
    
    macd = indicators['MACD']
    adx = indicators['ADX']
    
    # 确保指标值有效
    if pd.isna(macd) or pd.isna(adx):
        return True  # 数据无效时默认通过
    
    # 只在强趋势中允许信号通过
    if adx > 25:  # 强趋势
        return True
    
    return False  # 弱趋势中拒绝信号
# 信号强度过滤
def signal_strength_filter(signal: Dict, context: TechnicalSignalContext) -> bool:
    """
    信号强度过滤规则
    只允许强度足够的信号通过
    """
    strength = signal.get('strength', 0)
    return strength > 0.5  # 信号强度需要大于0.5
# 加工动量过滤
def price_momentum_filter(signal: Dict, context: TechnicalSignalContext) -> bool:
    """
    价格动量过滤规则
    确保信号方向与价格动量一致
    """
    signal_direction = signal.get('signal', 0)
    if signal_direction == 0:
        return True  # 中性信号直接通过
    
    # 获取价格动量指标
    price_change = context.market_context.get('price_change_pct', 0)
    
    # 买入信号需要价格上涨动量，卖出信号需要价格下跌动量
    if signal_direction > 0:  # 买入信号
        return price_change > -0.02  # 价格跌幅不超过2%
    else:  # 卖出信号
        return price_change < 0.02   # 价格涨幅不超过2%

def time_filter(signal: Dict, context: TechnicalSignalContext) -> bool:
    """
    时间过滤规则
    在特定时间段过滤信号（如开盘前30分钟）
    """
    timestamp = context.timestamp
    
    # 如果是交易日的开盘前30分钟，过滤信号
    if timestamp.hour == 9 and timestamp.minute < 30:
        return False
    
    # 如果是收盘前10分钟，过滤信号
    if timestamp.hour == 14 and timestamp.minute >= 50:
        return False
    
    return True

# 创建参数化过滤规则
def create_parameterized_volatility_filter(min_volatility: float = 0.01, 
                                          max_volatility: float = 0.5) -> Callable:
    """创建参数化的波动率过滤规则"""
    def volatility_filter_parameterized(signal: Dict, context: TechnicalSignalContext) -> bool:
        volatility = context.market_context.get('volatility', 0)
        return min_volatility <= volatility <= max_volatility
    
    volatility_filter_parameterized.chinese_name = f'波动率过滤规则(参数化:{min_volatility}-{max_volatility})'
    volatility_filter_parameterized.__name__ = f'volatility_filter_{min_volatility}_{max_volatility}'
    return volatility_filter_parameterized
def create_adaptive_volatility_filter(base_threshold: float = 0.3) -> Callable:
    """创建自适应波动率过滤规则"""
    def adaptive_volatility_filter(signal: Dict, context: TechnicalSignalContext) -> bool:
        volatility = context.market_context.get('volatility', 0.2)
        
        # 根据信号类型调整波动率阈值
        if signal.get('signal', 0) > 0:  # 买入信号
            # 买入时可以容忍更高的波动率
            return volatility <= base_threshold * 1.5
        else:  # 卖出信号
            # 卖出时要求更低的波动率
            return volatility <= base_threshold
    
    adaptive_volatility_filter.chinese_name = f'自适应波动率过滤规则(基础阈值:{base_threshold})'
    adaptive_volatility_filter.__name__ = f'adaptive_volatility_filter_{base_threshold}'
    return adaptive_volatility_filter
def create_parameterized_volume_filter(volume_multiplier: float = 1.2, 
                                      lookback_days: int = 20) -> Callable:
    """
    创建参数化的成交量确认过滤器
    """
    def volume_filter(signal: Dict, context: TechnicalSignalContext) -> bool:
        current_volume = context.volume
        avg_volume_key = f'avg_volume_{lookback_days}d'
        avg_volume = context.market_context.get(avg_volume_key, current_volume)
        return current_volume >= avg_volume * volume_multiplier
    
    return volume_filter
def create_parameterized_signal_strength_filter(min_strength: float = 0.5) -> Callable:
    """
    创建参数化的信号强度过滤器
    """
    def strength_filter(signal: Dict, context: TechnicalSignalContext) -> bool:
        return signal.get('strength', 0) >= min_strength
    
    return strength_filter

# 过滤规则名称映射
FILTER_RULE_NAMES = {
    'volume_confirmation_filter': '成交量确认过滤规则',
    'volatility_filter': '波动率过滤规则',
    'trend_strength_filter': '趋势强度过滤规则',
    'price_momentum_filter': '价格动量过滤规则',
    'signal_strength_filter': '信号强度过滤规则',
    'time_filter': '时间过滤规则',
}

# 设置中文名称
volume_confirmation_filter.chinese_name = '成交量确认过滤规则'
volatility_filter.chinese_name = '波动率过滤规则'
trend_strength_filter.chinese_name = '趋势强度过滤规则'
signal_strength_filter.chinese_name = '信号强度过滤规则'
price_momentum_filter.chinese_name = '价格动量过滤规则'
time_filter.chinese_name = '时间过滤规则'

# 导出常用过滤规则组合
DEFAULT_FILTER_RULES = [
    trend_strength_filter,
    volume_confirmation_filter,
    signal_strength_filter
]

STRICT_FILTER_RULES = [
    trend_strength_filter,
    volume_confirmation_filter,
    signal_strength_filter,
    price_momentum_filter,
    volatility_filter
]