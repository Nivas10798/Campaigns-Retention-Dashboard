# importing libraries
from dash import Dash, dcc, html, dash_table
from flask import Flask
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from datetime import datetime

from plotly.subplots import make_subplots
import plotly.express as px
import plotly.graph_objects as go

import pandas as pd
from sqlite3 import dbapi2 as sq3

# tab title
html.Title('Campaigns Retention Metrics Dashboard')

application = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP])

month = {'1':'January', '2':'February', '3':'March', '4':'April',
         '5':'May', '6':'June', '7':'July', '8':'August', '9':'September',
         '10':'October', '11':'November', '0':'December'}

#collecting data
final_df = pd.read_csv('monthwise_filtered_data.csv')

campaign_list = list(final_df.campaign.unique())
year_list = sorted(list(final_df.cohort.unique()))
wikidb_list = list(final_df.wiki_db.unique())

# application layout
application.layout = dbc.Container([
    html.Br(),
    html.H1('Campaigns Retention Metrics Dashboard'),
    html.P('The dashboard provides number of users who have retained after the end of a photo campaign'),
    html.Br(),
    html.H4('Editors who are active in a given time interval after the end of campaign'),
    dbc.Row([
        dbc.Col([html.P('Campaign Name'),
                 dcc.Dropdown(id = 'campaign',
                              options = [{'label': c, 'value': c}
                                         for c in campaign_list], value='WLM')
                ]),
        dbc.Col([html.P('Campaign Year'),
                 dcc.Dropdown(id = 'year',
                              options = [])
                ]),
        dbc.Col([html.P('Interval after end of campaign'),
                 dcc.Dropdown(id = 'interval',
                              options = [{'label':'3 months', 'value':4}, {'label':'6 months', 'value':7}, {'label':'9 months', 'value':10},
                                         {'label':'1 year', 'value':13}, {'label':'2 years', 'value':25}, {'label':'3 years', 'value':37}
                                         ], value=10)
                 ]),
        dbc.Col([html.P('Wiki Database'),
                 dcc.Dropdown(id = 'wiki_db',
                              options = [])
                ]),
    ]),
    html.Div(children=[dcc.Graph(id ='bar_fig')], style = {'width': '100%','marginLeft': 10, 'marginRight': 10, 'marginTop': 10, 'marginBottom': 0,
           'backgroundColor':'#F7FBFE', 'border': 'thin lightgrey dashed', 'padding': '6px 6px 6px 6px'},),
    html.Br(),
    html.Br(),
    html.H4('Count of new editors who contributed to country specific categories'),
    html.Div(children=[dcc.Graph(id ='map_fig')], style = {'width': '100%','marginLeft': 10, 'marginRight': 10, 'marginTop': 10, 'marginBottom': 0,
           'backgroundColor':'#F7FBFE', 'border': 'thin lightgrey dashed', 'padding': '6px 6px 6px 6px'},),
    html.Br(),
    html.Br(),
    html.H4('Wiki Projects and number of new editors contributing in a selected month'),
    dbc.Row([
        dbc.Col([html.P('Select a Month and Year'),
                 dcc.Dropdown(id = 'month_year',
                              options = [], style={'width': "70%"}), 
                ]),
    ]),
    dbc.Row([
        dbc.Col([html.Div(children=[dcc.Graph(id ='table_fig')])]),
        dbc.Col([html.Div(children=[dcc.Graph(id ='pie_fig')])])
    ]),
    
])

# callback for year
@application.callback(
    [Output('year', 'options'),
    Output('year', 'value')],
    Input('campaign', 'value'))
def get_year(camp):
    campaign_year = final_df[final_df['campaign'] == camp]
    res_year = [{'label': i, 'value': i} for i in sorted(list(campaign_year.cohort.unique()))]
    value_year = res_year[0]["value"]
    return res_year, value_year

# callback for interval
@application.callback(
    Output("interval", "value"),
    Input("interval", "otpions"))
