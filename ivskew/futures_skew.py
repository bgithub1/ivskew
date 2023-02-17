#!/usr/bin/env python
# coding: utf-8

# ### Description
# Build a grid-like Dash app with the dgrid_components.py module to display:
# 1. Volatility Skew of various Futures Options vs At-The-Money Volatility of those options
# 2. Volatility Skew of various Futures Options vs Price
# 3. At-The-Money Volatility of various Futures Options vs Price
# 
# ### Usage
# 1. Run all of the cells
# 2. The last cell that executes ```app.run_server``` will display a link to a local URL.  Click on the URL to see the application
# 

# In[ ]:

import sys,os
import importlib
import numpy as np
import datetime
import json
import pandas as pd
import tqdm
import traceback
import pathlib
import pdb

from IPython.display import display

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

import dash
import dash_html_components as html
import plotly_utilities as pu
# import plotly.graph_objs as go
# import plotly.tools as tls
from plotly.offline import  iplot
# from plotly.graph_objs.layout import Font,Margin

# if  not os.path.abspath('./') in sys.path:
#     sys.path.append(os.path.abspath('./'))
# if  not os.path.abspath('../') in sys.path:
#     sys.path.append(os.path.abspath('../'))

from scipy.signal import argrelextrema
from scipy.stats import norm
import pandas_datareader as pdr

import logger_init

# a logger is always helpful
logger = logger_init.init_root_logger('logfile.log','INFO') 

SYSTEM_HOME = pathlib.Path.home()
DEFAULT_CONFIGS = {"PATH_DATA_HOME":"./",
                  "host":"127.0.0.1",
                  "port":8550,
                  "url_base_pathname":"futskew"}
STYLE_TITLE={
    'line-height': '20px',
    'textAlign': 'center',
    'background-color':'#47bacc',
    'color':'#FFFFF9',
    'vertical-align':'middle',
} 

# read configuration
# try:
#     configs = json.load(open('./futures_skew.conf','r'))
#     logger.info(f'using configs located at futures_skew.conf')
# except:
#     traceback.print_exc()
#     logger.info(f'using default configs')
#     configs = DEFAULT_CONFIGS.copy()
configs = DEFAULT_CONFIGS.copy()

PATH_DATA_HOME = configs['PATH_DATA_HOME']
FILENAME_SKEW = 'df_iv_skew_COMMOD.csv'
FILENAME_IV = 'df_iv_final_COMMOD.csv'
FILENAME_FUT = 'df_cash_futures_COMMOD.csv'

SKEW_RANGE_LIST = [.05,.1,.2]

LEGEND_X=-0.1
LEGEND_Y=1.2




# def plotly_plot(df_in,x_column,plot_title=None,
#                 y_left_label=None,y_right_label=None,
#                 bar_plot=False,figsize=(16,10),
#                 number_of_ticks_display=20,
#                 yaxis2_cols=None):
#     ya2c = [] if yaxis2_cols is None else yaxis2_cols
#     ycols = [c for c in df_in.columns.values if c != x_column]
#     # create tdvals, which will have x axis labels
#     td = list(df_in[x_column]) 
#     nt = len(df_in)-1 if number_of_ticks_display > len(df_in) else number_of_ticks_display
#     spacing = len(td)//nt
#     tdvals = td[::spacing]
    
#     # create data for graph
#     data = []
#     # iterate through all ycols to append to data that gets passed to go.Figure
#     for ycol in ycols:
#         if bar_plot:
#             b = go.Bar(x=td,y=list(df_in[ycol]),name=ycol,yaxis='y' if ycol not in ya2c else 'y2')
#         else:
#             b = go.Scatter(x=td,y=list(df_in[ycol]),name=ycol,yaxis='y' if ycol not in ya2c else 'y2')
#         data.append(b)

#     # create a layout
#     layout = go.Layout(
#         autosize=True,
#         title=plot_title,
#         xaxis=dict(
#             ticktext=tdvals,
#             tickvals=tdvals,
#             tickangle=45,
#             type='category'),
#         yaxis=dict(
#             title='y main' if y_left_label is None else y_left_label
#         ),
#         yaxis2=dict(
#             title='y alt' if y_right_label is None else y_right_label,
#             overlaying='y',
#             side='right'),
#         margin=Margin(
#             b=100
#         )        
#     )

#     fig = go.Figure(data=data,layout=layout)
#     return fig


