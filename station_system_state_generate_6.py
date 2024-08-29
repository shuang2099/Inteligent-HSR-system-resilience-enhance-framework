# 将每个车站（affected_station）的地震动参数输入到 'input_SeismicResponseOfSystems.xls' 文件，表格名（sheet name）为车站名称
# 运行该 .py 文件，输出每个车站各子系统的状态，如：
# station_system_state_origin = {'平湖': np.array(
#   [[0, 1, 0], [1, 0, 0], [0, 1, 0], [1, 0, 0], [1, 0, 0], [0, 0, 1], [0, 0, 1], [1, 0, 0], [1, 0, 0], [0, 1, 0],
#     [0, 0, 1], [1, 0, 0], [1, 0, 0]]),
#                               '深圳东': np.array(
#                                   [[0, 1, 0], [1, 0, 0], [0, 1, 0], [1, 0, 0], [1, 0, 0], [0, 0, 1], [0, 0, 1],
#                                    [1, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 0, 0], [1, 0, 0]])}  # 受损车站的功能状态矩阵
# 0 降压站； 1 应急备用电源； 2 给排水系统； 3 消防子系统； 4 暖通空调子系统； 
# 5站房照明子系统； 6 车站信息机房； 7 候车空间； 8 换乘通道； 9 车场给排水子系统； 
# 10 车场照明子系统；11 控制台； 12 货物转运通道


import pickle
import pandas as pd
import numpy as np
import heapq
import csv
from ast import literal_eval

