# coding=utf-8
from sys import path
import os
# __file__ = r'D:\Lgb\pythonstudy\longgb\Allocation\data_process_batch_my.py'
import sys
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
pth=os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath("")))))
path.append(pth)
import  pandas as pd
import datetime
from collections import defaultdict,OrderedDict
import cPickle as pickle
import numpy as np
from inventory_process_batch_my_linux import inventory_proess
import configServer_my_linux as configServer
import  logging
import time


def printruntime(t1, name):
    '''
    性能测试，运行时间
    '''
    d = time.time() - t1
    min_d = np.floor(d / 60)
    sec_d = d % 60
    hor_d = np.floor(min_d / 60)
    if hor_d >0:
        print 'Run Time ({3}) is : {2} hours {0} min {1:.4f} s'.format(min_d, sec_d, hor_d, name)
    else:
        print 'Run Time ({2}) is : {0} min {1:.4f} s'.format(min_d, sec_d, name)


def datelist(start, end):
    start_date = datetime.datetime.strptime(start,'%Y-%m-%d')
    end_date = datetime.datetime.strptime(end,'%Y-%m-%d')
    result = []
    curr_date = start_date
    while curr_date != end_date:
        result.append("%04d-%02d-%02d" % (curr_date.year, curr_date.month, curr_date.day))
        curr_date += datetime.timedelta(1)
    result.append("%04d-%02d-%02d" % (curr_date.year, curr_date.month, curr_date.day))
    return result


def gene_index(fdc,sku,date_s=''):
    '''
    #生成调用索引,将在多个地方调用该函数
    '''
    return date_s+fdc+sku


# ================================================================================
# =                                 （1）日志信息设置                             =
# ================================================================================
# 日志记录部分
# 创建一个logger
logger = logging.getLogger('allocation .. logger')
logger.setLevel(logging.DEBUG)
# 创建一个handler，用于写入日志文件
fh = logging.FileHandler(configServer.log_path)
fh.setLevel(logging.DEBUG)
# 再创建一个handler，用于输出到控制台
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# 定义handler的输出格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# 给logger添加handler
logger.addHandler(fh)
logger.addHandler(ch)


# ================================================================================
# =                                 （2）仿真参数设置                             =
# ================================================================================
##标记仿真的开始和结束日期
start_date='2016-10-01'#'2016-10-01'
end_date='2016-10-03'

# 指定数据相关路径，数据加载分批加载清除操作，sale数据与sku数据按照三天的频次进行更新，即对应的字典中只保存三天的数据
# sku： 10-01：一天数据
# sku_data_path='/home/cmo_ipc/Allocation_shell/datasets/data_total3/total_sku/2016-10-01.pkl'
sku_data_path=configServer.sku_data_path
# fdc： 全量数据
# fdc_data_path='/home/cmo_ipc/Allocation_shell/datasets/data_total3/fdc_data.pkl'
fdc_data_path=configServer.fdc_data_path
# fdcinv: 10-01：一天数据
# fdc_initialization_inv='/home/cmo_ipc/Allocation_shell/datasets/data_total3/total_fdcinv/2016-10-01.pkl'
fdc_initialization_inv=configServer.fdc_initialization_inv
# 调拨单放全量数据
# order_data_path='/home/cmo_ipc/Allocation_shell/datasets/data_total3/order_data.pkl'
order_data_path=configServer.order_data_path
# sale每次增加一天数据，开始放一天数据即可
# sale_data_path_batch='/home/cmo_ipc/Allocation_shell/datasets/data_total3/total_sale/'
sale_data_path=configServer.sale_data_path_batch
# 数据集存储路径
save_data_path=configServer.save_data_path


# ================================================================================
# =                                 （3）数据读取                                 =
# ================================================================================
test_t2 = time.time()
test_t1 = time.time()
# （1）SKU 数据读取， 10-01
logger.info('开始读取sku数据并转化')
pkl_sku=open(sku_data_path)
allocation_sku_data=pickle.load(pkl_sku)
pkl_sku.close()
#allocation_sku_data.columns= ['sku_id','forecast_daily_override_sales','variance','ofdsales','inv','white_flag',
#                               'white_flag_01','date_s','dc_id','variance_ofdsales','std']
allocation_sku_data.columns= ['sku_id','mean_sales','variance','ofdsales','inv','white_flag',
                              'white_flag_01','date_s','dc_id','variance_ofdsales','std']
