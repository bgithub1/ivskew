// javascript functions
const VAR_COL_LEN_LIMIT = 100;
const DF_FROM_CSV_ROUTE = '/df_from_csv'
const COLS_CONVERSIONS = {
};

function showDiv(div_id) {
    document.getElementById(div_id).classList.remove("hide");
    document.getElementById(div_id).classList.add("show");
};

function hideDiv(div_id) {
    document.getElementById(div_id).classList.remove("show");
    document.getElementById(div_id).classList.add("hide");
};




function render_bar_plot(
  json_results,
  json_results_key,
  x_col,
  y_col,
  output_div,
  plot_type,
  graph_title,
  y_axis_title,
  marker_color="#7e8ed9",) {
  var df = json_results[json_results_key];
  var x_arr = df.map(row=>row[x_col]);
  var y_arr = df.map(row=>row[y_col]);
  var trace1 = {
      x:x_arr,
      y: y_arr,
      type: plot_type,
      marker:{color:marker_color}
  };

  var data = [trace1];
  var lay_out_yaxis = {
    title: {
      text: y_axis_title,
    }
  };

  var layout = {
      title: graph_title,
      yaxis: lay_out_yaxis,
      // showlegend: false
  };  
  var config = {responsive: true}
  Plotly.newPlot(output_div,data,layout,config);  
}


function display_variable_column_json_results(json_results,json_results_key){
  var cols = Object.keys(json_results[json_results_key][0]);
  // Step 2: Create the NON display column names
  // the line below is like python:
  //    range(1,lim - len(cor_matrix_cols))
  var non_display_cols = Array.from(
    {length:VAR_COL_LEN_LIMIT-cols.length},(v,i)=>'_'+(i+1).toString()
  );
  // Step 3: Create null data in each roww of df_corr, for the NON-display columns
  var df = json_results[json_results_key];
  var df_row_indices = Array.from({length:df.length},(v,i)=>i);
  for (var c of non_display_cols){
    for (var i of df_row_indices){
      df[i][c] = null;
    }
  }
  // Step 4: Concatenate the good columns with the NON-display columns
  cols = cols.concat(non_display_cols);
  // Step 5: store the new df_corr data in the json_results array
  json_results[json_results_key] = df;
  // Step 6: Call display_position
  display_dataframe_json(json_results,json_results_key,cols,json_results_key='df_from_csv');

}

async function upload_csv_to_express_server(csv_text){
  const response = await fetch(DF_FROM_CSV_ROUTE, {
    method: 'POST',
    // method: 'GET',
    headers: {
        // 'Accept': 'application/json',
        'Content-Type': 'application/json',
    },        
    body: JSON.stringify({'data':csv_text})
  })
  if (response.ok) { // if HTTP-status is 200-299
    // get the response body (the method explained below)
    let json = await response.json();
    return json;
  } else {
      alert("HTTP-Error: " + response.status);
      return null;
  }  
};

async function get_local_csv_file() {
  // const content = document.querySelector('#filecontent');
  const [file] = document.querySelector('input[type=file]').files;
  const reader = new FileReader();

  reader.addEventListener("load", () => {
    // this will then display a text file
    // content.innerText = reader.result;
    // change carriage return and line feed to semi-colon
    showDiv('spinner');
    // csv_json = d3.csvParse(reader.result);
    // upload_csv_to_express_server(csv_json)
    var csv_text = reader.result.replaceAll('\n',';');
    csv_text = csv_text.replaceAll('\r',';');
    upload_csv_to_express_server(csv_text)
    .then(function(json_results){
      // console.log(json_results);
      if (json_results!==null){
        display_variable_column_json_results(json_results,'FASTAPI_ROUTE_get_futures_skew');
      } else {
        alert('bad csv file uploaded')
      }
      hideDiv('spinner');
    });  

  }, false);

  if (file) {
    reader.readAsText(file);
  }
};



function convert_cols(col){
  if (col in COLS_CONVERSIONS){
    return COLS_CONVERSIONS[col];
  }
  return col;
}

function convert_df_col_names(row){
  var row_keys = Object.keys(row);
  ret = Object.assign(
    {}, ...row_keys.map(
      (x) => (
        {
          // [cols_conversions[x]]:row[x]
          [convert_cols(x)]:row[x]
        }
      )
    )
  );
  return ret;
}

function convert_df(df){
  // change the keys in each row of df_portolio to a shorter length
  var df_new = df.map(row=>convert_df_col_names(row));
  
  // make all floats only 3 decimal places

  for (var i=0;i<df_new.length;i++){
    var row = df_new[i];
    Object.keys(row).forEach(function(k){
      var row_value = row[k];
      if (typeof(row_value)=='number'){
        new_row_value = Math.round(row_value*1000)/1000;
        df_new[i][k] = new_row_value;
      }
    });
  }
  return df_new;
}


