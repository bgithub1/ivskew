import pandas as pd
import datetime
import pdb
from fastapi import Depends, FastAPI
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from pydantic import BaseModel

from fastapi.responses import FileResponse
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import io
import uvicorn

import pytz
from IPython import display
import argparse
import json
import futures_skew as fskew

# The GlobalVariables class allows you to populate global variables from the __main__
#  Below, I define a redis_port variable that I might want to use later in one of the 
#  FastAPI routes.  For now it is unused.

app = FastAPI()

YOUR_DOMAIN = 'yourdomain.com'

# list valid cross-origin origins
origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    f"http://www.{YOUR_DOMAIN}",
    f"http://{YOUR_DOMAIN}",
    f"https://www.{YOUR_DOMAIN}",
    f"https://{YOUR_DOMAIN}",
    "http://localhost",
    "http://localhost:3010",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GlobalVariables:
    pass
__m = GlobalVariables()  # m will contain all module-level values
__m.redis_port = None  # database name global in module
__m.origins = origins


@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI Tables Server"}

@app.get("/get_futures_skew")
async def get_futures_skew(commodity:str='CL',year:int=2020):
    return_dict = {}
    sks = fskew.IvSkewStatic()
    y = int(str(year))
    fig0 = sks.plot_atm_vs_close(commodity,year=y).to_dict()
    return_dict['atm_vs_close'] = fig0
    atm_vs_skew = []
    for d in [.05,.1,.2]:
        fig1,fig2 = sks.plot_skew_vs_atm(commodity,dist_from_zero=d,year=y)
        fig1 = fig1.to_dict()
        fig2 = fig2.to_dict()
        atm_vs_skew.append({'skew_vs_atm_iv':fig1,'skew_vs_close':fig2})
    return_dict['skew_vs_atm_close'] = atm_vs_skew    
    return return_dict


class CsvData(BaseModel):
    data: str

def transform_df(df:pd.DataFrame):
    # do something with DataFrame
    return df

@app.post("/df_from_csv")
async def df_from_csv_text(csv_text: CsvData):
    # This route is an http post route, that accepts a text string of 
    #   csv data.  Each csv line is separated by a ";".  The csv data on 
    #   each line is separated by a ",".
    # The route parses the input csv_text, and returns a json version
    #   of a DataFrame from that text.
    csv_text = csv_text.data
    print(type(csv_text))
    print(csv_text)
    list_data = csv_text.split(';')
    list_data = [
        v.split(',')
        for v in list_data
        if len(v)>0
    ]
    cols = list_data[0]
    dict_data = [
        {cols[i]:v[i] for i in range(len(cols))}
        for v in list_data[1:]
        if len(v)==len(cols)
    ]
    df = pd.DataFrame(dict_data)
    df = transform_df(df)
    return_dict = df.to_dict(orient='records')
    return {'csv_data_from_df':return_dict}



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
            prog = 'risk_server',
            description = 'A FastAPI restAPI',
            )
    hour = datetime.datetime.now().hour
    parser.add_argument('--host',default='127.0.0.1',type=str,help="uvicorn http host") 
    parser.add_argument('--port',default=8555,type=int,help="uvicorn http port") 
    parser.add_argument('--originport',default=3010,type=int,help="express origin http port") 
    parser.add_argument('--reload',
        help="Tell uvicorn to automatically reload server if source code changes",
        action='store_true'
    ) 
    parser.add_argument('--log_level',default='info',type=str,
            help="the logger's log level")
    parser.add_argument('--redis_port',default=None,type=int,
        help="Redis port, if you are going to use Redis fetch data") 
    args = parser.parse_args()  
    print(args)
    __m.redis_port = args.redis_port
    __m.origins.append(f"http://localhost:{args.originport}")

    uvicorn.run(
        "fastapi_server:app", 
        host=args.host, 
        port=args.port, 
        reload=args.reload, 
        log_level=args.log_level
    )