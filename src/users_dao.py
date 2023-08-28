"""
DAO (Data Access Object) file

Helper file containing functions for accessing data in our database
"""

from db import db
from db import User


def get_user_by_username(username):
    """
    returns a user object from the database given a username
    """
    return User.query.filter(User.username == username).first()


def get_user_by_session_token(session_token):
    """
    returns a user object from the database given a session token
    """
    return User.query.filter(User.session_token == session_token).first()


def get_user_by_update_token(update_token):
    """
    returns a user object from the database given an update token
    """
    return User.query.filter(User.update_token == update_token).first()


def verify_credentials(username, password):
    """
    returns true if the credentials match, otherwise returns false
    """
    optional_user = get_user_by_username(username)
    if optional_user is None:
        return False, None
    
    return optional_user.verify_password(password), optional_user


def create_user(username, password):
    """
    creates a User object in the database

    returns if creation was successful, and the User object
    """
    optional_user = get_user_by_username(username)
    if optional_user is not None:
        return False, optional_user
    user = User(username=username, password=password)
    db.session.add(user)
    db.session.commit()
    return True, user


def renew_session(update_token):
    """
    renews a user's session token
    
    returns the User object
    """
    user = get_user_by_update_token(update_token)
    if user is None:
        return None
    user.renew_session()
    db.session.commit()
    return user
