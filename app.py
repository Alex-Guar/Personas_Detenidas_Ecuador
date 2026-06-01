from ssl import ALERT_DESCRIPTION_UNRECOGNIZED_NAME

from threading import Condition

import types as typ 

from textwrap import indent

from dash import Dash, dcc, html, Input, Output, callback

from pandas._config import display

import plotly.graph_objects as go

import plotly.express as px

import numpy as np

import json

import pandas as pd

import orjson 

from plotly.graph_objs import layout

app = Dash(__name__)

server = app.server #huggingface
d_f_1 = pd.read_parquet('data.parquet')

data_months = d_f_1.fecha_detencion_aprehension.unique()


provincia_selec = None
#year

years = []
for i in d_f_1.fecha_detencion_aprehension.unique():
   
    year = i.year
    if not (year in years):
        years.append(year)
#times
times = {}
for y in years:
    times[y] = []
    for t in d_f_1.fecha_detencion_aprehension:
        if t.year == y and not (t in times[y]):
            times[y].append(t)
for year, month in times.items():
    month.sort() 
    

#month

months = list(enumerate(d_f_1.fecha_detencion_aprehension.unique()))

moths_str = [
        "Enero", "Febrero", "Marzo",
        "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre",
        "Octubre", "Noviembre", "Diciembre"
        ]

marks = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo',
        4: 'Abril', 5: 'Mayo', 6: 'Junio',
        7 : 'Julio',8: 'Agosto',9: 'Septiembre',
        10: 'Octubre',11: 'Noviembre', 12: 'Diciembre'
        } 

app.layout = html.Div([

    #head
    html.Div(
        children=[

           html.Div(
               children = [
                   dcc.Dropdown(
                       id = 'dropdown-year',
                       options = years,
                       value = 2026),

                   dcc.Dropdown(
                       id = 'dropdown-provincia',
                       options = d_f_1.nombre_provincia.unique(),
                       ),

                   dcc.Dropdown(
                       id='dropdown-canton')
                   ]),

           dcc.RadioItems(
               options = [
                   {'label' : 'Pan', 'value' : 'pan'},
                   {'label' : 'Lasso', 'value' : 'lasso'}
                   ],
               id = 'buttom_dragmode',
               inline = True,
               value = 'pan'),

           dcc.Slider(
               id = 'slider-mes',
               value = 1,
               marks= marks,
               )
           ],
        style= {'display' : 'block'}
        ),

#body
    html.Div(
        className = 'Dashbords',
        children = [
            #valores Derecha
            html.Div(
                children=[
                    dcc.Graph(
                        id = 'trace-bar-infraccion',
                        config = {'displayModeBar': True,'displaylogo':False},
                        style = {'height' : '393px'}),
                                    ], 
        style = {'width' : '25%','display' : 'inline-block','verticalAlign': 'top',}
        ),       


   # image central 
    dcc.Graph(
        id="trace-map",
        style = {
            'width' : '50%', 'height' : '400px',
            'display' : 'inline-block','margin' : '0px', 
            'padding' : '0px'
            },
        config = {
            'autosizable':True,'displaylogo':False,
            'modeBarButtonsToRemove' : ["pan2d",'lasso2d','select2d'], 
            'modeBarButtonsToAdd' : ["hoverClosestCartesian"]
            },
        hoverData = {'points':[{}]}
        ),

    #valores izquierda
       
    html.Div(
        children =[
            dcc.Graph(
               id = 'trace-bar-parroquia',
               config = {'displayModeBar': False},
               style = {'height' : '390px'})
            ],
        style = {
            'width' : '25%', 'padding': '0px ',
            'margin' : '0px','display' : 'inline-block',
            'verticalAlign': 'top'
            }
        ),

    #botoom
    html.Div(
        children = [
            dcc.Graph(
                id = 'trace-pie-sex',
                config = {'displayModeBar': False},
                style = {
                    'width':'23%','height' : '175px',
                    'display' : 'inline-block'}
                ),

            dcc.Graph(
                id='trace_histo_age',
                config = {'displayModeBar': False},
               style = {
                   'display': 'inline-block',
                   'width' : '25%','height' : '175px'
                   }
               ),

            dcc.Graph(
                id='trace_bar_medio',
                config = {'displayModeBar': False},
                style = {
                    'display': 'inline-block',
                    'width' : '25%','height' : '175px'
                    }
                ),

            dcc.Graph(
                id = 'trace-bar-nacionalidad',
                config = {'displayModeBar': False},
                style = {
                    'height' : '175px', 'width' : '25%',
                    'display' : 'inline-block'}
                )
            ])
        ])
    ])





