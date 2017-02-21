import json

from flask import Flask, render_template, abort

import config

def current_image_metadata(camera_id):
    with open(config.IMAGES_FILE) as f:
        return json.load(f)[str(camera_id)]

app = Flask(__name__)

@app.route('/<int:camera>')
def image(camera):
    if camera > len(config.CAMERAS):
        abort(404)
    camera_id = config.CAMERAS[camera - 1]
    image_metadata = current_image_metadata(camera_id)
    return render_template('camera.html',
        camera=camera,
        image_time=image_metadata['dateTaken'].split('T')[1],
        image_url=image_metadata['url']
    )
