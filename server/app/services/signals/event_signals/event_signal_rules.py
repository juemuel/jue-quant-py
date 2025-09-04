from app.services.events.event_service import MarketEvent, EventType, EventSeverity
from typing import Dict, Optional, Callable
from datetime import datetime
from functools import partial

# ============ 固定参数规则（保持向后兼容）============
# 新闻情感信号规则
def news_sentiment_rule(event: MarketEvent) -> Optional[Dict]:
    """基于新闻情感的信号规则（固定参数版本）"""
    return news_sentiment_rule_with_params(event, sentiment_threshold=0.7, 
                                          severity_levels=[EventSeverity.HIGH, EventSeverity.CRITICAL])
def news_sentiment_rule_with_params(event: MarketEvent, 
                                   sentiment_threshold: float = 0.7,
                                   severity_levels: list = None) -> Optional[Dict]:
    """参数化的新闻情感信号规则"""
    if event.event_type != EventType.NEWS:
        return None
    
    if severity_levels is None:
        severity_levels = [EventSeverity.HIGH, EventSeverity.CRITICAL]
    
    # 强烈正面新闻 -> 买入信号
    if event.sentiment_score > sentiment_threshold and event.severity in severity_levels:
        return {
            'symbol': event.symbol,
            'signal': 1,  # 买入
            'strength': min(event.sentiment_score, 1.0),
            'reason': f'正面新闻(阈值{sentiment_threshold}): {event.title}',
            'timestamp': event.timestamp,
            'event_id': event.event_id
        }
    
    # 负面新闻 -> 卖出信号
    elif event.sentiment_score < -sentiment_threshold and event.severity in severity_levels:
        return {
            'symbol': event.symbol,
            'signal': -1,  # 卖出
            'strength': min(abs(event.sentiment_score), 1.0),
            'reason': f'负面新闻(阈值{sentiment_threshold}): {event.title}',
            'timestamp': event.timestamp,
            'event_id': event.event_id
        }
    
    return None

# 财报披露前信号规则
def earnings_anticipation_rule(event: MarketEvent) -> Optional[Dict]:
    """财报披露前的预期信号（固定参数版本）"""
    return earnings_anticipation_rule_with_params(event, anticipation_days_min=1, 
                                                anticipation_days_max=3, signal_strength=0.5)
def earnings_anticipation_rule_with_params(event: MarketEvent,
                                         anticipation_days_min: int = 1,
                                         anticipation_days_max: int = 3,
                                         signal_strength: float = 0.5) -> Optional[Dict]:
    """参数化的财报披露前预期信号"""
    # 同时支持EARNINGS和FINANCIAL_REPORT类型
    if event.event_type not in [EventType.FINANCIAL_REPORT, EventType.EARNINGS]:
        return None
    
    # 财报披露前指定天数，根据历史表现决定
    days_until_disclosure = (event.timestamp - datetime.now()).days
    
    if anticipation_days_min <= days_until_disclosure <= anticipation_days_max:
        return {
            'symbol': event.symbol,
            'signal': signal_strength,  # 可配置的信号强度
            'strength': signal_strength,
            'reason': f'财报披露前预期({anticipation_days_min}-{anticipation_days_max}天): {event.title}',
            'timestamp': datetime.now(),
            'event_id': event.event_id
        }
    
    return None

# 关键词触发规则
def keyword_trigger_rule(event: MarketEvent) -> Optional[Dict]:
    """基于关键词的触发规则（固定参数版本）"""
    positive_keywords = ['重组', '收购', '合作', '中标', '业绩增长', '分红', '发布会', '成功', '获得', '奖项', '突破']
    negative_keywords = ['调查', '违规', '亏损', '退市', '停牌', '诉讼', '下滑', '风波', '调整', '收紧']
    return keyword_trigger_rule_with_params(event, positive_keywords=positive_keywords,
                                           negative_keywords=negative_keywords,
                                           severity_levels=[EventSeverity.HIGH, EventSeverity.CRITICAL],
                                           strength=0.9)
