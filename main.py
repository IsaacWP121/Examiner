import discord
from discord import app_commands
from discord.ext import commands
from database import EloDatabase, Player
from random import randint

#Select menu object
class QueueSelect(discord.ui.Select):
    def __init__(self, ranks):
        options = []
        for i in ranks:
            option = discord.SelectOption(label=i, description=ranks[i])
            options.append(option)
        super().__init__(placeholder="Select an option", max_values=1, min_values=1, options=options)
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id in panel.queues[self.values[0]]:
            await interaction.response.edit_message(content=f"You are already in the {self.values[0]} Queue", view=None)
        else:
            for queue in panel.queues:
                if interaction.user.id in panel.queues[queue]: 
                    panel.queues[queue].remove(interaction.user.id)
            panel.queues[self.values[0]].append(interaction.user.id)
            if len(panel.queues[self.values[0]]) >= 2:
                a = panel.queues[self.values[0]].pop(0)
                b = panel.queues[self.values[0]].pop(0)
                await panel.create_match(interaction, str(a), str(b))
                await panel.update()
                await interaction.response.edit_message(content=f"You have been added to {self.values[0]} Queue", view=None)
                await interaction.channel.send(content=f"{client.get_user(a).mention} | {client.get_user(b).mention} have found a match in the {self.values[0]} Queue")
            else:
                await panel.update()
                await interaction.response.edit_message(content=f"You have been added to {self.values[0]} Queue", view=None)

class SelectView(discord.ui.View,):
    def __init__(self, *, timeout=None, ranks=None):
        super().__init__(timeout=timeout)
        self.add_item(QueueSelect(ranks))

class PanelButtons(discord.ui.View):
    def __init__(self, *, timeout=None):
        super().__init__(timeout=timeout)
        self.ranks = {
            "All Rank":"All Ratings",
            "Masters+":2200,
            "Masters":2000, 
            "Intermediate":1700, 
            "Beginner":1400, 
            "Super Beginner":1000
            }

    @discord.ui.button(label="Queue", style=discord.ButtonStyle.blurple)
    async def queuebutton(self, interaction:discord.Interaction, button:discord.ui.Button):
        if data.players.get(interaction.user.id) == None:
            await interaction.response.send_message(f"You are not in the database please use {client.command_prefix}register to continue", ephemeral=True)
        
        else:
            ranks = {}
            for rank in self.ranks:
                if rank == "All Rank":
                    ranks[rank] = self.ranks[rank]
                    continue
                if data.get_rating(interaction.user.id)[0] >= self.ranks[rank]:
                    ranks[rank] = self.ranks[rank]
                    
            await interaction.response.send_message(view=SelectView(ranks=ranks), ephemeral=True, delete_after=180)
    
    @discord.ui.button(label="Unqueue", style=discord.ButtonStyle.grey)
    async def unqueuebutton(self, interaction:discord.Interaction, button:discord.ui.Button):
        if data.players.get(interaction.user.id) == None:
            await interaction.response.send_message(f"You are not in the database please use {client.command_prefix}register to continue", ephemeral=True)
        else:
            found = False
            for queue in panel.queues:
                if interaction.user.id in panel.queues[queue]:
                    panel.queues[queue].remove(interaction.user.id)
                    found = True
            if not found:
                await interaction.response.send_message("You are not in any queue", ephemeral=True)
            else:
                await panel.update()
                await interaction.response.send_message("You are no longer in the queue", ephemeral=True)       

