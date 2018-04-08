# Anki Quake 3

This project is a fork of IOQuake3 (http://ioquake3.org) designed for learning gamification
in conjunction with the Anki flashcard software package (https://apps.ankiweb.net/).

## Basics
* You can start single player games with bots using this special build of IOQuake3
* You will not be able to pick up any weapons, ammo or powerups off the ground. You will have to earn those by doing Anki reviews. Bots will pick up items/weapons and shoot you with them though.
* You start the game with a Railgun and Rocket Launcher, with no ammo. You can request ammo for them at the cost of 5 anki reviews for each ammo pack (this is configurable). 
* Similarly, you can request Health or Armor.
* When you request items, the bots become paused and will not attack you.
* You can then alt-tab into Anki, which has been notified of your target review count.
* Perform all your reviews in Anki. You will hear audio feedback from Quake3 as you perform your reviews and earn items. You will also hear a sound when all your reviews are done. You can then alt-tab into Quake3 and resume playing.

![Anki Quake 3 screenshot](https://raw.githubusercontent.com/lucwastiaux/anki-quake3/master/screenshots/anki_quake3.jpg)

## Limitations
* You must own a copy of Quake 3 Arena (http://store.steampowered.com/app/2200/Quake_III_Arena/)
* The only items/weapons supported currently are:
   * Railgun (damage changed to 200 instead of default 100)
   * Rocket Launcher
   * Armor
   * Health
* Only windows is supported.


## Setup
* Download current release https://github.com/lucwastiaux/anki-quake3/blob/master/releases/anki-quake3-2018-04-08.zip (Windows 64bit)
* Unzip
* copy all *.pk3 files from your Steam install (C:\Program Files (x86)\Steam\steamapps\common\Quake 3 Arena\baseq3) into anki-quake3/baseq3
* Launch the game once so that it'll create a user profile (start ioquake3.x86_64.exe), but exit right away as we need to do some more setup
* After exiting, open windows explorer and paste this path: 
* Open *q3config.cfg** in a text editor, and add the following lines at the bottom (you can change the key bindings)
   * **bind e "toggle bot_pause"**  *//this will toggle the bot pause mode, use this to restart the game after reviews*
   * **bind r "request_rail"** *//this requests rail slugs, and starts review mode (pauses bots). You can press it multiple times*
   * **bind t "request_rockets"** *//this requests rockets, and starts review mode (pauses bots)*
   * **bind f "request_health"** *//this requests health, and starts review mode (pauses bots)*
   * **bind g "request_armor"** *//this requests armor, and starts review mode (pauses bots)*
   * **bind q "anki_decrement"** *//if you want to use software other than Anki, you can use this key to manually fulfill reviews*
* Copy the Anki add-on script (https://raw.githubusercontent.com/lucwastiaux/anki-quake3/master/code/python/Anki_Quake3.py) into **%APPDATA%\Roaming\Anki2\addons**
* Start-up Anki, you should see a red bar at the top saying *Quake III Anki - Waiting for connection*
* You are now ready to start a game, launch the game using **ioquake3.x86_64.exe +set sv_pure 0 +set vm_cgame 0 +set vm_game 0 +set vm_ui 0** (those command-line parameters are important, otherwise IOQuake3 may end up using code from the Steam install)
* Start a single player game. Wait a bit for the bots to join, then hit the **r** key to request rail slugs.
* Alt-tab into Anki. You should see a red progress bar at the top showing how many reviews you have to do. Do your reviews, you should hear a sound, and when you alt-tab into Quake3, you should now have 5 railgun slugs.

### Optional setup
Anki and Quake3 need two-way communication, and this is done using UDP sockets. Quake3 will open one on port 27960. The python script running the Anki add-on will open one on port 27975. This is configurable at the top of **Anki_Quake3.py**. You can change these ports if necessary.

This configuration entry (to be placed in **q3config.cfg**) allows you to change the host/port anki is listening on.
**seta cl_ankiHostPort "127.0.0.1:27975"**