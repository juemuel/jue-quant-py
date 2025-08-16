from core.logger import logger
from data_providers import get_data_provider
from common.utils import clean_numeric_data, safe_convert_to_dict, debug_dataframe
import pandas as pd
import numpy as np
from typing import List, Dict
import datetime
from . import analytic_service
from .risk_manage_service import (
    calculate_position_size, ManagerFactory, RiskManager, PositionManager,
    calculate_volatility, calculate_max_drawdown, 
    calculate_sharpe_ratio, calculate_var, calculate_win_rate)
from .signal_service import DataSignalGenerator, EventSignalGenerator, UnifiedSignalManager
from .event_service import MarketEvent, EventType, EventSeverity 
from .signal_rules.data_signal_rules import (
    adaptive_ma_crossover_rule, 
    multi_confirmation_rsi_rule,
    trend_strength_filter_rule,
    support_resistance_breakout_rule
)
from .signal_rules.event_signal_rules import (
    news_sentiment_rule,
    earnings_anticipation_rule,
    keyword_trigger_rule,
)
# ============ 价格数据信号 ============
# 1.1.1 单信号-均线交叉信号 - 基于价格计算的移动平均线[在基础单信号生成中已验证]
def generate_ma_crossover_signal(df, short_period=5, long_period=20):
    """
    生成移动平均线交叉信号
    :param df: 价格数据
    :param short_period: 短期均线周期
    :param long_period: 长期均线周期
    :return: 包含交易信号的数据
    """
    logger.info(f"[Strategy]生成均线交叉信号，周期: {short_period}, {long_period}")
    try:
        # 计算移动平均线
        ma_result = analytic_service.calculate_moving_averages(df, [short_period, long_period])
        if ma_result['status'] != 'success':
            return ma_result
        
        result_df = pd.DataFrame(ma_result['data'])
        
        # 生成交易信号
        result_df['signal'] = 0
        result_df['position'] = 0
        
        # 金叉买入，死叉卖出
        short_ma = f'MA{short_period}'
        long_ma = f'MA{long_period}'
        
        # 当短期均线上穿长期均线时买入
        result_df.loc[(result_df[short_ma] > result_df[long_ma]) & 
                     (result_df[short_ma].shift(1) <= result_df[long_ma].shift(1)), 'signal'] = 1
        
        # 当短期均线下穿长期均线时卖出
        result_df.loc[(result_df[short_ma] < result_df[long_ma]) & 
                     (result_df[short_ma].shift(1) >= result_df[long_ma].shift(1)), 'signal'] = -1
        
        # 计算持仓状态
        result_df['position'] = result_df['signal'].replace(to_replace=0, method='ffill').fillna(0)
        
        # 清理数据
        cleaned_data = clean_numeric_data(result_df)
        data_dict = safe_convert_to_dict(cleaned_data)
        
        return {
            "status": "success",
            "data": data_dict,
            "message": "均线交叉信号生成完成"
        }
    except Exception as e:
        logger.error(f"[Strategy]生成均线交叉信号失败: {e}")
        return {"status": "error", "message": f"信号生成失败: {e}"}

# 1.1.2 单信号-RSI信号 - 基于价格计算的RSI指标[在基础单信号生成中已验证]
def generate_rsi_signal(df, period=14, oversold=30, overbought=70):
    """
    生成RSI超买超卖信号
    :param df: 价格数据
    :param period: RSI周期
    :param oversold: 超卖阈值
    :param overbought: 超买阈值
    :return: 包含交易信号的数据
    """
    logger.info(f"[Strategy]生成RSI信号，周期: {period}, 超卖: {oversold}, 超买: {overbought}")
    try:
        # 计算RSI
        rsi_result = analytic_service.calculate_rsi(df, period)
        if rsi_result['status'] != 'success':
            return rsi_result
        
        result_df = pd.DataFrame(rsi_result['data'])

        # 关键修正：确保RSI列是数值类型
        if 'RSI' in result_df.columns:
            result_df['RSI'] = pd.to_numeric(result_df['RSI'], errors='coerce')
        
        # 生成交易信号
        result_df['signal'] = 0
        result_df['position'] = 0
        
        # RSI超卖时买入
        result_df.loc[result_df['RSI'] < oversold, 'signal'] = 1
        
        # RSI超买时卖出
        result_df.loc[result_df['RSI'] > overbought, 'signal'] = -1
        
        # 计算持仓状态
        result_df['position'] = result_df['signal'].replace(to_replace=0, method='ffill').fillna(0)
        
        # 清理数据
        cleaned_data = clean_numeric_data(result_df)
        data_dict = safe_convert_to_dict(cleaned_data)
        
        return {
            "status": "success",
            "data": data_dict,
            "message": "RSI信号生成完成"
        }
    except Exception as e:
        logger.error(f"[Strategy]生成RSI信号失败: {e}")
        return {"status": "error", "message": f"信号生成失败: {e}"}

# 1.2.1 使用数据驱动信号生成器(TODO)
def generate_data_driven_signals(df, signal_rules=None, filter_rules=None):
    """
    基于规则的信号生成
    :param df: 价格数据
    :param signal_rules: 自定义信号规则列表
    :param filter_rules: 自定义过滤规则列表
    :return: 包含交易信号的数据
    """
    logger.info("[Strategy]开始基于规则的信号生成")
    
    try:
        # 计算所需的技术指标
        indicators = {}
        
        # 计算移动平均线
        ma_result = analytic_service.calculate_moving_averages(df, [3, 5, 10, 20])
        if ma_result['status'] == 'success':
            ma_df = pd.DataFrame(ma_result['data'])
            for col in ma_df.columns:
                if col.startswith('MA'):
                    indicators[col] = ma_df[col]
        
        # 计算RSI
        rsi_result = analytic_service.calculate_rsi(df, 14)
        if rsi_result['status'] == 'success':
            rsi_df = pd.DataFrame(rsi_result['data'])
            indicators['RSI'] = rsi_df['RSI']
        
        # 计算MACD
        macd_result = analytic_service.calculate_macd(df)
        if macd_result['status'] == 'success':
            macd_df = pd.DataFrame(macd_result['data'])
            indicators['MACD'] = macd_df['MACD']
        
        # 初始化信号生成器
        signal_generator = DataSignalGenerator()
        
        # 添加默认规则
        if signal_rules is None:
            signal_rules = [
                adaptive_ma_crossover_rule,
                multi_confirmation_rsi_rule,
                trend_strength_filter_rule,
                support_resistance_breakout_rule
            ]
        
        for rule in signal_rules:
            signal_generator.add_signal_rule(rule)
        
        # 添加过滤规则
        if filter_rules:
            for filter_rule in filter_rules:
                signal_generator.add_filter_rule(filter_rule)
        
        # 生成信号
        signals = signal_generator.generate_signals(df, indicators)
        
        return {
            "status": "success",
            "data": signals,
            "message": f"基于规则的信号生成完成，共生成 {len(signals)} 个信号"
        }
        
    except Exception as e:
        logger.error(f"[Strategy]基于规则的信号生成失败: {e}")
        return {"status": "error", "message": f"信号生成失败: {e}"}

# ============ 事件驱动信号 ============
# 2.1.1 单信号-新闻情感信号生成(TODO)
def generate_news_sentiment_signal(events_data: List[Dict], sentiment_threshold=0.7):
    """
    生成基于新闻情感的交易信号
    :param events_data: 事件数据列表
    :param sentiment_threshold: 情感阈值
    :return: 新闻情感信号
    """
    logger.info(f"[Strategy]生成新闻情感信号，情感阈值: {sentiment_threshold}")
    
    try:
        from .event_service import MarketEvent, EventType, EventSeverity
        
        signal_generator = EventSignalGenerator()
        signal_generator.add_rule(news_sentiment_rule)
        
        # 过滤新闻事件
        news_events = []
        for event_data in events_data:
            # 处理MarketEvent对象或字典
            if isinstance(event_data, MarketEvent):
                if event_data.event_type == EventType.NEWS:
                    news_events.append(event_data)
            elif isinstance(event_data, dict):
                if event_data.get('event_type') == EventType.NEWS.value:
                    try:
                        event = MarketEvent(**event_data)
                        news_events.append(event)
                    except Exception as e:
                        logger.warning(f"[Strategy]跳过无效新闻事件: {e}")
                        continue
        
        signals = signal_generator.generate_signals(news_events)
        
        # 根据阈值过滤信号
        filtered_signals = [
            signal for signal in signals 
            if abs(signal.get('strength', 0)) >= sentiment_threshold
        ]
        
        return {
            "status": "success",
            "data": {
                "signals": filtered_signals,
                "news_events_processed": len(news_events),
                "signals_generated": len(filtered_signals),
                "sentiment_threshold": sentiment_threshold
            },
            "message": f"成功生成 {len(filtered_signals)} 个新闻情感信号"
        }
        
    except Exception as e:
        logger.error(f"[Strategy]新闻情感信号生成失败: {e}")
        return {"status": "error", "message": f"信号生成失败: {e}"}

# 2.1.2 单信号-财报事件信号生成(TODO)
def generate_earnings_signal(events_data: List[Dict], anticipation_days=3):
    """
    生成基于财报事件的交易信号
    :param events_data: 事件数据列表（可以是字典或MarketEvent对象）
    :param anticipation_days: 财报预期天数
    :return: 财报事件信号
    """
    logger.info(f"[Strategy]生成财报事件信号，预期天数: {anticipation_days}")
    
    try:
        from .event_service import MarketEvent, EventType
        
        signal_generator = EventSignalGenerator()
        signal_generator.add_rule(earnings_anticipation_rule)
        
        # 过滤财报事件
        earnings_events = []
        for event_data in events_data:
            # 处理MarketEvent对象或字典
            if isinstance(event_data, MarketEvent):
                # 同时支持EARNINGS和FINANCIAL_REPORT类型
                if event_data.event_type in [EventType.EARNINGS, EventType.FINANCIAL_REPORT]:
                    earnings_events.append(event_data)
            elif isinstance(event_data, dict):
                event_type_value = event_data.get('event_type')
                if (event_type_value == EventType.FINANCIAL_REPORT.value or 
                    event_type_value == EventType.EARNINGS.value):
                    try:
                        event = MarketEvent(**event_data)
                        earnings_events.append(event)
                    except Exception as e:
                        logger.warning(f"[Strategy]跳过无效财报事件: {e}")
                        continue
        
        signals = signal_generator.generate_signals(earnings_events)
        
        return {
            "status": "success",
            "data": {
                "signals": signals,
                "earnings_events_processed": len(earnings_events),
                "signals_generated": len(signals),
                "anticipation_days": anticipation_days
            },
            "message": f"成功生成 {len(signals)} 个财报事件信号"
        }
        
    except Exception as e:
        logger.error(f"[Strategy]财报事件信号生成失败: {e}")
        return {"status": "error", "message": f"信号生成失败: {e}"}