logger.info('SKU数据读取完成')
printruntime(test_t1, 'SKU表数据读取')

test_t1 = time.time()
# （2）FDC 数据读取， 全量
logger.info('开始读取fdc数据并转化')
pkl_fdc=open(fdc_data_path)
allocation_fdc_data=pickle.load(pkl_fdc)
pkl_fdc.close()
allocation_fdc_data.columns=['org_from','org_to','actiontime_max','alt','alt_cnt']
logger.info('fdc数据读取完成')
printruntime(test_t1, 'fdc表数据读取')

test_t1 = time.time()
# （3）fdcinv 数据读取， 10-01
logger.info('fdc初始化库存数据读取')
pkl_fdc_initialization=open(fdc_initialization_inv)
allocation_fdc_initialization=pickle.load(pkl_fdc_initialization)
pkl_sku.close()
allocation_fdc_initialization.columns=['sku_id','open_po_fdc','inv','date_s','dc_id']
logger.info('fdc初始化库存数据读取完成')
printruntime(test_t1, 'fdcinv表数据读取')

test_t1 = time.time()
# （4）fdcinv 数据读取， 10-01
logger.info('开始读取order数据并转化')
pkl_order=open(order_data_path)
allocation_order_data=pickle.load(pkl_order)
pkl_order.close()
allocation_order_data.columns=['arrive_time','item_sku_id','arrive_quantity','dc_id']
logger.info('order数据读取完成')
printruntime(test_t1, 'order表数据读取')

test_t1 = time.time()
# （5）date_range 生成
#仿真的时间窗口 时间格式如下：2016-11-29
date_range=datelist(start_date,end_date)
logger.info('开始读取详单明细数据')

# （5）sale 数据读取
pkl_sale=[]
for p in date_range:
    pkl_sale_mid=open(sale_data_path+p+'.pkl')
    mid_allocation_sale_data=pickle.load(pkl_sale_mid)
    pkl_sale.append(mid_allocation_sale_data)
    pkl_sale_mid.close()
allocation_sale_data=pd.concat(pkl_sale)
# pkl_sale = open(sale_data_path)
# allocation_sale_data = pickle.load(pkl_sale)
# pkl_sale.close()
allocation_sale_data.columns=['org_dc_id', 'sale_ord_det_id', 'sale_ord_id', 'parent_sale_ord_id','item_sku_id',
                              'sale_qtty', 'sale_ord_tm', 'sale_ord_type', 'sale_ord_white_flag','white_flag_01',
                              'item_third_cate_cd', 'item_second_cate_cd', 'shelves_dt', 'shelves_tm', 'date_s', 'dc_id']
logger.info('详单明细数据读取完成')
printruntime(test_t1, 'sale表数据读取')
printruntime(test_t2, '读取数据总耗时')


