import fnmatch
import json
import os
import random
import re
import webbrowser
import requests
from flask import Flask, request, render_template

with open('user_data.json', 'r', encoding='utf-8') as f:
    USER_DATA = json.load(f)

LIVE = True
INDEX_URL = 'https://raw.githubusercontent.com/TheBenefactour/emcsabrowser/main/indexed_stories.json'
ROOT = 'http://localhost:5000/'
TAGS_DICT = {'bd': 'Bondage and/or Discipline', 'be': 'Bestiality', 'ca': 'Cannibalism',
             'cb': 'Comic Book: Super-hero/heroine', 'ds': 'Dominance and/or Submission', 'ex': 'Exhibitionism',
             'fd': 'Female Dominant', 'ff': 'Female/Female Sex', 'ft': 'Fetish', 'fu': 'Furry',
             'gr': 'Growth/Enlargement of Bodies and Parts', 'hm': 'Humiliation', 'hu': 'Humiliation', 'in': 'Incest',
             'la': 'Lactation', 'ma': 'Masturbation', 'mc': 'Mind Control', 'md': 'Male Dominant',
             'mf': 'Male/Female Sex', 'mm': 'Male/Male Sex', 'nc': 'Non-Consensual', 'rb': 'Robots', 'sc': 'Scatology',
             'sf': 'Science Fiction', 'ts': 'Time Stop', 'ws': 'Watersports'}
TAGS_REM = [f'{i}-rem' for i in TAGS_DICT]

app = Flask(__name__)
webbrowser.open(ROOT)

if LIVE:
    r = requests.request('HEAD', INDEX_URL)
    etag = r.headers['ETag']
    if etag != USER_DATA['updated']:
        print('Updating database...')
        new = requests.get(INDEX_URL)
        with open('indexed_stories.json', 'w', encoding='utf-8') as f:
            f.write(new.content.decode('utf-8'))
        USER_DATA['updated'] = etag
    else:
        print('Database is up to date!')


def update_user_data():
    with open('user_data.json', 'w', encoding='utf-8') as g:
        json.dump(USER_DATA, g)


update_user_data()
with open('indexed_stories.json', 'r', encoding='utf-8') as f:
    STORY_DATA = json.load(f)


@app.route('/')
def app_root():
    return render_template('main.html')


def add_favorites(favorites_to_add):
    new_favorites = [i for i in favorites_to_add if i not in USER_DATA['favorites']]
    for i in new_favorites:
        USER_DATA['favorites'].append(i)
    update_user_data()


@app.route('/list', methods=['GET', 'POST'])
def list_stories():
    favorites_to_add = request.form
    try:
        USER_DATA['favorites']
    except KeyError:
        USER_DATA.update({'favorites': []})
    add_favorites(favorites_to_add)
    return render_template('list.html', data=STORY_DATA, favorites=USER_DATA['favorites'])


def list_files():
    location = 'chapters'
    includes = ['*.html']  # for files only
    excludes = ['/none']  # for dirs and files

    # transform glob patterns to regular expressions
    includes = r'|'.join([fnmatch.translate(x) for x in includes])
    excludes = r'|'.join([fnmatch.translate(x) for x in excludes]) or r'$.'
    file_list = []

    def iterate(directory):
        for root, dirs, files in os.walk(directory):

            # exclude dirs
            dirs[:] = [os.path.join(root, d) for d in dirs]
            dirs[:] = [d for d in dirs if not re.match(excludes, d)]
            for d in dirs:
                iterate(d)

            # exclude/include files
            files = [os.path.join(root, h) for h in files]
            files = [h for h in files if not re.match(excludes, h)]
            files = [h for h in files if re.match(includes, h)]

            for filename in files:
                file_list.append(filename)

    iterate(location)

    out_str = '<span>'
    for g in file_list:
        out_str += '<p>'
        out_str += g.split('\\')[-1]
        out_str += '</p>'
    out_str += '</span>'
    return out_str


@app.route('/random', methods=['GET', 'POST'])
def select_random_story():
    story = random.choice(list(STORY_DATA))
    return render_template('random_story.html', data=STORY_DATA,
                           i=[story, STORY_DATA[story]["author url"].split("/")[-1]])


@app.route('/search', methods=['GET', 'POST'])
def search():
    try:
        term = request.form['query']
        tags = []
        tags_rem = []
        for i in request.form:
            if i in TAGS_DICT:
                tags.append(i)
            elif i in TAGS_REM:
                tags_rem.append(i)
        tags_rem_form = [i[0:2] for i in tags_rem]
        if len(tags_rem) == 0:
            tags_rem_form = 'none'
        tags, temp_list = filter_story_list_by_tags(tags, tags_rem)
        out_list = []
        for i in temp_list:
            try:
                story_added = False
                for t in term.split(' '):
                    if t in i or t in STORY_DATA[i]['description'] and not story_added:
                        out_list.append([i, STORY_DATA[i]["author url"].split("/")[-1]])
                        story_added = True
            except KeyError:
                pass
        if out_list:
            return render_template('search_results.html', term=term, tags=tags, tags_rem=tags_rem_form,
                                   results=out_list, data=STORY_DATA)
    except Exception:
        out_list = []
        for i in request.form:
            out_list.append(i)
        add_favorites(out_list)
        return render_template('search.html', tags=TAGS_DICT)


def filter_story_list_by_tags(tags, tags_rem):
    temp_list = []
    if len(tags) == 0:
        tags = 'all'
        temp_list = STORY_DATA
    else:
        for i in STORY_DATA:
            story_tags_set = set(STORY_DATA[i]['story tags'])
            if story_tags_set.intersection(tags) != set() and \
                    set([f'{i}-rem' for i in story_tags_set]).intersection(tags_rem) == set():
                temp_list.append(i)
    return tags, temp_list


@app.route('/favorites')
def favorites():
    out = []
    try:
        temp = USER_DATA['favorites']
        temp.sort()
        for i in temp:
            out.append([i, STORY_DATA[i]["author url"].split("/")[-1]])
        return render_template('favorites.html', data=STORY_DATA, favorites=out)
    except KeyError:
        return "No favorites found."


def get_story_string(story, data=None, out_chapters=None):
    if not data:
        data = STORY_DATA[story]
    if not out_chapters:
        out_chapters = get_chapters_string(data)
    out = f'<p><a href={story}>{story}</a><p><p>Tags: {data["story tags"]}</p>' \
          f'<p>Author: <a href=https://mcstories.com/Authors/{data["author url"].split("/")[-1]}>{data["author"]}</a>' \
          f'</p><p>Word Count: {data["word count"]}</p><p>{out_chapters}</p><p>Date Added: {data["date added"]}</p>' \
          f'<p>Date Updated: {data["date updated"]}</p><p>Summary: {data["description"]}</p>'
    return out


def get_chapters_string(data):
    chapters = [f'<p><a href=https://mcstories.com{i[0]}>{i[1]}</a></p>' for i in data['chapters']]
    out_chapters = ''
    for i in chapters:
        out_chapters += i
    return out_chapters
