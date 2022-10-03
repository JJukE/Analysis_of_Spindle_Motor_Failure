import matplotlib.pyplot as plt
import pandas as pd
import pickle
import natsort
import numpy as np
import os
import argparse

from numpy.fft import fft
from mpl_toolkits.mplot3d import Axes3D

parser = argparse.ArgumentParser(description='parsers')
parser.add_argument('--spindle_num', required=True, help='SPINLE number in the path (ex. SPINDLE1 -> 1)')
parser.add_argument('--datapath', required=True, help='setting data path (ex.S2_MR1_U2)')
parser.add_argument('--savepath', required=True, help='path to save')
parser.add_argument('--start', required=True, help='start index of folder')
parser.add_argument('--end', required=True, help='end index of folder')


#=========================================================================
# fft_spindle
# function to fft transformation
#=========================================================================
def fft_spindle(data):
    # FFT
    N = len(data) # 10000 (1초간 10000개 data 측정)
    T = 1.0 / 10000 # 측정 주기
    amp_x_dis = fft(data['x_dis'].values) # fft 결과 x_dis 열의 amplitude 값
    amp_y_dis = fft(data['y_dis'].values) # fft 결과 y_dis 열의 amplitude 값
    amp_x_dis = 2.0/N * np.abs(amp_x_dis[:N//2]) # 반만 필요
    amp_y_dis = 2.0/N * np.abs(amp_y_dis[:N//2])
    freq = np.linspace(0.0, 1.0/(2.0*T), N//2) # frequency (반만 가져옴)
    return freq, amp_x_dis, amp_y_dis

#=========================================================================
# merge_and_transform
# Merge the raw data and transform to dataframe which has 7 attributes as below.
# 1. Filtered_freq_list
# 2. popCount_freq
# 3. popCount_x
# 4. popCount_y
# 5. popDegree_mean_x
# 6. popDegree_mean_y
#=========================================================================
def merge_and_transform(spindle_idx, data_dir, start, end, save_dir, threshold=0.001, fft_example_idx=0):
    #============================================================
    # Arguments
    # spindle_idx : 폴더 안에 SPINDLE1_TEST인지, SPINDLE2_TEST인지 등
    # data_dir : txt 데이터가 들어가 있는 폴더
    # start : TEST_XXX에서 시작할 index
    # end : TEST_XXX에서 끝날 index
    # save_dir : TEST_XXX 파일 각각을 merge 및 transform 후 저장할 directory
    # threshold : 튄 값의 기준 (default: 0.001)
    # fft_example_idx : fft 그려볼 index (default: 0)
    #============================================================
    data_path_list = []
    save_path_list = []
    for dir in os.listdir(data_dir):
        # for TEST_XXX,
        if os.path.isdir(dir) and 'TEST_' in dir:
            if ('(' not in dir and dir.split('_')[1] >= start and dir.split('_')[1] <= end) or 
            ('(' in dir and dir.split('_')[1].split('(')[0] >= start and dir.split('_')[1].split('(') <= end):
                save_path_list.append(dir) # file name만
                dir = os.path.join(data_dir, dir) # 전체 path
                data_path_list.append(dir)
                if dir.split('_')[1].split('(')[0] == start:
                    print('start directory: ', dir)
                elif dir.split('_')[1].split('(')[0] == end:
                    print('end directory: ', dir)
                    print('num of dirs:', len(data_path_list))
                    print()

    for directory in data_path_list:
        print('#########################################################')
        print("for the directory '{}'".format(directory))
        file_paths = []
        file_names = []
        for dirname, _, filenames in os.walk(directory):
            filenames = natsort.natsorted(filenames)
            for filename in filenames:
                path = os.path.join(dirname, filename)
                if (path.endswith('txt') and 'SPINDLE' + str(spindle_idx) + '_TEST' in path and '-' in path and 'RMS' not in path):
                    file_paths.append(path)
                    file_names.append(filename)
        print("Num of paths: ", len(file_paths))
    
        # 초당 데이터 FFT 변환
        t_data = []
        for i in range(len(file_paths)):
            t_data.append(pd.read_table(file_paths[i], sep='\t', header=None,
                                        names=['time', 'x_acc', 'time2', 'y_acc', 'time3', 'temperature',
                                            'time4', 'x_dis', 'time5', 'y_dis']))
            # 불필요한 열 삭제
            t_data[i].drop(['time2', 'time3', 'temperature', 'time4', 'time5'], axis=1, inplace=True)
        
        print("Num of time domain data: ", len(t_data))
        
        # 새로운 df 생성
        filteredFreq = []
        numPop_total = [] # x, y distance 총 튄 값 개수
        numPop_x = [] # x distance 튄 값 개수 list
        numPop_y = [] # y distance 튄 값 개수 list
        popVal_x = [] # x distance 튄 값들의 평균값 list
        popVal_y = [] # y distance 튄 값들의 평균값 list
        popVal_mean = [] # x, y 전체 튄 값들의 평균값 list
        
        # 20000 기준으로 나눠서 진행 (메모리 문제)
        num_data = len(t_data)
        k = num_data // 20000
        for i in range(k + 1):
            for j in range(20000 * i, 20000 * (i + 1)):
                if j >= num_data:
                    print("transformed the data!")
                    break
                elif j % 10000 == 0: print("{}th new data created!".format(j))
                else:
                    freq, pop_x, pop_y = fft_spindle(t_data[j])
                    pop_x[0] = 0 # 맨 처음 값은 FFT 특성 상 큰 값을 가지므로 무시
                    pop_y[0] = 0
                    freq = np.where(((pop_x > threshold) | (pop_y > threshold)), freq, 0)
                    # print(len(freq))
                    # print(np.count_nonzero(freq))
                    pop_x = np.where(pop_x > threshold, pop_x, 0) # 튄 값만 그대로 두고 나머지는 0
                    pop_y = np.where(pop_y > threshold, pop_y, 0)
                    # print(len(pop_x))
                    # print(np.count_nonzero(pop_x))

                    filteredFreq.append(freq[np.nonzero(freq)]) # 튄 값의 freq를 하나의 리스트로
                    numPop_total.append(np.count_nonzero(freq))
                    numPop_x.append(np.count_nonzero(pop_x))
                    numPop_y.append(np.count_nonzero(pop_y))
                    popVal_x.append(np.sum(pop_x) / np.count_nonzero(pop_x))
                    popVal_y.append(np.sum(pop_y) / np.count_nonzero(pop_y))
                    popVal_mean.append((np.sum(pop_x) + np.sum(pop_y)) /
                                    (np.count_nonzero(pop_x) + np.count_nonzero(pop_y)))
        df = pd.DataFrame({
            'Filtered_freq_list' : filteredFreq,
            'popCount_freq' : numPop_total,
            'popCount_x' : numPop_x,
            'popCount_y' : numPop_y,
            'popDegree_mean_x' : popVal_x,
            'popDegree_mean_y' : popVal_y,
            'popDegree_total_mean' : popVal_mean
        })
        print(df.info())
        
        transformed_dfs.append(df)
        print('#########################################################')
        print()
        print()
        
    print('number of total transformed df: ', len(transformed_dfs))
    print()
    print()

    # 마지막 directory의 FFT Plot
    freq, amp_x, amp_y = fft_spindle(t_data[fft_example_idx])
    plt.plot(freq, amp_x)
    plt.xlim(0, 5000)
    plt.ylim(0, 0.001)
    plt.show()
    
    # save each dataframe as a pickle file
    for i in range(len(transformed_dfs)):
        with open(save_path + '/transformed_' + save_path_list[i] + '.pickle', 'wb') as w:
            pickle.dump(transformed_dfs[i], w)

    return transformed_dfs