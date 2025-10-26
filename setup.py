from pyrogram import Client
import start, register
from bot import MeTube
if __name__=="__main__":
    MeTube.run()
    print("MeTubeBot Starting")
    with MeTube:
        MeTube.send_message(6239769036, "Bot Started 💯")
