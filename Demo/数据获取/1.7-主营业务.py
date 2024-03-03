from comm import *

# 获取东财个股主营构成
zygc_em_df = ak.stock_zygc_em(symbol='SZ000651')
# print(zygc_em_df)
'''
任务：找出最新的一次报告
'''
new_date = zygc_em_df.groupby('报告日期')['报告日期'].first().sort_values(ascending=False)[0]
# print(new_date)
new_df = zygc_em_df[zygc_em_df['报告日期'] == new_date]
# print(new_df)

# tushare 上市公司基本信息
pro = ts.pro_api(token)
df = pro.stock_company(ts_code='000651.SZ', fields=[
	"chairman",
	"reg_capital",
	"province",
	"city",
	"employees",
	"main_business",
	"introduction",
	"business_scope"
])
# print(df)

# 同花顺-主营介绍
zyjs_ths_df = ak.stock_zyjs_ths(symbol='000651')
print(zyjs_ths_df)