def keyword_trigger_rule_with_params(event: MarketEvent,
                                    positive_keywords: list = None,
                                    negative_keywords: list = None,
                                    severity_levels: list = None,
                                    strength: float = 0.9) -> Optional[Dict]:
    """参数化的关键词触发规则"""
    if positive_keywords is None:
        positive_keywords = ['重组', '收购', '合作', '中标', '业绩增长']
    if negative_keywords is None:
        negative_keywords = ['调查', '违规', '亏损', '退市', '停牌']
    if severity_levels is None:
        severity_levels = [EventSeverity.HIGH, EventSeverity.CRITICAL]
    
    # 增加严重程度要求
    if event.severity not in severity_levels:
        return None
    
    # 检查正面关键词
    if any(keyword in event.title or keyword in ' '.join(event.keywords) 
           for keyword in positive_keywords):
        return {
            'symbol': event.symbol,
            'signal': 1,
            'strength': strength,
            'reason': f'正面关键词触发(强度{strength}): {event.title}',
            'timestamp': event.timestamp,
            'event_id': event.event_id
        }
    
    # 检查负面关键词
    elif any(keyword in event.title or keyword in ' '.join(event.keywords) 
             for keyword in negative_keywords):
        return {
            'symbol': event.symbol,
            'signal': -1,
            'strength': strength,
            'reason': f'负面关键词触发(强度{strength}): {event.title}',
            'timestamp': event.timestamp,
            'event_id': event.event_id
        }
    
    return None

# 添加规则
def create_parameterized_news_rule(sentiment_threshold: float = 0.7,
                                  severity_levels: list = None) -> Callable:
    """创建参数化的新闻情感规则"""
    rule = partial(news_sentiment_rule_with_params, 
                  sentiment_threshold=sentiment_threshold,
                  severity_levels=severity_levels)
    rule.chinese_name = f'新闻情感规则(参数化:阈值{sentiment_threshold})'
    rule.__name__ = f'news_sentiment_rule_parameterized_{sentiment_threshold}'  # 添加这行
    return rule

def create_parameterized_earnings_rule(anticipation_days_min: int = 1,
                                       anticipation_days_max: int = 3,
                                       signal_strength: float = 0.5) -> Callable:
    """创建参数化的财报预期规则"""
    rule = partial(earnings_anticipation_rule_with_params,
                  anticipation_days_min=anticipation_days_min,
                  anticipation_days_max=anticipation_days_max,
                  signal_strength=signal_strength)
    rule.chinese_name = f'财报预期规则(参数化:天数{anticipation_days_min}-{anticipation_days_max})'
    rule.__name__ = f'earnings_rule_parameterized_{anticipation_days_min}_{anticipation_days_max}'  # 添加这行
    return rule

def create_parameterized_keyword_rule(positive_keywords: list = None,
                                      negative_keywords: list = None,
                                      severity_levels: list = None,
                                      strength: float = 0.9) -> Callable:
    """创建参数化的关键词触发规则"""
    if positive_keywords is None:
        positive_keywords = ['利好', '上涨', '增长']
    if negative_keywords is None:
        negative_keywords = ['利空', '下跌', '亏损']
    if severity_levels is None:
        severity_levels = [EventSeverity.MEDIUM, EventSeverity.HIGH]
    
    rule = partial(keyword_trigger_rule_with_params,
                  positive_keywords=positive_keywords,
                  negative_keywords=negative_keywords,
                  severity_levels=severity_levels,
                  strength=strength)
    rule.chinese_name = f'关键词触发规则(参数化:强度{strength})'
    rule.__name__ = f'keyword_rule_parameterized_{strength}'  # 添加这行
    return rule

# 添加中文名称
news_sentiment_rule.chinese_name = '新闻情感规则(固定参数)'
keyword_trigger_rule.chinese_name = '关键词触发规则(固定参数)'
earnings_anticipation_rule.chinese_name = '财报预期规则(固定参数)'

news_sentiment_rule_with_params.chinese_name = '新闻情感规则(参数化)'
keyword_trigger_rule_with_params.chinese_name = '关键词触发规则(参数化)'
earnings_anticipation_rule_with_params.chinese_name = '财报预期规则(参数化)'