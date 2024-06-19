from flask import render_template, request, redirect, url_for, jsonify
from app import app, series_collection
from bson.objectid import ObjectId
import yt_dlp


@app.route('/')
def index():
    series = list(series_collection.find())
    return render_template('index.html', series=series)


@app.route('/series', methods=['GET'])
def get_series():
    series_list = list(series_collection.find())
    return jsonify(series_list)


@app.route('/add_series', methods=['POST'])
def add_series():
    name = request.form['name']
    new_series = {
        'name': name,
        'episodes': []
    }
    series_collection.insert_one(new_series)
    return redirect(url_for('index'))


@app.route('/toggle_episode/<series_id>/<category>', methods=['POST'])
def toggle_episode(series_id, category):
    follow_status = series_collection.find_one({'_id': series_id})
    follow_status = follow_status['follow']
    follow_status[category] = not follow_status[category]
    series_collection.update_one({'_id': series_id}, {'$set': {'follow': follow_status}})
    return redirect(url_for('index'))


@app.route('/download_episode/<series_id>/<category>/<episode_id>', methods=['POST'])
def update_episode(series_id, category, episode_id):
    def my_hook(d):
        if d['status'] == 'finished':
            print('Done downloading, now post-processing ...')

    URLS = ["https://tver.jp" + '/episodes/' + episode_id]
    series = series_collection.find_one({'_id': series_id})
    ydl_opts = {
        'format': 'best',
        'writesubtitles': True,
        'allsubtitles': True,
        'subtitlesformat': 'srt/best',
        'progress_hooks': [my_hook],
        'outtmpl': f"/Media/{series['name']}/{series['episode'][category][episode_id]}.%(ext)s"
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        error_code = ydl.download(URLS)


@app.route('/delete_series/<series_id>')
def delete_series(series_id):
    series_collection.delete_one({'_id': ObjectId(series_id)})
    return redirect(url_for('index'))


@app.route('/delete_episode/<series_id>/<episode_id>')
def delete_episode(series_id, episode_id):
    series_collection.update_one({'_id': ObjectId(series_id)}, {'$pull': {'episodes': {'_id': ObjectId(episode_id)}}})
    return redirect(url_for('index'))
