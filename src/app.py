import json
from db import db
from flask import Flask, request
import users_dao
import datetime
from db import User
from db import Movie
from imdb import Cinemagoer




app = Flask(__name__)
db_filename = "movie_list.db"

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_filename}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True

db.init_app(app)
with app.app_context():
    db.create_all()

# generalized response formats
def success_response(data, code=200):
    return json.dumps(data), code

def failure_response(message, code=404):
    return json.dumps({"error": message}), code

# authentication method
def extract_token(request):
    """
    helper function that extracts the token from the header of a request
    """
    auth_header = request.headers.get("Authorization")
    if auth_header is None:
        return False, failure_response("Missing auth header", 400)
    bearer_token = auth_header.replace("Bearer", "").strip()
    if not bearer_token:
        return False, failure_response("Invalid auth header", 400)
    return True, bearer_token

# base endpoint
@app.route("/")
def secret():
    """
    endpoint for a fun secret message :)
    """
    
    return """                     ##        .            
              ## ## ##       ==            
           ## ## ## ##      ===            
       /\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\___/ ===        
  ~~~ {~~ ~~~~ ~~~ ~~~~ ~~ ~ /  ===- ~~~   
       \______ o          __/            
         \    \        __/             
          \____\______/                
          
          
          
          
          
          
          
          
          
          
          
          
          
          
          









          pls let me in 🫣"""

# user routes
@app.route("/register/", methods=["POST"])
def register_account():
    """
    endpoint for registering a new user
    """
    body = json.loads(request.data)
    username = body.get("username")
    password = body.get("password")

    if username is None or password is None:
        return failure_response("Invalid username or password", 400)
    
    created, user = users_dao.create_user(username, password)

    if not created:
        return failure_response("User already exists", 400)

    return success_response(
        {
            "session_token": user.session_token,
            "session_expiration": str(user.session_expiration),
            "update_token": user.update_token
        }
    )

@app.route("/login/", methods=["POST"])
def login():
    """
    endpoint for logging in a user
    """
    body = json.loads(request.data)
    username = body.get("username")
    password = body.get("password")
    
    if username is None or password is None:
        return failure_response("Invalid username or password", 400)
    
    success, user = users_dao.verify_credentials(username, password)

    if not success:
        return failure_response("Incorrect username or password", 400)

    return success_response(
        {
            "session_token": user.session_token,
            "session_expiration": str(user.session_expiration),
            "update_token": user.update_token
        }
    )

@app.route("/logout/", methods=["POST"])
def logout():
    """
    endpoint for logging out a user
    """
    success, session_token = extract_token(request)
    if not success:
        return session_token
    user = users_dao.get_user_by_session_token(session_token)
    if user is None or not user.verify_session_token(session_token):
        return failure_response("Invalid session token", 400)
    user.session_expiration = datetime.datetime.now()
    db.session.commit()
    return success_response({"message": "User has successfully logged out"})

@app.route("/session/", methods=["POST"])
def update_session():
    """
    endpoint for updating a user's session
    """
    success, update_token = extract_token(request)
    if not success:
        return update_token
    user = users_dao.renew_session(update_token)
    if user is None:
        return failure_response("Invalid update token")
    return success_response(
        {
            "session_token": user.session_token,
            "session_expiration": str(user.session_expiration),
            "update_token": user.update_token
        }
    )

@app.route("/secret/", methods=["POST"])
def secret_message():
    """
    endpoint for verifying a session token and returning a secret message
    """
    success, session_token = extract_token(request)

    if not success:
        return session_token
    user = users_dao.get_user_by_session_token(session_token)
    if user is None or not user.verify_session_token(session_token):
        return failure_response("Invalid session token", 400)
    
    return success_response({"message": "Wow we implemented session token!!"})

# movie routes

