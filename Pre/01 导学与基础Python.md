# 准备工作
## Python
1. 变量不需要声明，赋值时确定
   2. 区分大小写
2. 基本语法规则
   3. = 赋值
   3. == 数值比较 != 不等于
   4. :表示后面接程序块，往往要缩进了
   4. print(a,b,c) 输出变量，自带空格分割，结束自带换行；print(1/3) 3+中自动取双精度
2. 数据结构
   3. 字符串 str
      4. str=""
      4. 操作可以理解为特殊list的组合："早上好" == [“早”,"上","好"]
      5. 可以直接 for x in STR 将当作list中的元素输出
   3. 列表 list 
      4. l = [] 
      5. l[] .append、del 、len()
      4. 取列表：l(0:2)即[0,2)的内容; l(2:)即[2,length]，l(2:-1)，[l,length-1]
      4. pandas中由更强的pd.Series，带索引的有序列表
   4. 集合 set  无序，**无索引**，**无重复**（适合无重复的结构）
      5. s = {} s = set(l)
      6. 不支持索引 判断是否在 2 in s、2 not in s 
   5. 字典 dict 赋值
      6. d = {'a' : 1, ‘c’ : x} ，可以赋任意类型
      7. d['']、del
      8. 判断是否在 'a' in d
      9. d['c'][:2]，取出某列表，再取其中部分
   6. 元组 tuple 有序，**不可修改**，可重复（适合不可修改的结构）
      7. t=() t[]
6. 标识符：
7. 注释单行#、注释段三个```
8. 代码块分块：靠缩进，用\分割；一段代码用相同的缩进都可允许
9. 模块导入：import module、from method import module、import module as mName
10. 基本语句：略
    11. while、for、continue、break、pass特殊标记，表示什么都不做
12. 函数与错误处理
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
   2. dir(module)、help()
   3. 常见模块：
      4. math：数据标准化、求统计值
      5. datetime：时间戳
      6. random：数据采样生成
      7. file：存储
      8. re
      9. sys
2. 三方库
   3. NumPy
   4. SciPy:数学科学工程
   5. Matplotlib
   6. pandas
      7. import pandas as pd
      7. pd.__version__：查看版本号
   7. 机器学习
      8. scikit-learn：机器学习
      9. OpenCV：图像处理
      10. NLTK：自然语言
      11. Gensim：自然语言
12. 平台
    13. TensorFlow
    14. PyTorch
    15. PaddlePaddle
16. pip
    17. pip install tensorflow
    18. pop search
    19. pip list
    20. 切换镜像源：请搜索
21. Anaconda：Baoguanliqi、编辑器、环境管理器
    22. 预装150+以来、提供250+可选开源
    23. conda install module 如果没有报，则用pip install
    24. conda update/upgrade module 或者 pip install --upgrade module
23. 配置环境
    24. anaconda-spyder
    24. pycharm