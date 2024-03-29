# -*- coding: utf-8 -*-
"""
Created on Thu Sep 24 21:42:48 2020

@author: njucsxh
"""
# 不标准的情况：
# WHERE,SELECT,ASK没有大写
# 代求变量多于实际数量，不写代求变量
# 完整链接的生成，应该严格按照前缀，简写形式的生成，才需要字典，确认一下
'''
PREFIX xsd:<http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?uri WHERE { 
?uri <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://dbpedia.org/ontology/Song> . 
?uri <http://dbpedia.org/ontology/artist> <http://dbpedia.org/resource/Bruce_Springsteen> . 
?uri <http://dbpedia.org/ontology/releaseDate> ?date . 
FILTER (?date >= '1980-01-01'^^<http://www.w3.org/2001/XMLSchema#date> && ?date <= '1990-12-31'^^<http://www.w3.org/2001/XMLSchema#date>) }

PREFIX xsd:<http://www.w3.org/2001/XMLSchema#> SELECT DISTINCT ?uri WHERE { ?uri <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://dbpedia.org/ontology/Song> . ?uri <http://dbpedia.org/ontology/artist> <http://dbpedia.org/resource/Bruce_Springsteen> . ?uri <http://dbpedia.org/ontology/releaseDate> ?date . FILTER (?date >= '1980-01-01'^^xsd:date && ?date <= '1990-12-31'^^xsd:date) }

还需要一个处理;共用主语形式的normalize
'''
# 遇到的小细节
# <http://.*?>多写点，不要只写<>以为filter里面有<>=
# link或者abbr都应该是针对whered ，former不应该处理
# where,filter都可以小写的

import re

import socket

from SPARQLWrapper import SPARQLWrapper, JSON



class RegexDict(dict):
    import re
    def __init__(self, *args, **kwds):
        self.update(*args, **kwds)

    def __getitem__(self, required):
        for key in dict.__iter__(self):
            if self.re.match(key, required):
                return dict.__getitem__(self, key)