def generate_t0(station_name, pipe_connector1, with_seismic_design, L, x, condition1, condition2, pipe_connector2, condition3):
    # 请选择站房管道-接头材料
    # pipe_connector1 = 0.铸铁-石棉水泥； 1.铸铁-自应力水泥； 2.铸铁-胶圈石棉灰； 3.铸铁-胶圈自应力灰； 4.钢筋混凝土-水泥砂浆； 5.预应力混凝土-橡胶圈

    # 消防设施是否按照抗震要求设计
    # with_seismic_design = 1代表是；0代表否

    # L = 消防管道总长度（英尺）
    # x = 每个消防用水单位（喷头、消火栓）的独立给水管的总数

    # 暖通空调风管的安装状况-安装位置
    # condition1 = 0.无抗摇杆-非屋顶层； 1.无抗摇杆-屋顶层； 2.有抗摇感-非屋顶层； 3.有抗摇感-屋顶层

    # 站房照明系统的安装状况
    # condition2 = 0.非抗震设计； 1.带固定夹； 2.抗震设计

    # 车场管道-接头材料
    # pipe_connector2 = 0.铸铁-石棉水泥； 1.铸铁-自应力水泥； 2.铸铁-胶圈石棉灰； 3.铸铁-胶圈自应力灰； 4.钢筋混凝土-水泥砂浆；
    # 5.预应力混凝土-橡胶圈

    # 车场照明系统的安装状况
    # condition3 = 0.非抗震设计； 1.带固定夹； 2.抗震设计

    station_seismic_response = pd.read_excel('F:/OneDrive - stu.hit.edu.cn/Documents/Papers/station&network/PyModel/input_SeismicResponseOfSystems.xlsx',
                                             sheet_name=station_name, index_col=0)
    t0 = np.array([[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0],
                   [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]])

    # 判断电力子系统功能状态
    if (station_seismic_response.loc['降压站', '均值'] <= 0.9) & (
            station_seismic_response.loc['配电室', '均值'] <= 1.3):
        t0[0] = [1, 0, 0]
    elif (station_seismic_response.loc['降压站', '均值'] <= 1.9) & (
            station_seismic_response.loc['配电室', '均值'] >= 0.9):
        t0[0] = [0, 1, 0]
    elif (station_seismic_response.loc['降压站', '均值'] <= 3.5) & (
            station_seismic_response.loc['配电室', '均值'] >= 1.3):
        t0[0] = [0, 1, 0]
    else:
        t0[0] = [0, 0, 1]

    # 判断应急备用电源子系统功能状态
    if station_seismic_response.loc['应急备用电源', '均值'] > 1.1:
        t0[1] = [0, 0, 1]
    else:
        t0[1] = [1, 0, 0]

    # 判断站房给排水系统功能状态
    ReferenceValue1 = np.array([[0.32, 2.65], [0.58, 2.88], [4.5, 25.68], [5.59, 24.98], [0.42, 3], [5, 38.6]])
    if all(i > ReferenceValue1[pipe_connector1][1] for i in
           station_seismic_response.loc['站房给排水系统', ['地震响应1', '地震响应2', '地震响应3', '地震响应4']]):
        t0[2] = [0, 0, 1]
    elif all(i < ReferenceValue1[pipe_connector1][0] for i in
             station_seismic_response.loc['站房给排水系统', ['地震响应1', '地震响应2', '地震响应3', '地震响应4']]):
        t0[2] = [1, 0, 0]
    else:
        t0[2] = [0, 1, 0]

    # 判断消防子系统功能状态
    ReferenceValue2 = np.array([[0.1, 0.01, 0], [0.2, 0.08, 0], [0.3, 0.10, 0], [0.4, 0.14, 0.005], [0.5, 0.16, 0.01],
                                [0.6, 0.20, 0.015], [0.7, 0.24, 0.02], [0.8, 0.30, 0.025], [0.9, 0.34, 0.03],
                                [1.2, 0.46, 0.04]])
    demaged_pipe = 0
    if station_seismic_response.loc['消防系统', '均值'] > 1.2:
        if with_seismic_design==1:
            demaged_pipe = ReferenceValue2[-1][2] * (L / 1000)
        else:
            demaged_pipe = ReferenceValue2[-1][1] * (L / 1000)
    else:
        for i in ReferenceValue2:
            if station_seismic_response.loc['消防系统', '均值'] <= i[0]:
                if with_seismic_design==1:
                    demaged_pipe = i[2] * (L / 1000)
                else:
                    demaged_pipe = i[1] * (L / 1000)
                break

    if demaged_pipe > 0.5 * x:
        t0[3] = [0, 0, 1]
    else:
        t0[3] = [1, 0, 0]

    # 判断暖通空调子系统功能状态
    ReferenceValue3 = [1.25, 0.5, 2.38, 0.96]
    if (station_seismic_response.loc['空调机组', '均值'] >= 2.9) or (
            station_seismic_response.loc['风管', '均值'] >= ReferenceValue3[condition1]):
        t0[4] = [0, 0, 1]
    elif (station_seismic_response.loc['冷却塔', '均值'] > 2.2) and (
            station_seismic_response.loc['风管', '均值'] < ReferenceValue3[condition1]):
        t0[4] = [0, 1, 0]
    else:
        t0[4] = [1, 0, 0]

    # 判断站房照明子系统功能状态
    ReferenceValue4 = [0.6, 1.1, 1.5]
    if station_seismic_response.loc['站房照明系统', '均值'] > ReferenceValue4[condition2]:
        t0[5] = [0, 0, 1]
    else:
        t0[5] = [1, 0, 0]

    # 判断车站信息机房功能状态
    if station_seismic_response.loc['车站信息机房', '均值'] > 0.6:
        t0[6] = [0, 0, 1]
    else:
        t0[6] = [1, 0, 0]

    # 判断候车空间功能状态
    if station_seismic_response.loc['候车空间', '均值'] == 0:
        t0[7] = [0, 0, 1]
    elif station_seismic_response.loc['候车空间', '均值'] == 0.5:
        t0[7] = [0, 1, 0]
    else:
        t0[7] = [1, 0, 0]

    # 判断换乘通道功能状态
    if station_seismic_response.loc['换乘通道', '均值'] < 0.005:
        t0[8] = [1, 0, 0]
    elif station_seismic_response.loc['换乘通道', '均值'] < 0.017:
        t0[8] = [0, 1, 0]
    else:
        t0[8] = [0, 0, 1]

    # 判断车场给排水子系统功能状态
    if all(i > ReferenceValue1[pipe_connector2][1] for i in
           station_seismic_response.loc['车场给排水系统', ['地震响应1', '地震响应2', '地震响应3', '地震响应4']]):
        t0[9] = [0, 0, 1]
    elif all(i < ReferenceValue1[pipe_connector2][1] for i in
             station_seismic_response.loc['车场给排水系统', ['地震响应1', '地震响应2', '地震响应3', '地震响应4']]):
        t0[9] = [1, 0, 0]
    else:
        t0[9] = [0, 1, 0]

    # 判断车场照明子系统功能状态
    if station_seismic_response.loc['车场照明系统', '均值'] > ReferenceValue4[condition3]:
        t0[10] = [0, 0, 1]
    else:
        t0[10] = [1, 0, 0]

    # 判断控制台功能状态
    if station_seismic_response.loc['控制台', '均值'] <= 1.4:
        t0[11] = [1, 0, 0]
    else:
        t0[11] = [0, 0, 1]

    # 判断货物转运通道功能状态
    if station_seismic_response.loc['货物转运通道', '均值'] == 0:
        t0[12] = [0, 0, 1]
    elif station_seismic_response.loc['货物转运通道', '均值'] == 0.5:
        t0[12] = [0, 1, 0]
    else:
        t0[12] = [1, 0, 0]

    return t0


