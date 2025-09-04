from math import log
from typing import Dict, Optional, Callable
import pandas as pd  # 添加这行
import numpy as np   # 也建议添加这行，因为volatility是numpy.float64类型
from .core import TechnicalSignalContext, SignalRuleFunc, ParameterizedRuleCreator, SignalType, RuleType
from .filter_rules import ParameterizedFilterFactory
from core.logger import logger
from app.services.analytics.indicator_service import calculate_adaptive_period, get_adaptive_periods_range
from common.debug_utils import debug_signals
class ParameterizedRuleFactory:
    """参数化规则工厂"""
    
    @staticmethod
    def create_ma_rule(short_period: int = 5, 
                      long_period: int = 20, 
                      volatility_threshold: float = 0.02, 
                      adaptive: bool = False,
                      filter_config: Optional[Dict] = None) -> SignalRuleFunc:
        """创建参数化均线规则"""
        def rule(context: TechnicalSignalContext) -> Optional[Dict]:
            # 前置过滤器检查 - 在信号计算前执行
            if filter_config and not _apply_front_signal_filters(context, filter_config):
                debug_signals(f'[MA规则调试] 前置过滤器拒绝，跳过信号计算')
                return None 
            # 收集调试信息标识符
            debug_flags = []
            debug_info = {}
            if adaptive:
                volatility = context.market_context.get('volatility', 0.1)
                # 简单的数值稳定性检查
                # volatility = float(volatility)  # 强制类型转换

                # 添加NaN检查
                if pd.isna(volatility) or volatility is None or volatility <= 0:
                    logger.warning(f'Invalid volatility: {volatility}')
                    volatility = 0.1
                vol_factor = 1 - volatility * 0.3  # 波动率越高，周期越短
                final_short_period = calculate_adaptive_period(
                    base_period=short_period,
                    volatility=volatility,
                    indicator_type='ma',
                    is_short=True
                )
                final_long_period = calculate_adaptive_period(
                    base_period=long_period,
                    volatility=volatility,
                    indicator_type='ma',
                    is_short=False
                )
                ma_short_key = f'MA_{final_short_period}'
                ma_long_key = f'MA_{final_long_period}'
                adjusted_threshold = volatility_threshold * (1 + volatility)
                debug_flags.append('ADAPTIVE')
                debug_info['volatility'] = volatility
                debug_info['vol_factor'] = vol_factor
                debug_info['period_change'] = f'{short_period}/{long_period} -> {final_short_period}/{final_long_period}'
                debug_info['threshold_calc'] = f'{volatility_threshold:.4f} * (1 + {volatility:.4f}) = {adjusted_threshold:.4f}'
            else:
                # 固定模式，最终周期就是基础周期
                final_short_period = short_period
                final_long_period = long_period
                ma_short_key = f'MA_{final_short_period}'
                ma_long_key = f'MA_{final_long_period}'       
                adjusted_threshold = volatility_threshold
                debug_flags.append('FIXED')
                debug_info['periods'] = f'{final_short_period}/{final_long_period}'
                debug_info['threshold'] = adjusted_threshold
            
            ma_short = context.indicators.get(ma_short_key, 0)
            ma_long = context.indicators.get(ma_long_key, 0)
            # 检查指标键匹配
            available_ma_keys = [k for k in context.indicators.keys() if k.startswith('MA_')]
            if ma_short_key not in context.indicators:
                debug_flags.append('SHORT_MISSING')
            if ma_long_key not in context.indicators:
                debug_flags.append('LONG_MISSING')
            if ma_short == 0 or ma_long == 0:
                debug_flags.append('ZERO_VALUES')
            
            debug_info['available_keys'] = sorted(available_ma_keys)
            # debug_signals(f'[MA规则调试] 规则状态变化标识: {"|" .join(debug_flags)} | {debug_info}')
            
            # 添加除零保护
            if ma_long == 0:
                return None  # 无法计算交叉比率时返回None
                
            crossover_ratio = abs(ma_short - ma_long) / ma_long
            
            # 金叉信号
            if ma_short > ma_long and crossover_ratio > adjusted_threshold:
                # 确定显示的周期信息
                signal = {
                    'symbol': context.symbol,
                    'signal': SignalType.BUY,
                    'strength': min(crossover_ratio * 10, 1.0),
                    'reason': f'MA金叉自适应({final_short_period}/{final_long_period}): {ma_short:.2f} > {ma_long:.2f}',
                    'timestamp': context.timestamp,
                    'rule_name': '参数化均线规则',
                    'category': RuleType.TREND_FOLLOWING  # 添加规则类型
                }
                return signal
            # 死叉信号
            elif ma_short < ma_long and crossover_ratio > adjusted_threshold:
                signal = {
                    'symbol': context.symbol,
                    'signal': SignalType.SELL,
                    'strength': min(crossover_ratio * 10, 1.0),
                    'reason': f'MA死叉自适应({final_short_period}/{final_long_period}): {ma_short:.2f} < {ma_long:.2f}',
                    'timestamp': context.timestamp,
                    'rule_name': '参数化均线规则',
                    'category': RuleType.TREND_FOLLOWING  # 添加规则类型
                }
                return signal
            # 均线平行，观望
            else:
                return {
                    'symbol': context.symbol,
                    'signal': SignalType.HOLD,
                    'strength': 0.0,
                    'reason': f'MA平行: MA{final_short_period}({ma_short:.2f}) ≈ MA{final_long_period}({ma_long:.2f})',
                    'timestamp': context.timestamp,
                    'rule_name': '参数化均线规则',
                    'category': RuleType.TREND_FOLLOWING  # 添加规则类型
                }
            
            return None
        
        # 设置规则元数据
        rule.metadata = {
            'chinese_name': f'自适应均线交叉规则(基准{short_period}/{long_period})' if adaptive else f'均线交叉规则({short_period}/{long_period})',
            'parameters': {
                'short_period': short_period,
                'long_period': long_period,
                'volatility_threshold': volatility_threshold,
                'adaptive': adaptive
            },
            'required_indicators': [
                # 使用与实际计算一致的自适应周期范围
                *[f'MA_{p}' for p in get_adaptive_periods_range(
                    base_period=short_period,
                    indicator_type='ma',
                    is_short=True,
                    volatility_range=(0.0, 1.0),
                    step=0.05
                )],
                *[f'MA_{p}' for p in get_adaptive_periods_range(
                    base_period=long_period,
                    indicator_type='ma',
                    is_short=False,
                    volatility_range=(0.0, 1.0),
                    step=0.05
                )],
                'volatility'
            ] if adaptive else [f'MA_{short_period}', f'MA_{long_period}'],
            'category': RuleType.TREND_FOLLOWING,  # 使用常量替代字符串
            'description': f'参数化均线交叉规则，可自定义短期({short_period})和长期({long_period})均线周期。' + 
                (f'启用自适应模式：根据市场波动率同时调整均线周期和交叉阈值。波动率高时周期缩短(最短3周期)，交叉阈值放宽；波动率低时周期接近设定值，阈值收紧。需要volatility指标支持。' if adaptive else 
                f'固定模式：使用固定的短期({short_period})、长期({long_period})周期和波动率阈值({volatility_threshold})。')
        }
        return rule
    
    @staticmethod
    def create_rsi_rule(period: int = 14, 
                       oversold: float = 30, 
                       overbought: float = 70,
                       adaptive: bool = False,
                       filter_config: Optional[Dict] = None) -> SignalRuleFunc:
        """创建参数化RSI规则"""
        def rule(context: TechnicalSignalContext) -> Optional[Dict]:
            # 前置过滤器检查 - 在信号计算前执行
            if filter_config and not _apply_front_signal_filters(context, filter_config):
                debug_signals(f'[RSI规则调试] 前置过滤器拒绝，跳过信号计算')
                return None 
            # 收集调试信息标识符
            debug_flags = []
            debug_info = {}
            # 自适应阈值调整
            if adaptive:
                volatility = context.market_context.get('volatility', 0.1)
                # 添加NaN检查
                if pd.isna(volatility) or volatility is None or volatility <= 0:
                    logger.warning(f'Invalid volatility: {volatility}')
                    volatility = 0.1
                final_period = calculate_adaptive_period(
                    base_period=period,
                    volatility=volatility,
                    indicator_type='rsi'
                )
                rsi_key = f'RSI_{final_period}'
                oversold_adj = max(20, oversold * (1 - volatility * 0.5))
                overbought_adj = min(80, overbought * (1 + volatility * 0.5))
                debug_flags.append('ADAPTIVE')
                debug_info['volatility'] = volatility
                debug_info['period_change'] = f'{period} -> {final_period}'
                debug_info['oversold_calc'] = f'{oversold:.1f} * (1 - {volatility:.4f} * 0.5) = {oversold_adj:.1f}'
                debug_info['overbought_calc'] = f'{overbought:.1f} * (1 + {volatility:.4f} * 0.5) = {overbought_adj:.1f}'
            else:
                # 固定模式，最终周期就是基础周期
                final_period = period
                rsi_key = f'RSI_{period}'
                oversold_adj = oversold
                overbought_adj = overbought
                debug_flags.append('FIXED')
                debug_info['period'] = period
                debug_info['oversold'] = oversold_adj
                debug_info['overbought'] = overbought_adj
            rsi = context.indicators.get(rsi_key, 50)

            # 检查指标键匹配
            available_rsi_keys = [k for k in context.indicators.keys() if k.startswith('RSI_')]
            if rsi_key not in context.indicators:
                debug_flags.append('RSI_MISSING')
            if rsi == 50:  # 默认值，可能表示数据缺失
                debug_flags.append('DEFAULT_VALUE')
            
            debug_info['rsi_key'] = rsi_key
            debug_info['rsi_value'] = rsi
            debug_info['available_keys'] = sorted(available_rsi_keys)
            # 统一输出调试信息
            # debug_signals(f'[RSI规则调试] 规则状态变化标识: {"|" .join(debug_flags)} | {debug_info}')
            # RSI超卖信号
            if rsi < oversold_adj:
                signal = {
                    'symbol': context.symbol,
                    'signal': SignalType.BUY,
                    'strength': min((oversold_adj - rsi) / oversold_adj, 1.0),
                    'reason': f'RSI超卖({final_period}周期): {rsi:.2f} < {oversold_adj:.1f}',
                    'timestamp': context.timestamp,
                    'rule_name': '参数化RSI规则',
                    'category': RuleType.MOMENTUM
                }
                
                return signal
            
            # RSI超买信号
            elif rsi > overbought_adj:
                signal = {
                    'symbol': context.symbol,
                    'signal': SignalType.SELL,
                    'strength': min((rsi - overbought_adj) / (100 - overbought_adj), 1.0),
                    'reason': f'RSI超买({final_period}周期): {rsi:.2f} > {overbought_adj:.1f}',
                    'timestamp': context.timestamp,
                    'rule_name': '参数化RSI规则',
                    'category': RuleType.MOMENTUM
                }
                
                return signal
            # RSI在正常区间，观望
            else:
                return {
                    'symbol': context.symbol,
                    'signal': SignalType.HOLD,
                    'strength': 0.0,
                    'reason': f'RSI正常: {rsi:.2f} (30-70区间)',
                    'timestamp': context.timestamp,
                    'rule_name': '参数化RSI规则',
                    'category': RuleType.MOMENTUM
                }

            
            return None
        
        rule.metadata = {
            'chinese_name': f'自适应RSI规则(基准{period}周期)' if adaptive else f'RSI规则({period}周期)',
            'parameters': {
                'period': period,
                'oversold': oversold,
                'overbought': overbought,
                'adaptive': adaptive
            },
            'required_indicators': [
                # 使用与实际计算一致的自适应周期范围
                *[f'RSI_{p}' for p in get_adaptive_periods_range(
                    base_period=period,
                    indicator_type='rsi',
                    volatility_range=(0.0, 1.0),
                    step=0.05
                )],
                'volatility'
            ] if adaptive else [f'RSI_{period}'],
            'category': RuleType.MOMENTUM,
            'description': f'参数化RSI规则，可自定义计算周期({period})、超卖阈值({oversold})和超买阈值({overbought})。' + 
                (f'启用自适应模式：根据市场波动率同时调整RSI计算周期和超买超卖阈值。波动率高时周期延长、阈值范围扩大(超卖降低、超买提高)；波动率低时周期缩短、阈值收紧。周期范围7-21，需要volatility指标支持。' if adaptive else 
                f'固定模式：使用固定的计算周期({period})、超卖阈值({oversold})和超买阈值({overbought})。')
        }
        return rule

