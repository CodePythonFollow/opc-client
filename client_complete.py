import os
import requests
from opcua import Client, ua

"""
参考：https://blog.csdn.net/qq_37887537/article/details/84850015  笨笨D幸福
"""


# 指针状态栈
class CurState:
    def __init__(self, parent=None, p=None, d=0):
        self.parent = parent  # unused
        self.p = p
        self.d = d


# opc客户端
class OPCClient:
    # 初始化客户端
    def __init__(self, url):
        self.c = Client(url)

        # 为符合公司平台要求将有关类型进行转换。
        self.node_id_types = {
            'FourByte': 'Numeric',
            'TwoByte': 'Numeric',
            'Numeric': 'Numeric',
            'String': 'String',
            'Guid': 'UUID',
            'ByteString': 'Numeric'
        }
        self.variant_types = {
            'UInt32': 'DWord',
            'Int32': 'Long',
            'UInt64': 'QWord',
            'Int64': 'LongLong',
            'SByte': 'Char'
        }
        self.file = open('Objects.csv', 'a')
        # 记录错误信息， 遇到过一个structure数据类型python源码没有写到
        self.error_msg = {}

    # 利用栈进行遍历（参考网友写法）
    def browser_child(self, root, max_d=-1, ignore=()):
        stack = [CurState(None, root, 0)]
        while len(stack):
            cur = stack.pop()
            name = cur.p.get_node_class().name

            if cur.p.get_browse_name().Name in ignore:
                continue

            if name == "Object":
                self.browser_obj(cur.p, cur.d)
                if 0 < max_d <= cur.d:
                    continue
                for c in cur.p.get_children():
                    stack.append(CurState(cur.p, c, cur.d + 1))

            elif name == 'Variable':
                continue
                # print(''.join(['\b' for _ in range(cur.d)]), end="")
            else:
                self.browser_invalid(cur.p, cur.d)

    # 浏览object，我要的数据
    def browser_obj(self, v, d):
        self.file.close()
        rw = 'R '
        name_index = v.nodeid.NamespaceIndex
        b_name = v.get_display_name().Text
        print(''.join(['  ' for _ in range(d)]), end="")
        print("*%2d:%-30s" %
              (name_index, b_name), rw, d)
        self.file = open(f'{b_name}.csv', 'a', encoding='utf-8')
        self.file.write("*Name,a.k.a,*Identifier,*Identifier type,*Data type,Unit,*Namespace,*R/W,," + '\n')
        for i in v.get_referenced_nodes()[2:]:
            if i.get_node_class().name == 'Variable':
                print(''.join(['  ' for _ in range(d + 1)]), end="")
                self.browser_valid(i)

    #  获取所有有效标签
    def browser_valid(self, v):
        rw = 'R '
        if ua.AccessLevel.CurrentWrite in v.get_access_level():
            rw = "RW"
        try:
            name_index = v.nodeid.NamespaceIndex
            b_name = v.get_display_name().Text
            node_id_type = str(v.nodeid.NodeIdType).split('.')[1]
            variant_type = str(v.get_data_value().Value.VariantType).split('.')[1]
            # variant_type = v.get_data_value().Value
            # print(variant_type.VariantType)

            print("-%2d:%-30s  %s   %-2s  %-23s   " %
                  (name_index, self.transfer_word(str(b_name)), self.node_id_types.get(node_id_type, node_id_type), rw,
                   self.variant_types.get(variant_type, variant_type)), v.nodeid)
            # 保存
            self.file.write(f"{self.transfer_word(b_name)},{b_name},{v.nodeid.Identifier},"
                            f"{self.node_id_types.get(node_id_type, node_id_type)},"
                            f"{self.variant_types.get(variant_type, variant_type)},"
                            f"{''},{ name_index },{'read-only'}" + '\n')

        except Exception as e:
            b_name = v.get_browse_name().Name
            print(f"{'*' * 5}  { b_name } : {e}")
            self.error_msg[b_name] = e

    # 非有效数据
    @staticmethod
    def browser_invalid(v, d):
        # print(v.get_description())
        rw = 'C '
        name_index = v.nodeid.NamespaceIndex
        b_name = v.get_display_name().Text
        print(''.join(['  ' for _ in range(d + 1)]), end="")
        print("@%2d:%-30s  rw: %-2s  node_type:%-23s   " %
              (name_index, b_name, rw, "Method"))

    # 为符合公司要求转拼音
    @staticmethod
    def transfer_word(word):
        url = 'https://api.djapi.cn/pinyins/get'
        data = {
            'cn': word,
            'first_code_in_upper': 1,
            'token': 'ca9d4db3ec610d33f1e803acdf7e484f'
        }
        response = requests.post(url, data=data)
        return response.json()['Result'].replace(' ', '')

    # 连接opc服务并获取第一个节点
    def main_c(self):
        try:
            self.c.connect()
            root = self.c.get_root_node()
            self.browser_child(root.get_child(["0:Objects"]), -1, ["Server"])
        except Exception as e:
            print("Client Exception:", e)
        finally:
            self.c.disconnect()
            self.file.close()
            self.del_empty()
            print("出现错误的信息有：")
            for index, val in self.error_msg.items():
                print(f"{ '*' * 5 } { index } : { val }")

    # 删除空文件夹
    @staticmethod
    def del_empty():
        list_dirs = os.listdir('./')

        for list_dir in list_dirs:
            if '.csv' in list_dir:
                with open(list_dir, 'r', encoding='utf-8') as fi:
                    lines = fi.readlines()
                if len(lines) == 1:
                    os.remove(list_dir)
                    print(f"已删除空文件夹：{list_dir}")


if __name__ == "__main__":
    client = OPCClient("opc.tcp://it-hao4-dong:4840")
    client.main_c()

"""
1、源码修改 ua_binary  里面的decode加上无效字符处理
"""