affected_station = ['东莞','常平','樟木头','平湖','深圳东','深圳','东莞西','西平西',
                    '东城南','寮步','松山湖北','大朗镇','常平南','常平东','樟木头东',
                    '银瓶','沥林北','陈江南','惠环','龙丰','西湖东','云山','小金口',
                    '虎门','光明城','深圳北','福田','惠州南','深圳坪山','惠州北',
                    '东莞南','厚街','虎门北','虎门东','长安西','长安','沙井西',
                    '福海西','深圳机场北','惠州','东莞东']
install_condition = {s: (4, 1, 500, 5, 2, 2, 4, 2) for s in affected_station}

# %% 把黄钰文的PFA/层间位移角数据写入标准格式excel表格里
def write_to_exist_excel(fileName, sheetName, data_added):            
    writer = pd.ExcelWriter(fileName,mode='a', engine='openpyxl',if_sheet_exists='replace')
    data_added.to_excel(writer, sheet_name=sheetName, index=True)
    writer.close()

data = pd.read_csv(r'F:/OneDrive - stu.hit.edu.cn/Documents/Papers/station&network/PyModel/damage_state_station_6.csv',sep=',', quotechar='"', quoting=csv.QUOTE_ALL, encoding='utf-8', engine='python')
station_system_state_origin = {}
for s in affected_station:
    columns1=['地震响应1',	'地震响应2',	'地震响应3',	'地震响应4',	'均值']
    index1=['降压站','配电室','应急备用电源','站房给排水系统','消防系统','空调机组',
            '风管','冷却塔','站房照明系统','车站信息机房','候车空间','换乘通道',
            '车场给排水系统','车场照明系统','控制台','货物转运通道']
    station_state=pd.DataFrame(columns=columns1,index=index1)
    max_acc = literal_eval(data[data['station']==s]['每层最大加速度'].item())
    max_dspl = literal_eval(data[data['station']==s]['每层最大位移角'].item())
    structure_state = data[data['station']==s]['damage_state_HAZUS'].item()
    station_state.loc[['降压站','应急备用电源','站房给排水系统','消防系统',
                       '站房照明系统','车站信息机房','车场给排水系统','车场照明系统',
                       '控制台'],'地震响应1']=min(max_acc)
    l = len(max_acc)
    if l>=4:
        station_state.loc['配电室',['地震响应1',	'地震响应2',	'地震响应3',	'地震响应4']] = heapq.nsmallest(4, max_acc) 
    elif l==1:
        station_state.loc['配电室','地震响应1'] = max_acc 
    elif l==2:
        station_state.loc['配电室',['地震响应1',	'地震响应2']] = max_acc 
    elif l==3:
        station_state.loc['配电室',['地震响应1',	'地震响应2',	'地震响应3']] = max_acc 

    try:
        station_state.loc[['空调机组', '风管'],'地震响应1']=max_acc[-2]
    except:
        station_state.loc[['空调机组', '风管'],'地震响应1']=max_acc    

    station_state.loc['冷却塔','地震响应1']=max_acc[-1]
        
    if structure_state == 1:
        station_state.loc[['候车空间','货物转运通道'],'地震响应1'] = 1
    elif structure_state ==2:
        station_state.loc[['候车空间','货物转运通道'],'地震响应1'] = 0.5
    else:
        station_state.loc[['候车空间','货物转运通道'],'地震响应1'] = 0
        
    if l>=4:
        station_state.loc['换乘通道',['地震响应1',	'地震响应2',	'地震响应3']] = heapq.nsmallest(3, max_dspl) 
    elif l==1:
        station_state.loc['配电室','地震响应1'] = 0
    elif l==2:
        station_state.loc['配电室',['地震响应1']] = max_dspl 
    elif l==3:
        station_state.loc['换乘通道',['地震响应1', '地震响应2']] = max_dspl
        
    for i in station_state.index:
        station_state.loc[i,'均值']=np.mean(station_state.loc[i,['地震响应1',	'地震响应2',	'地震响应3',	'地震响应4']].dropna())
    write_to_exist_excel(fileName='F:/OneDrive - stu.hit.edu.cn/Documents/Papers/station&network/PyModel/Input_SeismicResponseOfSystems.xlsx',
                         sheetName=s,
                         data_added=station_state)

# %% 计算所有车站所有子系统初始状态，写入文件保持
for s in affected_station:    
    t = generate_t0(s, *install_condition[s])
    station_system_state_origin[s] = t

# 保存
with open('F:/OneDrive - stu.hit.edu.cn/Documents/Papers/station&network/PyModel/station_system_state_origin_6.pickle', 'wb') as f:
    pickle.dump(station_system_state_origin, f)