def _apply_front_signal_filters(context: TechnicalSignalContext, filter_config: Dict) -> bool:
    """应用前置过滤器 - 在信号计算前执行"""
    front_filters = filter_config.get('front_signal_filters', {})
    
    # 波动率过滤
    if front_filters.get('volatility_filter', {}).get('enable', False):
        vol_config = front_filters['volatility_filter']
        volatility_filter = ParameterizedFilterFactory.create_volatility_filter(
            min_volatility=vol_config.get('min_volatility', 0.01),
            max_volatility=vol_config.get('max_volatility', 0.5)
        )
        # 创建一个临时信号对象用于过滤器检查
        temp_signal = {'symbol': context.symbol}
        if not volatility_filter(temp_signal, context):
            debug_signals(f'[前置过滤] 波动率过滤器拒绝')
            return False
    
    # 趋势强度过滤
    if front_filters.get('trend_strength_filter', {}).get('enable', False):
        trend_config = front_filters['trend_strength_filter']
        adx = context.indicators.get('ADX', 0)
        min_adx = trend_config.get('min_adx', 25)
        if adx < min_adx:
            debug_signals(f'[前置过滤] 趋势强度过滤器拒绝: ADX={adx:.2f} < {min_adx}')
            return False
    
    # 成交量确认过滤
    if front_filters.get('volume_confirmation', {}).get('enable', False):
        vol_config = front_filters['volume_confirmation']
        volume_filter = ParameterizedFilterFactory.create_volume_filter(
            volume_multiplier=vol_config.get('volume_multiplier', 1.2),
            lookback_days=vol_config.get('lookback_days', 20)
        )
        temp_signal = {'symbol': context.symbol}
        if not volume_filter(temp_signal, context):
            debug_signals(f'[前置过滤] 成交量确认过滤器拒绝')
            return False
    
    return True

def _apply_post_signal_filters(signal: Dict, context: TechnicalSignalContext, filter_config: Dict) -> bool:
    """应用后置过滤器 - 在信号生成后执行"""
    post_filters = filter_config.get('post_signal_filters', {})
    
    # 信号强度过滤
    if post_filters.get('signal_strength_filter', {}).get('enable', False):
        strength_config = post_filters['signal_strength_filter']
        min_strength = strength_config.get('min_strength', 0.5)
        if signal.get('strength', 0) < min_strength:
            debug_signals(f'[后置过滤] 信号强度过滤器拒绝: {signal.get("strength", 0):.3f} < {min_strength}')
            return False
    
    # 价格动量过滤
    # if post_filters.get('price_momentum_filter', {}).get('enable', False):
    #     momentum_config = post_filters['price_momentum_filter']
        # 这里可以添加价格动量检查逻辑
        # ...
    
    return True

# 参数化规则创建器注册表
PARAMETERIZED_RULE_CREATORS = {
    'ma_crossover': ParameterizedRuleFactory.create_ma_rule,
    'rsi': ParameterizedRuleFactory.create_rsi_rule,
}