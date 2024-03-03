from comm import *
'''
任务：对龙虎榜机构大致解读

1. 龙虎榜详情
2. 查询个股详细机构数据
3. 查看当日该营业部还购买了什么股
4. 查看营业部月排行和统计数据
'''

# 龙虎榜详情
df = ak.stock_lhb_detail_em(start_date='20230601', end_date='20230601')
print(df)
# # 循环输出每一行数据
for index, row in df.iterrows():
	code = row['代码']
	# 获取个股龙虎榜详情
	stock_detail_df = ak.stock_lhb_stock_detail_em(symbol=code, date='20230601', flag='买入')
	# 统一名称
	stock_detail_df = stock_detail_df.rename(columns={'交易营业部名称': '营业部名称'})
	# 每日活跃营业部
	lhb_hyyyb_df = ak.stock_lhb_hyyyb_em(start_date='20230601', end_date='20230601')
	# 根据指定字段，进行合并操作
	detail_and_hyyyb_df = pd.merge(stock_detail_df, lhb_hyyyb_df, on='营业部名称', how='inner')
	# 营业部统计
	lhb_traderstatistic_df = ak.stock_lhb_traderstatistic_em(symbol='近一月')
	# 根据指定字段，进行left类型的合并
	detail_and_hyyyb_and_traderstatistic_df = pd.merge(detail_and_hyyyb_df, lhb_traderstatistic_df, on='营业部名称',
													   how='left')
	# 将字符中指定部分去掉
	detail_and_hyyyb_and_traderstatistic_df['营业部名称'] = detail_and_hyyyb_and_traderstatistic_df['营业部名称'] \
		.str.replace('股份有限公司', '').str.replace('有限责任公司', '').str.replace('有限公司', '')
	# 营业部排行
	lhb_yybph_df = ak.stock_lhb_yybph_em(symbol='近一月')
	res_df = pd.merge(detail_and_hyyyb_and_traderstatistic_df, lhb_yybph_df, on='营业部名称', how='left')

	print("-" * 100)
	print(f"当前股票：{code} - {row['名称']} - {row['解读']}")
	print("*" * 100)
	for i_index, r_row in res_df.iterrows():
		print(f"营业部名称：{r_row['营业部名称']}, "
			  f"当前股票 --> 买入占比：{r_row['买入金额-占总成交比例']}, 卖出占比：{r_row['卖出金额-占总成交比例']}, 净额：{r_row['净额']}, "
			  f"其它交易 ---> 买入股票：{r_row['买入股票']}, 净额：{r_row['总买卖净额']}, "
			  f"近一个月龙虎榜成交金额：{r_row['龙虎榜成交金额']}, "
			  f"上榜后10天-平均涨幅：{r_row['上榜后10天-平均涨幅']}")
	sleep()
