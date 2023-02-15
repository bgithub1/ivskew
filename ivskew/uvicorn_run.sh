# Run ther fastapi_server via uvicorn.
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# IMPORTANT
# DO NOT RUN AS: bash uvicorn_run.sh
#  RUN using "dot":  . uvicorn_run.sh
# Example: run on port 8556
# . uvicorn_run.sh 8556
# Example: run on port 8556 when the express.js app is running on port 3012
# . uvicorn_run.sh 8556 3012
# Example: run on port 8556 when the express.js app is running on port 3012 using virtual environment ~/Virtualenv/myenv
# . uvicorn_run.sh 8556 3012 ~/Virtualenv/myenv
port=${1}
if [[ -z ${port} ]]
then
	port=8555
fi
originport=${2}
if [[ -z ${originport} ]]
then
	originport=3010
fi

virtualenv_path=${3}
if [[ -z ${virtualenv_path} ]]
then
	virtualenv_path=$(cd ~/Virtualenvs3/risktables;pwd)
fi
source ${virtualenv_path}/bin/activate
python3 fastapi_server.py --port ${port} --originport ${originport} --host "127.0.0.1" --reload