class queuepanel:
    def __init__(self):
        self.ranks = {
            "All Rank":"All Ratings",
            "Masters+":2200,
            "Masters":2000,
            "Intermediate":1700,
            "Beginner":1400,
            "Super Beginner":1000
            }
        self.queues = {
            "All Rank":[],
            "Masters+":[],
            "Masters":[],
            "Intermediate":[],
            "Beginner":[],
            "Super Beginner":[]
            }
        self.matches = {
        } # MatchId (int) : match object (match())
        self.embed = discord.Embed(title="Dusk Matchmaking")
        for i in self.queues:
            key, value = i, self.queues[i] # just to help understanding
            self.embed.add_field(name=key, value=f"Currently queuing: {len(value)}\n")
        
        self.buttons = PanelButtons()

    async def send(self, interaction):
        self.message = await interaction.channel.send(embed=self.embed, view=self.buttons)
        await interaction.response.send_message(content="Queue Panel Set", ephemeral=True)

    async def create_match(self, interaction, player_a: str, player_b: str):
        def is_mention(string):
            try:
                user = interaction.message.guild.get_member(int(string[2:-1]))
                if user:
                    return True
            finally:
                return False

        try:
            player_a = int(player_a)
        except:
            player_a = int(player_a[2:-1])
        try:
            player_b = int(player_b)
        except:
            player_b = int(player_b[2:-1])

        if data.players.get(player_a) == None or data.players.get(player_b) is None:
            await interaction.response.send_message("One or both players are not in the database.")
            return
        matchId = int(str(randint(1000,9999))+str(len(self.matches)))
        self.matches[matchId] = Match(channel=interaction.channel, player_a=player_a, player_b=player_b, matchId=matchId)
        await self.matches[matchId].send(interaction)

    async def update(self):
        self.embed = discord.Embed(title="Dusk Matchmaking")
        for i in self.queues:
            key, value = i, self.queues[i] # just to help understanding
            self.embed.add_field(name=key, value=f"Currently queuing: {len(value)}\n")
        await self.message.edit(embed=self.embed)