# ================================================================================
# =                                 （4）生成 dict 数据                           =
# ================================================================================
test_t2 = time.time()
test_t1 = time.time()
# （0）fdc_alt、fdc_alt_prob 的转换
# 由原始数据转化为 alt 数据
# 2.1 某个 RDC -> FDC 的某个 alt时长 的频数累计。
fdc_01=allocation_fdc_data.groupby(['org_from','org_to','alt']).sum()
fdc_01=fdc_01.reset_index()         # 【】把复合index放下
# 2.2 某个 RDC -> FDC 的  alt时长 的频数累计。
fdc_02=allocation_fdc_data['alt_cnt'].groupby([allocation_fdc_data['org_from'],allocation_fdc_data['org_to']]).sum()
# 上面等价于 fdc_03=allocation_fdc_data.groupby(['org_from','org_to']).sum()['alt_cnt']
fdc_02=fdc_02.reset_index()
fdc_alt=pd.merge(fdc_01,fdc_02,on=['org_from','org_to'])
fdc_alt.columns=['org_from','org_to','alt','alt_cnt','alt_all_cnt']
fdc_alt['alt_prob']=fdc_alt['alt_cnt']/fdc_alt['alt_all_cnt']
allocation_fdc_data=fdc_alt
allocation_fdc_data.columns=['org_from','dc_id','alt','alt_cnt','alt_all_cnt','alt_prob']
allocation_fdc_data['dc_id'] = map(lambda x:str(int(x)),allocation_fdc_data['dc_id'].values)
allocation_fdc_data=allocation_fdc_data[allocation_fdc_data['org_from']==316]   # 【不然取数据的时候直接取 316 好了？】
# RDC-->FDC时长分布,{fdc:[alt]}  {fdc:[alt_prob]}
fdc_alt=defaultdict(list)
fdc_alt_prob=defaultdict(list)
# {fdc:[alt]}  {fdc:[alt_prob]}
for index,row in allocation_fdc_data.iterrows():        # 遍历每一行，新方法
    if row['dc_id'] in fdc_alt:
        try:
            tmp=eval(row['alt'])
            fdc_alt[row['dc_id']].append(tmp)
        except:
            pass
    else:
        try:
            tmp=eval(row['alt'])
            fdc_alt[row['dc_id']]=[tmp]
        except:
            pass
    if row['dc_id'] in fdc_alt_prob:
        try:
            tmp=row['alt_prob']
            fdc_alt_prob[row['dc_id']].append(tmp)
        except:
            pass
    else:
        try:
            tmp=row['alt_prob']
            fdc_alt_prob[row['dc_id']]=[tmp]
        except:
            pass
printruntime(test_t1, 'fdc_alt、fdc_alt_prob的转换')

test_t1 = time.time()
# （1）预测数据：均值            【fdc_forecast_sales】
# 预测数据相关信息{fdc_sku_date:[7 days sales]},{fdc_sku_data:[7 days cv]}
# 该部分只考虑白名单的数据即可
# 【结构】：dict：{'id'(date_s+dc_id+sku_id):'forecast_value'(mean_sales)}
logger.info('开始读取sku预测数据并转化')
fdc_forecast_sales=pd.concat([allocation_sku_data['date_s'].astype('str')+allocation_sku_data['dc_id'].astype('str')
                              +allocation_sku_data['sku_id'].astype('str'),
                              allocation_sku_data['mean_sales']],axis=1)
fdc_forecast_sales.columns=['id','forecast_value']
fdc_forecast_sales=fdc_forecast_sales.set_index('id')['forecast_value'].to_dict()
printruntime(test_t1, 'fdc_forecast_sales的转换to_dict()')

test_t1 = time.time()
# （2）预测数据：标准差           【fdc_forecast_std】
# 【结构】：dict：{'id'(date_s+dc_id+sku_id):'forecast_std'(std)}
fdc_forecast_std=pd.concat([allocation_sku_data['date_s'].astype('str')+allocation_sku_data['dc_id'].astype('str')
                            +allocation_sku_data['sku_id'].astype('str'),
                            allocation_sku_data['std']],axis=1)
fdc_forecast_std.columns=['id','forecast_std']
fdc_forecast_std=fdc_forecast_std.set_index('id')['forecast_std'].to_dict()
logger.info('sku预测数据转化完成')
printruntime(test_t1, 'fdc_forecast_std的转换to_dict()')

test_t1 = time.time()
# （3）fdcinv 数据              【fdc_inv】
# 【结构】：dict：{'id'(date_s+dc_id+sku_id):{'k':'inv'(inv)}}
# defaultdict(lamda:defaultdict(int)),FDC只需要一个初始化库存即可,直接从FDC初始化库存中读取即可
fdc_inv=defaultdict(lambda :defaultdict(int))
allocation_fdc_initialization['inv']=allocation_fdc_initialization['inv']+allocation_fdc_initialization['open_po_fdc']
mid_fdc_inv=pd.concat([allocation_fdc_initialization['date_s'].astype(str)+allocation_fdc_initialization['dc_id'].astype(str)
                       +allocation_fdc_initialization['sku_id'].astype(str),
                       allocation_fdc_initialization['inv']],axis=1)
mid_fdc_inv.columns=['id','inv']
mid_fdc_inv=mid_fdc_inv.drop_duplicates()
mid_fdc_inv=mid_fdc_inv.set_index('id')['inv'].to_dict()
for k,v in mid_fdc_inv.items():         # 【】
    fdc_inv[k]['inv']=v
printruntime(test_t1, 'fdc_inv的转换to_dict()')