async function display_candlestick_chart(){
  d3.csv('https://raw.githubusercontent.com/plotly/datasets/master/finance-charts-apple.csv', function(err, rows){

  function unpack(rows, key) {
    return rows.map(function(row) {
      return row[key];
    });
  }

  var trace = {
    x: unpack(rows, 'Date'),
    close: unpack(rows, 'AAPL.Close'),
    high: unpack(rows, 'AAPL.High'),
    low: unpack(rows, 'AAPL.Low'),
    open: unpack(rows, 'AAPL.Open'),

    // cutomise colors
    increasing: {line: {color: 'green'}},
    decreasing: {line: {color: 'red'}},

    type: 'candlestick',
    xaxis: 'x',
    yaxis: 'y'
  };

  var data = [trace];

  var layout = {
    title: 'Candlestick Chart',
    dragmode: 'zoom',
    showlegend: false,
    xaxis: {
      title: 'Date',
     range: ['2016-06-01 12:00', '2017-01-01 12:00']
    },
    yaxis: {
      autorange: true,
    }
  };

  Plotly.newPlot('candle_plot', data, layout);
  });

}


function display_dataframe_json(json_results,json_results_key,cols_to_display,tag_id) {
  var df = json_results[json_results_key];
  // convert the keys of that df_portfolio rows to keys that have smaller lengths, like 'symbol' will be 'sym'.
  df = convert_df(df);
  // these are the shorter length keys that we will display in the datatables
  const converted_cols = cols_to_display.map(c=>convert_cols(c));
  // this is the dictionary that you pass to datatable
  var dt_cols = converted_cols.map(function(c){
    return {"data":c,"title":c,"visible":c[0]!=='_'}
  });
  
  // display datatable
  if ( ! $.fn.DataTable.isDataTable("#"+tag_id) ) {
    // // these are the shorter length keys that we will display in the datatables
    // const converted_cols = cols_to_display.map(c=>convert_cols(c));
    // // this is the dictionary that you pass to datatable
    // var dt_cols = converted_cols.map(function(c){
    //   return {"data":c,"title":c}
    // });
    // display the datatable
    $("#"+tag_id).dataTable( {
        "data": df,
        "columns":dt_cols,
        "order": [[0, 'asc']],
        "pageLength": 10,
        "searching": false,
        "lengthChange": false,
        "info":false,
        "scrollX": true,
    } );      
  } else {
    $("#"+tag_id).dataTable( {
        "data": df,
        "columns":dt_cols,
        "order": [[0, 'asc']],
        "pageLength": 10,
        "searching": false,
        "lengthChange": false,
        "info":false,
        "scrollX": true,
        "destroy":true,
    } );      
  }        
};

function display_json_results(json_results) {
  // use display_dataframe_json and render_bar_plot to show json_results
  display_dataframe_json(json_results,'spdr_etfs',['symbol','position'],'spdr_etfs');
  display_dataframe_json(json_results,'spdr_etf_options',['symbol','position'],'spdr_etf_options');
  display_candlestick_chart();
};

async function display_spdr_etf_csvs(){
  const response = await fetch('/get_futures_skew', {
    method: 'GET',
    headers: {
        // 'Accept': 'application/json',
        'Content-Type': 'application/json',
    }        
  });
  if (response.ok) { // if HTTP-status is 200-299
    // get the response body (the method explained below)
    let json = await response.json();
    display_json_results(json);
  } else {
      alert("HTTP-Error: " + response.status);
      return null;
  }  
};

async function get_graphs(){
  var commodity_choice = document.getElementById('commodity_select').value;
  var year_choice = document.getElementById('year_select').value;
  year_choice = Math.floor( year_choice );
  render_skew(commodity=commodity_choice,year=year_choice);
}

async function render_skew(commodity='CL',year=2020){
  const url = `/get_futures_skew?commodity=${commodity}&year=${year}`;
  const response = await fetch(url, {
    method: 'GET',
    headers: {
        // 'Accept': 'application/json',
        'Content-Type': 'application/json',
    }        
  });
  if (response.ok) { // if HTTP-status is 200-299
    // get the response body (the method explained below)
    let json = await response.json();
    var plot_config = {responsive: true}

    // First display the atm_vs_close graph
    atm_vs_close = json['atm_vs_close'];
    avc_data = atm_vs_close['data'];
    avc_layout = atm_vs_close['layout'];
    Plotly.newPlot('atm_vs_close_plot',avc_data,avc_layout,plot_config);  
    
    // Next, display 6 graphs relating to 
    const skew_vs_atm_close_plots = json['skew_vs_atm_close'];
    for (let i=0;i< skew_vs_atm_close_plots.length;i++){

      var skew_vs_atm_close_plot_dict = skew_vs_atm_close_plots[i];
      //skew_vs_atm_iv_plot_0 
      var skew_vs_atm_iv_plot = skew_vs_atm_close_plot_dict['skew_vs_atm_iv'];
      var plot_id = `skew_vs_atm_iv_plot_${i}`; 
      Plotly.newPlot(
        plot_id,
        skew_vs_atm_iv_plot['data'],
        skew_vs_atm_iv_plot['layout'],
        plot_config
        );  
      
      var skew_vs_close_plot = skew_vs_atm_close_plot_dict['skew_vs_close'];
      plot_id = `skew_vs_close_plot_${i}`; 
      Plotly.newPlot(
        plot_id,
        skew_vs_close_plot['data'],
        skew_vs_close_plot['layout'],
        plot_config
        );  
    }
  } else {
      alert("HTTP-Error: " + response.status);
      return null;
  }  
};

function initit(){
  // This is the first thing that's called on page load
  // display stuff
  showDiv('spinner');
  // display_spdr_etf_csvs();
  render_skew()
  hideDiv('spinner');
}

