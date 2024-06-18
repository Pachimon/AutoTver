from flask import render_template, request, redirect, url_for
from app import app, series_collection
from bson.objectid import ObjectId


@app.route('/')
def index():
    series = list(series_collection.find())
    return render_template('index.html', series=series)


@app.route('/add_series', methods=['POST'])
def add_series():
    name = request.form['name']
    new_series = {
        'name': name,
        'episodes': []
    }
    series_collection.insert_one(new_series)
    return redirect(url_for('index'))


@app.route('/add_episode/<series_id>', methods=['POST'])
def add_episode(series_id):
    title = request.form['title']
    release_date = request.form['release_date']
    new_episode = {
        'title': title,
        'release_date': release_date,
        'downloaded': False
    }
    series_collection.update_one({'_id': ObjectId(series_id)}, {'$push': {'episodes': new_episode}})
    return redirect(url_for('index'))


@app.route('/update_episode/<series_id>/<episode_id>', methods=['POST'])
def update_episode(series_id, episode_id):
    # Add logic to update episode information
    pass


@app.route('/delete_series/<series_id>')
def delete_series(series_id):
    series_collection.delete_one({'_id': ObjectId(series_id)})
    return redirect(url_for('index'))


@app.route('/delete_episode/<series_id>/<episode_id>')
def delete_episode(series_id, episode_id):
    series_collection.update_one({'_id': ObjectId(series_id)}, {'$pull': {'episodes': {'_id': ObjectId(episode_id)}}})
    return redirect(url_for('index'))
