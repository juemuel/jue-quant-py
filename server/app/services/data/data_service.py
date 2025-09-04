from core.logger import logger
from data_providers import get_data_provider
from common.utils import clean_numeric_data, safe_convert_to_dict, debug_dataframe
import pandas as pd
import numpy as np
import datetime
from typing import List, Dict, Optional
from app.services.data.processor.data_processor import DataProcessor
from common.debug_utils import debug_data_provider


# 一、数据服务层-市场行情数据
# 1.1.1 获取所有股票列表（标准化流程）
def get_all_stocks(source="akshare", market=None, fields=None, page=None, page_size=20):
    """
    获取所有股票列表
    :param source: 数据源名称（akshare/tushare/juejinquant）
        akshare 无限制
        tushare 限制次数（积分要求）
        juejinquant 需下载终端
        qstock 移除
    :param market: 交易所名称（SH/SZ/BJ/KE/CY）
    :param fields: 返回字段,逗号分隔
    :param page: 页码
    :param page_size: 每页数量
    :return: 分页后的股票列表
    """
    debug_data_provider("获取所有股票", {"source": source, "market": market, "fields": fields, "page": page, "page_size": page_size})
    try:
        # 1.调用接口
        data_provider = get_data_provider(source)
        df = data_provider.get_all_stocks(source=source, market=market)
        # 2.判空处理
        if df.empty:
            logger.warning(f"[Service]无数据返回 {source}")
            return {"status": 'error', "message": "未查询到数据"}
        # 3.使用标准化数据处理器进行字段标准化和处理
        try:
            result = DataProcessor.process_stock_list_data(
                df, source, use_chinese=True, core_only=False, fields=fields
            )
            df_processed = result["data"]
            available_fields = result["available_fields"]
            
            # 数据处理后的结果
            debug_data_provider("处理后数据", {
                "处理后列名": df_processed.columns.tolist(),
                "可用标准字段": available_fields
            }, horizontal_output=True, show_full_content=True)
        except ValueError as e:
            logger.error(f"[Service]字段处理失败: {e}")
            return {"status": 'error', "message": str(e)}
        # 4.应用分页处理+补充字段
        result_data = DataProcessor.apply_pagination(df_processed, page, page_size)
        result_data["available_fields"] = available_fields
        return {
            "status": 'success', 
            "data": result_data,
            "message": "Success"
        }
    except Exception as e:
        logger.error(f"[Service]获取所有股票失败: {e}")
        return {"status": 'error', "message": f"获取失败：{e}"}

# 1.1.2 获取所有概念板块列表（标准化流程）
def get_concept_stocks(source="akshare", fields=None, page=None, page_size=20):
    """
    获取概念板块列表
    :param source: 数据源名称
    :param fields: 返回字段,逗号分隔
    :param page: 页码
    :param page_size: 每页数量
    :return: 概念板块列表
    """
    debug_data_provider("获取概念板块列表", {"source": source, "fields": fields, "page": page, "page_size": page_size})
    try:
        # 0.调用数据提供者获取原始数据
        data_provider = get_data_provider(source)
        df = data_provider.get_all_concepts()
        
        # 2.判空处理
        if df.empty:
            logger.warning(f"[Service]无数据返回 {source}")
            return {"status": "error", "message": "未查询到数据"}
        
        # 3.使用标准化数据处理器进行字段标准化和处理
        try:
            result = DataProcessor.process_concept_data(
                df, source, use_chinese=True, core_only=True, fields=fields
            )
            df_processed = result["data"]
            available_fields = result["available_fields"]
            
            # 数据处理后的结果
            debug_data_provider("处理后数据", {
                "处理后列名": df_processed.columns.tolist(),
                "可用标准字段": available_fields
            }, horizontal_output=True, show_full_content=True)
            
        except ValueError as e:
            logger.error(f"[Service]字段处理失败: {e}")
            return {"status": "error", "message": str(e)}
        
        # 4.应用分页处理+补充字段
        result_data = DataProcessor.apply_pagination(df_processed, page, page_size)
        result_data["available_fields"] = available_fields
        
        return {
            "status": "success", 
            "data": result_data,
            "message": "概念板块数据获取成功"
        }
        
    except Exception as e:
        logger.error(f"[Service]获取概念板块列表失败: {e}")
        return {"status": "error", "message": f"获取失败: {e}"}

