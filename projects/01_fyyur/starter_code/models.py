from sqlalchemy.orm import backref

from app import db


class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    genres= db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_talent= db.Column(db.Boolean, nullable= True, default= False)
    seeking_description= db.Column(db.String, nullable= True)

    shows = db.relationship('Show', cascade="all,delete", backref= 'venue')
    # TODO: implement any missing fields, as a database migration using Flask-Migrate xxxxxxxxx

class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    website_link = db.Column(db.String(120))
    seeking_venue= db.Column(db.Boolean, nullable= True, default= False)
    seeking_desciption= db.Column(db.String, nullable= True)

    shows = db.relationship('Show', cascade="all,delete", backref= 'artist')
    # TODO: implement any missing fields, as a database migration using Flask-Migrate xxxxxxxxxxx



# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.


class Show(db.Model):
    __tablename__ = 'show'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'))
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'))
    start_time = db.Column(db.DateTime, nullable=False)


    # TODO: implement any missing fields, as a database migration using Flask-Migrate xxxxxxxxx
