# 数据管理与Pandas
## 统计软件
需要二维表
1. SPSS
2. Stata
3. RGui,R语言
4. Python-Pandas
## Pandas
事实上的二维表结构 ，用Spyder+DataFrame更清晰；也可以导入导出为数据库、R等外部工具互通提供了简单的接口
以下内容按照统计分析的功能，主要是列数据的操作
### 获取数据与保存数据
1. 新建数据框DATAFrame：pd.DATAFrame(data=[],COLUMNS=[])
   1. 每行是list的增强版：
   2. 表头内容用类似Dict实现，实际上是Series
   3. 索引列（带索引）：pd.Series(data=[],name=[])
2. 读入与保存
   1. 读取csv、txt文件、保存文件
         ```PYTHON
         pd.read_csv("eng.csv", encoding="gbk") # 常用；默认分割符逗号
         pd.read_table("eng.csv", sep=",", encoding="gbk") # 不常用；默认分隔符是制表符/t，可以seq设置,
         to_csv()
      ```
   2. 读取excel文件、保存excel文件
         ```PYTHON
         pd.read_excel("eng.xlsx", sheet_name="full")
         # 默认第一个，也可以是数字，0第一个，1第2个
         to_excel()
         ```
   3. 其他读入命令与保存命令
         ```PYTHON
         # read_clipboard to_clipboard #剪贴板保存
         # read_json
         # read_html to_html
         # read_stata to_stata
         # read_sas sas不能保存，得付钱
         # read_spss pyreadstats.write_sav
         # read_sql，read_sql_query，read_sql_table，to_sql
         ```
   4. DataFrame转其它数据格式
         ```PYTHON
         ```
### 清晰、整理
1. 行筛选
   2. 
2. 列操作
### 统计图表
