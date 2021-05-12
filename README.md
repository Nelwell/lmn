# LMNOP

## Live Music Notes, Opinions, Photographs

### Features

1. Web app that allows authenticated users to rate and create notes for recent live music shows in the Twin Cities 
2. Anyone can visit the site and create a free account
3. No account required to view artist, venue and show information
4. Users can search Venues and Artists to find associated shows
5. Users can view and search their own notes
6. Users recieve badges for writing notes when they reach certain quantities
7. Users can share artists, venues, shows and notes on social media


### To install

1. Create and activate a virtual environment. Use Python3 as the interpreter. Suggest locating the venv/ directory outside of the code directory.

```
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

Site at

http://127.0.0.1:8000


### Create superuser

`python manage.py createsuperuser`

enter username and password

will be able to use these to log into admin console at

127.0.0.1:8000/admin


### Populate database

With the site server running, go to http://127.0.0.1:8000/scraper

Remain on the page until a small "ok" is displayed in the upper left corner (should take 3-5 minutes)

Close the browser, or navigate back to http://127.0.0.1:8000


#### Adding badges to the database

In the project root directory, run console command: python manage.py loaddata badge_data_fixture.json > lmn.Badge


### Run tests


```
python manage.py test lmn.tests
```

Or just some of the tests,

```
python manage.py test lmn.tests.test_views
python manage.py test lmn.tests.test_views.TestUserAuthentication
python manage.py test lmn.tests.test_views.TestUserAuthentication.test_user_registration_logs_user_in
```


### Functional Tests with Selenium

Make sure you have the latest version of Chrome or Firefox, and the most recent chromedriver or geckodriver, and latest Selenium.

chromedriver/geckodriver needs to be in path or you need to tell Selenium where it is. Pick an approach: http://stackoverflow.com/questions/40208051/selenium-using-python-geckodriver-executable-needs-to-be-in-path

If your DB is hosted at Elephant, your tests might time out, and you might need to use longer waits http://selenium-python.readthedocs.io/waits.html

Run tests with

```
python manage.py test lmn.tests.functional_tests
```

Or select tests, for example,
```
python manage.py test lmn.tests.functional_tests.HomePageTest
python manage.py test lmn.tests.functional_tests.BrowseArtists.test_searching_artists
```


### Test coverage

From directory with manage.py in it,

```
coverage run --source='.' manage.py test lmn.tests
coverage report
```


### PostgreSQL

Recommend using PaaS Postgres such as Elephant, instead of installing local Postgres. 


### References 

#### Pagination code adapted from: 
https://engineertodeveloper.com/how-to-create-pagination-using-django/
#### Code to extend User model adapted from: 
https://blog.khophi.co/extending-django-user-model-userprofile-like-a-pro/
#### Star rating feature references: 
https://codepen.io/neilpomerleau/pen/wzxzQr, 
https://www.semicolonworld.com/question/65313/how-to-send-data-from-javascript-function-to-django-view, 
https://www.pluralsight.com/guides/work-with-ajax-django
#### Social share links from: 
https://pypi.org/project/django-social-share/
