from core.logger import logger
from common.utils import clean_numeric_data, safe_convert_to_dict
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple
from functools import wraps
def validate_dataframe(func):
    """装饰器：验证DataFrame格式和必要列"""
    @wraps(func)
    def wrapper(self, df: pd.DataFrame, *args, **kwargs):
        if df is None or df.empty:
            return {"status": "error", "message": "输入数据为空"}
        
        # 标准化列名
        df = self._standardize_columns(df)
        
        # 检查必要的列
        required_cols = kwargs.get('required_columns', ['close'])
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return {"status": "error", "message": f"缺少必要列: {missing_cols}"}
        
        return func(self, df, *args, **kwargs)
    return wrapper
class IndicatorCalculator:
    """
    通用技术指标计算器
    提供高兼容性的指标计算功能，支持多种数据格式和参数配置
    """
    
    def __init__(self):
        self.supported_indicators = {
            'ma': self.calculate_moving_averages,
            'ema': self.calculate_exponential_moving_averages,
            'rsi': self.calculate_rsi,
            'macd': self.calculate_macd,
            'bollinger': self.calculate_bollinger_bands,
            'stoch': self.calculate_stochastic,
            'atr': self.calculate_atr,
            'volume_ma': self.calculate_volume_indicators,
            'support_resistance': self.calculate_support_resistance
        }
    

    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化列名，支持中英文列名"""
        column_mapping = {
            '开盘': 'open', '开盘价': 'open',
            '收盘': 'close', '收盘价': 'close',
            '最高': 'high', '最高价': 'high',
            '最低': 'low', '最低价': 'low',
            '成交量': 'volume', '成交额': 'amount',
            '日期': 'date', '时间': 'date'
        }
        
        df_copy = df.copy()
        for chinese_col, english_col in column_mapping.items():
            if chinese_col in df_copy.columns and english_col not in df_copy.columns:
                df_copy = df_copy.rename(columns={chinese_col: english_col})
        
        return df_copy
    
    def _format_result(self, df: pd.DataFrame, message: str, 
                      indicator_columns: List[str] = None) -> Dict:
        """格式化返回结果"""
        logger.debug(f"[IndicatorCalculator]开始格式化结果，DataFrame形状: {df.shape}, 指标列: {indicator_columns}")
        
        try:
            # 第一步：数据清理
            logger.debug(f"[IndicatorCalculator]步骤1: 开始清理数据")
            cleaned_data = clean_numeric_data(df)
            logger.debug(f"[IndicatorCalculator]步骤1: 数据清理完成，形状: {cleaned_data.shape}")
            
            # 第二步：转换为字典
            logger.debug(f"[IndicatorCalculator]步骤2: 开始转换为字典")
            data_dict = safe_convert_to_dict(cleaned_data)
            logger.debug(f"[IndicatorCalculator]步骤2: 字典转换完成，记录数: {len(data_dict)}")
            
            result = {
                "status": "success",
                "data": data_dict,
                "message": message,
                "indicators": indicator_columns or []
            }
            
            # 第三步：添加统计信息
            if indicator_columns:
                logger.debug(f"[IndicatorCalculator]步骤3: 开始计算统计信息，指标数量: {len(indicator_columns)}")
                stats = {}
                
                for i, col in enumerate(indicator_columns):
                    logger.debug(f"[IndicatorCalculator]步骤3.{i+1}: 处理指标 {col}")
                    
                    if col in df.columns:
                        try:
                            # 详细调试每个步骤
                            logger.debug(f"[IndicatorCalculator]步骤3.{i+1}.1: 获取列 {col} 的原始数据")
                            series_data = df[col]
                            logger.debug(f"[IndicatorCalculator]步骤3.{i+1}.1: 原始数据类型: {type(series_data)}, 长度: {len(series_data)}")
                            
                            logger.debug(f"[IndicatorCalculator]步骤3.{i+1}.2: 转换为数值类型")
                            numeric_series = pd.to_numeric(series_data, errors='coerce')
                            logger.debug(f"[IndicatorCalculator]步骤3.{i+1}.2: 数值转换完成，类型: {type(numeric_series)}")
                            
                            logger.debug(f"[IndicatorCalculator]步骤3.{i+1}.3: 删除NaN值")
                            clean_series = numeric_series.dropna()
                            logger.debug(f"[IndicatorCalculator]步骤3.{i+1}.3: 清理完成，有效数据量: {len(clean_series)}")
                            
                            if len(clean_series) > 0:
                                logger.debug(f"[IndicatorCalculator]步骤3.{i+1}.4: 开始计算统计值")
                                
                                # 逐个计算统计值并记录
                                logger.debug(f"[IndicatorCalculator]步骤3.{i+1}.4.1: 计算均值")
                                mean_val = float(clean_series.mean())
                                logger.debug(f"[IndicatorCalculator]步骤3.{i+1}.4.1: 均值 = {mean_val}")
                                
                                logger.debug(f"[IndicatorCalculator]步骤3.{i+1}.4.2: 计算标准差")
                                std_val = float(clean_series.std()) if len(clean_series) > 1 else 0.0
                                logger.debug(f"[IndicatorCalculator]步骤3.{i+1}.4.2: 标准差 = {std_val}")
                                
                                logger.debug(f"[IndicatorCalculator]步骤3.{i+1}.4.3: 计算最小值")
                                min_val = float(clean_series.min())
                                logger.debug(f"[IndicatorCalculator]步骤3.{i+1}.4.3: 最小值 = {min_val}")
                                
                                logger.debug(f"[IndicatorCalculator]步骤3.{i+1}.4.4: 计算最大值")
                                max_val = float(clean_series.max())
                                logger.debug(f"[IndicatorCalculator]步骤3.{i+1}.4.4: 最大值 = {max_val}")
                                
                                # 检查是否为有效数值
                                logger.debug(f"[IndicatorCalculator]步骤3.{i+1}.5: 检查数值有效性")
                                finite_check = [np.isfinite(val) for val in [mean_val, std_val, min_val, max_val]]
                                logger.debug(f"[IndicatorCalculator]步骤3.{i+1}.5: 有效性检查结果: {finite_check}")
                                
                                if all(finite_check):
                                    logger.debug(f"[IndicatorCalculator]步骤3.{i+1}.6: 构建统计字典")
                                    stats[col] = {
                                        'count': int(len(clean_series)),
                                        'mean': mean_val,
                                        'std': std_val,
                                        'min': min_val,
                                        'max': max_val
                                    }
                                    logger.debug(f"[IndicatorCalculator]步骤3.{i+1}.6: 统计字典构建成功")
                                else:
                                    logger.warning(f"[IndicatorCalculator]指标 {col} 包含无效数值，跳过统计。有效性: {finite_check}")
                            else:
                                logger.debug(f"[IndicatorCalculator]步骤3.{i+1}: 指标 {col} 无有效数据，跳过")
                                
                        except Exception as e:
                            logger.error(f"[IndicatorCalculator]计算 {col} 统计信息失败: {e}")
                            logger.error(f"[IndicatorCalculator]异常详情: {type(e).__name__}: {str(e)}")
                            import traceback
                            logger.error(f"[IndicatorCalculator]异常堆栈: {traceback.format_exc()}")
                            # 跳过有问题的列，继续处理其他列
                            continue
                    else:
                        logger.warning(f"[IndicatorCalculator]指标列 {col} 不存在于DataFrame中")
                        
                logger.debug(f"[IndicatorCalculator]步骤3: 统计信息计算完成，统计项数量: {len(stats)}")
                result['statistics'] = stats
            
            logger.debug(f"[IndicatorCalculator]格式化结果成功完成")
            return result
            
        except Exception as e:
            logger.error(f"[IndicatorCalculator]格式化结果失败: {e}")
            logger.error(f"[IndicatorCalculator]异常详情: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"[IndicatorCalculator]异常堆栈: {traceback.format_exc()}")
            
            # 返回基本结果，不包含统计信息
            try:
                logger.debug(f"[IndicatorCalculator]尝试备用格式化方案")
                cleaned_data = clean_numeric_data(df)
                data_dict = safe_convert_to_dict(cleaned_data)
                logger.debug(f"[IndicatorCalculator]备用格式化成功")
                return {
                    "status": "success",
                    "data": data_dict,
                    "message": message,
                    "indicators": indicator_columns or [],
                    "statistics": {}
                }
            except Exception as fallback_e:
                logger.error(f"[IndicatorCalculator]备用格式化也失败: {fallback_e}")
                logger.error(f"[IndicatorCalculator]备用异常详情: {type(fallback_e).__name__}: {str(fallback_e)}")
                import traceback
                logger.error(f"[IndicatorCalculator]备用异常堆栈: {traceback.format_exc()}")
                return {
                    "status": "error", 
                    "message": f"格式化失败: {e}",
                    "data": [],
                    "indicators": [],
                    "statistics": {}
                }
    
    @validate_dataframe
    def calculate_moving_averages(self, df: pd.DataFrame, 
                                periods: Union[List[int], int] = [5, 10, 20, 60],
                                ma_type: str = 'sma') -> Dict:
        """
        计算移动平均线
        :param df: 价格数据
        :param periods: 周期列表或单个周期
        :param ma_type: 移动平均类型 ('sma', 'ema', 'wma')
        :return: 计算结果
        """
        if isinstance(periods, int):
            periods = [periods]
        
        logger.debug(f"[IndicatorCalculator]需要计算{ma_type.upper()}移动平均线，周期: {periods}")
        
        try:
            result_df = df.copy()
            indicator_columns = []
            
            for period in periods:
                col_name = f'{ma_type.upper()}{period}'
                
                if ma_type.lower() == 'sma':
                    result_df[col_name] = df['close'].rolling(window=period).mean()
                elif ma_type.lower() == 'ema':
                    result_df[col_name] = df['close'].ewm(span=period).mean()
                elif ma_type.lower() == 'wma':
                    weights = np.arange(1, period + 1)
                    result_df[col_name] = df['close'].rolling(window=period).apply(
                        lambda x: np.average(x, weights=weights), raw=True
                    )
                
                indicator_columns.append(col_name)
                
                # 记录有效值信息（debugInfo）
                # first_valid_idx = result_df[col_name].first_valid_index()
                # if first_valid_idx is not None:
                #     logger.info(f"[IndicatorCalculator]{col_name} 从索引{first_valid_idx}开始有效")
            
            return self._format_result(result_df, f"{ma_type.upper()}移动平均线计算完成", indicator_columns)
            
        except Exception as e:
            logger.error(f"[IndicatorCalculator]计算移动平均线失败: {e}")
            return {"status": "error", "message": f"计算失败: {e}"}
    
    @validate_dataframe
    def calculate_exponential_moving_averages(self, df: pd.DataFrame, 
                                            periods: Union[List[int], int] = [12, 26]) -> Dict:
        """计算指数移动平均线"""
        return self.calculate_moving_averages(df, periods, ma_type='ema')
    
    @validate_dataframe
    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> Dict:
        """
        计算RSI指标
        :param df: 价格数据
        :param period: RSI周期
        :return: 计算结果
        """
        logger.debug(f"[IndicatorCalculator]需要计算RSI指标，周期: {period}")
        
        try:
            result_df = df.copy()
            
            # 确定收盘价列名
            close_col = 'close' if 'close' in df.columns else '收盘'
            if close_col not in df.columns:
                return {"status": "error", "message": "未找到收盘价数据"}
            
            # 计算价格变化
            delta = df[close_col].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            # 添加除0保护 - 使用向量化操作
            rs = gain / loss.replace(0, np.nan)
            rsi_column = f'RSI{period}'
            result_df[rsi_column] = 100 - (100 / (1 + rs))
            
            # 处理边界情况
            mask_loss_zero = (loss == 0)
            mask_gain_positive = (gain > 0) & mask_loss_zero
            mask_gain_zero = (gain == 0) & mask_loss_zero
            
            result_df.loc[mask_gain_positive, rsi_column] = 100.0
            result_df.loc[mask_gain_zero, rsi_column] = 50.0
            # 添加有效值起始点判断
            first_valid_idx = result_df[rsi_column].first_valid_index()
            if first_valid_idx is not None:
                logger.info(f"[Analytics]RSI 从第{first_valid_idx + 1}个交易日开始有值（索引{first_valid_idx}）")
                logger.info(f"[Analytics]RSI 需要{period + 1}个交易日的数据才能开始计算")
            else:
                logger.warning(f"[Analytics]RSI 没有有效值")
            
            result_df[rsi_column] = pd.to_numeric(result_df[rsi_column], errors='coerce')
            # 关键步骤：添加数据清理
            from common.utils import clean_numeric_data
            result_df = clean_numeric_data(result_df)
            
            return self._format_result(result_df, "RSI指标计算完成", [rsi_column])
            
        except Exception as e:
            logger.error(f"[IndicatorCalculator]计算RSI失败: {e}")
            return {"status": "error", "message": f"计算失败: {e}"}
    
    @validate_dataframe
    def calculate_multiple_rsi(self, df: pd.DataFrame, periods: List[int]) -> Dict:
        """
        计算多个周期的RSI指标
        :param df: 价格数据
        :param periods: RSI周期列表
        :return: 计算结果
        """
        logger.debug(f"[IndicatorCalculator]计算多个RSI指标，周期: {periods}")
        
        try:
            result_df = df.copy()
            
            # 确定收盘价列名
            close_col = 'close' if 'close' in df.columns else '收盘'
            if close_col not in df.columns:
                return {"status": "error", "message": "未找到收盘价数据"}
            
            rsi_columns = []
            
            for period in periods:
                # 计算价格变化
                delta = df[close_col].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                
                # 添加除0保护
                rs = gain / loss.replace(0, np.nan)
                rsi_column = f'RSI{period}'
                result_df[rsi_column] = 100 - (100 / (1 + rs))
                
                # 处理边界情况 - 修复布尔掩码使用方式
                # 使用 .where() 方法替代 .loc[] 索引
                loss_zero_mask = (loss == 0)
                gain_positive_mask = (gain > 0) & loss_zero_mask
                gain_zero_mask = (gain == 0) & loss_zero_mask
                
                # 安全的赋值方式
                result_df[rsi_column] = result_df[rsi_column].where(~gain_positive_mask, 100.0)
                result_df[rsi_column] = result_df[rsi_column].where(~gain_zero_mask, 50.0)
                
                result_df[rsi_column] = pd.to_numeric(result_df[rsi_column], errors='coerce')
                rsi_columns.append(rsi_column)
            
            # 数据清理
            from common.utils import clean_numeric_data
            result_df = clean_numeric_data(result_df)
            
            return self._format_result(result_df, f"多周期RSI指标计算完成，周期: {periods}", rsi_columns)
            
        except Exception as e:
            logger.error(f"[IndicatorCalculator]计算多周期RSI失败: {e}")
            return {"status": "error", "message": f"计算失败: {e}"}
   
    @validate_dataframe
    def calculate_macd(self, df: pd.DataFrame, fast: int = 12, 
                      slow: int = 26, signal: int = 9) -> Dict:
        """
        计算MACD指标
        :param df: 价格数据
        :param fast: 快线周期
        :param slow: 慢线周期
        :param signal: 信号线周期
        :return: 计算结果
        """
        logger.info(f"[IndicatorCalculator]计算MACD指标，参数: {fast}, {slow}, {signal}")
        
        try:
            result_df = df.copy()
            
            # 计算MACD
            exp1 = df['close'].ewm(span=fast).mean()
            exp2 = df['close'].ewm(span=slow).mean()
            result_df['MACD'] = exp1 - exp2
            result_df['MACD_Signal'] = result_df['MACD'].ewm(span=signal).mean()
            result_df['MACD_Histogram'] = result_df['MACD'] - result_df['MACD_Signal']
            
            indicator_columns = ['MACD', 'MACD_Signal', 'MACD_Histogram']
            return self._format_result(result_df, "MACD指标计算完成", indicator_columns)
            
        except Exception as e:
            logger.error(f"[IndicatorCalculator]计算MACD失败: {e}")
            return {"status": "error", "message": f"计算失败: {e}"}
    
    @validate_dataframe
    def calculate_bollinger_bands(self, df: pd.DataFrame, period: int = 20, 
                                 std_dev: float = 2.0) -> Dict:
        """
        计算布林带指标
        :param df: 价格数据
        :param period: 移动平均周期
        :param std_dev: 标准差倍数
        :return: 计算结果
        """
        logger.info(f"[IndicatorCalculator]计算布林带指标，周期: {period}, 标准差: {std_dev}")
        
        try:
            result_df = df.copy()
            
            # 计算布林带
            result_df['BB_Middle'] = df['close'].rolling(window=period).mean()
            bb_std = df['close'].rolling(window=period).std()
            result_df['BB_Upper'] = result_df['BB_Middle'] + (bb_std * std_dev)
            result_df['BB_Lower'] = result_df['BB_Middle'] - (bb_std * std_dev)
            result_df['BB_Width'] = result_df['BB_Upper'] - result_df['BB_Lower']
            result_df['BB_Position'] = (df['close'] - result_df['BB_Lower']) / result_df['BB_Width']
            
            indicator_columns = ['BB_Upper', 'BB_Middle', 'BB_Lower', 'BB_Width', 'BB_Position']
            return self._format_result(result_df, "布林带指标计算完成", indicator_columns)
            
        except Exception as e:
            logger.error(f"[IndicatorCalculator]计算布林带失败: {e}")
            return {"status": "error", "message": f"计算失败: {e}"}
    
    @validate_dataframe
    def calculate_stochastic(self, df: pd.DataFrame, k_period: int = 14, 
                           d_period: int = 3) -> Dict:
        """
        计算随机指标KDJ
        :param df: 价格数据（需要high, low, close列）
        :param k_period: K值周期
        :param d_period: D值周期
        :return: 计算结果
        """
        required_columns = ['high', 'low', 'close']
        for col in required_columns:
            if col not in df.columns:
                return {"status": "error", "message": f"缺少必要列: {col}"}
        
        logger.info(f"[IndicatorCalculator]计算KDJ指标，K周期: {k_period}, D周期: {d_period}")
        
        try:
            result_df = df.copy()
            
            # 计算KDJ
            low_min = df['low'].rolling(window=k_period).min()
            high_max = df['high'].rolling(window=k_period).max()
            
            result_df['K'] = 100 * (df['close'] - low_min) / (high_max - low_min)
            result_df['D'] = result_df['K'].rolling(window=d_period).mean()
            result_df['J'] = 3 * result_df['K'] - 2 * result_df['D']
            
            indicator_columns = ['K', 'D', 'J']
            return self._format_result(result_df, "KDJ指标计算完成", indicator_columns)
            
        except Exception as e:
            logger.error(f"[IndicatorCalculator]计算KDJ失败: {e}")
            return {"status": "error", "message": f"计算失败: {e}"}
    
    @validate_dataframe
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> Dict:
        """
        计算平均真实波幅ATR
        :param df: 价格数据（需要high, low, close列）
        :param period: ATR周期
        :return: 计算结果
        """
        required_columns = ['high', 'low', 'close']
        for col in required_columns:
            if col not in df.columns:
                return {"status": "error", "message": f"缺少必要列: {col}"}
        
        logger.info(f"[IndicatorCalculator]计算ATR指标，周期: {period}")
        
        try:
            result_df = df.copy()
            
            # 计算真实波幅
            high_low = df['high'] - df['low']
            high_close_prev = np.abs(df['high'] - df['close'].shift(1))
            low_close_prev = np.abs(df['low'] - df['close'].shift(1))
            
            true_range = np.maximum(high_low, np.maximum(high_close_prev, low_close_prev))
            result_df['ATR'] = true_range.rolling(window=period).mean()
            
            return self._format_result(result_df, "ATR指标计算完成", ['ATR'])
            
        except Exception as e:
            logger.error(f"[IndicatorCalculator]计算ATR失败: {e}")
            return {"status": "error", "message": f"计算失败: {e}"}
    
    @validate_dataframe
    def calculate_volume_indicators(self, df: pd.DataFrame, periods: List[int] = [5, 20]) -> Dict:
        """
        计算成交量相关指标
        :param df: 价格数据（需要volume列）
        :param periods: 成交量移动平均周期
        :return: 计算结果
        """
        if 'volume' not in df.columns:
            return {"status": "error", "message": "缺少成交量数据"}
        
        logger.info(f"[IndicatorCalculator]计算成交量指标，周期: {periods}")
        
        try:
            result_df = df.copy()
            indicator_columns = []
            
            # 成交量移动平均
            for period in periods:
                col_name = f'Volume_MA{period}'
                result_df[col_name] = df['volume'].rolling(window=period).mean()
                indicator_columns.append(col_name)
            
            # 成交量比率
            if len(periods) >= 2:
                short_period, long_period = periods[0], periods[1]
                result_df['Volume_Ratio'] = (
                    result_df[f'Volume_MA{short_period}'] / result_df[f'Volume_MA{long_period}']
                )
                indicator_columns.append('Volume_Ratio')
            
            # 价量配合指标
            if 'close' in df.columns:
                price_change = df['close'].pct_change()
                volume_change = df['volume'].pct_change()
                result_df['Price_Volume_Trend'] = (price_change * df['volume']).cumsum()
                indicator_columns.append('Price_Volume_Trend')
            
            return self._format_result(result_df, "成交量指标计算完成", indicator_columns)
            
        except Exception as e:
            logger.error(f"[IndicatorCalculator]计算成交量指标失败: {e}")
            return {"status": "error", "message": f"计算失败: {e}"}
    
    @validate_dataframe
    def calculate_support_resistance(self, df: pd.DataFrame, window: int = 20, 
                                   min_touches: int = 2) -> Dict:
        """
        计算支撑阻力位
        :param df: 价格数据
        :param window: 计算窗口
        :param min_touches: 最小触及次数
        :return: 计算结果
        """
        required_columns = ['high', 'low', 'close']
        for col in required_columns:
            if col not in df.columns:
                return {"status": "error", "message": f"缺少必要列: {col}"}
        
        logger.info(f"[IndicatorCalculator]计算支撑阻力位，窗口: {window}")
        
        try:
            result_df = df.copy()
            
            # 计算局部高点和低点
            result_df['Local_High'] = df['high'].rolling(window=window, center=True).max()
            result_df['Local_Low'] = df['low'].rolling(window=window, center=True).min()
            
            # 标识支撑阻力位
            result_df['Is_Resistance'] = (df['high'] == result_df['Local_High'])
            result_df['Is_Support'] = (df['low'] == result_df['Local_Low'])
            
            # 计算动态支撑阻力位
            result_df['Dynamic_Resistance'] = df['high'].rolling(window=window).quantile(0.8)
            result_df['Dynamic_Support'] = df['low'].rolling(window=window).quantile(0.2)
            
            indicator_columns = ['Local_High', 'Local_Low', 'Is_Resistance', 'Is_Support', 
                               'Dynamic_Resistance', 'Dynamic_Support']
            
            return self._format_result(result_df, "支撑阻力位计算完成", indicator_columns)
            
        except Exception as e:
            logger.error(f"[IndicatorCalculator]计算支撑阻力位失败: {e}")
            return {"status": "error", "message": f"计算失败: {e}"}
    
    def calculate_multiple_indicators(self, df: pd.DataFrame, 
                                    indicators_config: Dict) -> Dict:
        """
        批量计算多个指标
        :param df: 价格数据
        :param indicators_config: 指标配置字典
        :return: 计算结果
        """
        logger.info(f"[IndicatorCalculator]批量计算指标: {list(indicators_config.keys())}")
        
        try:
            result_df = df.copy()
            all_indicators = []
            calculation_results = {}
            
            for indicator_name, config in indicators_config.items():
                if indicator_name in self.supported_indicators:
                    try:
                        calc_func = self.supported_indicators[indicator_name]
                        result = calc_func(df, **config)
                        
                        if result['status'] == 'success':
                            # 合并指标数据
                            indicator_df = pd.DataFrame(result['data'])
                            for col in result.get('indicators', []):
                                if col in indicator_df.columns:
                                    result_df[col] = indicator_df[col]
                                    all_indicators.append(col)
                            
                            calculation_results[indicator_name] = {
                                'status': 'success',
                                'indicators': result.get('indicators', []),
                                'statistics': result.get('statistics', {})
                            }
                        else:
                            calculation_results[indicator_name] = {
                                'status': 'error',
                                'message': result['message']
                            }
                            logger.warning(f"[IndicatorCalculator]指标{indicator_name}计算失败: {result['message']}")
                    
                    except Exception as e:
                        calculation_results[indicator_name] = {
                            'status': 'error',
                            'message': str(e)
                        }
                        logger.error(f"[IndicatorCalculator]指标{indicator_name}计算异常: {e}")
                else:
                    calculation_results[indicator_name] = {
                        'status': 'error',
                        'message': f'不支持的指标: {indicator_name}'
                    }
            
            # 格式化最终结果
            final_result = self._format_result(result_df, "批量指标计算完成", all_indicators)
            final_result['calculation_details'] = calculation_results
            
            return final_result
            
        except Exception as e:
            logger.error(f"[IndicatorCalculator]批量计算指标失败: {e}")
            return {"status": "error", "message": f"批量计算失败: {e}"}
    
    def get_supported_indicators(self) -> List[str]:
        """获取支持的指标列表"""
        return list(self.supported_indicators.keys())


# 支持传入策略规则，保持向后兼容
def calculate_indicators_for_strategy(df: pd.DataFrame, 
                                    config: Dict) -> Tuple[Dict, pd.DataFrame]:
    """为策略服务提供的便捷指标计算函数"""
    calculator = IndicatorCalculator()
    
    indicators = {}
    
    # MA指标
    if config.get('ma_crossover', {}).get('enable', True):
        ma_config = config.get('ma_crossover', {})
        
        if ma_config.get('adaptive', False):
            periods = [3, 5, 10, 20, 30]
            logger.debug(f"[Indicator]使用MA自适应模式，计算周期: {periods}")
        else:
            periods = [ma_config.get('short_period', 5), ma_config.get('long_period', 20)]
            logger.debug(f"[Indicator]使用固定MA周期: {periods}")
            
        ma_result = calculator.calculate_moving_averages(df, periods)
        
        if ma_result['status'] == 'success':
            ma_df = pd.DataFrame(ma_result['data'])
            for col in ma_df.columns:
                if col.startswith('SMA'):
                    # 修复：返回 pandas Series 而不是 list
                    try:
                        indicators[col.replace('SMA', 'MA')] = pd.to_numeric(ma_df[col], errors='coerce').fillna(0)
                    except Exception as e:
                        logger.warning(f"[Indicator]MA指标 {col} 转换失败: {e}")
                        indicators[col.replace('SMA', 'MA')] = pd.Series(dtype=float)
    
    # RSI指标
    if config.get('rsi', {}).get('enable', True):
        rsi_config = config.get('rsi', {})
        
        if rsi_config.get('adaptive', False):
            base_period = rsi_config.get('period', 14)
            periods = [
                max(base_period - 7, 7),
                max(base_period - 4, 10),
                base_period,
                min(base_period + 7, 28),
                min(base_period + 14, 35)
            ]
            periods = sorted(list(set(periods)))
            logger.debug(f"[Indicator]使用RSI自适应模式，计算周期: {periods}")
            
            rsi_result = calculator.calculate_multiple_rsi(df, periods)
            
            if rsi_result['status'] == 'success':
                rsi_df = pd.DataFrame(rsi_result['data'])
                for period in periods:
                    rsi_column = f'RSI{period}'
                    if rsi_column in rsi_df.columns:
                        # 修复：返回 pandas Series 而不是 list
                        try:
                            indicators[rsi_column] = pd.to_numeric(rsi_df[rsi_column], errors='coerce').fillna(50)
                        except Exception as e:
                            logger.warning(f"[Indicator]RSI指标 {rsi_column} 转换失败: {e}")
                            indicators[rsi_column] = pd.Series(dtype=float)
                
                # 为了向后兼容，也保留原来的键名
                base_rsi_column = f'RSI{base_period}'
                if base_rsi_column in indicators:
                    indicators['RSI'] = indicators[base_rsi_column]
        else:
            period = rsi_config.get('period', 14)
            logger.debug(f"[Indicator]使用固定RSI周期: {period}")
            
            rsi_result = calculator.calculate_rsi(df, period)
            
            if rsi_result['status'] == 'success':
                rsi_df = pd.DataFrame(rsi_result['data'])
                rsi_column = f'RSI{period}'
                if rsi_column in rsi_df.columns:
                    # 修复：返回 pandas Series 而不是 list
                    try:
                        indicators[rsi_column] = pd.to_numeric(rsi_df[rsi_column], errors='coerce').fillna(50)
                        indicators['RSI'] = indicators[rsi_column]  # 向后兼容
                    except Exception as e:
                        logger.warning(f"[Indicator]RSI指标 {rsi_column} 转换失败: {e}")
                        indicators[rsi_column] = pd.Series(dtype=float)
                        indicators['RSI'] = pd.Series(dtype=float)
    
    return indicators, df