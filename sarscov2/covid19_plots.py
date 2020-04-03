
import pandas as pd
import numpy as np
from bokeh.io import show, output_notebook
from bokeh.models import ColumnDataSource, GeoJSONDataSource, ColorBar, HoverTool, Legend, LogColorMapper, ColorBar
from bokeh.plotting import figure
from bokeh.palettes import brewer
from bokeh.models import CustomJS, Select, MultiSelect, Plot, LinearAxis, Range1d, DatetimeTickFormatter
from bokeh.models.glyphs import Line, MultiLine
from bokeh.palettes import Category10
import geopandas as gpd
import json

import panel as pn
import panel.widgets as pnw
pn.extension()

def get_data():
    df = pd.read_excel('https://www.ecdc.europa.eu/sites/default/files/documents/COVID-19-geographic-disbtribution-worldwide.xlsx')
    df['dateRep'] = pd.to_datetime(df.dateRep, infer_datetime_format=True)
    df = df.sort_values(['countriesAndTerritories','dateRep'])
    #find cumulative cases in each country by using groupby-apply
    df['totalcases'] = df.groupby(['countriesAndTerritories'])['cases'].apply(lambda x: x.cumsum())
    df['totaldeaths'] = df.groupby(['countriesAndTerritories'])['deaths'].apply(lambda x: x.cumsum())
    df['countriesAndTerritories'] = df.countriesAndTerritories.str.replace('_',' ')
    return df

def get_geodata():
    shapefile = 'map_data/ne_110m_admin_0_countries.shp'
    #Read shapefile using Geopandas
    gdf = gpd.read_file(shapefile)[['ADMIN', 'ADM0_A3', 'geometry']]
    #Rename columns.
    gdf.columns = ['country', 'country_code', 'geometry']
    gdf = gdf.drop(gdf.index[159])
    return gdf

def get_geodatasource(gdf):    
    """Get getjsondatasource from geopandas object"""
    json_data = json.dumps(json.loads(gdf.to_json()))
    return GeoJSONDataSource(geojson = json_data)

def bokeh_plot_map(gdf, column=None, title=''):
    """Plot bokeh map from GeoJSONDataSource """
    
    geosource = get_geodatasource(gdf)
    palette = brewer['OrRd'][8]
    palette = palette[::-1]
    vals = gdf[column]
    columns = ['cases','deaths','ratio','popData2018','countriesAndTerritories']
    x = [(i, "@%s" %i) for i in columns]    
    hover = HoverTool(
        tooltips=x, point_policy='follow_mouse')
    #Instantiate LinearColorMapper that linearly maps numbers in a range, into a sequence of colors.
    color_mapper = LogColorMapper(palette = palette, low = vals.min(), high = vals.max())
    tools = ['wheel_zoom,pan,reset',hover]
    p = figure(title = title, plot_height=400 , width=650, toolbar_location='right', tools=tools)
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None
    #Add patch renderer to figure
    p.patches('xs','ys', source=geosource, fill_alpha=1, line_width=0.5, line_color='black',  
              fill_color={'field' :column , 'transform': color_mapper})
    p.toolbar.logo = None
    p.background_fill_color = "#e1e1ea"
    p.sizing_mode = 'stretch_width'
    return p