class IvSkewStatic:
    def __init__(self): 
        df_iv_skew, df_iv_final, df_cash_futures = self.build_static_files()
        self.df_iv_skew = df_iv_skew
        self.df_iv_final = df_iv_final
        self.df_cash_futures = df_cash_futures

    def build_static_files(self):
        df_iv_skew = None
        df_iv_final = None
        df_cash_futures = None
        for commod in ['CL','CB','ES','NG']:
            fn_skew = FILENAME_SKEW.replace('COMMOD',commod)
            df_skew = pd.read_csv(f'{PATH_DATA_HOME}/{fn_skew}')
            df_skew = df_skew.dropna()
            fn_iv = FILENAME_IV.replace('COMMOD',commod)
            df_iv = pd.read_csv(f'{PATH_DATA_HOME}/{fn_iv}')
            df_iv = df_iv[[c for c in df_iv.columns.values if c not in ['close_x','pc']]]
            df_iv = df_iv.dropna()
            fn_fut = FILENAME_FUT.replace('COMMOD',commod)
            df_fut = pd.read_csv(f'{PATH_DATA_HOME}/{fn_fut}')
            df_fut = df_fut.dropna()
            df_skew['commod'] = commod
            df_iv['commod'] = commod
            df_fut['commod'] = commod
            if df_iv_skew is None:
                df_iv_skew = df_skew.copy()
                df_iv_final = df_iv.copy()
                df_cash_futures = df_fut.copy()
            else:
                df_iv_skew = df_iv_skew.append(df_skew.copy())
                df_iv_final = df_iv_final.append(df_iv.copy())
                df_cash_futures = df_cash_futures.append(df_fut.copy())
        df_iv_skew = df_iv_skew.rename(columns={c:float(c) for c in df_iv_skew.columns.values if '0.' in c})
        return df_iv_skew, df_iv_final, df_cash_futures  

    def plot_skew_vs_atm(self,SYMBOL_TO_RESEARCH,dist_from_zero=.1,year=None,number_of_ticks_display=10):
            # Step 00: select only SYMBOL_TO_RESEARCH from DataFrames 
            df_iv_final = self.df_iv_final[self.df_iv_final.symbol.str.slice(0,2)==SYMBOL_TO_RESEARCH].copy()
            df_iv_skew = self.df_iv_skew[self.df_iv_skew.symbol.str.slice(0,2)==SYMBOL_TO_RESEARCH].copy()
            df_cash_futures = self.df_cash_futures[self.df_cash_futures.symbol.str.slice(0,2)==SYMBOL_TO_RESEARCH].copy()
            
            year = 'all' if year is None else year
            if str(year).lower() != 'all':
                y = int(str(year))
                beg_year = y*100*100+1*100+1
                end_year = y*100*100+12*100+31
                df_iv_final = df_iv_final[(df_iv_final.settle_date>=beg_year) & (df_iv_final.settle_date<=end_year)]
                df_iv_skew = df_iv_skew[(df_iv_skew.settle_date>=beg_year) & (df_iv_skew.settle_date<=end_year)]
                df_cash_futures = df_cash_futures[(df_cash_futures.settle_date>=beg_year) & (df_cash_futures.settle_date<=end_year)]

            # sort by settle_date
            df_iv_final = df_iv_final.sort_values('settle_date') 
            df_iv_skew = df_iv_skew.sort_values('settle_date') 
            df_cash_futures = df_cash_futures.sort_values('settle_date') 

            print(f'plot_skew_vs_atm year: {year}')

            # Step 01: create df_skew_2, which holds skew difference between 
            #   positive dist_from_zero and negative dist_from_zero, for each settle_date
            df_skew_2 = df_iv_skew.copy()
            df_skew_2.index.name = None
            skew_range_col = f'iv_skew'
            df_skew_2[skew_range_col] = df_skew_2[dist_from_zero] - df_skew_2[-dist_from_zero]
            df_skew_2.settle_date = df_skew_2.settle_date.astype(int)
            df_skew_2 = df_skew_2[['settle_date',skew_range_col]]
            
            # Step 02: create atm implied vol table, that also has the cash price for each settle_date
            df_atmv = df_iv_final[['settle_date','atm_iv']].drop_duplicates()
            df_cf = df_cash_futures[df_cash_futures.symbol==f'{SYMBOL_TO_RESEARCH}Z99']
            df_atmv = df_atmv.merge(df_cf[['settle_date','close']],how='inner',on='settle_date')
            
            # Step 03: merge skew and atm vol/close tables
            df_ivs = df_skew_2.merge(df_atmv,how='inner',on='settle_date')
            df_ivs = df_ivs.sort_values('settle_date')
            
            # Step 04: plot skew vs atm_iv
            chart_title = f'{SYMBOL_TO_RESEARCH} skew {dist_from_zero*100}% up and down vs atm vol'
            df_ivs_skew_vs_atm_iv = df_ivs[['settle_date',skew_range_col,'atm_iv']]
            fig_skew_vs_atm_iv = pu.plotly_plot(
                df_ivs_skew_vs_atm_iv,x_column='settle_date',yaxis2_cols=['atm_iv'],
                y_left_label='iv_skew',y_right_label='atm_iv',plot_title=chart_title,
                legend_x= LEGEND_X,legend_y=LEGEND_Y,number_of_ticks_display=number_of_ticks_display
            )
            
            # Step 05: plot skew vs close
            chart_title = f'{SYMBOL_TO_RESEARCH} skew {dist_from_zero*100}% up and down vs close'
            df_ivs_skew_vs_close = df_ivs[['settle_date',skew_range_col,'close']]
            fig_skew_vs_close = pu.plotly_plot(
                df_ivs_skew_vs_close,x_column='settle_date',yaxis2_cols=['close'],
                y_left_label='iv_skew',y_right_label='close',plot_title=chart_title,
                legend_x= LEGEND_X,legend_y=LEGEND_Y,number_of_ticks_display=number_of_ticks_display
            )
            return fig_skew_vs_atm_iv,fig_skew_vs_close

    
    def plot_atm_vs_close(self,SYMBOL_TO_RESEARCH,year=None,number_of_ticks_display=10):
        # Step 00: select only SYMBOL_TO_RESEARCH from DataFrames 
        df_iv_final = self.df_iv_final[self.df_iv_final.symbol.str.slice(0,2)==SYMBOL_TO_RESEARCH].copy()
        df_cash_futures = self.df_cash_futures[self.df_cash_futures.symbol.str.slice(0,2)==SYMBOL_TO_RESEARCH].copy()
        
        year = 'all' if year is None else year
        if str(year).lower() != 'all':
            y = int(str(year))
            beg_year = y*100*100+1*100+1
            end_year = y*100*100+12*100+31
            df_iv_final = df_iv_final[(df_iv_final.settle_date>=beg_year) & (df_iv_final.settle_date<=end_year)]
            df_cash_futures = df_cash_futures[(df_cash_futures.settle_date>=beg_year) & (df_cash_futures.settle_date<=end_year)]

        print(f'plot_atm_vs_close year: {year}')
        
        # Step 01: create atm implied vol table, that also has the cash price for each settle_date
        df_atmv = df_iv_final[['settle_date','atm_iv']].drop_duplicates()
        df_cf = df_cash_futures[df_cash_futures.symbol==f'{SYMBOL_TO_RESEARCH}Z99']
        df_atmv = df_atmv.merge(df_cf[['settle_date','close']],how='inner',on='settle_date')

        # Step 02: plot atm_iv vs close
        chart_title = f'{SYMBOL_TO_RESEARCH} atm vol vs close'
        df_atm_vs_close = df_atmv[['settle_date','atm_iv','close']]
        fig_atm_vs_close = pu.plotly_plot(
            df_atm_vs_close,x_column='settle_date',yaxis2_cols=['close'],
            y_left_label='atm_iv',y_right_label='close',plot_title=chart_title,
            legend_x= LEGEND_X,legend_y=LEGEND_Y,number_of_ticks_display=number_of_ticks_display
        )
        return fig_atm_vs_close



        def get_all_years_per_product(prod,df):
            df2 = df.copy()
            df['prod'] = df.symbol.apply(lambda v: v[:(len(v)-3)])
        #     df_this_prod = df_cash_futures[df_cash_futures.symbol.str.slice(0,2)=='CL']
            df_this_prod = df_cash_futures[df_cash_futures.symbol.str.slice(0,2)==prod]
            years = df_this_prod.settle_date.astype(str).str.slice(0,4).astype(int).unique()
            return years.tolist()

    def _chained_years(self,inputs):
        prod = inputs[1]
        if prod is None or len(prod)<1:
            return []
        print(prod)
        yyyys = get_all_years_per_product(prod,self.df_cash_futures)
        choices = [{'label':'all','value':'all'}]  + [{'label':str(yyyy),'value':str(yyyy)} for yyyy in yyyys]
        return  choices



if __name__=='__main__':
    args = sys.argv;
    commod = "CL"
    year = 2020
    if len(args)>1:
        commod = args[1]
    if len(args)>2:
        year = int(args[2])

    sks = IvSkewStatic()

    iplot(sks.plot_atm_vs_close(commod,year=year))
    for d in [.05,.1,.2]:
        fig1,fig2 = sks.plot_skew_vs_atm(commod,dist_from_zero=d,year=year)
        iplot(fig1)
        iplot(fig2)

    
