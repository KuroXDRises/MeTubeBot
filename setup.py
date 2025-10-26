from pyrogram import Client
import start, register
MeTube = Client("MeTube",
                api_id=27548865,
                api_hash="db07e06a5eb288c706d4df697b71ab61",
                bot_token="8304647918:AAEmLuWW9mXpyfygdUpOdAd0PxSiqgZXllI"
               )
if __name__=="__main__":
    MeTube.run()
    print("MeTubeBot Starting")
    with MeTube:
        MeTube.send_message(6239769036, "Bot Started 💯")
