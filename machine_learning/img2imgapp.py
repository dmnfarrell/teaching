#!/local/stablediff/bin/python

"""
    panel app for stable diffusion image-to-image 
    Created Dec 2023
    opyright (C) Damien Farrell

    This program is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License
    as published by the Free Software Foundation; either version 3
    of the License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""

import os, glob
import random, math
import numpy as np
import pandas as pd
from PIL import Image
import matplotlib as mpl
from tools import *

import panel as pn
import panel.widgets as pnw
pn.extension('tabulator', css_files=[pn.io.resources.CSS_URLS['font-awesome']])

artists = list(pd.read_csv('stable_diffusion_artist_styles.csv').Name)
artists = ['','random']+artists

def random_image(outfile):
    from randimage import get_random_image, show_array
    img_size = (256,256)
    img = get_random_image(img_size)
    mpl.image.imsave(outfile, img)
    
def dashboard():
    
    def run(**kwargs):
        """Run prompt""" 
      
        filename = img2imgprompt(path='temp', n=1, **kwargs)
        name = kwargs['seed']
        add_image(filename)
        #print (filename)

    w=210
    startimg = None
    styles = ['','oil','impressionist','pencil','ink','watercolor','crayon drawing','digital art','pop art','cubism',
              'sculpture','craft clay','linocut','engraving','anime','studio photography','analog film',
              'abstract','pixel art','paper collage','isometric','lowpoly','origami']
    
    #title = html_pane = pn.pane.HTML("""<h2>image-to-image app</h2>""")
    file_input = pnw.FileInput(width=w,accept='.png,.jpg')    
    go_btn = pnw.Button(name='run',width=w,button_type='success')
    stop_btn = pnw.Button(name='stop',width=w,button_type='danger')
    prompt_input = pnw.TextAreaInput(name='prompt',value='',width=w)
    style_input = pnw.Select(name='style',options=styles,width=w)
    artist_input = pnw.Select(name='artist',options=artists,width=w)
    strength_input = pnw.FloatSlider(name='strength',value=.8,step=.01,start=.01,end=.99,width=w)
    guidance_input = pnw.IntSlider(name='guidance',value=5,step=1,start=0,end=10,width=w)
    seed_input = pnw.IntInput(name='seed',value=0,step=1,start=0,end=10000,width=w)
    progress = pn.indicators.Progress(name='Progress', value=0, width=w, bar_color='primary')    
    widgets = pn.Column(pn.WidgetBox(file_input,prompt_input,style_input,artist_input,strength_input,
                                     guidance_input,seed_input,go_btn,progress), height=700, width=230)
                
    img_pane = pn.pane.Image(caption='template', sizing_mode="stretch_width")
    randimg_btn = pnw.Button(name='random template',width=160,button_type='primary')
    setcurrent_btn = pnw.Button(name='use current',width=160,button_type='primary')
    tabs = pn.Tabs(closable=True, tabs_location='left',sizing_mode="stretch_width")

    def random_template(event):
        random_image('randimg.png')
        img_pane.object = 'randimg.png'
        #file_input.filename = None
        
    def load_template(event):
        img_pane.object = file_input.value

    def current_to_template(event):
        img_pane.object = tabs[tabs.active].object
        #file_input.filename = None
        
    def add_image(imgfile):
        #add new image         
        name = os.path.basename(imgfile)
        new = pn.pane.Image(imgfile, caption=name, sizing_mode="stretch_both")        
        tabs.append(new)
        tabs.active = len(tabs)-1
              
    def execute(event):
        #run the model with widget         
        startimg = file_input.filename
        #print (file_input.filename,img_pane.object)
              
        if startimg == None:
            startimg = img_pane.object
        seed = seed_input.value
        if seed == 0:
            seed = None
        if startimg is None:
            return
        progress.value=-1
        if artist_input.value == 'random':
            artist = random.choice(artists[2:])
        else:
            artist = artist_input.value
        prompt = prompt_input.value+', '+style_input.value
        run(prompt=prompt, style=artist, 
            init_images=[startimg],strength=strength_input.value, seed=seed)
        progress.value=0
        
    file_input.param.watch(load_template, 'value')
    go_btn.param.watch(execute, 'clicks')
    randimg_btn.param.watch(random_template, 'clicks')
    setcurrent_btn.param.watch(current_to_template, 'clicks')
    
    app = pn.Column(
                 pn.Row(widgets,tabs,pn.Column(randimg_btn,setcurrent_btn,img_pane,height=500,width=220),
                 sizing_mode='stretch_both',
                 styles={'background': 'WhiteSmoke'}))

    return app

bootstrap = pn.template.BootstrapTemplate(title='image-to-image app',
                logo='flowers.jpg',header_color='blue')
pn.config.sizing_mode = 'stretch_width'
app = dashboard()
bootstrap.main.append(app)
bootstrap.servable()

if __name__ == '__main__':
	pn.serve(bootstrap, host=['*'], port=5000, 
          websocket_origin=['*'])