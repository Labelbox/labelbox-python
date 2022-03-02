import glob
import json
import os

import click
import nbformat
import requests
from nbconvert import MarkdownExporter

README_AUTH = os.getenv('README_AUTH')
README_ENDPOINT = "https://dash.readme.com/api/v1/docs"
README_DOC_ENDPOINT = "https://dash.readme.com/api/v1/docs/"
CATEGORY_ID = '61fb645198ad91004246bd5f'
CATEGORY_SLUG = 'tutorials'


def upload_doc(path, section):
    title = path.split('/')[-1].replace(".ipynb", '').capitalize().replace('_', ' ')

    with open(path) as fb:
        nb = nbformat.reads(json.dumps(json.load(fb)), as_version=4)

    nb.cells = [nb.cells[1]] + nb.cells[3:]
    nb.cells[0]['source'] += '\n'
    exporter = MarkdownExporter()

    body, resources = exporter.from_notebook_node(nb)

    payload = {
        "hidden": True,
        "title": title.replace(' ', '-') + f'-{section["slug"]}',
        "category": CATEGORY_ID,
        "parentDoc": section['id'],
        "body": body
    }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": README_AUTH
    }

    response = requests.post(README_ENDPOINT, json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()
    change_name(data['slug'], title, headers)


def make_sections(sections):
    for section in sections:
        print(section)
        payload = {
            "hidden": True,
            "order": section['order'],
            "title": section['title'].replace(' ', '-') + '-nb-section',
            "category": CATEGORY_ID
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": README_AUTH
        }

        response = requests.post(README_ENDPOINT, json=payload, headers=headers)
        data = response.json()

        section['id'] = data['id']
        section['slug'] = data['slug']

        change_name(data["slug"], section['title'], headers)

    return sections


def change_name(slug, title, headers):
    resp = requests.put(
        f'{README_DOC_ENDPOINT}/{slug}',
        json={
            "title": title,
            "category": CATEGORY_ID
        },
        headers=headers
    )
    resp.raise_for_status()


def erase_category_docs(cat_slug):
    headers = {
        "Accept": "application/json",
        "Authorization": README_AUTH
    }

    response = requests.request("GET", f'https://dash.readme.com/api/v1/categories/{cat_slug}/docs', headers=headers)
    docs = response.json()
    for doc in docs:
        for child in doc["children"]:
            resp = requests.delete(f'{README_DOC_ENDPOINT}/{child["slug"]}', headers=headers)
        resp = requests.delete(f'{README_DOC_ENDPOINT}/{doc["slug"]}', headers=headers)


@click.command()
@click.option('--config-path')
# @click.option('--output-path')
def main(config_path):
    # print(input_path)
    erase_category_docs(CATEGORY_SLUG)
    with open(config_path) as fb:
        config = json.load(fb)
        config = make_sections(config)

    for section in config:
        print(section, '\n------')
        for path in glob.glob(f'{section["dir"]}/**.ipynb'):
            print('*', path)
            upload_doc(path, section)
        print('-------')


if __name__ == '__main__':
    main()