@callback(
        Output('slider-mes','max'),
        Output('slider-mes','min'),
        Input('dropdown-year','value')
        )
def calculate_month(year):


    numbers_months = []

    for time in data_months:
        if time.year == year:
            numbers_months.append(time.month)
    
    numbers_months.sort()

    first_mont = numbers_months[0]

    long_month = len(numbers_months)

    end_month = numbers_months[long_month-1]
    return end_month, first_mont

            

@callback(
        Output('dropdown-canton','options'),
        Input('dropdown-provincia', 'value'))
def dropdown_canton(provincia):
    values = d_f_1[d_f_1.nombre_provincia == provincia].nombre_canton.unique()

    return values  

def querys(canton,provincia,month,year):
    
    day = times[year][month-1]
    condition =(d_f_1.fecha_detencion_aprehension == day) 

    if provincia != None:

         condition =  (
                 (d_f_1.fecha_detencion_aprehension == day) &
                 (d_f_1.nombre_provincia == provincia)               
                 )

         if canton  != None:

             condition =  (
                     (d_f_1.fecha_detencion_aprehension ==day) &
                     (d_f_1.nombre_provincia == provincia) &
                     (d_f_1.nombre_canton == canton)
                     )
    return condition  


@callback(
        Output('trace-map','figure'),
        Input('dropdown-year','value'),
        Input('dropdown-provincia','value'),
        Input('dropdown-canton','value'),
        Input('slider-mes','value'),
        Input('buttom_dragmode', 'value'),
        Input('trace-map','relayoutData'),
        )

def map_plot(year,provincia,canton,month,dragmode,relayoutData):
    relayout = relayoutData

    condition = querys(canton,provincia,month,year)
    df = d_f_1[condition]
   
    df_array = df.to_numpy()

    fig_dict = {
            'data':[],
            'layout' : {},
            'frames' : [],
            }

    fig_dict['data']= [{
        'lat': df.latitud.to_numpy(),   # array
        'legendgroup': '',
        'lon': df.longitud.to_numpy(),   #array
        'marker': {'color': '#636efa', 'coloraxis' :"coloraxis3"},
        'hovertext' : df.presunta_infraccion, # Información que aparace al colocar el mouse sobre el un punto
        'mode': 'markers',
        'name': '',
        'customdata' : df_array, 
        'hovertemplate' : 'presenta infracción=%{customdata[1]}<br>edad = %{customdata[4]}',
        'showlegend': False,
        #'subplot': 'map',
        'type': 'scattermap'}
                       ]

    fig_dict['layout']= {
            'legend': {'tracegroupgap': 0},
            'template' : 'plotly_dark',
            'map': {
                'center': {
                    'lat': np.float64(-1.3658860059836733),
                    'lon': np.float64(-78.93841490558367)
                    },
                'domain': {'x': [0.0, 1.0], 'y': [0.0, 1.0]},
                'zoom': 5,
                'style' : 'dark',
                'bounds' : {
                    'east' : np.float64(-74.12),
                    'north' : np.float64(2.00),
                    'south' : np.float64(-5.14),
                    'west'  : np.float64(-93.483)
                    }
                },
            'mapbox': {
                'center': {
                    'lat': np.float64(-1.3658860059836733), 
                    'lon': np.float64(-78.93841490558367)
                    },
                'zoom': 8,
                },
            'margin': {'b': 0, 't':0, 'l':0,'r':0},
            'autosize' : True,
            'dragmode' :dragmode,
            }



    if type(relayout) == typ.NoneType:
        pass 
    else:
        if  "map.center" in relayout:
            fig_dict['layout']["map"]['center'] = relayout["map.center"]

    if type(relayout) == typ.NoneType:
        pass

    else: 
        if "map.zoom" in relayout:
            if type(relayout["map.center"]) == typ.NoneType:
                pass
            else:
                fig_dict['layout']['map']['zoom'] = relayout['map.zoom']

    fig = fig_dict

    #fig_dumps = orjson.dumps(fig)
    
   # fig_dumps_str = fig_dumps.decode('utf-8')

   # fig_loads = orjson.loads(fig_dumps)


    return fig
     

