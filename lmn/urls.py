from django.urls import path
from django.contrib.auth import views as auth_views

from . import views
from .views import views_main, views_artists, views_venues, views_notes, views_users, views_shows


# app_name = 'lmn'

urlpatterns = [

    path('', views_main.homepage, name='homepage'),

    # Venue-related
    path('venues/list/', views_venues.venue_list, name='venue_list'),
    path('venues/detail/<int:venue_pk>/', views_venues.venue_detail, name='venue_detail'),
    path('venues/artists_at/<int:venue_pk>/', views_venues.artists_at_venue, name='artists_at_venue'),

    # Note related
    path('notes/latest/', views_notes.latest_notes, name='latest_notes'),
    path('notes/detail/<int:note_pk>/', views_notes.note_detail, name='note_detail'),
    path('notes/add/<int:show_pk>/', views_notes.new_note, name='new_note'),
    path('notes/edit/<int:note_pk>/', views_notes.edit_note, name='edit_note'),
    path('notes/delete/<int:note_pk>/', views_notes.delete_note, name='delete_note'),
    path('notes/most_notes/', views_notes.most_notes, name='most_notes'),

    # Artist related
    path('artists/list/', views_artists.artist_list, name='artist_list'),
    path('artists/detail/<int:artist_pk>/', views_artists.artist_detail, name='artist_detail'),
    path('artists/venues_played/<int:artist_pk>/', views_artists.venues_for_artist, name='venues_for_artist'),

    # Show related
    path('shows/rate/<int:show_pk>/', views_shows.save_show_rating, name='save_show_rating'),
    path('shows/detail/<int:show_pk>/', views_shows.show_detail, name='show_detail'),

    # User related
    path('user/profile/<int:user_pk>/', views_users.user_profile, name='user_profile'),
    path('user/profile/edit/<int:user_pk>/', views_users.edit_user, name='edit_user'),
    path('user/profile/me/', views_users.my_user_profile, name='my_user_profile'),

    # Account related
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(template_name='registration/logout.html'), name='logout'),
    path('register/', views_users.register, name='register'),

]
