from collections import defaultdict
import json
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

import keep_alive

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

active_votes = {
  "nation": "",
  "question": None,
  "candidates": [],
  "votes": defaultdict(list),
  "open": False,
  "voteAuthor": None,
}

try:
  with open("votes.json", "r") as f:
    active_votes["votes"] = json.load(f)
except FileNotFoundError:
  active_votes["votes"] = {}

@bot.event
async def on_ready():
  print(f"✅ Logged in as {bot.user}")
  await bot.tree.sync()

@bot.command()
async def startvote(ctx, question: str, nation: str, *candidates):
  if active_votes["open"]:
    await ctx.send("A vote is already running idiot. Finish it first.")
    return
  active_votes["question"] = question
  active_votes["candidates"] = list(candidates)
  active_votes["nation"] = nation
  active_votes["votes"].clear()
  active_votes["open"] = True
  active_votes["voteAuthor"] = ctx.author.id
  await ctx.send(
    f"**A NEW ELECTION HAS STARTED BOYS!!** \n"
    f"**Nation:** {nation} \n"
    f"**Questions:** {question} \n"
    f"**Candidates:** {', '.join(candidates)} \n"
    f"DM me your vote in order like: Alice>Bob>Charlie"
  )

@bot.command()
async def endvote(ctx):
  if not active_votes["open"]:
    await ctx.send("No active vote to end.")
    return
  if ctx.author.id != active_votes["voteAuthor"]:
    await ctx.send("Only the vote creator can end the vote.")
    return

  votes = active_votes["votes"]
  candidates = active_votes["candidates"].copy()

  if not votes:
    await ctx.send("No votes have been cast.")
    active_votes["open"] = False
    active_votes["votes"].clear()
    active_votes["question"] = None
    active_votes["candidates"] = []
    active_votes["nation"] = ""
    active_votes["voteAuthor"] = None
    return

  while True:
    tally = {c: 0 for c in candidates}
    for vote in votes.values():
      for choice in vote:
        if choice in candidates:
          tally[choice] += 1
          break
    
    total_votes = sum(tally.values())
    for candidate, count in tally.items():
      if count > total_votes / 2:
        winner = candidate
        await ctx.send(f"🏆 The winner is **{winner}**!")
        active_votes["open"] = False
        active_votes["votes"].clear()
        active_votes["question"] = None
        active_votes["candidates"] = []
        active_votes["nation"] = ""
        active_votes["voteAuthor"] = None
        return

    if not tally or sum(tally.values()) == 0:
      winner = ", ".join(candidates)
      await ctx.send(f"⚖️ It's a tie between: {winner}")
      break

    min_votes = min(tally.values())
    eliminated = [c for c, v in tally.items() if v == min_votes]
    for e in eliminated:
      candidates.remove(e)

    if len(candidates) == 1:
      winner = candidates[0]
      await ctx.send(f"🏆 The winner is **{winner}**!")
      active_votes["open"] = False
      active_votes["votes"].clear()
      active_votes["question"] = None
      active_votes["candidates"] = []
      active_votes["nation"] = ""
      active_votes["voteAuthor"] = None
      with open("votes.json", "w") as f:
        json.dump({}, f)
      return


@bot.event
async def on_message(message):
  if message.author.bot:
    return
  if message.guild is None and active_votes["open"]:
    content = message.content.strip()
    ranks = [c.strip() for c in content.split(">") if c.strip()]
    candidates_lower = [c.lower() for c in active_votes["candidates"]]
    ranks_lower = [c.lower() for c in ranks]
    if str(message.author.id) in active_votes["votes"]:
      await message.channel.send("You already voted, no take backs!")
      return
    if len(ranks) != len(active_votes["candidates"]):
      await message.channel.send(f"Your vote must rank all candidates: {', '.join(active_votes['candidates'])}")
      return
    if not all(c in candidates_lower for c in ranks_lower):
      await message.channel.send(f"Invalid vote. All candidates must be in: {', '.join(active_votes['candidates'])}")
      return
    try:
      with open("votes.json", "r") as f:
        saved_votes = json.load(f)
    except FileNotFoundError:
      saved_votes = {}
    saved_votes[str(message.author.id)] = ranks
    with open("votes.json", "w") as f:
      json.dump(saved_votes, f, indent=2)
    active_votes["votes"] = saved_votes
    await message.channel.send("Your vote has been recorded. No take backs.")
  await bot.process_commands(message)

@bot.command()
async def activevotes(ctx):
  if active_votes["open"]:
    await ctx.send("A vote is active bro, GO VOTE!")
  else:
    await ctx.send("No active votes right now, chill.")

@bot.command()
async def ping(ctx):
  await ctx.send("THE AQABA ELECTION KING DOES NOT DIE. IT IS ALIVE.")

@bot.command()
async def hello(ctx):
  await ctx.send(f"OK BRO, {ctx.author.mention}! YOU WANT AN ELECTION OR NOT? NO HELLOS, JUST ELECTION")

if __name__ == "__main__":
    keep_alive.keep_alive()
    bot.run(os.getenv("BOT_TOKEN"))