@callback(  
    Output('trace-pie-sex','figure'),
    Input('dropdown-canton','value'),
    Input('dropdown-provincia','value'),
    Input('slider-mes','value'),
    Input('buttom_dragmode','value'), 
    Input('trace-map','selectedData'),
    Input('dropdown-year','value')
        )
def pie_display(canton,provincia,month,dragmode,selectedData,year):
    
    data = []
    
    condition = querys(canton,provincia,month,year)
         
    data_pan = (
            d_f_1[condition]
            .sexo.to_numpy())

    data_pan_array = np.unique(data_pan,return_counts=True)
    if dragmode == 'pan':
        fig_dict_pie = {
                'data' : [],
                'layout' :{},
                'frames' : [],
                }

        def traces_pie(values,labels):
            trace = {
                    'data': [{
                            'type' : 'pie',
                            'name': "Sexo",
                            'values' : values,
                            'labels' : labels
                }]}
            return trace

        fig_dict_pie['layout']= {
                                'legend': {'tracegroupgap': 0},
                                'margin': {'b':0, 't': 45, 'l':0,'r':0},
                                'template' : 'plotly_dark',

                                   'title' : {'text': 'Sexo'}
                                 }

        #Aquí va el slider del mapa no se necesita porque es el mismo para este gráfico
        traces = traces_pie(data_pan_array[1],data_pan_array[0],)
        fig_dict_pie["frames"].append(traces)
        fig_dict_pie["data"] = fig_dict_pie["frames"][0]['data']



    else:


        if type(selectedData) == typ.NoneType :

            fig_dict_pie = {
                            'data' : [],
                            'layout' :{'showlegend' : False,
                                       'margin': {'b' : 25, 'l' : 25 ,'pad': 25 ,'r' :15 ,'t' : 25},
                                       'template' : 'plotly_dark',
                                       'yaxis' : {'visible' : False
                                                  },
                                       'xaxis' : {'visible' : False},
                                       },
                            'frames' : [],
                            }



        else:
            for i in selectedData["points"]:
                gender = i["customdata"][5]
                data.append(gender)
        
            data_np = np.unique(np.array(data),return_counts=True)

            fig_dict_pie = {
                    'data' : [],
                    'layout' :{},
                    'frames' : [],
                    }

            def traces_pie(values,labels,name):
                trace = {'data': [{
                                'type' : 'pie',
                                'name': name,
                                'values' : values,
                                'labels' : labels
                    }]}
                return trace

            fig_dict_pie['layout']= {
                                    'legend': {'tracegroupgap': 0},
                                    'margin': {'b':0, 't': 45, 'l':0,'r':0},
                                    'template' : 'plotly_dark',

                                       'title' : {'text': 'Sexo'}
                                     }

            #Aquí va el slider del mapa no se necesita porque es el mismo para este gráfico
            traces = traces_pie(data_np[1],data_np[0],"pie")
            fig_dict_pie["frames"].append(traces)
            fig_dict_pie["data"] = fig_dict_pie["frames"][0]['data']

    return go.Figure(fig_dict_pie)

@callback(   
    Output('trace_histo_age','figure'),
    Input('dropdown-canton','value'),
    Input('dropdown-provincia','value'),
    Input('slider-mes','value'),
    Input('dropdown-year','value'),
    Input('buttom_dragmode','value'),
    Input('trace-map','selectedData') 
        )