def bokeh_plot_cases(event):
    """Plot cases per country"""
    
    countries = country_select.value[:10]
    scale = scale_select.value
    value = plot_select.value
    index = 'dateRep'
    axtype = 'datetime'
    colors = Category10[10] + Category10[10]
    items=[]
    if value == 'total vs cases':
        index = 'totalcases'
        value = 'new cases'
        x = df[df.countriesAndTerritories.isin(countries)]
        p = figure(plot_width=600,plot_height=500,
               y_axis_type='log',x_axis_type='log',
               tools=[])
        i=0
        for c,g in x.groupby('countriesAndTerritories'):
            source = ColumnDataSource(g)
            line = Line(x='totalcases',y='cases', line_color=colors[i],line_width=3,line_alpha=.8,name='x')     
            glyph = p.add_glyph(source, line)
            i+=1     
            items.append((c,[glyph]))
    else:
        data = pd.pivot_table(df,index=index,columns='countriesAndTerritories',values=value).reset_index()    
        source = ColumnDataSource(data)        
        i=0   
        p = figure(plot_width=600,plot_height=500,x_axis_type=axtype,
                   y_axis_type=scale,
                   tools=[])        
        for c in countries:
            line = Line(x=index,y=c, line_color=colors[i],line_width=3,line_alpha=.8,name=c)
            glyph = p.add_glyph(source, line)
            i+=1
            items.append((c,[glyph]))
    
    p.xaxis.axis_label = index
    p.yaxis.axis_label = value        
    p.add_layout(Legend(
                location="top_left",
                items=items))    
    p.background_fill_color = "#e1e1ea"
    p.background_fill_alpha = 0.5
    p.legend.location = "top_left"
    p.legend.label_text_font_size = "9pt"
    p.toolbar.logo = None
    p.sizing_mode = 'scale_height'
    plot_pane.object = p
    return 

def summary_plot(event=None):
    
    #countries = list(set(common[:5] + country_select.value[:10]))    
    scale = scale_select.value
    x = summary[:20]
    #x = summary[summary.countriesAndTerritories.isin(countries)]
    hover = HoverTool(tooltips=[
                ('Cases', '@cases'),
                ('Deaths', '@deaths'),
                ('Population','@popData2018')]
            )
    p = figure(plot_width=300,plot_height=500, y_range=list(x.countriesAndTerritories),               
               x_axis_type=scale, title='Total Cases', tools=[hover])
    
    source = ColumnDataSource(summary)
    p.hbar(y='countriesAndTerritories', right='cases', left=0.01, height=0.9, color='orange', source=source)  
    p.xaxis.major_label_orientation = 45
    p.background_fill_color = "#e1e1ea"
    p.toolbar.logo = None
    summary_pane.object = p
    return 
    
def update(event):
    df = get_data()
    return

df = get_data()
summary = df.groupby('countriesAndTerritories').agg({'deaths':np.sum,'cases':np.sum,'popData2018':np.mean}).reset_index().sort_values('cases',ascending=False)
summary['ratio'] = summary.deaths/summary.cases

common=['China','United Kingdom','United States of America','Spain','Italy',
           'Germany','France','Iran','Australia','Ireland','Sweden','Belgium','Turkey','India']

names = list(df.countriesAndTerritories.unique() )
country_select = pnw.MultiSelect(name="Country", value=common[:4], height=140, options=names, width=180)
country_select.param.watch(bokeh_plot_cases, 'value')
scale_select = pnw.Select(name="Scale", value='linear', options=['linear','log'], width=180)
scale_select.param.watch(bokeh_plot_cases, 'value')
plot_select = pnw.Select(name="Plot type", value='cases', options=['cases','totalcases','deaths','totaldeaths','total vs cases'], width=180)
plot_select.param.watch(bokeh_plot_cases, 'value')
#btn = pnw.Button(name='Update',width=180,button_type='primary')
plot_pane = pn.pane.Bokeh()
plot = bokeh_plot_cases(None)
summary_pane = pn.pane.Bokeh()
summary_plot()
scale_select.param.watch(summary_plot, 'value')

gdf = get_geodata()
gdf = gdf.merge(summary, left_on='country', right_on='countriesAndTerritories', how='inner')
mp = bokeh_plot_map(gdf, 'cases')
map_pane = pn.pane.Bokeh(mp,sizing_mode='stretch_width')

title = pn.pane.HTML('<h2>COVID-19 ECDC data</h2><b>https://www.ecdc.europa.eu/</b>')
helptxt = pn.pane.HTML('<p><small>ctrl-click for multiple selections</small></p>')
info = pn.pane.HTML('<a href="http://dmnfarrell.github.io/plotting/ecdc-covid19-dashboard-panel">link to original article</a>')
app = pn.Column(pn.Row(pn.Column(title,country_select,scale_select,plot_select,helptxt),plot_pane,summary_pane,
                       sizing_mode='stretch_height'), map_pane, info)

app.servable(title='COVID-19 ECDC dashboard')