# 1.1.3 获取概念板块成分股（标准化流程）
def get_concept_constituent_stocks(source="akshare", concept_identifier=None, fields=None, page=None, page_size=20):
    """
    获取概念板块成分股
    :param source: 数据源名称
    :param concept_identifier: 概念板块标识符（板块代码或板块名称）
    :param fields: 返回字段,逗号分隔
    :param page: 页码
    :param page_size: 每页数量
    :return: 概念板块成分股列表
    """
    
    debug_data_provider("获取概念板块成分股", {
        "source": source, 
        "concept_identifier": concept_identifier
    })
    if not concept_identifier:
        return {"status": "error", "message": "概念板块标识符不能为空"}
    
    try:
        # 1.调用接口
        data_provider = get_data_provider(source)
        # 特殊补充：获取板块信息用于返回元数据
        concept_info = None
        if source == "akshare":
            concept_list_df = data_provider.get_all_concepts()
            if concept_identifier in concept_list_df['板块代码'].values:
                concept_row = concept_list_df[concept_list_df['板块代码'] == concept_identifier].iloc[0]
                concept_info = {
                    "板块代码": str(concept_row['板块代码']),
                    "板块名称": str(concept_row['板块名称'])
                }
            elif concept_identifier in concept_list_df['板块名称'].values:
                concept_row = concept_list_df[concept_list_df['板块名称'] == concept_identifier].iloc[0]
                concept_info = {
                    "板块代码": str(concept_row['板块代码']),
                    "板块名称": str(concept_row['板块名称'])
                }
        df = data_provider.get_concept_constituent_stocks(concept_identifier)
        
        # 2.判空处理
        if df.empty:
            logger.warning(f"[Service]无数据返回 {source} for concept={concept_identifier}")
            return {"status": "error", "message": f"未查询到概念板块 '{concept_identifier}' 的成分股数据"}
        
        # 3.使用标准化数据处理器进行字段标准化和处理
        try:
            result = DataProcessor.process_concept_constituent_stocks_data(
                df, source, use_chinese=True, core_only=True, fields=fields
            )
            df_processed = result["data"]
            available_fields = result["available_fields"]
            # 数据处理后的结果
            debug_data_provider("处理后数据", {
                "处理后列名": df_processed.columns.tolist(),
                "可用标准字段": available_fields
            }, horizontal_output=True, show_full_content=True)
            
        except ValueError as e:
            logger.error(f"[Service]字段处理失败: {e}")
            return {"status": "error", "message": str(e)}
        
        # 4.应用分页处理+补充字段
        result_data = DataProcessor.apply_pagination(df_processed, page, page_size)
        result_data["concept_info"] = concept_info
        result_data["available_fields"] = available_fields
        
        return {
            "status": "success",
            "data": result_data,
            "message": "概念成分股数据获取成功"
        }
        
    except Exception as e:
        logger.error(f"[Service]获取概念板块成分股失败: {e}")
        return {"status": "error", "message": f"获取失败: {e}"}

