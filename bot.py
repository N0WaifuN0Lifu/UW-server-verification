import discord
from discord.ext import commands
import time
import configparser
import uuid
import requests
from bs4 import BeautifulSoup


#Configurations
config = configparser.ConfigParser()
config.read('config.ini')
TOKEN = config['MAIN']['Token']
PREFIX = config['MAIN']['Prefix']
client = commands.Bot(command_prefix=PREFIX)

@client.event
async def on_ready():
    print("bot is ready")
    while True:
        with SqliteDict('./my_db.sqlite') as mydict:
            check_dict = mydict
            for key in check_dict:
                if not check_dict[key]["server_verified"]
                    user_id = check_dict[key]["discordid"]
                    await discord.Member.add_roles(user_id, "verified")
                    check_dict[key]["server_verified"] = True
                    mydict = check_dict
                    mydict.commit()      
            time.sleep(300)
            

@client.command()
async def hello(ctx):
    await ctx.send("Your name is: "+str(ctx.message.author.name)+" your ID is: "+str(ctx.message.author.id))
    user = client.get_user(ctx.message.author.id)
    embed=discord.Embed(title="Verification!",url="https://www.brocksolutions.com/wp-content/uploads/2020/02/University-of-Waterloo-1080x675.jpg", description="Hi, This is AndrewBot, The UW verify bot. Could you be a gamer for me and go to the following page to verify your email. The reason its a separate web page is for absolutely no data to be stored.", color=0x5a38d6)
    embed.add_field(name="Verification Link:", value=str(requests.get("http://127.0.0.1:5000/new/"+str(ctx.message.author.id)).text), inline=True)
    embed.add_field(name="Server Owner:", value=f"{ctx.guild.owner}")
    embed.set_thumbnail(url="https://uwaterloo.ca/library/sites/ca.library/files/uploads/images/img_0236_0.jpg")
    await user.send(embed=embed)


@client.event
@commands.has_role(name='Admin')
async def unverify(user):
    #await discord.Member.removeroll_roles(user, "verified")
    with SqliteDict('./my_db.sqlite') as mydict:
            check_dict = mydict
        #find persons in list and remove em
    

    
    

try:
    client.run(TOKEN, bot = True)
except Exception as e:
    print(f'Error when logging in: {e}')
    
    
    
    
    
    
    