# {}前后空格，末尾没有.，变量统一，去前缀，
class SPARQL(object):
    def __init__(self, raw_sparql, *filename):
        self.raw_sparql = raw_sparql
        try:
            self.filename = filename[0]
        except:
            self.filename = '123'
        self.pre_map = {
            'prop': '<http://dbpedia.org/property/>',
            'owl': '<http://www.w3.org/2002/07/owl#>',
            'dbp': '<http://dbpedia.org/property/>',
            'dct': '<http://purl.org/dc/terms/>',
            'res': '<http://dbpedia.org/resource/>',
            'dbo': '<http://dbpedia.org/ontology/>',
            'skos': '<http://www.w3.org/2004/02/skos/core#>',
            'db': '<http://dbpedia.org/>',
            'yago': '<http://dbpedia.org/class/yago/>',
            'onto': '<http://dbpedia.org/ontology/>',
            'rdfs': '<http://www.w3.org/2000/01/rdf-schema#>',
            'foaf': '<http://xmlns.com/foaf/0.1/>',
            'dbr': '<http://dbpedia.org/resource/>',
            'dbc': '<http://dbpedia.org/resource/Category:>',
            'dbpedia2': '<http://dbpedia.org/property/>'
        }

        self.map_pre = RegexDict({
            '<http://dbpedia.org/>': 'db',
            '<http://dbpedia.org/class/yago/.*?>': 'yago',
            '<http://dbpedia.org/ontology/.*?>': 'dbo',
            '<http://dbpedia.org/property/.*?>': 'dbp',
            '<http://dbpedia.org/resource/.*?>': 'dbr',
            '<http://dbpedia.org/resource/Category:>': 'dbc',
            '<http://purl.org/dc/terms/.*?>': 'dct',
            '<http://www.w3.org/1999/02/22-rdf-syntax-ns#>': 'rdf',
            '<http://www.w3.org/2000/01/rdf-schema#>': 'rdfs',
            '<http://www.w3.org/2001/XMLSchema#>': 'xsd',
            '<http://www.w3.org/2002/07/owl#>': 'owl',
            '<http://xmlns.com/foaf/0.1/>': 'foaf',
            '<http://www.w3.org/2004/02/skos/core#>': 'skos',
            'http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#' : 'dul'
        })
        self.normalize()
        self.set_sparql()  # link_sparql
        self.set_former()  
        self.set_where()  
        self.set_intent()  
        if self.intent != 'ASK':
            self.set_vars()  # 设置firstVar,allVar,处理冗余变量，如果有冗余变量，会重新设置former（where不变不用再写一次）
        else:
            self.firstVar = 'UNK'
            self.all_var = []
        self.set_variable_normalize()
        self.set_abbr_sparql()  # abbr_sparql，abbr_where也处理了
        self.set_link_sparql()  # link_sparql
        self.set_abbr_where()  # abbr_where
        self.set_link_where()  # link_where
        self.set_abbr_triple_list()  # abbr_triple_list

        self.set_link()  # 所有的链接
        self.set_constrain()  # constrain
        self.set_triple_info()  # 

        self.set_template()  # 替换链接为<E/R>
        self.set_former_template()  # former的模板
        self.set_where_template()  # 
        self.set_host_ip()  # ip

        self.set_union()
        self.set_filter()
        self.set_having()
        self.set_order()
        self.set_bind()
        self.set_contain()
        self.set_group()
        self.set_optional()

        # self.draw()#画图，文件名暂无好办法

    def normalize(self):

        # 去连续空格，前后空格，{}旁边的空格
        self.sparql = ' '.join(self.raw_sparql.split())  # 去连续空格
        self.sparql = self.sparql.replace('. }', '}')  # 去掉最后一句的句号
        self.sparql = self.sparql.replace(' }', '}')  # 去掉}前的空格
        self.sparql = self.sparql.replace('{ ', '{')  # 去掉{后的空格
        self.sparql = ' '.join(self.sparql.split())  # 去连续空格
        self.sparql = self.sparql.strip()  # 去前后空格

    def set_sparql(self):  # 转换成<http://>完整形式
        '''只处理where部分，处理former没有意义'''
        string = self.sparql
        where_start = string.find('WHERE')  # where开始的地方
        # query_start是有PREFIX的时候select（former）开始的地方
        # 有前缀
        if string.find('PREFIX') != -1:  # 有PREFIX，先找到他给的词典，和正文开始的地方SELECT，在用他给的词典还原
            # 但是对于通用的rdf:type，xsd:data是可以不给前缀的
            pattern_pre = re.compile(r'PREFIX .+?>')
            pre_list = pattern_pre.findall(string)  # 所有前缀
            temp_dic = {}
            for item in pre_list:
                index_split = item.find(':<http://')  # 先找到：
                former_part = item[:index_split]  # PREFIX dbr:<>可以    PREFIX dbr : <>是非法的
                abbr_part = former_part.replace('PREFIX', '').replace('prefix', '').strip()  # 大小写都合法
                link_part = item[index_split + 1:].strip()  # 完整链接
                temp_dic[abbr_part] = link_part
            # query正文开始（前缀后面）
            # 最后一个前缀,为了获取正文
            last_pre = pre_list[[string.find(p) for p in pre_list].index(max([string.find(p) for p in pre_list]))]
            # 正文
            query_start = string.find(last_pre) + len(last_pre) + 1

            for pre in temp_dic.keys():
                while string.find(pre + ':', where_start) != -1:  # 找得到dbo:这种
                    content_start_index = string.find(pre + ':', where_start) + len(pre) + 1  # content开始的地方,加一是：的位置
                    # dbo:content content 就是content
                    # 下面两行应对 dbr:content}}的情况，如果没有空格，那么查询结果为-1,还原的时候会少一个},所以如果没找到空格，就找}
                    # <http://dbpedia.org/resource/Mean_Hamster_Software}>}，模板也会少一个}
                    space_valid = string.find(' ', content_start_index)  # 找:后面的空格
                    brack_valid = string.find('}', content_start_index)  # 找:后面的}
                    if space_valid == -1:
                        content_end_index = brack_valid
                    else:
                        content_end_index = space_valid
                    content = string[content_start_index:content_end_index]
                    # 整个缩写的的部分 dbr:xxx
                    abbr_format = string[content_start_index - len(pre) - 1:content_end_index]  # -1是：的位置
                    # 完整格式
                    new_format = temp_dic[pre][:-1] + content + '>'  # -1去掉原来的>
                    # 替换
                    string = string.replace(abbr_format, new_format)
        else:  # 没有PREFIX，用通用词典
            query_start = 0  # 全部是正文
            for pre in self.pre_map.keys():
                while string.find(pre + ':', where_start) != -1:
                    content_start_index = string.find(pre + ':', where_start) + len(pre) + 1
                    # dbo:content content 就是content
                    space_valid = string.find(' ', content_start_index)  # 找:后面的空格
                    brack_valid = string.find('}', content_start_index)  # 找:后面的}
                    if space_valid == -1:
                        content_end_index = brack_valid
                    else:
                        content_end_index = space_valid
                    content = string[content_start_index:content_end_index]
                    # 前缀形式的部分
                    pre_format = string[content_start_index - len(pre) - 1:content_end_index]
                    # 完整格式
                    new_format = self.pre_map[pre][:-1] + content + '>'
                    # 替换
                    string = string.replace(pre_format, new_format)

        self.sparql = string[query_start:]

    def set_former(self):
        self.former = self.sparql[:self.sparql.find('WHERE')].strip()

    def set_where(self):
        self.where = self.sparql[self.sparql.find('WHERE'):].strip()

    def set_vars(self):
        '''sparql中所有的变量
        把变量冗余也放在这里处理，分成former和where两个部分找var，如果former里的变量没有出现在where中 且 这个变量前面没有AS这种重命名符号
        那么在self.sparql中替换这个变量为空，由于init函数中set_var前面还有set_former，这个需要重做
        where,former只能当一个工具，原版的数据，还要加两个属性abbr的和link的
        '''
        all_var = []

        def find_variable(substr):
            end_index = 999
            if substr.find(' ') != -1:
                end_index = min(end_index, substr.find(' '))
            if substr.find(')') != -1:
                end_index = min(end_index, substr.find(')'))
            if substr.find('}') != -1:
                end_index = min(end_index, substr.find('}'))
            if substr.find(';') != -1:
                end_index = min(end_index, substr.find(';'))
            if substr.find(',') != -1:
                end_index = min(end_index, substr.find(','))
            if substr.find('.') != -1:
                end_index = min(end_index, substr.find('.'))
            return end_index

        # 先求former中的var
        former_var = []
        end_index = 0
        start_inde = 0
        sparql_query = self.former
        while sparql_query.find('?', end_index) != -1:
            start_index = sparql_query.find('?', end_index)
            end_index = find_variable(sparql_query[start_index:])
            former_var.append(sparql_query[start_index:end_index + start_index])
            end_index += start_index
        # 再求where中的var
        where_var = []
        end_index = 0
        start_inde = 0
        sparql_query = self.where
        while sparql_query.find('?', end_index) != -1:
            start_index = sparql_query.find('?', end_index)
            end_index = find_variable(sparql_query[start_index:])
            where_var.append(sparql_query[start_index:end_index + start_index])
            end_index += start_index
        # 判断有没有异常（former里有但是where里根本没有）（找变量只要找where就可以了，former里面可能有重命名，判断一下有没有AS就行了）
        for fv in former_var:
            if fv not in where_var:
                if 'AS' not in self.former[:self.former.find(fv)] or 'as' not in self.former[:self.former.find(fv)]:
                    self.sparql = self.sparql.replace(fv, '')
                    self.set_former()
        # 一般主变量都是former里的第一个，这样写对付select *这种情况
        if len(former_var) != 0:
            self.firstVar = former_var[0]
        else:
            self.firstVar = where_var[0]
        self.all_var = list(set(where_var))

    def set_abbr_sparql(self):
        string = self.sparql
        if string.find('PREFIX') != -1:  # 有前缀的格式,只留正文
            pattern_pre = re.compile(r'PREFIX .+?>')
            pre_list = pattern_pre.findall(string)  # 所有前缀
            # 最后一个prefix
            last_pre = pre_list[[string.find(p) for p in pre_list].index(max([string.find(p) for p in pre_list]))]
            query_start = string.find(last_pre) + len(last_pre) + 1  # 正文开始的     索引
            string = string[query_start:]  # 取query正文

        # 有些有前缀和没有前缀混合的，还有只有有前缀形式的，把有前缀的转换掉
        pattern = re.compile('<http://.+?>')
        full_format = pattern.findall(string)  # 所有完整的uri
        for x in full_format:
            content = x[max(x.rfind('/'), x.rfind('#')) + 1:-1]  # 获取内容
            full_uri = x
            pre_uri = self.map_pre[x[:max(x.rfind('/'), x.rfind('#')) + 1] + '>'] + ':' + content
            string = string.replace(full_uri, pre_uri)

            # 检查不标准的缩写 onto,res,感觉用不到
            '''
        for pre in self.pre_map.keys():
            if pre not in self.map_pre.values():#不标准，如果标准的也处理会陷入死循环
                while string.find(pre+':')!=-1:#有这种缩写
                    abr_start=string.find(pre+':')
                    abr_stop=abr_start+len(pre)
                    ill_form=string[abr_start:abr_stop]#现在的格式#
                    standard_form=self.map_pre[self.pre_map[ill_form]]
                    #替换
                    string=string.replace(ill_form,standard_form)         
                    '''
        self.abbr_sparql = string



        

    def set_link_sparql(self):
        self.link_sparql = self.sparql

    def set_abbr_where(self):
        self.abbr_where = self.abbr_sparql[self.abbr_sparql.find('WHERE'):].strip()

    def set_link_where(self):
        self.link_where = self.link_sparql[self.link_sparql.find('WHERE'):].strip()

    def set_abbr_triple_list(self):
        abbr_triple_content = self.abbr_where.replace('}', '').replace('{', '').replace('WHERE', '').replace('where',
                                                                                                             '').strip()
        self.abbr_triple_list = list(map(lambda x: x.strip(), abbr_triple_content.split('. ')))

    def set_triple_info(self):
        self.triple_num = len(self.where.split('. '))
        triple_content = self.where.replace('}', '').replace('{', '').replace('WHERE', '').replace('where', '').strip()
        self.triple_list = list(map(lambda x: x.strip(), triple_content.split('. ')))

    # TODO不完善，约束可能在WHERE里面
    def set_constrain(self):
        self.constrain = self.sparql[self.sparql.find('}') + 1:]

    def set_link(self):
        ''''所有链接，考虑了xsd:data和rdf:type'''
        pattern = re.compile('<http://.+?>')
        result = re.findall(pattern, self.sparql)
        if 'xsd:data' in self.sparql:
            result.append('xsd:data')
        if 'a' in self.sparql or 'rdf:type' in self.sparql:
            result.append('rdf:type')
        self.link = result

    def set_template(self):
        self.template = re.sub('<http://.+?>', '<E/R>', self.sparql)

    def set_former_template(self):
        self.former_template = self.template[:self.template.find('WHERE')].strip()

    def set_where_template(self):
        self.where_template = self.template[self.template.find('WHERE'):].strip()

    def set_union(self):
        self.union = 'UNION' in self.sparql

    def set_filter(self):
        self.filter = 'FILTER' in self.sparql

    def set_having(self):
        self.having = 'HAVING' in self.sparql

    def set_order(self):
        self.order = 'ORDER' in self.sparql

    def set_bind(self):
        self.bind = 'BIND' in self.sparql

    def set_contain(self):
        self.contain = 'contain' in self.sparql

    def set_group(self):
        self.group = 'GROUP' in self.sparql

    def set_optional(self):
        self.optional = 'OPTIONAL' in self.sparql

    def set_variable_normalize(self):
        # 把sparql的变量统一，有序，有VAR3一定有VAR2,VAR1
        try:
            firstVar, allVariable = self.firstVar, self.allVar
            # 构造映射关系
            inter_var = ['?VAR1', '?VAR2', '?VAR3',
                         '?VAR4']  # 一定要选取肯定没有在原始SPARQL中使用的变量名，假如你把?x换成了?y,?y在原SPARQL中出现了，那么?y也要映射到其他变量，相当于?x和?y成了一个变量
            sparql = self.sparql.replace(firstVar, '?MAINVAR')
            inter_index = 0  # inter_var用到第几号了
            for i in range(len(allVariable)):
                if allVariable[i] != firstVar:
                    sparql = sparql.replace(allVariable[i], inter_var[inter_index])
                    inter_index += 1
            sparql = sparql.replace('?MAINVAR', '?uri')
            self.sparql = sparql
        except:
            pass

    def set_host_ip(self):
        """查询本机ip地址"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        finally:
            s.close()
        self.ip_address = ip

    def query(self):
        #sparql = SPARQLWrapper('http://' + self.ip_address + ':8890/sparql')
        # HXX完整DBpedia
        sparql = SPARQLWrapper("https://api.triplydb.com/datasets/academy/pokemon/services/pokemon/sparql")
        sparql.setQuery(self.raw_sparql)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()  # json,type为dict
        self.answer = self.answer_convert(results)
        return self.answer

    def answer_convert(self, item_answer):

        if 'boolean' in item_answer.keys():
            at = 'boolean'
        else:
            at = item_answer['head']['vars'][0]
        answer = []
        if at == 'boolean':
            answer.append(item_answer['boolean'])
        else:
            for cand in item_answer['results']['bindings']:
                if at == 'date':
                    answer.append(cand['date']['value'])
                elif at == 'number':
                    answer.append(cand['c']['value'])
                elif at == 'resource' or at == 'uri':
                    answer.append(cand['uri']['value'])
                elif at == 'string':
                    answer.append(cand['string']['value'])
                elif at == 'callret-0':
                    answer.append(cand['callret-0']['value'])
                else:  # 貌似都是这个套路，不知道还有什么类型
                    answer.append(cand[at]['value'])
        return answer

    def set_intent(self):
        if 'ASK' in self.former:
            self.intent = 'ASK'
        elif 'COUNT' in self.former:
            self.intent = 'COUNT'
        else:
            self.intent = 'SELECT'

    def draw(self):
        from graphviz import Digraph
        dot = Digraph(format='jpg')

        dot.attr(label=self.abbr_sparql)

        for triple in self.abbr_triple_list:
            if len(triple.split(' ')) != 3:
                continue
            if 'FILTER' in triple:
                pass
            head = triple.split(' ')[0]
            relation = triple.split(' ')[1]
            tail = triple.split(' ')[2]
            if head == self.firstVar:
                dot.node(head.split(':')[-1], head, shape='diamond')
            else:
                dot.node(head.split(':')[-1], head)
            if tail == self.firstVar:
                dot.node(tail.split(':')[-1], tail, shape='diamond')
            else:
                dot.node(tail.split(':')[-1], tail)
            dot.edge(head.split(':')[-1], tail.split(':')[-1], relation)

        dot.render(self.filename, 'parser/', format='jpg', cleanup=True)