# 2.1.3 单信号-关键词触发信号生成(TODO)
def generate_keyword_trigger_signal(events_data: List[Dict], keywords=None, trigger_strength=0.6):
    """
    生成基于关键词触发的交易信号
    :param events_data: 事件数据列表
    :param keywords: 关键词列表
    :param trigger_strength: 触发强度阈值
    :return: 关键词触发信号
    """
    logger.info(f"[Strategy]生成关键词触发信号，触发强度: {trigger_strength}")
    
    try:
        from .event_service import MarketEvent
        
        signal_generator = EventSignalGenerator()
        signal_generator.add_rule(keyword_trigger_rule)
        
        # 转换所有事件
        market_events = []
        for event_data in events_data:
            try:
                event = MarketEvent(**event_data)
                market_events.append(event)
            except Exception as e:
                logger.warning(f"[Strategy]跳过无效事件: {e}")
                continue
        
        signals = signal_generator.generate_signals(market_events)
        
        # 根据触发强度过滤信号
        filtered_signals = [
            signal for signal in signals 
            if signal.get('strength', 0) >= trigger_strength
        ]
        
        return {
            "status": "success",
            "data": {
                "signals": filtered_signals,
                "events_processed": len(market_events),
                "signals_generated": len(filtered_signals),
                "trigger_strength": trigger_strength,
                "keywords_used": keywords or "默认关键词"
            },
            "message": f"成功生成 {len(filtered_signals)} 个关键词触发信号"
        }
        
    except Exception as e:
        logger.error(f"[Strategy]关键词触发信号生成失败: {e}")
        return {"status": "error", "message": f"信号生成失败: {e}"}

# 2.1.4 单信号-市场异动事件信号生成(TODO)
def generate_market_anomaly_signal(events_data: List[Dict], anomaly_threshold=2.0):
    """
    生成基于市场异动事件的交易信号
    :param events_data: 事件数据列表
    :param anomaly_threshold: 异动阈值（标准差倍数）
    :return: 市场异动信号
    """
    logger.info(f"[Strategy]生成市场异动信号，异动阈值: {anomaly_threshold}")
    
    try:
        from .event_service import MarketEvent, EventType
        
        signal_generator = EventSignalGenerator()
        
        # 定义市场异动规则
        def market_anomaly_rule(event: MarketEvent):
            if event.event_type != EventType.MARKET_DATA:
                return None
            
            # 检查是否为异动事件（这里简化处理）
            if hasattr(event, 'volatility') and event.volatility > anomaly_threshold:
                return {
                    'symbol': event.symbol,
                    'signal': -0.5 if event.volatility > anomaly_threshold * 1.5 else 0.3,
                    'strength': min(event.volatility / anomaly_threshold, 1.0),
                    'reason': f'市场异动检测: 波动率 {event.volatility:.2f}',
                    'timestamp': event.timestamp,
                    'event_id': event.event_id
                }
            return None
        
        signal_generator.add_rule(market_anomaly_rule)
        
        # 过滤市场数据事件
        market_events = []
        for event_data in events_data:
            if event_data.get('event_type') == EventType.MARKET_DATA.value:
                try:
                    event = MarketEvent(**event_data)
                    market_events.append(event)
                except Exception as e:
                    logger.warning(f"[Strategy]跳过无效市场事件: {e}")
                    continue
        
        signals = signal_generator.generate_signals(market_events)
        
        return {
            "status": "success",
            "data": {
                "signals": signals,
                "market_events_processed": len(market_events),
                "signals_generated": len(signals),
                "anomaly_threshold": anomaly_threshold
            },
            "message": f"成功生成 {len(signals)} 个市场异动信号"
        }
        
    except Exception as e:
        logger.error(f"[Strategy]市场异动信号生成失败: {e}")
        return {"status": "error", "message": f"信号生成失败: {e}"}

# 2.2.1 综合信号-事件权重信号生成（TODO）
def generate_composite_event_signal(events_data: List[Dict], signal_weights=None):
    """
    生成综合事件信号（结合多种事件类型）
    :param events_data: 事件数据列表
    :param signal_weights: 各类型信号权重
    :return: 综合事件信号
    """
    logger.info(f"[Strategy]生成综合事件信号")
    
    try:
        # 默认权重配置
        if signal_weights is None:
            signal_weights = {
                'news_sentiment': 0.4,
                'earnings': 0.3,
                'keyword_trigger': 0.2,
                'market_anomaly': 0.1
            }
        
        # 生成各类型信号
        news_result = generate_news_sentiment_signal(events_data)
        earnings_result = generate_earnings_signal(events_data)
        keyword_result = generate_keyword_trigger_signal(events_data)
        anomaly_result = generate_market_anomaly_signal(events_data)
        
        # 合并信号
        composite_signals = []
        
        # 收集所有信号
        all_signals = []
        if news_result['status'] == 'success':
            for signal in news_result['data']['signals']:
                signal['type'] = 'news_sentiment'
                signal['weight'] = signal_weights['news_sentiment']
                all_signals.append(signal)
        
        if earnings_result['status'] == 'success':
            for signal in earnings_result['data']['signals']:
                signal['type'] = 'earnings'
                signal['weight'] = signal_weights['earnings']
                all_signals.append(signal)
        
        if keyword_result['status'] == 'success':
            for signal in keyword_result['data']['signals']:
                signal['type'] = 'keyword_trigger'
                signal['weight'] = signal_weights['keyword_trigger']
                all_signals.append(signal)
        
        if anomaly_result['status'] == 'success':
            for signal in anomaly_result['data']['signals']:
                signal['type'] = 'market_anomaly'
                signal['weight'] = signal_weights['market_anomaly']
                all_signals.append(signal)
        
        # 按股票代码和时间聚合信号
        from collections import defaultdict
        signal_groups = defaultdict(list)
        
        for signal in all_signals:
            key = (signal['symbol'], signal['timestamp'])
            signal_groups[key].append(signal)
        
        # 计算加权综合信号
        for (symbol, timestamp), signals in signal_groups.items():
            weighted_signal = sum(s['signal'] * s['weight'] * s['strength'] for s in signals)
            weighted_strength = sum(s['strength'] * s['weight'] for s in signals)
            
            composite_signals.append({
                'symbol': symbol,
                'signal': weighted_signal,
                'strength': weighted_strength,
                'timestamp': timestamp,
                'reason': f"综合信号 ({len(signals)}个事件)",
                'component_signals': signals,
                'signal_count': len(signals)
            })
        
        return {
            "status": "success",
            "data": {
                "signals": composite_signals,
                "component_results": {
                    "news_sentiment": news_result,
                    "earnings": earnings_result,
                    "keyword_trigger": keyword_result,
                    "market_anomaly": anomaly_result
                },
                "signal_weights": signal_weights,
                "total_signals": len(composite_signals)
            },
            "message": f"成功生成 {len(composite_signals)} 个综合事件信号"
        }
        
    except Exception as e:
        logger.error(f"[Strategy]综合事件信号生成失败: {e}")
        return {"status": "error", "message": f"信号生成失败: {e}"}

# 2.3.1 生成器-使用事件驱动信号生成器(TODO)
def generate_event_driven_signals(events_data: List[Dict], signal_rules=None):
    """
    生成事件驱动信号
    :param events_data: 事件数据列表
    :param signal_rules: 信号生成规则列表
    :return: 生成的信号列表
    """
    logger.info(f"[Strategy]开始生成事件驱动信号，事件数量: {len(events_data)}")
    
    try:
        from .event_service import MarketEvent
        
        # 初始化信号生成器
        signal_generator = EventSignalGenerator()
        
        # 添加默认规则
        if signal_rules is None:
            signal_rules = [news_sentiment_rule, keyword_trigger_rule, earnings_anticipation_rule]
        
        for rule in signal_rules:
            signal_generator.add_rule(rule)
        
        # 转换事件数据为MarketEvent对象
        market_events = []
        for event_data in events_data:
            try:
                event = MarketEvent(**event_data)
                market_events.append(event)
            except Exception as e:
                logger.warning(f"[Strategy]跳过无效事件数据: {e}")
                continue
        
        # 生成信号
        signals = signal_generator.generate_signals(market_events)
        
        return {
            "status": "success",
            "data": {
                "signals": signals,
                "events_processed": len(market_events),
                "signals_generated": len(signals),
                "rules_applied": len(signal_rules)
            },
            "message": f"成功生成 {len(signals)} 个事件驱动信号"
        }
        
    except Exception as e:
        logger.error(f"[Strategy]事件驱动信号生成失败: {e}")
        return {"status": "error", "message": f"信号生成失败: {e}"}

