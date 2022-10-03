import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import pickle
import math
import natsort
from numpy.fft import fft
import argparse
import easydict

parser = argparse.ArgumentParser(description='path parsers')
parser.add_argument('--datapath', required=True, help='setting data path')
parser.add_argument('--savepath', required=True, help='path to save')
parser.add_argument('--start', required=True, help='start index of folder')
parser.add_argument('--end', required=True, help='end index of folder')

args = easydict.EasyDict(
    {
        "datapath" : "/Volumes/Spindle/S2_MR1_U2",
        "savepath" : "/Volumes/Spindle/S2_MR1_U2/PickleData",
        "start" : "160",
        "end" : "176"
    }
)

# args = parser.parse_args()

def save_folder_as_pickle(folder_idx):
    # setting data path
    for dirs in os.listdir(args.datapath):
        if 'TEST_' + folder_idx in dirs and not dirs.endswith('zip'):
            data_path = args.datapath + '/' + dirs
            print(str(folder_idx) + 'th folder to pickle!')
            print('data path: ', data_path)

            # natsort
            # 모든 텍스트 파일 불러오기
            file_paths = [] # 파일 경로를 담을 배열 선언
            file_names = [] # 파일 이름을 담을 배열 선언

            for dirname, _, filenames in os.walk(data_path):
                filenames = natsort.natsorted(filenames)
                for filename in filenames:
                    path = os.path.join(dirname, filename)
                    
                    # 파일명에 SPINDLE1_TEST를 포함하고, -와 RMS는 포함하지 않는 경우 1초간의 rawData
                    if(path.endswith('txt') and "SPINDLE1_TEST" in path and "-" not in path and "RMS" not in path):
                        file_paths.append(path)
                        file_names.append(filename)

            for i in range(len(file_paths)):
                print(file_paths[i])
                print(file_names[i])
                if i > 3 or len(file_paths) == (1 or 2): break

            # text to dataframe (+ concatenate)
            df_arr = [] # 각각의 파일을 dataframe으로 불러와 배열에 저장
            for i in range(len(file_paths)):
                df_arr.append(pd.read_table(file_paths[i], sep='\t', header=None,
                                            names=['time', 'x_acc', 'time2', 'y_acc', 'time3', 'temperature',
                                                'time4', 'x_dis', 'time5', 'y_dis']))

                # 불필요한 열 삭제
                df_arr[i].drop(['time2', 'time3', 'temperature', 'time4', 'time5'], axis=1, inplace=True)

            if len(file_paths) > 1:
                # print(df_arr[0])
                print(df_arr[1].columns)
                print('dataframe으로 불러온 array 개수: ', len(df_arr))
                print('파일 path 개수 (위와 같아야 함): ', len(file_paths))
                len_df_0 = len(df_arr[0])
                print('첫 번째 파일 행 개수: ', len_df_0)
                len_df_1 = len(df_arr[1])
                print('두 번째 파일 행 개수: ', len_df_1)

            for i in range(len(file_paths)):
                df_arr[i]['x_acc'] = df_arr[i]['x_acc'].astype(np.float16)
                df_arr[i]['y_acc'] = df_arr[i]['y_acc'].astype(np.float16)
                df_arr[i]['x_dis'] = df_arr[i]['x_dis'].astype(np.float16)
                df_arr[i]['y_dis'] = df_arr[i]['y_dis'].astype(np.float16)

            # merging
            if len(file_paths) == 1:
                df = df_arr[0]
            else:
                last_index = df_arr[0].shape[0] # 마지막 행 index (확인용)
                print(last_index)

                for i in range(len(file_paths) - 1): # 마지막 파일은 제외
                    last_time = df_arr[i].iloc[-1,0]
                    
                    if (i == 0):
                        print(last_time)
                        print(type(last_time))
                    
                    # 연결될 파일(다음 파일)의 time열에만 last_time을 더함
                    df_arr[i+1] = df_arr[i+1].add([last_time + 600, 0, 0, 0, 0], axis=1) # 600초 간격 부여
                    
                    if (i == 0):
                        print(df_arr[i].iloc[last_index - 1,:])
                        print()
                        print(df_arr[i+1].iloc[0,:])
                    
                # dataframe을 연결함
                df = pd.concat(df_arr, ignore_index=True)
                df_arr[i+1] = pd.concat([df_arr[i], df_arr[i+1]], axis=0)

                print('Merge Results: ')
                print(df.iloc[len_df_0 - 1,:])
                print()
                print(df.iloc[len_df_0,:])

                print(len(df_arr[0]))
                print(len(df_arr[1]))

            print(len(df))
            print(len(df_arr))
            print()
            print(df.head())
            print(df.info())
            print(df.describe())
            print('column 별 결측치 개수')
            print(df.isnull().sum())

            # save as pickle
            with open(args.savepath + '/TEST_' + folder_idx + '.pickle', 'wb') as fw:
                pickle.dump(df, fw, protocol=4)
                print('========================================================')
                print('saved as: ', args.savepath)
                print('========================================================')

for i in range(int(args.start), int(args.end) + 1):
    save_folder_as_pickle(str(i))
    print(str(i) + 'th folder to pickle!')