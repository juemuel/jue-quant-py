from comm import *

# 财务报表-东财
df = ak.stock_balance_sheet_by_report_em(symbol='SH600519')
# print(df)
# 获取最近三年的一季度报，重新更新索引
df = df[df['REPORT_TYPE'] == '一季报'].head(3).reset_index(drop=True)
# 去掉数据中NaN的列
df = df.dropna(axis=1)
'''
任务：翻转结果集中的行和列
'''
df = pd.pivot_table(df, columns='REPORT_DATE_NAME')
print(df)
# 预约披露时间-巨潮资讯
# choice of {"沪深京", "深市", "深主板", "创业板", "沪市", "沪主板", "科创板", "北交所"}
# period="2021年报"; 近四期的财务报告; e.g., choice of {"2021一季", "2021半年报", "2021三季", "2021年报"}
# df = ak.stock_report_disclosure(market="沪深京", period="2023一季")
# print(print_markdown(df))
# 财务报表-新浪
# choice of {"资产负债表", "利润表", "现金流量表"}
# df = ak.stock_financial_report_sina(stock="sh600600", symbol="资产负债表")
# print(df)
# 财务指标-新浪
# df = ak.stock_financial_analysis_indicator(symbol="600004")
# print(df)
