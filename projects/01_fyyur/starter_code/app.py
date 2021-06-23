#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
from os import name
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import sys
from flask_migrate import Migrate

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

from models import *

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  if isinstance(value, str):
      date = dateutil.parser.parse(value)
  else:
      date = value 
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  
  data=[]
  cities= Venue.query.with_entities(Venue.city, Venue.state).group_by(Venue.city,  Venue.state).all()
  num_shows= 0

  for city in cities: 
    venues= Venue.query.filter_by(city=city.city).filter_by(state=city.state).all()
    city_venues=[]

    for venue in venues:

      curr_time= datetime.now().strftime('%Y-%m-%d %H:%M:%S')
      up_coming_shows= db.session.query(Show).filter(Show.start_time> curr_time).all()
      for show in up_coming_shows: 
        if show.venue_id == venue.id: 
          num_shows += 1
      city_venues.append({
          "id": venue.id,
          "name": venue.name,
          "num_upcoming_shows": num_shows
        })

    data.append({
      "city": city.city, 
      "state": city.state, 
      "venues": city_venues
    })

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():

  response= []
  venues= []
  num_result=0
  num_shows= 0
  search_term= request.form.get('search_term')
  result= Venue.query.filter(Venue.name.ilike('%' +search_term+ '%')).all()

  for venue in result: 
    num_result += 1

    curr_time= datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    up_coming_shows= db.session.query(Show).filter(Show.start_time> curr_time).all()
    for show in up_coming_shows: 
      if show.venue_id == venue.id: 
        num_shows += 1

    venues.append({
      "id": venue.id, 
      "name": venue.name, 
      "num_upcoming_shows": num_shows
    })

  response={
    "count": num_result,
    "data": venues
  }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  data=[]
  past_list=[]
  upcoming_list=[]
  upcoming_num=0
  past_num=0
  i=0
  venue= Venue.query.get(venue_id)

  if venue: 
    genres= (venue.genres).split(",")
    for genre in genres: 
      genre= genre.replace('}', '')
      genre= genre.replace('{', '')
      genre= genre.translate({ord('\"'): None})
      genres[i]= genre
      i += 1; 

  #------shows count--------#
    curr_time= datetime.now()
    #.strftime('%Y-%m-%d %H:%M:%S')
    upcoming_shows= Show.query.options(db.joinedload(Show.venue)).filter(Show.venue_id == venue_id).filter(Show.start_time > curr_time).all()
    past_shows= Show.query.options(db.joinedload(Show.venue)).filter(Show.venue_id == venue_id).filter(Show.start_time < curr_time).all()

    for show in upcoming_shows: 
      upcoming_num += 1
      artist= Artist.query.get(show.artist_id)
      image= artist.image_link
      upcoming_list.append({
        "artist_id": artist.id,
        "artist_name": artist.name,
        "artist_image_link": image ,
        "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      })

    for show in past_shows: 
      past_num += 1
      artist= Artist.query.get(show.artist_id)
      past_list.append({
        "artist_id": artist.id,
        "artist_name": artist.name,
        "artist_image_link": artist.image_link,
        "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      })

  #-------data fill---------#
    data= {
      "id": venue.id, 
      "name": venue.name,
      "city": venue.city,
      "state": venue.state,
      "address": venue.address,
      "phone": venue.phone,
      "genres": genres,
      "facebook_link": venue.facebook_link,
      "image_link": venue.image_link,
      "website":  venue.website_link,
      "seeking_talent": venue.seeking_talent,
      "seeking_description": venue.seeking_description,
      "past_shows": past_list,
      "upcoming_shows": upcoming_list,
      "past_shows_count": past_num,
      "upcoming_shows_count": upcoming_num
    }

  else: 
    return render_template('errors/404.html')

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error= False
  
  try: 
    venue= Venue()
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.phone = request.form['phone']
    venue.address = request.form['address']
    venue.genres = request.form.getlist('genres')
    venue.facebook_link = request.form['facebook_link']
    venue.image_link = request.form['image_link']
    venue.website_link = request.form['website_link'] 
    venue.seeking_talent= True if 'seeking_talent' in request.form else False

    venue.seeking_description= request.form['seeking_description']
    
    db.session.add(venue)
    db.session.commit()
  except:
    db.session.rollback()
    error=True
  

  # on successful db insert, flash success
  if error: 
    error_string = str(error)
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.') 

  if not error:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/

  db.session.close()

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
 
  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data=[]
  artists= Artist.query.all()
  for artist in artists: 
    data.append({
      "id": artist.id, 
      "name": artist.name
    })
  
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
 
  response= []
  artists= []
  num_result=0
  num_shows= 0
  search_term= request.form.get('search_term')
  result= Artist.query.filter(Artist.name.ilike('%' +search_term+ '%')).all()

  for artist in result: 
    num_result += 1

    curr_time= datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    up_coming_shows= db.session.query(Show).filter(Show.start_time> curr_time).all()
    for show in up_coming_shows: 
      if show.artist_id == artist.id: 
        num_shows += 1

    artists.append({
      "id": artist.id, 
      "name": artist.name, 
      "num_upcoming_shows": num_shows
    })

  response={
    "count": num_result,
    "data": artists
  }
  
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
 

  data=[]
  past_list=[]
  upcoming_list=[]
  upcoming_num=0
  past_num=0
  i=0
  artist= Artist.query.get(artist_id)

  if artist:     

    genres= (artist.genres).split(",")
    for genre in genres: 
      genre= genre.replace('}', '')
      genre= genre.replace('{', '')
      genre= genre.translate({ord('\"'): None})
      genres[i]= genre
      i += 1

  #------shows count--------#
    curr_time= datetime.now()
    upcoming_shows= Show.query.options(db.joinedload(Show.artist)).filter(Show.artist_id == artist_id).filter(Show.start_time > curr_time).all()
    past_shows= Show.query.options(db.joinedload(Show.artist)).filter(Show.artist_id == artist_id).filter(Show.start_time < curr_time).all()

    for show in upcoming_shows: 
      upcoming_num += 1
      venue= Venue.query.get(show.venue_id)
      upcoming_list.append({
        "venue_id": venue.id,
        "venue_name": venue.name,
        "venue_image_link": venue.image_link ,
        "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      })

    for show in past_shows: 
      past_num += 1
      venue= Venue.query.get(show.venue_id)
      past_list.append({
        "venue_id": venue.id,
        "venue_name": venue.name,
        "venue_image_link": venue.image_link ,
        "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      })

  #-------data fill---------#
    data= {
      "id": artist.id, 
      "name": artist.name,
      "city": artist.city,
      "state": artist.state,
      # "address": venue.address,
      "phone": artist.phone,
      "genres": genres,
      "facebook_link": artist.facebook_link,
      "image_link": artist.image_link,
      "website":  artist.website_link,
      "seeking_venue": artist.seeking_venue,
      "seeking_description": artist.seeking_description,
      "past_shows": past_list,
      "upcoming_shows": upcoming_list,
      "past_shows_count": past_num,
      "upcoming_shows_count": upcoming_num
    }

  else: 
    return render_template('errors/404.html')

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist= Artist.query.get(artist_id)

  if artist: 
    form.name.data = artist.name
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.genres.data = artist.genres
    form.facebook_link.data = artist.facebook_link
    form.image_link.data = artist.image_link
    form.website_link.data = artist.website_link
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_description
  
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
 
  error = False  
  artist = Artist.query.get(artist_id)
  try: 
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.genres = request.form.getlist('genres')
    artist.image_link = request.form['image_link']
    artist.facebook_link = request.form['facebook_link']
    artist.website_link = request.form['website_link']
    artist.seeking_venue = True if 'seeking_venue' in request.form else False 
    artist.seeking_description = request.form['seeking_description']

    db.session.commit()
  except: 
    error = True
    db.session.rollback()
  

  if error: 
    flash('An error has occurred. could not update the Artist <strong>'+ artist.name +'<\strong>.')
  if not error: 
    flash(artist.name + ' has been successfully updated!')

  db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue= Venue.query.get(venue_id)

  if venue: 
    form.name.data = venue.name
    form.city.data = venue.city
    form.state.data = venue.state
    form.address.data= venue.address
    form.phone.data = venue.phone
    form.genres.data = venue.genres
    form.facebook_link.data = venue.facebook_link
    form.image_link.data = venue.image_link
    form.website_link.data = venue.website_link
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description
  

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
 
  error = False  
  venue = Venue.query.get(venue_id)

  try: 
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']    
    venue.phone = request.form['phone']
    venue.genres = request.form.getlist('genres')
    venue.image_link = request.form['image_link']
    venue.facebook_link = request.form['facebook_link']
    venue.website_link = request.form['website_link']
    venue.seeking_talent = True if 'seeking_talent' in request.form else False 
    venue.seeking_description = request.form['seeking_description']
    db.session.commit()

  except: 
    error = True
    db.session.rollback()
 
  if error: 
    flash('An error has occurred. could not update the Venue <strong>'+ venue.name +'<\strong>.')
  if not error: 
    flash(venue.name + ' has been successfully updated!')
  
  db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  
  error= False

  try: 
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    fb_link = request.form['facebook_link']
    img_link = request.form['image_link']
    website_link = request.form['website_link']

    looking_for_venues= True if 'seeking_venue' in request.form else False 
    seeking_desc= request.form['seeking_description']

    artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres, facebook_link=fb_link, image_link=img_link, website_link=website_link, seeking_venue= looking_for_venues, seeking_description= seeking_desc)
    db.session.add(artist)
    db.session.commit()
  except:
    db.session.rollback()
    error=True


  if error: 
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.') 

  # on successful db insert, flash success  
  if not error:
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  
  db.session.close()
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  
  data=[]
  shows= Show.query.all()
  for show in shows: 
    venue= Venue.query.get(show.venue_id)
    artist= Artist.query.get(show.artist_id)

    data.append({
      "venue_id": venue.id,
      "venue_name": venue.name,
      "artist_id": artist.id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  error= False

  try: 
    artist_id = request.form['artist_id']
    venue_id = request.form['venue_id']
    start_time = request.form['start_time']
  
    show = Show(artist_id= artist_id, venue_id= venue_id, start_time= start_time); 

    db.session.add(show)
    db.session.commit()
  except:
    db.session.rollback()
    error=True
  

  db.session.close()
  # on successful db insert, flash success
  if not error:
    flash('Show was successfully listed!')
  if error: 
    flash('An error occurred. Show could not be listed.') 
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
