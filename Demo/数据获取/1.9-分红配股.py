from comm import *

# 分红配股整体情况
df = ak.stock_fhps_em(date='20221231')
'''
任务：假设小红投资5万元钱，这5万元买哪只股票获取分红最多
'''
print(df)
# 将NaN数据填充0
df = df.fillna(0)
# 过滤数据
df = df[df['现金分红-股息率'] > 0]
df['股价'] = ((df['现金分红-现金分红比例'] / 10) / df['现金分红-股息率']).round(2)
df['买入数量'] = (((50000 / df['股价']) / 100) * 100).astype(int)
df['分红收益'] = (df['买入数量'] * (df['现金分红-现金分红比例'] / 10)).round(2)
df = df.sort_values(by='分红收益', ascending=False).reset_index(drop=True).head(10)
print(tabulate(df, headers='keys', tablefmt='github'))

# 个股分红配股情况
fhps_detail_em_df = ak.stock_fhps_detail_em(symbol='601699')
print(fhps_detail_em_df)