# 1.2.1 获取股票历史记录（标准化流程）
def get_stock_history(source="akshare", code="000001", market="SH", start_date=None, end_date=None, fields=None, page=None, page_size=100):
    """
    获取股票历史行情数据并标准化输出格式
    :param source: 数据源名称（akshare/tushare/efinance/qstock）
    :param code: 股票代码
    :param market: 市场（SH/SZ）
    :param start_date：开始日期
    :param end_date：结束日期
    :param fields: 返回字段
    :param page: 页码
    :param page_size: 每页数量
    :return: 标准化格式的股票历史数据
    """
    debug_data_provider("获取股票历史记录", {
        "source": source, 
        "code": code, 
        "market": market, 
        "start_date": start_date, 
        "end_date": end_date, 
        "fields": fields, 
        "page": page, 
        "page_size": page_size
    })

    try:
        # 1.调用接口
        data_provider = get_data_provider(source)
        df = data_provider.get_stock_history(source=source, code=code, market=market, start_date=start_date, end_date=end_date)
        
        # 2.判空处理
        if df.empty:
            logger.warning(f"[Service]无数据返回 {source} for {code}.{market}")
            return {"status": "error", "message": "未查询到数据"}
        
        # 3.使用标准化数据处理器进行字段标准化和处理
        try:
            result = DataProcessor.process_stock_history_data(
                df, source, use_chinese=True, core_only=False, fields=fields
            )
            
            df_processed = result["data"]
            available_fields = result["available_fields"]
            
            # 数据处理后的结果
            debug_data_provider("处理后数据", {
                "处理后列名": df_processed.columns.tolist(),
                "可用标准字段": available_fields
            }, horizontal_output=True, show_full_content=True)
            
        except ValueError as e:
            logger.error(f"[Service]字段处理失败: {e}")
            return {"status": "error", "message": str(e)}
        
        # 4.应用分页处理+补充字段
        result_data = DataProcessor.apply_pagination(df_processed, page, page_size)
        result_data["symbol"] = f"{code}.{market}"
        result_data["date_range"] = f"{start_date} to {end_date}" if start_date and end_date else "latest"
        result_data["available_fields"] = available_fields
        return {
            "status": "success",
            "data": result_data,
            "message": "股票历史数据获取成功"
        }
        
    except Exception as e:
        logger.error(f"[Data]获取股票历史行情数据失败: {e}")
        return {"status": "error", "message": f"获取失败：{e}"}

# 1.3.1 获取股票实时数据（标准化流程）
def get_realtime_quotes(source="akshare", codes=None, fields=None, page=None, page_size=20):
    """
    获取股票实时行情
    :param source: 数据源名称
    :param codes: 股票代码列表(逗号分隔)
    :param fields: 指定返回字段
    :param page: 页码
    :param page_size: 每页数量
    :return: 实时行情数据
    """
    debug_data_provider("获取实时行情", {"source": source, "codes": codes})
    try:
        # 1.调用数据提供者获取原始数据
        data_provider = get_data_provider(source)
        df = data_provider.get_realtime_quotes(source=source, codes=codes)

        # 2.判空处理
        if df.empty:
            logger.warning(f"[Service]无数据返回 {source} for codes={codes}")
            return {"status": "error", "message": "未查询到数据"}
        
        # 3.使用标准化数据处理器进行字段标准化和处理
        try:
            result = DataProcessor.process_realtime_quotes_data(
                df, source, use_chinese=True, core_only=True, fields=fields
            )
            df_processed = result["data"]
            available_fields = result["available_fields"]
            
            # 数据处理后的结果
            debug_data_provider("处理后数据", {
                "处理后列名": df_processed.columns.tolist(),
                "可用标准字段": available_fields
            }, horizontal_output=True, show_full_content=True)
            
        except ValueError as e:
            logger.error(f"[Service]字段处理失败: {e}")
            return {"status": "error", "message": str(e)}
        
        # 4.应用分页处理+补充字段
        result_data = DataProcessor.apply_pagination(df_processed, page, page_size)
        result_data["available_fields"] = available_fields
        
        return {
            "status": "success",
            "data": result_data,
            "message": "实时行情数据获取成功"
        }
        
    except Exception as e:
        logger.error(f"[Service]获取实时行情失败: {e}")
        return {"status": "error", "message": f"获取失败：{e}"}

# 二、数据服务层-基本面数据
# 2.1 获取宏观数据（标准化流程）
def get_indicator_description(indicator):
    """
    获取指标描述
    """
    descriptions = {
        "GDP": "国内生产总值，反映一个国家或地区经济总量",
        "CPI": "消费者价格指数，反映消费品和服务价格变动",
        "PPI": "生产者价格指数，反映生产环节价格变动",
        "PMI": "采购经理指数，反映制造业和服务业景气程度"
    }
    return descriptions.get(indicator.upper(), f"{indicator}相关经济指标")
