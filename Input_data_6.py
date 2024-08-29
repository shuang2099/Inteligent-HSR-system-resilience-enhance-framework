import pandas as pd
import pickle

station_capacity_full = pd.read_excel('GBA_stations.xlsx', sheet_name='AD_track_full').drop_duplicates()
capacity_full = dict(zip(station_capacity_full['station'].tolist(), station_capacity_full['线'].tolist()))
station_capacity = pd.read_excel('GBA_stations.xlsx', sheet_name='AD_track_6').drop_duplicates()
capacity_origin = dict(zip(station_capacity['station'].tolist(), station_capacity['线'].tolist()))  # 车站-可用到发线{字典}

train_data_station_1 = pd.read_csv('Train1.CSV', encoding='gbk')
train_data_station_2 = pd.read_csv('Train2.CSV', encoding='gbk')
train_data_station = pd.concat([train_data_station_1, train_data_station_2],
                               axis=0, join='inner').drop_duplicates().reset_index(drop=True)

seg_time = pd.read_excel('GBA_stations.xlsx', sheet_name='min_runtime')
segment_running_time = {i: seg_time[i].tolist() for i in seg_time.columns}  # 区间最短运行时间

with open('origin_passenger_demand.pickle', 'rb') as f:
    origin_passenger_demand = pickle.load(f)

with open('origin_can_passenger.pickle', 'rb') as f:
    origin_can_passenger = pickle.load(f)

with open('origin_can_train.pickle', 'rb') as f:
    origin_can_train = pickle.load(f)

with open('train_passenger_number_at_station.pickle', 'rb') as f:
    v = pickle.load(f)

with open('station_system_state_origin_6.pickle', 'rb') as f:
    station_system_state_origin = pickle.load(f)

V = {t: 600 for t in train_data_station['train'].drop_duplicates().tolist()}  # 每辆列车的载客量

peak_flow_sheet = pd.read_excel('GBA_stations.xlsx', sheet_name='AD_track_full').drop_duplicates()
peak_flow = dict(zip(peak_flow_sheet['station'].tolist(), peak_flow_sheet['peak_flow'].tolist()))

station_passenger_flow = {s:[int(peak_flow[s] * (0.9 ** abs(13 - i))) 
                             for i in range(1, 25)] for s in peak_flow.keys()}

broken_line_origin = {'l1': ['广深线140~180km/h', '平湖', '深圳东'],
                      'l2': ['广深线140~180km/h', '平湖', '樟木头'],
                      'l3': ['京港高速线赣深段350km/h', '光明城', '仲恺'],
                      'l4': ['樟木头-东莞南跨线', '樟木头', '东莞南']}  # 受损线路

to_be_repair = []
for i in station_system_state_origin.keys():
    for j in range(len(station_system_state_origin[i])):
        if j in [1, 2, 6, 11]:
            if station_system_state_origin[i][j][2] == 1:
                to_be_repair.append(['station_system_state', i, j])
        else:
            if station_system_state_origin[i][j][0] != 1:
                to_be_repair.append(['station_system_state', i, j])

for i in broken_line_origin.keys():
    to_be_repair.append(['broken_line', i])

for i in capacity_origin.keys():
    if capacity_origin[i] != capacity_full[i]:
        for j in range(capacity_full[i] - capacity_origin[i]):
            to_be_repair.append(['capacity', i])

tracks_data_station = pd.read_excel('GBA_stations.xlsx', sheet_name='stations')

OD_station = ['清城', '花都', '白云机场北', '佛山西', '肇庆', '中堂', '深圳机场', '新塘南', '广州东', '广州',
              '深圳坪山', '肇庆东', '深圳东',
              '深圳北', '福田', '广州南', '珠海', '深圳', '东莞西', '小金口', '阳江', '江门', '珠海长隆', '东莞南',
              '怀集',
              '香港西九龙', '广州北']  # 有调车能力的终点站

stations_m = set(station_capacity['station'].tolist()) - set(OD_station)

