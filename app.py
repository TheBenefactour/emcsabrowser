import fnmatch
import json
import os
import random
import re
import webbrowser
import requests
import datetime
from string import ascii_uppercase
from eldar import Query
from flask import Flask, request, render_template


def update_user_data():
    with open('user_data.json', 'w', encoding='utf-8') as g:
        json.dump(USER_DATA, g)


with open('user_data.json', 'r', encoding='utf-8') as f:
    USER_DATA = json.load(f)
if not os.path.exists('templates\\cache\\'):
    os.mkdir('templates\\cache\\')


LIVE = True
ALPHA = ascii_uppercase
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

global last_search

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


update_user_data()
with open('indexed_stories.json', 'r', encoding='utf-8') as f:
    STORY_DATA = json.load(f)
if os.path.exists('archived_stories.json'):
    with open('archived_stories.json', 'r', encoding='utf-8') as f:
        STORY_DATA.update(json.load(f))


@app.route('/')
def app_root():
    return render_template('main.html')


@app.route('/list', methods=['GET', 'POST'])
def list_stories():
    favorites_to_add = request.form
    try:
        USER_DATA['favorites']
    except KeyError:
        USER_DATA.update({'favorites': []})
    add_favorites(favorites_to_add)
    return render_template('list.html', data=STORY_DATA, favorites=USER_DATA['favorites'])


@app.route('/random', methods=['GET'])
def select_random_story():
    try:
        tags, tags_rem = get_tags_from_request(request.args)
        tags, temp_list = filter_story_list_by_tags(tags, tags_rem)
        story = random.choice(list(temp_list))
        return render_template('random_story.html', data=STORY_DATA,
                               i=[story, STORY_DATA[story]["author url"].split("/")[-1]], tags=TAGS_DICT)
    except IndexError:
        return "No results found for tags"


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        global last_search
        try:
            term = request.form.get('query')
            tags = []
            tags_rem = []
            file_search = Query(term, ignore_case=True)
            tags, temp_list = filter_stories_by_tags(tags, tags_rem)
            out_list = []
            tags_rem_form = [i[0:2] for i in tags_rem]
            if len(tags_rem) == 0:
                tags_rem_form = 'none'
            for i in temp_list:
                try:
                    story_data = STORY_DATA[i]['description'] + ' ' + i
                    if file_search(story_data):
                        out_list.append([i, STORY_DATA[i]["author url"].split("/")[-1]])
                except KeyError:
                    pass
            if request.form.get('cached'):
                files = list_files('templates\\cache')
                for file in files:
                    try:
                        file_parts = file.split("\\")
                        story_id = f'https://mcstories.com/{file_parts[2]}/index.html'
                        author = STORY_DATA[story_id]["author url"].split("/")[-1]
                        if [story_id, author] not in out_list:
                            if set(STORY_DATA[story_id]['story tags']).intersection(tags) != set() or tags == 'all':
                                if set(STORY_DATA[story_id]['story tags']).intersection(
                                        tags_rem_form) == set() or tags_rem_form == 'none':
                                    with open(file, 'r', encoding='utf-8') as g:
                                        story_data = g.read()
                                    if file_search(story_data):
                                        story_id = f'https://mcstories.com/{file_parts[2]}/index.html'
                                        author = STORY_DATA[story_id]["author url"].split("/")[-1]
                                        out_list.append([story_id, author])
                    except:
                        pass
            if out_list:
                out_list.sort()
                last_search = render_template('search_results.html', term=term, tags=tags, tags_rem=tags_rem_form,
                                              results=out_list, data=STORY_DATA)
                return last_search
            else:
                return 'No results'
        except:
            for i in request.form:
                if i != 'query' or i != 'cached':
                    cache_path = f'templates\\cache\\{i.split("/")[-2]}\\'
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S\\")
                    if not os.path.exists(cache_path):
                        os.mkdir(cache_path)
                    os.mkdir(cache_path + timestamp)
                    with open(cache_path + timestamp + 'index.html', 'wb') as g:
                        data = requests.get(i)
                        g.write(data.content)
                    for chapter in STORY_DATA[i]['chapters']:
                        with open(f'{cache_path}{timestamp}{chapter[0].split("/")[-1]}', 'wb') as g:
                            data = requests.get(f'https://mcstories.com{chapter[0]}')
                            g.write(data.content)
                    try:
                        return last_search
                    except:
                        return render_template('search.html', tags=TAGS_DICT)
    else:
        out_list = []
        for i in request.form:
            out_list.append(i)
        add_favorites(out_list)
        return render_template('search.html', tags=TAGS_DICT)


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


@app.route('/cache')
def cached_list():
    return render_template('cache.html', stories=return_cache_data('templates\\cache', 2))


@app.route('/cache/<title>')
def cached_story(title):
    if title:
        return render_template('cached_story.html', dates=return_cache_data(f'templates\\cache\\{title}', 3),
                               title=title)
    else:
        return 'Missing story parameter'


@app.route('/cache/<title>/<date>')
def cached(title, date):
    if title and date:
        return render_template('cached_date.html', title=title, date=date,
                               files=return_cache_data(f'templates\\cache\\{title}\\{date}', -1))
    else:
        return 'Missing date parameter'


@app.route('/cache/<title>/<date>/<file>')
def cached_view(title, date, file):
    if title and date and file:
        return render_template('cached_file.html', data=read_cached_file(date, file, title))
    else:
        return 'Missing file parameter'


@app.route('/authors')
def list_authors():
    return render_template('authors.html', data=get_author_list())


@app.route('/author/<author>')
def stories_by_author(author):
    return render_template('author.html', results=[[i, author + '.html'] for i in get_author_story_list(author)],
                           data=STORY_DATA)


def read_cached_file(date, file, title):
    with open(f'templates\\cache\\{title}\\{date}\\{file}', 'rb') as g:
        data = g.read().decode('utf-8')
    return data


def get_author_list():
    authors = []
    for story in STORY_DATA:
        data = STORY_DATA[story]['author']
        if data in authors:
            pass
        else:
            authors.append(data)
    return authors


def get_author_story_list(author):
    stories = []
    for story in STORY_DATA:
        if STORY_DATA[story]['author'] == author:
            stories.append(story)
    return stories


def get_chapters_string(data):
    chapters = [f'<p><a href=https://mcstories.com{i[0]}>{i[1]}</a></p>' for i in data['chapters']]
    out_chapters = ''
    for i in chapters:
        out_chapters += i
    return out_chapters


def return_cache_data(dir_location, index_location):
    cached_files = list_files(dir_location)
    data = set()
    for file in cached_files:
        data.add(file.split('\\')[index_location])
    return data


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


def filter_stories_by_tags(tags, tags_rem):
    for i in request.form:
        if i in TAGS_DICT:
            tags.append(i)
        elif i in TAGS_REM:
            tags_rem.append(i)
    tags, temp_list = filter_story_list_by_tags(tags, tags_rem)
    return tags, temp_list


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


def list_files(location):
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

    return file_list


def add_favorites(favorites_to_add):
    new_favorites = [i for i in favorites_to_add if i not in USER_DATA['favorites']]
    for i in new_favorites:
        USER_DATA['favorites'].append(i)
    update_user_data()


def get_tags_from_request(data):
    tags = []
    tags_rem = []
    for i in data:
        if i in TAGS_DICT:
            tags.append(i)
        elif i in TAGS_REM:
            tags_rem.append(i)
    return tags, tags_rem
