import tempfile
import filecmp
import os 

from django.test import TestCase, Client

from django.test import override_settings
from django.urls import reverse
from django.contrib import auth
from django.contrib.auth import authenticate
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from django.db import transaction

from lmn.models import Profile, Venue, Artist, Note, Show, ShowRating, Badge
from django.contrib.auth.models import User

import re, datetime
from datetime import timezone

from PIL import Image 

# TODO verify correct templates are rendered.

class TestEmptyViews(TestCase):

    ''' main views - the ones in the navigation menu'''
    def test_with_no_artists_returns_empty_list(self):
        response = self.client.get(reverse('artist_list'))
        self.assertFalse(response.context['artists'])  # An empty list is false

    def test_with_no_venues_returns_empty_list(self):
        response = self.client.get(reverse('venue_list'))
        self.assertFalse(response.context['venues'])  # An empty list is false

    def test_with_no_notes_returns_empty_list(self):
        response = self.client.get(reverse('latest_notes'))
        self.assertFalse(response.context['notes'])  # An empty list is false


class TestArtistViews(TestCase):

    fixtures = ['testing_artists', 'testing_venues', 'testing_shows']

    def test_all_artists_displays_all_alphabetically(self):
        response = self.client.get(reverse('artist_list'))

        # .* matches 0 or more of any character. Test to see if
        # these names are present, in the right order

        regex = '.*ACDC.*REM.*Yes.*'
        response_text = str(response.content)

        self.assertTrue(re.match(regex, response_text))
        self.assertEqual(len(response.context['artists']), 3)


    def test_artists_search_clear_link(self):
        response = self.client.get( reverse('artist_list') , {'search_name' : 'ACDC'} )

        # There is a clear link, it's url is the main venue page
        all_artists_url = reverse('artist_list')
        self.assertContains(response, all_artists_url)


    def test_artist_search_no_search_results(self):
        response = self.client.get( reverse('artist_list') , {'search_name' : 'Queen'} )
        self.assertNotContains(response, 'Yes')
        self.assertNotContains(response, 'REM')
        self.assertNotContains(response, 'ACDC')
        # Check the length of artists list is 0
        self.assertEqual(len(response.context['artists']), 0)


    def test_artist_search_partial_match_search_results(self):

        response = self.client.get(reverse('artist_list'), {'search_name' : 'e'})
        # Should be two responses, Yes and REM
        self.assertContains(response, 'Yes')
        self.assertContains(response, 'REM')
        self.assertNotContains(response, 'ACDC')
        # Check the length of artists list is 2
        self.assertEqual(len(response.context['artists']), 2)


    def test_artist_search_one_search_result(self):

        response = self.client.get(reverse('artist_list'), {'search_name' : 'ACDC'} )
        self.assertNotContains(response, 'REM')
        self.assertNotContains(response, 'Yes')
        self.assertContains(response, 'ACDC')
        # Check the length of artists list is 1
        self.assertEqual(len(response.context['artists']), 1)


    def test_correct_template_used_for_artists(self):
        # Show all
        response = self.client.get(reverse('artist_list'))
        self.assertTemplateUsed(response, 'lmn/artists/artist_list.html')

        # Search with matches
        response = self.client.get(reverse('artist_list'), {'search_name' : 'ACDC'} )
        self.assertTemplateUsed(response, 'lmn/artists/artist_list.html')
        # Search no matches
        response = self.client.get(reverse('artist_list'), {'search_name' : 'Non Existant Band'})
        self.assertTemplateUsed(response, 'lmn/artists/artist_list.html')

        # Artist list for venue
        response = self.client.get(reverse('artists_at_venue', kwargs={'venue_pk':1}))
        self.assertTemplateUsed(response, 'lmn/artists/artist_list_for_venue.html')


    def test_venues_played_at_most_recent_shows_first(self):
        ''' For each artist, display a list of venues they have played shows at '''

        # Artist 1 (REM) has played at venue 2 (Turf Club) on two dates

        url = reverse('venues_for_artist', kwargs={'artist_pk':1})
        response = self.client.get(url)
        shows = list(response.context['shows'])
        show1, show2 = shows[0], shows[1]
        self.assertEqual(2, len(shows))

        self.assertEqual(show1.artist.name, 'REM')
        self.assertEqual(show1.venue.name, 'The Turf Club')

         # From the fixture, show 2's "show_date": "2017-02-02T19:30:00-06:00"
        expected_date = datetime.datetime(2017, 2, 2, 19, 30, 0, tzinfo=timezone.utc)
        self.assertEqual(show1.show_date, expected_date)

        # from the fixture, show 1's "show_date": "2017-01-02T17:30:00-00:00",
        self.assertEqual(show2.artist.name, 'REM')
        self.assertEqual(show2.venue.name, 'The Turf Club')
        expected_date = datetime.datetime(2017, 1, 2, 17, 30, 0, tzinfo=timezone.utc)
        self.assertEqual(show2.show_date, expected_date)

        # Artist 2 (ACDC) has played at venue 1 (First Ave)

        url = reverse('venues_for_artist', kwargs={'artist_pk': 2})
        response = self.client.get(url)
        shows = list(response.context['shows'])
        show1 = shows[0]
        self.assertEqual(1, len(shows))

        # This show has "show_date": "2017-01-21T21:45:00-00:00",
        self.assertEqual(show1.artist.name, 'ACDC')
        self.assertEqual(show1.venue.name, 'First Avenue')
        expected_date = datetime.datetime(2017, 1, 21, 21, 45, 0, tzinfo=timezone.utc)
        self.assertEqual(show1.show_date, expected_date)

        # Artist 3 , no shows

        url = reverse('venues_for_artist', kwargs={'artist_pk':3})
        response = self.client.get(url)
        shows = list(response.context['shows'])
        self.assertEqual(0, len(shows))