in_city_station = {'广州': ['广州', '广州南', '广州东', '广州北'],
                   '东莞': ['东莞', '东莞南', '东莞东', '东莞西'],
                   '虎门': ['虎门', '虎门东'],
                   '惠州': ['惠州', '惠州北', '惠州南'],
                   '江门': ['江门', '江门东'],
                   '深圳': ['深圳', '深圳坪山', '深圳东', '深圳北', '深圳机场', '深圳机场北'],
                   '肇庆': ['肇庆', '肇庆东'],
                   '中山': ['中山', '中山北'],
                   '佛山': ['佛山', '佛山西']}

# 专列列车开行的站点两端有接发车能力的始发（终点）站范围内为影响范围内；键表示天数，值表示[[in-area所有包含的站点],[in-area外围的OD站点],[研究范围除去这些站都是范围外],[中断部分外围的OD站点]]
input_in_area_station = {
    0: [['新塘南', '东莞', '常平', '樟木头', '平湖', '深圳东'], ['新塘南', '深圳东', '东莞南'],['东莞', '常平', '平湖'],['新塘南', '深圳东', '东莞南','光明城','惠州北']],
    1: [['新塘南', '东莞', '常平', '樟木头', '平湖', '深圳东'], ['新塘南', '深圳东', '东莞南'],['东莞', '常平', '平湖'],['新塘南', '深圳东', '东莞南','光明城','惠州北']],
    2: [['新塘南', '东莞', '常平', '樟木头', '平湖', '深圳东'], ['新塘南', '深圳东', '东莞南'],['东莞', '常平', '平湖'],['新塘南', '深圳东', '东莞南','光明城','惠州北']],
    3: [['新塘南', '东莞', '常平', '樟木头', '平湖', '深圳东'], ['新塘南', '深圳东', '东莞南'],['东莞', '常平', '平湖'],['新塘南', '深圳东', '东莞南','光明城','惠州北']],
    4: [['新塘南', '东莞', '常平', '樟木头', '平湖', '深圳东'], ['新塘南', '深圳东', '东莞南'],['东莞', '常平', '平湖'],['新塘南', '深圳东', '东莞南']],
    5: [['新塘南', '东莞', '常平', '樟木头', '平湖', '深圳东'], ['新塘南', '深圳东', '东莞南'],['东莞', '常平', '平湖'],['新塘南', '深圳东', '东莞南']],
    6: [['新塘南', '东莞', '常平', '樟木头', '平湖', '深圳东'], ['新塘南', '深圳东', '东莞南'],['东莞', '常平', '平湖'],['新塘南', '深圳东', '东莞南']],
    7: [['新塘南', '东莞', '常平', '樟木头', '平湖', '深圳东'], ['新塘南', '深圳东', '东莞南'],['东莞', '常平', '平湖'],[]],
    8: [['新塘南', '东莞', '常平', '樟木头', '平湖', '深圳东'], ['新塘南', '深圳东', '东莞南'],['东莞', '常平', '平湖'],[]],
    9: [['新塘南', '东莞', '常平', '樟木头', '平湖', '深圳东'], ['新塘南', '深圳东', '东莞南'],['东莞', '常平', '平湖'],[]],
    10:[['新塘南', '东莞', '常平', '樟木头', '平湖', '深圳东'], ['新塘南', '深圳东', '东莞南'],['东莞', '常平', '平湖'],[]],
    11:[['新塘南', '东莞', '常平', '樟木头', '平湖', '深圳东'], ['新塘南', '深圳东', '东莞南'],['东莞', '常平', '平湖'],[]],
    12:[['新塘南', '东莞', '常平', '樟木头', '平湖', '深圳东'], ['新塘南', '深圳东', '东莞南'],['东莞', '常平', '平湖'],[]],
    13:[['新塘南', '东莞', '常平', '樟木头', '平湖', '深圳东'], ['新塘南', '深圳东', '东莞南'],['东莞', '常平', '平湖'],[]],
    14:[['新塘南', '东莞', '常平', '樟木头', '平湖', '深圳东'], ['新塘南', '深圳东', '东莞南'],['东莞', '常平', '平湖'],[]]}

