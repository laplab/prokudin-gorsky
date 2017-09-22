from os.path import join
from pathlib import Path

import click
import numpy as np
from skimage.io import imread, imsave
from tqdm import tqdm

from utils import channel_crop, channel_split, channel_pyramid_search, mse, shift


@click.command()
@click.argument('img')
@click.argument('dest')
def align_image(img, dest):
    """
    Aligns channels from image IMG and saves
    colored version as DEST image
    """
    camera = imread(img)
    img = channel_crop(camera)
    camera_height, camera_width = camera.shape
    r, g, b = channel_split(img)

    depth = 3
    if camera_width > 1000:
        depth = 5

    red_offset = channel_pyramid_search(g, r, mse, (-7, 7), depth)
    blue_offset = channel_pyramid_search(g, b, mse, (-7, 7), depth)
    offset = np.concatenate((red_offset, blue_offset))

    imsave(dest, shift(img, offset))


@click.command()
@click.argument('img_dir', metavar='img')
@click.argument('dest_dir', metavar='dest')
@click.pass_context
def align_images(ctx, img_dir, dest_dir):
    """
    Aligns channels from images in IMG directory and
    saves colored versions in DEST directory
    """
    for img_path in tqdm(Path(img_dir).iterdir()):
        ctx.invoke(align_image, img=str(img_path), dest=join(dest_dir, img_path.name))


@click.group()
def app():
    pass

app.add_command(align_image)
app.add_command(align_images)

if __name__ == '__main__':
    app()
