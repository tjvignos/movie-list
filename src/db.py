from flask_sqlalchemy import SQLAlchemy
import base64
import boto3
import datetime
import io
from io import BytesIO
from mimetypes import guess_extension, guess_type
import os
import random
import re
import string
import hashlib
import bcrypt

db = SQLAlchemy()

watch_list_table = db.Table(
    "watch list table",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("movie_id", db.Integer, db.ForeignKey("movie.id"))
)

watched_list_table = db.Table(
    "watched list table",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("movie_id", db.Integer, db.ForeignKey("movie.id"))
)

class User(db.Model):
    """
    user model
    """
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # user info
    username = db.Column(db.String, nullable=False, unique=True)
    password_digest = db.Column(db.String, nullable=False)
    
    # session information
    session_token = db.Column(db.String, nullable=False, unique=True)
    session_expiration = db.Column(db.DateTime, nullable=False)
    update_token = db.Column(db.String, nullable=False, unique=True)

    # lists
    watch_list = db.relationship("Movie", secondary=watch_list_table)
    watched_list = db.relationship("Movie", secondary=watched_list_table)

    def __init__(self, **kwargs):
        """
        initializes a user object
        """
        self.username = kwargs.get("username")
        self.password_digest = bcrypt.hashpw(kwargs.get("password").encode("utf8"), bcrypt.gensalt(rounds=13))
        self.renew_session()

    def _urlsafe_base_64(self):
        """
        randomly generates hashed tokens (used for session/update tokens)
        """
        return hashlib.sha1(os.urandom(64)).hexdigest()

    def renew_session(self):
        """
        renews the sessions, i.e.
        1. creates a new session token
        2. sets the expiration time of the session to be a day from now
        3. creates a new update token
        """
        self.session_token = self._urlsafe_base_64()
        self.session_expiration = datetime.datetime.now() + datetime.timedelta(days=1)
        self.update_token = self._urlsafe_base_64()

    def verify_password(self, password):
        """
        verifies the password of a user
        """
        return bcrypt.checkpw(password.encode("utf8"), self.password_digest)

    def verify_session_token(self, session_token):
        """
        verifies the session token of a user
        """
        return session_token == self.session_token and datetime.datetime.now() < self.session_expiration

    def verify_update_token(self, update_token):
        """
        verifies the update token of a user
        """
        return update_token == self.update_token
    
    def serialize(self):
        """
        serializes a user object
        """
        return {
            "id": self.id,
            "username": self.username,
            "watch_list": [i.simple_serialize() for i in self.watch_list],
            "watched_list": [j.simple_serialize() for j in self.watched_list]
        }
    
    def simple_serialize(self):
        """
        serializes a user object without the lists of movies
        """
        return {
            "id": self.id,
            "username": self.username
        }
        

class Movie(db.Model):
    """
    movie model
    """
    __tablename__ = "movie"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # movie info
    title = db.Column(db.String, nullable=False, unique=True)
    genres = db.Column(db.String)
    director = db.Column(db.String, nullable = False)
    year = db.Column(db.String, nullable = False)
    runtime = db.Column(db.String, nullable = False)
    rating = db.Column(db.String, nullable = False)
    plot_outline = db.Column(db.String, nullable = False)

    # user lists
    user_watch_list = db.relationship("User", secondary=watch_list_table)
    user_watched_list = db.relationship("User", secondary=watched_list_table)

    def __init__(self, **kwargs):
        """
        initializes a movie object
        """
        self.title = kwargs.get("title")
        self.director = kwargs.get("director")
        self.year = kwargs.get("year")
        self.runtime = kwargs.get("runtime")
        self.rating = kwargs.get("rating")
        self.plot_outline = kwargs.get("plot_outline")

    def serialize(self):
        """
        serializes a movie object
        """
        return {
            "id": self.id,
            "title": self.title,
            "director": self.director,
            "year": self.year,
            "runtime": self.runtime,
            "rating": self.rating,
            "plot_outline": self.plot_outline,
            "user_watch_list": [i.simple_serialize() for i in 
                                self.user_watch_list],
            "user_watched_list": [i.simple_serialize() for i in 
                                  self.user_watched_list]
        }
    
    def simple_serialize(self):
        """
        serializes a movie object without the lists of users
        """
        return {
            "id": self.id,
            "title": self.title,
            "director": self.director,
            "year": self.year,
            "runtime": self.runtime,
            "rating": self.rating,
            "plot_outline": self.plot_outline
        }

