# opc-client
遍历opc节点将有效数据保存成csv文件

# OPCClient
+ 利用栈将所有节点入栈，并记录等级为了做格式化
+ 当记录到object类型对象增加节点等级。(object就是目录节点)
+ 利用reference方法遍历object对象将Variable类型节点保存到csv文件

# 利用点晴数据api将文字转换为英文
+ https://api.djapi.cn

# 当运行完成会有部分空文件利用os模块删除

# 由于遇到一种数据类型opc-ua库没有进行处理为了防止更多设置错误字典记录
