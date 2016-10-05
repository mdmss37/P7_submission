#Full Stack Nanodegree Project 4 Refresh

## Set-Up Instructions:
1.  Update the value of application in app.yaml to the app ID you have registered
 in the App Engine admin console and would like to use to host your instance of this sample.
1.  Run the app with the devserver using dev_appserver.py DIR, and ensure it's
 running by visiting the API Explorer - by default localhost:8080/_ah/api/explorer.
1.  (Optional) Generate your client library(ies) with the endpoints tool.
 Deploy your application.



##Game Description:
player is requested to guess the word(hang man)

Players are ranked based on win qty.

Each game can be retrieved or played by using the path parameter
`urlsafe_game_key`.

##Files Included:
 - api.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration.
 - main.py: Handler for taskqueue handler.
 - models.py: Entity and message definitions including helper methods.
 - utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.

##Endpoints Included:
 - **create_user**
    - Path: 'user'
    - Method: POST
    - Parameters: user_name, email (optional)
    - Returns: Message confirming creation of the User.
    - Description: Creates a new User. user_name provided must be unique. Will
    raise a ConflictException if a User with that user_name already exists.

 - **new_game**
    - Path: 'game'
    - Method: POST
    - Parameters: user_name, min, max, attempts
    - Returns: GameForm with initial game state.
    - Description: Creates a new Game. user_name provided must correspond to an
    existing user - will raise a NotFoundException if not. Min must be less than
    max. Also adds a task to a task queue to update the average moves remaining
    for active games.

 - **get_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with current game state.
    - Description: Returns the current state of a game.

 - **make_move**
    - Path: 'game/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key, guess
    - Returns: GameForm with new game state.
    - Description: Accepts a 'guess' and returns the updated state of the game.
    If this causes a game to end, a corresponding Score entity will be created.

 - **get_scores**
    - Path: 'scores'
    - Method: GET
    - Parameters: None
    - Returns: ScoreForms.
    - Description: Returns all Scores in the database (unordered).

 - **get_user_scores**
    - Path: 'scores/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: ScoreForms.
    - Description: Returns all Scores recorded by the provided player (unordered).
    Will raise a NotFoundException if the User does not exist.

 - **get_user_active_games**
    - Path: 'games/user/active'
    - Method: GET
    - Parameters: None
    - Returns: StringMessage
    - Description: Gets active games of certan user

 - **get_user_all_games**
    - Path: 'games/user/all'
    - Method: GET
    - Parameters: None
    - Returns: StringMessage
    - Description: Gets active games of certan user

 - **cancel_game**
    - Path: 'game/cancel'
    - Method: PUT
    - Parameters: None
    - Returns: StringMessage
    - Description: Cancel certain game

 - **get_high_scores**
    - Path: 'games/highscores'
    - Method: GET
    - Parameters: None
    - Returns: StringMessage
    - Description: Gets highscores of games limited with number_of_results.

 - **get_user_rankings**
    - Path: 'games/rankings'
    - Method: GET
    - Parameters: None
    - Returns: StringMessage
    - Description: Gets ranking of users. Ranking is based on number of win.

 - **get_game_history**
    - Path: 'game/history'
    - Method: GET
    - Parameters: None
    - Returns: StringMessage
    - Description: Gets all movement for certaion game.


##Models Included:
 - **User**
    - Stores unique user_name and (optional) email address.

 - **Game**
    - Stores unique game states. Associated with User model via KeyProperty.

 - **Score**
    - Records completed games. Associated with Users model via KeyProperty.

##Forms Included:
 - **GameForm**
    - Representation of a Game's state (urlsafe_key, attempts_remaining,
    game_over flag, message, user_name).
 - **GameForms**
    - Multiple GameForm container.
 - **NewGameForm**
    - Used to create a new game (user_name, min, max, attempts)
 - **MakeMoveForm**
    - Inbound make move form (guess).
 - **ScoreForm**
    - Representation of a completed game's Score (user_name, date, won flag,
    guesses).
 - **ScoreForms**
    - Multiple ScoreForm container.
 - **UserRank**
    - Number of win for certain player.
 - **UserRanks**
    - Multiple UserRank container.
 - **StringMessage**
    - General purpose String container.