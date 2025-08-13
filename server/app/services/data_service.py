from core.logger import logger
from data_providers import get_data_provider
from common.utils import clean_numeric_data, safe_convert_to_dict, debug_dataframe
import pandas as pd
import numpy as np
import datetime
# 1.1 获取所有股票列表（已完成）
def get_all_stocks(source="akshare", market=None, fields=None, page=None, page_size=20 ):
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
    logger.info(f"[Bridge]获取所有股票 from {source}")
    try:
        # 0.调用接口
        data_provider = get_data_provider(source)
        df = data_provider.get_all_stocks(source=source, market=market)
        
        # 1.判空处理
        if df.empty:
            logger.warning(f"[Service]无数据返回 {source}")
            return {"status": 'error', "message": "未查询到数据"}
        
        # 2.标准化字段列名校验+重命名（左转右）+数据源支持校验+字段格式调整
        if source in ["akshare", "tushare", "juejinquant"]:
            required_columns = {
                'code': '代码',
                'name': '名称'
            }
        else:
            return {"status": 'error', "message": "不支持的数据源"}
        missing_cols = [col for col in required_columns.keys() if col not in df.columns]
        if missing_cols:
            logger.warning(f"[Service]缺少关键列 {source}: {', '.join(missing_cols)}")
            return {"status": 'error', "message": f"缺少关键列: {', '.join(missing_cols)}"}
        df.rename(columns=required_columns, inplace=True)
        
        # 3.传入列字段过滤
        if fields:
            field_list = [f.strip() for f in fields.split(',')]
            available_fields = [col for col in field_list if col in df.columns]
            if not available_fields:
                return {"status": "error", "message": "请求的字段不存在"}
            df = df[available_fields]
        else:
            df = df[['代码', '名称']]
            
        # 4.data处理，是否开启分页处理（统一处理始终返回list和pagination）
        total = len(df)
        if page is not None:
            # 分页模式
            start = (page - 1) * page_size
            end = start + page_size
            paged_df = df.iloc[start:end]
            data = {
                "list": paged_df.to_dict(orient='records'),
                "pagination": {
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "pages": (total + page_size - 1) // page_size
                }
            }
        else:
            data = {
                "list": df.to_dict(orient='records'),
                "pagination": {
                    "total": len(df),
                    "page": 1,
                    "page_size": len(df),
                    "pages": 1
                }
            }
        return {
            "status": 'success', 
            "data": data,
            "message": "Success"
        }
    except Exception as e:
        logger.error(f"[Service]获取所有股票失败: {e}")
        return {"status": 'error', "message": f"获取失败：{e}"}

# 1.2 获取所有概念板块列表（已完成）
def get_concept_stocks(source="akshare", fields=None, page=None, page_size=20):
    """
    获取概念板块成分股
    :param source: 数据源名称
    :param concept: 概念板块名称
    :return: 概念板块成分股列表
    """
    logger.info(f"[Bridge]获取概念板块成分股 from {source}")
    try:
        # 0.调用接口
        data_provider = get_data_provider(source)
        df = data_provider.get_all_concepts()

        # 1.判空处理
        if df.empty:
            logger.warning(f"[Service]无数据返回 {source}")
            return {"status": "error", "message": "未查询到数据"}

        # 2.标准化字段列名校验+重命名（左转右）+数据源支持校验+字段格式调整
        if source == "akshare":
            required_columns = {
                '板块代码': '板块代码',
                '板块名称': '板块名称'
            }
        else:
            return {"status": "error", "message": "不支持的数据源"}
        missing_cols = [col for col in required_columns.keys() if col not in df.columns]
        if missing_cols:
            logger.error(f"[Service]缺少字段: {missing_cols}")
            return {"status": "error", "message": f"数据缺少必要字段: {', '.join(missing_cols)}"}
        df.rename(columns=required_columns, inplace=True)
       
        # 3.传入列字段过滤
        if fields:
            field_list = [f.strip() for f in fields.split(',')]
            available_fields = [col for col in field_list if col in df.columns]
            if not available_fields:
                return {"status": "error", "message": "请求的字段不存在"}
            df = df[available_fields]
        else:
            df = df[['板块代码', '板块名称']]
         # 3.5 数据排序 - 按板块名称升序排列
        # 3.5 数据排序 = 按板块名称升序排列
        try:
            df = df.sort_values('板块名称', ascending=True, na_last=True)
            df = df.reset_index(drop=True)
        except Exception as e:
            logger.warning(f"[Service]排序失败，使用原始顺序: {e}")
        # 4.data处理，是否开启分页处理（统一处理始终返回list和pagination）
        total = len(df)
        if page is not None:
            # 分页模式
            start = (page - 1) * page_size
            end = start + page_size
            paged_df = df.iloc[start:end]
            data = {
                "list": paged_df.to_dict(orient='records'),
                "pagination": {
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "pages": (total + page_size - 1) // page_size
                }
            }
        else:
            # 非分页模式，但保持结构一致
            data = {
                "list": df.to_dict(orient='records'),
                "pagination": {
                    "total": total,
                    "page": 1,
                    "page_size": total,
                    "pages": 1
                }
            }

        return {
            "status": 'success', 
            "data": data,
            "message": "Success"
        }
    except Exception as e:
        logger.error(f"[Service]获取概念板块成分股失败: {e}")
        return {"status": "error", "message": f"获取失败: {e}"}