test_t1 = time.time()
# （4）白名单数据              【white_list_dict】
logger.info('开始生成白名单字典')
# 白名单,不同日期的白名单不同
# 【结构】：{fdc:{date_s:[]}}
white_list_dict=defaultdict(lambda :defaultdict(list))
tmp_df=allocation_sku_data[allocation_sku_data['white_flag']==1][['date_s','sku_id','dc_id']]
for k,v in tmp_df['sku_id'].groupby([tmp_df['date_s'],tmp_df['dc_id']]):        # 【】
    white_list_dict[k[1]][k[0]]=list(v)
logger.info('白名单生成完成')
printruntime(test_t1, 'white_list_dict的转换to_dict()')

test_t1 = time.time()
# （5）初始化RDC库存，第一天   【rdc_inv】
fdc_allocation=''
fdc=['628','630','658']
# RDC库存，{date_sku_rdc:库存量} defaultdict(int),只需要初始化的RDC库存
rdc_inv=defaultdict(int)
tmp_df=allocation_sku_data[allocation_sku_data['date_s']==start_date]
mid_rdc_inv=pd.concat([tmp_df['date_s'].astype(str)+'rdc'+tmp_df['sku_id'].astype(str),
                       tmp_df['inv']],axis=1)
mid_rdc_inv.columns=['id','inv']
mid_rdc_inv=mid_rdc_inv.drop_duplicates()
mid_rdc_inv=mid_rdc_inv.set_index('id')['inv'].to_dict()
rdc_inv.update(mid_rdc_inv)             # 【】
printruntime(test_t1, 'rdc_inv的转换to_dict()')

test_t1 = time.time()
# （6）order 数据处理         【order_list】
# 【结构】：{'date':{'sku':'arrive_quantity'}}
# 采购单数据，采购ID，SKU，实际到达量，到达时间,将其转换为{到达时间:{SKU：到达量}}形式的字典，defaultdict(lambda :defaultdict(int))
# 采购单ID在这里没有作用，更关心的是单个SKU在某一天的到达量
logger.info('开始处理采购单数据')
tmp_df=allocation_order_data[['arrive_time','item_sku_id','arrive_quantity']]
tmp_df.columns=['date','item_sku_id','arrive_quantity']
order_list=defaultdict(lambda :defaultdict(int))
logger.info('进行字典推导更新')
for index,row in tmp_df.iterrows():
    if order_list.has_key(row['date']):         # 【】
        if order_list[row['date']].has_key(row['item_sku_id']):
            order_list[row['date']][row['item_sku_id']]=order_list[row['date']][row['item_sku_id']]+row['arrive_quantity']
        else:
            order_list[row['date']][row['item_sku_id']]=row['arrive_quantity']
    else:
        order_list[row['date']]={row['item_sku_id']:row['arrive_quantity']}
# **** order_list['\\N'] 没有处理？
logger.info('order字典更新完成')
logger.info('遍历中间字典，更新采购单字典')
logger.info('采购单数据处理完成')
#订单数据：{fdc_订单时间_订单id:{SKU：数量}},当前的存储会造成的空间浪费应当剔除大小为0的SKU
logger.info('开始处理订单明细数据并转化')
# Run Time (order_list的转换to_dict()) is : 2.0 min 21.7833 s          【重点优化】
printruntime(test_t1, 'order_list的转换to_dict()')

test_t1 = time.time()
# （7）orders_retail FDC+某天 ： 销售时间+某订单id ： sku-id ： 销售量
# 【结构】：{'dc_date_id'(dc_id+date_s):{'id'(sale_ord_tm+sale_ord_id):{'item_sku_id':'sale_qtty'}}}
tmp_df=allocation_sale_data[['dc_id','date_s','item_sku_id','sale_ord_id','sale_ord_tm','sale_qtty']]
tmp_df=pd.DataFrame(tmp_df)
orders_retail_mid=pd.concat([tmp_df['dc_id'].astype(str)+tmp_df['date_s'].astype(str),tmp_df['sale_ord_tm'].astype(str)+
                             tmp_df['sale_ord_id'].astype(str),tmp_df[['item_sku_id','sale_qtty']]],
                            axis=1)