def histogram_display(canton,provincia,month,year,dragmode,selectedData):


    condition = querys(canton,provincia,month,year)

    df = d_f_1[condition].iloc[:,4:6].to_numpy()
   
    

    def assign_age_range(data):
        age_total_15_18 = 0
        age_total_18_35 = 0
        age_total_35_50 = 0
        age_total_50_64 = 0
        age_total_64 = 0 

        for i in data:
            ty = str(i)
            if ty != 'SIN_DATO':
                age_int = int(ty) 
                if (age_int >= 15) and (age_int<18):
                    age_total_15_18 += 1
                if (age_int >=18)  and (age_int<35):
                    age_total_18_35 += 1
                if (age_int >= 35) and (age_int<50):
                    age_total_35_50 += 1
                if (age_int >= 50) and (age_int < 64):
                    age_total_50_64 += 1
                if (age_int >= 64):
                    age_total_64 += 1
            else:
                pass
        total = {'15-18':age_total_15_18,
                '18-35' : age_total_18_35,
                 '35-50' : age_total_35_50,
                 '50-64' : age_total_50_64,
                 '64+' : age_total_64
                 } 
        return total


    def traces_histogram(values_female,values_male):

        fig_dict = {
                'data' : [],
                'layout' :{},
                }

        fig_dict['data'] = [
                        {
                        'type' : 'histogram',
                        'name': "Hombre",
                        'y' : list(values_male.values()),
                        'x' : list(values_male),
                        'showlegend' : True,
                        'offsetgroup': 'Female',
                        'xaxis': 'x',
                        'yaxis': 'y',
                        'bingroup': 'x',
                        'histfunc' : 'max'
                        },
                        {
                        'type' : 'histogram',
                        'name': "Mujer",
                        'y' : list(values_female.values()),
                        'x' : list(values_female),
                        'showlegend' : True,
                        'offsetgroup': 'Male',
                        'xaxis': 'x',
                        'yaxis': 'y',
                        'bingroup': 'x',
                        'histfunc' : 'max'

                          }
                          ]
        fig_dict['layout']= {
                                'legend': {'tracegroupgap': 0},
                                'xaxis' : {'categoryarray':list(data_men.values()),
                                           'showgrid' : False
                                           },
                                'yaxis' : {'showgrid' : False},
                                'barmode': 'stack',
                                'margin': {'b': 0, 't': 42, 'l':0,'r':0},
                                'template' : 'plotly_dark',
                                'title' : {'text': 'Edad'}
                                

                               # 'template': 'plotly_dark',
                                 }
        return fig_dict



    if dragmode == "pan":


        condition_1 = df== "HOMBRE"
        condition_2 = df== 'MUJER'
        age_sex_men = df[condition_1[:,1]]
        age_sex_women = df[condition_2[:,1]]
        age_men = age_sex_men[:,0]
        age_women = age_sex_women[:,0]

        # se remplazo la función
        data_men = assign_age_range(age_men)
        data_wom = assign_age_range(age_women)
        #Aquí va el slider del mapa no se necesita porque es el mismo para este gráfico

        fig_dict = traces_histogram(data_wom,data_men)

    
    else:



        data = []
        if type(selectedData) == typ.NoneType :
             fig_dict = {
                    'data' : [],
                    'layout' :{'showlegend' : False,
                                       'margin': {'b' : 0, 'l' : 0 ,'pad': 0 ,'r' :0 ,'t' : 0},
                                       'template' : 'plotly_dark',
                                       'yaxis' : {'visible' : False
                                                  },
                                       'xaxis' : {'visible' : False}
                                       },
                    }


        else:
            for i in selectedData["points"]:
                age = i["customdata"][4:6]
                data.append(age)

            data_np = np.array(data)

            if not (data_np.ndim == 1):

                condition_1 = data_np== "HOMBRE"
                condition_2 = data_np == 'MUJER'
                age_sex_men = data_np[condition_1[:,1]]
                age_sex_women = data_np[condition_2[:,1]]
                age_men = age_sex_men[:,0]
                age_women = age_sex_women[:,0]
               
                # se remplazo la función
                data_men = assign_age_range(age_men)
                data_wom = assign_age_range(age_women)
                

                fig_dict = traces_histogram(data_wom,data_men)
            else:
                fig_dict = {
                        'data' : [],
                        'layout' : {'template' : 'plotly_dark'}
                        }
    return go.Figure(fig_dict)




