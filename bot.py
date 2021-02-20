import asyncio
import time
import uuid

import discord
from discord.ext import commands
from sqlitedict import SqliteDict

import config
import db

config = config.read()


class VerifyCog(commands.Cog):
    def __init__(self, bot, *args, **kwargs):
        self.bot = bot
        bot.loop.create_task(self.maintenance_loop())
        super().__init__(*args, **kwargs)

    @commands.Cog.listener()
    async def on_ready(self):
        print("Bot is ready")

    async def maintenance_loop(self):
        interval = config.check_interval
        print(f"Sleeping {interval} seconds between maintenance iterations")
        while True:
            await self.bot.wait_until_ready()

            async for session_id, session in db.verified_user_ids(
                    config.expiry_seconds):
                user_id, guild_id = session.user_id, session.guild_id
                try:
                    guild = self.bot.get_guild(guild_id)
                    member = await guild.fetch_member(user_id)
                    # TODO: search for "uw-verified" role once and cache it by guild id
                    role = guild.get_role(812472842632691725)
                    print(
                        f"Adding role to {session.discord_name} with id {member.id}"
                    )
                    await member.add_roles(role, reason="Verification Bot")
                except Exception as e:
                    print(f"Failed to add role to user in {guild_id}:\n{e}")
                    continue
                db.delete_session(session_id)

            await db.collect_garbage(config.expiry_seconds)
            await asyncio.sleep(interval)

    @commands.command()
    async def verify(self, ctx):
        # Ignore all DMs for now
        if not ctx.message.guild:
            return

        user_id = ctx.author.id
        guild_id = ctx.guild.id
        name = f"{ctx.author.name}#{ctx.author.discriminator}"
        session_id = db.new_session(user_id, guild_id, name)

        verification_link = f"{config.url}/start/{session_id}/email"

        embed = discord.Embed(
            title="Verification!",
            url=verification_link,
            description=
            "Please use this page to enter your email for verification. Your email will not be shared with Discord.",
            color=0xffc0cb,
        )
        embed.add_field(
            name="Verification Link",
            value=verification_link,
            inline=True,
        )
        embed.set_thumbnail(
            url=
            "https://uwaterloo.ca/library/sites/ca.library/files/uploads/images/img_0236_0.jpg"
        )
        await ctx.message.author.send(embed=embed)


def main():
    try:
        bot = commands.Bot(command_prefix=config.prefix)
        bot.add_cog(VerifyCog(bot))
        bot.run(config.token)
    except Exception as e:
        print(f'Error: {e}')


if __name__ == "__main__":
    main()
