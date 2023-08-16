import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='-', intents=intents) # Prefix is usless because the bot uses interactions

owner_id = 00000000000000000 # Bot owner id
admin_ids = set() # Don't change this
blacklist_channel_id = 00000000000000000 # Channel where you can't say the words
log_channel_id = 00000000000000000 # Logs Channel ID
channel_blacklists = {} # More channels blacklist // Leave blank for just one
user_spam_tracker = {} # Peaple that can say the bad words // Leave blank to use /addadmin & /removeadmin
antiwords_enabled = False # Can also do /antiwords true/false

def load_blacklisted_words():
    with open("words.txt", "r") as file:
        for line in file:
            word = line.strip().lower()
            channel_blacklists[blacklist_channel_id].add(word)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    channel_blacklists[blacklist_channel_id] = set()
    load_blacklisted_words()

@bot.slash_command(name="add", description="Adds a word to the blacklist.")
async def add(ctx, word: str):
    """
    Adds a word to the blacklist.
    Usage: /add word
    """
    if ctx.author.id != owner_id or ctx.channel.id != blacklist_channel_id:
        await ctx.send("You don't have permission to use this command in this channel.")
        return

    word_lower = word.lower()
    channel_blacklists[blacklist_channel_id].add(word_lower)

    with open("words.txt", "a") as file:
        file.write(word_lower + "\n")

    await ctx.send(f'Word "{word}" added to the blacklist.')

    log_message = f"{ctx.author.mention} added word \"{word}\" to the blacklist."
    log_channel = bot.get_channel(log_channel_id)
    await log_channel.send(log_message)

@bot.slash_command(name="remove", description="Removes a word from the blacklist.")
async def remove(ctx, word: str):
    """
    Removes a word from the blacklist.
    Usage: /remove word
    """
    if ctx.author.id != owner_id or ctx.channel.id != blacklist_channel_id:
        await ctx.send("You don't have permission to use this command in this channel.")
        return

    word_lower = word.lower()
    if word_lower in channel_blacklists[blacklist_channel_id]:
        channel_blacklists[blacklist_channel_id].remove(word_lower)

        with open("words.txt", "r") as file:
            lines = file.readlines()
        with open("words.txt", "w") as file:
            for line in lines:
                if line.strip().lower() != word_lower:
                    file.write(line)

        await ctx.send(f'Word "{word}" removed from the blacklist.')

        log_message = f"{ctx.author.mention} removed word \"{word}\" from the blacklist."
        log_channel = bot.get_channel(log_channel_id)
        await log_channel.send(log_message)
    else:
        await ctx.send(f'Word "{word}" is not in the blacklist.')

@bot.slash_command(name="antiwords", description="Enable or disable anti-words filter.")
async def antiwords(ctx, value: bool):
    """
    Enable or disable anti-words filter.
    Usage: /antiwords on/off
    """
    global antiwords_enabled
    antiwords_enabled = value
    status = "enabled" if antiwords_enabled else "disabled"
    await ctx.send(f"Anti-words filter is now {status}.")

    log_message = f"{ctx.author.mention} changed anti-words filter to {status}."
    log_channel = bot.get_channel(log_channel_id)
    await log_channel.send(log_message)

@bot.slash_command(name="addadmin", description="Grant a user admin permissions.")
async def add_admin(ctx, user: discord.Member):
    """
    Grant a user admin permissions.
    Usage: /addadmin @user
    """
    if ctx.author.id != owner_id:
        await ctx.send("You don't have permission to use this command.")
        return

    admin_ids.add(user.id)
    await ctx.send(f"{user.mention} has been granted admin permissions.")

    log_message = f"{ctx.author.mention} granted admin permissions to {user.mention}."
    log_channel = bot.get_channel(log_channel_id)
    await log_channel.send(log_message)

@bot.slash_command(name="removeadmin", description="Remove admin permissions from a user.")
async def remove_admin(ctx, user: discord.Member):
    """
    Remove admin permissions from a user.
    Usage: /removeadmin @user
    """
    if ctx.author.id != owner_id:
        await ctx.send("You don't have permission to use this command.")
        return

    if user.id in admin_ids:
        admin_ids.remove(user.id)
        await ctx.send(f"Admin permissions have been removed from {user.mention}.")

        log_message = f"{ctx.author.mention} removed admin permissions from {user.mention}."
        log_channel = bot.get_channel(log_channel_id)
        await log_channel.send(log_message)
    else:
        await ctx.send(f"{user.mention} doesn't have admin permissions.")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content = message.content.lower()

    if message.channel.id == blacklist_channel_id and antiwords_enabled:
        for word in channel_blacklists[blacklist_channel_id]:
            if word in content and message.author.id not in admin_ids:
                await message.delete()
                if message.author.id not in user_spam_tracker or user_spam_tracker[message.author.id] != word:
                    user_spam_tracker[message.author.id] = word
                    response = f"{message.author.mention} you can't say the word \"{word}\" in {message.channel.mention}"
                    await message.channel.send(response)
                    log_message = f"{message.author.mention} said word \"{word}\" and I deleted their message"
                    log_channel = bot.get_channel(log_channel_id)
                    await log_channel.send(log_message)
                return

    await bot.process_commands(message)

bot.run('token')