class YesNoButtons(discord.ui.View):
    def __init__(self, *, timeout=None):
        super().__init__(timeout=timeout)

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.blurple)
    async def YesCallback(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            matchKey = int(interaction.message.embeds[0].fields[-1].value)
            match = panel.matches[matchKey]
            players = [int(match.player_a), int(match.player_b)]
            playerAuthNeeded = players[0] if match.PA_Result is None else players[1]

            print("Before record_match")
            await interaction.response.defer()

            if interaction.user.id == playerAuthNeeded:
                if interaction.user.id == players[0]:
                    await match.message.edit(view=None)
                    await interaction.message.edit(view=None)
                    data.record_match(int(players[0]), int(players[1]), match.PB_Result)
                    print("a")
                elif interaction.user.id == players[1]:
                    await match.message.edit(view=None)
                    await interaction.message.edit(view=None)
                    del panel.matches[matchKey]
                    data.record_match(int(players[0]), int(players[1]), match.PA_Result)
                    print("b")

                await interaction.followup.send(embed=match.matchRecordedEmbed)
                print("After record_match")
                print(data.dev_dump)
            else:
                await interaction.followup.send("Your opponent must verify the results", ephemeral=True)
        except Exception as e:
            print(f"Error in YesCallback: {e}")


    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def NoCallback(self, interaction:discord.Interaction, button:discord.ui.Button):
        try:
            matchKey = int(interaction.message.embeds[0].fields[len(interaction.message.embeds[0].fields)-1].value)
            match = panel.matches[matchKey] # match = Match()
            players = [match.player_a, match.player_b]
            playerAuthNeeded = players[0] if (match.PA_Result == None) else players[1]
            await interaction.response.defer()
            if interaction.user.id in players:
                if interaction.user.id == playerAuthNeeded:
                    await match.message.edit(view=None)
                    await interaction.message.edit(view=None)
                    await interaction.followup.send(f"""{client.guilds[0].get_role(adjudicateRole).mention} Can you please adjudicate and report on the result on this match.\n{client.get_user(int(players[0])).mention} reported a win for {client.get_user(int(players[0])).mention if match.PA_Result == 1 else client.get_user(int(players[1])).mention} and {client.get_user(int(players[1])).mention} reported a win for {client.get_user(int(players[0])).mention if match.PB_Result == 1 else client.get_user(int(players[1])).mention}\nTo report the result of this match use `/report [match_id] [user_id]` where the matchId can be found at the bottom of the embeds""")
                else:
                    await interaction.followup.send("Your opponent must verify the results", ephemeral=True)
            else:
                await interaction.followup.send("You are not able to verify results on this match", ephemeral=True)

        except Exception as e:
            print(e)

class MatchButtons(discord.ui.View):
    def __init__(self, *, timeout=None):
        super().__init__(timeout=timeout)
        self.YNbuttons = YesNoButtons()

    @discord.ui.button(label="A", style=discord.ButtonStyle.red, row=0)
    async def PlayerAButton_Callback(self, interaction:discord.Interaction, button:discord.ui.Button):
        try:
            matchKey = int(interaction.message.embeds[0].fields[len(interaction.message.embeds[0].fields)-1].value)
            match = panel.matches[matchKey] # match = Match()
            players = [match.player_a, match.player_b]
            self.embed = discord.Embed(title=f"Match Result Verification", color=0x00ff00)

            if interaction.user.id in players:

                if interaction.user.id == players[0]:
                    match.PA_Result = 1
                    self.embed.add_field(name="", value=f"""{client.get_user(players[0]).mention} has reported the winner as being: {client.get_user(players[0]).mention}""", inline=False)
                    self.embed.add_field(name="", value=f"""Is this result correct?""", inline=False)
                    self.embed.add_field(name="\u200b", value=f"{matchKey}")
                    await interaction.response.send_message(content=f"{client.get_user(players[1]).mention}", embed=self.embed, view=self.YNbuttons)
                    await match.message.edit(view=None)

                if interaction.user.id == players[1]:
                    match.PB_Result = 1
                    self.embed.add_field(name="", value=f"""{client.get_user(players[1]).mention} has reported the winner as being: {client.get_user(players[0]).mention}\n
                        Is this result correct?""", inline=False)
                    self.embed.add_field(name="\u200b", value=f"{matchKey}")
                    await interaction.response.send_message(content=f"{client.get_user(players[0]).mention}", embed=self.embed, view=self.YNbuttons)
                    await match.message.edit(view=None)

        except Exception as e:
            print(e)

    @discord.ui.button(label="B", style=discord.ButtonStyle.red, row=0)
    async def PlayerBButton_Callback(self, interaction:discord.Interaction, button:discord.ui.Button):
        try:
            matchKey = int(interaction.message.embeds[0].fields[len(interaction.message.embeds[0].fields)-1].value)
            match = panel.matches[matchKey] # match = Match()
            players = [match.player_a, match.player_b]
            self.embed = discord.Embed(title=f"Match Result Verification", color=0x00ff00)

            if interaction.user.id in players:

                if interaction.user.id == players[0]:
                    match.PA_Result = 0
                    self.embed.add_field(name="", value=f"""{client.get_user(players[0]).mention} has reported the winner as being: {client.get_user(players[1]).mention}\n
                        Is this result correct?""", inline=False)
                    self.embed.add_field(name="\u200b", value=f"{matchKey}")
                    await interaction.response.send_message(content=f"{client.get_user(players[1]).mention}", embed=self.embed, view=self.YNbuttons)
                    await match.message.edit(view=None)

                if interaction.user.id == players[1]:
                    match.PB_Result = 0
                    self.embed.add_field(name="", value=f"""{client.get_user(players[1]).mention} has reported the winner as being: {client.get_user(players[1]).mention}\n
                        Is this result correct?""", inline=False)
                    self.embed.add_field(name="\u200b", value=f"{matchKey}")
                    await interaction.response.send_message(content=f"{client.get_user(players[0]).mention}", embed=self.embed, view=self.YNbuttons)
                    await match.message.edit(view=None)

        except Exception as e:
            print(e)

    @discord.ui.button(label=f"Cancel Match", style=discord.ButtonStyle.gray, row=1)
    async def Cancel(self, interaction:discord.Interaction, button:discord.ui.Button):
        try:
            matchKey = int(interaction.message.embeds[0].fields[len(interaction.message.embeds[0].fields)-1].value)
            match = panel.matches[matchKey] # match = Match()
            players = [match.player_a, match.player_b]
            if interaction.user.id in players:
                await interaction.response.edit_message(embed=None, content=f"Match Canceled by {client.get_user(interaction.user.id)}", view=None)
                del panel.matches[matchKey]

        except Exception as e:
            print(e)

class Match:
    def __init__(self, channel, player_a: Player, player_b: Player, matchId:int):
        self.player_a = player_a #player id's will be a Player object
        self.player_b = player_b
        self.channel = channel # discord.guild
        self.PA_Result = None # Player A Match Result
        self.PB_Result = None # Player B Match Result
        self.buttons = MatchButtons()
        self.verification_failed = False
        self.matchId = matchId
        self.matchRecordedEmbed = discord.Embed(title=f"Recorded Match", color=0x00ff00)
        self.matchRecordedEmbed.add_field(name="", value=f"""Match between {client.get_user(int(player_a)).mention} and {client.get_user(int(player_b)).mention} recorded.\nElo's can be checked using `{client.command_prefix}rating`\nLeaderboard can be checked with `{client.command_prefix}leaderboard`""")

    async def send(self, interaction):
        # send embed with buttons
        self.embed = discord.Embed(title=f"Record Match Between {data.players.get(self.player_a).name}#{client.get_user(self.player_a).discriminator} and {client.get_user(self.player_b).name}#{client.get_user(self.player_b).discriminator}", color=0x00ff00)
        self.embed.add_field(name=f"For {data.players.get(self.player_a).name}#{client.get_user(self.player_a).discriminator} Win", value="Press 🅰️", inline=False)
        self.embed.add_field(name=f"For {client.get_user(self.player_b).name}#{client.get_user(self.player_b).discriminator} Win", value="Press 🅱️", inline=False)
        self.embed.add_field(name="\u200b", value=f"{self.matchId}")
        self.message = await interaction.channel.send(embed=self.embed, view=self.buttons)

# setup
client = commands.Bot(command_prefix="/", intents=discord.Intents.all(), case_insensitive=True)
client.remove_command('help')
data = EloDatabase()
channel_id = []
q = []
adjudicateRole = 1030981787180093490
panel = None

@client.event
async def on_ready():
    global panel
    panel = queuepanel()
    try:
        synced = await client.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

@client.event
async def on_message(message):
    await client.process_commands(message)

@client.tree.command(name="set_channel", description="Examiner: Sets up the queuing embed. (Admin Only)")
async def set_channel(interaction: discord.Interaction):
    if interaction.permissions.administrator:
        await panel.send(interaction)
    else:
        await interaction.response.send_message("You do not have the permissions for this command", ephemeral=True)

@client.tree.command(name="manual_register", description="Examiner: Manually registers a new player in the database. (Admin Only)")
@app_commands.describe(id_arg="id_arg is the id of the user to be registered")
async def manual_register(interaction: discord.Interaction, id_arg: str) -> None:
    if interaction.permissions.administrator:
        await interaction.response.send_message(f"{data.add_player(client.get_user(int(id_arg)))}", ephemeral=True)
    else:
        interaction.response.send_message("You do not have the permissions for this command", ephemeral=True)

@client.tree.command(name="manual_remove", description="Examiner: Manually removes a player from the database. (Admin Only)")
@app_commands.describe(id_arg="id_arg is the id of the user to be removed")
async def manual_remove(interaction: discord.Interaction, id_arg: str) -> None:
    if interaction.permissions.administrator:
        await interaction.response.send_message(f"{data.remove_player(client.get_user(int(id_arg)))}", ephemeral=True)
    else:
        interaction.response.send_message("You do not have the permissions for this command", ephemeral=True)

@client.tree.command(name="report", description="Examiner: Used to adjudicate a match dispute (Admin Only)")
@app_commands.describe(match_id="matchId is used to identify the match needing adjudicating")
@app_commands.describe(user_id="userId is the userId of the winner")
async def report(interaction: discord.Interaction, match_id: str, user_id: str) -> None:
    if interaction.user.get_role(adjudicateRole) != None:
        match = panel.matches[int(match_id)] # match = Match()
        players = [match.player_a, match.player_b]
        if int(user_id) == players[0]:
            data.record_match(int(players[0]), int(players[1]), 1)
        if int(user_id) == players[1]:
            data.record_match(int(players[0]), int(players[1]), 0)
        await interaction.response.send_message(embed=match.matchRecordedEmbed)
        del panel.matches[int(match_id)]
    else:
        interaction.response.send_message("You do not have the permissions for this command", ephemeral=True)

@client.tree.command(name="edit_rating", description="Examiner: Manually updates a player's rating. (Admin Only)")
@app_commands.describe(user_id="user_id is the id of the user to have their rating changed", rating="The desired rating")
async def edit_rating(interaction: discord.Interaction, user_id: str, rating: int):
    data.edit_rating(int(user_id), rating)
    await interaction.response.send_message("Updated", ephemeral=True)
    
    if interaction.permissions.administrator:
        data.edit_rating(int(user_id), rating)
        await interaction.response.send_message("Updated", ephemeral=True)
    else:
        interaction.response.send_message("You do not have the permissions for this command", ephemeral=True)

@client.tree.command(name="help", description="Examiner: Provides a list of available commands")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(title="Available Commands", color=0x00ff00)
    if interaction.permissions.administrator:
        embed.title = "Available Commands (Admin Included)"
        embed.add_field(name="set_channel", value="Sets up the queuing embed (Admin Only)", inline=False)
        embed.add_field(name="manual_register", value="Manually registers a new player in the database. (Admin Only)", inline=False)
        embed.add_field(name="manual_remove", value="Manually removes a player from the database. (Admin Only)", inline=False)
        embed.add_field(name="edit_rating", value="Manually edits a player's rating in the database. (Admin Only)", inline=False)
        embed.add_field(name="report", value="Used to adjudicate a match dispute (Admin Only)", inline=False)
    embed.add_field(name="help", value="Shows this help message.", inline=False)
    embed.add_field(name="register", value="Registers a new player in the database.", inline=False)
    embed.add_field(name="rating", value="Allows you to view the rating of the sender.", inline=False)
    embed.add_field(name="leaderboard", value="Displays the leaderboard of players and their Elo ratings.", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@client.tree.command(name="register", description="Examiner: Registers a new player in the database.")
async def register(interaction: discord.Interaction):
    await interaction.response.send_message(f"{data.add_player(interaction.user)}", ephemeral=True)

@client.tree.command(name="rating", description="Examiner: Allows you to view the rating of the sender.")
async def rating(interaction: discord.Interaction) -> None:
    try:
        embed = discord.Embed(color=0x00ff00)
        embed.add_field(name=f"{data.get_rating(interaction.user.id)[1]} Rating:", value=f"{round(data.get_rating(interaction.user.id)[0])}", inline=False)         
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except:
        print("error")
        await interaction.response.send_message(f"You are not in the database please use {client.command_prefix}register to continue", ephemeral=True)

@client.tree.command(name="leaderboard", description="Examiner: Displays the leaderboard of players and their Elo ratings.")
async def leaderboard(interaction: discord.Interaction):
    await interaction.response.send_message(embed=data.get_leaderboard(), ephemeral=True)

@client.event
async def on_command_error(interaction: discord.Interaction, error):
    if isinstance(error, commands.CommandNotFound):
        await interaction.response.send_message("Invalid command. Try !help for a list of available commands.")

@client.event
async def on_interaction_add(interaction, user):
    try:
        if user.id != client.user.id and "Record" in interaction.message.embeds[0].title.split()[0]:
            players = [int(player_id) for player_id in interaction.message.embeds[0].fields[len(interaction.message.embeds[0].fields)-1].value.split(" | ")]
            if user.id in players:
                if interaction.emoji == "🅰️":
                    outcome_value = 1
                elif interaction.emoji == "🤝":
                    outcome_value = 0.5
                elif interaction.emoji == "🅱️":
                    outcome_value = 0
                else:
                    await interaction.response.send_message("Invalid outcome.", ephemeral=True)
                    return

                await interaction.message.clear_interactions()
                data.record_match(int(players[0]), int(players[1]), outcome_value)
                await interaction.message.channel.send(f"Match between {client.get_user(int(players[0])).mention} and {client.get_user(int(players[1])).mention} recorded.\nElo's can be checked using {client.command_prefix}rating\nLeaderboard can be checked with {client.command_prefix}leaderboard")
    except Exception as e:
        print(e)

if __name__ == "__main__":
    # Run the bot with the specified token
    client.run(Token)