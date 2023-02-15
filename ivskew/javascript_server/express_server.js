// Express.js application
const express = require('express');
const app = express();
const axios = require('axios');
const path = require('path');

const PORT = 3010;
const FASTAPI_URL = 'http://localhost:8555';
const     FASTAPI_ROUTE_get_futures_skew = '/get_futures_skew';
var FASTAPI_ROUTE_df_from_csv = '/df_from_csv';

app.use(express.static(path.join(__dirname, 'public')));
app.use(express.json({limit: '50mb'}));
app.use(express.urlencoded({limit: '50mb'}));

const axios_base = axios.create({
  baseURL: FASTAPI_URL,
  headers: {
    'Authorization': 'Bearer token'
  }
});


app.get('/',(req,res) => {
  res.sendFile(__dirname + '/index.html');
});



app.get(FASTAPI_ROUTE_get_futures_skew, (req, res) => {
  // assemble a url
  const url = `${FASTAPI_ROUTE_get_futures_skew}?commodity=${req.query.commodity}&year=${req.query.year}`;
  axios_base.get(url)
    // .then(response => response.json())
    .then(response => {
      // console.log(response.data);
      console.log(`success from ${url}`);
      res.json(response.data);
    })
    .catch(error => {
      console.error('Error:', error);
      res.status(500).json({ error: error });
    });
});

app.post(FASTAPI_ROUTE_df_from_csv, (req, res) => {
  r = '{"status":"okfromexpress"}';
  try {    
      console.log(`success from ${FASTAPI_ROUTE_df_from_csv}`);
  } catch (error) {
    console.error(Object.keys(req));
    r = JSON.stringify({"status":error});
  }  
  try {
    axios_base.post(FASTAPI_ROUTE_df_from_csv,{
        headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
        },
        // data: JSON.stringify({'data':req.body.data})
        data: JSON.stringify({'data':req.body.data})
    })
      // .then((response) => response.json())
      .then((response) => {
        console.log('Success:', response.data);
        res.json(response.data);
      })
      .catch((error) => {
        console.error('Error:', error);
      }); 
  } catch (error) {
    console.log(error);
    r = JSON.stringify({"status":error});
  }
});

app.listen(PORT, () => {
  console.log(`Express.js app is listening on port ${PORT}}`);
});


