from core.logger import logger
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime

# 导入数据驱动相关
from .signal_rules.data_signal_rules import (
    TechnicalSignalContext,
    adaptive_ma_crossover_rule,
    adaptive_rsi_rule,
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
        logger.debug(f"[SignalService]开始生成数据信号，数据行数: {len(df)}, 信号规则数量: {len(self.signal_rules)}")
        logger.info(f"[SignalService]信号规则: {[rule.__name__ for rule in self.signal_rules]}")
        logger.info(f"[SignalService]过滤规则: {[rule.__name__ for rule in self.filter_rules]}")
        logger.info(f"[SignalService]可用指标: {list(indicators.keys())}")
        for name, series in indicators.items():
            valid_count = series.notna().sum()
            # logger.info(f"[SignalService]指标 {name}: 长度={len(series)}, 有效值数量={valid_count}, 类型={series.dtype}")
            # if len(series) > 0:
            #     logger.info(f"[SignalService]指标 {name} 样本值: 索引20={series.iloc[20] if len(series) > 20 else 'N/A'}, 索引50={series.iloc[50] if len(series) > 50 else 'N/A'}")
        
        for i in range(1, len(df)):  # 从第二行开始，确保有前一期数据
            row = df.iloc[i]
            prev_row = df.iloc[i-1]
            
            # 获取价格和成交量，确保是数值类型
            price_raw = row.get('收盘价', row.get('close', row.get('收盘', 0)))
            volume_raw = row.get('成交量', row.get('volume', 0))
            
            # 转换为数值类型
            try:
                price = float(pd.to_numeric(price_raw, errors='coerce'))
                if pd.isna(price):
                    price = 0.0
            except (ValueError, TypeError):
                price = 0.0
                
            try:
                volume = float(pd.to_numeric(volume_raw, errors='coerce'))
                if pd.isna(volume):
                    volume = 0.0
            except (ValueError, TypeError):
                volume = 0.0
            
            # 提取指标值
            extracted_indicators = self._extract_indicators(indicators, i, prev_row)
            market_context = self._calculate_market_context(df, i)
            
            # 构建技术信号上下文
            context = TechnicalSignalContext(
                symbol=row.get('证券代码', row.get('symbol', 'UNKNOWN')),
                timestamp=row.get('日期', row.get('date', pd.Timestamp.now())),
                price=price,  # 使用转换后的数值
                volume=volume,  # 使用转换后的数值
                indicators=extracted_indicators,
                market_context=market_context
            )
            # 应用所有信号规则
            for rule_idx, rule in enumerate(self.signal_rules):
                try:
                     # 在循环开始就定义 rule_name，确保在所有分支中都可用
                    rule_name = getattr(rule, 'chinese_name', rule.__name__ if hasattr(rule, '__name__') else f"规则{rule_idx}")
                    signal = rule(context)
                    if signal:
                        # 应用过滤规则
                        if self._apply_filters(signal, context):
                            # 应用权重规则
                            signal = self._apply_weights(signal, context)
                            signals.append(signal)
                            if i % 100 == 0:
                                logger.debug(f"[SignalService]规则{rule_name}在第{i}行生成信号: 类型={signal.get('signal')}, 强度={signal.get('strength'):.3f}, 原因={signal.get('reason')}, 使用指标={signal.get('indicators_used')}")
                        else:
                            if i % 100 == 0:
                                logger.debug(f"[SignalService]信号被过滤规则拒绝")
                    else:
                        if i % 100 == 0:  # 每50行记录一次，避免日志过多
                            logger.debug(f"[SignalService]规则{rule_name}在第{i}行未触发(每100的抽样)")
                except Exception as e:
                    logger.error(f"[SignalService]规则{rule_idx}在第{i}行执行失败: {e}")
                    import traceback
                    logger.error(f"[SignalService]错误详情: {traceback.format_exc()}")
        # 统计生成的信号类型分布
        signal_type_stats = {}
        for signal in signals:
            signal_type = signal.get('signal', 'unknown')
            signal_type_stats[signal_type] = signal_type_stats.get(signal_type, 0) + 1
        logger.info(f"[DataSignalService]信号类型分布: {signal_type_stats}")    
        return signals
    
    def _extract_indicators(self, indicators: Dict, index: int, prev_row) -> Dict[str, float]:
        """提取当前时点的指标值"""
        result = {}
        for name, series in indicators.items():
            if index < len(series):
                # 确保指标值是数值类型
                value = series.iloc[index]
                if pd.notna(value):
                    try:
                        converted_value = float(pd.to_numeric(value, errors='coerce'))
                        result[name] = converted_value
                    except (ValueError, TypeError) as e:
                        result[name] = 0.0
                else:
                    result[name] = 0.0
                
                # 处理前一期值 - 这部分必须在for循环内部！
                if index > 0:
                    prev_value = series.iloc[index-1]
                    if pd.notna(prev_value):
                        try:
                            converted_prev_value = float(pd.to_numeric(prev_value, errors='coerce'))
                            result[f'{name}_prev'] = converted_prev_value
                        except (ValueError, TypeError) as e:
                            result[f'{name}_prev'] = 0.0
                    else:
                        result[f'{name}_prev'] = 0.0
        # 添加调试信息
        if index % 50 == 0:
            logger.info(f"[SignalService]第{index}行提取的指标: {result}")
        return result
    
    def _calculate_market_context(self, df: pd.DataFrame, index: int) -> Dict[str, float]:
        """计算市场环境上下文"""
        # 计算最近20期的波动率
        start_idx = max(0, index - 20)
        recent_data = df.iloc[start_idx:index+1]
        
        if len(recent_data) > 1:
            # 优先使用中文列名，再尝试英文列名
            close_col = None
            if '收盘价' in recent_data.columns:
                close_col = '收盘价'
            elif 'close' in recent_data.columns:
                close_col = 'close'
            elif '收盘' in recent_data.columns:
                close_col = '收盘'
            
            if close_col:
                returns = recent_data[close_col].pct_change().dropna()
                if len(returns) > 0:
                    daily_volatility = returns.std()
                    # 年化波动率：日波动率 * sqrt(252)
                    volatility = daily_volatility * np.sqrt(252)
                else:
                    volatility = 0.2
            else:
                volatility = 0.2
        else:
            volatility = 0.2
        
        # 计算平均成交量，确保不返回NaN
        volume_col = None
        if '成交量' in recent_data.columns:
            volume_col = '成交量'
        elif 'volume' in recent_data.columns:
            volume_col = 'volume'
        
        if volume_col and not recent_data[volume_col].empty:
            # 先转换为数值类型，过滤异常值
            volume_series = pd.to_numeric(recent_data[volume_col], errors='coerce')
            volume_series = volume_series.dropna()
            
            if len(volume_series) > 0:
                # 过滤异常值：去除超过中位数100倍的值
                median_volume = volume_series.median()
                if median_volume > 0:
                    volume_series = volume_series[volume_series <= median_volume * 100]
                
                avg_volume = volume_series.mean()
                # 确保avg_volume不是NaN且在合理范围内
                if pd.isna(avg_volume) or avg_volume <= 0 or avg_volume > 1e12:
                    avg_volume = median_volume if median_volume > 0 else 1000000  # 默认一个大值，使之不满足
            else:
                avg_volume = 1000000  # 默认一个大值，使之不满足
        else:
            avg_volume = 1000000  # 默认一个大值，使之不满足
        
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
        
        # 开始日志
        logger.debug(f"[EventSignalService]开始生成事件信号，事件数量: {len(events)}, 信号规则数量: {len(self.signal_rules)}")
        logger.info(f"[EventSignalService]事件信号规则: {[rule.__name__ for rule in self.signal_rules]}")
        
        # 统计事件类型分布
        event_type_stats = {}
        for event in events:
            event_type = event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type)
            event_type_stats[event_type] = event_type_stats.get(event_type, 0) + 1
        logger.info(f"[EventSignalService]事件类型分布: {event_type_stats}")
        
        # 处理每个事件
        for event_idx, event in enumerate(events):
            # 应用所有事件信号规则
            for rule_idx, rule_func in enumerate(self.signal_rules):
                try:
                    signal = rule_func(event)
                    if signal:
                        rule_name = getattr(rule_func, 'chinese_name', rule_func.__name__ if hasattr(rule_func, '__name__') else f"事件规则{rule_idx}")
                        if event_idx % 100 == 0:
                            logger.debug(f"[EventSignalService]第{event_idx}个事件:{rule_name}对事件{event.event_type}生成信号: 事件类型={event.event_type}, 信号类型={signal.get('signal')}, 强度={signal.get('strength'):.3f}, 原因={signal.get('reason')}, 事件ID={signal.get('event_id')}")

                        signals.append(signal)
                    else:
                        if event_idx % 100 == 0:
                            rule_name = getattr(rule_func, 'chinese_name', rule_func.__name__ if hasattr(rule_func, '__name__') else f"事件规则{rule_idx}")
                            logger.debug(f"[EventSignalService]第{event_idx}个事件:{rule_name}对事件{event.event_type}未触发(每100的抽样)")
                except Exception as e:
                    rule_name = getattr(rule_func, 'chinese_name', rule_func.__name__ if hasattr(rule_func, '__name__') else f"事件规则{rule_idx}")
                    logger.error(f"[EventSignalService]第{event_idx}个事件:{rule_name}处理事件{event_idx}失败: {e}")
                    logger.error(f"[EventSignalService]事件详情: 类型={event.event_type}, 标题={event.title}")
        
        # 统计生成的信号类型分布
        signal_type_stats = {}
        for signal in signals:
            signal_type = signal.get('signal', 'unknown')
            signal_type_stats[signal_type] = signal_type_stats.get(signal_type, 0) + 1
        logger.info(f"[EventSignalService]信号类型分布: {signal_type_stats}")
        
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
    # 将原始信号结构转为统一信号结构
    def merge_signals(self, data_signals: List[Dict], event_signals: List[Dict]) -> List[Dict]:
        """合并数据驱动和事件驱动信号"""
        unified_signals = []
        
        # 添加数据驱动信号
        for signal in data_signals:
            # 正确映射字段
            signal_value = signal.get('signal', 0)  # 1/-1/0
            signal_type_map = {1: 'buy', -1: 'sell', 0: 'hold'}
            unified_signal = {
                'type': 'data_driven',
                'signal_type': signal_type_map.get(signal_value, 'unknown'),
                'timestamp': signal.get('timestamp'),
                'symbol': signal.get('symbol', 'UNKNOWN'),
                'direction': signal_value,  # 直接使用原始signal值
                'strength': signal.get('strength', 0.5),
                'confidence': signal.get('strength', 0.5),  # 使用strength作为confidence
                'reason': signal.get('reason', ''),  # 保留原始reason
                'source': 'technical_analysis',
                'indicators_used': signal.get('indicators_used', []),
                'metadata': signal
            }
            # 只有当timestamp存在时才添加信号
            if unified_signal['timestamp'] is not None:
                unified_signals.append(unified_signal)
        
        # 添加事件驱动信号
        for signal in event_signals:
            # 正确映射事件信号字段
            signal_value = signal.get('signal', 0)  # 1/-1/0
            signal_type_map = {1: 'buy', -1: 'sell', 0: 'hold'}
            
            unified_signal = {
                'type': 'event_driven',
                'signal_type': signal_type_map.get(signal_value, 'unknown'),
                'timestamp': signal.get('timestamp'),
                'symbol': signal.get('symbol', 'UNKNOWN'),
                'direction': signal_value,  # 使用原始signal值作为direction
                'strength': signal.get('strength', 0.5),
                'confidence': signal.get('strength', 0.5),  # 使用strength作为confidence
                'reason': signal.get('reason', ''),  # 保留原始reason
                'source': 'event_analysis',
                'event_id': signal.get('event_id'),  # 保留事件ID
                'metadata': signal
            }
            # 只有当timestamp存在时才添加信号
            if unified_signal['timestamp'] is not None:
                unified_signals.append(unified_signal)
        
        # 按时间排序
        unified_signals.sort(key=lambda x: x['timestamp'])
        
        # 信号去重和优化
        optimized_signals = self._optimize_signals(unified_signals)
        
        return optimized_signals
    
    def _optimize_signals(self, signals: List[Dict]) -> List[Dict]:
        """优化信号：去重、合并同类信号等"""
        if not signals:
            return signals
        
        # 简单的去重逻辑：相同时间窗口内的同类信号只保留强度最高的
        optimized = []
        # time_window = pd.Timedelta(minutes=30)  # 30分钟时间窗口
        time_window = pd.Timedelta(days=1)  # 1天时间窗口

        for signal in signals:
            should_add = True
            signal_time = pd.to_datetime(signal['timestamp'])
            
            for existing in optimized:
                existing_time = pd.to_datetime(existing['timestamp'])
                
                # 如果在时间窗口内且是同类信号
                if (abs(signal_time - existing_time) <= time_window and 
                    signal['signal_type'] == existing['signal_type'] and
                    signal['symbol'] == existing['symbol']):
                    
                    # 如果新信号强度更高，替换现有信号
                    if signal['strength'] > existing['strength']:
                        optimized.remove(existing)
                        break
                    else:
                        should_add = False
                        break
            
            if should_add:
                optimized.append(signal)
        
        return optimized
    
    def create_default_data_generator(self):
        """创建默认数据信号生成器"""
        # 信号规则
        self.data_generator.add_signal_rule(adaptive_ma_crossover_rule)
        self.data_generator.add_signal_rule(adaptive_rsi_rule)
        # 过滤规则
        self.data_generator.add_filter_rule(trend_strength_filter_rule)
        return self.data_generator
    
    def create_default_event_generator(self):
        """创建默认事件信号生成器"""
        self.event_generator.add_rule(news_sentiment_rule)
        self.event_generator.add_rule(keyword_trigger_rule)
        return self.event_generator