# ============ 多驱动信号 ============
# 3.1 统一驱动信号-生成器(既支持数据信号也支持事件信号)
def generate_unified_signals(price_data: pd.DataFrame, events_data: List[Dict] = None, 
                           data_signal_config=None, event_signal_config=None):
    """
    统一信号生成管理器
    :param price_data: 价格数据
    :param events_data: 事件数据
    :param data_signal_config: 数据驱动信号配置
    :param event_signal_config: 事件驱动信号配置
    :return: 统一的信号结果
    """
    logger.info("[Strategy]开始统一信号生成")
    
    try:
        unified_manager = UnifiedSignalManager()
        
        # 配置数据驱动信号
        if data_signal_config is None:
            data_signal_config = {
                'ma_crossover': {'short_period': 5, 'long_period': 20},
                'rsi': {'period': 14, 'oversold': 30, 'overbought': 70},
                'rule_based': {'enable': True}
            }
        
        # 配置事件驱动信号
        if event_signal_config is None:
            event_signal_config = {
                'news_sentiment': {'threshold': 0.7},
                'earnings': {'anticipation_days': 3},
                'keyword_trigger': {'strength': 0.6}
            }
        
        # 生成数据驱动信号
        data_signals = []
        if data_signal_config.get('rule_based', {}).get('enable', True):
            # 使用DataSignalGenerator生成规则驱动的信号
            data_generator = DataSignalGenerator()
            # 添加信号规则
            data_generator.add_signal_rule(adaptive_ma_crossover_rule)
            data_generator.add_signal_rule(multi_confirmation_rsi_rule)
            # 计算技术指标
            indicators = {}
            if data_signal_config.get('ma_crossover', {}).get('enable', True):
                ma_result = analytic_service.calculate_moving_averages(
                    price_data, 
                    [3, 5, 10, 20]  # 包含所有可能的周期
                )
                # ma_result = analytic_service.calculate_moving_averages(
                #     price_data, 
                #     [data_signal_config['ma_crossover']['short_period'], 
                #     data_signal_config['ma_crossover']['long_period']]
                # )
                if ma_result['status'] == 'success':
                    ma_df = pd.DataFrame(ma_result['data'])
                    for col in ma_df.columns:
                        if col.startswith('MA'):
                            indicators[col] = ma_df[col]
            if data_signal_config.get('rsi', {}).get('enable', True):
                rsi_result = analytic_service.calculate_rsi(
                    price_data, 
                    data_signal_config['rsi']['period']
                )
                if rsi_result['status'] == 'success':
                    rsi_df = pd.DataFrame(rsi_result['data'])
                    logger.info(f"[Strategy]RSI DataFrame列: {rsi_df.columns.tolist()}")
                    logger.info(f"[Strategy]RSI列数据类型: {rsi_df['RSI'].dtype if 'RSI' in rsi_df.columns else 'RSI列不存在'}")
                    
                    # 确保RSI列是数值类型
                    if 'RSI' in rsi_df.columns:
                        rsi_df['RSI'] = pd.to_numeric(rsi_df['RSI'], errors='coerce')
                        logger.info(f"[Strategy]RSI转换后数据类型: {rsi_df['RSI'].dtype}")
                        indicators['RSI'] = rsi_df['RSI']
                        logger.info(f"[Strategy]indicators['RSI']数据类型: {indicators['RSI'].dtype}")
                    else:
                        logger.error(f"[Strategy]RSI列不存在于DataFrame中")
            # 生成信号
            data_signals = data_generator.generate_signals(price_data, indicators)
            logger.info(f"[Strategy]原生数据驱动信号生成完成，信号数量: {len(data_signals)}")
        
        # 生成事件驱动信号
        event_signals = []
        if events_data:
            # 使用EventSignalGenerator统一生成所有事件信号
            event_generator = EventSignalGenerator()
            # 根据配置添加相应的规则
            if event_signal_config.get('news_sentiment', {}).get('enable', True):
                event_generator.add_rule(news_sentiment_rule)
            
            if event_signal_config.get('earnings', {}).get('enable', True):
                event_generator.add_rule(earnings_anticipation_rule)
            
            if event_signal_config.get('keyword_trigger', {}).get('enable', True):
                event_generator.add_rule(keyword_trigger_rule)
            # 转换事件数据为MarketEvent对象
            market_events = []
            for event_data in events_data:
                try:
                    if isinstance(event_data, MarketEvent):
                        market_events.append(event_data)
                    elif isinstance(event_data, dict):
                        event = MarketEvent(**event_data)
                        market_events.append(event)
                except Exception as e:
                    logger.warning(f"[Strategy]跳过无效事件数据: {e}")
                    continue
            # 生成信号
            event_signals = event_generator.generate_signals(market_events)
            logger.info(f"[Strategy]原生事件驱动信号生成完成，信号数量: {len(event_signals)}")

        # 合并和优化信号
        unified_signals = unified_manager.merge_signals(data_signals, event_signals)
        
        return {
            "status": "success",
            "data": {
                "unified_signals": unified_signals,
                "data_signals_count": len(data_signals),
                "event_signals_count": len(event_signals),
                "total_signals": len(unified_signals),
                "config": {
                    "data_signal_config": data_signal_config,
                    "event_signal_config": event_signal_config
                }
            },
            "message": f"统一信号生成完成，共生成 {len(unified_signals)} 个信号"
        }
        
    except Exception as e:
        logger.error(f"[Strategy]统一信号生成失败: {e}")
        return {"status": "error", "message": f"统一信号生成失败: {e}"}