class TestVenues(TestCase):

        fixtures = ['testing_venues', 'testing_artists', 'testing_shows']

        def test_with_venues_displays_all_alphabetically(self):
            response = self.client.get(reverse('venue_list'))

            # .* matches 0 or more of any character. Test to see if
            # these names are present, in the right order

            regex = '.*First Avenue.*|.*Target Center.*|.*The Turf Club.*'
            response_text = str(response.content)
            self.assertTrue(re.search(regex, response_text))
            venues = list(response.context['venues'])
            self.assertEqual(len(venues), 3)
            self.assertTemplateUsed(response, 'lmn/venues/venue_list.html')


        def test_venue_search_clear_link(self):
            response = self.client.get( reverse('venue_list') , {'search_name' : 'Fine Line'} )

            # There is a clear link, it's url is the main venue page
            all_venues_url = reverse('venue_list')
            self.assertContains(response, all_venues_url)


        def test_venue_search_no_search_results(self):
            response = self.client.get( reverse('venue_list') , {'search_name' : 'Fine Line'} )
            self.assertNotContains(response, 'First Avenue')
            self.assertNotContains(response, 'Turf Club')
            self.assertNotContains(response, 'Target Center')
            # Check the length of venues list is 0
            self.assertEqual(len(response.context['venues']), 0)
            self.assertTemplateUsed(response, 'lmn/venues/venue_list.html')


        def test_venue_search_partial_match_search_results(self):
            response = self.client.get(reverse('venue_list'), {'search_name' : 'c'})
            # Should be two responses, Yes and REM
            self.assertNotContains(response, 'First Avenue')
            self.assertContains(response, 'Turf Club')
            self.assertContains(response, 'Target Center')
            # Check the length of venues list is 2
            self.assertEqual(len(response.context['venues']), 2)
            self.assertTemplateUsed(response, 'lmn/venues/venue_list.html')


        def test_venue_search_one_search_result(self):

            response = self.client.get(reverse('venue_list'), {'search_name' : 'Target'} )
            self.assertNotContains(response, 'First Avenue')
            self.assertNotContains(response, 'Turf Club')
            self.assertContains(response, 'Target Center')
            # Check the length of venues list is 1
            self.assertEqual(len(response.context['venues']), 1)
            self.assertTemplateUsed(response, 'lmn/venues/venue_list.html')


        def test_artists_played_at_venue_most_recent_first(self):
            # Artist 1 (REM) has played at venue 2 (Turf Club) on two dates

            url = reverse('artists_at_venue', kwargs={'venue_pk':2})
            response = self.client.get(url)
            shows = list(response.context['shows'])
            show1, show2 = shows[0], shows[1]
            self.assertEqual(2, len(shows))

            self.assertEqual(show1.artist.name, 'REM')
            self.assertEqual(show1.venue.name, 'The Turf Club')

            expected_date = datetime.datetime(2017, 2, 2, 19, 30, 0, tzinfo=timezone.utc)
            self.assertEqual(show1.show_date, expected_date)

            self.assertEqual(show2.artist.name, 'REM')
            self.assertEqual(show2.venue.name, 'The Turf Club')
            expected_date = datetime.datetime(2017, 1, 2, 17, 30, 0, tzinfo=timezone.utc)
            self.assertEqual(show2.show_date, expected_date)

            # Artist 2 (ACDC) has played at venue 1 (First Ave)

            url = reverse('artists_at_venue', kwargs={'venue_pk': 1})
            response = self.client.get(url)
            shows = list(response.context['shows'])
            show1 = shows[0]
            self.assertEqual(1, len(shows))

            self.assertEqual(show1.artist.name, 'ACDC')
            self.assertEqual(show1.venue.name, 'First Avenue')
            expected_date = datetime.datetime(2017, 1, 21, 21, 45, 0, tzinfo=timezone.utc)
            self.assertEqual(show1.show_date, expected_date)

            # Venue 3 has not had any shows

            url = reverse('artists_at_venue', kwargs={'venue_pk':3})
            response = self.client.get(url)
            shows = list(response.context['shows'])
            self.assertEqual(0, len(shows))


        def test_correct_template_used_for_venues(self):
            # Show all
            response = self.client.get(reverse('venue_list'))
            self.assertTemplateUsed(response, 'lmn/venues/venue_list.html')

            # Search with matches
            response = self.client.get(reverse('venue_list'), {'search_name' : 'First'} )
            self.assertTemplateUsed(response, 'lmn/venues/venue_list.html')
            # Search no matches
            response = self.client.get(reverse('venue_list'), {'search_name' : 'Non Existant Venue'})
            self.assertTemplateUsed(response, 'lmn/venues/venue_list.html')

            response = self.client.get(reverse('artists_at_venue', kwargs={'venue_pk':1}))
            self.assertTemplateUsed(response, 'lmn/artists/artist_list_for_venue.html')



