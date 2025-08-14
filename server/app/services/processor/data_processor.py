"""
多数据源数据处理器
"""
from math import log
import pandas as pd
from app.config.field_mappings import (
    DATA_SOURCE_MAPPINGS, 
    STANDARD_FIELDS, 
    CORE_FIELDS
)
from core.logger import logger
from common.utils import safe_convert_to_dict

class DataProcessor:
    # 获取数据源映射
    @staticmethod
    def _get_source_mapping(source, data_type):
        """
        获取数据源映射配置
        :param source: 数据源名称
        :param data_type: 数据类型
        :return: 映射配置字典
        """
        source_mapping = DATA_SOURCE_MAPPINGS.get(source, {}).get(data_type, {})
        if not source_mapping:
            logger.warning(f"未找到数据源 {source} 的{data_type}字段映射配置")
        return source_mapping
    
    # 标准化字段
    @staticmethod
    def _standardize_fields(df, source_mapping):
        """
        字段标准化
        :param df: 原始DataFrame
        :param source_mapping: 字段映射配置
        :return: 标准化后的DataFrame
        """
        return df.rename(columns=source_mapping)
    # 字段过滤
    @staticmethod
    def _filter_fields(df, data_type, core_only=False, fields=None, use_chinese=True):
        """
        字段过滤
        :param df: 标准化后的DataFrame
        :param data_type: 数据类型
        :param core_only: 是否只返回核心字段
        :param fields: 指定返回字段
        :param use_chinese: 是否使用中文字段名（用于字段名转换）
        :return: 过滤后的DataFrame
        """
        logger.info(f"[_filter_fields] 输入参数 - data_type: {data_type}, core_only: {core_only}, fields: {fields}, use_chinese: {use_chinese}")
        logger.info(f"[_filter_fields] DataFrame列名: {list(df.columns)}")
        
        # 优先处理自定义fields的情况
        if fields:
            # 指定字段过滤
            field_list = [f.strip() for f in fields.split(',')]
            logger.info(f"[_filter_fields] 指定字段列表: {field_list}")
            
            available_fields = [f for f in field_list if f in df.columns]
            logger.info(f"[_filter_fields] 匹配到的字段: {available_fields}")
            if available_fields:
                logger.info(f"[_filter_fields] 返回指定字段: {available_fields}")
                return df[available_fields]
            else:
                logger.warning(f"[_filter_fields] 指定字段 {field_list} 在DataFrame中未找到，fallback到核心字段")
                # 如果没有匹配的字段，返回核心字段
                available_core_fields = [f for f in CORE_FIELDS.get(data_type, []) if f in df.columns]
                logger.info(f"[_filter_fields] fallback核心字段: {available_core_fields}")
                if available_core_fields:
                    return df[available_core_fields]
        elif core_only:
            # 只有在没有指定 fields 时才考虑 core_only
            available_core_fields = [f for f in CORE_FIELDS.get(data_type, []) if f in df.columns]
            logger.info(f"[_filter_fields] 核心字段: {CORE_FIELDS.get(data_type, [])}")
            logger.info(f"[_filter_fields] 可用核心字段: {available_core_fields}")
            if available_core_fields:
                return df[available_core_fields]
        logger.info(f"[_filter_fields] 返回原始DataFrame")
        return df
    # 中文化处理    
    @staticmethod
    def _apply_chinese_mapping(df, use_chinese=True):
        """
        中文化处理
        :param df: DataFrame
        :param use_chinese: 是否使用中文字段名
        :return: 处理后的DataFrame
        """
        if use_chinese:
            chinese_mapping = {k: STANDARD_FIELDS.get(k, k) for k in df.columns}
            return df.rename(columns=chinese_mapping)
        return df
    # 通用数据处理流程    
    @staticmethod
    def _process_data_common(df, source, data_type, use_chinese=True, core_only=False, fields=None, custom_processor=None):
        """
        通用数据处理流程
        :param df: 原始数据DataFrame
        :param source: 数据源名称
        :param data_type: 数据类型
        :param use_chinese: 是否使用中文字段名
        :param core_only: 是否只返回核心字段
        :param fields: 指定返回字段
        :param custom_processor: 自定义处理函数
        :return: 处理后的DataFrame 或 包含数据和元数据的字典
        """
        # 空数据检查
        if df.empty:
            return {"data": df, "available_fields": []}
        
        # 1. 获取数据源映射配置
        source_mapping = DataProcessor._get_source_mapping(source, data_type)
        # logger.debug(f"Source mapping: {source_mapping}")
        if not source_mapping:
            return {"data": df, "available_fields": list(df.columns)}
        
        # 2. 字段标准化
        df_standardized = DataProcessor._standardize_fields(df, source_mapping)
        
        # 记录标准化后的字段列表（英文标准字段名）->只返回标准映射的字段列表
        # standardized_fields = list(df_standardized.columns)
        standardized_fields = list(source_mapping.values()) 

        # 3. 自定义处理（如日期格式化、报告类型过滤等）
        if custom_processor:
            df_standardized = custom_processor(df_standardized)
        
        # 4. 字段过滤
        df_filtered = DataProcessor._filter_fields(
            df_standardized, data_type, core_only, fields, use_chinese
        )
        
        # 5. 中文化处理
        df_result = DataProcessor._apply_chinese_mapping(df_filtered, use_chinese)
        
        # 统一返回字典格式
        return {
            "data": df_result,
            "available_fields": standardized_fields
        }
    # 1.1.1 处理股票列表数据
    @staticmethod
    def process_stock_list_data(df, source, use_chinese=True, core_only=False, fields=None):
        """
        处理股票列表数据
        :param df: 原始数据DataFrame
        :param source: 数据源名称
        :param use_chinese: 是否使用中文字段名
        :param core_only: 是否只返回核心字段
        :param fields: 指定返回字段
        :return: 处理后的DataFrame
        """
        # def validate_required_fields(df_standardized):
        #     # 验证必需字段
        #     required_fields = ['symbol_code', 'symbol_name']
        #     missing_fields = [f for f in required_fields if f not in df_standardized.columns]
        #     if missing_fields:
        #         logger.error(f"缺少必需字段: {missing_fields}")
        #         raise ValueError(f"缺少必需字段: {missing_fields}")
        #     return df_standardized
        def add_debug_logging(df_standardized):
            logger.info(f"[Processor]使用中文字段: {use_chinese}，使用核心字段：{core_only}，使用指定字段：{fields}")
            return df_standardized
        return DataProcessor._process_data_common(
            df, source, 'stock_list', use_chinese, core_only, fields, add_debug_logging)
    
    # 1.1.2 处理概念板块数据
    @staticmethod
    def process_concept_data(df, source, use_chinese=True, core_only=False, fields=None):
        """
        处理概念板块数据
        """
        return DataProcessor._process_data_common(
            df, source, 'concept_data', use_chinese, core_only, fields)

     # 1.1.3 处理概念成分股数据
    
    # 1.1.3 处理概念成分股数据
    @staticmethod
    def process_concept_constituent_stocks_data(df, source, use_chinese=True, core_only=False, fields=None):
        """
        处理概念成分股数据
        """
        return DataProcessor._process_data_common(
            df, source, 'concept_constituent_stocks', use_chinese, core_only, fields) 
    
    # 1.2.1 处理股票历史数据
    @staticmethod
    def process_stock_history_data(df, source, use_chinese=True, core_only=False, fields=None):
        """
        处理股票历史数据
        """
        def format_date(df_standardized):
            # 日期格式化
            if 'date' in df_standardized.columns:
                df_standardized['date'] = pd.to_datetime(df_standardized['date']).dt.strftime('%Y-%m-%d')
            return df_standardized
        
        return DataProcessor._process_data_common(
            df, source, 'stock_history', use_chinese, core_only, fields, format_date
        )
    
    # 1.3.1 处理实时行情数据
    @staticmethod
    def process_realtime_quotes_data(df, source, use_chinese=True, core_only=False, fields=None):
        """
        处理实时行情数据
        """
        return DataProcessor._process_data_common(
            df, source, 'realtime_quotes', use_chinese, core_only, fields)
    
    # 2.1 处理宏观经济数据
    @staticmethod
    def process_macro_data(df, source, indicator, start_date, end_date, use_chinese=True, core_only=False, fields=None):

        """
        处理宏观经济数据
        :param df: 原始数据DataFrame
        :param source: 数据源名称
        :param indicator: 指标类型
        :param use_chinese: 是否使用中文字段名
        :param core_only: 是否只返回核心字段
        :param fields: 指定返回字段
        :return: 处理后的DataFrame
        """
        def macro_custom_processor(df_standardized):
            # 1. 日期格式化
            date_columns = ['date', 'period', 'month']
            date_col = None
            for col in date_columns:
                if col in df_standardized.columns:
                    date_col = col
                    df_standardized[col] = pd.to_datetime(df_standardized[col], errors='coerce')
                    break
            
            # 2. 日期过滤
            if date_col and (start_date or end_date):
                if start_date:
                    start_dt = pd.to_datetime(start_date)
                    df_standardized = df_standardized[df_standardized[date_col] >= start_dt]
                if end_date:
                    end_dt = pd.to_datetime(end_date)
                    df_standardized = df_standardized[df_standardized[date_col] <= end_dt]
            
            # 3. 排序（按日期倒序）
            if date_col and date_col in df_standardized.columns:
                df_standardized = df_standardized.sort_values(date_col, ascending=False, na_position='last')
            
            return df_standardized
        # 根据indicator选择对应的数据类型
        data_type = f'macro_{indicator.lower()}'
        return DataProcessor._process_data_common(
            df, source, data_type, use_chinese, core_only, fields, macro_custom_processor
        )

    # 2.2 处理财务报告数据
    @staticmethod
    def process_financial_data(df, source, use_chinese=True, core_only=False, fields=None, report_type=None):
        """
        处理财务数据
        :param df: 原始数据DataFrame
        :param source: 数据源名称
        :param use_chinese: 是否使用中文字段名
        :param core_only: 是否只返回核心字段
        :param fields: 指定返回字段
        :param report_type: 报告类型（annual, quarterly, semi_annual, third_quarter）
        :return: 处理后的DataFrame
        """
        def filter_report_type(df_standardized):
            # 报告类型过滤
            if report_type and 'report_type' in df_standardized.columns:
                from app.config.field_mappings import REPORT_TYPE_MAPPING
                
                target_report_type = REPORT_TYPE_MAPPING.get(report_type)
                if target_report_type:
                    # 筛选指定报告类型的数据
                    df_filtered = df_standardized[df_standardized['report_type'] == target_report_type]
                    if df_filtered.empty:
                        logger.warning(f"未找到 {target_report_type} 类型的财务数据")
                        return pd.DataFrame()
                    logger.info(f"[Processor]按报告类型 '{target_report_type}' 过滤后，剩余 {len(df_filtered)} 条记录")
                    return df_filtered
                else:
                    logger.warning(f"[Processor]不支持的报告类型: {report_type}")
            return df_standardized
        
        return DataProcessor._process_data_common(
            df, source, 'financial_report', use_chinese, core_only, fields, filter_report_type)
    
    # 3.1 处理资金流向数据
    @staticmethod
    def process_fund_flow_data(df, source, use_chinese=True, core_only=False, fields=None):
        """
        处理资金流向数据
        """
        return DataProcessor._process_data_common(
            df, source, 'fund_flow', use_chinese, core_only, fields)
    
    # 3.2 处理龙虎榜数据
    @staticmethod
    def process_dragon_tiger_data(df, source, use_chinese=True, core_only=False, fields=None):
        """
        处理龙虎榜数据
        """
        def add_debug_logging(df_standardized):
            logger.info(f"[Processor]使用中文字段: {use_chinese}，使用核心字段：{core_only}，使用指定字段：{fields}")
            return df_standardized
        
        return DataProcessor._process_data_common(
            df, source, 'dragon_tiger', use_chinese, core_only, fields, add_debug_logging)
    
    # 4.1 处理财务新闻数据
    @staticmethod
    def process_news_data(df, source, use_chinese=True, core_only=False, fields=None):
        """
        处理新闻数据
        """
        return DataProcessor._process_data_common(
            df, source, 'news_sentiment', use_chinese, core_only, fields)
    
    @staticmethod
    def get_available_fields(source, data_type):
        """
        获取指定数据源和数据类型的可用字段
        :param source: 数据源名称
        :param data_type: 数据类型（financial_report, fund_flow等）
        :return: 可用字段列表
        """
        mapping = DATA_SOURCE_MAPPINGS.get(source, {}).get(data_type, {})
        return list(mapping.values())  # 返回标准字段名列表
    
    @staticmethod
    def apply_pagination(df, page=None, page_size=20):
        """
        应用分页处理
        :param df: DataFrame
        :param page: 页码
        :param page_size: 每页数量
        :return: 分页结果字典
        """
        total_records = len(df)
        
        if page is not None and page_size is not None:
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paged_df = df.iloc[start_idx:end_idx]
            
            return {
                "list": safe_convert_to_dict(paged_df),
                "pagination": {
                    "total": total_records,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total_records + page_size - 1) // page_size,
                    "has_next": page * page_size < total_records,
                    "has_prev": page > 1
                }
            }
        else:
            return {
                "list": safe_convert_to_dict(df),
                "pagination": {
                    "total": total_records,
                    "page": 1,
                    "page_size": total_records,
                    "total_pages": 1,
                    "has_next": False,
                    "has_prev": False
                }
            }