def get_macro_data(source="akshare", indicator="GDP", start_date=None, end_date=None, fields=None, page=None, page_size=20):
    """
    获取宏观经济数据
    :param source: 数据源名称
    :param indicator: 指标名称(GDP/CPI/PPI/PMI等)
    :param start_date: 开始日期
    :param end_date: 结束日期
    :param fields: 字段过滤
    :param page: 页码
    :param page_size: 每页数量
    :return: 标准化后的宏观经济数据
    """
    debug_data_provider("获取宏观经济数据", {
        "indicator": indicator,
        "source": source,
        "start_date": start_date,
        "end_date": end_date
    })
    try:
        # 1.调用接口
        data_provider = get_data_provider(source)
        if indicator.upper() == "GDP":
            df = data_provider.get_macro_gdp_data(source=source)
        elif indicator.upper() == "CPI":
            df = data_provider.get_macro_cpi_data(source=source)
        elif indicator.upper() == "PPI":
            df = data_provider.get_macro_ppi_data(source=source)
        elif indicator.upper() == "PMI":
            df = data_provider.get_macro_pmi_data(source=source)
        else:
            return {"status": "error", "message": f"暂不支持指标: {indicator}"}

        # 2.判空处理
        if df.empty:
            logger.warning(f"[Service]无数据返回 {source} for indicator={indicator}")
            return {"status": "error", "message": f"未查询到指标 '{indicator}' 的数据"}

        # 3.使用标准化数据处理器进行字段标准化和处理
        try:
            result = DataProcessor.process_macro_data(
                df, source, indicator, start_date, end_date, 
                use_chinese=True, core_only=True, fields=fields
            )
            df_processed = result["data"]
            available_fields = result["available_fields"]
            
            # 数据处理后的结果
            debug_data_provider("处理后数据", {
                "处理后列名": df_processed.columns.tolist(),
                "可用标准字段": available_fields
            }, horizontal_output=True, show_full_content=True)
            
        except ValueError as e:
            logger.error(f"[Service]字段处理失败: {e}")
            return {"status": "error", "message": str(e)}

        # 4.应用分页处理+字段补充
        result_data = DataProcessor.apply_pagination(df_processed, page, page_size)
        result_data["indicator_info"] = {
            "indicator": str(indicator.upper()),
            "description": str(get_indicator_description(indicator))
        }
        result_data["available_fields"] = available_fields
        
        return {
            "status": "success",
            "data": result_data,
            "message": "宏观经济数据获取成功"
        }
            
    except Exception as e:
        logger.error(f"[Service]获取宏观经济数据失败: {e}")
        return {"status": "error", "message": f"获取失败: {str(e)}"}

# 2.2 获取财务数据（标准化流程）——FINACIAL_REPORT 类型事件
def get_financial_report(source="akshare", code="000001", market=None, report_type=None, fields=None, page=None, page_size=20, use_chinese=True, core_only=True):
    """
    获取财务数据
    :param source: 数据源
    :param code: 股票代码
    :param market: 市场代码（可选）
    :param report_type: 报告类型 (annual/quarterly/semi_annual)
    :param fields: 返回字段,逗号分隔
    :param page: 页码
    :param page_size: 每页数量
    :return: 财务数据
    """
    debug_data_provider("获取财务数据", {
        "code": code,
        "source": source,
        "market": market,
        "report_type": report_type
    })
    try:
        # 处理股票代码格式
        if market:
            # 如果提供了市场代码，直接拼接
            symbol = f"{market}{code}"
        else:
            # 自动识别市场（简单规则）
            if code.startswith('6'):
                symbol = f"SH{code}"  # 上海证券交易所
            elif code.startswith(('0', '3')):
                symbol = f"SZ{code}"  # 深圳证券交易所
            else:
                # 如果已经包含前缀，直接使用
                if code.startswith(('SH', 'SZ')):
                    symbol = code
                else:
                    raise ValueError(f"无法识别股票代码格式: {code}")
        logger.info(f"[Provider]转换后的symbol: {symbol}")
        # 1.调用接口
        data_provider = get_data_provider(source)
        df = data_provider.get_financial_report(code=symbol)
        
        # 2.判空处理
        if df.empty:
            logger.warning(f"[Service]无数据返回 {source} for code={code}")
            return {"status": "error", "message": f"未查询到股票 '{code}' 的财务数据"}
        
        # 3.使用标准化数据处理器进行字段标准化和处理
        try:
            result = DataProcessor.process_financial_data(
                df, source, use_chinese=True, core_only=True, fields=fields,
                report_type=report_type
            )
            df_processed = result["data"]
            available_fields = result["available_fields"]
            
            logger.info(f"[Service]处理的列名: {df_processed.columns.tolist()}")
            logger.info(f"[Service]可用标准字段: {available_fields}")
        except ValueError as e:
            logger.error(f"[Service]字段处理失败: {e}")
            return {"status": "error", "message": str(e)}
        
        # 4.应用分页处理+补充字段
        result_data = DataProcessor.apply_pagination(df_processed, page, page_size)
        result_data["available_fields"] = available_fields
        return {
            "status": "success",
            "data": result_data,
            "message": "财务数据获取成功"
        }
            
    except Exception as e:
        logger.error(f"[Data]获取财务数据失败: {e}")
        return {"status": "error", "message": f"获取失败：{e}"}