class TestAddNoteUnauthentictedUser(TestCase):

    fixtures = [ 'testing_artists', 'testing_venues', 'testing_shows' ]  # Have to add artists and venues because of foreign key constrains in show

    def test_add_note_unauthenticated_user_redirects_to_login(self):
        response = self.client.get( '/notes/add/1/', follow=True)  # Use reverse() if you can, but not required.
        # Should redirect to login; which will then redirect to the notes/add/1 page on success.
        self.assertRedirects(response, '/accounts/login/?next=/notes/add/1/')


class TestAddNotesWhenUserLoggedIn(TestCase):
    fixtures = ['testing_users', 'testing_artists', 'testing_shows', 'testing_venues', 'testing_notes']

    def setUp(self):
        user = User.objects.first()
        self.client.force_login(user)


    def test_save_note_for_non_existent_show_is_error(self):
        new_note_url = reverse('new_note', kwargs={'show_pk':100})
        response = self.client.post(new_note_url)
        self.assertEqual(response.status_code, 404)


    def test_can_save_new_note_for_show_blank_data_is_error(self):

        initial_note_count = Note.objects.count()

        new_note_url = reverse('new_note', kwargs={'show_pk':1})

        # No post params
        response = self.client.post(new_note_url, follow=True)
        # No note saved, should show same page
        self.assertTemplateUsed('lmn/notes/new_note.html')

        # no title
        response = self.client.post(new_note_url, {'text':'blah blah' }, follow=True)
        self.assertTemplateUsed('lmn/notes/new_note.html')

        # no text
        response = self.client.post(new_note_url, {'title':'blah blah' }, follow=True)
        self.assertTemplateUsed('lmn/notes/new_note.html')

        # nothing added to database
        self.assertEqual(Note.objects.count(), initial_note_count)   # 2 test notes provided in fixture, should still be 2


    def test_add_note_database_updated_correctly(self):

        initial_note_count = Note.objects.count()

        new_note_url = reverse('new_note', kwargs={'show_pk':2})

        response = self.client.post(new_note_url, {'text':'ok', 'title':'blah blah' }, follow=True)

        # Verify note is in database
        new_note_query = Note.objects.filter(text='ok', title='blah blah')
        self.assertEqual(new_note_query.count(), 1)

        # And one more note in DB than before
        self.assertEqual(Note.objects.count(), initial_note_count + 1)


    def test_redirect_to_note_detail_after_save(self):

        initial_note_count = Note.objects.count()

        new_note_url = reverse('new_note', kwargs={'show_pk':2})
        response = self.client.post(new_note_url, {'text':'ok', 'title':'blah blah' }, follow=True)
        new_note = Note.objects.filter(text='ok', title='blah blah').first()

        self.assertRedirects(response, reverse('note_detail', kwargs={'note_pk': new_note.pk }))