# 简单回测功能（信号驱动+全仓交易）(TODO)
def simple_backtest(df, signals, initial_capital=100000, commission=0.001):
    """
    简单回测功能
    :param df: 价格数据
    :param signals: 交易信号数据
    :param initial_capital: 初始资金
    :param commission: 手续费率
    :return: 回测结果
    """
    logger.info(f"[Strategy]开始回测，初始资金: {initial_capital}")
    try:
        portfolio_value = initial_capital
        positions = 0
        trades = []
        portfolio_values = []
        
        signals_df = pd.DataFrame(signals) if isinstance(signals, list) else signals
        
        # 确定价格列名
        price_col = 'close' if 'close' in signals_df.columns else '收盘'
        if price_col not in signals_df.columns:
            return {"status": "error", "message": "未找到价格数据"}
        
        for i, row in signals_df.iterrows():
            current_price = row[price_col]
            signal = row.get('signal', 0)
            
            if signal == 1 and positions == 0:  # 买入信号
                shares = int(portfolio_value // (current_price * (1 + commission)))
                if shares > 0:
                    cost = shares * current_price * (1 + commission)
                    portfolio_value -= cost
                    positions = shares
                    trades.append({
                        'date': row.get('date', i),
                        'action': 'buy',
                        'price': current_price,
                        'shares': shares,
                        'value': cost
                    })
            
            elif signal == -1 and positions > 0:  # 卖出信号
                proceeds = positions * current_price * (1 - commission)
                portfolio_value += proceeds
                trades.append({
                    'date': row.get('date', i),
                    'action': 'sell',
                    'price': current_price,
                    'shares': positions,
                    'value': proceeds
                })
                positions = 0
            
            # 计算当前组合价值
            current_portfolio_value = portfolio_value + positions * current_price
            portfolio_values.append(current_portfolio_value)
        
        # 计算最终价值
        if positions > 0:
            final_price = signals_df.iloc[-1][price_col]
            portfolio_value += positions * final_price
        
        # 计算收益率
        total_return = (portfolio_value - initial_capital) / initial_capital
        
        return {
            "status": "success",
            "data": {
                "initial_capital": initial_capital,
                "final_value": portfolio_value,
                "total_return": total_return,
                "total_return_pct": total_return * 100,
                "trades_count": len(trades),
                "trades": trades,
                "portfolio_values": portfolio_values
            },
            "message": "回测完成"
        }
    except Exception as e:
        logger.error(f"[Strategy]回测失败: {e}")
        return {"status": "error", "message": f"回测失败: {e}"}
# 增强回测功能（信号驱动 + 风险分析）(TODO)
def enhanced_backtest(df, signals, initial_capital=100000, commission=0.001, risk_free_rate=0.03):
    """
    增强版回测功能，集成风险管理指标
    :param df: 价格数据
    :param signals: 交易信号数据
    :param initial_capital: 初始资金
    :param commission: 手续费率
    :param risk_free_rate: 无风险利率
    :return: 包含风险指标的回测结果
    """
    logger.info(f"[Strategy]开始增强版回测，初始资金: {initial_capital}")
    try:
        portfolio_value = initial_capital
        positions = 0
        trades = []
        portfolio_values = []
        
        signals_df = pd.DataFrame(signals) if isinstance(signals, list) else signals
        
        # 确定价格列名
        price_col = 'close' if 'close' in signals_df.columns else '收盘'
        if price_col not in signals_df.columns:
            return {"status": "error", "message": "未找到价格数据"}
        
        for i, row in signals_df.iterrows():
            current_price = row[price_col]
            signal = row.get('signal', 0)
            
            if signal == 1 and positions == 0:  # 买入信号
                shares = int(portfolio_value // (current_price * (1 + commission)))
                if shares > 0:
                    cost = shares * current_price * (1 + commission)
                    portfolio_value -= cost
                    positions = shares
                    trades.append({
                        'date': row.get('date', i),
                        'action': 'buy',
                        'price': current_price,
                        'shares': shares,
                        'value': cost
                    })
            
            elif signal == -1 and positions > 0:  # 卖出信号
                proceeds = positions * current_price * (1 - commission)
                portfolio_value += proceeds
                trades.append({
                    'date': row.get('date', i),
                    'action': 'sell',
                    'price': current_price,
                    'shares': positions,
                    'value': proceeds
                })
                positions = 0
            
            # 计算当前组合价值
            current_portfolio_value = portfolio_value + positions * current_price
            portfolio_values.append(current_portfolio_value)
        
        # 计算最终价值
        if positions > 0:
            final_price = signals_df.iloc[-1][price_col]
            portfolio_value += positions * final_price
        
        # 计算总收益率（这个变量在原代码中缺失）
        total_return = (portfolio_value - initial_capital) / initial_capital
        
        # 确保数据类型一致
        portfolio_values = [float(v) for v in portfolio_values]
        
        # 计算收益率序列
        if len(portfolio_values) < 2:
            return {"status": "error", "message": "数据不足，无法进行回测分析"}
        
        portfolio_series = pd.Series(portfolio_values)
        returns = portfolio_series.pct_change().dropna()
        
        # 集成风险管理指标（带错误处理）
        risk_metrics = {}
        
        if len(returns) >= 2:
            try:
                # 1. 波动率分析
                volatility_result = calculate_volatility(returns)
                if volatility_result["status"] == "success":
                    risk_metrics["volatility"] = volatility_result["data"]
                else:
                    risk_metrics["volatility"] = {"error": volatility_result["message"]}
            except Exception as e:
                risk_metrics["volatility"] = {"error": f"波动率计算失败: {e}"}
            
            try:
                # 2. 最大回撤分析
                drawdown_result = calculate_max_drawdown(portfolio_values)
                if drawdown_result["status"] == "success":
                    risk_metrics["drawdown"] = drawdown_result["data"]
                else:
                    risk_metrics["drawdown"] = {"error": drawdown_result["message"]}
            except Exception as e:
                risk_metrics["drawdown"] = {"error": f"最大回撤计算失败: {e}"}
            
            try:
                # 3. 夏普比率
                sharpe_result = calculate_sharpe_ratio(returns, risk_free_rate)
                if sharpe_result["status"] == "success":
                    risk_metrics["sharpe"] = sharpe_result["data"]
                else:
                    risk_metrics["sharpe"] = {"error": sharpe_result["message"]}
            except Exception as e:
                risk_metrics["sharpe"] = {"error": f"夏普比率计算失败: {e}"}
            
            try:
                # 4. VaR分析
                var_result = calculate_var(returns)
                if var_result["status"] == "success":
                    risk_metrics["var"] = var_result["data"]
                else:
                    risk_metrics["var"] = {"error": var_result["message"]}
            except Exception as e:
                risk_metrics["var"] = {"error": f"VaR计算失败: {e}"}
        else:
            risk_metrics["error"] = "收益率数据不足"
        
        # 计算胜率
        win_rate = calculate_win_rate(trades)
        
        # 计算其他统计指标
        total_trades = len([t for t in trades if t.get('action') == 'sell'])
        avg_return_per_trade = total_return / total_trades if total_trades > 0 else 0
        
        return {
            "status": "success",
            "data": {
                # 基础回测结果
                "initial_capital": initial_capital,
                "final_value": portfolio_value,
                "total_return": total_return,
                "total_return_pct": total_return * 100,
                "trades_count": len(trades),
                "completed_trades": total_trades,
                "trades": trades,
                "portfolio_values": portfolio_values,
                
                # 交易统计
                "win_rate": win_rate,
                "win_rate_pct": win_rate * 100,
                "avg_return_per_trade": avg_return_per_trade,
                "avg_return_per_trade_pct": avg_return_per_trade * 100,
                
                # 风险管理指标
                "risk_metrics": risk_metrics,
                
                # 综合评估
                "risk_adjusted_return": risk_metrics.get("sharpe", {}).get("sharpe_ratio", 0),
                "risk_level": "高" if risk_metrics.get("volatility", {}).get("annualized_volatility", 0) > 0.3 else 
                             "中" if risk_metrics.get("volatility", {}).get("annualized_volatility", 0) > 0.15 else "低",
                
                # 回测参数
                "backtest_params": {
                    "commission": commission,
                    "risk_free_rate": risk_free_rate,
                    "data_points": len(portfolio_values)
                }
            },
            "message": "增强版回测完成"
        }
    except Exception as e:
        logger.error(f"[Strategy]增强版回测失败: {e}")
        return {"status": "error", "message": f"回测失败: {e}"}

# 增强回测功能（信号驱动+仓位控制；风险驱动）(TODO)
def enhanced_backtest_with_position_management(
    df, signals, initial_capital=100000, commission=0.001, 
    risk_free_rate=0.03, risk_per_trade=0.02, stop_loss_pct=0.05
):
    """
    增强版回测功能，集成仓位管理
    :param df: 价格数据
    :param signals: 交易信号数据
    :param initial_capital: 初始资金
    :param commission: 手续费率
    :param risk_free_rate: 无风险利率
    :param risk_per_trade: 单笔交易风险比例（默认2%）
    :param stop_loss_pct: 止损百分比（默认5%）
    :return: 包含仓位管理的回测结果
    """
    logger.info(f"[Strategy]开始仓位管理回测，初始资金: {initial_capital}，单笔风险: {risk_per_trade*100}%")
    try:
        portfolio_value = initial_capital
        positions = 0
        trades = []
        portfolio_values = []
        position_records = []  # 记录仓位管理信息
        
        signals_df = pd.DataFrame(signals) if isinstance(signals, list) else signals
        
        # 确定价格列名
        price_col = 'close' if 'close' in signals_df.columns else '收盘'
        if price_col not in signals_df.columns:
            return {"status": "error", "message": "未找到价格数据"}
        
        for i, row in signals_df.iterrows():
            current_price = row[price_col]
            signal = row.get('signal', 0)
            
            if signal == 1 and positions == 0:  # 买入信号
                # 计算止损价格
                stop_loss_price = current_price * (1 - stop_loss_pct)
                
                # 使用仓位管理计算买入数量
                position_result = calculate_position_size(
                    capital=portfolio_value,
                    risk_per_trade=risk_per_trade,
                    entry_price=current_price,
                    stop_loss=stop_loss_price
                )
                
                if position_result["status"] == "success":
                    position_data = position_result["data"]
                    suggested_shares = position_data["position_size"]
                    
                    # 确保不超过可用资金
                    max_affordable_shares = int(portfolio_value // (current_price * (1 + commission)))
                    shares = min(suggested_shares, max_affordable_shares)
                    
                    if shares > 0:
                        cost = shares * current_price * (1 + commission)
                        portfolio_value -= cost
                        positions = shares
                        
                        trade_record = {
                            'date': row.get('date', i),
                            'action': 'buy',
                            'price': current_price,
                            'shares': shares,
                            'value': cost,
                            'stop_loss': stop_loss_price
                        }
                        trades.append(trade_record)
                        
                        # 记录仓位管理信息
                        position_records.append({
                            'date': row.get('date', i),
                            'suggested_position': suggested_shares,
                            'actual_position': shares,
                            'position_value': cost,
                            'position_ratio': position_data["position_ratio"],
                            'risk_amount': position_data["risk_amount"],
                            'stop_loss_price': stop_loss_price
                        })
                else:
                    logger.warning(f"[Strategy]仓位计算失败: {position_result['message']}")
            
            elif signal == -1 and positions > 0:  # 卖出信号
                proceeds = positions * current_price * (1 - commission)
                portfolio_value += proceeds
                
                # 计算这笔交易的盈亏
                last_buy = next((t for t in reversed(trades) if t['action'] == 'buy'), None)
                profit_loss = 0
                if last_buy:
                    profit_loss = proceeds - last_buy['value']
                
                trades.append({
                    'date': row.get('date', i),
                    'action': 'sell',
                    'price': current_price,
                    'shares': positions,
                    'value': proceeds,
                    'profit_loss': profit_loss
                })
                positions = 0
            
            # 检查止损（如果有持仓）
            elif positions > 0:
                last_buy = next((t for t in reversed(trades) if t['action'] == 'buy'), None)
                if last_buy and current_price <= last_buy.get('stop_loss', 0):
                    # 触发止损
                    proceeds = positions * current_price * (1 - commission)
                    portfolio_value += proceeds
                    
                    profit_loss = proceeds - last_buy['value']
                    
                    trades.append({
                        'date': row.get('date', i),
                        'action': 'stop_loss',
                        'price': current_price,
                        'shares': positions,
                        'value': proceeds,
                        'profit_loss': profit_loss
                    })
                    positions = 0
            
            # 计算当前组合价值
            current_portfolio_value = portfolio_value + positions * current_price
            portfolio_values.append(current_portfolio_value)
        
        # 计算最终价值
        if positions > 0:
            final_price = signals_df.iloc[-1][price_col]
            portfolio_value += positions * final_price
        
        # 计算总收益率
        total_return = (portfolio_value - initial_capital) / initial_capital
        
        # 确保数据类型一致
        portfolio_values = [float(v) for v in portfolio_values]
        
        # 计算收益率序列
        if len(portfolio_values) < 2:
            return {"status": "error", "message": "数据不足，无法进行回测分析"}
        
        portfolio_series = pd.Series(portfolio_values)
        returns = portfolio_series.pct_change().dropna()
        
        # 集成风险管理指标
        risk_metrics = {}
        if len(returns) >= 2:
            try:
                risk_metrics["volatility"] = calculate_volatility(returns)["data"]
                risk_metrics["drawdown"] = calculate_max_drawdown(portfolio_values)["data"]
                risk_metrics["sharpe"] = calculate_sharpe_ratio(returns, risk_free_rate)["data"]
                risk_metrics["var"] = calculate_var(returns)["data"]
            except Exception as e:
                risk_metrics["error"] = f"风险指标计算失败: {e}"
        
        # 计算胜率和其他统计
        win_rate = calculate_win_rate(trades)
        stop_loss_count = len([t for t in trades if t.get('action') == 'stop_loss'])
        total_trades = len([t for t in trades if t.get('action') in ['sell', 'stop_loss']])
        
        # 计算仓位管理统计
        avg_position_ratio = np.mean([p['position_ratio'] for p in position_records]) if position_records else 0
        max_position_ratio = max([p['position_ratio'] for p in position_records]) if position_records else 0
        
        return {
            "status": "success",
            "data": {
                # 基础回测结果
                "initial_capital": initial_capital,
                "final_value": portfolio_value,
                "total_return": total_return,
                "total_return_pct": total_return * 100,
                "trades_count": len(trades),
                "completed_trades": total_trades,
                "trades": trades,
                "portfolio_values": portfolio_values,
                
                # 仓位管理统计
                "position_management": {
                    "risk_per_trade": risk_per_trade,
                    "stop_loss_pct": stop_loss_pct,
                    "avg_position_ratio": avg_position_ratio,
                    "max_position_ratio": max_position_ratio,
                    "stop_loss_triggered": stop_loss_count,
                    "stop_loss_rate": stop_loss_count / total_trades if total_trades > 0 else 0,
                    "position_records": position_records
                },
                
                # 交易统计
                "win_rate": win_rate,
                "win_rate_pct": win_rate * 100,
                
                # 风险管理指标
                "risk_metrics": risk_metrics,
                
                # 综合评估
                "risk_adjusted_return": risk_metrics.get("sharpe", {}).get("sharpe_ratio", 0),
                "risk_level": "高" if risk_metrics.get("volatility", {}).get("annualized_volatility", 0) > 0.3 else 
                             "中" if risk_metrics.get("volatility", {}).get("annualized_volatility", 0) > 0.15 else "低"
            },
            "message": "仓位管理回测完成"
        }
    except Exception as e:
        logger.error(f"[Strategy]仓位管理回测失败: {e}")
        return {"status": "error", "message": f"回测失败: {e}"}

# 可插拔的增强回测功能（信号驱动+可配置仓位+风险管理器）
def pluggable_backtest(
    df, signals, initial_capital=100000, commission=0.001, 
    risk_free_rate=0.03, risk_manager_config=None, position_manager_config=None
):
    """
    可插拔的增强回测功能
    :param df: 价格数据
    :param signals: 交易信号数据
    :param initial_capital: 初始资金
    :param commission: 手续费率
    :param risk_free_rate: 无风险利率
    :param risk_manager_config: 风控管理器配置 {'type': 'basic', 'params': {...}}
    :param position_manager_config: 仓位管理器配置 {'type': 'fixed_ratio', 'params': {...}}
    :return: 回测结果
    """
    logger.info(f"[Strategy]开始可插拔回测，初始资金: {initial_capital}")
    
    try:
        # 创建管理器实例
        risk_manager = None
        position_manager = None
        
        if risk_manager_config:
            risk_manager = ManagerFactory.create_risk_manager(
                risk_manager_config['type'], 
                **risk_manager_config.get('params', {})
            )
        
        if position_manager_config:
            position_manager = ManagerFactory.create_position_manager(
                position_manager_config['type'],
                **position_manager_config.get('params', {})
            )
        
        # 初始化回测变量
        portfolio_value = initial_capital
        positions = 0
        trades = []
        portfolio_values = []
        risk_events = []  # 记录风控事件
        position_adjustments = []  # 记录仓位调整
        
        signals_df = pd.DataFrame(signals) if isinstance(signals, list) else signals
        price_col = 'close' if 'close' in signals_df.columns else '收盘'
        
        if price_col not in signals_df.columns:
            return {"status": "error", "message": "未找到价格数据"}
        
        # 计算市场波动率（用于动态仓位管理）
        prices = signals_df[price_col].values
        returns = pd.Series(prices).pct_change().dropna()
        market_volatility = returns.std() * np.sqrt(252) if len(returns) > 1 else 0.2
        
        entry_price = None
        stop_loss_price = None
        
        for i, row in signals_df.iterrows():
            current_price = row[price_col]
            signal = row.get('signal', 0)
            current_date = row.get('date', i)
            
            # 计算当前回撤
            peak_value = max(portfolio_values) if portfolio_values else initial_capital
            current_value = portfolio_value + positions * current_price
            current_drawdown = (peak_value - current_value) / peak_value if peak_value > 0 else 0
            
            # 买入信号处理
            if signal == 1 and positions == 0:
                # 风控检查
                risk_context = {
                    'portfolio_value': portfolio_value,
                    'current_drawdown': current_drawdown,
                    'market_volatility': market_volatility
                }
                
                risk_decision = {"status": "approve"}
                if risk_manager:
                    risk_decision = risk_manager.should_enter_position(risk_context)
                
                if risk_decision["status"] == "approve":
                    # 计算止损价格
                    if risk_manager:
                        stop_loss_price = risk_manager.get_stop_loss_price(current_price, risk_context)
                    else:
                        stop_loss_price = current_price * 0.95  # 默认5%止损
                    
                    # 计算仓位大小
                    position_context = {
                        'capital': portfolio_value,
                        'entry_price': current_price,
                        'stop_loss_price': stop_loss_price,
                        'commission': commission,
                        'market_volatility': market_volatility
                    }
                    
                    if position_manager:
                        position_result = position_manager.calculate_position_size(position_context)
                    else:
                        # 默认仓位计算
                        position_result = calculate_position_size(
                            capital=portfolio_value,
                            risk_per_trade=0.02,
                            entry_price=current_price,
                            stop_loss=stop_loss_price
                        )
                    
                    if position_result["status"] == "success":
                        position_data = position_result["data"]
                        suggested_shares = position_data["position_size"]
                        
                        # 确保不超过可用资金
                        max_affordable_shares = int(portfolio_value // (current_price * (1 + commission)))
                        shares = min(suggested_shares, max_affordable_shares)
                        
                        if shares > 0:
                            cost = shares * current_price * (1 + commission)
                            portfolio_value -= cost
                            positions = shares
                            entry_price = current_price
                            
                            trades.append({
                                'date': current_date,
                                'action': 'buy',
                                'price': current_price,
                                'shares': shares,
                                'value': cost,
                                'stop_loss': stop_loss_price
                            })
                else:
                    # 记录风控拒绝事件
                    risk_events.append({
                        'date': current_date,
                        'event': 'entry_rejected',
                        'reason': risk_decision.get('reason', '未知原因'),
                        'price': current_price
                    })
            
            # 卖出信号处理
            elif signal == -1 and positions > 0:
                proceeds = positions * current_price * (1 - commission)
                portfolio_value += proceeds
                
                profit_loss = proceeds - (entry_price * positions * (1 + commission)) if entry_price else 0
                
                trades.append({
                    'date': current_date,
                    'action': 'sell',
                    'price': current_price,
                    'shares': positions,
                    'value': proceeds,
                    'profit_loss': profit_loss
                })
                
                positions = 0
                entry_price = None
                stop_loss_price = None
            
            # 持仓期间的风控检查
            elif positions > 0:
                risk_context = {
                    'current_price': current_price,
                    'entry_price': entry_price,
                    'stop_loss_price': stop_loss_price,
                    'portfolio_value': portfolio_value,
                    'positions': positions
                }
                
                # 风控检查
                if risk_manager:
                    exit_decision = risk_manager.should_exit_position(risk_context)
                    
                    if exit_decision["status"] == "force_exit":
                        # 强制平仓
                        proceeds = positions * current_price * (1 - commission)
                        portfolio_value += proceeds
                        
                        profit_loss = proceeds - (entry_price * positions * (1 + commission)) if entry_price else 0
                        
                        trades.append({
                            'date': current_date,
                            'action': exit_decision.get('exit_type', 'force_exit'),
                            'price': current_price,
                            'shares': positions,
                            'value': proceeds,
                            'profit_loss': profit_loss
                        })
                        
                        risk_events.append({
                            'date': current_date,
                            'event': 'force_exit',
                            'reason': exit_decision.get('reason', '风控强制平仓'),
                            'price': current_price
                        })
                        
                        positions = 0
                        entry_price = None
                        stop_loss_price = None
                
                # 仓位调整检查
                if position_manager and positions > 0:
                    current_value = portfolio_value + positions * current_price
                    profit_ratio = (current_value - initial_capital) / initial_capital
                    
                    adjust_context = {
                        'market_volatility': market_volatility,
                        'profit_ratio': profit_ratio,
                        'current_price': current_price,
                        'entry_price': entry_price
                    }
                    
                    adjustment = position_manager.adjust_position(positions, adjust_context)
                    if adjustment["status"] == "success" and adjustment["action"] != "hold":
                        position_adjustments.append({
                            'date': current_date,
                            'action': adjustment["action"],
                            'reason': adjustment.get('reason', ''),
                            'adjustment_ratio': adjustment.get('adjustment_ratio', 1.0)
                        })
            
            # 记录组合价值
            current_portfolio_value = portfolio_value + positions * current_price
            portfolio_values.append(current_portfolio_value)
        
        # 最终清算
        if positions > 0:
            final_price = signals_df.iloc[-1][price_col]
            portfolio_value += positions * final_price
        
        # 计算回测结果
        total_return = (portfolio_value - initial_capital) / initial_capital
        portfolio_values = [float(v) for v in portfolio_values]
        
        # 计算风险指标
        risk_metrics = {}
        if len(portfolio_values) >= 2:
            portfolio_series = pd.Series(portfolio_values)
            returns = portfolio_series.pct_change().dropna()
            
            if len(returns) >= 2:
                try:
                    risk_metrics["volatility"] = calculate_volatility(returns)["data"]
                    risk_metrics["drawdown"] = calculate_max_drawdown(portfolio_values)["data"]
                    risk_metrics["sharpe"] = calculate_sharpe_ratio(returns, risk_free_rate)["data"]
                    risk_metrics["var"] = calculate_var(returns)["data"]
                except Exception as e:
                    risk_metrics["error"] = f"风险指标计算失败: {e}"
        
        # 计算交易统计
        completed_trades = [t for t in trades if t.get('action') in ['sell', 'stop_loss', 'force_exit']]
        win_rate = calculate_win_rate(trades)
        
        return {
            "status": "success",
            "data": {
                # 基础回测结果
                "initial_capital": initial_capital,
                "final_value": portfolio_value,
                "total_return": total_return,
                "total_return_pct": total_return * 100,
                "trades_count": len(trades),
                "completed_trades": len(completed_trades),
                "trades": trades,
                "portfolio_values": portfolio_values,
                
                # 管理器配置
                "risk_manager_config": risk_manager_config,
                "position_manager_config": position_manager_config,
                
                # 风控事件
                "risk_events": risk_events,
                "risk_events_count": len(risk_events),
                
                # 仓位调整记录
                "position_adjustments": position_adjustments,
                "position_adjustments_count": len(position_adjustments),
                
                # 交易统计
                "win_rate": win_rate,
                "win_rate_pct": win_rate * 100,
                
                # 风险指标
                "risk_metrics": risk_metrics,
                
                # 市场环境
                "market_volatility": market_volatility,
                "market_volatility_pct": market_volatility * 100
            },
            "message": "可插拔回测完成"
        }
        
    except Exception as e:
        logger.error(f"[Strategy]可插拔回测失败: {e}")
        return {"status": "error", "message": f"回测失败: {e}"}
# 事件驱动回测
def event_driven_backtest(
    events_data: List[Dict], price_data: pd.DataFrame, 
    initial_capital=100000, commission=0.001, 
    signal_rules=None, risk_manager_config=None
):
    """
    事件驱动回测功能
    :param events_data: 历史事件数据
    :param price_data: 价格数据
    :param initial_capital: 初始资金
    :param commission: 手续费率
    :param signal_rules: 信号生成规则列表
    :param risk_manager_config: 风险管理配置
    :return: 回测结果
    """
    logger.info(f"[Strategy]开始事件驱动回测，初始资金: {initial_capital}")
    
    try:
        from .signal_service import MarketEvent
        
        # 初始化信号生成器
        signal_generator = EventSignalGenerator()
        
        # 添加默认规则
        if signal_rules is None:
            signal_rules = [news_sentiment_rule, keyword_trigger_rule]
        
        for rule in signal_rules:
            signal_generator.add_rule(rule)
        
        portfolio_value = initial_capital
        positions = {}
        trades = []
        portfolio_values = []
        event_signals = []
        
        # 按时间排序事件
        sorted_events = sorted(events_data, key=lambda x: x['timestamp'])
        
        # 处理每个事件
        for event_data in sorted_events:
            # 转换为MarketEvent对象
            event = MarketEvent(**event_data)
            
            # 生成信号
            signals = signal_generator.generate_signals([event])
            
            for signal in signals:
                symbol = signal['symbol']
                signal_value = signal['signal']
                timestamp = signal['timestamp']
                
                # 获取当时的价格
                price_row = price_data[
                    (price_data['symbol'] == symbol) & 
                    (price_data['date'] <= timestamp)
                ].tail(1)
                
                if price_row.empty:
                    continue
                
                current_price = price_row['close'].iloc[0]
                
                # 执行交易逻辑
                if signal_value > 0:  # 买入信号
                    if symbol not in positions or positions[symbol] == 0:
                        # 计算买入数量（可以根据信号强度调整）
                        position_size = portfolio_value * signal['strength'] * 0.1  # 最多10%仓位
                        shares = int(position_size // (current_price * (1 + commission)))
                        
                        if shares > 0:
                            cost = shares * current_price * (1 + commission)
                            portfolio_value -= cost
                            positions[symbol] = positions.get(symbol, 0) + shares
                            
                            trades.append({
                                'date': timestamp,
                                'symbol': symbol,
                                'action': 'buy',
                                'price': current_price,
                                'shares': shares,
                                'value': cost,
                                'reason': signal['reason'],
                                'event_id': signal['event_id']
                            })
                            
                            event_signals.append(signal)
                
                elif signal_value < 0:  # 卖出信号
                    if symbol in positions and positions[symbol] > 0:
                        shares = positions[symbol]
                        proceeds = shares * current_price * (1 - commission)
                        portfolio_value += proceeds
                        positions[symbol] = 0
                        
                        trades.append({
                            'date': timestamp,
                            'symbol': symbol,
                            'action': 'sell',
                            'price': current_price,
                            'shares': shares,
                            'value': proceeds,
                            'reason': signal['reason'],
                            'event_id': signal['event_id']
                        })
                        
                        event_signals.append(signal)
            
            # 计算当前组合价值
            current_value = portfolio_value
            for symbol, shares in positions.items():
                if shares > 0:
                    latest_price_row = price_data[
                        (price_data['symbol'] == symbol) & 
                        (price_data['date'] <= event.timestamp)
                    ].tail(1)
                    if not latest_price_row.empty:
                        current_value += shares * latest_price_row['close'].iloc[0]
            
            portfolio_values.append({
                'date': event.timestamp,
                'value': current_value
            })
        
        # 计算最终收益
        final_value = portfolio_value
        for symbol, shares in positions.items():
            if shares > 0:
                final_price_row = price_data[price_data['symbol'] == symbol].tail(1)
                if not final_price_row.empty:
                    final_value += shares * final_price_row['close'].iloc[0]
        
        total_return = (final_value - initial_capital) / initial_capital
        
        return {
            "status": "success",
            "data": {
                "initial_capital": initial_capital,
                "final_value": final_value,
                "total_return": total_return,
                "total_return_pct": total_return * 100,
                "trades_count": len(trades),
                "trades": trades,
                "portfolio_values": portfolio_values,
                "event_signals": event_signals,
                "events_processed": len(sorted_events),
                "signals_generated": len(event_signals)
            },
            "message": "事件驱动回测完成"
        }
        
    except Exception as e:
        logger.error(f"[Strategy]事件驱动回测失败: {e}")
        return {"status": "error", "message": f"回测失败: {e}"}
# 多驱动方式回测
def multi_driven_backtest(
    price_data: pd.DataFrame, 
    events_data: List[Dict] = None,
    initial_capital=100000, 
    commission=0.001,
    data_signal_config=None,
    event_signal_config=None,
    signal_weights=None,
    risk_manager_config=None
):
    """
    多驱动方式回测（同时支持数据驱动和事件驱动）
    :param price_data: 价格数据
    :param events_data: 事件数据
    :param initial_capital: 初始资金
    :param commission: 手续费率
    :param data_signal_config: 数据驱动信号配置
    :param event_signal_config: 事件驱动信号配置
    :param signal_weights: 信号权重配置
    :param risk_manager_config: 风险管理配置
    :return: 多驱动回测结果
    """
    logger.info(f"[Strategy]开始多驱动方式回测，初始资金: {initial_capital}")
    
    try:
        # 默认配置
        if data_signal_config is None:
            data_signal_config = {
                'ma_crossover': {'enable': True, 'short_period': 5, 'long_period': 20},
                'rsi': {'enable': True, 'period': 14, 'oversold': 30, 'overbought': 70},
                'rule_based': {'enable': True}
            }
        
        if event_signal_config is None:
            event_signal_config = {
                'news_sentiment': {'enable': True, 'threshold': 0.7},
                'earnings': {'enable': True, 'anticipation_days': 3},
                'keyword_trigger': {'enable': True, 'strength': 0.6}
            }
        
        if signal_weights is None:
            signal_weights = {
                'data_driven': 0.6,  # 数据驱动信号权重
                'event_driven': 0.4  # 事件驱动信号权重
            }
        
        # 生成数据驱动信号
        data_signals = []
        data_signal_details = {}
        
        if data_signal_config.get('ma_crossover', {}).get('enable', False):
            ma_result = generate_ma_crossover_signal(
                price_data,
                data_signal_config['ma_crossover']['short_period'],
                data_signal_config['ma_crossover']['long_period']
            )
            if ma_result['status'] == 'success':
                ma_df = pd.DataFrame(ma_result['data'])
                ma_signals = ma_df[ma_df['signal'] != 0].to_dict('records')
                for signal in ma_signals:
                    signal['signal_type'] = 'ma_crossover'
                    signal['weight'] = signal_weights['data_driven'] * 0.5
                data_signals.extend(ma_signals)
                data_signal_details['ma_crossover'] = ma_result
        
        if data_signal_config.get('rsi', {}).get('enable', False):
            rsi_result = generate_rsi_signal(
                price_data,
                data_signal_config['rsi']['period'],
                data_signal_config['rsi']['oversold'],
                data_signal_config['rsi']['overbought']
            )
            if rsi_result['status'] == 'success':
                rsi_df = pd.DataFrame(rsi_result['data'])
                rsi_signals = rsi_df[rsi_df['signal'] != 0].to_dict('records')
                for signal in rsi_signals:
                    signal['signal_type'] = 'rsi'
                    signal['weight'] = signal_weights['data_driven'] * 0.5
                data_signals.extend(rsi_signals)
                data_signal_details['rsi'] = rsi_result
        
        # 生成事件驱动信号
        event_signals = []
        event_signal_details = {}
        
        if events_data:
            if event_signal_config.get('news_sentiment', {}).get('enable', False):
                news_result = generate_news_sentiment_signal(
                    events_data,
                    event_signal_config['news_sentiment']['threshold']
                )
                if news_result['status'] == 'success':
                    news_signals = news_result['data']['signals']
                    for signal in news_signals:
                        signal['signal_type'] = 'news_sentiment'
                        signal['weight'] = signal_weights['event_driven'] * 0.5
                    event_signals.extend(news_signals)
                    event_signal_details['news_sentiment'] = news_result
            
            if event_signal_config.get('earnings', {}).get('enable', False):
                earnings_result = generate_earnings_signal(
                    events_data,
                    event_signal_config['earnings']['anticipation_days']
                )
                if earnings_result['status'] == 'success':
                    earnings_signals = earnings_result['data']['signals']
                    for signal in earnings_signals:
                        signal['signal_type'] = 'earnings'
                        signal['weight'] = signal_weights['event_driven'] * 0.5
                    event_signals.extend(earnings_signals)
                    event_signal_details['earnings'] = earnings_result
        
        # 合并所有信号
        all_signals = data_signals + event_signals
        
        # 按时间排序信号
        all_signals.sort(key=lambda x: x.get('date', x.get('timestamp', '')))
        
        # 初始化回测变量
        portfolio_value = initial_capital
        positions = {}
        trades = []
        portfolio_values = []
        signal_history = []
        
        # 初始化风险管理器
        risk_manager = None
        if risk_manager_config:
            risk_manager = ManagerFactory.create_risk_manager(
                risk_manager_config.get('type', 'basic'),
                risk_manager_config.get('params', {})
            )
        
        # 处理每个信号
        for signal in all_signals:
            try:
                symbol = signal.get('symbol', 'default')
                signal_value = signal.get('signal', 0)
                signal_weight = signal.get('weight', 1.0)
                signal_date = signal.get('date', signal.get('timestamp'))
                signal_type = signal.get('signal_type', 'unknown')
                
                # 获取当前价格
                current_price_row = price_data[
                    price_data['date'] <= signal_date
                ].tail(1)
                
                if current_price_row.empty:
                    continue
                
                current_price = current_price_row['close'].iloc[0]
                
                # 应用权重调整信号强度
                adjusted_signal = signal_value * signal_weight
                
                # 风险管理检查
                if risk_manager:
                    risk_check = risk_manager.check_risk({
                        'portfolio_value': portfolio_value,
                        'positions': positions,
                        'signal': adjusted_signal,
                        'price': current_price
                    })
                    if not risk_check.get('allow_trade', True):
                        logger.info(f"[Strategy]风险管理阻止交易: {risk_check.get('reason', '未知原因')}")
                        continue
                
                # 执行交易逻辑
                if adjusted_signal > 0.1:  # 买入信号阈值
                    if symbol not in positions or positions[symbol] <= 0:
                        # 计算买入数量
                        position_size = portfolio_value * abs(adjusted_signal) * 0.1  # 最多10%仓位
                        shares = int(position_size // (current_price * (1 + commission)))
                        
                        if shares > 0:
                            cost = shares * current_price * (1 + commission)
                            portfolio_value -= cost
                            positions[symbol] = positions.get(symbol, 0) + shares
                            
                            trade_record = {
                                'date': signal_date,
                                'symbol': symbol,
                                'action': 'buy',
                                'price': current_price,
                                'shares': shares,
                                'value': cost,
                                'signal_type': signal_type,
                                'signal_strength': adjusted_signal,
                                'reason': signal.get('reason', f'{signal_type}信号')
                            }
                            trades.append(trade_record)
                            
                elif adjusted_signal < -0.1:  # 卖出信号阈值
                    if symbol in positions and positions[symbol] > 0:
                        shares = positions[symbol]
                        proceeds = shares * current_price * (1 - commission)
                        portfolio_value += proceeds
                        positions[symbol] = 0
                        
                        trade_record = {
                            'date': signal_date,
                            'symbol': symbol,
                            'action': 'sell',
                            'price': current_price,
                            'shares': shares,
                            'value': proceeds,
                            'signal_type': signal_type,
                            'signal_strength': adjusted_signal,
                            'reason': signal.get('reason', f'{signal_type}信号')
                        }
                        trades.append(trade_record)
                
                # 记录信号历史
                signal_history.append({
                    'date': signal_date,
                    'signal_type': signal_type,
                    'signal_value': signal_value,
                    'adjusted_signal': adjusted_signal,
                    'weight': signal_weight,
                    'symbol': symbol
                })
                
                # 计算当前组合价值
                current_value = portfolio_value
                for pos_symbol, shares in positions.items():
                    if shares > 0:
                        latest_price_row = price_data[
                            (price_data['date'] <= signal_date)
                        ].tail(1)
                        if not latest_price_row.empty:
                            current_value += shares * latest_price_row['close'].iloc[0]
                
                portfolio_values.append({
                    'date': signal_date,
                    'value': current_value,
                    'cash': portfolio_value,
                    'positions_value': current_value - portfolio_value
                })
                
            except Exception as e:
                logger.warning(f"[Strategy]处理信号时出错: {e}")
                continue
        
        # 计算最终价值
        final_value = portfolio_value
        for symbol, shares in positions.items():
            if shares > 0:
                final_price_row = price_data.tail(1)
                if not final_price_row.empty:
                    final_value += shares * final_price_row['close'].iloc[0]
        
        total_return = (final_value - initial_capital) / initial_capital
        
        # 统计信号类型分布
        signal_type_stats = {}
        for signal in signal_history:
            signal_type = signal['signal_type']
            if signal_type not in signal_type_stats:
                signal_type_stats[signal_type] = {'count': 0, 'total_strength': 0}
            signal_type_stats[signal_type]['count'] += 1
            signal_type_stats[signal_type]['total_strength'] += abs(signal['adjusted_signal'])
        
        return {
            "status": "success",
            "data": {
                "initial_capital": initial_capital,
                "final_value": final_value,
                "total_return": total_return,
                "total_return_pct": total_return * 100,
                "trades_count": len(trades),
                "trades": trades,
                "portfolio_values": portfolio_values,
                "signal_history": signal_history,
                "signal_type_stats": signal_type_stats,
                "data_signal_details": data_signal_details,
                "event_signal_details": event_signal_details,
                "config": {
                    "data_signal_config": data_signal_config,
                    "event_signal_config": event_signal_config,
                    "signal_weights": signal_weights
                },
                "signals_processed": {
                    "data_signals": len(data_signals),
                    "event_signals": len(event_signals),
                    "total_signals": len(all_signals)
                }
            },
            "message": "多驱动方式回测完成"
        }
        
    except Exception as e:
        logger.error(f"[Strategy]多驱动方式回测失败: {e}")
        return {"status": "error", "message": f"回测失败: {e}"}
# ============ 策略性能评估 ============
def evaluate_strategy_performance(backtest_results: Dict, benchmark_data: pd.DataFrame = None):
    """
    策略性能综合评估
    :param backtest_results: 回测结果
    :param benchmark_data: 基准数据（如沪深300）
    :return: 性能评估报告
    """
    logger.info("[Strategy]开始策略性能评估")
    
    try:
        if backtest_results.get('status') != 'success':
            return {"status": "error", "message": "回测结果无效"}
        
        data = backtest_results['data']
        portfolio_values = data.get('portfolio_values', [])
        trades = data.get('trades', [])
        
        if not portfolio_values:
            return {"status": "error", "message": "缺少组合价值数据"}
        
        # 转换为DataFrame便于计算
        portfolio_df = pd.DataFrame(portfolio_values)
        portfolio_df['date'] = pd.to_datetime(portfolio_df['date'])
        portfolio_df = portfolio_df.sort_values('date')
        
        # 计算收益率序列
        portfolio_df['returns'] = portfolio_df['value'].pct_change().fillna(0)
        
        # 基础性能指标
        total_return = data.get('total_return', 0)
        annual_return = (1 + total_return) ** (252 / len(portfolio_df)) - 1
        volatility = portfolio_df['returns'].std() * np.sqrt(252)
        sharpe_ratio = (annual_return - 0.03) / volatility if volatility > 0 else 0
        
        # 最大回撤
        portfolio_df['cumulative'] = (1 + portfolio_df['returns']).cumprod()
        portfolio_df['peak'] = portfolio_df['cumulative'].expanding().max()
        portfolio_df['drawdown'] = (portfolio_df['cumulative'] - portfolio_df['peak']) / portfolio_df['peak']
        max_drawdown = portfolio_df['drawdown'].min()
        
        # 交易统计
        winning_trades = [t for t in trades if t.get('profit', 0) > 0]
        losing_trades = [t for t in trades if t.get('profit', 0) < 0]
        win_rate = len(winning_trades) / len(trades) if trades else 0
        
        avg_win = np.mean([t.get('profit', 0) for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.get('profit', 0) for t in losing_trades]) if losing_trades else 0
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        
        # 基准比较（如果提供）
        benchmark_metrics = {}
        if benchmark_data is not None:
            benchmark_returns = benchmark_data['close'].pct_change().fillna(0)
            benchmark_annual_return = (1 + benchmark_returns.mean()) ** 252 - 1
            benchmark_volatility = benchmark_returns.std() * np.sqrt(252)
            
            # 计算Alpha和Beta
            covariance = np.cov(portfolio_df['returns'], benchmark_returns)[0][1]
            benchmark_variance = benchmark_returns.var()
            beta = covariance / benchmark_variance if benchmark_variance > 0 else 0
            alpha = annual_return - (0.03 + beta * (benchmark_annual_return - 0.03))
            
            benchmark_metrics = {
                'benchmark_annual_return': benchmark_annual_return,
                'benchmark_volatility': benchmark_volatility,
                'alpha': alpha,
                'beta': beta,
                'information_ratio': (annual_return - benchmark_annual_return) / 
                                   (portfolio_df['returns'] - benchmark_returns).std() * np.sqrt(252)
            }
        
        # 风险调整收益指标
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
        sortino_ratio = annual_return / (portfolio_df['returns'][portfolio_df['returns'] < 0].std() * np.sqrt(252))
        
        performance_report = {
            "status": "success",
            "data": {
                "return_metrics": {
                    "total_return": total_return,
                    "annual_return": annual_return,
                    "volatility": volatility,
                    "sharpe_ratio": sharpe_ratio,
                    "calmar_ratio": calmar_ratio,
                    "sortino_ratio": sortino_ratio
                },
                "risk_metrics": {
                    "max_drawdown": max_drawdown,
                    "var_95": np.percentile(portfolio_df['returns'], 5),
                    "cvar_95": portfolio_df['returns'][portfolio_df['returns'] <= np.percentile(portfolio_df['returns'], 5)].mean()
                },
                "trading_metrics": {
                    "total_trades": len(trades),
                    "win_rate": win_rate,
                    "profit_factor": profit_factor,
                    "avg_win": avg_win,
                    "avg_loss": avg_loss
                },
                "benchmark_metrics": benchmark_metrics,
                "evaluation_date": datetime.datetime.now().isoformat()
            },
            "message": "策略性能评估完成"
        }
        
        return performance_report
        
    except Exception as e:
        logger.error(f"[Strategy]策略性能评估失败: {e}")
        return {"status": "error", "message": f"性能评估失败: {e}"}

# 便捷函数：获取可用的管理器列表
def get_available_managers():
    """获取所有可用的管理器"""
    return ManagerFactory.list_managers()


# ============ 策略参数优化（TODO） ============
# 优化数据驱动单信号参数(TODO)
def optimize_ma_crossover():
    # 获取价格数据
    df = get_stock_data('000001.SZ', '2023-01-01', '2024-01-01')
    
    # 定义参数范围
    param_ranges = {
        'short_period': [5, 10, 15, 20],
        'long_period': [20, 30, 50, 60]
    }
    
    # 执行参数优化
    optimization_result = optimize_strategy_parameters(
        df=df,
        strategy_func=generate_ma_crossover_signal,
        param_ranges=param_ranges,
        optimization_metric='sharpe_ratio',
        max_iterations=50
    )
    
    # 获取最佳参数
    best_params = optimization_result['data']['best_params']
    print(f"最佳参数: {best_params}")
def optimize_rsi_strategy():
    df = get_stock_data('000001.SZ', '2023-01-01', '2024-01-01')
    
    param_ranges = {
        'period': [10, 14, 20, 25],
        'oversold': [20, 25, 30, 35],
        'overbought': [65, 70, 75, 80]
    }
    
    result = optimize_strategy_parameters(
        df=df,
        strategy_func=generate_rsi_signal,
        param_ranges=param_ranges,
        optimization_metric='total_return'
    )
    
    return result['data']['best_params']
# 优化事件驱动单信号参数(TODO)
def optimize_news_sentiment_strategy():
    events_data = get_news_events('000001.SZ', '2023-01-01', '2024-01-01')
    
    param_ranges = {
        'sentiment_threshold': [0.5, 0.6, 0.7, 0.8, 0.9]
    }
    
    # 包装函数以适配优化器
    def wrapped_news_strategy(df, sentiment_threshold):
        return generate_news_sentiment_signal(events_data, sentiment_threshold)
    
    result = optimize_strategy_parameters(
        df=df,
        strategy_func=wrapped_news_strategy,
        param_ranges=param_ranges,
        optimization_metric='win_rate'
    )
    
    return result
def optimize_strategy_parameters(df: pd.DataFrame, strategy_func, param_ranges: Dict, 
                               optimization_metric='sharpe_ratio', max_iterations=100):
    """
    策略参数优化
    :param df: 价格数据
    :param strategy_func: 策略函数
    :param param_ranges: 参数范围字典
    :param optimization_metric: 优化目标指标
    :param max_iterations: 最大迭代次数
    :return: 优化结果
    """
    logger.info(f"[Strategy]开始策略参数优化，目标指标: {optimization_metric}")
    
    try:
        from itertools import product
        import random
        
        # 生成参数组合
        param_names = list(param_ranges.keys())
        param_values = [param_ranges[name] for name in param_names]
        
        # 如果组合数量太大，使用随机采样
        all_combinations = list(product(*param_values))
        if len(all_combinations) > max_iterations:
            combinations = random.sample(all_combinations, max_iterations)
        else:
            combinations = all_combinations
        
        best_params = None
        best_score = float('-inf')
        optimization_results = []
        
        for i, param_combo in enumerate(combinations):
            try:
                # 构建参数字典
                params = dict(zip(param_names, param_combo))
                
                # 运行策略
                strategy_result = strategy_func(df, **params)
                
                if strategy_result.get('status') != 'success':
                    continue
                
                # 运行回测
                backtest_result = simple_backtest(df, strategy_result['data'])
                
                if backtest_result.get('status') != 'success':
                    continue
                
                # 计算评估指标
                performance = evaluate_strategy_performance(backtest_result)
                
                if performance.get('status') != 'success':
                    continue
                
                # 获取目标指标值
                score = performance['data']['return_metrics'].get(optimization_metric, 0)
                
                optimization_results.append({
                    'params': params,
                    'score': score,
                    'performance': performance['data']
                })
                
                # 更新最佳参数
                if score > best_score:
                    best_score = score
                    best_params = params
                
                logger.info(f"[Strategy]优化进度: {i+1}/{len(combinations)}, 当前最佳{optimization_metric}: {best_score:.4f}")
                
            except Exception as e:
                logger.warning(f"[Strategy]参数组合 {param_combo} 优化失败: {e}")
                continue
        
        # 排序结果
        optimization_results.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            "status": "success",
            "data": {
                "best_params": best_params,
                "best_score": best_score,
                "optimization_metric": optimization_metric,
                "total_combinations_tested": len(optimization_results),
                "top_10_results": optimization_results[:10],
                "all_results": optimization_results
            },
            "message": f"参数优化完成，最佳{optimization_metric}: {best_score:.4f}"
        }
        
    except Exception as e:
        logger.error(f"[Strategy]策略参数优化失败: {e}")
        return {"status": "error", "message": f"参数优化失败: {e}"}

# ============ 策略组合管理（TODO） ============
def create_optimized_portfolio():
    df = get_stock_data('000001.SZ', '2023-01-01', '2024-01-01')
    
    # 首先优化各个策略的参数
    ma_best_params = optimize_ma_crossover()
    rsi_best_params = optimize_rsi_strategy()
    
    # 创建策略组合配置
    strategies_config = [
        {
            'name': 'MA_Crossover_Optimized',
            'function': generate_ma_crossover_signal,
            'params': ma_best_params,
            'weight': 0.4  # 40%权重
        },
        {
            'name': 'RSI_Optimized',
            'function': generate_rsi_signal,
            'params': rsi_best_params,
            'weight': 0.3  # 30%权重
        },
        {
            'name': 'Data_Driven_Signals',
            'function': generate_data_driven_signals,
            'params': {'signal_rules': ['adaptive_ma_crossover_rule']},
            'weight': 0.3  # 30%权重
        }
    ]
    
    # 创建策略组合
    portfolio_result = create_strategy_portfolio(
        strategies_config=strategies_config,
        df=df,
        allocation_method='custom_weight'
    )
    
    return portfolio_result
def create_hybrid_portfolio():
    df = get_stock_data('000001.SZ', '2023-01-01', '2024-01-01')
    events_data = get_news_events('000001.SZ', '2023-01-01', '2024-01-01')
    
    strategies_config = [
        {
            'name': 'Technical_Signals',
            'function': lambda df: generate_unified_signals(
                price_data=df,
                data_signal_config={'rules': ['adaptive_ma_crossover_rule', 'multi_confirmation_rsi_rule']}
            ),
            'params': {},
            'weight': 0.6
        },
        {
            'name': 'Event_Signals',
            'function': lambda df: generate_unified_signals(
                price_data=df,
                events_data=events_data,
                event_signal_config={'rules': ['news_sentiment_rule']}
            ),
            'params': {},
            'weight': 0.4
        }
    ]
    
    portfolio_result = create_strategy_portfolio(
        strategies_config=strategies_config,
        df=df,
        allocation_method='custom_weight'
    )
    
    return portfolio_result
def create_strategy_portfolio(strategies_config: List[Dict], df: pd.DataFrame, 
                            allocation_method='equal_weight'):
    """
    创建策略组合
    :param strategies_config: 策略配置列表
    :param df: 价格数据
    :param allocation_method: 资金分配方法
    :return: 策略组合结果
    """
    logger.info(f"[Strategy]创建策略组合，策略数量: {len(strategies_config)}")
    
    try:
        strategy_results = []
        total_weight = 0
        
        # 执行各个策略
        for strategy_config in strategies_config:
            strategy_name = strategy_config.get('name', 'unknown')
            strategy_func = strategy_config.get('function')
            strategy_params = strategy_config.get('params', {})
            strategy_weight = strategy_config.get('weight', 1.0)
            
            if not strategy_func:
                logger.warning(f"[Strategy]策略 {strategy_name} 缺少函数定义")
                continue
            
            try:
                # 执行策略
                result = strategy_func(df, **strategy_params)
                if result.get('status') == 'success':
                    strategy_results.append({
                        'name': strategy_name,
                        'weight': strategy_weight,
                        'signals': result['data'],
                        'config': strategy_config
                    })
                    total_weight += strategy_weight
                    
            except Exception as e:
                logger.error(f"[Strategy]策略 {strategy_name} 执行失败: {e}")
                continue
        
        if not strategy_results:
            return {"status": "error", "message": "没有成功执行的策略"}
        
        # 标准化权重
        for result in strategy_results:
            result['normalized_weight'] = result['weight'] / total_weight
        
        # 合并信号
        combined_signals = []
        
        if allocation_method == 'equal_weight':
            # 等权重合并
            for result in strategy_results:
                weight = 1.0 / len(strategy_results)
                for signal in result['signals']:
                    signal_copy = signal.copy()
                    signal_copy['weight'] = weight
                    signal_copy['strategy'] = result['name']
                    combined_signals.append(signal_copy)
                    
        elif allocation_method == 'custom_weight':
            # 自定义权重合并
            for result in strategy_results:
                weight = result['normalized_weight']
                for signal in result['signals']:
                    signal_copy = signal.copy()
                    signal_copy['weight'] = weight
                    signal_copy['strategy'] = result['name']
                    combined_signals.append(signal_copy)
        
        return {
            "status": "success",
            "data": {
                "portfolio_signals": combined_signals,
                "strategy_results": strategy_results,
                "allocation_method": allocation_method,
                "total_strategies": len(strategy_results),
                "total_signals": len(combined_signals)
            },
            "message": f"策略组合创建完成，包含 {len(strategy_results)} 个策略"
        }
        
    except Exception as e:
        logger.error(f"[Strategy]策略组合创建失败: {e}")
        return {"status": "error", "message": f"策略组合创建失败: {e}"}

# ============ 完整策略流程 ============

def complete_strategy_workflow():
    """完整的策略开发和优化工作流程"""
    
    # 1. 数据准备
    df = get_stock_data('000001.SZ', '2023-01-01', '2024-01-01')
    events_data = get_news_events('000001.SZ', '2023-01-01', '2024-01-01')
    
    # 2. 单策略参数优化
    print("步骤1: 优化MA交叉策略参数...")
    ma_optimization = optimize_strategy_parameters(
        df=df,
        strategy_func=generate_ma_crossover_signal,
        param_ranges={
            'short_period': [5, 10, 15],
            'long_period': [20, 30, 50]
        },
        optimization_metric='sharpe_ratio'
    )
    
    print("步骤2: 优化RSI策略参数...")
    rsi_optimization = optimize_strategy_parameters(
        df=df,
        strategy_func=generate_rsi_signal,
        param_ranges={
            'period': [10, 14, 20],
            'oversold': [25, 30, 35],
            'overbought': [65, 70, 75]
        },
        optimization_metric='total_return'
    )
    
    # 3. 创建优化后的策略组合
    print("步骤3: 创建策略组合...")
    strategies_config = [
        {
            'name': 'Optimized_MA',
            'function': generate_ma_crossover_signal,
            'params': ma_optimization['data']['best_params'],
            'weight': 0.4
        },
        {
            'name': 'Optimized_RSI',
            'function': generate_rsi_signal,
            'params': rsi_optimization['data']['best_params'],
            'weight': 0.3
        },
        {
            'name': 'Event_Driven',
            'function': lambda df: generate_news_sentiment_signal(events_data, 0.7),
            'params': {},
            'weight': 0.3
        }
    ]
    
    portfolio = create_strategy_portfolio(
        strategies_config=strategies_config,
        df=df,
        allocation_method='custom_weight'
    )
    
    # 4. 组合回测
    print("步骤4: 执行组合回测...")
    backtest_result = multi_driven_backtest(
        price_data=df,
        events_data=events_data,
        initial_capital=100000,
        data_signal_config={
            'rules': ['adaptive_ma_crossover_rule'],
            'params': ma_optimization['data']['best_params']
        },
        event_signal_config={
            'rules': ['news_sentiment_rule'],
            'params': {'sentiment_threshold': 0.7}
        },
        signal_weights={'data_signals': 0.7, 'event_signals': 0.3}
    )
    
    # 5. 性能评估
    print("步骤5: 评估策略性能...")
    performance = evaluate_strategy_performance(backtest_result)
    
    return {
        'optimizations': {
            'ma_strategy': ma_optimization,
            'rsi_strategy': rsi_optimization
        },
        'portfolio': portfolio,
        'backtest': backtest_result,
        'performance': performance
    }
