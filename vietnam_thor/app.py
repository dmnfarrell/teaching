"""
    Web app with Panel for THOR data.
    Created May 2021
    Copyright (C) Damien Farrell

    This program is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License
    as published by the Free Software Foundation; either version 2
    of the License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""

import os, io, random
import string
import numpy as np
import pandas as pd
import pylab as plt
import seaborn as sns
from collections import OrderedDict
import datetime as dt
import geopandas as gpd

from bokeh.layouts import column
from bokeh.models import ColumnDataSource, Slider, CustomJS, DatePicker
from bokeh.plotting import figure
from bokeh.themes import Theme
from bokeh.io import show, output_notebook
from bokeh.models import (DataTable, GeoJSONDataSource, ColumnDataSource, HoverTool, renderers,
                          Label, LabelSet, CustomJS, MultiSelect, Dropdown, Div)
from bokeh.tile_providers import CARTODBPOSITRON, get_provider

import panel as pn
import panel.widgets as pnw
pn.extension()


def wgs84_to_web_mercator(df, lon="LON", lat="LAT"):
    """convert mat long to web mercartor"""

    k = 6378137
    df.loc[:,"x"] = df[lon] * (k * np.pi/180.0)
    df.loc[:,"y"] = np.log(np.tan((90 + df[lat]) * np.pi/360.0)) * k
    return df
    
s=pd.read_csv('thor_data_vietnam_small.csv', low_memory=False,index_col=0)
s['MSNDATE'] = pd.to_datetime(s.MSNDATE, format='%Y/%m/%d',errors='coerce')
s['YEAR'] = s.MSNDATE.dt.year.fillna(0).astype(int)
s=s[s.YEAR>0]
s = wgs84_to_web_mercator(s, lon="TGTLONDDD_DDD_WGS84", lat="TGTLATDD_DDD_WGS84")
x = s[~s.TGTLATDD_DDD_WGS84.isnull()].copy()
x = x[~x.TGTCOUNTRY.isin(['PHILLIPINES','UNKNOWN','WESTPAC WATERS'])]

colormap={'NORTH VIETNAM':'brown','SOUTH VIETNAM':'orange','LAOS':'red',
                'CAMBODIA':'green','THAILAND':'blue','UNKNOWN':'gray'}
providers = ['CARTODBPOSITRON','STAMEN_TERRAIN','OSM','ESRI_IMAGERY']
cats = ['TGTCOUNTRY','WEAPONTYPE','MFUNC_DESC']

def draw_map(df=None, long=None, lat=None, height=500, colorby='TGTCOUNTRY',
             point_size=5,
              tile_provider='CARTODBPOSITRON'):
    tile_provider = get_provider(tile_provider)
    tools = "pan,wheel_zoom,box_zoom,hover,tap,lasso_select,reset,save"
    sizing_mode='stretch_both'

    # range bounds supplied in web mercator coordinates
    k = 6378137
    pad = 700000
    if lat == None:
        lat = 16
    if long == None:
        long = 108
    x = long * (k * np.pi/180.0)
    y = np.log(np.tan((90 + lat) * np.pi/360.0)) * k
      
    p = figure(x_range=(x-pad, x+pad), y_range=(y-pad, y+pad),
               x_axis_type="mercator", y_axis_type="mercator", tools=tools,
               plot_width=height, plot_height=height, sizing_mode=sizing_mode)
    p.add_tile(tile_provider)
    if df is None:
        return
    df.loc[:,'color'] = [colormap[i] if i in colormap else 'gray' for i in df[colorby]]
    #df['size'] = 10
    source = ColumnDataSource(df)    
    p.circle(x='x', y='y', size=point_size, alpha=0.7, color='color', source=source)#, legend_group=colorby)
    p.toolbar.logo = None    
    p.title.text = "date"
    hover = p.select(dict(type=HoverTool))
    hover.tooltips = OrderedDict([
        ("TGTCOUNTRY", "@TGTCOUNTRY"),
        ("MSNDATE", "@MSNDATE{%F}"),
        ("TAKEOFFLOCATION", "@TAKEOFFLOCATION"),
        ("WEAPONTYPE", "@WEAPONTYPE"),
        ("MFUNC_DESC", "@MFUNC_DESC")     
    ])
    hover.formatters={'@MSNDATE': 'datetime'}
    return p 
    
def dashboard():
    cols = list(x.columns)
    colorby='TGTCOUNTRY'
    map_pane=pn.pane.Bokeh(width=700)
    df_pane = pn.pane.DataFrame(width=600,height=600)
    date_picker = pnw.DatePicker(name='Pick Date',width=200)
    from datetime import date  
    date_picker.value=date(1965, 1, 1)    
    date_slider = pnw.DateSlider(name='Date', start=dt.datetime(1965, 1, 1), 
                                 end=dt.datetime(1973, 10, 31), value=dt.datetime(1968, 1, 1))      
    tile_select = pnw.Select(name='tile layer',options=providers,width=200)
    filterby_select = pnw.Select(name='filter by',value='',options=['']+cols[1:4],width=200)
    value_select = pnw.Select(name='value',value='',options=[],width=200)
    find_btn = pnw.Button(name='find in region',button_type='primary',width=200)

    def update_tile(event=None):
        p = map_pane.object
        p.renderers = [x for x in p.renderers if not str(x).startswith('TileRenderer')]
        rend = renderers.TileRenderer(tile_source= get_provider(tile_select.value))
        p.renderers.insert(0, rend)

    def update_filter(event):
        col=filterby_select.value
        if col=='':
            value_select.options = []
        else:
            value_select.options = sorted(list(x[col].dropna().unique()))

    def find_in_region(event):
        #get points in selected map area
        p = map_pane.object
        source = p.renderers[1].data_source
        d = x[(x.x>p.x_range.start) & (x.x<p.x_range.end) & (x.y>p.y_range.start) & (x.y<p.y_range.end)]
        #add any filter
        d = do_filter(d)
        if len(d)==0:
            return
        elif len(d)>25000:           
            p.title.text = 'too many points!'
        else: 
            d.loc[:,'color'] = [colormap[i] if i in colormap else 'gray' for i in d[colorby]]        
            source.data = dict(d)
            p.title.text = 'selected %s points' %len(d)
        map_pane.param.trigger('object')     
        return

    def do_filter(d):
        col = filterby_select.value
        val = value_select.value
        if col != '':
            d = d[d[col]==val] 
        return d
    
    def update_date(event):
        date_slider.value = date_picker.value     
        
    def update_map(event=None, date=None):
        p = map_pane.object
        source = p.renderers[1].data_source
        if date == None:
            date = str(date_slider.value)
        d = x[x.MSNDATE==date]
        d = do_filter(d)
        if len(d)==0:
            return  
        d.loc[:,'color'] = [colormap[i] if i in colormap else 'gray' for i in d[colorby]]
        source.data = dict(d)
        p.title.text = date

    sdate='1968-01-01'
    d = x[x.MSNDATE==sdate]
    map_pane.object=draw_map(d) 
    
    date_slider.param.watch(update_map,'value')
    date_picker.param.watch(update_date,'value')
    tile_select.param.watch(update_tile,'value')
    filterby_select.param.watch(update_filter,'value')
    value_select.param.watch(update_map,'value')
    find_btn.on_click(find_in_region)

    dashboard = pn.Column(date_slider,pn.Row(pn.Column(date_picker,tile_select,filterby_select,value_select,find_btn),map_pane))
    return dashboard

app=dashboard()

bootstrap = pn.template.BootstrapTemplate(title='THOR SE ASIA data view',
            header_color='blue') #favicon='static/logo.png'
pn.config.sizing_mode = 'stretch_width'
app=dashboard()
bootstrap.main.append(app)
bootstrap.servable()