class TestUserProfile(TestCase):
    fixtures = [ 'testing_users', 'testing_artists', 'testing_venues', 'testing_shows', 'testing_notes' ]  # Have to add artists and venues because of foreign key constrains in show

    # verify correct list of reviews for a user
    def test_user_profile_show_list_of_their_notes(self):
        # get user profile for user 2. Should have 2 reviews for show 1 and 2.
        response = self.client.get(reverse('user_profile', kwargs={'user_pk':2}))
        notes_expected = list(Note.objects.filter(user=2).order_by('-posted_date'))
        notes_provided = list(response.context['notes'])
        self.assertTemplateUsed('lmn/users/user_profile.html')
        self.assertEqual(notes_expected, notes_provided)

        # test notes are in date order, most recent first.
        # Note PK 3 should be first, then PK 2
        first_note = response.context['notes'][0]
        self.assertEqual(first_note.pk, 3)

        second_note = response.context['notes'][1]
        self.assertEqual(second_note.pk, 2)


    def test_user_with_no_notes(self):
        response = self.client.get(reverse('user_profile', kwargs={'user_pk':3}))
        self.assertFalse(response.context['notes'])


    def test_username_shown_on_profile_page(self):
        # A string "username's notes" is visible
        response = self.client.get(reverse('user_profile', kwargs={'user_pk':1}))
        self.assertContains(response, 'alice\'s Information')
        
        response = self.client.get(reverse('user_profile', kwargs={'user_pk':2}))
        self.assertContains(response, 'bob\'s Information')


    def test_correct_user_name_shown_different_profiles(self):
        logged_in_user = User.objects.get(pk=2)
        self.client.force_login(logged_in_user)  # bob
        response = self.client.get(reverse('user_profile', kwargs={'user_pk':2}))
        self.assertContains(response, 'You are logged in, <a href="/user/profile/2/">bob</a>')
        
        
        # Same message on another user's profile. Should still see logged in message 
        # for currently logged in user, in this case, bob
        response = self.client.get(reverse('user_profile', kwargs={'user_pk':3}))
        self.assertContains(response, 'You are logged in, <a href="/user/profile/2/">bob</a>')
        

class TestNotes(TestCase):
    fixtures = [ 'testing_users', 'testing_artists', 'testing_venues', 'testing_shows', 'testing_notes' ]  # Have to add artists and venues because of foreign key constrains in show

    def test_latest_notes(self):
        response = self.client.get(reverse('latest_notes'))
        expected_notes = list(Note.objects.all())
        # Should be note 3, then 2, then 1
        context = response.context['notes']
        first, second, third = context[0], context[1], context[2]
        self.assertEqual(first.pk, 3)
        self.assertEqual(second.pk, 2)
        self.assertEqual(third.pk, 1)


    def test_notes_for_show_view(self):
        # Verify correct list of notes shown for a Show, most recent first
        # Show 1 has 2 notes with PK = 2 (most recent) and PK = 1
        response = self.client.get(reverse('show_detail', kwargs={'show_pk':1}))
        context = response.context['notes']
        first, second = context[0], context[1]
        self.assertEqual(first.pk, 2)
        self.assertEqual(second.pk, 1)


    def test_correct_templates_uses_for_notes(self):
        response = self.client.get(reverse('latest_notes'))
        self.assertTemplateUsed(response, 'lmn/notes/note_list.html')

        response = self.client.get(reverse('note_detail', kwargs={'note_pk':1}))
        self.assertTemplateUsed(response, 'lmn/notes/note_detail.html')

        response = self.client.get(reverse('show_detail', kwargs={'show_pk':1}))
        self.assertTemplateUsed(response, 'lmn/shows/show_detail.html')

        # Log someone in
        self.client.force_login(User.objects.first())
        response = self.client.get(reverse('new_note', kwargs={'show_pk':1}))
        self.assertTemplateUsed(response, 'lmn/notes/new_note.html')


class TestUserNotes(TestCase):

    fixtures = [ 'testing_users', 'testing_artists', 'testing_venues', 'testing_shows', 'testing_notes' ]

    def test_delete_own_note(self):
        self.client.force_login(User.objects.first())
        response = self.client.post(reverse('delete_note', args=(1,)), follow=True)
        self.assertEqual(200, response.status_code)
        note_1 = Note.objects.filter(pk=1).first()
        self.assertIsNone(note_1)   


    def test_delete_someone_else_note(self):
        self.client.force_login(User.objects.first())
        response = self.client.post(reverse('delete_note',  args=(2,)), follow=True)
        self.assertEqual(403, response.status_code)
        note_2 = Note.objects.get(pk=2)
        self.assertIsNotNone(note_2)   


