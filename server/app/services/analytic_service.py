from core.logger import logger
from data_providers import get_data_provider
from common.utils import clean_numeric_data, safe_convert_to_dict, debug_dataframe
import pandas as pd
import numpy as np
import datetime

# 技术指标计算
def calculate_moving_averages(df, periods=[5, 10, 20, 60]):
    """
    计算移动平均线
    :param df: 包含价格数据的DataFrame
    :param periods: 移动平均周期列表
    :return: 包含移动平均线的DataFrame
    """
    logger.info(f"[Analytics]计算移动平均线，周期: {periods}")
    try:
        result_df = df.copy()
        
        for period in periods:
            if 'close' in df.columns:
                result_df[f'MA{period}'] = df['close'].rolling(window=period).mean()
            elif '收盘' in df.columns:
                result_df[f'MA{period}'] = df['收盘'].rolling(window=period).mean()
            else:
                logger.warning("[Analytics]未找到收盘价列")
                return {"status": "error", "message": "未找到收盘价数据"}
        
        # 清理数据
        cleaned_data = clean_numeric_data(result_df)
        data_dict = safe_convert_to_dict(cleaned_data)
        
        return {
            "status": "success",
            "data": data_dict,
            "message": "移动平均线计算完成"
        }
    except Exception as e:
        logger.error(f"[Analytics]计算移动平均线失败: {e}")
        return {"status": "error", "message": f"计算失败: {e}"}

def calculate_macd(df, fast=12, slow=26, signal=9):
    """
    计算MACD指标
    :param df: 包含价格数据的DataFrame
    :param fast: 快线周期
    :param slow: 慢线周期
    :param signal: 信号线周期
    :return: 包含MACD指标的数据
    """
    logger.info(f"[Analytics]计算MACD指标，参数: {fast}, {slow}, {signal}")
    try:
        result_df = df.copy()
        
        # 确定收盘价列名
        close_col = 'close' if 'close' in df.columns else '收盘'
        if close_col not in df.columns:
            return {"status": "error", "message": "未找到收盘价数据"}
        
        # 计算MACD
        exp1 = df[close_col].ewm(span=fast).mean()
        exp2 = df[close_col].ewm(span=slow).mean()
        result_df['MACD'] = exp1 - exp2
        result_df['Signal'] = result_df['MACD'].ewm(span=signal).mean()
        result_df['Histogram'] = result_df['MACD'] - result_df['Signal']
        
        # 清理数据
        cleaned_data = clean_numeric_data(result_df)
        data_dict = safe_convert_to_dict(cleaned_data)
        
        return {
            "status": "success",
            "data": data_dict,
            "message": "MACD指标计算完成"
        }
    except Exception as e:
        logger.error(f"[Analytics]计算MACD失败: {e}")
        return {"status": "error", "message": f"计算失败: {e}"}

def calculate_rsi(df, period=14):
    """
    计算RSI指标
    :param df: 包含价格数据的DataFrame
    :param period: RSI周期
    :return: 包含RSI指标的数据
    """
    logger.info(f"[Analytics]计算RSI指标，周期: {period}")
    try:
        result_df = df.copy()
        
        # 确定收盘价列名
        close_col = 'close' if 'close' in df.columns else '收盘'
        if close_col not in df.columns:
            return {"status": "error", "message": "未找到收盘价数据"}
        
        # 计算RSI
        delta = df[close_col].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        result_df['RSI'] = 100 - (100 / (1 + rs))
        
        # 清理数据
        cleaned_data = clean_numeric_data(result_df)
        data_dict = safe_convert_to_dict(cleaned_data)
        
        return {
            "status": "success",
            "data": data_dict,
            "message": "RSI指标计算完成"
        }
    except Exception as e:
        logger.error(f"[Analytics]计算RSI失败: {e}")
        return {"status": "error", "message": f"计算失败: {e}"}

def calculate_bollinger_bands(df, period=20, std_dev=2):
    """
    计算布林带指标
    :param df: 包含价格数据的DataFrame
    :param period: 移动平均周期
    :param std_dev: 标准差倍数
    :return: 包含布林带指标的数据
    """
    logger.info(f"[Analytics]计算布林带指标，周期: {period}, 标准差: {std_dev}")
    try:
        result_df = df.copy()
        
        # 确定收盘价列名
        close_col = 'close' if 'close' in df.columns else '收盘'
        if close_col not in df.columns:
            return {"status": "error", "message": "未找到收盘价数据"}
        
        # 计算布林带
        result_df['BB_Middle'] = df[close_col].rolling(window=period).mean()
        bb_std = df[close_col].rolling(window=period).std()
        result_df['BB_Upper'] = result_df['BB_Middle'] + (bb_std * std_dev)
        result_df['BB_Lower'] = result_df['BB_Middle'] - (bb_std * std_dev)
        
        # 清理数据
        cleaned_data = clean_numeric_data(result_df)
        data_dict = safe_convert_to_dict(cleaned_data)
        
        return {
            "status": "success",
            "data": data_dict,
            "message": "布林带指标计算完成"
        }
    except Exception as e:
        logger.error(f"[Analytics]计算布林带失败: {e}")
        return {"status": "error", "message": f"计算失败: {e}"}

# 基本面分析
def calculate_financial_ratios(financial_data):
    """
    计算财务比率
    :param financial_data: 财务数据字典
    :return: 财务比率分析结果
    """
    logger.info("[Analytics]计算财务比率")
    try:
        ratios = {}
        
        # 盈利能力指标
        if 'net_income' in financial_data and 'revenue' in financial_data:
            ratios['net_profit_margin'] = financial_data['net_income'] / financial_data['revenue']
        
        if 'net_income' in financial_data and 'total_equity' in financial_data:
            ratios['roe'] = financial_data['net_income'] / financial_data['total_equity']
        
        if 'net_income' in financial_data and 'total_assets' in financial_data:
            ratios['roa'] = financial_data['net_income'] / financial_data['total_assets']
        
        # 偿债能力指标
        if 'current_assets' in financial_data and 'current_liabilities' in financial_data:
            ratios['current_ratio'] = financial_data['current_assets'] / financial_data['current_liabilities']
        
        if 'total_debt' in financial_data and 'total_equity' in financial_data:
            ratios['debt_to_equity'] = financial_data['total_debt'] / financial_data['total_equity']
        
        return {
            "status": "success",
            "data": ratios,
            "message": "财务比率计算完成"
        }
    except Exception as e:
        logger.error(f"[Analytics]计算财务比率失败: {e}")
        return {"status": "error", "message": f"计算失败: {e}"}