# 三、数据服务层--资金流与订单流
# 3.1 获取资金流向数据（标准化流程）——MARKET_SENTIMENT 类型事件
def get_stock_fund_flow(source="akshare", code="000001", indicator="今日", fields=None, page=None, page_size=20):
    """
    获取股票资金流向数据
    :param source: 数据源
    :param code: 股票代码
    :param indicator: 时间周期（"今日", "3日", "5日", "10日"）
    :param fields: 返回字段,逗号分隔
    :param page: 页码
    :param page_size: 每页数量
    :return: 股票资金流向数据
    """
    debug_data_provider("获取资金流向数据", {
        "code": code,
        "source": source,
        "indicator": indicator
    })
    try:
        # 1.调用接口
        data_provider = get_data_provider(source)
        df = data_provider.get_stock_fund_flow(code=code, indicator=indicator)
        
        # 2.判空处理
        if df.empty:
            logger.warning(f"[Service]无数据返回 {source} for code={code}")
            return {"status": "error", "message": f"未查询到股票 '{code}' 的资金流向数据"}
        
        # 3.使用标准化数据处理器进行字段标准化和处理
        try:
            result = DataProcessor.process_fund_flow_data(
                df, source, use_chinese=True, core_only=False, fields=fields
            )
            
            df_processed = result["data"]
            available_fields = result["available_fields"]
            
            logger.info(f"[Service]处理的列名: {df_processed.columns.tolist()}")
            logger.info(f"[Service]可用标准字段: {available_fields}")
        except ValueError as e:
            logger.error(f"[Service]字段处理失败: {e}")
            return {"status": "error", "message": str(e)}
        
        # 4.应用分页处理+补充字段
        result_data = DataProcessor.apply_pagination(df_processed, page, page_size)
        result_data["symbol"] = code
        result_data["indicator"] = indicator
        result_data["available_fields"] = available_fields
        return {
            "status": "success",
            "data": result_data,
            "message": "资金流向数据获取成功"
        }
            
    except Exception as e:
        logger.error(f"[Data]获取资金流向数据失败: {e}")
        return {"status": "error", "message": f"获取失败：{e}"}

# 3.2 获取龙虎榜数据（标准化流程）——INSIDER_TRADING 类型事件
def get_dragon_tiger_list(source="akshare", start_date=None, end_date=None, fields=None, page=None, page_size=20):
    """
    获取龙虎榜数据
    """
    debug_data_provider("获取龙虎榜数据", {
        "source": source,
        "start_date": start_date,
        "end_date": end_date,
        "fields": fields
    })
    try:
        # 1.调用接口
        data_provider = get_data_provider(source)
        df = data_provider.get_dragon_tiger_list(start_date=start_date, end_date=end_date)
        
        # 2.判空处理
        if df.empty:
            logger.warning(f"[Service]无数据返回 {source} for date range={start_date} to {end_date}")
            return {"status": "error", "message": f"未查询到日期范围 '{start_date}' 到 '{end_date}' 的龙虎榜数据"}
        
        # 3.使用标准化数据处理器进行字段标准化和处理
        try:
            result = DataProcessor.process_dragon_tiger_data(
                df, source, use_chinese=True, core_only=False, fields=fields
            )
            df_processed = result["data"]
            available_fields = result["available_fields"]
            
            logger.info(f"[Service]处理的列名: {df_processed.columns.tolist()}")
            logger.info(f"[Service]可用标准字段: {available_fields}")
        except ValueError as e:
            logger.error(f"[Service]字段处理失败: {e}")
            return {"status": "error", "message": str(e)}
        
        # 4.应用分页处理+补充字段
        result_data = DataProcessor.apply_pagination(df_processed, page, page_size)
        result_data["date_range"] = f"{start_date} to {end_date}"
        result_data["available_fields"] = available_fields
        return {
            "status": "success",
            "data": result_data,
            "message": "龙虎榜数据获取成功"
        }
            
    except Exception as e:
        logger.error(f"[Data]获取龙虎榜数据失败: {e}")
        return {"status": "error", "message": f"获取失败：{e}"}