@app.route("/movie/search/", methods=["POST"])
def search_movie():
    """
    endpoint for searching for a movie
    """
    body = json.loads(request.data)
    title = body.get("title")
    ia = Cinemagoer()
    movie_search = ia.search_movie(title)
    for i in range(5):
        ia.update(movie_search[i], info=["title", "year"])
    return success_response({
        movie_search[0]["title"] + " (" + str(movie_search[0]["year"]) + ")" : movie_search[0].movieID,
        movie_search[1]["title"] + " (" + str(movie_search[1]["year"]) + ")" : movie_search[1].movieID,
        movie_search[2]["title"] + " (" + str(movie_search[2]["year"]) + ")" : movie_search[2].movieID,
        movie_search[3]["title"] + " (" + str(movie_search[3]["year"]) + ")" : movie_search[3].movieID,
        movie_search[4]["title"] + " (" + str(movie_search[4]["year"]) + ")" : movie_search[4].movieID
    }, 200)

@app.route("/movie/add/", methods=["POST"])
def create_movie():
    """
    endpoint for adding a movie to the database by movie id and adding it to a 
    user's watch list by session token
    """
    body = json.loads(request.data)
    movieID = body.get("movieID")
    session_token = body.get("session_token")
    if movieID is None:
        return failure_response("movieID not present", 400)
    if session_token is None:
        return failure_response("session_token not present", 400)
    user = User.query.filter_by(session_token=session_token).first()
    if user is None:
        return failure_response("User not found", 404)
    ia = Cinemagoer()
    movie_obj = ia.get_movie(movieID)
    ia.update(movie_obj, info=["title", "genres", "director", "year", "runtime", 
                           "rating", "plot outline"])
    movie = Movie.query.filter_by(title=movie_obj["title"]).first()
    if movie is None:
        directors = ""
        for d in movie_obj["director"]:
            if d["name"] == movie_obj["director"][0]["name"]:
                directors += d["name"]
            else:
                directors += ", " + d["name"]
        movie = Movie(
            title = movie_obj["title"],
            genres = ", ".join(movie_obj["genres"]),
            director = directors,
            year = movie_obj["year"],
            runtime = movie_obj["runtime"][0],
            rating = movie_obj["rating"],
            plot_outline = movie_obj["plot outline"]
        )
        db.session.add(movie)
        db.session.commit()
    user.watch_list.append(movie)
    db.session.commit()
    return success_response(movie.serialize(), 201)

@app.route("/movie/get/", methods=["POST"])
def get_movies():
    """
    endpoint for getting watch list or watched list by session token
    """
    body = json.loads(request.data)
    session_token = body.get("session_token")
    watched = body.get("watched")
    if session_token is None:
        return failure_response("Session token not present")
    if watched is None:
        return failure_response("Watched not present")
    user = User.query.filter_by(session_token=session_token).first()
    if user is None:
        return failure_response("User not found", 404)
    if watched:
        return success_response({
            "watched_list": [i.simple_serialize() for i in user.watched_list] 
        }, 200)
    else:
        return success_response({
            "watch_list": [j.simple_serialize() for j in user.watch_list]
        }, 200)
    
@app.route("/movie/move/", methods=["POST"])
def move_movie():
    """
    endpoint for moving a movie from a user's watch list to their watched list
    or vice versa by session token and movie title
    """
    body = json.loads(request.data)
    session_token = body.get("session_token")
    title = body.get("title")
    watched = body.get("watched")
    if session_token is None:
        return failure_response("Session token not present", 400)
    if title is None:
        return failure_response("Title not present", 400)
    if watched is None:
        return failure_response("Watched not present", 400)
    user = User.query.filter_by(session_token=session_token).first()
    if user is None:
        return failure_response("User not found", 404)
    movie = Movie.query.filter_by(title=title).first()
    if movie is None:
        return failure_response("Movie not found", 404)
    if watched:
        user.watch_list.remove(movie)
        user.watched_list.append(movie)
    else:
        user.watched_list.remove(movie)
        user.watch_list.append(movie)
    db.session.commit()
    return success_response(movie.serialize(), 201)
    



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)