@callback(
        Output('trace_bar_medio','figure'),
        Input('buttom_dragmode','value'),
        Input('dropdown-canton','value'),
        Input('dropdown-provincia','value'),
        Input('slider-mes','value'),
        Input('dropdown-year','value'),
        Input('trace-map','selectedData')
        )
def trace_bar(dragmode,canton,provincia,month,year,selectedData):
    

    def clean_data(records):
        '''Determine values true''' 
        
        results = [] 
        for i_medio in records:
                medio = i_medio
                if (str(medio) != 'NO_APLICA') and (str(medio) != 'SE_DESCONOCE'):

                    results.append(medio)

        results_array = np.array(results)
            
        category_value = np.unique(results_array,return_counts=True)
           
   #    The category is 0 and values 1 
        return category_value

    condition =  querys(canton,provincia,month,year)

    events_pan = d_f_1[condition].movilizacion.to_numpy()
        

    if dragmode == 'pan':

        outcomes_pan = clean_data(events_pan)    
        
        outcomes_pan_categorys = outcomes_pan[0]

        outcomes_pan_values = outcomes_pan[1]

        fig_dict = {
                'data' : [],
                'layout' : {},
                }

        fig_dict['data'] = [{'type' : 'bar',
                             'x' : outcomes_pan_categorys,
                             'y' : outcomes_pan_values,
                             }]
        fig_dict['layout']= {
                            'template': 'plotly_dark',
                            'xaxis' : {'showgrid' : False},
                            'yaxis' : {'showgrid' : False},
                            'margin': {'b': 0, 't': 42, 'l':0,'r':0},
                            'title' : {'text' :'Medio de Movilización' },
                            }

    else:

        if type(selectedData) == typ.NoneType:

            fig_dict = {
                    'data' : [],
                    'layout' :{'showlegend' : False,
                                       'margin': {'b' : 0, 'l' : 0 ,'pad': 0 ,'r' :0 ,'t' : 0},
                                        'template' : 'plotly_dark',
                                       'yaxis' : {'visible' : False
                                                  },
                                       'xaxis' : {'visible' : False}
                                       }
                    }
        else: 
            
            result = []
            for event in selectedData["points"]:
                medio = event['customdata'][11]
                result.append(medio)

            result_array = np.array(result)

            category_and_values = np.unique(result_array,return_counts=True)

            

            category = category_and_values[0]

            values = category_and_values[1]


            fig_dict = {
                    'data' : [],
                    'layout' : {},
                    }

            fig_dict['data'] = [{'type' : 'bar',
                                 'x' : category,
                                 'y' : values}
                                ]

            fig_dict['layout']= {
                            'template': 'plotly_dark',
                            'xaxis' : {'showgrid' : False},
                            'yaxis' : {'showgrid' : False},
                            'margin': {'b': 0, 't': 42, 'l':0,'r':0},
                            'title' : {'text' :'Medio de Movilización' },
                    }

            

    return go.Figure(fig_dict)

@callback(
        Output("trace-bar-nacionalidad",'figure'),
        Input('buttom_dragmode','value'),
        Input('dropdown-canton','value'),
        Input('dropdown-provincia','value'),
        Input('slider-mes','value'),
        Input('dropdown-year','value'),
        Input('trace-map','selectedData')
        )
