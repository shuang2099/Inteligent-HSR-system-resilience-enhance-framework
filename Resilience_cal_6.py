import copy
import gurobipy as gp
import math
import numpy as np
import time
import threading
from ast import literal_eval
import pandas as pd
from gurobipy import GRB
from gurobipy import abs_

from Input_data_6 import *
from parameter_set import *


## 修复过程，每日的‘station_system_state’ and ‘broken_line’ and ‘capacity’表示
def total_function(repair_data):        
    def daily_function_value(num_of_day):        
        def write_to_exist_excel(fileName, sheetName, data_added):            
            writer = pd.ExcelWriter(fileName,mode='a', engine='openpyxl',if_sheet_exists='replace')
            data_added.to_excel(writer, sheet_name=sheetName, index=False)
            writer.close()
            
        def scope_of_outage(line_station, broken_station):  ## 定义由线路中断、车站控制台损坏、车站到发线全部损坏确定中断范围的函数
            outage_stations = []
            for s in broken_station:
                for l in tracks_data_station.columns:
                    station_list = tracks_data_station[l].dropna().tolist()
                    if s in station_list:
                        outage_stations.append(s)
                        temp_station_list_1 = station_list[0:station_list.index(s)]
                        temp_station_list_2 = station_list[station_list.index(s)::]
                        temp_station_list_2.remove(s)
                        for s1 in temp_station_list_1[::-1]:
                            if not s1 in OD_station:
                                outage_stations.append(s1)
                            else:
                                outage_stations.append(s1)
                                break
                        for s2 in temp_station_list_2:
                            if not s2 in OD_station:
                                outage_stations.append(s2)
                            else:
                                outage_stations.append(s2)
                                break
            if not line_station == {}:
                for l in line_station.keys():
                    station_list = tracks_data_station[line_station[l][0]].dropna().tolist()
                    if line_station[l][1] in OD_station:
                        outage_stations.append(line_station[l][1])
                        if line_station[l][2] in OD_station:  # 损坏区间【A,B】两端车站A,B都是终点站
                            index_0 = station_list.index(line_station[l][1])
                            index_1 = station_list.index(line_station[l][2])
                            if index_0 < index_1:  # A站在线路车站列表中排在B前面
                                outage_stations.extend(
                                    station_list[
                                    station_list.index(line_station[l][1]) + 1:station_list.index(line_station[l][2])])
                                outage_stations.append(line_station[l][2])
                            else:  # B站在线路车站列表中排在A前面
                                outage_stations.extend(
                                    station_list[
                                    station_list.index(line_station[l][2]):station_list.index(line_station[l][1])])
                        else:  # 损坏区间【A,B】中A是终点站，B不是
                            index_0 = station_list.index(line_station[l][1])
                            index_1 = station_list.index(line_station[l][2])
                            if index_0 < index_1:  # A站在线路车站列表中排在B前面
                                temp_station_list = station_list[station_list.index(line_station[l][1]) + 1::]
                                for s in temp_station_list:
                                    if temp_station_list.index(s) <= temp_station_list.index(line_station[l][2]):
                                        outage_stations.append(s)
                                    else:
                                        if not s in OD_station:
                                            outage_stations.append(s)
                                        else:
                                            outage_stations.append(s)
                                            break
                            else:  # B站在线路车站列表中排在A前面
                                temp_station_list = station_list[0:station_list.index(line_station[l][1])]
                                for s in temp_station_list:
                                    if temp_station_list.index(s) >= temp_station_list.index(line_station[l][2]):
                                        outage_stations.append(s)
                                    else:
                                        if not s in OD_station:
                                            outage_stations.append(s)
                                        else:
                                            outage_stations.append(s)
                                            break
                    else:
                        if line_station[l][2] in OD_station:  # 损坏区间【A,B】中是B终点站，A不是
                            outage_stations.append(line_station[l][2])
                            index_0 = station_list.index(line_station[l][1])
                            index_1 = station_list.index(line_station[l][2])
                            if index_0 < index_1:  # A站在线路车站列表中排在B前面
                                temp_station_list = station_list[0:station_list.index(line_station[l][2])]
                                for s in temp_station_list[::-1]:
                                    if temp_station_list.index(s) >= temp_station_list.index(line_station[l][1]):
                                        outage_stations.append(s)
                                    else:
                                        if not s in OD_station:
                                            outage_stations.append(s)
                                        else:
                                            outage_stations.append(s)
                                            break
                            else:  # B站在线路车站列表中排在A前面
                                temp_station_list = station_list[station_list.index(line_station[l][2]) + 1::]
                                for s in temp_station_list:
                                    if temp_station_list.index(s) <= temp_station_list.index(line_station[l][1]):
                                        outage_stations.append(s)
                                    else:
                                        if not s in OD_station:
                                            outage_stations.append(s)
                                        else:
                                            outage_stations.append(s)
                                            break
                        else:  # 损坏区间【A,B】中A,B都不是终点站
                            index_0 = station_list.index(line_station[l][1])
                            index_1 = station_list.index(line_station[l][2])
                            if index_0 < index_1:  # A站在线路车站列表中排在B前面
                                outage_stations.extend(
                                    station_list[
                                    station_list.index(line_station[l][1]):station_list.index(line_station[l][2])])
                                temp_station_list_1 = station_list[0:station_list.index(line_station[l][1])]
                                temp_station_list_2 = station_list[station_list.index(line_station[l][2])::]
                                for s in temp_station_list_1[::-1]:
                                    if not s in OD_station:
                                        outage_stations.append(s)
                                    else:
                                        outage_stations.append(s)
                                        break
                                for s in temp_station_list_2:
                                    if not s in OD_station:
                                        outage_stations.append(s)
                                    else:
                                        outage_stations.append(s)
                                        break
                            else:  # B站在线路车站列表中排在A前面
                                outage_stations.extend(
                                    station_list[
                                    station_list.index(line_station[l][2]):station_list.index(line_station[l][1])])
                                temp_station_list_1 = station_list[0:station_list.index(line_station[l][2])]
                                temp_station_list_2 = station_list[station_list.index(line_station[l][1])::]
                                for s in temp_station_list_1[::-1]:
                                    if not s in OD_station:
                                        outage_stations.append(s)
                                    else:
                                        outage_stations.append(s)
                                        break
                                for s in temp_station_list_2:
                                    if not s in OD_station:
                                        outage_stations.append(s)
                                    else:
                                        outage_stations.append(s)
                                        break
            return list(set(outage_stations))

        def BRB_function(t):
            def cal_BETA(WK, betajk, beta):
                BETAj = (1 / (sum(np.prod(WK * betajk + 1 - WK * beta, axis=0)) - (N - 1) * np.prod(1 - WK * beta,
                                                                                                    axis=0))) * \
                        (np.prod(WK * betajk + (1 - WK * beta), axis=0) - np.prod(1 - WK * beta, axis=0)) \
                        / (1 - (
                        1 / (sum(np.prod(WK * betajk + 1 - WK * beta, axis=0)) - (N - 1) * np.prod(1 - WK * beta,
                                                                                                   axis=0))) *
                           (np.prod(1 - WK, axis=0)))
                return BETAj

            thita1 = np.ones((6, 1))
            betajk1 = np.array([[1, 0, 0], [0.2, 0.8, 0.0], [0, 0.8, 0.2], [0.8, 0.2, 0], [0, 0.8, 0.2], [0, 0, 1]])
            thita2 = np.ones((3, 1))
            betajk2 = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
            thita3 = np.ones((3, 1))
            betajk3 = np.array([[1, 0, 0], [1, 0, 0], [0, 0, 1]])
            thita4 = np.ones((3, 1))
            betajk4 = np.array([[1, 0, 0], [1, 0, 0], [0, 0, 1]])
            thita5 = np.ones((9, 1))
            betajk5 = np.array([[1, 0, 0], [0.2, 0.6, 0.2], [0, 0, 1], [0.2, 0.8, 0], [0, 0.6, 0.4],
                                [0, 0, 1], [0.4, 0.6, 0], [0, 0.2, 0.8], [0, 0, 1]])
            thita6 = np.ones((36, 1))
            betajk6 = np.array(
                [[1, 0, 0], [0.6, 0.2, 0.2], [0.8, 0.2, 0], [0.4, 0.4, 0.2], [0, 1, 0], [0, 0.8, 0.2], [0.2, 0.8, 0],
                 [0.4, 0.4, 0.2], [0.2, 0.8, 0], [0.2, 0.6, 0.2], [0, 1, 0], [0, 0.6, 0.4], [0, 0.6, 0.4],
                 [0, 0.4, 0.6],
                 [0, 0.4, 0.6], [0, 0.2, 0.8], [0, 0.4, 0.6], [0, 0.2, 0.8], [0, 0, 1], [0, 0, 1], [0, 0, 1],
                 [0, 0, 1],
                 [0, 0, 1], [0, 0, 1], [0, 0, 1], [0, 0, 1], [0, 0, 1], [0, 0, 1], [0, 0, 1], [0, 0, 1], [0, 0, 1],
                 [0, 0, 1],
                 [0, 0, 1], [0, 0, 1], [0, 0, 1], [0, 0, 1]])
            thita7 = np.ones((9, 1))
            betajk7 = np.array([[1, 0, 0], [0.2, 0.8, 0], [0, 0.2, 0.8], [0.2, 0.8, 0],
                                [0, 1, 0], [0, 0.2, 0.8], [0, 0, 1], [0, 0, 1], [0, 0, 1]])
            thita8 = np.ones((3, 1))
            betajk8 = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
            thita9 = np.ones((3, 1))
            betajk9 = np.array([[1, 0, 0], [1, 0, 0], [0, 0, 1]])
            thita10 = np.ones((18, 1))
            betajk10 = np.array([[1, 0, 0], [0.8, 0.2, 0], [0.6, 0.4, 0], [0.6, 0.4, 0], [0.5, 0.5, 0], [0.4, 0.6, 0],
                                 [0.4, 0.6, 0], [0.3, 0.5, 0.2], [0, 0.7, 0.3], [0, 0, 1], [0, 0, 1], [0, 0, 1],
                                 [0, 0, 1],
                                 [0, 0, 1], [0, 0, 1], [0, 0, 1], [0, 0, 1], [0, 0, 1]])
            thita11 = np.ones((9, 1))
            betajk11 = np.array([[1, 0, 0], [0.5, 0.5, 0], [0, 0, 1], [0.2, 0.8, 0],
                                 [0, 0.8, 0.2], [0, 0, 1], [0, 0, 1], [0, 0, 1], [0, 0, 1]])
            thita12 = np.ones((9, 1))
            betajk12 = np.array([[1, 0, 0], [0.5, 0.5, 0], [0, 0, 1], [0.2, 0.8, 0], [0, 0.8, 0.2],
                                 [0, 0, 1], [0, 0, 1], [0, 0, 1], [0, 0, 1]])
            thita13 = np.ones((9, 1))
            betajk13 = np.array([[1, 0, 0], [0.2, 0.8, 0], [0, 1, 0], [0.8, 0.2, 0], [0, 1, 0],
                                 [0, 0.8, 0.2], [0, 1, 0], [0, 0.8, 0.2], [0, 0, 1]])
            # 初始输入参考
            temp_t_01 = copy.deepcopy(t)
            temp_t_01[:, 0] = t[:, 0] + t[:, 1]
            t_01 = temp_t_01[:, [0, 2]]

            a1 = t[0, :]
            # 已知基层指标x1输入
            b1 = t_01[1, :]
            # 已知基层指标x2输入
            A1 = np.zeros((len(a1), len(b1)))
            for i in range(len(a1)):
                for j in range(len(b1)):
                    A1[i, j] = a1[i] * b1[j]

            WK1 = thita1 * np.reshape(A1, [len(a1) * len(b1), 1], order='F') / sum(
                thita1 * np.reshape(A1, [len(a1) * len(b1), 1],
                                    order='F'))
            N = 3
            # 评价等级结果的数量
            # %%
            beta1 = np.ones((np.size(betajk1, 0), 1))
            BETAj1 = cal_BETA(WK1, betajk1, beta1)
            # %%
            a2 = BETAj1
            A2 = a2
            WK2 = thita2 * np.reshape(A2, [len(a2), 1]) / sum(thita2 * np.reshape(A2, [len(a2), 1]))
            beta2 = np.ones((np.size(betajk2, 0), 1))
            BETAj2 = cal_BETA(WK2, betajk2, beta2)
            # %%
            a3 = a2
            A3 = a3
            WK3 = thita3 * np.reshape(A3, [len(a3), 1]) / sum(thita3 * np.reshape(A3, [len(a3), 1]))
            beta3 = np.ones((np.size(betajk3, 0), 1))
            temp_BETAj3 = cal_BETA(WK3, betajk3, beta3)
            temp_BETAj3[0] = temp_BETAj3[0] + temp_BETAj3[1]
            BETAj3 = temp_BETAj3[[0, 2]]
            # %%
            a4 = t[2, :]
            A4 = a4
            WK4 = thita4 * np.reshape(A4, [len(a4), 1]) / sum(thita4 * np.reshape(A4, [len(a4), 1]))
            beta4 = np.ones((np.size(betajk4, 0), 1))
            temp_BETAj4 = cal_BETA(WK4, betajk4, beta4)
            temp_BETAj4[0] = temp_BETAj4[0] + temp_BETAj4[1]
            BETAj4 = temp_BETAj4[[0, 2]]
            # %%
            a5 = a2
            b5 = a4
            A5 = np.zeros((len(a5), len(b5)))
            for i in range(len(a5)):
                for j in range(len(b5)):
                    A5[i, j] = a5[i] * b5[j]

            WK5 = thita5 * np.reshape(A5, [len(a5) * len(b5), 1], order='F') / sum(
                thita5 * np.reshape(A5, [len(a5) * len(b5), 1], order='F'))
            beta5 = np.ones((np.size(betajk5, 0), 1))
            BETAj5 = cal_BETA(WK5, betajk5, beta5)
            # %%
            a6_cal = BETAj4
            a6_inp = t_01[3, :]
            if sum([1, 0] * a6_cal) < sum([1, 0] * a6_inp):
                a6 = a6_cal
            else:
                a6 = a6_inp

            b6_cal = BETAj5
            b6_inp = t[4, :]
            if sum([1, 0.5, 0] * b6_cal) < sum([1, 0.5, 0] * b6_inp):
                b6 = b6_cal
            else:
                b6 = b6_inp

            c6_cal = BETAj2
            c6_inp = t[5, :]
            if sum([1, 0.5, 0] * c6_cal) < sum([1, 0.5, 0] * c6_inp):
                c6 = c6_cal
            else:
                c6 = c6_inp

            d6_cal = BETAj3
            d6_inp = t_01[6, :]
            if sum([1, 0] * d6_cal) < sum([1, 0] * d6_inp):
                d6 = d6_cal
            else:
                d6 = d6_inp
            A6 = np.zeros((len(a6), len(b6), len(c6), len(d6)))
            for i in range(len(a6)):
                for j in range(len(b6)):
                    for k in range(len(c6)):
                        for l in range(len(d6)):
                            A6[i, j, k, l] = a6[i] * b6[j] * c6[k] * d6[l]

            WK6 = thita6 * np.reshape(A6, [len(a6) * len(b6) * len(c6) * len(d6), 1], order='F') / \
                  sum(thita6 * np.reshape(A6, [len(a6) * len(b6) * len(c6) * len(d6), 1], order='F'))

            beta6 = np.ones((np.size(betajk6, 0), 1))
            BETAj6 = cal_BETA(WK6, betajk6, beta6)
            # %%
            a7_cal = BETAj6
            a7_inp = t[7, :]
            if sum([1, 0.5, 0] * a7_cal) < sum([1, 0.5, 0] * a7_inp):
                a7 = a7_cal
            else:
                a7 = a7_inp

            b7 = t[8, :]
            A7 = np.zeros((len(a7), len(b7)))
            for i in range(len(a7)):
                for j in range(len(b7)):
                    A7[i, j] = a7[i] * b7[j]

            WK7 = thita7 * np.reshape(A7, [len(a7) * len(b7), 1], order='F') / sum(
                thita7 * np.reshape(A7, [len(a7) * len(b7), 1], order='F'))
            beta7 = np.ones((np.size(betajk7, 0), 1))
            BETAj7 = cal_BETA(WK7, betajk7, beta7)
            # %%
            a8 = a2
            A8 = a8
            WK8 = thita8 * np.reshape(A8, [len(a8), 1]) / sum(thita8 * np.reshape(A8, [len(a8), 1]))
            beta8 = np.ones((np.size(betajk8, 0), 1))
            BETAj8 = cal_BETA(WK8, betajk8, beta8)
            # %%
            a9 = BETAj1
            A9 = a9
            WK9 = thita2 * np.reshape(A9, [len(a9), 1]) / sum(thita2 * np.reshape(A9, [len(a9), 1]))
            beta9 = np.ones((np.size(betajk2, 0), 1))
            BETAj9 = cal_BETA(WK9, betajk2, beta9)
            # %%
            a10 = a2
            A10 = a10
            WK10 = thita9 * np.reshape(A10, [len(a10), 1]) / sum(thita9 * np.reshape(A10, [len(a10), 1]))
            beta10 = np.ones((np.size(betajk9, 0), 1))
            temp_BETAj10 = cal_BETA(WK10, betajk9, beta10)
            temp_BETAj10[0] = temp_BETAj10[0] + temp_BETAj10[1]
            BETAj10 = temp_BETAj10[[0, 2]]
            # %%
            a11_cal = BETAj8
            a11_inp = t[9, :]
            if sum([1, 0.5, 0] * a11_cal) < sum([1, 0.5, 0] * a11_inp):
                a11 = a11_cal
            else:
                a11 = a11_inp

            b11_cal = BETAj9
            b11_inp = t[10, :]
            if sum([1, 0.5, 0] * b11_cal) < sum([1, 0.5, 0] * b11_inp):
                b11 = b11_cal
            else:
                b11 = b11_inp

            c11_cal = BETAj10
            c11_inp = t_01[11, :]
            if sum([1, 0] * c11_cal) < sum([1, 0] * c11_inp):
                c11 = c11_cal
            else:
                c11 = c11_inp

            A11 = np.zeros((len(a11), len(b11), len(c11)))
            for i in range(len(a11)):
                for j in range(len(b11)):
                    for k in range(len(c11)):
                        A11[i, j, k] = a11[i] * b11[j] * c11[k]

            WK11 = thita10 * np.reshape(A11, [len(a11) * len(b11) * len(c11), 1], order='F') / sum(
                thita10 * np.reshape(A11, [len(a11) * len(b11) * len(c11), 1], order='F'))

            beta11 = np.ones((np.size(betajk10, 0), 1))
            BETAj11 = cal_BETA(WK11, betajk10, beta11)
            # %%
            a12 = BETAj7
            b12 = BETAj11
            A12 = np.zeros((len(a12), len(b12)))
            for i in range(len(a12)):
                for j in range(len(b12)):
                    A12[i, j] = a12[i] * b12[j]
            WK12 = thita11 * np.reshape(A12, [len(a12) * len(b12), 1], order='F') / sum(
                thita11 * np.reshape(A12, [len(a12) * len(b12), 1], order='F'))

            beta12 = np.ones((np.size(betajk11, 0), 1))
            BETAj12 = cal_BETA(WK12, betajk11, beta12)
            # %%
            a13 = t[12, :]
            b13 = b12
            A13 = np.zeros((len(a13), len(b13)))
            for i in range(len(a13)):
                for j in range(len(b13)):
                    A13[i, j] = a13[i] * b13[j]

            WK13 = thita12 * np.reshape(A13, [len(a13) * len(b13), 1], order='F') / sum(
                thita12 * np.reshape(A13, [len(a13) * len(b13), 1], order='F'))

            beta13 = np.ones((np.size(betajk12, 0), 1))
            BETAj13 = cal_BETA(WK13, betajk12, beta13)
            # %%
            a14 = BETAj12
            b14 = BETAj13
            A14 = np.zeros((len(a14), len(b14)))
            for i in range(len(a14)):
                for j in range(len(b14)):
                    A14[i, j] = a14[i] * b14[j]

            WK14 = thita13 * np.reshape(A14, [len(a14) * len(b14), 1], order='F') / sum(
                thita13 * np.reshape(A14, [len(a14) * len(b14), 1], order='F'))

            beta14 = np.ones((np.size(betajk13, 0), 1))
            BETAj14 = cal_BETA(WK14, betajk13, beta14)
            # %%
            BETAj = [BETAj1, BETAj2, temp_BETAj3, temp_BETAj4, BETAj5, BETAj6,
                     BETAj7, BETAj8, BETAj9, temp_BETAj10, BETAj2, BETAj11, BETAj12, BETAj13, BETAj14]
            U = sum([1, 0.5, 0] * BETAj14)
            return BETAj, U

        def station_loc(line, station):
            location = tracks_data_station[tracks_data_station[line] == station].index[0]
            return location

        def dwell_time(train, line, station, events_timetable, trains_information):
            all_station = events_timetable[(events_timetable['traincode'] == train) &
                                              (events_timetable['line'] == line)]['station'].tolist()
            all_station_2 = sorted(set(all_station), key=all_station.index)
            ith = all_station_2.index(station)
            time = trains_information.loc[(trains_information['traincode'] == train) &
                                             (trains_information['line'] == line), 'dwell'].item()[ith]
            return time

        def to_time(time):
            this_time = int(time.split(':')[0]) * 60 + int(time.split(':')[1])
            return this_time

        def this_data(t):
            data = train_data_p[train_data_p['train'] == t]
            return data

        def in_city_s(t):
            in_city_station_list = list()
            for s in np.unique(this_data(t)['station']):
                for k in in_city_station.keys():
                    if s in in_city_station[k]:
                        for j in in_city_station[k]:
                            in_city_station_list.append(j)
            return set(in_city_station_list)

        def this_station(t):
            list_s = this_data(t)['station'].tolist()
            for s in this_data(t)['station'].tolist():
                for k in in_city_station.keys():
                    if s in in_city_station[k]:
                        index_s = list_s.index(s)
                        for in_city_s in in_city_station[k]:
                            if in_city_s != s:
                                list_s.insert(index_s + 1, in_city_s)
            return list_s

        def get_value(s):
            list_station = []
            for k in in_city_station.keys():
                if s in in_city_station[k]:
                    for in_city_s in in_city_station[k]:
                        list_station.append(in_city_s)
            if not list_station:
                list_station.append(s)
            return list_station

        # %% 通过控制台可用状态判断车站可用性
        control_table_broken_station = []
        for s in station_system_state[num_of_day].keys():
            # 判断控制台能不能用，“station_system_state[s][0][1]”应是表示控制台状态参考值为“正常运行”的位置
            if station_system_state[num_of_day][s][11][2] == 1:
                control_table_broken_station.append(s)

        # %% 有加开专列的情况
        try:  
            # 需要开行专列列车，划分影响区域
            ## 第t天计划开行的专列
            add_train_events_timetable = pd.read_excel('add_train_events_timetable_6.xlsx',
                                                       sheet_name='day' + str(num_of_day))
            special_train_station = np.unique(add_train_events_timetable['station'].tolist())  # 第t天开行专列的所有车站
            special_train_line = np.unique(add_train_events_timetable['line'].tolist())  # 第t天开行专列的所有线路

            # 通过中断线路确定不能开行列车的范围
            broken_station = []
            broken_station.extend(i for i in control_table_broken_station)
            broken_station.extend(i for i in capacity[num_of_day].keys()
                                  if capacity[num_of_day][i] == 0)

            outage_stations = scope_of_outage(broken_line[num_of_day], broken_station)

            # %%运行车站BRB
            station_loss_passenger = {}
            for station in station_system_state[num_of_day].keys():
                station_t = station_system_state[num_of_day][station]
                loss_passenger = 0
                if (BRB_function(station_t) != 1)&(BRB_function(station_t) != 0):
                    for i in range(14, 16):
                        if BRB_function(station_t)[1] * peak_flow[station] < station_passenger_flow[station][i]:
                            loss_passenger = loss_passenger + station_passenger_flow[station][i] - BRB_function(station_t)[
                                1] * peak_flow[station]
                station_loss_passenger[num_of_day, station] = int(loss_passenger)

            # %%运行data_in
            events_timetable = pd.read_csv('events_timetable.CSV', encoding='gbk')

            # 仅考虑地震影响范围内列车事件
            events_timetable_in = events_timetable[
                events_timetable['station'].isin(input_in_area_station[num_of_day][0])]
            events_timetable_in = pd.concat([events_timetable_in, events_timetable[events_timetable['station'].isin(outage_stations)]]).drop_duplicates()

            # 去掉在影响范围外运行，但始发、终到站在影响范围内的列车
            for t in np.unique(events_timetable_in['traincode']):
                temp = events_timetable_in[events_timetable_in['traincode'] == t]
                if len(temp['station'].drop_duplicates()) == 1:
                    events_timetable_in = events_timetable_in[events_timetable_in['traincode'] != t]

            events_timetable_in = events_timetable_in[
                events_timetable_in['line'].isin(special_train_line)]  # 单条线路不考虑跨线情况

            train_events = pd.read_csv('train_events.CSV', encoding='gbk')
            trains_information_in = pd.DataFrame(columns=['line', 'direction', 'dwell', 'traincode'])
            for t in list(np.unique(events_timetable_in['traincode'])):
                data_0 = events_timetable_in[events_timetable_in['traincode'] == t]
                if not data_0.empty:
                    start = 0
                    for line in data_0['line'].drop_duplicates().tolist():
                        data = data_0[start:start + len(data_0[data_0['line'] == line])]
                        dwell = [train_events[(train_events['train'] == t) &
                                              (train_events['station'] == s)]['dwell'].item()
                                 for s in data['station'].drop_duplicates().tolist()]
                        start = start + len(data[data['line'] == line])
                        if (tracks_data_station[line][
                            tracks_data_station[line] == data.iloc[0]['station']].index <
                                tracks_data_station[line][
                                    tracks_data_station[line] == data.iloc[-1]['station']].index):
                            direction = 1
                        else:
                            direction = 2

                        trains_information_in = pd.concat(
                            [trains_information_in, pd.DataFrame(pd.Series({'line': line, 'direction': direction,
                                                                            'dwell': dwell, 'traincode': t,
                                                                            'class': 1})).T],
                            ignore_index=True)

            #  加开列车事件
            add_train_trains_information = pd.read_excel('add_train_trains_information_6.xlsx', 'day' + str(num_of_day))
            add_train = list(np.unique(add_train_events_timetable['traincode']))
            for i in add_train_trains_information.index:
                add_train_trains_information.at[i, 'dwell'] = literal_eval(add_train_trains_information.loc[i, 'dwell'])

            # 加开列车事件并入列车-事件表格
            events_timetable_in = pd.concat([events_timetable_in, add_train_events_timetable], ignore_index=True)
            trains_information_in = pd.concat([trains_information_in, add_train_trains_information], ignore_index=True)

            # 研究范围内列车始-终事件处理
            for t in np.unique(events_timetable_in['traincode']):
                temp = events_timetable_in[events_timetable_in['traincode'] == t]
                if not temp.iloc[0]['state'] == 'first':
                    events_timetable_in.loc[(events_timetable_in['traincode'] == t) &
                                            (events_timetable_in['station'] == temp.iloc[0]['station']) &
                                            (events_timetable_in['arr'] == temp.iloc[0]['arr']), 'state'] = 'first'
                if not temp.iloc[-1]['state'] == 'last':
                    events_timetable_in.loc[(events_timetable_in['traincode'] == t) &
                                            (events_timetable_in['station'] == temp.iloc[-1]['station']) &
                                            (events_timetable_in['arr'] == temp.iloc[-1]['arr']), 'state'] = 'last'

            stations_m_in = []
            for i in special_train_line:
                stations_m_in.extend(tracks_data_station[i].dropna().tolist()[1:-1])

            trains_in = events_timetable_in['traincode'].drop_duplicates().tolist()
            all_events_timetable_in = copy.copy(events_timetable_in)

            # 影响范围内列车的原事件（有到发时间要求的事件）
            all_origin_events_index_in = []
            for j in all_events_timetable_in.index:
                train = all_events_timetable_in.loc[j]['traincode']
                temp = train_data_station[train_data_station['train'] == train]
                if all_events_timetable_in.loc[j]['station'] in temp['station'].tolist():
                    all_origin_events_index_in.append(j)

            # Cancel trains and relative events that pass stations of 0 capacity
            canceled_train_in = []
            unpassable_station = []
            temp = []
            for i in broken_line[num_of_day].keys():
                for s in broken_line[num_of_day][i][1::]:
                    temp.append(s)
            for i in temp:
                if temp.count(i)>1:
                    unpassable_station.append(i)
                    
            unpassable_station = list(set(unpassable_station + broken_station))
            
            for s in unpassable_station:
                for i in trains_in:
                    if s in events_timetable_in[events_timetable_in['traincode'] == i]['station'].tolist():
                        if i not in canceled_train_in:
                            canceled_train_in.append(i)

            trains_in = list(set(trains_in) - set(canceled_train_in))

            # 专列列车
            wounded_trains = trains_information_in[trains_information_in['class'] == 3][
                'traincode'].drop_duplicates().tolist()
            doctor_trains = trains_information_in[trains_information_in['class'] == 4][
                'traincode'].drop_duplicates().tolist()
            supplies_trains = trains_information_in[trains_information_in['class'] == 5][
                'traincode'].drop_duplicates().tolist()
            need_of_wou = len(wounded_trains) * num_of_wou_per_train
            need_of_doc = len(doctor_trains) * num_of_doc_per_train
            need_of_supp = len(supplies_trains) * kg_of_supp_per_train

            # %% 线路通行的情况下，运行TRP_in
            if trains_in:
                # 删除因车站到发线全部损坏造成中断不能开行的列车
                events_timetable_in = events_timetable_in[events_timetable_in['traincode'].isin(trains_in)]

                # 没取消列车的原事件（有到发时间要求的事件）
                origin_events_index_in = []
                for j in events_timetable_in.index:
                    train = events_timetable_in.loc[j]['traincode']
                    temp = train_data_station[train_data_station['train'] == train]
                    if events_timetable_in.loc[j]['station'] in temp['station'].tolist():
                        origin_events_index_in.append(j)

                origin_events_timetable_in = events_timetable_in.loc[origin_events_index_in]
                origin_trains_in = list(set(trains_in) - set(add_train))

                # 加开列车
                add_train_index = events_timetable_in[events_timetable_in['traincode'].isin(
                    add_train_events_timetable['traincode'].tolist())].index

                # 上、下行列车
                events_timetable_up_index_in = []
                for i in events_timetable_in.index:
                    if events_timetable_in.loc[i, 'traincode'] in \
                            trains_information_in[trains_information_in['direction'] ==
                                                  1]['traincode'].tolist():
                        line = events_timetable_in.loc[i, 'line']
                        if line in trains_information_in.loc[
                            (trains_information_in['direction'] == 1) &
                            (trains_information_in['traincode'] ==
                             events_timetable_in.loc[i, 'traincode']), 'line'].tolist():
                            events_timetable_up_index_in.append(i)

                events_timetable_down_index_in = list(set(events_timetable_in.index) -
                                                      set(events_timetable_up_index_in))
                up_events_timetable_in = events_timetable_in.loc[events_timetable_up_index_in]
                down_events_timetable_in = events_timetable_in.loc[events_timetable_down_index_in]
                
                model_in = gp.Model('TRP_in')
                # Part 1. Decision Variables
                y_in = model_in.addVars(trains_in, vtype=GRB.BINARY, name='Define canceled train')
                time_in = model_in.addVars(events_timetable_in.index, vtype=GRB.INTEGER, name='Time')
                delay_in = model_in.addVars(events_timetable_in.index, vtype=GRB.INTEGER)
                abs_d_in = model_in.addVars(events_timetable_in.index, vtype=GRB.INTEGER)
                d_in = model_in.addVars(events_timetable_in.index, events_timetable_in.index, vtype=GRB.BINARY)
                g_in = model_in.addVars(events_timetable_in.index, events_timetable_in.index, vtype=GRB.BINARY)
                model_in.update()
    
                #  给出引导解
                for i in trains_in:
                    y_in[i].VarHintVal = 0
    
                for i in events_timetable_in[~events_timetable_in['traincode'].isin(add_train)].index:
                    time_in[i].VarHintVal = events_timetable_in.loc[i, 'time']
    
                # Part 4 Add constrains
                # 0. 限制列车事件的时间范围(影响范围内列车可以取消)
                model_in.addConstrs(
                    time_in[e] <= M + M * y_in[events_timetable_in.loc[e, 'traincode']] for e in events_timetable_in.index)
    
                # For origin planned trains
                # 1. Train cannot depart at stations before scheduled
                model_in.addConstrs(
                    (time_in[e] - events_timetable_in.loc[e, 'time'] >= M * y_in[events_timetable_in.loc[e, 'traincode']]
                     for e in origin_events_timetable_in[origin_events_timetable_in['dep'] == 1].index)
                    , 'C1')
                # Constraints for a single train
                # 2. Maximum delay/early time of event e is smaller than D
                model_in.addConstrs(
                    delay_in[e] == time_in[e] - events_timetable_in.loc[e, 'time'] for e in events_timetable_in.index)
                model_in.addConstrs(abs_d_in[e] == abs_(delay_in[e]) for e in events_timetable_in.index)
                model_in.addConstrs(
                    (abs_d_in[e] <= D + M * y_in[events_timetable_in.loc[e, 'traincode']] for e in origin_events_index_in),
                    'C1')
    
                # 3. Train running time in segment should be no less than the minimum segment running time
                model_in.addConstrs(
                    (time_in[e2] - time_in[e1] >= segment_running_time[events_timetable_in.loc[e1, 'line']][station_loc(
                        events_timetable_in.loc[e1, 'line'], events_timetable_in.loc[e1, 'station'])]
                     for e1 in up_events_timetable_in[(up_events_timetable_in['dep'] == 1)
                                                      & (up_events_timetable_in['state'] != 'last')].index
                     for e2 in
                     up_events_timetable_in[
                         (up_events_timetable_in['traincode'] == up_events_timetable_in.loc[e1, 'traincode'])
                         & (up_events_timetable_in['station'] == up_events_timetable_in.loc[e1 + 1, 'station'])
                         & (up_events_timetable_in['line'] == up_events_timetable_in.loc[e1, 'line'])
                         & (up_events_timetable_in['arr'] == 1)].index)
                    , 'C2-1')
    
                model_in.addConstrs(
                    (time_in[e2] - time_in[e1] >= segment_running_time[events_timetable_in.loc[e2, 'line']][station_loc(
                        events_timetable_in.loc[e2, 'line'], events_timetable_in.loc[e2, 'station'])]
                     for e1 in down_events_timetable_in[(down_events_timetable_in['dep'] == 1)
                                                        & (down_events_timetable_in['state'] != 'last')].index
                     for e2 in down_events_timetable_in[
                         (down_events_timetable_in['traincode'] == down_events_timetable_in.loc[e1, 'traincode'])
                         & (down_events_timetable_in['station'] == down_events_timetable_in.loc[e1 + 1, 'station'])
                         & (down_events_timetable_in['line'] == down_events_timetable_in.loc[e1, 'line'])
                         & (down_events_timetable_in['arr'] == 1)].index)
                    , 'C2-2')
    
                # 4. Train dwelling time in each middle station should be respected
                model_in.addConstrs((time_in[e2] - time_in[e1] >= dwell_time(
                    events_timetable_in.loc[e1, 'traincode'], events_timetable_in.loc[e1, 'line'],
                    events_timetable_in.loc[e1, 'station'], events_timetable_in, trains_information_in)
                                     for e1 in events_timetable_in[events_timetable_in['arr'] == 1].index
                                     for e2 in
                                     events_timetable_in[
                                         (events_timetable_in['traincode'] == events_timetable_in.loc[e1, 'traincode'])
                                         & (events_timetable_in['station'] == events_timetable_in.loc[e1, 'station'])
                                         & (events_timetable_in['dep'] == 1)].index)
                                    , 'C4')
    
                # Station capacity constraint
                model_in.addConstrs((
                    gp.quicksum(d_in[e3, e1] for e3 in events_timetable_in[
                        (events_timetable_in['station'] == events_timetable_in.loc[e1, 'station'])
                        & (events_timetable_in['arr'] == 1)
                        & (events_timetable_in['traincode'] != events_timetable_in.loc[e1, 'traincode'])
                        ].index)
                    - gp.quicksum(g_in[e2, e1] for e2 in events_timetable_in[
                        (events_timetable_in['station'] == events_timetable_in.loc[e1, 'station'])
                        & (events_timetable_in['dep'] == 1)
                        & (events_timetable_in['traincode'] != events_timetable_in.loc[e1, 'traincode'])
                        ].index)
                    <= (capacity[num_of_day][events_timetable_in.loc[e1, 'station']] - 1)
                    for e1 in
                    events_timetable_in[
                        (events_timetable_in['station'].isin(stations_m_in)) & (events_timetable_in['arr'] == 1)].index)
                    , 'C5')
    
                # Arrival-departure interval constrain in station of two train
                # Definition of fai: 定义g[e1][e1],如果列车e1从车站出发发生在列车e2到达该车站之前,则g[e1, e1]=1
                model_in.addConstrs((time_in[e2] - time_in[e1] + M2 * (1 - g_in[e1, e2]) >= ad_time_interval
                                     for e1 in events_timetable_in[events_timetable_in['dep'] == 1].index
                                     for e2 in
                                     events_timetable_in[
                                         (events_timetable_in['station'] == events_timetable_in.loc[e1, 'station'])
                                         & (events_timetable_in['arr'] == 1)
                                         & (events_timetable_in['traincode'] != events_timetable_in.loc[
                                             e1, 'traincode'])
                                         # & (up_events_timetable['line'] == up_events_timetable.loc[e1, 'line'])
                                         ].index)
                                    , 'C6')
    
                # Headway constraints between train services
                # Same direction trains wouldn't overtake in segment
                # The arrival order in the next station just as the same as departure order in station
                model_in.addConstrs((d_in[e1, e2] == d_in[e3, e4]
                                     for e1 in events_timetable_in[(events_timetable_in['dep'] == 1)
                                                                   & (events_timetable_in['state'] != 'last')
                                                                   ].index
                                     for e2 in
                                     events_timetable_in[
                                         (events_timetable_in['station'] == events_timetable_in.loc[e1, 'station'])
                                         & (events_timetable_in['dep'] == 1)
                                         & (events_timetable_in['traincode'] != events_timetable_in.loc[
                                             e1, 'traincode'])
                                         & (events_timetable_in['line'] == events_timetable_in.loc[e1, 'line'])
                                         & (events_timetable_in['state'] != 'last')
                                         ].index
                                     for e3 in
                                     events_timetable_in[
                                         (events_timetable_in['station'] == events_timetable_in.loc[e1 + 1, 'station'])
                                         & (events_timetable_in['arr'] == 1)
                                         & (events_timetable_in['traincode'] == events_timetable_in.loc[e1, 'traincode'])
                                         ].index
                                     for e4 in
                                     events_timetable_in[
                                         (events_timetable_in['station'] == events_timetable_in.loc[e2 + 1, 'station'])
                                         & (events_timetable_in['station'] == events_timetable_in.loc[e3, 'station'])
                                         & (events_timetable_in['arr'] == 1)
                                         & (events_timetable_in['traincode'] == events_timetable_in.loc[e2, 'traincode'])
                                         & (events_timetable_in['line'] == events_timetable_in.loc[e3, 'line'])
                                         ].index)
                                    , 'C7')
    
                # The departure and arrival minimum time interval between two trains should be respected. 列车追踪距离（3min）约束
                model_in.addConstrs((time_in[e1] - time_in[e2] + M2 * (1 - d_in[e2, e1]) >= arrival_time_interval
                                     for e1 in up_events_timetable_in[(up_events_timetable_in['arr'] == 1)].index
                                     for e2 in
                                     up_events_timetable_in[
                                         (up_events_timetable_in['station'] == up_events_timetable_in.loc[e1, 'station'])
                                         & (up_events_timetable_in['arr'] == 1)
                                         & (up_events_timetable_in['traincode'] != up_events_timetable_in.loc[
                                             e1, 'traincode'])
                                         & (up_events_timetable_in['line'] == up_events_timetable_in.loc[e1, 'line'])
                                         ].index)
                                    , 'C8-1-1')
    
                model_in.addConstrs((time_in[e1] - time_in[e2] + M2 * (1 - d_in[e2, e1]) >= arrival_time_interval
                                     for e1 in down_events_timetable_in[(down_events_timetable_in['arr'] == 1)].index
                                     for e2 in
                                     down_events_timetable_in[
                                         (down_events_timetable_in['station'] == down_events_timetable_in.loc[
                                             e1, 'station'])
                                         & (down_events_timetable_in['arr'] == 1)
                                         & (down_events_timetable_in['traincode'] != down_events_timetable_in.loc[
                                             e1, 'traincode'])
                                         & (down_events_timetable_in['line'] == down_events_timetable_in.loc[e1, 'line'])
                                         ].index)
                                    , 'C8-1-2')
    
                model_in.addConstrs((time_in[e1] - time_in[e2] + M2 * (1 - d_in[e2, e1]) >= departure_time_interval
                                     for e1 in up_events_timetable_in[(up_events_timetable_in['dep'] == 1)].index
                                     for e2 in
                                     up_events_timetable_in[
                                         (up_events_timetable_in['station'] == up_events_timetable_in.loc[e1, 'station'])
                                         & (up_events_timetable_in['dep'] == 1)
                                         & (up_events_timetable_in['traincode'] != up_events_timetable_in.loc[
                                             e1, 'traincode'])
                                         & (up_events_timetable_in['line'] == up_events_timetable_in.loc[e1, 'line'])
                                         ].index)
                                    , 'C8-2-1')
    
                model_in.addConstrs((time_in[e1] - time_in[e2] + M2 * (1 - d_in[e2, e1]) >= departure_time_interval
                                     for e1 in down_events_timetable_in[(down_events_timetable_in['dep'] == 1)].index
                                     for e2 in
                                     down_events_timetable_in[
                                         (down_events_timetable_in['station'] == down_events_timetable_in.loc[
                                             e1, 'station'])
                                         & (down_events_timetable_in['dep'] == 1)
                                         & (down_events_timetable_in['traincode'] != down_events_timetable_in.loc[
                                             e1, 'traincode'])
                                         & (down_events_timetable_in['line'] == down_events_timetable_in.loc[e1, 'line'])
                                         ].index)
                                    , 'C8-2-2')
    
                model_in.addConstrs((d_in[e1, e2] + d_in[e2, e1] == 1
                                     for e1 in events_timetable_in.index
                                     for e2 in
                                     events_timetable_in[
                                         (events_timetable_in['station'] == events_timetable_in.loc[e1, 'station'])
                                         & (events_timetable_in['dep'] == events_timetable_in.loc[e1, 'dep'])
                                         & (events_timetable_in['traincode'] != events_timetable_in.loc[
                                             e1, 'traincode'])
                                         ].index)
                                    , 'C9')
    
                # Extra constrain
                model_in.addConstrs((d_in[e1, e3] >= g_in[e2, e3]
                                     for e1 in events_timetable_in[(events_timetable_in['arr'] == 1) &
                                                                   (events_timetable_in['state'] == 'middle')].index
                                     for e2 in
                                     events_timetable_in[
                                         (events_timetable_in['station'] == events_timetable_in.loc[e1, 'station'])
                                         & (events_timetable_in['dep'] == 1)
                                         & (events_timetable_in['traincode'] == events_timetable_in.loc[
                                             e1, 'traincode'])
                                         ].index
                                     for e3 in
                                     events_timetable_in[
                                         (events_timetable_in['station'] == events_timetable_in.loc[e1, 'station'])
                                         & (events_timetable_in['arr'] == 1)
                                         & (events_timetable_in['traincode'] != events_timetable_in.loc[
                                             e1, 'traincode'])
                                         ].index)
                                    , 'C10')
    
                # Part 0. Objective function
                passenger_demand = {t: origin_passenger_demand[t] for t in origin_trains_in}
    
                in_num_p_p_c = gp.quicksum(len(passenger_demand[t]) * y_in[t] for t in origin_trains_in)
    
                in_num_p_p_d = gp.quicksum((len(passenger_demand[events_timetable_in.loc[e, 'traincode']][
                                                    passenger_demand[events_timetable_in.loc[e, 'traincode']]['D'] ==
                                                    events_timetable_in.loc[e, 'station']]) * events_timetable_in.loc[
                                                e, 'arr']
                                            + len(passenger_demand[events_timetable_in.loc[e, 'traincode']][
                                                      passenger_demand[events_timetable_in.loc[e, 'traincode']]['O'] ==
                                                      events_timetable_in.loc[e, 'station']]) * events_timetable_in.loc[
                                                e, 'dep']) * (
                                                       abs_d_in[e] - M * y_in[events_timetable_in.loc[e, 'traincode']])
                                           for e in origin_events_index_in)
    
                in_num_wou_p_p_c = gp.quicksum(num_of_wou_per_train * y_in[t] for t in list(set(wounded_trains)&set(trains_in)))
    
                in_num_doc_p_p_c = gp.quicksum(num_of_doc_per_train * y_in[t] for t in list(set(doctor_trains)&set(trains_in)))
    
                in_num_supp_p_p_c = gp.quicksum(kg_of_supp_per_train * y_in[t] for t in list(set(supplies_trains)&set(trains_in)))
                
                in_num_wou_arranged = gp.quicksum(num_of_wou_per_train * (1-y_in[t]) for t in list(set(wounded_trains)&set(trains_in)))
    
                in_num_doc_arranged = gp.quicksum(num_of_doc_per_train * (1-y_in[t]) for t in list(set(doctor_trains)&set(trains_in)))
    
                in_num_supp_arranged = gp.quicksum(kg_of_supp_per_train * (1-y_in[t]) for t in list(set(supplies_trains)&set(trains_in)))
    
                ## 考虑未满足的伤员、医务人员、普通乘客出行需求、普通乘客准时性需求、应急物资运输需求
                in_objective = p_p_delay * in_num_p_p_d + p_p_cancel * in_num_p_p_c + \
                               p_doc * in_num_doc_p_p_c + p_wou * in_num_wou_p_p_c + p_supp * in_num_supp_p_p_c
    
                model_in.setObjective(in_objective, GRB.MINIMIZE)
                model_in.optimize()
    
                TRP_in_delay = p_p_delay * in_num_p_p_d.getValue()
                TRP_in_cancel = p_p_cancel * in_num_p_p_c.getValue()
                if list(set(add_train)-set(trains_in))==[]:
                    TRP_in_cancel_special = p_doc * in_num_doc_p_p_c.getValue() + \
                                            p_wou * in_num_wou_p_p_c.getValue() + \
                                            p_supp * in_num_supp_p_p_c.getValue()
                else:
                    TRP_in_cancel_special = p_doc*need_of_doc + p_wou*need_of_wou + p_supp*need_of_supp -\
                                            (p_doc * in_num_doc_arranged.getValue() + \
                                            p_wou * in_num_wou_arranged.getValue() + \
                                            p_supp * in_num_supp_arranged.getValue())
                                            
                timetable_in = pd.DataFrame(columns=['Train', 'Station', 'Time', 'Time Change', 'Operate or not'])
                for i in events_timetable_in.index:
                    timetable_in.loc[len(timetable_in.index)] = [events_timetable_in.loc[i, 'traincode'],
                                                                 events_timetable_in.loc[i, 'station'],
                                                                 time_in[i].x,
                                                                 time_in[i].x - events_timetable_in.loc[i, 'time'],
                                                                 y_in[events_timetable_in.loc[i, 'traincode']].x]
    
                timetable_in.to_csv('timetable_in_' + str(num_of_day) + '.csv', encoding='utf-8_sig')

                for t in origin_trains_in:
                    if y_in[t].x == 1:
                        canceled_train_in.append(t)
                        
                canceled_add_train = list(set(add_train) - set(trains_in))
                for t in list(set(add_train)&set(trains_in)):
                    if y_in[t].x == 1:
                        canceled_add_train.append(t)
                
                uncancel_train_in = list(set(trains_in) - set(canceled_train_in))
                canceled_add_train_trains_information = add_train_trains_information[add_train_trains_information['traincode'].isin(canceled_add_train)]
                canceled_add_train_events_timetable = add_train_events_timetable[add_train_events_timetable['traincode'].isin(canceled_add_train)]
                
            else:
                canceled_add_train_trains_information = copy.deepcopy(add_train_trains_information)
                canceled_add_train_events_timetable = copy.deepcopy(add_train_events_timetable)
                uncancel_train_in = copy.deepcopy(trains_in)
            # %% 当天未开行成果的专列累积到下一天
            next_day_add_train_trains_information = pd.concat([canceled_add_train_trains_information,pd.read_excel('add_train_trains_information_6.xlsx',
                                                       sheet_name='day' + str(num_of_day+1))], ignore_index=True)
            next_day_add_train_events_timetable = pd.concat([canceled_add_train_events_timetable,pd.read_excel('add_train_events_timetable_6.xlsx',
                                                       sheet_name='day' + str(num_of_day+1))], ignore_index=True)
            write_to_exist_excel(fileName='add_train_trains_information_6.xlsx',
                                 sheetName='day' + str(num_of_day+1),
                                 data_added=next_day_add_train_trains_information)
            write_to_exist_excel(fileName='add_train_events_timetable_6.xlsx',
                                 sheetName='day' + str(num_of_day+1),
                                 data_added=next_day_add_train_events_timetable)
            
            # %% 运行Data_out
            # 提取中断线路及车站部分内外列车事件
            if outage_stations:
                events_timetable_outage = events_timetable[events_timetable['station'].isin(set(outage_stations)-set(input_in_area_station[num_of_day][3]))] # 列车在中断的线路内的运行事件                                                
                canceled_train_outage = events_timetable[events_timetable['station'].isin(outage_stations)]['traincode'].drop_duplicates().tolist()
                canceled_train = list(set(canceled_train_in+canceled_train_outage))
                events_timetable_out_area = events_timetable[~events_timetable['station'].isin(input_in_area_station[num_of_day][2])]
                events_timetable_out = pd.concat([events_timetable_out_area, events_timetable_outage]).drop_duplicates(keep=False)
            else:
                events_timetable_out = pd.concat([events_timetable, 
                                                  events_timetable[events_timetable['station'].isin(input_in_area_station[num_of_day[2]])]]).drop_duplicates(keep=False)
            # 地震范围外原计划通过地震外围内的列车数据分段
            while_i = 1                
            while while_i <= 3:
                for t in events_timetable_out['traincode'].drop_duplicates().tolist():  # 跨越中断范围外列车事件分段
                    temp = events_timetable_out[events_timetable_out['traincode']==t]
                    if (len(temp['station'].drop_duplicates()) == 1) or (temp['station'].tolist()[0] not in OD_station) or (temp['station'].tolist()[-1] not in OD_station):
                        events_timetable_out = events_timetable_out[~(events_timetable_out['traincode'] == t)]
                    else:
                        if t[:(len(t[:])+1-while_i)] in canceled_train:
                            index_list = temp.index.tolist()
                            if not all([index_list[i+1]-index_list[i]==1 for i in range(len(index_list)-1)]):
                                part_a_index = []
                                part_b_index = []
                                for i in range(len(index_list)-1):
                                    if index_list[i+1]-index_list[i]==1:
                                        part_a_index.append(index_list[i])
                                    else:
                                        part_a_index.append(index_list[i])
                                        break
                                for j in index_list[i+1::]:
                                    part_b_index.append(j)
                                    
                                if part_a_index:
                                    events_timetable_out.loc[part_a_index,
                                    'traincode'] = events_timetable_out.loc[
                                                       part_a_index,
                                                       'traincode'] + 'A'
                                if part_b_index:
                                    events_timetable_out.loc[part_b_index,
                                    'traincode'] = events_timetable_out.loc[
                                                       part_b_index,
                                                       'traincode'] + 'B'
                while_i += 1

            # 列车开行方向、停站事件数据汇总
            trains_information_out = pd.DataFrame(columns=['line', 'direction', 'dwell', 'traincode', 'class'])
            for i in tracks_data_station.columns:
                for t in list(np.unique(events_timetable_out['traincode'])):
                    data = events_timetable_out[
                        (events_timetable_out['line'] == i) & (events_timetable_out['traincode'] == t)]
                    if t[-1].isalpha():
                        if not t[-2].isalpha():
                            dwell = [train_events[(train_events['train'] == t[:-1]) &
                                                  (train_events['station'] == s)]['dwell'].item()
                                     for s in data['station'].drop_duplicates().to_list()]
                        else:
                            dwell = [train_events[(train_events['train'] == t[:-2]) &
                                                  (train_events['station'] == s)]['dwell'].item()
                                     for s in data['station'].drop_duplicates().to_list()]
                    else:
                        dwell = [train_events[(train_events['train'] == t) &
                                              (train_events['station'] == s)]['dwell'].item()
                                 for s in data['station'].drop_duplicates().to_list()]

                    if not data.empty:
                        if (tracks_data_station[i][tracks_data_station[i] == data.iloc[0]['station']].index <
                                tracks_data_station[i][tracks_data_station[i] == data.iloc[-1]['station']].index):
                            direction = 1
                        else:
                            direction = 2

                        trains_information_out = pd.concat(
                            [trains_information_out, pd.DataFrame(pd.Series({'line': i, 'direction': direction,
                                                                             'dwell': dwell, 'traincode': t,
                                                                             'class': 1})).T],
                            ignore_index=True)

            # 研究范围外列车始-终事件处理
            for t in np.unique(events_timetable_out['traincode']):
                temp = events_timetable_out[events_timetable_out['traincode'] == t]
                if not temp.iloc[0]['state'] == 'first':
                    events_timetable_out.loc[(events_timetable_out['traincode'] == t) &
                                             (events_timetable_out['station'] == temp.iloc[0]['station']) &
                                             (events_timetable_out['arr'] == temp.iloc[0]['arr']), 'state'] = 'first'
                if not temp.iloc[-1]['state'] == 'last':
                    events_timetable_out.loc[(events_timetable_out['traincode'] == t) &
                                             (events_timetable_out['station'] == temp.iloc[-1]['station']) &
                                             (events_timetable_out['arr'] == temp.iloc[-1]['arr']), 'state'] = 'last'

            # 原事件（有到发时间要求的事件）
            events_timetable_out = events_timetable_out.reset_index(drop=True)
            origin_events_index_out = []
            for j in events_timetable_out.index:
                if events_timetable_out.loc[j, 'traincode'][-1].isalpha():
                    if not events_timetable_out.loc[j, 'traincode'][-2].isalpha():
                        train = events_timetable_out.loc[j]['traincode'][:-1]
                    else: 
                        train = events_timetable_out.loc[j]['traincode'][:-2]
                else:
                    train = events_timetable_out.loc[j]['traincode']
                temp = train_data_station[train_data_station['train'] == train]
                if events_timetable_out.loc[j]['station'] in temp['station'].tolist():
                    origin_events_index_out.append(j)

            origin_events_timetable_out = events_timetable_out.loc[origin_events_index_out]
            origin_trains_out = list(np.unique(origin_events_timetable_out['traincode']))

            # 上、下行列车
            events_timetable_up_index_out = []
            for i in events_timetable_out.index:
                if events_timetable_out.loc[i, 'traincode'] in \
                        trains_information_out[trains_information_out['direction'] ==
                                               1]['traincode'].tolist():
                    line = events_timetable_out.loc[i, 'line']
                    if line in trains_information_out.loc[
                        (trains_information_out['direction'] == 1) &
                        (trains_information_out['traincode'] ==
                         events_timetable_out.loc[i, 'traincode']), 'line'].tolist():
                        events_timetable_up_index_out.append(i)

            events_timetable_down_index_out = list(set(events_timetable_out.index) -
                                                   set(events_timetable_up_index_out))
            up_events_timetable_out = events_timetable_out.loc[events_timetable_up_index_out]
            down_events_timetable_out = events_timetable_out.loc[events_timetable_down_index_out]
            
            trains = events_timetable_out['traincode'].drop_duplicates()
            # 滚动时域法保持最开始的时刻表用  test_data_out = events_timetable_out.copy(deep=True)
            # %% 运行TRP_out
            model = gp.Model('TRP')
            # model.setParam('NodefileStart', 0.5)
            # model.setParam('Method', -1)

            y = model.addVars(trains, vtype=GRB.BINARY, name='Define canceled train')
            time = model.addVars(events_timetable_out.index, vtype=GRB.INTEGER, name='Time')
            delay = model.addVars(events_timetable_out.index, vtype=GRB.INTEGER)
            abs_d = model.addVars(events_timetable_out.index, vtype=GRB.INTEGER)
            d = model.addVars(events_timetable_out.index, events_timetable_out.index, vtype=GRB.BINARY)
            g = model.addVars(events_timetable_out.index, events_timetable_out.index, vtype=GRB.BINARY)
            model.update()

            #  给出引导解
            for i in trains:
                y[i].VarHintVal = 0

            for i in events_timetable_out.index:
                time[i].VarHintVal = events_timetable_out.loc[i, 'time']

            # Part 4 Add constrains
            # 0. 限制列车事件的时间范围
            model.addConstrs(
                time[e] <= M + M * y[events_timetable_out.loc[e, 'traincode']] for e in events_timetable_out.index)

            # For origin planned trains
            # 1. Train cannot depart at stations before scheduled
            model.addConstrs(
                (time[e] - events_timetable_out.loc[e, 'time'] >= M * y[events_timetable_out.loc[e, 'traincode']]
                 for e in origin_events_timetable_out[origin_events_timetable_out['dep'] == 1].index)
                , 'C1')
            # Constraints for a single train
            # 2. Maximum delay/early time of event e is smaller than D
            model.addConstrs(
                delay[e] == time[e] - events_timetable_out.loc[e, 'time'] for e in events_timetable_out.index)
            model.addConstrs(abs_d[e] == abs_(delay[e]) for e in events_timetable_out.index)
            model.addConstrs(
                (abs_d[e] <= D + M * y[events_timetable_out.loc[e, 'traincode']] for e in origin_events_index_out), 'C1')

            # 3. Train running time in segment should be no less than the minimum segment running time
            model.addConstrs(
                (time[e2] - time[e1] >= segment_running_time[events_timetable_out.loc[e1, 'line']][station_loc(
                    events_timetable_out.loc[e1, 'line'], events_timetable_out.loc[e1, 'station'])]
                 for e1 in up_events_timetable_out[(up_events_timetable_out['dep'] == 1)
                                                   & (up_events_timetable_out['state'] != 'last')].index
                 for e2 in
                 up_events_timetable_out[
                     (up_events_timetable_out['traincode'] == up_events_timetable_out.loc[e1, 'traincode'])
                     & (up_events_timetable_out['station'] == up_events_timetable_out.loc[e1 + 1, 'station'])
                     & (up_events_timetable_out['line'] == up_events_timetable_out.loc[e1, 'line'])
                     & (up_events_timetable_out['arr'] == 1)].index)
                , 'C2-1')

            model.addConstrs(
                (time[e2] - time[e1] >= segment_running_time[events_timetable_out.loc[e2, 'line']][station_loc(
                    events_timetable_out.loc[e2, 'line'], events_timetable_out.loc[e2, 'station'])]
                 for e1 in down_events_timetable_out[(down_events_timetable_out['dep'] == 1)
                                                     & (down_events_timetable_out['state'] != 'last')].index
                 for e2 in down_events_timetable_out[
                     (down_events_timetable_out['traincode'] == down_events_timetable_out.loc[e1, 'traincode'])
                     & (down_events_timetable_out['station'] == down_events_timetable_out.loc[e1 + 1, 'station'])
                     & (down_events_timetable_out['line'] == down_events_timetable_out.loc[e1, 'line'])
                     & (down_events_timetable_out['arr'] == 1)].index)
                , 'C2-2')

            # 4. Train dwelling time in each middle station should be respected
            model.addConstrs((time[e2] - time[e1] >= dwell_time(
                events_timetable_out.loc[e1, 'traincode'], events_timetable_out.loc[e1, 'line'],
                events_timetable_out.loc[e1, 'station'], events_timetable_out, trains_information_out)
                              for e1 in events_timetable_out[events_timetable_out['arr'] == 1].index
                              for e2 in events_timetable_out[
                                  (events_timetable_out['traincode'] == events_timetable_out.loc[e1, 'traincode'])
                                  & (events_timetable_out['station'] == events_timetable_out.loc[e1, 'station'])
                                  & (events_timetable_out['dep'] == 1)].index)
                             , 'C4')

            # Station capacity constraint
            model.addConstrs((
                gp.quicksum(d[e3, e1] for e3 in events_timetable_out[
                    (events_timetable_out['station'] == events_timetable_out.loc[e1, 'station'])
                    & (events_timetable_out['arr'] == 1)
                    & (events_timetable_out['traincode'] != events_timetable_out.loc[e1, 'traincode'])
                    ].index)
                - gp.quicksum(g[e2, e1] for e2 in events_timetable_out[
                    (events_timetable_out['station'] == events_timetable_out.loc[e1, 'station'])
                    & (events_timetable_out['dep'] == 1)
                    & (events_timetable_out['traincode'] != events_timetable_out.loc[e1, 'traincode'])
                    ].index)
                <= (capacity[num_of_day][events_timetable_out.loc[e1, 'station']] - 1)
                for e1 in events_timetable_out[
                (events_timetable_out['station'].isin(stations_m)) & (events_timetable_out['arr'] == 1)].index)
                , 'C5')

            # Arrival-departure interval constrain in station of two train
            # Definition of fai: 定义g[e1][e1],如果列车e1从车站出发发生在列车e2到达该车站之前,则g[e1, e1]=1
            model.addConstrs((time[e2] - time[e1] + M2 * (1 - g[e1, e2]) >= ad_time_interval
                              for e1 in events_timetable_out[events_timetable_out['dep'] == 1].index
                              for e2 in events_timetable_out[
                                  (events_timetable_out['station'] == events_timetable_out.loc[e1, 'station'])
                                  & (events_timetable_out['arr'] == 1)
                                  & (events_timetable_out['traincode'] != events_timetable_out.loc[e1, 'traincode'])
                                  # & (up_events_timetable_out['line'] == up_events_timetable_out.loc[e1, 'line'])
                                  ].index)
                             , 'C6')

            # Headway constraints between train services
            # Same direction trains wouldn't overtake in segment
            # The arrival order in the next station just as the same as departure order in station
            model.addConstrs((d[e1, e2] == d[e3, e4]
                              for e1 in events_timetable_out[(events_timetable_out['dep'] == 1)
                                                             & (events_timetable_out['state'] != 'last')
                                                             ].index
                              for e2 in events_timetable_out[
                                  (events_timetable_out['station'] == events_timetable_out.loc[e1, 'station'])
                                  & (events_timetable_out['dep'] == 1)
                                  & (events_timetable_out['traincode'] != events_timetable_out.loc[e1, 'traincode'])
                                  & (events_timetable_out['line'] == events_timetable_out.loc[e1, 'line'])
                                  & (events_timetable_out['state'] != 'last')
                                  ].index
                              for e3 in events_timetable_out[
                                  (events_timetable_out['station'] == events_timetable_out.loc[e1 + 1, 'station'])
                                  & (events_timetable_out['arr'] == 1)
                                  & (events_timetable_out['traincode'] == events_timetable_out.loc[e1, 'traincode'])
                                  ].index
                              for e4 in events_timetable_out[
                                  (events_timetable_out['station'] == events_timetable_out.loc[e2 + 1, 'station'])
                                  & (events_timetable_out['station'] == events_timetable_out.loc[e3, 'station'])
                                  & (events_timetable_out['arr'] == 1)
                                  & (events_timetable_out['traincode'] == events_timetable_out.loc[e2, 'traincode'])
                                  & (events_timetable_out['line'] == events_timetable_out.loc[e3, 'line'])
                                  ].index)
                             , 'C7')

            # The departure and arrival minimum time interval between two trains should be respected. 列车追踪距离（3min）约束
            model.addConstrs((time[e1] - time[e2] + M2 * (1 - d[e2, e1]) >= arrival_time_interval
                              for e1 in up_events_timetable_out[(up_events_timetable_out['arr'] == 1)].index
                              for e2 in
                              up_events_timetable_out[
                                  (up_events_timetable_out['station'] == up_events_timetable_out.loc[e1, 'station'])
                                  & (up_events_timetable_out['arr'] == 1)
                                  & (up_events_timetable_out['traincode'] != up_events_timetable_out.loc[
                                      e1, 'traincode'])
                                  & (up_events_timetable_out['line'] == up_events_timetable_out.loc[e1, 'line'])
                                  ].index)
                             , 'C8-1-1')

            model.addConstrs((time[e1] - time[e2] + M2 * (1 - d[e2, e1]) >= arrival_time_interval
                              for e1 in down_events_timetable_out[(down_events_timetable_out['arr'] == 1)].index
                              for e2 in
                              down_events_timetable_out[
                                  (down_events_timetable_out['station'] == down_events_timetable_out.loc[e1, 'station'])
                                  & (down_events_timetable_out['arr'] == 1)
                                  & (down_events_timetable_out['traincode'] != down_events_timetable_out.loc[
                                      e1, 'traincode'])
                                  & (down_events_timetable_out['line'] == down_events_timetable_out.loc[e1, 'line'])
                                  ].index)
                             , 'C8-1-2')

            model.addConstrs((time[e1] - time[e2] + M2 * (1 - d[e2, e1]) >= departure_time_interval
                              for e1 in up_events_timetable_out[(up_events_timetable_out['dep'] == 1)].index
                              for e2 in
                              up_events_timetable_out[
                                  (up_events_timetable_out['station'] == up_events_timetable_out.loc[e1, 'station'])
                                  & (up_events_timetable_out['dep'] == 1)
                                  & (up_events_timetable_out['traincode'] != up_events_timetable_out.loc[
                                      e1, 'traincode'])
                                  & (up_events_timetable_out['line'] == up_events_timetable_out.loc[e1, 'line'])
                                  ].index)
                             , 'C8-2-1')

            model.addConstrs((time[e1] - time[e2] + M2 * (1 - d[e2, e1]) >= departure_time_interval
                              for e1 in down_events_timetable_out[(down_events_timetable_out['dep'] == 1)].index
                              for e2 in
                              down_events_timetable_out[
                                  (down_events_timetable_out['station'] == down_events_timetable_out.loc[e1, 'station'])
                                  & (down_events_timetable_out['dep'] == 1)
                                  & (down_events_timetable_out['traincode'] != down_events_timetable_out.loc[
                                      e1, 'traincode'])
                                  & (down_events_timetable_out['line'] == down_events_timetable_out.loc[e1, 'line'])
                                  ].index)
                             , 'C8-2-2')

            model.addConstrs((d[e1, e2] + d[e2, e1] == 1
                              for e1 in events_timetable_out.index
                              for e2 in events_timetable_out[
                                  (events_timetable_out['station'] == events_timetable_out.loc[e1, 'station'])
                                  & (events_timetable_out['dep'] == events_timetable_out.loc[e1, 'dep'])
                                  & (events_timetable_out['traincode'] != events_timetable_out.loc[e1, 'traincode'])
                                  ].index)
                             , 'C9')

            # Extra constrain
            model.addConstrs((d[e1, e3] >= g[e2, e3]
                              for e1 in events_timetable_out[(events_timetable_out['arr'] == 1) &
                                                             (events_timetable_out['state'] == 'middle')].index
                              for e2 in events_timetable_out[
                                  (events_timetable_out['station'] == events_timetable_out.loc[e1, 'station'])
                                  & (events_timetable_out['dep'] == 1)
                                  & (events_timetable_out['traincode'] == events_timetable_out.loc[e1, 'traincode'])
                                  ].index
                              for e3 in events_timetable_out[
                                  (events_timetable_out['station'] == events_timetable_out.loc[e1, 'station'])
                                  & (events_timetable_out['arr'] == 1)
                                  & (events_timetable_out['traincode'] != events_timetable_out.loc[e1, 'traincode'])
                                  ].index)
                             , 'C10')

            # Part 0. Objective function
            code = {}
            for t in trains:
                if t[-1].isalpha():
                    if t[-2].isalpha():
                        code[t] = t[:-2]
                    else:
                        code[t]=t[:-1]
                else:
                    code[t]=t
                    
            passenger_demand = {t: origin_passenger_demand[code[t]] for t in trains}

            num_p_p_c = gp.quicksum(max(len(passenger_demand[t]),1) * y[t] for t in trains)

            num_p_p_d = gp.quicksum(max((len(passenger_demand[events_timetable_out.loc[e, 'traincode']][
                                                passenger_demand[events_timetable_out.loc[e, 'traincode']]['D'] ==
                                                events_timetable_out.loc[e, 'station']])
                                        + len(passenger_demand[events_timetable_out.loc[e, 'traincode']][
                                                  passenger_demand[events_timetable_out.loc[e, 'traincode']]['O'] ==
                                                  events_timetable_out.loc[e, 'station']])),1) * abs_d[e]
                                       for e in origin_events_index_out)

            objective = p_p_delay * num_p_p_d + p_p_cancel * num_p_p_c

            model.setObjective(objective, GRB.MINIMIZE)
            model.optimize()

            time_changed_train = []
            for e in origin_events_index_out:
                if time[e].x != events_timetable_out.loc[e, 'time']:
                    t = events_timetable_out.loc[e, 'traincode']
                    if not t in time_changed_train:
                        time_changed_train.append(t)

            for i in trains:
                if y[i].x == 1:
                    canceled_train.append(i)

            
            timetable_out = pd.DataFrame(columns=['Train', 'Station', 'Time', 'Time Change', 'Operate or not'])
            for i in events_timetable_out.index:
                timetable_out.loc[len(timetable_out.index)] = [events_timetable_out.loc[i, 'traincode'],
                                                             events_timetable_out.loc[i, 'station'],
                                                             time[i].x,
                                                             time[i].x - events_timetable_out.loc[i, 'time'],
                                                             y[events_timetable_out.loc[i, 'traincode']].x]

            timetable_out.to_csv('timetable_out_' + str(num_of_day) + '.csv', encoding='utf-8_sig')

            TRP_delay = p_p_delay * num_p_p_d.getValue()
            TRP_cancel = p_p_cancel * num_p_p_c.getValue()
            # %% 运行passenger_routing
            # 取消列车的乘客需求
            canceled_passenger_demand = pd.DataFrame(columns=('O', 'D', 'O_time', 'D_time'))

            all_canceled_train = list(set(canceled_train) - set(add_train))

            for t in all_canceled_train:
                canceled_passenger_demand = pd.concat([canceled_passenger_demand, origin_passenger_demand[t]],
                                                      ignore_index=True)

            canceled_passenger_demand = canceled_passenger_demand[~
                ((canceled_passenger_demand['O'].isin(not_to_station[num_of_day]))
                &
                (canceled_passenger_demand['D'].isin(not_to_station[
                    num_of_day])))]
            canceled_passenger_demand = canceled_passenger_demand[(canceled_passenger_demand['O_time'] >= 0)
                                                                  & (canceled_passenger_demand['D_time'] <= 120)]
            canceled_passenger_demand.reset_index(drop=True, inplace=True)

            # 数据格式处理
            train_data_p = pd.DataFrame(columns=['station', 'arr', 'dep', 'train'])
            uncancel_train = list(set(trains).union(set(uncancel_train_in)) -set(all_canceled_train))
            for t in uncancel_train:
                for s in np.unique(origin_events_timetable_out[origin_events_timetable_out['traincode'] == t]['station']):
                    if len(origin_events_timetable_out[(origin_events_timetable_out['traincode'] == t) &
                                                       (origin_events_timetable_out['station'] == s)]) == 2:
                        arr_time = origin_events_timetable_out.loc[
                            (origin_events_timetable_out['traincode'] == t) &
                            (origin_events_timetable_out['station'] == s) &
                            (origin_events_timetable_out['arr'] == 1), 'time'].item()
                        dep_time = origin_events_timetable_out.loc[
                            (origin_events_timetable_out['traincode'] == t) &
                            (origin_events_timetable_out['station'] == s) &
                            (origin_events_timetable_out['dep'] == 1), 'time'].item()
                    else:
                        if origin_events_timetable_out.loc[
                            (origin_events_timetable_out['traincode'] == t) &
                            (origin_events_timetable_out['station'] == s), 'arr'].item() == 1:
                            arr_time = origin_events_timetable_out.loc[
                                (origin_events_timetable_out['traincode'] == t) &
                                (origin_events_timetable_out['station'] == s) &
                                (origin_events_timetable_out['arr'] == 1), 'time'].item()
                            dep_time = arr_time
                        else:
                            dep_time = origin_events_timetable_out.loc[
                                (origin_events_timetable_out['traincode'] == t) &
                                (origin_events_timetable_out['station'] == s) &
                                (origin_events_timetable_out['dep'] == 1), 'time'].item()
                            arr_time = dep_time
                    train_data_p = pd.concat([train_data_p, pd.DataFrame(pd.Series({'station': s, 'arr': arr_time,
                                                                                    'dep': dep_time, 'train': t})).T],
                                             ignore_index=True)
            train_data_p = train_data_p.sort_values(by=['train', 'arr'], inplace=False, ascending=True)

            train = np.unique(train_data_p['train'])  # 影响范围外的列车 T_out

            # 乘客可以被安排到的列车集合{乘客：[列车集合]}
            can_train = {}
            for p in canceled_passenger_demand.index:
                can_t = []
                i = canceled_passenger_demand.loc[p, 'O']
                j = canceled_passenger_demand.loc[p, 'D']
                for o in origin_can_train.keys():
                    for d in origin_can_train[o].keys():
                        if (i == o) & (j == d):
                            for t in origin_can_train[o][d]:
                                if t in train:
                                    can_t.append(t)
                can_train[p] = can_t
                            
            # 列车可以接受的乘客集合{列车：[乘客集合]}
            can_passenger = {t: [can_train[0] for can_train in can_train.items() if t in can_train[1]] for t in train}

            model_passenger = gp.Model('PR')
            #  Decision variables:
            yp = model_passenger.addVars(canceled_passenger_demand.index, vtype=GRB.BINARY, name='yp')
            z_p = model_passenger.addVars(canceled_passenger_demand.index, train, vtype=GRB.BINARY, name='z')

            # Constrains
            ## 乘客分配约束
            model_passenger.addConstrs(
                (gp.quicksum(z_p[p, t] for t in can_train[p]) + yp[p] == 1 for p in canceled_passenger_demand.index),
                name='cp1')
            model_passenger.addConstrs(
                (gp.quicksum(z_p[p, t] for t in train) <= 1 for p in canceled_passenger_demand.index),
                name='cp2')

            ##  列车容量约束
            ### 列车在每一个站的容量约束
            model_passenger.addConstrs(
                (gp.quicksum(
                    z_p[p, t] for p in can_passenger[t] if canceled_passenger_demand.loc[p]['O'] in get_value(s))
                 +
                 gp.quicksum(z_p[p1, t] for p1 in can_passenger[t] if
                             this_station(t).index(canceled_passenger_demand.loc[p1][0]) <=
                             this_station(t).index(s))
                 -
                 gp.quicksum(z_p[p2, t] for p2 in can_passenger[t] if
                             this_station(t).index(canceled_passenger_demand.loc[p2][0]) <=
                             this_station(t).index(s))
                 <= V[code[t]] - v[(code[t], s)]
                 for t in train
                 for s in this_data(t)['station'])
                , name='train_capacity_cons')

            #  Objective function
            d_O = gp.quicksum(z_p[p, t] * abs(int([this_data(t).loc[i, 'dep'] for i in this_data(t).index
                                                   if canceled_passenger_demand.loc[p]['O'] in get_value(
                    this_data(t).loc[i, 'station'])][0])
                                              - int(canceled_passenger_demand.loc[p]['O_time']))
                              for p in canceled_passenger_demand.index for t in can_train[p])

            d_D = gp.quicksum(z_p[p, t] * abs(int([this_data(t).loc[i, 'arr'] for i in this_data(t).index
                                                   if canceled_passenger_demand.loc[p]['D'] in get_value(
                    this_data(t).loc[i, 'station'])][0])
                                              - int(canceled_passenger_demand.loc[p]['D_time']))
                              for p in canceled_passenger_demand.index for t in can_train[p])

            p_cancel = gp.quicksum(yp[p] for p in canceled_passenger_demand.index)
            passenger_rerouting_delay = d_O * p_p_delay + d_D * p_p_delay
            passenger_rerouting_cancel = p_cancel * p_p_cancel
            model_passenger.setObjective(passenger_rerouting_delay + passenger_rerouting_cancel, GRB.MINIMIZE)

            # 更新模型
            model_passenger.optimize()

            canceled_passenger_demand['to_train'] = 0
            for i in canceled_passenger_demand.index:  # 输出乘客重安排结果
                for t in train:
                    if z_p[i, t].x == 1:
                        canceled_passenger_demand.loc[i, 'to_train'] = t

            passenger_demand_2 = canceled_passenger_demand[canceled_passenger_demand['to_train'] == 0]  # 没有安排的乘客

            # 输出
            passenger_need_rerouting = len(canceled_passenger_demand)
            success_rerouted = len(canceled_passenger_demand) - len(passenger_demand_2)
            passenger_rerouting_delay = passenger_rerouting_delay.getValue()
            passenger_rerouting_cancel = passenger_rerouting_cancel.getValue()

            # %% 功能及韧性指标计算
            ## 有加开列车的情况
            ## 恢复阶段判断
            if num_of_day in emergence_period:
                station_loss={}
                for i in station_loss_passenger.keys():
                    unconsider_station = list(set(list(set(outage_stations)-set(input_in_area_station[num_of_day][3]))+not_to_station[num_of_day]))
                    if not i[1] in unconsider_station:
                        station_loss[i]=station_loss_passenger[i]

                try:
                    function_of_the_day = math.exp(
                        -(TRP_in_delay + TRP_delay + passenger_rerouting_delay 
                          + passenger_rerouting_cancel + TRP_in_cancel_special
                          + sum(station_loss.values()) * p_p_cancel) / 10000) 
                except:
                    function_of_the_day = math.exp(
                        -(passenger_rerouting_delay+ TRP_delay + passenger_rerouting_cancel 
                          + p_doc*need_of_doc + p_wou*need_of_wou
                          + p_supp*need_of_supp + sum(station_loss.values()) * p_p_cancel) / 10000) 
            else:  ## 考虑出行需求、准时性需求和车站集散能力造成无法满足的旅客需求
                station_loss={}
                for i in station_loss_passenger.keys():
                    unconsider_station = list(set(outage_stations)-set(input_in_area_station[num_of_day][3]))
                    if not i[1] in unconsider_station:
                        station_loss[i]=station_loss_passenger[i]
                        
                try:
                    function_of_the_day = math.exp(
                    -(TRP_in_delay + TRP_delay + passenger_rerouting_delay +
                      passenger_rerouting_cancel + TRP_in_cancel_special + 
                      sum(station_loss.values()) * p_p_cancel) / 10000)
                except:
                    function_of_the_day = math.exp(
                    -(passenger_rerouting_delay + TRP_delay +
                      passenger_rerouting_cancel + p_doc*need_of_doc 
                      + p_wou*need_of_wou + p_supp*need_of_supp
                      + sum(station_loss.values()) * p_p_cancel) / 10000)
            function[num_of_day] = function_of_the_day
            # return function_of_the_day
        
        # %%    
        except:  # 没有加开列车
            # 通过中断线路确定不能开行列车的范围
            broken_station = []
            broken_station.extend(i for i in control_table_broken_station)
            broken_station.extend(i for i in capacity[num_of_day].keys()
                                  if capacity[num_of_day][i] == 0 if i not in broken_station)

            outage_stations = scope_of_outage(broken_line[num_of_day], broken_station)

            # %%运行车站BRB
            station_loss_passenger = {} # {(天数，站名)：人数}
            for station in station_system_state[num_of_day].keys():
                station_t = station_system_state[num_of_day][station]
                loss_passenger = 0
                if (BRB_function(station_t) != 1)&(BRB_function(station_t) != 0):
                    for i in range(14, 16):
                        if BRB_function(station_t)[1] * peak_flow[station] < station_passenger_flow[station][i]:
                            loss_passenger = loss_passenger + station_passenger_flow[station][i] - BRB_function(station_t)[
                                1] * peak_flow[station]
                station_loss_passenger[num_of_day, station] = int(loss_passenger)

            events_timetable = pd.read_csv('events_timetable.CSV', encoding='gbk')
            train_events = pd.read_csv('train_events.CSV', encoding='gbk')

            # %%  如果有中断的车站
            if outage_stations: 
                # 提取中断线路及车站部分内外列车事件
                events_timetable_in = events_timetable[events_timetable['station'].isin(outage_stations)]
                events_timetable_in_outage = events_timetable[events_timetable['station'].isin(set(outage_stations)-set(input_in_area_station[num_of_day][3]))] # 列车在中断的线路内的运行事件                                                
                canceled_train_in = events_timetable_in['traincode'].drop_duplicates().tolist()
                
                events_timetable_out = pd.concat([events_timetable, events_timetable_in_outage]).drop_duplicates(keep=False)

                while_i = 1                
                while while_i <= 3:
                    for t in events_timetable_out['traincode'].drop_duplicates().tolist():  # 跨越中断范围外列车事件分段
                        temp = events_timetable_out[events_timetable_out['traincode']==t]
                        if len(temp['station'].drop_duplicates()) == 1:
                            events_timetable_out = events_timetable_out[~(events_timetable_out['traincode'] == t)]
                        else:
                            if t[:(len(t[:])+1-while_i)] in canceled_train_in:
                                index_list = temp.index.tolist()
                                if not all([index_list[i+1]-index_list[i]==1 for i in range(len(index_list)-1)]):
                                    part_a_index = []
                                    part_b_index = []
                                    for i in range(len(index_list)-1):
                                        if index_list[i+1]-index_list[i]==1:
                                            part_a_index.append(index_list[i])
                                        else:
                                            part_a_index.append(index_list[i])
                                            break
                                    for j in index_list[i+1::]:
                                        part_b_index.append(j)
                                        
                                    if part_a_index:
                                        events_timetable_out.loc[part_a_index,
                                        'traincode'] = events_timetable_out.loc[
                                                           part_a_index,
                                                           'traincode'] + 'A'
                                    if part_b_index:
                                        events_timetable_out.loc[part_b_index,
                                        'traincode'] = events_timetable_out.loc[
                                                           part_b_index,
                                                           'traincode'] + 'B'
                    while_i += 1
                    
            else:
                events_timetable_out = copy.deepcopy(events_timetable)
                canceled_train_in = []

            # %%  列车开行方向、停站事件数据汇总
            trains_information_out = pd.DataFrame(columns=['line', 'direction', 'dwell', 'traincode', 'class'])
            for i in tracks_data_station.columns:
                for t in list(np.unique(events_timetable_out['traincode'])):
                    data = events_timetable_out[
                        (events_timetable_out['line'] == i) & (events_timetable_out['traincode'] == t)]
                    if t[-1].isalpha():
                        if not t[-2].isalpha():
                            dwell = [train_events[(train_events['train'] == t[:-1]) &
                                                  (train_events['station'] == s)]['dwell'].item()
                                     for s in data['station'].drop_duplicates().to_list()]
                        else:
                            dwell = [train_events[(train_events['train'] == t[:-2]) &
                                                  (train_events['station'] == s)]['dwell'].item()
                                     for s in data['station'].drop_duplicates().to_list()]
                    else:
                        dwell = [train_events[(train_events['train'] == t) &
                                              (train_events['station'] == s)]['dwell'].item()
                                 for s in data['station'].drop_duplicates().to_list()]

                    if not data.empty:
                        if (tracks_data_station[i][tracks_data_station[i] == data.iloc[0]['station']].index <
                                tracks_data_station[i][tracks_data_station[i] == data.iloc[-1]['station']].index):
                            direction = 1
                        else:
                            direction = 2

                        trains_information_out = pd.concat(
                            [trains_information_out, pd.DataFrame(pd.Series({'line': i, 'direction': direction,
                                                                             'dwell': dwell, 'traincode': t,
                                                                             'class': 1})).T],
                            ignore_index=True)

            # %%  研究范围外列车始-终事件处理
            trains = np.unique(events_timetable_out['traincode'])
            for t in trains:
                temp = events_timetable_out[events_timetable_out['traincode'] == t]
                if not temp.iloc[0]['state'] == 'first':
                    events_timetable_out.loc[(events_timetable_out['traincode'] == t) &
                                             (events_timetable_out['station'] == temp.iloc[0]['station']) &
                                             (events_timetable_out['arr'] == temp.iloc[0]['arr']), 'state'] = 'first'
                if not temp.iloc[-1]['state'] == 'last':
                    events_timetable_out.loc[(events_timetable_out['traincode'] == t) &
                                             (events_timetable_out['station'] == temp.iloc[-1]['station']) &
                                             (events_timetable_out['arr'] == temp.iloc[-1]['arr']), 'state'] = 'last'
            # 原事件（有到发时间要求的事件）
            origin_events_index_out = []
            for j in events_timetable_out.index:
                if events_timetable_out.loc[j, 'traincode'][-1].isalpha():
                    if not events_timetable_out.loc[j, 'traincode'][-2].isalpha():
                        train = events_timetable_out.loc[j]['traincode'][:-1]
                    else: 
                        train = events_timetable_out.loc[j]['traincode'][:-2]
                else:
                    train = events_timetable_out.loc[j]['traincode']
                temp = train_data_station[train_data_station['train'] == train]
                if events_timetable_out.loc[j]['station'] in temp['station'].tolist():
                    origin_events_index_out.append(j)

            origin_events_timetable_out = events_timetable_out.loc[origin_events_index_out]
            origin_trains_out = list(np.unique(origin_events_timetable_out['traincode']))

            # 上、下行列车
            events_timetable_up_index_out = []
            for i in events_timetable_out.index:
                if events_timetable_out.loc[i, 'traincode'] in \
                        trains_information_out[trains_information_out['direction'] ==
                                              1]['traincode'].tolist():
                    line = events_timetable_out.loc[i, 'line']
                    if line in trains_information_out.loc[
                        (trains_information_out['direction'] == 1) &
                        (trains_information_out['traincode'] ==
                         events_timetable_out.loc[i, 'traincode']), 'line'].tolist():
                        events_timetable_up_index_out.append(i)

            events_timetable_down_index_out = list(set(events_timetable_out.index) -
                                                  set(events_timetable_up_index_out))
            up_events_timetable_out = events_timetable_out.loc[events_timetable_up_index_out]
            down_events_timetable_out = events_timetable_out.loc[events_timetable_down_index_out]

            # 运行基础设施条件下列车重排
            model = gp.Model('TRP')
            # model.setParam('NodefileStart', 0.5)
            # model.setParam('Method', -1)

            y = model.addVars(trains, vtype=GRB.BINARY, name='Define canceled train')
            time = model.addVars(events_timetable_out.index, vtype=GRB.INTEGER, name='Time')
            delay = model.addVars(events_timetable_out.index, vtype=GRB.INTEGER)
            abs_d = model.addVars(events_timetable_out.index, vtype=GRB.INTEGER)
            d = model.addVars(events_timetable_out.index, events_timetable_out.index, vtype=GRB.BINARY)
            g = model.addVars(events_timetable_out.index, events_timetable_out.index, vtype=GRB.BINARY)
            model.update()

            #  给出引导解
            for i in trains:
                y[i].VarHintVal = 0

            for i in events_timetable_out.index:
                time[i].VarHintVal = events_timetable_out.loc[i, 'time']

            # Part 4 Add constrains
            # 0. 限制列车事件的时间范围
            model.addConstrs(
                time[e] <= M + M * y[events_timetable_out.loc[e, 'traincode']] for e in events_timetable_out.index)

            # For origin planned trains
            # 1. Train cannot depart at stations before scheduled
            model.addConstrs(
                (time[e] - events_timetable_out.loc[e, 'time'] >= M * y[events_timetable_out.loc[e, 'traincode']]
                 for e in origin_events_timetable_out[origin_events_timetable_out['dep'] == 1].index)
                , 'C1')
            # Constraints for a single train
            # 2. Maximum delay/early time of event e is smaller than D
            model.addConstrs(
                delay[e] == time[e] - events_timetable_out.loc[e, 'time'] for e in events_timetable_out.index)
            model.addConstrs(abs_d[e] == abs_(delay[e]) for e in events_timetable_out.index)
            model.addConstrs(
                (abs_d[e] <= D + M * y[events_timetable_out.loc[e, 'traincode']] for e in origin_events_index_out), 'C1')

            # 3. Train running time in segment should be no less than the minimum segment running time
            model.addConstrs(
                (time[e2] - time[e1] >= segment_running_time[events_timetable_out.loc[e1, 'line']][station_loc(
                    events_timetable_out.loc[e1, 'line'], events_timetable_out.loc[e1, 'station'])]
                 for e1 in up_events_timetable_out[(up_events_timetable_out['dep'] == 1)
                                                   & (up_events_timetable_out['state'] != 'last')].index
                 for e2 in
                 up_events_timetable_out[
                     (up_events_timetable_out['traincode'] == up_events_timetable_out.loc[e1, 'traincode'])
                     & (up_events_timetable_out['station'] == up_events_timetable_out.loc[e1 + 1, 'station'])
                     & (up_events_timetable_out['line'] == up_events_timetable_out.loc[e1, 'line'])
                     & (up_events_timetable_out['arr'] == 1)].index)
                , 'C2-1')

            model.addConstrs(
                (time[e2] - time[e1] >= segment_running_time[events_timetable_out.loc[e2, 'line']][station_loc(
                    events_timetable_out.loc[e2, 'line'], events_timetable_out.loc[e2, 'station'])]
                 for e1 in down_events_timetable_out[(down_events_timetable_out['dep'] == 1)
                                                     & (down_events_timetable_out['state'] != 'last')].index
                 for e2 in down_events_timetable_out[
                     (down_events_timetable_out['traincode'] == down_events_timetable_out.loc[e1, 'traincode'])
                     & (down_events_timetable_out['station'] == down_events_timetable_out.loc[e1 + 1, 'station'])
                     & (down_events_timetable_out['line'] == down_events_timetable_out.loc[e1, 'line'])
                     & (down_events_timetable_out['arr'] == 1)].index)
                , 'C2-2')

            # 4. Train dwelling time in each middle station should be respected
            model.addConstrs((time[e2] - time[e1] >= dwell_time(
                events_timetable_out.loc[e1, 'traincode'], events_timetable_out.loc[e1, 'line'],
                events_timetable_out.loc[e1, 'station'], events_timetable_out, trains_information_out)
                              for e1 in events_timetable_out[events_timetable_out['arr'] == 1].index
                              for e2 in events_timetable_out[
                                  (events_timetable_out['traincode'] == events_timetable_out.loc[e1, 'traincode'])
                                  & (events_timetable_out['station'] == events_timetable_out.loc[e1, 'station'])
                                  & (events_timetable_out['dep'] == 1)].index)
                             , 'C4')

            # Station capacity constraint
            model.addConstrs((
                gp.quicksum(d[e3, e1] for e3 in events_timetable_out[
                    (events_timetable_out['station'] == events_timetable_out.loc[e1, 'station'])
                    & (events_timetable_out['arr'] == 1)
                    & (events_timetable_out['traincode'] != events_timetable_out.loc[e1, 'traincode'])
                    ].index)
                - gp.quicksum(g[e2, e1] for e2 in events_timetable_out[
                    (events_timetable_out['station'] == events_timetable_out.loc[e1, 'station'])
                    & (events_timetable_out['dep'] == 1)
                    & (events_timetable_out['traincode'] != events_timetable_out.loc[e1, 'traincode'])
                    ].index)
                <= (capacity[num_of_day][events_timetable_out.loc[e1, 'station']] - 1)
                for e1 in events_timetable_out[
                (events_timetable_out['station'].isin(stations_m)) & (events_timetable_out['arr'] == 1)].index)
                , 'C5')

            # Arrival-departure interval constrain in station of two train
            # Definition of fai: 定义g[e1][e1],如果列车e1从车站出发发生在列车e2到达该车站之前,则g[e1, e1]=1
            model.addConstrs((time[e2] - time[e1] + M2 * (1 - g[e1, e2]) >= ad_time_interval
                              for e1 in events_timetable_out[events_timetable_out['dep'] == 1].index
                              for e2 in events_timetable_out[
                                  (events_timetable_out['station'] == events_timetable_out.loc[e1, 'station'])
                                  & (events_timetable_out['arr'] == 1)
                                  & (events_timetable_out['traincode'] != events_timetable_out.loc[e1, 'traincode'])
                                  # & (up_events_timetable_out['line'] == up_events_timetable_out.loc[e1, 'line'])
                                  ].index)
                             , 'C6')

            # Headway constraints between train services
            # Same direction trains wouldn't overtake in segment
            # The arrival order in the next station just as the same as departure order in station
            model.addConstrs((d[e1, e2] == d[e3, e4]
                              for e1 in events_timetable_out[(events_timetable_out['dep'] == 1)
                                                             & (events_timetable_out['state'] != 'last')
                                                             ].index
                              for e2 in events_timetable_out[
                                  (events_timetable_out['station'] == events_timetable_out.loc[e1, 'station'])
                                  & (events_timetable_out['dep'] == 1)
                                  & (events_timetable_out['traincode'] != events_timetable_out.loc[e1, 'traincode'])
                                  & (events_timetable_out['line'] == events_timetable_out.loc[e1, 'line'])
                                  & (events_timetable_out['state'] != 'last')
                                  ].index
                              for e3 in events_timetable_out[
                                  (events_timetable_out['station'] == events_timetable_out.loc[e1 + 1, 'station'])
                                  & (events_timetable_out['arr'] == 1)
                                  & (events_timetable_out['traincode'] == events_timetable_out.loc[e1, 'traincode'])
                                  ].index
                              for e4 in events_timetable_out[
                                  (events_timetable_out['station'] == events_timetable_out.loc[e2 + 1, 'station'])
                                  & (events_timetable_out['station'] == events_timetable_out.loc[e3, 'station'])
                                  & (events_timetable_out['arr'] == 1)
                                  & (events_timetable_out['traincode'] == events_timetable_out.loc[e2, 'traincode'])
                                  & (events_timetable_out['line'] == events_timetable_out.loc[e3, 'line'])
                                  ].index)
                             , 'C7')

            # The departure and arrival minimum time interval between two trains should be respected. 列车追踪距离（3min）约束
            model.addConstrs((time[e1] - time[e2] + M2 * (1 - d[e2, e1]) >= arrival_time_interval
                              for e1 in up_events_timetable_out[(up_events_timetable_out['arr'] == 1)].index
                              for e2 in
                              up_events_timetable_out[
                                  (up_events_timetable_out['station'] == up_events_timetable_out.loc[e1, 'station'])
                                  & (up_events_timetable_out['arr'] == 1)
                                  & (up_events_timetable_out['traincode'] != up_events_timetable_out.loc[
                                      e1, 'traincode'])
                                  & (up_events_timetable_out['line'] == up_events_timetable_out.loc[e1, 'line'])
                                  ].index)
                             , 'C8-1-1')

            model.addConstrs((time[e1] - time[e2] + M2 * (1 - d[e2, e1]) >= arrival_time_interval
                              for e1 in down_events_timetable_out[(down_events_timetable_out['arr'] == 1)].index
                              for e2 in
                              down_events_timetable_out[
                                  (down_events_timetable_out['station'] == down_events_timetable_out.loc[e1, 'station'])
                                  & (down_events_timetable_out['arr'] == 1)
                                  & (down_events_timetable_out['traincode'] != down_events_timetable_out.loc[
                                      e1, 'traincode'])
                                  & (down_events_timetable_out['line'] == down_events_timetable_out.loc[e1, 'line'])
                                  ].index)
                             , 'C8-1-2')

            model.addConstrs((time[e1] - time[e2] + M2 * (1 - d[e2, e1]) >= departure_time_interval
                              for e1 in up_events_timetable_out[(up_events_timetable_out['dep'] == 1)].index
                              for e2 in
                              up_events_timetable_out[
                                  (up_events_timetable_out['station'] == up_events_timetable_out.loc[e1, 'station'])
                                  & (up_events_timetable_out['dep'] == 1)
                                  & (up_events_timetable_out['traincode'] != up_events_timetable_out.loc[
                                      e1, 'traincode'])
                                  & (up_events_timetable_out['line'] == up_events_timetable_out.loc[e1, 'line'])
                                  ].index)
                             , 'C8-2-1')

            model.addConstrs((time[e1] - time[e2] + M2 * (1 - d[e2, e1]) >= departure_time_interval
                              for e1 in down_events_timetable_out[(down_events_timetable_out['dep'] == 1)].index
                              for e2 in
                              down_events_timetable_out[
                                  (down_events_timetable_out['station'] == down_events_timetable_out.loc[e1, 'station'])
                                  & (down_events_timetable_out['dep'] == 1)
                                  & (down_events_timetable_out['traincode'] != down_events_timetable_out.loc[
                                      e1, 'traincode'])
                                  & (down_events_timetable_out['line'] == down_events_timetable_out.loc[e1, 'line'])
                                  ].index)
                             , 'C8-2-2')

            model.addConstrs((d[e1, e2] + d[e2, e1] == 1
                              for e1 in events_timetable_out.index
                              for e2 in events_timetable_out[
                                  (events_timetable_out['station'] == events_timetable_out.loc[e1, 'station'])
                                  & (events_timetable_out['dep'] == events_timetable_out.loc[e1, 'dep'])
                                  & (events_timetable_out['traincode'] != events_timetable_out.loc[e1, 'traincode'])
                                  ].index)
                             , 'C9')

            # Extra constrain
            model.addConstrs((d[e1, e3] >= g[e2, e3]
                              for e1 in events_timetable_out[(events_timetable_out['arr'] == 1) &
                                                             (events_timetable_out['state'] == 'middle')].index
                              for e2 in events_timetable_out[
                                  (events_timetable_out['station'] == events_timetable_out.loc[e1, 'station'])
                                  & (events_timetable_out['dep'] == 1)
                                  & (events_timetable_out['traincode'] == events_timetable_out.loc[e1, 'traincode'])
                                  ].index
                              for e3 in events_timetable_out[
                                  (events_timetable_out['station'] == events_timetable_out.loc[e1, 'station'])
                                  & (events_timetable_out['arr'] == 1)
                                  & (events_timetable_out['traincode'] != events_timetable_out.loc[e1, 'traincode'])
                                  ].index)
                             , 'C10')

            # Part 0. Objective function
            code = {}
            for t in trains:
                if t[-1].isalpha():
                    if t[-2].isalpha():
                        code[t] = t[:-2]
                    else:
                        code[t]=t[:-1]
                else:
                    code[t]=t
                    
            passenger_demand = {t: origin_passenger_demand[code[t]] for t in trains}

            num_p_p_c = gp.quicksum(max(len(passenger_demand[t]),1) * y[t] for t in trains)

            num_p_p_d = gp.quicksum(max((len(passenger_demand[events_timetable_out.loc[e, 'traincode']][
                                                passenger_demand[events_timetable_out.loc[e, 'traincode']]['D'] ==
                                                events_timetable_out.loc[e, 'station']])
                                        + len(passenger_demand[events_timetable_out.loc[e, 'traincode']][
                                                  passenger_demand[events_timetable_out.loc[e, 'traincode']]['O'] ==
                                                  events_timetable_out.loc[e, 'station']])),1) * abs_d[e]
                                       for e in origin_events_index_out)

            objective = p_p_delay * num_p_p_d + p_p_cancel * num_p_p_c

            model.setObjective(objective, GRB.MINIMIZE)
            model.optimize()

            time_changed_train = []
            for e in origin_events_index_out:
                if time[e].x != events_timetable_out.loc[e, 'time']:
                    t = events_timetable_out.loc[e, 'traincode']
                    if not t in time_changed_train:
                        time_changed_train.append(t)
            
            canceled_train = copy.deepcopy(canceled_train_in)
            for i in trains:
                if y[i].x == 1:
                    canceled_train.append(i)
            
            timetable_out = pd.DataFrame(columns=['Train', 'Station', 'Time', 'Time Change', 'Operate or not'])
            for i in events_timetable_out.index:
                timetable_out.loc[len(timetable_out.index)] = [events_timetable_out.loc[i, 'traincode'],
                                                             events_timetable_out.loc[i, 'station'],
                                                             time[i].x,
                                                             time[i].x - events_timetable_out.loc[i, 'time'],
                                                             y[events_timetable_out.loc[i, 'traincode']].x]

            timetable_out.to_csv('timetable_out_' + str(num_of_day) + '.csv', encoding='utf-8_sig')

            TRP_delay = p_p_delay * num_p_p_d.getValue()
            TRP_cancel = p_p_cancel * num_p_p_c.getValue()

            # %% 运行passenger_routing
            if canceled_train: 
                # 取消列车的乘客需求
                canceled_passenger_demand = pd.DataFrame(columns=('O', 'D', 'O_time', 'D_time'))
                for t in canceled_train:
                    canceled_passenger_demand = pd.concat([canceled_passenger_demand, origin_passenger_demand[t]],
                                                          ignore_index=True)

                canceled_passenger_demand = canceled_passenger_demand[~(
                    (canceled_passenger_demand['O'].isin(not_to_station[num_of_day]))
                    &
                    (canceled_passenger_demand['D'].isin(not_to_station[
                        num_of_day])))]
                canceled_passenger_demand = canceled_passenger_demand[(canceled_passenger_demand['O_time'] >= 0)
                                                      & (canceled_passenger_demand['D_time'] <= 120)]

                canceled_passenger_demand.reset_index(drop=True, inplace=True)

                # 数据格式处理
                train_data_p = pd.DataFrame(columns=['station', 'arr', 'dep', 'train'])
                for t in (set(np.unique(origin_events_timetable_out['traincode'])) - set(canceled_train)):
                    for s in np.unique(
                            origin_events_timetable_out[origin_events_timetable_out['traincode'] == t]['station']):
                        if len(origin_events_timetable_out[(origin_events_timetable_out['traincode'] == t) &
                                                       (origin_events_timetable_out['station'] == s)]) == 2:
                            arr_time = origin_events_timetable_out.loc[
                                (origin_events_timetable_out['traincode'] == t) &
                                (origin_events_timetable_out['station'] == s) &
                                (origin_events_timetable_out['arr'] == 1), 'time'].item()
                            dep_time = origin_events_timetable_out.loc[
                                (origin_events_timetable_out['traincode'] == t) &
                                (origin_events_timetable_out['station'] == s) &
                                (origin_events_timetable_out['dep'] == 1), 'time'].item()
                        else:
                            if origin_events_timetable_out.loc[
                                (origin_events_timetable_out['traincode'] == t) &
                                (origin_events_timetable_out['station'] == s), 'arr'].item() == 1:
                                arr_time = origin_events_timetable_out.loc[
                                    (origin_events_timetable_out['traincode'] == t) &
                                    (origin_events_timetable_out['station'] == s) &
                                    (origin_events_timetable_out['arr'] == 1), 'time'].item()
                                dep_time = arr_time
                            else:
                                dep_time = origin_events_timetable_out.loc[
                                    (origin_events_timetable_out['traincode'] == t) &
                                    (origin_events_timetable_out['station'] == s) &
                                    (origin_events_timetable_out['dep'] == 1), 'time'].item()
                                arr_time = dep_time
                        train_data_p = pd.concat([train_data_p, pd.DataFrame(pd.Series({'station': s, 'arr': arr_time,
                                                                                        'dep': dep_time, 'train': t})).T],
                                                 ignore_index=True)
                train_data_p = train_data_p.sort_values(by=['train', 'arr'], inplace=False, ascending=True)

                train = np.unique(train_data_p['train'])  # 非中断线路运行没有取消的列车 T_out

                can_train = {}
                for p in canceled_passenger_demand.index:
                    can_t = []
                    i = canceled_passenger_demand.loc[p, 'O']
                    j = canceled_passenger_demand.loc[p, 'D']
                    for o in origin_can_train.keys():
                        for d in origin_can_train[o].keys():
                            if (i == o) & (j == d):
                                for t in origin_can_train[o][d]:
                                    if t in train:
                                        can_t.append(t)
                    can_train[p] = can_t

                can_passenger = {t: [can_train[0] for can_train in can_train.items() if t in can_train[1]] for t in train}

                model_passenger = gp.Model('PR')
                #  Decision variables:
                yp = model_passenger.addVars(canceled_passenger_demand.index, vtype=GRB.BINARY, name='yp')
                z_p = model_passenger.addVars(canceled_passenger_demand.index, train, vtype=GRB.BINARY, name='z')

                # Constrains
                ## 乘客分配约束
                model_passenger.addConstrs(
                    (gp.quicksum(z_p[p, t] for t in can_train[p]) + yp[p] == 1 for p in canceled_passenger_demand.index),
                    name='cp1')
                model_passenger.addConstrs(
                    (gp.quicksum(z_p[p, t] for t in train) <= 1 for p in canceled_passenger_demand.index),
                    name='cp2')

                ##  列车容量约束
                ### 列车在每一个站的容量约束
                model_passenger.addConstrs(
                    (gp.quicksum(
                        z_p[p, t] for p in can_passenger[t] if canceled_passenger_demand.loc[p]['O'] in get_value(s))
                     +
                     gp.quicksum(z_p[p1, t] for p1 in can_passenger[t] if
                                 this_station(t).index(canceled_passenger_demand.loc[p1][0]) <=
                                 this_station(t).index(s))
                     -
                     gp.quicksum(z_p[p2, t] for p2 in can_passenger[t] if
                                 this_station(t).index(canceled_passenger_demand.loc[p2][0]) <=
                                 this_station(t).index(s))
                     <= V[code[t]] - v[(code[t], s)]
                     for t in train
                     for s in this_data(t)['station'])
                    , name='train_capacity_cons')

                #  Objective function
                d_O = gp.quicksum(z_p[p, t] * abs(int([this_data(t).loc[i, 'dep'] for i in this_data(t).index
                                                       if canceled_passenger_demand.loc[p]['O'] in get_value(
                        this_data(t).loc[i, 'station'])][0])
                                                  - int(canceled_passenger_demand.loc[p]['O_time']))
                                  for p in canceled_passenger_demand.index for t in can_train[p])

                d_D = gp.quicksum(z_p[p, t] * abs(int([this_data(t).loc[i, 'arr'] for i in this_data(t).index
                                                       if canceled_passenger_demand.loc[p]['D'] in get_value(
                        this_data(t).loc[i, 'station'])][0])
                                                  - int(canceled_passenger_demand.loc[p]['D_time']))
                                  for p in canceled_passenger_demand.index for t in can_train[p])

                p_cancel = gp.quicksum(yp[p] for p in canceled_passenger_demand.index)
                passenger_rerouting_delay = d_O * p_p_delay + d_D * p_p_delay
                passenger_rerouting_cancel = p_cancel * p_p_cancel
                model_passenger.setObjective(passenger_rerouting_delay + passenger_rerouting_cancel, GRB.MINIMIZE)

                # 更新模型
                model_passenger.optimize()

                canceled_passenger_demand['to_train'] = 0
                for i in canceled_passenger_demand.index:  # 输出乘客重安排结果
                    for t in train:
                        if z_p[i, t].x == 1:
                            canceled_passenger_demand.loc[i, 'to_train'] = t

                passenger_demand_2 = canceled_passenger_demand[canceled_passenger_demand['to_train'] == 0]  # 没有安排的乘客

                # 输出
                passenger_need_rerouting = len(canceled_passenger_demand)
                success_rerouted = len(canceled_passenger_demand) - len(passenger_demand_2)
                passenger_rerouting_delay = passenger_rerouting_delay.getValue()
                passenger_rerouting_cancel = passenger_rerouting_cancel.getValue()

            # %% 功能及韧性指标计算 
                ## 1.没有加开列车且有原计划列车取消的情况
                ## 恢复阶段判断
                if num_of_day in emergence_period:
                    station_loss={}
                    for i in station_loss_passenger.keys():
                        unconsider_station = list(set(list(set(outage_stations)-set(input_in_area_station[num_of_day][3]))+not_to_station[num_of_day]))
                        if not i[1] in unconsider_station:
                            station_loss[i]=station_loss_passenger[i]
                            
                    function_of_the_day = math.exp(
                        -(TRP_delay + passenger_rerouting_delay +
                          passenger_rerouting_cancel+ sum(station_loss.values()) * p_p_cancel) / 10000)
                else:  ## 考虑出行需求、准时性需求和车站集散能力造成无法满足的旅客需求
                    station_loss={}
                    for i in station_loss_passenger.keys():
                        unconsider_station = list(set(outage_stations)-set(input_in_area_station[num_of_day][3]))
                        if not i[1] in unconsider_station:
                            station_loss[i]=station_loss_passenger[i]
                            
                    function_of_the_day = math.exp(
                        -(TRP_delay + passenger_rerouting_delay +
                          passenger_rerouting_cancel + 
                          sum(station_loss.values()) * p_p_cancel) / 10000)

            ## 2.没有加开列车且没有原计划列车取消的情况
            else:
                if num_of_day in emergence_period:
                    station_loss={}
                    for i in station_loss_passenger.keys():
                        unconsider_station = list(set(list(set(outage_stations)-set(input_in_area_station[num_of_day][3]))+not_to_station[num_of_day]))
                        if not i[1] in unconsider_station:
                            station_loss[i]=station_loss_passenger[i]
                    function_of_the_day = math.exp(
                        -(TRP_delay + sum(station_loss.values()) * p_p_cancel) / 10000)
                else:  ## 考虑出行需求、准时性需求和车站集散能力造成无法满足的旅客需求
                    station_loss={}
                    for i in station_loss_passenger.keys():
                        unconsider_station = list(set(outage_stations)-set(input_in_area_station[num_of_day][3]))
                        if not i[1] in unconsider_station:
                            station_loss[i]=station_loss_passenger[i]
                            
                    function_of_the_day = math.exp(
                        -(TRP_delay + sum(station_loss.values()) * p_p_cancel) / 10000)
            
            function[num_of_day] = function_of_the_day
            # return function_of_the_day

    # %% 恢复周期内功能计算
    for num_of_day in repair_data.keys():
        if num_of_day == 0:
            station_system_state[num_of_day] = copy.deepcopy(station_system_state_origin)
            broken_line[num_of_day] = copy.deepcopy(broken_line_origin)
            capacity[num_of_day] = copy.deepcopy(capacity_origin)
        else:
            station_system_state[num_of_day] = copy.deepcopy(station_system_state[num_of_day-1])
            broken_line[num_of_day] = copy.deepcopy(broken_line[num_of_day-1])
            capacity[num_of_day] = copy.deepcopy(capacity[num_of_day-1])   
            for repair_subsys in repair_data[num_of_day]:
                if repair_subsys[0] == 'station_system_state':
                    station_system_state[num_of_day][repair_subsys[1]][repair_subsys[2]] = [1, 0, 0]
                elif repair_subsys[0] == 'broken_line':
                    broken_line[num_of_day] = {key: val for key, val in broken_line[num_of_day].items() if
                                                   key != repair_subsys[1]}
                else:
                    capacity[num_of_day][repair_subsys[1]] += 1
    
    function = {}
    # for num_of_day in repair_data.keys():
    #     function[num_of_day] = daily_function_value(num_of_day)
    
    if __name__=='__main__':
        for num_of_day in repair_data.keys():
            sub_thread = threading.Thread(target=daily_function_value(num_of_day))
            sub_thread.start()
    
    recovery_function = [function[f] for f in function.keys() if function[f] < 1 ]
    total_function = sum(recovery_function)
    return function, recovery_function, total_function


# %%  初始部件受损情况
station_system_state = {}
broken_line = {}
capacity = {}
station_system_state[0] = copy.deepcopy(station_system_state_origin)
broken_line[0] = copy.deepcopy(broken_line_origin)
capacity[0] = copy.deepcopy(capacity_origin)

time_start = time.time()

function_list, recovery_function, total_function = total_function(repair_data)

resilience = total_function/(len(recovery_function)+1)

time_end = time.time()

cal_time = time_end - time_start

print(cal_time)
print(function_list, resilience)