class TestUserAuthentication(TestCase):

    ''' Some aspects of registration (e.g. missing data, duplicate username) covered in test_forms '''
    ''' Currently using much of Django's built-in login and registration system'''

    def test_user_registration_logs_user_in(self):
        response = self.client.post(reverse('register'), {'username':'sam12345', 'email':'sam@sam.com', 'password1':'feRpj4w4pso3az', 'password2':'feRpj4w4pso3az', 'first_name':'sam', 'last_name' : 'sam'}, follow=True)

        # Assert user is logged in - one way to do it...
        user = auth.get_user(self.client)
        self.assertEqual(user.username, 'sam12345')

        # This works too. Don't need both tests, added this one for reference.
        # sam12345 = User.objects.filter(username='sam12345').first()
        # auth_user_id = int(self.client.session['_auth_user_id'])
        # self.assertEqual(auth_user_id, sam12345.pk)


    def test_user_registration_redirects_to_correct_page(self):
        # TODO If user is browsing site, then registers, once they have registered, they should
        # be redirected to the last page they were at, not the homepage.
        response = self.client.post(reverse('register'), {'username':'sam12345', 'email':'sam@sam.com', 'password1':'feRpj4w4pso3az@1!2', 'password2':'feRpj4w4pso3az@1!2', 'first_name':'sam', 'last_name' : 'sam'}, follow=True)
        new_user = authenticate(username='sam12345', password='feRpj4w4pso3az@1!2')
        self.assertRedirects(response, reverse('user_profile', kwargs={"user_pk": new_user.pk}))   
        self.assertContains(response, 'sam12345')  # page has user's name on it


class TestImageUpload(TestCase):

    fixtures = [ 'testing_users', 'testing_artists', 'testing_venues', 'testing_shows', 'testing_notes' ]

    def setUp(self):
        user = User.objects.get(pk=1)
        self.client.force_login(user)
        self.MEDIA_ROOT = tempfile.mkdtemp()


    def create_temp_image_file(self):
        handle, tmp_img_file = tempfile.mkstemp(suffix='.jpg')
        img = Image.new('RGB', (10, 10) )
        img.save(tmp_img_file, format='JPEG')
        return tmp_img_file


    def test_upload_new_image_for_own_note(self):
        
        img_file_path = self.create_temp_image_file()

        with self.settings(MEDIA_ROOT=self.MEDIA_ROOT):
        
            with open(img_file_path, 'rb') as img_file:

                resp = self.client.post(reverse('edit_note', kwargs={'note_pk': 1} ), 
                       {'image': img_file, 
                        'title': 'Hello', 
                        'text': 'Yo'}, 
                       follow=True)

                self.assertEqual(200, resp.status_code)

                note_1 = Note.objects.get(pk=1)
                img_file_name = os.path.basename(img_file_path)
                expected_uploaded_file_path = os.path.join(self.MEDIA_ROOT, 'user_images', img_file_name)

                self.assertTrue(os.path.exists(expected_uploaded_file_path))
                self.assertIsNotNone(note_1.image)
                self.assertTrue(filecmp.cmp( img_file_path,  expected_uploaded_file_path ))


    def test_change_image_for_own_note_expect_old_deleted(self):
        
        first_img_file_path = self.create_temp_image_file()
        second_img_file_path = self.create_temp_image_file()

        with self.settings(MEDIA_ROOT=self.MEDIA_ROOT):
        
            with open(first_img_file_path, 'rb') as first_img_file:

                resp = self.client.post(reverse('edit_note', kwargs={'note_pk': 1} ), 
                       {'image': first_img_file, 
                        'title': 'Hello', 
                        'text': 'Yo'}, 
                       follow=True)

                note_1 = Note.objects.get(pk=1)

                first_uploaded_image = note_1.image.name

                with open(second_img_file_path, 'rb') as second_img_file:
                    resp = self.client.post(reverse('edit_note', kwargs={'note_pk': 1} ), 
                           {'image': second_img_file, 
                            'title': 'Hello', 
                            'text': 'Yo'}, 
                           follow=True)

                    note_1 = Note.objects.get(pk=1)

                    second_uploaded_image = note_1.image.name

                    first_path = os.path.join('lmn', self.MEDIA_ROOT, first_uploaded_image)
                    second_path = os.path.join('lmn', self.MEDIA_ROOT, second_uploaded_image)

                    self.assertFalse(os.path.exists(first_path))
                    self.assertTrue(os.path.exists(second_path))


    def test_upload_image_for_someone_else_note(self):

        with self.settings(MEDIA_ROOT=self.MEDIA_ROOT):
  
            img_file = self.create_temp_image_file()
            with open(img_file, 'rb') as image:
                resp = self.client.post(reverse('edit_note', kwargs={'note_pk': 2} ), 
                       {'image': img_file, 
                        'title': 'Hello', 
                        'text': 'Yo'}, 
                       follow=True)
                self.assertEqual(403, resp.status_code)

                note_2 = Note.objects.get(pk=2)
                self.assertFalse(note_2.image)  


    def test_delete_note_with_image_image_deleted(self):
        
        img_file_path = self.create_temp_image_file()

        with self.settings(MEDIA_ROOT=self.MEDIA_ROOT):
        
            with open(img_file_path, 'rb') as img_file:
                resp = self.client.post(reverse('edit_note', kwargs={'note_pk': 1} ), 
                       {'image': img_file, 
                        'title': 'Hello', 
                        'text': 'Yo'}, 
                       follow=True)
                
                self.assertEqual(200, resp.status_code)

                note_1 = Note.objects.get(pk=1)
                img_file_name = os.path.basename(img_file_path)
                
                uploaded_file_path = os.path.join(self.MEDIA_ROOT, 'user_images', img_file_name)

                note_1 = Note.objects.get(pk=1)
                note_1.delete()

                self.assertFalse(os.path.exists(uploaded_file_path))


