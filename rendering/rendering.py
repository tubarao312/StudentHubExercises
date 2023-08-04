# import sympy as sp

# sp.preview(r'$$\int_0^1 e^x\,dx$$', viewer='file', filename='test.png', euler=False)


import matplotlib.pyplot as plt
import matplotlib as mpl
import io
from PIL import Image, ImageChops

white = (255, 255, 255, 255)

def latex_to_img(tex):
    buf = io.BytesIO()
    plt.rc('text', usetex=True)
    plt.rc('font', family='serif')
    mpl.rcParams.update(mpl.rcParamsDefault)
    plt.axis('off')
    plt.text(0.05, 0.5, f'${tex}$', size=40)
    plt.savefig(buf, format='png')
    plt.close()

    im = Image.open(buf)
    bg = Image.new(im.mode, im.size, white)
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    return im.crop(bbox)

latex_to_img(latex).save('img.png')