# 四、数据服务层-财务新闻、市场情绪、行业动态
# 4.1 获取财务新闻数据（标准化流程）——NEWS 类型事件
def get_news_sentiment(source="akshare", symbol=None, start_date=None, end_date=None, fields=None, page=None, page_size=20):
    """
    获取新闻情感数据
    """
    debug_data_provider("获取新闻情感数据", {
        "symbol": symbol,
        "source": source,
        "start_date": start_date,
        "end_date": end_date
    })
    try:
        # 1.调用接口
        data_provider = get_data_provider(source)
        df = data_provider.get_news_sentiment(symbol=symbol, start_date=start_date, end_date=end_date)
        
        # 2.判空处理
        if df.empty:
            logger.warning(f"[Service]无数据返回 {source} for symbol={symbol}")
            return {"status": "error", "message": f"未查询到股票 '{symbol}' 的新闻数据"}
        # 添加调试信息
        # debug_dataframe(df, "[Debug-1] 原始数据")
        # 2.情感分析处理（在字段处理前）
        if '新闻标题' in df.columns and '新闻内容' in df.columns:
            try:
                from snownlp import SnowNLP
                import jieba.analyse
                df['情感得分'] = df.apply(lambda row: 
                    SnowNLP(str(row['新闻标题']) + str(row['新闻内容'])).sentiments, axis=1)
                df['关键词'] = df.apply(lambda row: 
                    jieba.analyse.extract_tags(str(row['新闻标题']) + str(row['新闻内容']), topK=5), axis=1)
                # 修复：添加安全的标量值检查
                def classify_sentiment(score):
                    try:
                        # 确保score是标量值
                        if hasattr(score, '__len__') and not isinstance(score, str):
                            score = score[0] if len(score) > 0 else 0.5
                        score = float(score)
                        return '正面' if score > 0.6 else '负面' if score < 0.4 else '中性'
                    except (ValueError, TypeError, IndexError):
                        return '中性'
                df['情感分类'] = df['情感得分'].apply(classify_sentiment)
                
            except ImportError:
                logger.warning("[Service]缺少情感分析依赖包，跳过情感分析")
        # 3.使用新的数据处理器进行字段标准化和处理
        try:
            result = DataProcessor.process_news_data(
                df, source, use_chinese=True, core_only=False, fields=fields
            )
            
            df_processed = result["data"]
            available_fields = result["available_fields"]
            
            logger.info(f"[Service]处理的列名: {df_processed.columns.tolist()}")
            logger.info(f"[Service]可用标准字段: {available_fields}")
        except ValueError as e:
            logger.error(f"[Service]字段处理失败: {e}")
            return {"status": "error", "message": str(e)}
        
        # 4.应用分页处理
        result_data = DataProcessor.apply_pagination(df_processed, page, page_size)
        result_data["symbol"] = symbol
        result_data["date_range"] = f"{start_date} to {end_date}" if start_date and end_date else "latest"
        result_data["available_fields"] = available_fields
        return {
            "status": "success",
            "data": result_data,
            "message": "新闻情感数据获取成功"
        }
            
    except Exception as e:
        logger.error(f"[Data]获取新闻情感数据失败: {e}")
        return {"status": "error", "message": f"获取失败：{e}"}