orders_retail_mid.columns=['dc_date_id','id','item_sku_id','sale_qtty']
orders_retail={}
for f in fdc:
   orders_retail[f]=defaultdict(lambda :defaultdict(int))
##能直接update 是因为订单编号是唯一的 所以这个key是唯一的 不会存在覆盖的现象
for index,row in orders_retail_mid.iterrows():
    if row['dc_date_id'] in orders_retail:
        orders_retail[row['dc_date_id']].update({row['id']:{row['item_sku_id']:row['sale_qtty']}})
    else:
        orders_retail[row['dc_date_id']]={row['id']:{row['item_sku_id']:row['sale_qtty']}}
#订单类型:{订单id:类型}
logger.info('订单明细数据处理完成')
orders_retail_type=defaultdict(str)
#sku当天从FDC的出库量，从RDC的出库量
sku_fdc_sales=defaultdict(int)
sku_rdc_sales=defaultdict(int)
#全量SKU列表
all_sku_list=list(set(allocation_sku_data['sku_id'].values))
printruntime(test_t1, 'orders_retail的转换to_dict()')
printruntime(test_t2, '转换总耗时')

# ================================================================================
# =                                 （5）开始仿真                                 =
# ================================================================================
logger.info('开始进行仿真运算')
###初始化仿真类，并运行相关结果
allocation=inventory_proess(fdc_forecast_sales,fdc_forecast_std,fdc_alt,fdc_alt_prob,fdc_inv,white_list_dict,fdc_allocation,
                            fdc,rdc_inv,order_list,date_range,orders_retail,all_sku_list,logger,save_data_path)
allocation.OrdersSimulation()
logger.info('仿真运算完成，开始进行数据保存与KPI计算')


# ================================================================================
# =                                 （6）保存数据                                 =
# ================================================================================
# 保存关键仿真数据
logger.info('开始保存仿真数据......')
pickle.dump(fdc_forecast_sales,open(save_data_path+'fdc_forecast_sales.pkl','w'))
pickle.dump(fdc_forecast_std,open(save_data_path+'fdc_forecast_std.pkl','w'))
pickle.dump(fdc_alt,open(save_data_path+'fdc_alt.pkl','w'))
pickle.dump(fdc_alt_prob,open(save_data_path+'fdc_alt_prob.pkl','w'))
pickle.dump(all_sku_list,open(save_data_path+'all_sku_list.pkl','w'))
pickle.dump(dict(allocation.fdc_inv),open(save_data_path+'fdc_inv.pkl','w'))
# pickle.dump(white_list_dict,open(save_data_path+'white_list_dict','w'))
pickle.dump(dict(allocation.fdc_allocation),open(save_data_path+'fdc_allocation.pkl','w'))
pickle.dump(dict(allocation.rdc_inv),open(save_data_path+'rdc_inv.pkl','w'))
# pickle.dump(dict(allocation.order_list),open(save_data_path+'order_list','w'))
# pickle.dump(dict(allocation.orders_retail),open(save_data_path+'orders_retail','w'))
# pickle.dump(dict(allocation.simu_orders_retail),open(save_data_path+'simu_orders_retail','w'))
# pickle.dump(dict(allocation.fdc_simu_orders_retail),open(save_data_path+'fdc_simu_orders_retail','w'))

####保存嵌套的字典#####
with open(save_data_path+'white_list_dict.txt','w') as white:
    for k,v in white_list_dict.items():
        for k1,v1 in v.items():
            white.write(str(k))
            white.write('\t')
            white.write(str(k1))
            white.write('\t')
            white.write(str(v1))
        white.write('\n')
pickle.dump(dict(allocation.fdc_allocation),open(save_data_path+'fdc_allocation.pkl','w'))
pickle.dump(dict(allocation.rdc_inv),open(save_data_path+'rdc_inv.pkl','w'))

with open(save_data_path+'order_list.txt','w') as ol:
    for k,v in allocation.order_list.items():
        for k1,v1 in v.items():
            ol.write(str(k))
            ol.write('\t')
            ol.write(str(k1))
            ol.write('\t')
            ol.write(str(v1))
        ol.write('\n')

