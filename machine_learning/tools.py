
import os, glob
import random, math
import numpy as np
import pandas as pd
from PIL import Image
import torch
from diffusers import StableDiffusionImg2ImgPipeline, EulerDiscreteScheduler

model_id = "stabilityai/stable-diffusion-2-1"
scheduler = EulerDiscreteScheduler.from_pretrained(model_id, subfolder="scheduler")
pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
    model_id, scheduler=scheduler, torch_dtype=torch.float16).to("cuda")

def get_words():
    import requests
    word_site = "https://www.mit.edu/~ecprice/wordlist.10000"
    response = requests.get(word_site)
    w = response.content.splitlines()
    w = [i.decode() for i in w]
    w = [i for i in w if len(i)>3]
    return w

randwords = get_words()

def random_image(image, style, path, n=1,k=3, strength=0.8):

    for i in range(n):
        words = random.choices(randwords,k=k)
        print (words)
        txt = ' '.join(words)
        img2imgprompt(txt, style=style, path=path, init_images=[image], strength=strength)


def tile_images(image_paths, outfile, grid=False, tile_width=300):
    """Make tiled image"""

    from PIL import Image, ImageDraw
    images = [Image.open(path) for path in image_paths]
      
    ratio = images[0].height / images[0].width
    tile_height = int( tile_width * ratio )
    num_rows = int(math.sqrt(len(image_paths)))
    # Calculate number of cols
    num_columns = (len(images) + num_rows - 1) // num_rows

    tiled_width = num_columns * tile_width
    tiled_height = num_rows * tile_height
    tiled_image = Image.new("RGB", (tiled_width, tiled_height))

    for idx, image in enumerate(images):      
        row = idx // num_columns
        col = idx % num_columns
        x_offset = col * tile_width
        y_offset = row * tile_height
        tiled_image.paste(image.resize((tile_width, tile_height)), (x_offset, y_offset))
    if grid == True:
        draw = ImageDraw.Draw(tiled_image)
        # Draw borders around each tile
        for row in range(num_rows):
            for col in range(num_columns):
                x1 = col * tile_width
                y1 = row * tile_height
                x2 = x1 + tile_width
                y2 = y1 + tile_height
                draw.rectangle([x1, y1, x2, y2], outline=(0, 0, 0), width=3)  

    tiled_image.save(outfile)
    return tiled_image

def make_gif(path, outfile):
    """make gif from same condition image"""

    import glob
    from PIL import Image
    files = sorted(glob.glob(path+'/*.png'))
    #print (files)
    img = Image.open(files[0])    
    #size = img.size
    images=[]
    images = [Image.open(f) for f in files]
    images[0].save(outfile,
               save_all=True, append_images=images[1:], 
               optimize=False, duration=400, loop=0)
    return

def img2imgprompt(prompt, n=1, style=None, path='.', negative_prompt=None, 
                    init_images=None, strength=0.8, guidance_scale=9, seed=None):
    """Image-to-image prompt, assumes the correct pipe object"""

    if style != None:
        prompt += ' by %s'%style
    init_images = [Image.open(image).convert("RGB").resize((768,768)) for image in init_images]
    if negative_prompt == None:
        negative_prompt = 'disfigured, bad anatomy, low quality, ugly, tiling, poorly drawn hands, out of frame'
    for c in range(n):        
        if seed == None:
            currseed = torch.randint(0, 10000, (1,)).item()
        else:
            currseed = seed
        #print (prompt, strength, currseed)
        generator = torch.Generator(device="cuda").manual_seed(currseed)        
        image = pipe(prompt, negative_prompt='', image=init_images, num_inference_steps=50,
                     guidance_scale=guidance_scale, generator=generator, strength=strength).images[0]
        if not os.path.exists(path):
            os.makedirs(path)
        i=1
        imgfile = os.path.join(path,prompt[:100]+'_%02d_%d.png' %(i,currseed))
        #print (imgfile)
        while os.path.exists(imgfile):
            i+=1
            imgfile = os.path.join(path,prompt[:100]+'_%02d_%d.png' %(i,currseed))
        image.save(imgfile,'png')        
    return imgfile