def get_interval(interval):
    return [k['value'] for k in interval]

# callback for wiki_db
@application.callback(
    Output('wiki_db', 'options'),
    Input('year', 'value'),
    Input('campaign','value'))
def get_wikidb(year, camp):
    year_wikidb = final_df[(final_df['cohort'] == year) & (final_df['campaign'] == camp)]
    return [{'label': i, 'value': i} for i in list(year_wikidb.wiki_db.unique())]

# callback for month_year
@application.callback(
    Output('month_year', 'options'),
    Output('month_year', 'value'),
    Input('year', 'value'),
    Input('campaign','value'))
def get_monthyear(year, camp):
    monthyear_df = final_df[(final_df['cohort'] == year) & (final_df['campaign'] == camp)]
    res_monthyear = [{'label': i, 'value': i} for i in list(monthyear_df.event_month_year.unique())]
    value_monthyear = res_monthyear[0]["value"]
    return res_monthyear, value_monthyear

# bubblemap function callback
@application.callback(
    Output("map_fig", "figure"), 
    [Input("campaign", "value"),
    Input("year", "value")])
def update_bubble_map(campaign, year):
    dropdown_df = final_df[(final_df['campaign']==campaign) & (final_df['cohort']==year)]
    dropdown_df1 = dropdown_df.groupby(['user_name', 'event_month_number', 'event_month_year', 'country', 'campaign', 'cohort', 'wiki_db', 'iso_code']).size().reset_index(name='edit_count')
    dropdown_df1 = dropdown_df1.sort_values(by=['event_month_number', 'event_month_year', 'country', 'campaign', 'cohort', 'wiki_db'])
    editors_count_df = dropdown_df1.groupby(['country', 'campaign', 'cohort', 'iso_code']).size().reset_index(name='editors_count')
    map_fig = px.scatter_geo(editors_count_df, locations="iso_code", color="country", hover_data=["editors_count"],
                           size="editors_count", projection="orthographic")
    map_fig.update_geos(projection_type="orthographic", landcolor="white", oceancolor="MidnightBlue", showocean=True, lakecolor="LightBlue")
    map_fig.update_layout(height=600, title_text = f"Number of new editors who participated by contributing to the highlighted country category in {campaign}, {year}", title_x=0.5)
    map_fig.update_traces(marker=dict(color="crimson", size=10,line=dict(width=2, color='DarkSlateGrey')), selector=dict(mode='markers'))
    return map_fig

# table and pie chart function callback
@application.callback(
    [Output("table_fig", "figure"),
    Output("pie_fig", "figure")],
    [Input("campaign", "value"),
    Input("year", "value"),
    Input("month_year","value")])
def update_table(campaign, year, month_year):
    dropdown_df = final_df[(final_df['campaign']==campaign) & (final_df['cohort']==year)]
    dropdown_df1 = dropdown_df.groupby(['user_name', 'event_month_number', 'event_month_year', 'country', 'campaign', 'cohort', 'wiki_db', 'iso_code']).size().reset_index(name='edit_count')
    dropdown_df1 = dropdown_df1.sort_values(by=['event_month_number', 'event_month_year', 'country', 'campaign', 'cohort', 'wiki_db'])
    drop_df = pd.DataFrame(dropdown_df1.groupby(['event_month_number', 'wiki_db']).size().reset_index(name='editors_count'))
    month_map_dict = dict(zip(dropdown_df1.event_month_number, dropdown_df1.event_month_year))
    drop_df['event_month_year'] = drop_df['event_month_number'].map(month_map_dict)
    new_df = drop_df[drop_df['event_month_year']==month_year].sort_values(by='editors_count', ascending=False)[['wiki_db', 'editors_count']]
    new_df['%_editors_in_current_month'] = (new_df['editors_count']/new_df['editors_count'].sum())*100
    new_df['%_editors_in_current_month'] = new_df['%_editors_in_current_month'].apply(lambda x:round(x,2))
    new_df.reset_index(inplace=True, drop=True)

    table_fig = go.Figure(data=[go.Table(columnwidth = [25,33,72],
        header=dict(values=list(new_df[:10].columns), align='left', fill_color='paleturquoise', font=dict(size=14)),
        cells=dict(values=[new_df[:10][col] for col in new_df[:10].columns], align='left', height=27.5,  fill_color='mintcream', font=dict(size=14)))
    ])
    table_fig.update_layout(title={'text':f'New users from {campaign} {year} who contributed <br>to various wiki projects (upto 10) in {month_year}','x':0.5,}, height=500, font=dict(size=12))

    pie_fig = px.pie(new_df, values='%_editors_in_current_month', names='wiki_db', title='Pie chart to show the overall editors on possible Wiki projects')
    pie_fig.update_layout(height=500)
    return [table_fig, pie_fig]    