with open(save_data_path+'orders_retail.txt','w') as orl:
    for k,v in allocation.orders_retail.items():
        for k1,v1 in v.items():
            for k2,v2 in v1.items():
                orl.write(str(k))
                orl.write('\t')
                orl.write(str(k1))
                orl.write('\t')
                orl.write(str(k2))
                orl.write('\t')
                orl.write(str(v2))
        orl.write('\n')

try:
    with open(save_data_path+'simu_orders_retail.txt','w') as orl:
        print allocation.simu_orders_retail.items()
        for k,v in allocation.simu_orders_retail.items():
            for k1,v1 in v.items():
                for k2,v2 in v1.items():
                    orl.write(str(k))
                    orl.write('\t')
                    orl.write(str(k1))
                    orl.write('\t')
                    orl.write(str(k2))
                    orl.write('\t')
                    orl.write(str(v2))
            orl.write('\n')
except:
    print 'simu order  in the except'
try:
    with open(save_data_path+'fdc_simu_orders_retail.txt','w') as orl:
        for k,v in allocation.fdc_simu_orders_retail.items():
            print allocation.fdc_simu_orders_retail.items()
            for k1,v1 in v.items():
                for k2,v2 in v1.items():
                    orl.write(str(k))
                    orl.write('\t')
                    orl.write(str(k1))
                    orl.write('\t')
                    orl.write(str(k2))
                    orl.write('\t')
                    orl.write(str(v2))
            orl.write('\n')
    logger.info('仿真数据保存完成...仿真程序完成...')
except:
    print 'in the except'


# ================================================================================
# =                                 （7）计算 KPI                                 =
# ================================================================================
#####计算KPI，KPI主要包括本地订单满足率，周转，SKU满足率
# 本地订单满足率 (本地出库订单+订单驱动内配)/订单数量
# print 'origin orders......',allocation.orders_retail
# print 'sim orders .......',allocation.simu_orders_retail
# print 'fdc orders ......',allocation.fdc_simu_orders_retail
# print '订单满足率:.........'
# print len(allocation.fdc_simu_orders_retail)/len(allocation.simu_orders_retail)
cnt_orders_retail_type={}
for k,v in allocation.orders_retail_type.items():
    cnt_orders_retail_type.setdefault(v,[]).append(k)
for k,v in cnt_orders_retail_type.items():
    print k,'has orders number:',len(v)
# 周转，考核单个SKU的周转,考察一个SKU7天的周转，7天平均库存/7天的平均销量  订单数据：{fdc_dt:{订单时间_订单id:{SKU：数量}}}
# 将订单数据转换为{fdc{date：{sku,销量}}},同时需要判断订单是否有FDC出货，需要在仿真的过程中标记，便于后续获取计算
# 直接标记不易标记，建立两个字典，一个记录仿真销量情况，一个记录仿真FDC销量情况
# fdc_date:{sku:数量}
sale_orders_retail_sku_cnt=defaultdict(lambda :defaultdict(lambda :defaultdict(int)))

for k,v in allocation.fdc_simu_orders_retail.items():
    k00=k[-10:]
    k01=k[:-10]
    for k1,v1 in v.items():
        for k2,v2 in v1.items():
            sale_orders_retail_sku_cnt[k01][k00][k2]+=v2


# print allocation.fdc_inv[index]['inv'],将其拆解为{fdc:{date:{sku:inv}}}
inv_orders_retail_sku_cnt=defaultdict(lambda :defaultdict(lambda :defaultdict(int)))
for k,v in allocation.fdc_inv.items():
    print k
    k1,k2,k3=k[:11],k[11:14],k[14:]     # 仅针对三位数的FDC，如果采用其他的则需要考虑把FDC编码映射成三位或增加分隔符
    inv_orders_retail_sku_cnt[k1][k2][k3]=v['inv']

# 遍历fdc,遍历日期，遍历sku,计算周转情况,ot_sku的数据格式：(fdc_sku_date:周转天数)
ot_sku=defaultdict(int)

for f in fdc:
    for i in len(date_range):
        sub_set=date_range[i:i+7]
        for sku in all_sku_list:
            v1=0
            v2=0
            for s in sub_set:
                v1+=sale_orders_retail_sku_cnt[f][s][sku]
                v2+=inv_orders_retail_sku_cnt[f][s][sku]
            index=gene_index(f,sku,date_range[i])
            ot_sku[index]=v2/v1
print ot_sku

