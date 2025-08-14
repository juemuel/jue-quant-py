import pandas as pd
import numpy as np
import datetime
from core.logger import logger

# common/utils.py
# 业务单位处理
def format_number(num_str):
    if '万' in num_str:
        return float(num_str.replace('万', '')) * 10000
    elif '亿' in num_str:
        return float(num_str.replace('亿', '')) * 100000000
    else:
        return float(num_str)
def format_stock_code(code):
    return str(code).zfill(6)

# DataFrame调试
def debug_dataframe(df, prefix="Debug", show_sample_rows=5):
    """
    输出DataFrame的调试信息
    :param df: 待调试的DataFrame
    :param prefix: 日志前缀
    :param show_sample_rows: 显示的样本行数
    """
    logger.info(f"[{prefix}]数据形状: {df.shape}")
    logger.info(f"[{prefix}]列名: {df.columns.tolist()}")
    logger.info(f"[{prefix}]数据类型: {df.dtypes.to_dict()}")
    
    if show_sample_rows > 0:
        logger.info(f"[{prefix}]前{show_sample_rows}行数据: {df.head(show_sample_rows).to_dict()}")
    
    # 检查缺失值
    null_counts = df.isnull().sum()
    if null_counts.any():
        logger.info(f"[{prefix}]缺失值统计: {null_counts[null_counts > 0].to_dict()}")
    
    # 检查无穷大值
    for col in df.columns:
        if df[col].dtype in ['float64', 'float32', 'int64', 'int32']:
            inf_count = df[col].isin([float('inf'), float('-inf')]).sum()
            if inf_count > 0:
                logger.warning(f"[{prefix}]列 '{col}' 包含 {inf_count} 个无穷大值")
                inf_positions = df[df[col].isin([float('inf'), float('-inf')])].index.tolist()
                logger.info(f"[{prefix}]'{col}' 无穷大值位置: {inf_positions[:10]}...")  # 只显示前10个位置
    
    # 检查数值范围
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        logger.info(f"[{prefix}]数值列统计:")
        for col in numeric_cols:
            if not df[col].empty:
                try:
                    min_val = df[col].min()
                    max_val = df[col].max()
                    mean_val = df[col].mean()
                    logger.info(f"[{prefix}]  {col}: min={min_val}, max={max_val}, mean={mean_val:.2f}")
                except Exception as e:
                    logger.warning(f"[{prefix}]  {col}: 统计计算失败 - {str(e)}")
def debug_dataframe_simple(df, prefix="Debug"):
    """
    简化版DataFrame调试信息
    :param df: 待调试的DataFrame
    :param prefix: 日志前缀
    """
    logger.info(f"[{prefix}]数据形状: {df.shape}")
    logger.info(f"[{prefix}]列名: {df.columns.tolist()}")
    logger.info(f"[{prefix}]数据类型: {df.dtypes.to_dict()}")
def check_dataframe_quality(df, prefix="DataQuality"):
    """
    检查DataFrame数据质量
    :param df: 待检查的DataFrame
    :param prefix: 日志前缀
    :return: 质量检查结果字典
    """
    quality_report = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "null_counts": df.isnull().sum().to_dict(),
        "inf_counts": {},
        "duplicate_rows": df.duplicated().sum(),
        "memory_usage": df.memory_usage(deep=True).sum()
    }
    
    # 检查无穷大值
    for col in df.columns:
        if df[col].dtype in ['float64', 'float32', 'int64', 'int32']:
            inf_count = df[col].isin([float('inf'), float('-inf')]).sum()
            if inf_count > 0:
                quality_report["inf_counts"][col] = inf_count
    
    logger.info(f"[{prefix}]数据质量报告: {quality_report}")
    return quality_report
# DataFrame处理
def clean_numeric_data(df):
    """
    清理DataFrame中的数值数据，处理NaN和无穷大值
    :param df: 待清理的DataFrame
    :return: 清理后的DataFrame
    """
    df_copy = df.copy()
    for col in df_copy.columns:
        if df_copy[col].dtype in ['float64', 'float32', 'int64', 'int32']:
            # 将无穷大值替换为None
            df_copy[col] = df_copy[col].replace([np.inf, -np.inf], None)
            # 将NaN替换为None
            df_copy[col] = df_copy[col].where(pd.notna(df_copy[col]), None)
    return df_copy
def safe_convert_to_dict(df):
    """
    安全地将DataFrame转换为字典列表，确保所有数据都是JSON可序列化的
    :param df: 待转换的DataFrame
    :return: 字典列表
    """
    result = []
    for _, row in df.iterrows():
        row_dict = {}
        for key, value in row.items():
             # 先检查是否为列表或数组类型
            if isinstance(value, (list, tuple, np.ndarray)):
                try:
                    row_dict[key] = [str(item) for item in value] if value else []
                except (TypeError, ValueError):
                    row_dict[key] = str(value)
            elif pd.isna(value) or value in [np.inf, -np.inf]:
                row_dict[key] = None
            elif isinstance(value, (np.integer, np.floating)):
                if np.isfinite(value):
                    row_dict[key] = float(value) if isinstance(value, np.floating) else int(value)
                else:
                    row_dict[key] = None
            elif isinstance(value, datetime.date):
                # 处理 datetime.date 对象
                row_dict[key] = value.strftime('%Y-%m-%d')
            elif isinstance(value, datetime.datetime):
                # 处理 datetime.datetime 对象
                row_dict[key] = value.strftime('%Y-%m-%d %H:%M:%S')
            elif hasattr(value, 'strftime'):
                # 处理其他日期时间类型
                row_dict[key] = value.strftime('%Y-%m-%d')
            else:
                row_dict[key] = str(value)
        result.append(row_dict)
    return result
def clean_dataframe_for_json(df):
    """
    一站式DataFrame清理函数，结合数值清理和安全转换
    :param df: 待处理的DataFrame
    :return: JSON可序列化的字典列表
    """
    cleaned_df = clean_numeric_data(df)
    return safe_convert_to_dict(cleaned_df)