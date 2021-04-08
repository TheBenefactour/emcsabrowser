import fnmatch
import json
import os
import random
import re
import webbrowser
import requests
from flask import Flask, request

with open('user_data.json', 'r', encoding='utf-8') as f:
    USER_DATA = json.load(f)

LIVE = True
INDEX_URL = 'https://raw.githubusercontent.com/TheBenefactour/emcsabrowser/main/indexed_stories.json'
ROOT = 'http://localhost:5000/'
TAGS_LIST_ADD = '<p><fieldset name=tags><h2>Include Tags:</h2>' \
            '<p><input type="checkbox" name="md" value="md "/><label for="md">Male Dominant</label>' \
            '<input type="checkbox" name="fd" value="fd" /><label for="fd">Female Dominant</label>' \
            '<input type="checkbox" name="ca" value="ca" /><label for="ca">Cannibalism</label></p><p>' \
            '<input type="checkbox" name="cb" value="cb" /><label for="cb">Comic Book: Super-hero/heroine</label>' \
            '<input type="checkbox" name="ds" value="ds" /><label for="ds">Dominance and/or Submission</label>' \
            '<input type="checkbox" name="ff" value="ff" /><label for="ff">Female/Female Sex</label></p><p>' \
            '<input type="checkbox" name="ft" value="ft" /><label for="ft">Fetish</label>' \
            '<input type="checkbox" name="fu" value="fu" /><label for="fu">Furry</label>' \
            '<input type="checkbox" name="gr" value="gr" />' \
            '<label for="gr">Growth/Enlargement of Bodies and Parts</label>' \
            '</p><p><input type="checkbox" name="hm" value="hm" /><label for="hm">Humiliation</label>' \
            '<input type="checkbox" name="hu" value="hu" /><label for="hu">Humor</label>' \
            '<input type="checkbox" name="in" value="in" /><label for="in">Incest</label></p><p>' \
            '<input type="checkbox" name="la" value="la" /><label for="la">Lactation</label>' \
            '<input type="checkbox" name="ma" value="ma" /><label for="ma">Masturbation</label>' \
            '<input type="checkbox" name="mc" value="mc" /><label for="mc">Mind Control</label></p><p>' \
            '<input type="checkbox" name="mf" value="mf" /><label for="mf">Male/Female Sex</label>' \
            '<input type="checkbox" name="mm" value="mm" /><label for="ex">Male/Male Sex</label>' \
            '<input type="checkbox" name="nc" value="nc" /><label for="nc">Non-consensual</label></p><p>' \
            '<input type="checkbox" name="rb" value="rb" /><label for="ex">Robots</label>' \
            '<input type="checkbox" name="sc" value="sc" /><label for="sc">Scatology</label>' \
            '<input type="checkbox" name="sf" value="sf" /><label for="sf">Science Fiction</label></p><p>' \
            '<input type="checkbox" name="ts" value="ts" /><label for="ts">Time Stop</label>' \
            '<input type="checkbox" name="ws" value="ws" /><label for="ws">Watersports</label>' \
            '</p></fieldset></p>'
TAGS_LIST_REM = '<p><fieldset name=tags-rem><h2>Exclude Tags:</h2>' \
            '<p><input type="checkbox" name="md-rem" value="md-rem"/><label for="md-rem">Male Dominant</label>' \
            '<input type="checkbox" name="fd-rem" value="fd-rem" /><label for="fd-rem">Female Dominant</label>' \
            '<input type="checkbox" name="ca-rem" value="ca-rem" /><label for="ca-rem">Cannibalism</label></p><p>' \
            '<input type="checkbox" name="cb-rem" value="cb-rem" />' \
            '<label for="cb-rem">Comic Book: Super-hero/heroine</label>' \
            '<input type="checkbox" name="ds-rem" value="ds-rem" />' \
            '<label for="ds-rem">Dominance and/or Submission</label>' \
            '<input type="checkbox" name="ff-rem" value="ff-rem" />' \
            '<label for="ff-rem">Female/Female Sex</label></p><p>' \
            '<input type="checkbox" name="ft-rem" value="ft-rem" /><label for="ft-rem">Fetish</label>' \
            '<input type="checkbox" name="fu-rem" value="fu-rem" /><label for="fu-rem">Furry</label>' \
            '<input type="checkbox" name="gr-rem" value="gr-rem" />' \
            '<label for="gr-rem">Growth/Enlargement of Bodies and Parts</label>' \
            '</p><p><input type="checkbox" name="hm-rem" value="hm-rem" /><label for="hm-rem">Humiliation</label>' \
            '<input type="checkbox" name="hu-rem" value="hu-rem" /><label for="hu-rem">Humor</label>' \
            '<input type="checkbox" name="in-rem" value="in-rem" /><label for="in-rem">Incest</label></p><p>' \
            '<input type="checkbox" name="la-rem" value="la-rem" /><label for="la-rem">Lactation</label>' \
            '<input type="checkbox" name="ma-rem" value="ma-rem" /><label for="ma-rem">Masturbation</label>' \
            '<input type="checkbox" name="mc-rem" value="mc-rem" /><label for="mc-rem">Mind Control</label></p><p>' \
            '<input type="checkbox" name="mf-rem" value="mf-rem" /><label for="mf-rem">Male/Female Sex</label>' \
            '<input type="checkbox" name="mm-rem" value="mm-rem" /><label for="ex-rem">Male/Male Sex</label>' \
            '<input type="checkbox" name="nc-rem" value="nc-rem" /><label for="nc-rem">Non-consensual</label></p><p>' \
            '<input type="checkbox" name="rb-rem" value="rb-rem" /><label for="ex-rem">Robots</label>' \
            '<input type="checkbox" name="sc-rem" value="sc-rem" /><label for="sc-rem">Scatology</label>' \
            '<input type="checkbox" name="sf-rem" value="sf-rem" /><label for="sf-rem">Science Fiction</label></p><p>' \
            '<input type="checkbox" name="ts-rem" value="ts-rem" /><label for="ts-rem">Time Stop</label>' \
            '<input type="checkbox" name="ws-rem" value="ws-rem" /><label for="ws-rem">Watersports</label>' \
            '</p></fieldset></p>'