def trace_bar_nacionalidad(dragmode,canton,provincia,month,year,selectedData):
    
    condition = querys(canton,provincia,month,year)

    events_pan = d_f_1[condition].nacionalidad.to_numpy()

    
    def clean_data_nacionalidad(records):
        
        result = []

        for event in records:

            if event != 'SE_DESCONOCE':
             
                result.append(event)
        
        result_array = np.array(result)

        category_and_values = np.unique(result_array,return_counts=True)

        return category_and_values

    def trace_nacionalidad(categorys,values):
        fig_dict = {
                'data' : [],
                'layout' : {}
                }
        
        fig_dict['data'] = [{
            'type' : 'bar',
            'x' : categorys,
            'y' : values,
            'orientation' : 'v',
            }]

        fig_dict['layout']  = {
            'template': 'plotly_dark',

            'margin': {'b': 0, 't': 42, 'l':0,'r':0},
            'xaxis' : {'showgrid':False},
            'yaxis' : {'showgrid' : False},
            'title' : {'text' : 'Nacionalidad' }
                }
        return fig_dict


            


    if dragmode == 'pan' :

        outcomes = clean_data_nacionalidad(events_pan)

        outcomes_pan_categorys = outcomes[0]

        outcomes_pan_values = outcomes[1]

        fig_dict = trace_nacionalidad(outcomes_pan_categorys,outcomes_pan_values)


    else:     

        if type(selectedData) == typ.NoneType:
            fig_dict = {
                    'data' : [],

                    'layout' :{'showlegend' : False,
                                 #      'margin': {'b' : 32, 'l' : 32 ,'pad': 32 ,'r' :32 ,'t' : 32},
                                       'template' : 'plotly_dark',
                                       'yaxis' : {'visible' : False
                                                  },
                                       'xaxis' : {'visible' : False}
                                       }
                    }
        else: 
            data = []
            for i in selectedData["points"]:
                nacionalidad = i['customdata'][7]
                if str(nacionalidad) != 'SE_DESCONOCE':
                    data.append(nacionalidad)

            data_array = np.array(data)

            category_and_values = np.unique(data_array,return_counts=True)

            categorys = category_and_values[0]

            values  = category_and_values[1]

            fig_dict = trace_nacionalidad(categorys,values)

    return go.Figure(fig_dict)


@callback(
        Output('trace-bar-infraccion','figure'),
        Input('buttom_dragmode','value'),
        Input('dropdown-canton','value'),
        Input('dropdown-provincia','value'),
        Input('slider-mes','value'),
        Input('dropdown-year','value'),
        Input('trace-map','selectedData')
        )
def trace_bar_infraccion(dragmode,canton,provincia,month,year,selectedData):


    condition = querys(canton,provincia,month,year)

    events_pan = d_f_1[condition].presunta_infraccion.to_numpy()


    def clean_data_infraccion(records):
        
        result = []

        for event in records:
             
            result.append(event)
        
        result_array = np.array(result)

        category_and_values = np.unique(result_array,return_counts=True)

        return category_and_values

    def trace_infraccion(values,category,font_size):

        fig_dict = {
                'data' : [],
                'layout' : {},
                }

        fig_dict['data'] = [{
            'type' : 'bar',
            'x' : values,
            'y' : category,
            'orientation' : 'h',
            'textposition' : "outside",
            'textfont' : {'size' : font_size},
            'text' : category,
            'hoverinfo' : "x",
            }]

        fig_dict['layout'] = {
                'template' : 'plotly_dark',
                'margin': {'b': 12, 't': 42, 'l':0,'r':0},
                'xaxis' : {'showgrid':False},
                'yaxis' : {'showgrid' : False,
                           'showticklabels' : False,
                           'ticksuffix' : "",
                           },
                'title' : {'text' : 'Presunta Infracción'},
                'dragmode' : "pan",
                'modebar':dict(remove = ["lasso2d","select","zoom2d"], orientation = 'v'),
                'autosize' : True
                    }

        return fig_dict

    
    def text_size_font(length_values):
        '''It Define the size of title of bar text'''
        if length_values > 12:
            size = 112211
        else:
            size = 12

        return size


    if dragmode == 'pan':

        outcomes = clean_data_infraccion(events_pan)

        outcomes_pan_categorys = outcomes[0]

        outcomes_pan_values = outcomes[1]

        fig_dict = trace_infraccion(outcomes_pan_values,outcomes_pan_categorys,text_size_font(outcomes_pan_categorys.size))
          

    else:

        if type(selectedData) ==  typ.NoneType:

            fig_dict = {
                        'data' : [],

                        'layout' :{'showlegend' : False,
                                       'margin': {'b' : 0, 'l' : 0 ,'pad': 0 ,'r' :0 ,'t' : 0},
                                       'template' : 'plotly_dark',
                                       'yaxis' : {'visible' : False
                                                  },
                                       'xaxis' : {'visible' : False}
                                       }
                        }
        else: 
            
            result = []
            for event in selectedData["points"]:
                nacionalidad = event['customdata'][32]
                result.append(nacionalidad)

            result_array = np.array(result)

            category_and_values = np.unique(result_array,return_counts=True)

            

            category = category_and_values[0]

            values = category_and_values[1]

            fig_dict = trace_infraccion(values,category,text_size_font(category.size))
    return go.Figure(fig_dict)