class TestShowRatings(TestCase):

    fixtures = [ 'testing_users', 'testing_artists', 'testing_venues', 'testing_shows']

    def setUp(self):
        user = User.objects.get(pk=1)
        self.client.force_login(user)


    def test_add_rating_rating_exists_in_database(self):

        initial_rating_count = ShowRating.objects.count()
        new_rating_url = reverse('save_show_rating', kwargs={'show_pk':1})
        response = self.client.post(new_rating_url, {'rating_out_of_five': 3}, follow=True)
        new_rating_query = ShowRating.objects.filter(rating_out_of_five=3)

        self.assertEqual(new_rating_query.count(), 1)
        self.assertEqual(ShowRating.objects.count(), initial_rating_count + 1)
        self.assertEqual(response.status_code, 200)


    def test_add_blank_rating_rating_not_saved(self):

        initial_rating_count = ShowRating.objects.count()
        new_rating_url = reverse('save_show_rating', kwargs={'show_pk':1})

        with self.assertRaises(ValueError):
            with transaction.atomic():
                response = self.client.post(new_rating_url, {'rating_out_of_five': ''}, follow=True)

        self.assertEqual(ShowRating.objects.count(), initial_rating_count)


    def test_add_string_rating_rating_not_saved(self):

        initial_rating_count = ShowRating.objects.count()
        new_rating_url = reverse('save_show_rating', kwargs={'show_pk':1})
        

        with self.assertRaises(ValidationError) as ve:
            response = self.client.post(new_rating_url, {'rating_out_of_five': 'five out of five'}, follow=True)   

        self.assertEqual(ShowRating.objects.count(), initial_rating_count)


    def test_add_rating_below_1_rating_not_saved(self):

        initial_rating_count = ShowRating.objects.count()
        new_rating_url = reverse('save_show_rating', kwargs={'show_pk':1})

        # test invalid rating
        with self.assertRaises(ValidationError) as ve:
            response = self.client.post(new_rating_url, {'rating_out_of_five': 0}, follow=True)

        new_invalid_rating_query = ShowRating.objects.filter(rating_out_of_five=0)

        self.assertEqual(new_invalid_rating_query.count(), 0)
        self.assertEqual(ShowRating.objects.count(), initial_rating_count)
        
        # test valid rating
        response = self.client.post(new_rating_url, {'rating_out_of_five': 1}, follow=True)
        new_valid_rating_query = ShowRating.objects.filter(rating_out_of_five=1)

        self.assertEqual(new_valid_rating_query.count(), 1)
        self.assertEqual(ShowRating.objects.count(), initial_rating_count + 1)
        self.assertEqual(response.status_code, 200)



    def test_add_rating_above_5_rating_not_saved(self):

        initial_rating_count = ShowRating.objects.count()
        new_rating_url = reverse('save_show_rating', kwargs={'show_pk':1})

        # test invalid rating
        with self.assertRaises(ValidationError) as ve:
            response = self.client.post(new_rating_url, {'rating_out_of_five': 6}, follow=True)

        new_invalid_rating_query = ShowRating.objects.filter(rating_out_of_five=6)

        self.assertEqual(new_invalid_rating_query.count(), 0)   
        self.assertEqual(ShowRating.objects.count(), initial_rating_count)

        # test valid rating
        # test valid rating
        response = self.client.post(new_rating_url, {'rating_out_of_five': 5}, follow=True)
        new_valid_rating_query = ShowRating.objects.filter(rating_out_of_five=5)

        self.assertEqual(new_valid_rating_query.count(), 1)
        self.assertEqual(ShowRating.objects.count(), initial_rating_count + 1)
        self.assertEqual(response.status_code, 200)


    def test_user_can_only_rate_each_show_once(self):

        initial_rating_count = ShowRating.objects.count()
        new_rating_url = reverse('save_show_rating', kwargs={'show_pk':1})

        # test valid first rating
        response = self.client.post(new_rating_url, {'rating_out_of_five': 3}, follow=True)
        first_rating_query = ShowRating.objects.filter(rating_out_of_five=3)

        self.assertEqual(first_rating_query.count(), 1)
        self.assertEqual(ShowRating.objects.count(), initial_rating_count + 1)
        self.assertEqual(response.status_code, 200)

        # test invalid second rating
        with self.assertRaises(IntegrityError):
            with transaction.atomic():

                response = self.client.post(new_rating_url, {'rating_out_of_five': 2}, follow=True) 
                second_rating_query = ShowRating.objects.filter(rating_out_of_five=2)

                self.assertEqual(second_rating_query.count(), 0)
                self.assertEqual(ShowRating.objects.count(), initial_rating_count + 1)
                self.assertEqual(response.status_code, 200)


    def test_two_users_can_rate_same_show(self):

        initial_rating_count = ShowRating.objects.count()
        new_rating_url = reverse('save_show_rating', kwargs={'show_pk':1})

        # test first user
        response = self.client.post(new_rating_url, {'rating_out_of_five': 3}, follow=True)
        first_user_rating_query = ShowRating.objects.filter(rating_out_of_five=3)

        self.assertEqual(first_user_rating_query.count(), 1)
        self.assertEqual(ShowRating.objects.count(), initial_rating_count + 1)
        self.assertContains(response, 'alice')
        self.assertEqual(response.status_code, 200)

        # login second user
        user = User.objects.get(pk=2)
        self.client.force_login(user)

        response = self.client.post(new_rating_url, {'rating_out_of_five': 2}, follow=True)
        second_user_rating_query = ShowRating.objects.filter(rating_out_of_five=2)

        self.assertContains(response, 'bob')
        self.assertEqual(second_user_rating_query.count(), 1)
        self.assertEqual(ShowRating.objects.count(), initial_rating_count + 2)
        self.assertEqual(response.status_code, 200)

    
    def test_user_already_rated_show_message(self):

        initial_rating_count = ShowRating.objects.count()
        new_rating_url = reverse('save_show_rating', kwargs={'show_pk':1})
        
        response = self.client.get(reverse('show_detail', kwargs={'show_pk':1}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'You\'ve already rated this show.')

        response = self.client.post(new_rating_url, {'rating_out_of_five': 3}, follow=True)
        self.assertEqual(response.status_code, 200)
        first_rating_query = ShowRating.objects.filter(rating_out_of_five=3)

        response = self.client.get(reverse('show_detail', kwargs={'show_pk':1}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'You\'ve already rated this show.')

        # test new user - already rated message should not be shown
        user = User.objects.get(pk=2)
        self.client.force_login(user)

        response = self.client.get(reverse('show_detail', kwargs={'show_pk':1}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'You\'ve already rated this show.')


    def test_rate_show_in_show_detail_message_displayed_in_new_note(self):

        initial_rating_count = ShowRating.objects.count()
        new_rating_url = reverse('save_show_rating', kwargs={'show_pk':1})

        # user already rated show message should not display before show is rated
        response = self.client.get(reverse('new_note', kwargs={'show_pk':1}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'You\'ve already rated this show.')

        # rate show on show detail page
        response = self.client.post(new_rating_url, {'rating_out_of_five': 3}, follow=True)
        new_rating_query = ShowRating.objects.filter(rating_out_of_five=3)

        # rating is saved in database
        self.assertEqual(new_rating_query.count(), 1)
        self.assertEqual(ShowRating.objects.count(), initial_rating_count + 1)

        # user already rated show message should be displayed when created a new note for that show
        response = self.client.get(reverse('new_note', kwargs={'show_pk':1}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'You\'ve already rated this show.')


class TestRateShowsInNotes(TestCase):

    fixtures = [ 'testing_users', 'testing_artists', 'testing_venues', 'testing_shows']

    def setUp(self):
        user = User.objects.get(pk=1)
        self.client.force_login(user)


    def test_create_note_without_rating_rating_not_saved(self):

        initial_note_count = Note.objects.count()
        initial_rating_count = ShowRating.objects.count()

        new_note_url = reverse('new_note', kwargs={'show_pk':1})

        response = self.client.post(new_note_url, {'text':'ok', 'title':'blah blah' }, follow=True)

        # Verify note is in database
        new_note_query = Note.objects.filter(text='ok', title='blah blah')  

        self.assertEqual(new_note_query.count(), 1)
        self.assertEqual(Note.objects.count(), initial_note_count + 1)
        self.assertEqual(response.status_code, 200)

        # Verify no new ratings in the database
        self.assertEqual(ShowRating.objects.count(), initial_rating_count)


    def test_create_note_with_rating_both_saved(self):

        initial_note_count = Note.objects.count()
        initial_rating_count = ShowRating.objects.count()

        new_note_url = reverse('new_note', kwargs={'show_pk':1})
        response = self.client.post(new_note_url, {'text':'ok', 'title':'blah blah', 'rating_out_of_five': 4}, follow=True)

        # Verify note is in database
        new_note_query = Note.objects.filter(text='ok', title='blah blah')
        self.assertEqual(new_note_query.count(), 1)
        self.assertEqual(response.status_code, 200)

        # Verify rating is in database
        new_rating_query = ShowRating.objects.filter(rating_out_of_five=4)
        self.assertEqual(new_rating_query.count(), 1)
        self.assertEqual(Note.objects.count(), initial_note_count + 1)
        self.assertEqual(ShowRating.objects.count(), initial_rating_count + 1)


    def test_rate_show_in_new_note_message_displayed_in_show_detail(self):
        
        initial_rating_count = ShowRating.objects.count()
        new_rating_url = reverse('new_note', kwargs={'show_pk':1})

        # user already rated show message should not display before show is rated
        response = self.client.get(reverse('show_detail', kwargs={'show_pk':1}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'You\'ve already rated this show.')

        # rate show on show detail page
        response = self.client.post(new_rating_url, {'text':'ok', 'title':'blah blah', 'rating_out_of_five':4}, follow=True)
        new_rating_query = ShowRating.objects.filter(rating_out_of_five=4)

        # rating is saved in database
        self.assertEqual(new_rating_query.count(), 1)
        self.assertEqual(ShowRating.objects.count(), initial_rating_count + 1)

        # user already rated show message should be displayed when created a new note for that show
        response = self.client.get(reverse('new_note', kwargs={'show_pk':1}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'You\'ve already rated this show.')


class TestBadges(TestCase):

    fixtures = [ 'testing_users', 'testing_artists', 'testing_venues', 'testing_shows', 'testing_badges']

    def setUp(self):
        user = User.objects.get(pk=1)
        self.client.force_login(user)


    def test_add_note_badge_awarded_appropriately(self):
        new_note_url = reverse('new_note', kwargs={'show_pk':1})
        response = self.client.post(new_note_url, {'text':'ok', 'title':'blah blah' }, follow=True)
        self.assertEqual(response.status_code, 200)

        user = response.context['user']
        user_profile = user.profile
        user_badges = user_profile.badges.count()
        
        self.assertEqual(user_badges, 1)

        new_note_url = reverse('new_note', kwargs={'show_pk':2})
        response = self.client.post(new_note_url, {'text':'ok', 'title':'blah blah' }, follow=True)
        self.assertEqual(response.status_code, 200)

        user = response.context['user']
        user_profile = user.profile
        user_badges = user_profile.badges.count()
        
        self.assertEqual(user_badges, 2)


    def test_add_note_number_shouldnt_get_badge_badge_not_applied(self):
        
        # Add 3 notes, should only have 2 badges
        new_note_url = reverse('new_note', kwargs={'show_pk':1})
        response = self.client.post(new_note_url, {'text':'ok', 'title':'blah blah' }, follow=True)
        self.assertEqual(response.status_code, 200)
        new_note_url = reverse('new_note', kwargs={'show_pk':2})
        response = self.client.post(new_note_url, {'text':'ok', 'title':'blah blah' }, follow=True)
        self.assertEqual(response.status_code, 200)
        new_note_url = reverse('new_note', kwargs={'show_pk':3})
        response = self.client.post(new_note_url, {'text':'ok', 'title':'blah blah' }, follow=True)
        self.assertEqual(response.status_code, 200)

        user = response.context['user']
        user_profile = user.profile
        user_badges = user_profile.badges.count()
        
        self.assertEqual(user_badges, 2)






