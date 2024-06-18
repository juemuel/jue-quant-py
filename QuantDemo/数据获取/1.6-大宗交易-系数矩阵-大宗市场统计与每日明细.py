from common import *

# 每日统计
dzjy_mrtj_df = ak.stock_dzjy_mrtj(start_date='20220609', end_date='20220609')
# print(dzjy_mrtj_df)
'''
任务：计算相关系数矩阵
'''
corr_matrix = dzjy_mrtj_df[['折溢率', '成交总量', '成交总额/流通市值', '涨跌幅']].corr()
print(corr_matrix)
# 通过分析，我们大发现 部分列与涨跌幅的相关度较高，我们进一步验证
dzjy_mrtj_df['涨跌幅'] = dzjy_mrtj_df['涨跌幅'].astype(float)
print(dzjy_mrtj_df.sort_values(by='涨跌幅', ascending=False))


# 市场统计
dzjy_sctj_df = ak.stock_dzjy_sctj()
print(dzjy_sctj_df)
# m每日明细
dzjy_mrmx_df = ak.stock_dzjy_mrmx(symbol='A股', start_date='20220518', end_date='20230518')
print(dzjy_mrmx_df)
