RipMaster
=========
http://github.com/shidarin/RipMaster

Project Status
--------------

Active development, pre-beta.
Bugs still being squashed, check issues list on GitHub.
Code style should be pep-8 with google doctstrings and naming.

Description
-----------

Ripmaster's main goal is to take an extracted mkv from makeMkv, and take it
through all the intermediate steps needed to produce a high quality result mkv,
including audio tracks that handbrake can't pass through, and bluray subtitles
that handbrake can't convert.

Process
-------

It's assumed the user rips all the audio tracks, subtitles and movies themselves
into an MKV format, probably using MakeMKV. If the user doesn't want to rip
their own movies, there are other projects out there that will JUST do the
automated ripping. However, in my experience this process requires so much hand
holding (having to pick the right track, etc.) that it's better just to do it
manually.

After that, Ripmaster extracts subtitles from the MKV (since Handbrake cannot
handle those directly).

Ripmaster uses BDSupToSub to convert the subtitle sup files into a matching IDX
and SUB pair, while also checking for 'forced' subtitles. If it finds forced
subtitles, either in part or through the entire track, it creates an additional
'forced only' subtitle track. If the original track consists only of forced
subtitles, the 'normal' IDX and SUB pair are not created from that track,
leaving only the 'forced' result.

Handbrake then converts the video track, compressing it according to user
specified criteria. The converted mkv has no audio tracks, as all ripped
audio tracks are passed unmolested from the rip to the final mkv.

Finally, mkvmerge takes all resulting files (the original rip with audio, the
IDX-SUB subtitles, and the converted video), and merges them together, setting
flags on 'forced' tracks correctly, and maintaining default/forced flags on the
rest of the tracks.

If at any point in the process the computer crashes (normally during the
Handbrake encoding), Ripmaster starts from the last completed task.

Initial Setup
-------------

The following programs are required for Ripmaster to run:


    Python (2.6-2.7: http://www.python.org/)
    Java (http://java.com/en/download/index.jsp)
    MKVToolNix (http://www.bunkus.org/videotools/mkvtoolnix/)
        MKVToolNix contains MKVMerge, MKVInfo and MKVExtract
    BDSup2Sub (v5+ by mjuhasz: https://github.com/mjuhasz/BDSup2Sub/wiki)
    Handbrake with CLI (I recommend v9.6 at this time http://handbrake.fr/)



While you can rip to an MKV file using whatever you wish, MakeMKV is probably
the best option: http://www.makemkv.com/

User's need to edit Ripmaster.ini and enter the paths to BDSupToSub, Java,
HandBrakeCLI, mkvMerge, mkvExtract.

Users should also set their desired x264 speed, available options are:

    ultrafast
    superfast
    veryfast
    faster
    fast
    medium
    slow (default)
    slower
    veryslow

If you desire a fallback audio other than AC3, you should set that here too.
Options for fallback audio are:


    faac
    ffaac
    ffac3 (default)
    lame
    vorbis
    ffflac

But note that not all of these support full surround sound.

If you want to specify additional BFrames to be used with the 'animation' x264
tuning, set that with the Animation BFrames setting. If not present, only the
BFrames specified by the speed preset and tune will be used. This will be in
addition to the BFrames set by the speed preset, but will override the tune.

Default: None

If you want to adjust the movie order, you can change the sorting setting.

Options for sorting are:

    alphabetical (default)
    resolution (lowest res to highest)
    quality (lowest quality to highest)

You can also set the sorting to be reverse sorting with the sorting_Reverse
setting.

Sample Ripmaster.ini file:
```
================================================================================

[Programs]
BDSupToSub: C://Program Files (x86)/MKVToolNix/BDSup2Sub.jar
HandbrakeCLI: C://Program Files/Handbrake/HandBrakeCLI.exe
Java: C://Program Files (x86)/Java/jre7/bin/java
mkvExtract: C://Program Files (x86)/MKVToolNix/mkvextract.exe
mkvMerge: C://Program Files (x86)/MKVToolNix/mkvmerge.exe

[Handbrake Settings]
animation_BFrames: 8
audio_Fallback: ffac3
language: English
sorting: alphabetical
sorting_Reverse: no
x264_Speed: slow

[Base Encode Quality]
1080p: 20
720p: 20
480p: 20

[High Encode Quality]
1080p: 19
720p: 19
480p: 19

[Ultra Encode Quality]
1080p: 16
720p: 16
480p: 16

================================================================================
```
Leading and trailing whitespaces are automatically removed, but all entries
are case sensitive.

Users need to Rip their own movies from disk, preferably using MakeMKV, then
they need to decide on how they want each movie processed, this is done by
changing the folder name that contains a single or multiple mkv files.

Encoding Instructions
---------------------

A sample folder name might be:

    Akira__1080_hq_animation

Anything before the double underscore ('__') is considered the title of the
movie. Anything after is part of the instruction set.

RESOLUTION:

You at least need a resolution, accepted arguments for this are:

    1080, 720, 480

If you don't provide a target resolution, it tries to query the audio track to
resolve the image resolution and use that. If that resolve fails, we default to
1080.

QUALITY:

Optionally, you can provide a quality preset:

    uq, hq, bq

This preset will be cross referenced with the resolution to get the 'rf' quality
setting Handbrake will use for the video encode.

If you don't provide a quality, it defaults to 'bq' for the resolution.

X264 TUNING:

Selects the x264 tuning preset to be used. Options are:

    film
    animation
    grain
    stillimage
    psnr
    ssim
    fastdecode
    zerolatency

But it's recommended to only stick to 'film', 'animation', or 'grain'.

SET FPS:

Some material needs to be 'forced' to a certain fps, especially DVD material:

    30p, 25p, 24p

DE-INTERLACING:

If your file needs to be de-interlaced, give the instruction set:

    tv

And it will do a high quality de-interlacing pass.

How To:
-------

Save your mkv to a folder with the title of the movie and the encoding
instructions (see above). Place that folder in ripmaster's 'toConvert' folder,
which is where Ripmaster will search for movies to encode.

Double click on Ripmaster.py to begin the process.

If you want Ripmaster to automatically start up after a crash, place a shortcut
to Ripmaster.py in your startup folder, but be warned that EVERY time you start
your computer, Ripmaster will start with it. Just close the window if you don't
want Ripmaster doing things right now, the crash protection will pickup where
you left off.

Starting Fresh:
---------------

If you mess something up, or you want to start an entire encode batch over again
(say you changed the ini settings), simply delete the following from the folder:

    movies.p
    movies.p.bak

Once those are deleted, every movie ripmaster finds will be treated as a new
movie to be converted.
