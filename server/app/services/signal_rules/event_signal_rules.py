from app.services.event_service import MarketEvent, EventType, EventSeverity
from typing import Dict, Optional
from datetime import datetime

# 新闻情感信号规则
def news_sentiment_rule(event: MarketEvent) -> Optional[Dict]:
    """基于新闻情感的信号规则"""
    if event.event_type != EventType.NEWS:
        return None
    
    # 强烈正面新闻 -> 买入信号
    if event.sentiment_score > 0.7 and event.severity in [EventSeverity.HIGH, EventSeverity.CRITICAL]:
        return {
            'symbol': event.symbol,
            'signal': 1,  # 买入
            'strength': min(event.sentiment_score, 1.0),
            'reason': f'强烈正面新闻: {event.title}',
            'timestamp': event.timestamp,
            'event_id': event.event_id
        }
    
    # 负面新闻 -> 卖出信号
    elif event.sentiment_score < -0.7 and event.severity in [EventSeverity.HIGH, EventSeverity.CRITICAL]:
        return {
            'symbol': event.symbol,
            'signal': -1,  # 卖出
            'strength': min(abs(event.sentiment_score), 1.0),
            'reason': f'强烈负面新闻: {event.title}',
            'timestamp': event.timestamp,
            'event_id': event.event_id
        }
    
    return None

# 财报披露前信号规则
def earnings_anticipation_rule(event: MarketEvent) -> Optional[Dict]:
    """财报披露前的预期信号"""
    # 同时支持EARNINGS和FINANCIAL_REPORT类型
    if event.event_type not in [EventType.FINANCIAL_REPORT, EventType.EARNINGS]:
        return None
    
    # 财报披露前3天，根据历史表现决定
    days_until_disclosure = (event.timestamp - datetime.now()).days
    
    if 1 <= days_until_disclosure <= 3:
        return {
            'symbol': event.symbol,
            'signal': 0.5,  # 轻仓买入
            'strength': 0.5,
            'reason': f'财报披露前预期: {event.title}',
            'timestamp': datetime.now(),
            'event_id': event.event_id
        }
    
    return None

# 关键词触发规则
def keyword_trigger_rule(event: MarketEvent) -> Optional[Dict]:
    """基于关键词的触发规则"""
    # 扩展关键词列表
    positive_keywords = ['重组', '收购', '合作', '中标', '业绩增长', '分红', '发布会', '成功', '获得', '奖项', '突破']
    negative_keywords = ['调查', '违规', '亏损', '退市', '停牌', '诉讼', '下滑', '风波', '调整', '收紧']
    # 增加严重程度要求
    if event.severity not in [EventSeverity.HIGH, EventSeverity.CRITICAL]:
        return None
    # 检查正面关键词
    if any(keyword in event.title or keyword in ' '.join(event.keywords) 
           for keyword in positive_keywords):
        return {
            'symbol': event.symbol,
            'signal': 1,
            'strength': 0.9,
            'reason': f'重要正面关键词触发: {event.title}',
            'timestamp': event.timestamp,
            'event_id': event.event_id
        }
    
    # 检查负面关键词
    elif any(keyword in event.title or keyword in ' '.join(event.keywords) 
             for keyword in negative_keywords):
        return {
            'symbol': event.symbol,
            'signal': -1,
            'strength': 0.9,
            'reason': f'重要负面关键词触发: {event.title}',
            'timestamp': event.timestamp,
            'event_id': event.event_id
        }
    
    return None