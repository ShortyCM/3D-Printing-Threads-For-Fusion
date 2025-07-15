Here's a python script I've come up with in an attempt to handle modelled threads for 3D printing to try to compensate for the
nature of that manufacturing method. As anyone familiar with 3D printing will tell you, printing threads can be kind of hit and
miss. A lot of the time you're better off chasing the printed threads with a tap or die to clean them up, as leaving them as they
came off the printer means you have to deal with some relatively poor tolerances. And that usually means things might have trouble
fitting, most particularly when both the male and female parts are printed. This isn't perfect, but so far I've found it to be
pretty helpful at not having to mess around with threads after printing to clean them up. Sometimes the compensation provided by
this script is enough all on its own, and as threads get smaller it can help to combine this compensation with variable layer
heights in the slicer. (For example, a 0.5 mm thread pitch printed with the standard 0.2 mm layer height could have the threads
skip past each other with a little bit of pressure, but using variable layer heights solves this. The 0.5 mm threads work as
intended in that case. You'll likely have less issues with your threads if you use variable layer heights regardless of the thread
pitch, anyway.) I've been having good luck with my Bambu Labs X1-Carbon and this script for the last little while, and figured
others might also find it helpful.

The script looks in your Windows user\appdata directory to find the directory where Fusion 360 stores its thread definitions files.
Since new updates to the app mess around with this folder structure, and the threads definition files, it contains some code to
find the right spot, so it should continue to work as new updates are released. Just run it again after an app update. Once it
finds the definitions it reads all the xml files in the directory and creates copies with some offsets applied according to thread
pitch to help compensate for the printing process. This leaves the originals as they were, only creating new files to go alongside
them. If this is not the first time you've run it, perhaps you've edited the offset coefficient and need to regenerate, it first
deletes any old "-3Dprinting" copies, and then generates the new files. Once you fire up Fusion 360 you'll find the threads dialog
dropdown now contains the usual threads selections, as well as copies for 3D printing.

While testing this I first tried just using a single offset for all the threads, but that didn't work very well at all. Smaller
thread pitches don't seem to need as much compensation as larger pitches do. And at a certain point there also doesn't seem to
be any need to continue using more and more compensation. So I've made it use smaller offsets for smaller thread pitches, and as
the thread pitches get larger the compensation tops out at 0.2 mm, as I haven't found that I've needed any more than that. This is
probably related to both the layer heights and the nozzle diameter, of which I usually use 0.2 mm layer height and a 0.4 mm nozzle,
as I'm sure is popular. So I think for most people this will work as-is, but if you're using a different nozzle and/or layer
heights then you might want to tweak things a bit. The coefficient and the ceiling are the first things listed, so you don't have
to go hunting for them if you are going to try playing with them.

So far, this seems to work at least down to 0.5 mm thread pitches, and I've tried up to as large as 8 TPI (3.175 mm), and things
seem to be alright. Even down to 0.5 mm with a 0.2 mm layer height isn't too bad, but you'll obviously get smoother threads if
you're also using smaller/variable layer heights once you start going to smaller threads like that. Naturally, you'll probably get
better results with 3D printing if you're using threads a little larger than 0.5 mm, though. Hehe. But they do work. I haven't
tried any smaller than that.

Anyway, here's the code. If you don't have python installed, and for whatever reason don't want to install it, I could make up a
one-file exe with pyinstaller, I suppose, but I figured most of the 3D printing crowd probably wouldn't mind installing python, if
they don't already have it installed anyway.

**2024-06-12 update: I have updated the script to do two things. First, it now checks the creation dates of the directories to
ensure it is actually working on the latest directory. That way when Fusion 360 updates come out it will actually find the right
directory to work with. Second, it will now also copy any custom threads xml files that you keep in the same directory as the
script to the latest working directory. It does this before the 3D printing tweaks, so that your custom threads files will also get
3D printing versions.

**2024-07-13 update: I've upped the ceiling from 0.2 mm to 0.3 mm because of an experience I had over the last week. I did a job
for a buddy of mine that required some M80x6 threads, and there seemed to be a problem with such a large thread pitch. It was
pretty tight, so I decided to change the ceiling from 0.2 mm to 0.4 mm and try the parts again. That time they fit, but I felt the
fit was a bit looser than necessary, so I've updated the script now to try using a 0.3 mm script. I didn't print those parts again,
because even though it was a little more wiggle than I'd prefer, they went together nicely and worked as intended. But since the
original 0.2 mm ceiling resulted in parts that were a little too tight I've bumped it to 0.3 mm. Naturally, this will only make a
difference on thread pitches that are larger than 1.25 mm, as the offsets will be the same at that pitch and below. This means
thread pitches between 1.25 mm and 1.875 mm will now scale from between 0.2 mm and 0.3 mm offsets, and above 1.875 mm will use that
0.3 mm ceiling now.

**2024-07-27 update: Threads tested so far:

M2.5x0.45

M3x0.5

M4.5x0.5

M15x1.5

M18x2.5

M23x0.6

M25x2

M35x1.5

M80x6

5-40 UNC (#5, 0.125")

1/4-20 UNC

1/4-28 UNF

5/16-18 UNC

3/8-16 UNC

1/2-28 UNEF

5/8-28 UN

3/4-20 UNEF

3/4-32 UN

13/16-32 UN

1-20 UNEF (1")

1-40 UN (1")
