# 准备工作
## Python
1. 变量不需要声明，赋值时确定
   1. 区分大小写
2. 基本语法规则
   1. = 赋值
   2. == 数值比较 != 不等于
   3. :表示后面接程序块，往往要缩进了
   4. print(a,b,c) 输出变量，自带空格分割，结束自带换行；print(1/3) 3+中自动取双精度
3. 数据结构
   1. 字符串 str
      1. str=""
      2. 操作可以理解为特殊list的组合："早上好" == [“早”,"上","好"]
      3. 可以直接 for x in STR 将当作list中的元素输出
   2. 列表 list 
      1. l = [] 
      2. l[] .append、del 、len()
      3. 取列表：l(0:2)即[0,2)的内容; l(2:)即[2,length]，l(2:-1)，[l,length-1]
      4. pandas中由更强的pd.Series，带索引的有序列表
   3. 集合 set  无序，**无索引**，**无重复**（适合无重复的结构）
      1. s = {} s = set(l)
      2. 不支持索引 判断是否在 2 in s、2 not in s 
   4. 字典 dict 赋值
      1. d = {'a' : 1, ‘c’ : x} ，可以赋任意类型
      2. d['']、del
      3. 判断是否在 'a' in d
      4. d['c'][:2]，取出某列表，再取其中部分
   5. 元组 tuple 有序，**不可修改**，可重复（适合不可修改的结构）
      1. t=() t[]
4. 标识符：
5. 注释单行#、注释段三个```
6. 代码块分块：靠缩进，用\分割；一段代码用相同的缩进都可允许
7. 模块导入：import module、from method import module、import module as mName
8. 基本语句：略
   11. while、for、continue、break、pass特殊标记，表示什么都不做
9. 函数与错误处理
   13. def func1(): 换行缩进 代码块、 func1()调用
       14. 当无return语句没有时，会用最后一句赋值的结果，如果没有赋值的语句就返回空
   14. def func2(var)、func(2)
   15. try:~、except 错误名:~、 else:没错执行的内容
       16. try: 
       17. except Exception as e: print(e)
       17. except TypeError as e:
       18. excpet: print(e)Paas：语法完备跳过

## Python扩展包与环境
1. 标准库
   1. dir(module)、help()
   2. 常见模块：
      1. math：数据标准化、求统计值
      2. datetime：时间戳
      3. random：数据采样生成
      4. file：存储
      5. re
      6. sys
2. 三方库
   1. NumPy：灵活
   2. SciPy：灵活，数学科学工程
   3. Matplotlib：统计绘图
   4. **pandas**——数据底层框架
      1. import pandas as pd
      2. pd.__version__：查看版本号
   5. **statsmodels**：基本的数据建模
   6. 机器学习
      1. **scikit-learn**：机器学习的数据建模
      2. OpenCV：图像处理
      3. NLTK：自然语言
      4. Gensim：自然语言
3. 平台
   1. TensorFlow
   2. PyTorch
   3. PaddlePaddle
4. pip
   1. pip install tensorflow
   2. pop search
   3. pip list
   4. 切换镜像源：请搜索
5. Anaconda：Baoguanliqi、编辑器、环境管理器
   1. 预装150+以来、提供250+可选开源
   2. conda install module 如果没有报，则用pip install
   3. conda update/upgrade module 或者 pip install --upgrade module
6. 配置环境
   1. anaconda-spyder
   2. pycharm