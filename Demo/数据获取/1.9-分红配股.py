from common import *

# 一、某日期市场的分红配股整体情况，k.stock_fhps_em
df = ak.stock_fhps_em(date='20221231')
# 将NaN数据填充0
df = df.fillna(0)
print(df)

'''
任务：假设小红投资5万元钱，这5万元买哪只股票获取分红最多
'''
# 过滤数据，计算出股价、固定价格的买入数量、分红收益，取出前10条分红收益最高的
# 在分红之前买进，波动又不大时，那么是很赚的
df = df[df['现金分红-股息率'] > 0]
df['股价'] = ((df['现金分红-现金分红比例'] / 10) / df['现金分红-股息率']).round(2)
df['买入数量'] = (((50000 / df['股价']) / 100) * 100).astype(int)
df['分红收益'] = (df['买入数量'] * (df['现金分红-现金分红比例'] / 10)).round(2)
df = df.sort_values(by='分红收益', ascending=False).reset_index(drop=True).head(10)
print(tabulate(df, headers='keys', tablefmt='github'))


# 二、某个个股的分红配股情况
fhps_detail_em_df = ak.stock_fhps_detail_em(symbol='601699')
print(fhps_detail_em_df)

