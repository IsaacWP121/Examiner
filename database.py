import discord


class Player:
    def __init__(self, name, userid, rating=1400):
        self.name = name
        self.rating = rating
        self.userid = userid
        self.record = {'W': 0, 'L': 0, 'C': 0}
        self.opponents = []

    def __str__(self):
        return f'Player Name:{self.name}, Player Rating:{self.rating}, Player UserID:{self.userid}, Player Record:{self.record}, Player opponents:{self.opponents}'

def favoured_winner(rating_a, rating_b):
    returning_value = True if rating_a > rating_b else False if rating_a < rating_b else None
    return returning_value

def update_rating(rating, outcome, expected):
    if expected == None:
        return rating + (15 if outcome == 1 else -15)
    return rating + (10 if outcome == 1 else -20) if expected else rating + (20 if outcome == 1 else -10)


class EloDatabase:
    def __init__(self):
        # Initialize the EloDatabase with an empty dictionary to store players
        self.players = {}

    def add_player(self, user):
        try:
            # Check if the player with the given ID already exists
            if self.players[user.id] is not None:
                return f"{user.name} already added."
        except KeyError:
            pass  # No need to do anything if the key is not found

        # If the player doesn't exist, add them to the dictionary
        self.players[user.id] = Player(user.name, user.id)
        return f"{user.name} has been added!"

    def remove_player(self, user):
        # Remove a player from the dictionary if they exist
        if user.id in self.players:
            del self.players[user.id]
            return f"{user.name} removed."
        else:
            return f"{user.name} not in database"

    def record_match(self, player_a_id, player_b_id, outcome):
        # add the opponents to each player's list of opponents
        player_a = self.players.get(player_a_id)
        player_b = self.players.get(player_b_id)
        player_a.opponents.append(player_b.userid)
        player_b.opponents.append(player_a.userid)

        # calculate the expected outcome for each player
        favoured_a = favoured_winner(player_a.rating, player_b.rating)
        favoured_b = favoured_winner(player_b.rating, player_a.rating)

        print(favoured_a)
        print(favoured_b)

        # update the ratings of each player based on the outcome of the match
        self.edit_rating(player_a_id, update_rating(player_a.rating, outcome, favoured_a))
        self.edit_rating(player_b_id, update_rating(player_b.rating, 1-outcome, favoured_b))

        # update the record of each player based on the outcome of the match
        if outcome == 1:
            player_a.record['W'] += 1
            player_b.record['L'] += 1
        elif outcome == 0:
            player_a.record['L'] += 1
            player_b.record['W'] += 1
        else:
            player_a.record['C'] += 1
            player_b.record['C'] += 1
        # save the updated players to the file
        self.players[player_a_id] = player_a
        self.players[player_b_id] = player_b

    def get_rating(self, player_id):
        # Get the rating and name of a player with the given ID
        if player_id in self.players:
            return self.players[player_id].rating, self.players[player_id].name
        else:
            return None, None

    def edit_rating(self, player_id, rating):
        # Edit the rating of a player with the given ID if they exist
        if player_id in self.players:
            self.players[player_id].rating = rating
        else:
            print(f"Player {player_id} not found.")

    def dev_dump(self, player_id=None):
        # Return the player's information with the given ID, or None if not found
        return self.players.get(player_id, None)

    def get_leaderboard(self):
        # Sort players by rating in descending order to create a leaderboard
        leaderboard = sorted(self.players.values(), key=lambda x: -x.rating)
        
        embed = discord.Embed(title="Leaderboard", color=0x00ff00)
        # add the leaderboard data to the embed
        for i, player in enumerate(leaderboard):
            embed.add_field(name=f'{i+1}. {player.name}', value=round(player.rating), inline=True)
        return embed
    