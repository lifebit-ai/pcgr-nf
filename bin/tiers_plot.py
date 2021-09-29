#!/usr/bin/env python

import os
import sys
import json
import shutil
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.offline import plot

TIERS = {'Tier 1': 'Variants of<br>strong<br>clinical<br>significance',
        'Tier 2': 'Variants of<br>potential<br>clinical<br>significance',
        'Tier 3': 'Variants of<br>uncertain<br>clinical<br>significance',
        'Tier 4': 'Other<br>coding<br>mutation',
        'Noncoding': 'Noncoding<br>mutation'}

COLOURS = ['', '#028ddf', '#1faafc', '#57bffc', '#8fd4fd', '#c7e9fe' ]

def __main__():

    combined = sys.argv[1]

    print("Input combined tiers file: ", combined)
    
    reader = pd.read_csv(combined, sep='\t', header=0, chunksize=1000, usecols=['TIER', 'GENOMIC_CHANGE'])

    chunk_arr = []
    for df in reader:
        chunk_arr.append(df)
    df = pd.concat(chunk_arr, axis=0)

    # remove duplicated variants
    df = df.drop_duplicates()

    counts = {}
    tiers = df['TIER'].value_counts()
    for key in TIERS.keys():
        if key.upper() not in tiers:
            counts[key] = 0
        else:
            counts[key] = tiers[key.upper()]
            
    fig=make_subplots(rows=1, cols=5, shared_yaxes=True, shared_xaxes=True)
    col = 1
    for tier in TIERS.keys():
        fig.add_trace(go.Scatter(x=[-1,2],y=[1,1],fill='tozeroy', fillcolor=COLOURS[col], showlegend=False),col=col, row=1)
        fig.add_trace(go.Scatter(x=[0.5, 0.5, 0.5],y=[0.7, 0.5, 0.3], text=["<b>{}</b>".format(tier),counts[tier], TIERS[tier]], mode="text", showlegend=False),col=col, row=1)
        col += 1 
    fig.update_layout(plot_bgcolor='rgb(255,255,255)')
    fig.update_xaxes(showline=False, range=[0, 1], showticklabels=False)
    fig.update_yaxes(showline=False, range=[0.2, 0.8], showticklabels=False)
    fig.write_image("tiers.png")

if __name__=="__main__": __main__()