# 1.3 获取概念板块成分股（已完成）
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
    logger.info(f"[Bridge]获取概念板块成分股 from {source}, concept_identifier={concept_identifier}")
    
    if not concept_identifier:
        return {"status": "error", "message": "概念板块标识符不能为空"}
    
    try:
        # 0.调用接口
        data_provider = get_data_provider(source)
         # 获取板块信息
        concept_info = None
        if source == "akshare":
            # 获取所有概念板块列表，用于查找板块信息
            concept_list_df = data_provider.get_all_concepts()
            if concept_identifier in concept_list_df['板块代码'].values:
                # 通过板块代码查找
                concept_row = concept_list_df[concept_list_df['板块代码'] == concept_identifier].iloc[0]
                concept_info = {
                    "板块代码": str(concept_row['板块代码']),
                    "板块名称": str(concept_row['板块名称']),
                    "换手率": int(concept_row.get('换手率', 0)) if pd.notna(concept_row.get('换手率', 0)) else 0,
                    "涨跌幅": float(concept_row.get('涨跌幅', 0)) if pd.notna(concept_row.get('涨跌幅', 0)) else 0.0,
                    "上涨家数": int(concept_row.get('上涨家数', 0)) if pd.notna(concept_row.get('上涨家数', 0)) else 0,
                    "下跌家数": int(concept_row.get('下跌家数', 0)) if pd.notna(concept_row.get('下跌家数', 0)) else 0
                }
            elif concept_identifier in concept_list_df['板块名称'].values:
                # 通过板块名称查找
                concept_row = concept_list_df[concept_list_df['板块名称'] == concept_identifier].iloc[0]
                concept_info = {
                    "板块代码": str(concept_row['板块代码']),
                    "板块名称": str(concept_row['板块名称']),
                    "换手率": int(concept_row.get('换手率', 0)) if pd.notna(concept_row.get('换手率', 0)) else 0,
                    "涨跌幅": float(concept_row.get('涨跌幅', 0)) if pd.notna(concept_row.get('涨跌幅', 0)) else 0.0,
                    "上涨家数": int(concept_row.get('上涨家数', 0)) if pd.notna(concept_row.get('上涨家数', 0)) else 0,
                    "下跌家数": int(concept_row.get('下跌家数', 0)) if pd.notna(concept_row.get('下跌家数', 0)) else 0
                }
        df = data_provider.get_concept_constituent_stocks(concept_identifier=concept_identifier)
        # 1.判空处理
        if df.empty:
            logger.warning(f"[Service]无数据返回 {source} for concept={concept_identifier}")
            return {"status": "error", "message": f"未查询到概念板块 '{concept_identifier}' 的成分股数据"}

        # 2.标准化字段列名校验+重命名（左转右）+数据源支持校验+字段格式调整
        if source == "akshare":
            required_columns = {
                '代码': '代码',
                '名称': '名称',
                '最新价': '最新价',
                '涨跌幅': '涨跌幅',
                '涨跌额': '涨跌额',
                '成交量': '成交量',
                '成交额': '成交额',
                '振幅': '振幅',
                '最高': '最高价',
                '最低': '最低价',
                '今开': '开盘价',
                '昨收': '昨收价'
            }
        else:
            return {"status": "error", "message": "不支持的数据源"}
        
        missing_cols = [col for col in required_columns.keys() if col not in df.columns]
        if missing_cols:
            logger.error(f"[Service]缺少字段: {missing_cols}")
            return {"status": "error", "message": f"数据缺少必要字段: {', '.join(missing_cols)}"}
        df.rename(columns=required_columns, inplace=True)
        
        # 3.传入列字段过滤
        if fields:
            field_list = [f.strip() for f in fields.split(',')]
            available_fields = [col for col in field_list if col in df.columns]
            if not available_fields:
                return {"status": "error", "message": "请求的字段不存在"}
            df = df[available_fields]
        else:
            df = df[['代码', '名称', '最新价', '涨跌幅', '涨跌额', '成交量', '成交额', '振幅', '最高价', '最低价', '开盘价', '昨收价']]
        
        # 3.5 数据排序 - 按涨跌幅降序排列
        try:
            df = df.sort_values('涨跌幅', ascending=False, na_position='last')
            df = df.reset_index(drop=True)
        except Exception as e:
            logger.warning(f"[Service]排序失败，使用原始顺序: {e}")
        
        # 4.data处理，是否开启分页处理（统一处理始终返回list和pagination）
        total = len(df)
        if page is not None:
            # 分页模式
            start = (page - 1) * page_size
            end = start + page_size
            paged_df = df.iloc[start:end]
            data = {
                "concept_info": concept_info,
                "list": paged_df.to_dict(orient='records'),
                "pagination": {
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "pages": (total + page_size - 1) // page_size
                }
            }
        else:
            # 非分页模式，但保持结构一致
            data = {
                "concept_info": concept_info,
                "list": df.to_dict(orient='records'),
                "pagination": {
                    "total": total,
                    "page": 1,
                    "page_size": total,
                    "pages": 1
                }
            }

        return {
            "status": 'success', 
            "data": data,
            "message": "Success"
        }
    except ValueError as ve:
        logger.error(f"[Service]参数错误: {ve}")
        return {"status": "error", "message": str(ve)}
    except Exception as e:
        logger.error(f"[Service]获取概念板块成分股失败: {e}")
        return {"status": "error", "message": f"获取失败: {e}"}