@callback(
        Output('trace-bar-parroquia','figure'),
        Input('buttom_dragmode','value'),
        Input('dropdown-canton','value'),
        Input('dropdown-provincia','value'),
        Input('slider-mes','value'),
        Input('dropdown-year','value'),
        Input('trace-map','selectedData')
        )
def trace_bar_parroquia(dragmode,canton,provincia,month,year,selectedData):
    

    condition = querys(canton,provincia,month,year)

    events_pan = d_f_1[condition].nombre_parroquia.to_numpy()

    if canton != None:

        title = "Parroquias"
        events_pan = d_f_1[condition].nombre_parroquia.to_numpy()
    else:
        title = "Cantones"

        events_pan = d_f_1[condition].nombre_canton.to_numpy()

    def clean_data_parroquia(records):
        
        result = []

        for event in records:
             
            result.append(event)
        
        result_array = np.array(result)

        category_and_values = np.unique(result_array,return_counts=True)

        return category_and_values
       
    if dragmode == 'pan':

        outcomes = clean_data_parroquia(events_pan)

        outcomes_pan_categorys = outcomes[0]

        outcomes_pan_values = outcomes[1]


        fig_dict = {
                'data' : [],
                'layout' : {},
                }

        fig_dict['data'] = [{
            'type' : 'bar',
            'x' : outcomes_pan_values,
            'y' : outcomes_pan_categorys,
            'orientation' : 'h',
            }]

        fig_dict['layout'] = {
                'template' : 'plotly_dark',
                'xaxis' : {'showgrid':False},
                'yaxis' : {'showgrid' : False},
                'margin': {'b': 0, 't': 42, 'l':0,'r':0},
                'title' : {'text': title},
                }




    else:

        if type(selectedData) == typ.NoneType:

            fig_dict = {
                    'data' : [],

                    'layout' :{'showlegend' : False,
                                   'margin': {'b' : 0, 'l' : 0 ,'pad': 0 ,'r' :0 ,'t' : 0},
                                   'template' : 'plotly_dark',
                                   'yaxis' : {'visible' : False
                                              },
                                   'xaxis' : {'visible' : False}
                                   }
                    }
        else:

            result = []
            for event in selectedData["points"]:
                nacionalidad = event['customdata'][31]
                result.append(nacionalidad)

            result_array = np.array(result)

            category_and_values = np.unique(result_array,return_counts=True)

            outcomes_lasso_categorys = category_and_values[0]

            outcomes_lasso_values = category_and_values[1]

   
            

            fig_dict = {
                    'data' : [],
                    'layout' : {},
                    }

            fig_dict['data'] = [{
                'type' : 'bar',
                'x' : outcomes_lasso_values,
                'y' : outcomes_lasso_categorys,
                'orientation' : 'h',
                }]

            fig_dict['layout'] = {
                    'template' : 'plotly_dark',
                    'xaxis' : {'showgrid':False},
                    'yaxis' : {'showgrid' : False},
                    'margin': {'b': 0, 't': 42, 'l':0,'r':0},
                    'title' : {'text': 'Parroquias'},
                    }

    return go.Figure(fig_dict)


if __name__ == '__main__':
    app.run_server(debug=False, host='0.0.0.0', port=7860)
    
#    app.run(debug=True)