# bargraph function callback
@application.callback(
    Output("bar_fig", "figure"),
    [Input("campaign", "value"),
    Input("year", "value"),
    Input("interval", "value"),
    Input("wiki_db", "value")])
def update_bar_chart(campaign, year, interval, wiki_db):
    dropdown_df = final_df[(final_df['campaign']==campaign) & (final_df['cohort']==year)]
    dropdown_df1 = dropdown_df.groupby(['user_name', 'event_month_number', 'event_month_year', 'country', 'campaign', 'cohort', 'wiki_db', 'iso_code']).size().reset_index(name='edit_count')
    dropdown_df1 = dropdown_df1.sort_values(by=['event_month_number', 'event_month_year', 'country', 'campaign', 'cohort', 'wiki_db'])
    
    if wiki_db != None:
        dropdown_df2 = dropdown_df1[dropdown_df1['wiki_db']==wiki_db]
        drop_df = pd.DataFrame(dropdown_df2.groupby(['event_month_number', 'wiki_db']).size().reset_index(name='editors_count'))
    else:
        drop_df = pd.DataFrame(dropdown_df1.groupby(['event_month_number']).size().reset_index(name='editors_count'))

    month_map_dict = dict(zip(dropdown_df1.event_month_number, dropdown_df1.event_month_year))
    drop_df['event_month_year'] = drop_df['event_month_number'].map(month_map_dict)
    x_list = []
    y_list = []
    year_check = year
    index = 0
    i_mon = str(int(dropdown_df1['event_month_number'].iloc[0].split('-')[1]))
    i_year = dropdown_df1['event_month_number'].iloc[0].split('-')[0]
    try:
        while len(x_list) <= interval-1 and index < len(drop_df):
            if int(i_mon) == 1:
                i_year = str(int(i_year)+1)
                year_check = drop_df['event_month_year'][index].split('-')[1]
            if month[str(int(i_mon))] == drop_df['event_month_year'][index].split('-')[0] and int(i_year) == int(year_check):
                x_list.append(drop_df['event_month_year'][index])
                y_list.append(drop_df['editors_count'][index])
                index = index+1
            else:
                x_list.append(month[str(int(i_mon))]+'-'+i_year)
                y_list.append(0)
            i_mon = str((int(i_mon)+1)%12)

    except:
        pass

    bar_fig = px.bar(x=x_list, y=y_list, color=y_list)
    bar_fig.update_traces(hovertemplate="<br>".join(["Month & Year: %{x}","Number of editors: %{y}",]))
    bar_fig.update_layout(title_text = f"New editors who are active for {interval-1} months after the end of {campaign}, {year}", title_x=0.5,
                            yaxis=dict(range=[0, max(y_list)+10], title_text="Editors count",
                                     tickmode="array", titlefont=dict(size=12),),
                            xaxis=dict(range=[0, max(x_list)], title_text="Timeline", 
                                     tickmode="array", titlefont=dict(size=12),),
                            margin=dict(l=20, r=20, b=0, t=100, ),)
    return bar_fig

# running the app
if __name__ == '__main__':
    application.run()

app = application.server