# 2.1 获取股票历史记录（已完成）
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
    :return: DataFrame 包含 ['日期', 'close']
    """
    logger.info(f"[Bridge]获取股票历史行情数据并标准化输出格式 for {code}.{market} from {source}")
    try:
        # 0.调用接口
        data_provider = get_data_provider(source)
        df = data_provider.get_stock_history(source=source, code=code, market=market, start_date=start_date, end_date=end_date)
        
        # 1.判空处理
        if df.empty:
            logger.warning(f"[Service]无数据返回 {source} for {code}.{market}")
            return {"status": 'error', "message": "未查询到数据"}
        
        # 2.标准化字段列名校验+重命名（左转右）+数据源支持校验+字段格式调整
        if source == "akshare":
            required_columns = {
                '股票代码': '代码',
                '日期': '日期',
                '开盘': '开盘价',
                '收盘': '收盘价',
                '最高': '最高价',
                '最低': '最低价',
                '成交量': '成交量'
            }
        elif source == "tushare":
            required_columns = {
                'trade_date': '日期',
                'open': '开盘价',
                'close': '收盘价',
                'high': '最高价',
                'low': '最低价',
                'vol': '成交量'
            }
        elif source == "qstock":
            required_columns = {
                'date': '日期',
                'open': '开盘价',
                'close': '收盘价',
                'high': '最高价',
                'low': '最低价',
                'volume': '成交量'
            }
        elif source == "yfinance":
            required_columns = {
                'Date': '日期',
                'Open': '开盘价',
                'Close': '收盘价',
                'High': '最高价',
                'Low': '最低价',
                'Volume': '成交量'
            }
        else:
            return {"status": 'error', "message": "不支持的数据源"}
        missing_cols = [col for col in required_columns.keys() if col not in df.columns]
        if missing_cols:
            logger.warning(f"[Service]缺少关键列 {source}: {', '.join(missing_cols)}")
            return {"status": 'error', "message": f"缺少关键列: {', '.join(missing_cols)}"}
        df.rename(columns=required_columns, inplace=True)
        df['日期'] = pd.to_datetime(df['日期']).dt.strftime('%Y-%m-%d')
        
        # 3.传入列字段过滤
        if fields:
            field_list = [f.strip() for f in fields.split(',')]
            available_fields = [col for col in field_list if col in df.columns]
            if not available_fields:
                return {"status": "error", "message": "请求的字段不存在"}
            df = df[available_fields]
        else:
            df = df[['代码','日期', '开盘价', '收盘价', '最高价', '最低价', '成交量']]
        
        # 4.data处理，是否开启分页处理（统一处理始终返回list和pagination）
        total = len(df)
        if page is not None:
            # 分页模式
            start = (page - 1) * page_size
            end = start + page_size
            paged_df = df.iloc[start:end]
            data = {
                "list": paged_df.to_dict(orient='records'),
                "pagination": {
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "pages": (total + page_size - 1) // page_size
                }
            }
        else:
            data = {
                "list": df.to_dict(orient='records'),
                "pagination": {
                    "total": len(df),
                    "page": 1,
                    "page_size": len(df),
                    "pages": 1
                }
            }
        return {
            "status": 'success', 
            "data": data,
            "message": "Success"
        }
    except Exception as e:
        logger.error(f"[Service]获取股票历史行情数据失败: {e}")
        return {"status": 'error', "message": f"获取失败：{e}"}

# 3.1 获取股票实时数据（已完成）
def get_realtime_quotes(source="akshare", codes=None, fields=None,page=None, page_size=20):
    """
    获取股票实时行情
    :param source: 数据源名称
    :param codes: 股票代码列表(逗号分隔)
    :param page: 页码
    :param page_size: 每页数量
    :return: 实时行情数据
    """
    logger.info(f"[Bridge]获取实时行情 from {source}")
    try:
        # 0.调用接口 
        data_provider = get_data_provider(source)
        df = data_provider.get_realtime_quotes(source=source, codes=codes)

        # 1.判空处理
        if df.empty:
            logger.warning(f"[Service]无数据返回 {source} for codes={codes}")
            return {"status": "error", "message": "未查询到数据"}
        
        # 2.标准化字段列名校验+重命名（左转右）+数据源支持校验+字段格式调整
        if source == "akshare":
            required_columns = {
                '代码': '代码',
                '名称': '名称',
                '最新价': '最新价',
                '涨跌幅': '涨跌幅',
                '成交量': '成交量',
                '最高': '最高价',
                '最低': '最低价',
                '量比': '量比',
                '换手率': '换手率',
                '市盈率-动态': '市盈率',
                '市净率': '市净率',
                '总市值': '总市值',
                '流通市值': '流通市值'
            }
        else:
            return {"status": "error", "message": "不支持的数据源"}
        missing_cols = [col for col in required_columns.keys() if col not in df.columns]
        if missing_cols:
            logger.error(f"[Service]缺少字段: {missing_cols}")
            return {"status": "error", "message": f"数据缺少必要字段: {', '.join(missing_cols)}"}
        df.rename(columns=required_columns, inplace=True)
        
        # 3.传入列字段过滤
        if fields:
            field_list = [f.strip() for f in fields.split(',')]
            available_fields = [col for col in field_list if col in df.columns]
            if not available_fields:
                return {"status": "error", "message": "请求的字段不存在"}
            df = df[available_fields]
        else:
            df = df[['代码', '名称', '最新价', '涨跌幅', '成交量', 
            '最高价', '最低价', '量比', '换手率', '市盈率', '市净率', '总市值', '流通市值']]

        # 4.data处理，是否开启分页处理（统一处理始终返回list和pagination）
        total = len(df)
        if page is not None:
            # 分页模式
            start = (page - 1) * page_size
            end = start + page_size
            paged_df = df.iloc[start:end]
            data = {
                "list": paged_df.to_dict(orient='records'),
                "pagination": {
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "pages": (total + page_size - 1) // page_size
                }
            }
        else:
            # 非分页模式，但保持结构一致
            data = {
                "list": df.to_dict(orient='records'),
                "pagination": {
                    "total": total,
                    "page": 1,
                    "page_size": total,
                    "pages": 1
                }
            }
        return {
            "status": "success",
            "data": data,
            "message": "Success"
        }
    except Exception as e:
        logger.error(f"[Service]获取实时行情失败: {e}")
        return {"status": "error", "message": f"获取失败: {e}"}

# 4.1 获取宏观数据（已完成）
# 4.1.1 获取宏观数据概念描述
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
    logger.info(f"[Service]获取宏观经济数据 {indicator} from {source}")
    
    try:
        # 0.调用接口
        data_provider = get_data_provider(source)
        # 根据指标类型调用不同方法
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
        # 调试输出：查看原始数据
        # debug_dataframe(df)

        # 1.判空处理
        if df.empty:
            logger.warning(f"[Service]无数据返回 {source} for indicator={indicator}")
            return {"status": "error", "message": f"未查询到指标 '{indicator}' 的数据"}

        # 2.标准化字段列名校验+重命名（左转右）+数据源支持校验+字段格式调整
        if source == "akshare":
            # 根据不同指标进行字段标准化
            if indicator.upper() == "GDP":
                required_columns = {
                    '季度': '日期',
                    '国内生产总值-绝对值': '数值',
                    '国内生产总值-同比增长': '同比增长率'
                }
            elif indicator.upper() == "CPI":
                required_columns = {
                    '日期': '日期',
                    '今值': '当前值',
                    '预测值': '预测值',
                    '前值': '前值',
                    '商品': '商品类别'
                }
            elif indicator.upper() == "PPI":
                required_columns = {
                    '日期': '日期',
                    '今值': '当前值',
                    '预测值': '预测值',
                    '前值': '前值',
                    '商品': '商品类别'
                }
            elif indicator.upper() == "PMI":
                required_columns = {
                    '月份': '日期',
                    '制造业-指数': '制造业-指数',
                    '制造业-同比增长': '制造业-同比增长',
                    '非制造业-指数': '非制造业-指数',
                    '非制造业-同比增长': '非制造业-同比增长'
                }
            
            # 检查必需列是否存在
            missing_columns = [col for col in required_columns.keys() if col not in df.columns]
            if missing_columns:
                logger.warning(f"[Service]缺少必需列: {missing_columns}")
                # 使用原始列名
                available_columns = {col: col for col in df.columns}
                df = df.rename(columns=available_columns)
            else:
                df = df.rename(columns=required_columns)

        # 3.日期过滤
        if start_date or end_date:
            date_column = '日期'
            if date_column in df.columns:
                df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
                if start_date:
                    start_dt = pd.to_datetime(start_date)
                    df = df[df[date_column] >= start_dt]
                if end_date:
                    end_dt = pd.to_datetime(end_date)
                    df = df[df[date_column] <= end_dt]
        
        # 4.字段过滤
        if fields:
            field_list = [f.strip() for f in fields.split(',')]
            available_fields = [f for f in field_list if f in df.columns]
            if available_fields:
                df = df[available_fields]
            else:
                logger.warning(f"[Service]指定字段不存在: {field_list}")
        
        # 5.排序（按日期倒序）
        if '日期' in df.columns:
            df = df.sort_values('日期', ascending=False, na_position='last')
        
        # 6.分页处理
        total_count = len(df)
        if page is not None and page_size is not None:
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            df_page = df.iloc[start_idx:end_idx]
            data_list = safe_convert_to_dict(df_page)
            return {
                "status": "success",
                "message": f"成功获取{indicator}数据",
                "data": {
                    "indicator_info": {
                        "indicator": str(indicator.upper()),
                        "total_count": int(total_count),
                        "description": str(get_indicator_description(indicator))
                    },
                    "pagination": {
                        "page": int(page),
                        "page_size": int(page_size),
                        "total_count": int(total_count),
                        "total_pages": int((total_count + page_size - 1) // page_size)
                    },
                    "records": data_list
                }
            }
        else:
            return {
                "status": "success",
                "message": f"成功获取{indicator}数据",
                "data": {
                    "indicator_info": {
                        "indicator": str(indicator.upper()),
                        "total_count": int(total_count),
                        "description": str(get_indicator_description(indicator))
                    },
                    "records": data_list
                }
            }
            
    except Exception as e:
        logger.error(f"[Service]获取宏观经济数据失败: {e}")
        return {"status": "error", "message": f"获取失败: {str(e)}"}