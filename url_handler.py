import json
import os
import sys
import urllib.parse

from flask import Flask, Request, Response, g, render_template, send_from_directory

import db_utils.query as query

INTERP = os.path.join(os.environ['HOME'], 'preview.mikeroburst.com', 'venv', 'bin', 'python')  # noqa
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)
sys.path.append(os.getcwd())

app = Flask(__name__)

# TODO: Get the root from external config
app.config['PHOTOS_ROOT'] = os.path.join(os.environ['HOME'], 'mikeroburst.com', 'pics', 'albums')


@app.route('/photos', strict_slashes=False)
@app.route('/photos/<path:user_path>', strict_slashes=False)
def photos(user_path=None):
    """
    This is the main interface for viewing a grid of images. It returns the
    html template needed for displaying the image grid and setting up the
    lightbox.
    :param user_path:
    :return:
    """
    if user_path is not None:
        user_path = format_user_path(user_path, leading_slash=False)
    # If we pass user_path=None, url_for() treats that as pointing to '/'
    return render_template('grid.html', user_path=user_path)


@app.route('/get_path_contents', strict_slashes=False)
@app.route('/get_path_contents/<path:user_path>', strict_slashes=False)
def get_path_contents(user_path=None):
    """
    This returns the JSON containing all the photos at a given path.
    :param user_path:
    :return:
    """
    if user_path is None:
        user_path = '/'
    user_path = format_user_path(user_path, leading_slash=True)
    querier = get_querier()
    res = json.dumps(querier.get_path_contents(user_path),
                     indent=4, sort_keys=True)
    return Response(res, mimetype='application/json')


@app.route('/photo/<path:filename>')
def photo(filename):
    """
    Serves individual photos and thumbnails.

    This is what maps URL requests like
    /photo/2017/foo.jpg
    to the defined location of photos on the server, like
    webpics/albums/2017/foo.jpg
    """
    filename = urllib.parse.unquote(filename)
    return send_from_directory(app.config['PHOTOS_ROOT'], filename)


def format_user_path(user_path, leading_slash=True):
    """
    Sanitizes the user path by un-escaping special characters and standardizing
    the trailing slash.
    :param user_path:
    :param leading_slash:
    :return:
    """
    path = urllib.parse.unquote(user_path)
    if leading_slash and not path.startswith('/'):
        path = '/{}'.format(path)
    if path != '/':
        path = path.rstrip('/')
    return path


def get_querier():
    if not hasattr(g, 'querier'):
        host = os.environ['PHOTOS_DB_HOST']
        user = os.environ['PHOTOS_DB_USER']
        password = os.environ['PHOTOS_DB_PASSWORD']
        db = os.environ['PHOTOS_DB_NAME']

        querier = query.Querier(host, user, password, db)
        querier.connect()
        g.querier = querier
        return querier
    else:
        return g.querier


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'querier'):
        g.querier.close()
