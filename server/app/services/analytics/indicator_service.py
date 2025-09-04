from core.logger import logger
from common.utils import clean_numeric_data, safe_convert_to_dict
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple
from functools import wraps
from common.debug_utils import debug_indicators
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
        
        try:
            # 第一步：数据清理
            cleaned_data = clean_numeric_data(df)
            
            # 第二步：转换为字典
            data_dict = safe_convert_to_dict(cleaned_data)
            
            result = {
                "status": "success",
                "data": data_dict,
                "message": message,
                "indicators": indicator_columns or []
            }
            
            # 第三步：添加统计信息
            if indicator_columns:
                stats = {}
                
                for i, col in enumerate(indicator_columns):
                    
                    if col in df.columns:
                        try:
                            # 详细调试每个步骤
                            series_data = df[col]
                            
                            numeric_series = pd.to_numeric(series_data, errors='coerce')
                            
                            clean_series = numeric_series.dropna()
                            
                            if len(clean_series) > 0:
                                mean_val = float(clean_series.mean())
                                
                                std_val = float(clean_series.std()) if len(clean_series) > 1 else 0.0
                                
                                min_val = float(clean_series.min())
                                
                                max_val = float(clean_series.max())
                                
                                # 检查是否为有效数值
                                finite_check = [np.isfinite(val) for val in [mean_val, std_val, min_val, max_val]]
                                
                                if all(finite_check):
                                    stats[col] = {
                                        'count': int(len(clean_series)),
                                        'mean': mean_val,
                                        'std': std_val,
                                        'min': min_val,
                                        'max': max_val
                                    }
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
                        
                result['statistics'] = stats
            return result
            
        except Exception as e:
            logger.error(f"[IndicatorCalculator]格式化结果失败: {e}")
            logger.error(f"[IndicatorCalculator]异常详情: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"[IndicatorCalculator]异常堆栈: {traceback.format_exc()}")
            
            try:
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
        
        try:
            result_df = df.copy()
            indicator_columns = []
            
            for period in periods:
                col_name = f'{ma_type.upper()}_{period}'  # 改为小写+下划线格式
                
                if ma_type.upper() == 'SMA':
                    result_df[col_name] = df['close'].rolling(window=period).mean()
                elif ma_type.upper() == 'EMA':
                    result_df[col_name] = df['close'].ewm(span=period).mean()
                elif ma_type.upper() == 'WMA':
                    weights = np.arange(1, period + 1)
                    result_df[col_name] = df['close'].rolling(window=period).apply(
                        lambda x: np.average(x, weights=weights), raw=True
                    )
                
                indicator_columns.append(col_name)
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
            rsi_column = f'RSI_{period}'
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
                rsi_column = f'RSI_{period}'  # 修改为下划线格式
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
            result_df['MACD_SIGNAL'] = result_df['MACD'].ewm(span=signal).mean()
            result_df['MACD_HISTOGRAM'] = result_df['MACD'] - result_df['MACD_SIGNAL']
            
            indicator_columns = ['MACD', 'MACD_SIGNAL', 'MACD_HISTOGRAM']
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
            result_df['BB_MIDDLE'] = df['close'].rolling(window=period).mean()
            bb_std = df['close'].rolling(window=period).std()
            result_df['BB_UPPER'] = result_df['BB_MIDDLE'] + (bb_std * std_dev)
            result_df['BB_LOWER'] = result_df['BB_MIDDLE'] - (bb_std * std_dev)
            result_df['BB_WIDTH'] = result_df['BB_UPPER'] - result_df['BB_LOWER']
            result_df['BB_POSITION'] = (df['close'] - result_df['BB_LOWER']) / result_df['BB_WIDTH']
            
            indicator_columns = ['BB_UPPER', 'BB_MIDDLE', 'BB_LOWER', 'BB_WIDTH', 'BB_POSITION']
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
                col_name = f'VOLUME_MA_{period}'
                result_df[col_name] = df['volume'].rolling(window=period).mean()
                indicator_columns.append(col_name)

            # 成交量比率
            if len(periods) >= 2:
                short_period, long_period = periods[0], periods[1]
                result_df['VOLUME_RATIO'] = (
                    result_df[f'VOLUME_MA_{short_period}'] / result_df[f'VOLUME_MA_{long_period}']
                )
                indicator_columns.append('VOLUME_RATIO')
            
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

def calculate_adaptive_period(base_period: int, 
                            volatility: float, 
                            indicator_type: str = 'rsi',
                            is_short: bool = True,
                            min_period: int = None,
                            max_period: int = None) -> int:
    """
    计算自适应周期
    :param base_period: 基础周期
    :param volatility: 波动率
    :param indicator_type: 指标类型 ('rsi', 'ma')
    :param is_short: 是否为短周期（仅MA使用）
    :param min_period: 最小周期（可选，覆盖默认值）
    :param max_period: 最大周期（可选，覆盖默认值）
    :return: 自适应周期
    """
    if indicator_type.lower() == 'rsi':
        # RSI: 波动率高时周期增加（更平滑）
        min_p = min_period or 7
        max_p = max_period or 21
        return max(min_p, min(max_p, int(base_period * (1 + volatility))))
    
    elif indicator_type.lower() == 'ma':
        # MA: 波动率高时周期减少（更敏感）
        vol_factor = max(0.7, 1 - volatility)
        if is_short:
            min_p = min_period or 3
            max_p = max_period or base_period
            return max(min_p, min(max_p, int(base_period * vol_factor)))
        else:
            # 长周期需要确保大于短周期
            adaptive_short = calculate_adaptive_period(
                base_period=int(base_period * 0.3), 
                volatility=volatility, 
                indicator_type='ma', 
                is_short=True
            )
            min_p = min_period or (adaptive_short + 5)
            max_p = max_period or base_period
            return max(min_p, min(max_p, int(base_period * vol_factor)))
    
    else:
        # 默认情况，直接返回基础周期
        return base_period
def get_adaptive_periods_range(base_period: int,
                             indicator_type: str = 'rsi',
                             is_short: bool = True,
                             volatility_range: tuple = (0.0, 1.0),
                             step: float = 0.05,
                             **kwargs) -> List[int]:
    """
    获取指标所有可能的自适应周期范围
    :param base_period: 基础周期
    :param indicator_type: 指标类型
    :param is_short: 是否为短周期
    :param volatility_range: 波动率范围
    :param step: 波动率步长
    :param kwargs: 其他参数（如min_period, max_period）
    :return: 周期列表
    """
    periods = set([base_period])
    
    min_vol, max_vol = volatility_range
    volatility = min_vol
    
    while volatility <= max_vol:
        adaptive_period = calculate_adaptive_period(
            base_period=base_period,
            volatility=volatility,
            indicator_type=indicator_type,
            is_short=is_short,
            **kwargs
        )
        periods.add(adaptive_period)
        volatility += step
    
    return sorted(list(periods))
def calculate_indicators_for_rule_configs(df: pd.DataFrame, 
                                    config: Dict) -> Tuple[Dict, pd.DataFrame]:
    """为策略服务提供的便捷指标计算函数"""
    calculator = IndicatorCalculator()
    
    indicators = {}
    
    # MA指标
    if config.get('ma_crossover', {}).get('enable', True):
        ma_config = config.get('ma_crossover', {})
        
        if ma_config.get('adaptive', False):
            # 自适应模式：计算更广泛的周期范围以覆盖可能的自适应周期
            base_short = ma_config.get('short_period', 5)
            base_long = ma_config.get('long_period', 20)
            # 分别计算短期和长期MA的自适应周期范围
            short_periods = get_adaptive_periods_range(
                base_period=base_short,
                indicator_type='ma',
                is_short=True,
                volatility_range=(0.0, 1.0),
                step=0.05
            )
            long_periods = get_adaptive_periods_range(
                base_period=base_long,
                indicator_type='ma',
                is_short=False,
                volatility_range=(0.0, 1.0),
                step=0.05
            )
            periods = sorted(list(set(short_periods + long_periods)))
            logger.debug(f"[Indicator]使用MA自适应模式，计算周期范围: {periods}")
        else:
            periods = [ma_config.get('short_period', 5), ma_config.get('long_period', 20)]
            logger.debug(f"[Indicator]使用固定MA周期: {periods}")
            
        ma_result = calculator.calculate_moving_averages(df, periods)
        
        if ma_result['status'] == 'success':
            ma_df = pd.DataFrame(ma_result['data'])
            for col in ma_df.columns:
                if col.startswith('SMA_'):  # 匹配新的命名格式
                    try:
                        # 将SMA_5转换为MA_5格式以保持向后兼容
                        period = col.split('_')[1]
                        indicators[f'MA_{period}'] = pd.to_numeric(ma_df[col], errors='coerce').fillna(0)
                    except Exception as e:
                        logger.warning(f"[Indicator]MA指标 {col} 转换失败: {e}")
                        indicators[f'MA_{period}'] = pd.Series(dtype=float)
    
    # RSI指标
    if config.get('rsi', {}).get('enable', True):
        rsi_config = config.get('rsi', {})
        
        if rsi_config.get('adaptive', False):
            base_period = rsi_config.get('period', 14)
            # rsi 自适应周期计算
            periods = get_adaptive_periods_range(
                base_period=base_period,
                indicator_type='rsi',
                volatility_range=(0.0, 1.0),
                step=0.05
            )
            logger.debug(f"[Indicator]使用RSI自适应模式，涉及指标周期: {periods}")
            
            rsi_result = calculator.calculate_multiple_rsi(df, periods)
            
            if rsi_result['status'] == 'success':
                rsi_df = pd.DataFrame(rsi_result['data'])
                for period in periods:
                    rsi_column = f'RSI_{period}'  # 匹配新的命名格式
                    if rsi_column in rsi_df.columns:
                        try:
                            indicators[f'RSI_{period}'] = pd.to_numeric(rsi_df[rsi_column], errors='coerce').fillna(50)
                        except Exception as e:
                            logger.warning(f"[Indicator]RSI指标 {rsi_column} 转换失败: {e}")
                            indicators[f'RSI_{period}'] = pd.Series(dtype=float)
                
                # 为了向后兼容，也保留原来的键名
                base_rsi_column = f'rsi_{base_period}'
                if base_rsi_column in indicators:
                    indicators['RSI'] = indicators[base_rsi_column]
        else:
            period = rsi_config.get('period', 14)
            logger.debug(f"[Indicator]使用RSI固定模式，涉及指标周期: {period}")
            
            rsi_result = calculator.calculate_rsi(df, period)
            
            if rsi_result['status'] == 'success':
                rsi_df = pd.DataFrame(rsi_result['data'])
                rsi_column = f'RSI_{period}'
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

def calculate_indicators_for_rule_names(price_data: pd.DataFrame, rule_names: List[str]) -> Dict[str, pd.Series]:
    """基于规则注册表计算所需指标"""
    from app.services.signals.data_signals import rule_registry
    
    # 获取所有需要的指标
    indicator_info = rule_registry.get_all_indicators(rule_names)
    required_indicators = indicator_info['required']
    optional_indicators = indicator_info['optional']
    
    debug_indicators(f"规则 {rule_names} 指标需求", {
        "必需指标": required_indicators,
        "可选指标": optional_indicators
    })
    
    indicators = {}
    calculator = IndicatorCalculator()
    
    try:
        # 计算必需指标
        for indicator in required_indicators:
            if indicator.startswith('ma_'):
                period = int(indicator.split('_')[1])
                indicators[indicator] = calculator.calculate_ma(price_data['close'], period)
            elif indicator.startswith('rsi_'):
                period = int(indicator.split('_')[1])
                indicators[indicator] = calculator.calculate_rsi(price_data['close'], period)
            elif indicator in ['high', 'low', 'close', 'volume']:
                indicators[indicator] = price_data[indicator]
            # 添加更多指标类型...
        
        # 计算可选指标（如果数据允许）
        for indicator in optional_indicators:
            try:
                if indicator == 'volatility':
                    indicators[indicator] = calculator.calculate_volatility(price_data['close'])
                elif indicator == 'volume' and 'volume' in price_data.columns:
                    indicators[indicator] = price_data['volume']
                # 添加更多可选指标...
            except Exception as e:
                logger.warning(f"[IndicatorService]可选指标 {indicator} 计算失败: {e}")
        
        logger.info(f"[IndicatorService]成功计算 {len(indicators)} 个指标")
        return indicators
        
    except Exception as e:
        logger.error(f"[IndicatorService]指标计算失败: {e}")
        return {}