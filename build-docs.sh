#!/usr/bin/env bash
# build the docs
pipenv run tox -e docs

# commit and push
git add -A
git commit -m "building and pushing docs"
git push origin master

# switch branches and pull the data we want
git checkout gh-pages
rm -rf .
git checkout master docs/build/html
mv ./docs/build/html/* ./
touch .nojekyll
rm -rf ./docs
git add -A
git commit -m "publishing updated docs..."
git push origin gh-pages

# switch back
git checkout master
