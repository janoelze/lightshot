import urllib
import traceback

from flask import Flask, request, jsonify

from lightshot.S3 import S3
from lightshot.screenshot import Screenshot
from lightshot.LoggerFactory import LoggerFactory

import argparse
import os

debug = True

app = Flask(__name__)
app.config.from_envvar('LIGHTSHOT_SETTINGS')
logger = LoggerFactory(app.config['LS_LOG_PATH'])
app.logger.addHandler(logger.create_rotating_file_handler())

_basedir = os.path.abspath(os.path.dirname(__file__))
parser = argparse.ArgumentParser(description='run the app')
parser.add_argument('--port', type=int, default=5000)
parser.add_argument('--host', type=str, default='127.0.0.1')
args = parser.parse_args()

@app.route("/generate")
def generate():
    url = request.args.get('url', '')
    url = urllib.unquote(url).decode('utf8')

    try:
        screenshot = Screenshot(url)
        filename = screenshot.capture()

        response = {'success': True, 'path': filename}

        upload_to_s3 = app.config['S3_UPLOAD']

        if upload_to_s3:
            s3 = S3(app.config['S3_ACCESS_KEY'], app.config['S3_SECRET_KEY'], app.config['S3_BUCKET'])
            s3_url = s3.upload_file(screenshot, public_read=True)
            screenshot.delete_local_file()
            response['s3_url'] = s3_url
            del response['path']

        return jsonify(response)

    except Exception as e:
        app.logger.error(traceback.format_exc())

        if app.debug:
            raise e

        return jsonify({'success': False})

if __name__ == "__main__":
    app.run(
        host=args.host,
        port=args.port,
        debug=debug
    )