# %% 定义的子系统修复计划；{天数：[当天修复好的子系统列表]}
repair_data = {0: [],
               1: [],
               2: [],
               3: [],
               4: [['broken_line', 'l3'],['broken_line', 'l4'],['capacity', '东莞南'],['station_system_state', '东莞', 9], ['station_system_state', '常平', 6], ['station_system_state', '樟木头', 11], ['station_system_state', '平湖', 11], ['station_system_state', '深圳东', 6], ['station_system_state', '深圳', 6], ['station_system_state', '东莞西', 9], ['station_system_state', '西平西', 9], ['station_system_state', '东城南', 9], ['station_system_state', '寮步', 9], ['station_system_state', '松山湖北', 6], ['station_system_state', '大朗镇', 6], ['station_system_state', '常平南', 6], ['station_system_state', '常平东', 6], ['station_system_state', '樟木头东', 6], ['station_system_state', '银瓶', 6], ['station_system_state', '沥林北', 6], ['station_system_state', '陈江南', 6], ['station_system_state', '惠环', 9], ['station_system_state', '龙丰', 9], ['station_system_state', '西湖东', 9], ['station_system_state', '云山', 9], ['station_system_state', '小金口', 9], ['station_system_state', '虎门', 9], ['station_system_state', '光明城', 6], ['station_system_state', '深圳北', 6], ['station_system_state', '福田', 6], ['station_system_state', '惠州南', 9], ['station_system_state', '深圳坪山', 6], ['station_system_state', '惠州北', 9], ['station_system_state', '东莞南', 11], ['station_system_state', '厚街', 9], ['station_system_state', '虎门北', 9], ['station_system_state', '虎门东', 9], ['station_system_state', '长安西', 9], ['station_system_state', '长安', 9], ['station_system_state', '沙井西', 9], ['station_system_state', '福海西', 9], ['station_system_state', '深圳机场北', 9], ['station_system_state', '惠州', 9], ['station_system_state', '东莞东', 6]], 
               5: [['station_system_state', '常平', 9], ['station_system_state', '樟木头', 6], ['station_system_state', '平湖', 10], ['station_system_state', '深圳东', 0], ['station_system_state', '深圳', 9], ['station_system_state', '松山湖北', 9], ['station_system_state', '大朗镇', 0], ['station_system_state', '常平南', 9], ['station_system_state', '常平东', 0], ['station_system_state', '樟木头东', 0], ['station_system_state', '银瓶', 0], ['station_system_state', '沥林北', 0], ['station_system_state', '陈江南', 9], ['station_system_state', '光明城', 0], ['station_system_state', '深圳北', 0], ['station_system_state', '福田', 9], ['station_system_state', '深圳坪山', 0], ['station_system_state', '东莞南', 6], ['station_system_state', '东莞东', 0]], 
               6: [['capacity', '东莞南'],['station_system_state', '樟木头', 0], ['station_system_state', '平湖', 8], ['station_system_state', '深圳东', 9], ['station_system_state', '大朗镇', 9], ['station_system_state', '常平东', 9], ['station_system_state', '樟木头东', 9], ['station_system_state', '银瓶', 9], ['station_system_state', '沥林北', 9], ['station_system_state', '光明城', 9], ['station_system_state', '深圳北', 9], ['station_system_state', '深圳坪山', 9], ['station_system_state', '东莞南', 5], ['station_system_state', '东莞东', 9]], 
               7: [['broken_line', 'l2'],['broken_line', 'l1'],['capacity', '平湖'],['station_system_state', '樟木头', 9], ['station_system_state', '平湖', 5], ['station_system_state', '樟木头东', 4], ['station_system_state', '光明城', 1], ['station_system_state', '东莞南', 10]], 
               8: [['capacity', '东莞南'],['station_system_state', '樟木头', 4], ['station_system_state', '平湖', 6], ['station_system_state', '樟木头东', 1], ['station_system_state', '东莞南', 0]], 
               9: [['station_system_state', '樟木头', 1], ['station_system_state', '平湖', 0], ['station_system_state', '东莞南', 4]], 
               10: [['capacity', '东莞南'],['station_system_state', '平湖', 4], ['station_system_state', '东莞南', 9]], 
               11: [['station_system_state', '平湖', 1], ['station_system_state', '东莞南', 1]], 
               12: [['station_system_state', '平湖', 9]]}

# %%
not_to_station = {0: ['平湖', '东莞南'], 1: ['平湖', '东莞南'], 2: ['平湖', '东莞南'], 3: ['平湖', '东莞南']}
for i in range(max(not_to_station.keys())+1, 20):
    not_to_station[i] = []

emergence_period = [0, 1, 2, 3]