TAGS = ['bd', 'be', 'ca', 'cb', 'ds', 'ex', 'fd', 'ff', 'ft', 'fu', 'gr', 'hm', 'hu', 'in', 'la', 'ma', 'mc', 'md',
        'mf', 'mm', 'nc', 'rb', 'sc', 'sf', 'ts', 'ws']
TAGS_REM = [f'{i}-rem' for i in TAGS]

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
    return f'<span><p><a href=/list>List</a></p><p><a href=/random>Random</a></p>' \
           f'<p><a href=/search>Search</a></p><p><a href=/favorites>Favorites</a></p></span>'


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

    out_list = '<div><form method="post"><div style="position:fixed; background-color:white; width:100%">' \
               '<p><input type="submit" value="Add selected to favorites."></p></div><div style="padding-top: 50px">'
    cur = 0
    for i in STORY_DATA:
        if i in USER_DATA['favorites']:
            out_list += f'<p><input type="checkbox" id="story{cur}" name="{i}" value="{i}"><label for="story{cur}">' \
                        f'<a href={i} style="background-color: yellow">{i}</a></label></p>'
        else:
            out_list += f'<p><input type="checkbox" id="story{cur}" name="{i}" value="{i}"><label for="story{cur}">' \
                        f'<a href={i}>{i}</a></label></p>'
        cur += 1
    return out_list + '</div></form></div>'


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
def select_random_story(tag=None):
    story = random.choice(list(STORY_DATA))
    data = STORY_DATA[story]
    out_chapters = get_chapters_string(data)
    out = get_story_string(story, data, out_chapters)
    if tag:
        out += '<p>Tag restrictions not yet implemented</p>'  # TODO
    return out


@app.route('/search', methods=['GET', 'POST'])
def search():
    try:
        term = request.form['query']
        tags = []
        tags_rem = []
        for i in request.form:
            if i in TAGS:
                tags.append(i)
            elif i in TAGS_REM:
                tags_rem.append(i)
        tags, temp_list = filter_story_list_by_tags(tags, tags_rem)
        out_list = f'<div><form method="post"><input type="text" name="query">' \
                   f'<input type="submit" label="Submit"></form></div>' \
                   f'<div><p>Searching for: "{term}" including {tags} tags and excluding {[i[0:2] for i in tags_rem]}' \
                   f'</p></div><form method="post">' \
                   f'<div style="position:fixed; background-color:white; width:100%"><p>' \
                   f'<input type="submit" value="Add selected to favorites."></p></div>' \
                   f'<div style="padding-top: 50px">'
        for i in temp_list:
            try:
                story_added = False
                for t in term.split(' '):
                    if t in i or t in STORY_DATA[i]['description'] and not story_added:
                        out_list += f'<div><input type="checkbox" id="{i}" name="{i}" value="{i}">' \
                                    f'<label for="{i}">Add to favorites</label>' + \
                                    get_story_string(i) + '</div><hr class="dotted">'
                        story_added = True
            except KeyError:
                pass
        if out_list:
            return out_list + '</form>'
    except Exception:
        out_list = []
        for i in request.form:
            out_list.append(i)
        add_favorites(out_list)
        return f'<form method="post"><p><input type="text" name="query" /><input type="submit" label="Submit" /></p>' \
               f'<fieldset><h1>Tags</h1>{TAGS_LIST_ADD}{TAGS_LIST_REM}</div></form>'


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
    out = ''
    try:
        temp = USER_DATA['favorites']
        temp.sort()
        for i in temp:
            out += f'<p>{get_story_string(i)}<p><hr class="dotted">'
        return out
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
