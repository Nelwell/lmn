from django.shortcuts import render, redirect, get_object_or_404

from ..models import Venue, Artist, Note, Show, Profile, ShowRating
from ..forms import VenueSearchForm, NewNoteForm, ArtistSearchForm, UserRegistrationForm, NewShowRatingForm

from django.db.models import Avg, Count, Min, Sum
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseForbidden
from django.core.paginator import EmptyPage, Paginator, PageNotAnInteger, EmptyPage
from django.db.utils import IntegrityError
from django.db import transaction



@login_required
def new_note(request, show_pk):

    show = get_object_or_404(Show, pk=show_pk)

    if request.method == 'POST':
        note_form = NewNoteForm(request.POST, request.FILES)
        rating_form = NewShowRatingForm(request.POST)

        if rating_form.is_valid(): # Form can be empty and still valid, but the database doesn't allow nulls
            try:
                with transaction.atomic():
                    rating = rating_form.save(commit=False)
                    rating.user = request.user
                    rating.show = show
                    rating.save()
            except IntegrityError as e: # If the user creates a note without a rating, the db NOT NULL constraint will fail
                print(e)                # This is the intended behavior

        if note_form.is_valid(): # Note form must not be blank to be valid
            note = note_form.save(commit=False)
            note.user = request.user
            note.show = show
            note.save()

            return redirect('note_detail', note_pk=note.pk)

    else:
        note_form = NewNoteForm()
        user_rating = ShowRating.objects.filter(show=show, user=request.user).first()

        if user_rating: # user can only have 1 rating per show, if they've already rated it, do not show rating form
            rating_form = None
        else:
            rating_form = NewShowRatingForm()

    return render(request, 'lmn/notes/new_note.html' , { 'note_form': note_form, 'rating_form': rating_form, 'show': show })


def latest_notes(request):
    notes = Note.objects.all().order_by('-posted_date')[:100]   # the 100 most recent notes

    paginator = Paginator(notes, 10) # allows only 10 artists to be viewed per page

    if request.GET.get('page'):
        page = int(request.GET.get('page'))
    else:
        page = None

    try:
        notes = paginator.page(page)
    except PageNotAnInteger:
        notes = paginator.page(1)
        page = 1
    except EmptyPage:
        notes = paginator.page(paginator.num_pages)
        page = paginator.num_pages

    return render(request, 'lmn/notes/note_list.html', {'notes' : notes, 
                  'page_range': paginator.page_range, 'num_pages' : paginator.num_pages, 
                  'current_page': page})

def most_notes(request):
    shows = Show.objects.annotate(num_notes=Count('note')).order_by('-num_notes')[:10]
    # top 10 shows with most notes
    return render(request, 'lmn/notes/most_notes.html', {'shows': shows })  

def note_detail(request, note_pk):
    note = get_object_or_404(Note, pk=note_pk)

    if request.user.is_authenticated:
        rating_model = ShowRating.objects.filter(show=note.show, user=request.user).first()

        if rating_model:
            rating = rating_model.rating_out_of_five
        else:
            rating = None

    else:
        rating = None
    
    return render(request, 'lmn/notes/note_detail.html' , { 'note': note, 'rating': rating })


@login_required    
def edit_note(request, note_pk):
    note = get_object_or_404(Note, pk=note_pk)

    if note.user != request.user: # return an error if a user attempts to edit a note that doesn't belong to them
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = NewNoteForm(request.POST, request.FILES, instance=note)

        if form.is_valid(): # if all fields are filled out correctly, save the contents of the form to database
            form.save()

        return redirect('note_detail', note_pk=note_pk)

    else: # this displays the place details if the request method is 'GET' instead of 'POST'
        review_form = NewNoteForm(instance=note) # reuse NewNoteForm for editing notes.
        return render(request, 'lmn/notes/edit_note.html', {'note': note, 'review_form': review_form})
        

@login_required
def delete_note(request, note_pk):
    note = get_object_or_404(Note, pk=note_pk)

    if note.user == request.user:
        note.delete()
        return redirect('user_profile', user_pk=note.user.pk) # redirects to the user's profile after deleting
    else:
        return HttpResponseForbidden()
