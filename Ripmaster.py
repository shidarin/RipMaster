#/usr/bin/python
# Ripmaster
# A python script to string and automate various ripping processes
# By Sean Wallitsch, 2013/09/04

"""

Description
-----------

The purpose of Ripmaster is to string together several processes that, done
through GUIs, are time consuming and error prone.

It's assumed the user rips all the audio tracks, subtitles and movies themselves
into an MKV format, probably using MakeMKV.

After that, Ripmaster extracts subtitles and TrueHD audio tracks from the MKV
(since Handbrake cannot handle those directly).

Ripmaster uses BDSupToSub to convert the subtitle sup files into a matching IDX
and SUB pair, while also checking for 'forced' subtitles. If it finds forced
subtitles, either in part or through the entire track, it creates an additional
'forced only' subtitle track. If the original track consists only of forced
subtitles, the 'normal' IDX and SUB pair are not created from that track,
leaving only the 'forced' result.

Handbrake then converts the video track, compressing it according to presets,
and auto-passing through all audio tracks (except TrueHD, which it cannot
handle). 

Finally, mkvmerge takes all resulting files (the IDX-SUB subtitles, the TrueHD
audio (if present) and the converted video), and merges them together, setting
flags on 'forced' tracks correctly, and setting TrueHD as the default audio
track if it's present.

If at any point in the process the computer crashes (normally during the
Handbrake encoding), Ripmaster starts from the point last left off. It does this
by pickle-saving lists at various points during the process, removing movies one
by one as they complete the step in the chain.

When Ripmaster recovers, it actually goes through the steps backwards- first it
checks if there are finals to merge with mkvmerge, then if there are movies to
encode with handbrake, finally if there are subtitles and audio to rip.

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

User's need to edit Ripmaster.ini and enter the paths to BDSupToSub, Java and
HandBrakeCLI. Users need to convert windows \s into /s for these install
locations, but that is not required for the movie files.

Users should also set their desired x264 speed, available options are:
ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow

Sample Ripmaster.ini file:

================================================================================

Java = C:/Program Files (x86)/Java/jre7/bin/java
BDSupToSub = C:/Program Files (x86)/MKVToolNix/BDSup2Sub.jar
HandbrakeCLI = C:/Program Files/Handbrake/HandBrakeCLI.exe

x264 Speed = slow
Baseline Quality
    1080p = 20
    720p = 20
    480p = 20
High Quality
    1080p = 19
    720p = 19
    480p = 19
Ultra Quality
    1080p = 10
    720p = 10
    480p = 10

Language = English

================================================================================

Leading and trailing whitespaces are automatically removed, but all entries
are case sensitive. Make sure there's still a space between the argument
and the '=' sign.

Users need to Rip their own movies from disk, preferably using MakeMKV, then
they need to decide on how they want each movie processed, editing the .mkv
file according to the instructions below (See Encoding Instructions).

Then, they simply need to add the filepath to a newline in between the <MOVIES>
and </MOVIES> tags.

Ripmaster will automatically remove the movie files once the first step- the
extraction of TrueHD audio with extraction and conversion of subtitles- is
completed.

Encoding Instructions
---------------------

In the above example, you can see the mkv file has an additional suffix attached
to the end of the filename, seperated by a '__' (double underscore). That string
will be used by both BDSupToSub and Handbrake to choose the proper resolution
and encoding and MUST be present or Ripmaster won't know what to do with the
file, Ripmaster does NOT have any default, you must be explicit.

Currently Ripmaster supports the following instruction strings:

    What you want										What you type
    -------------										-------------

    1080p:
         (Ultra Quality- NOT efficient)
        Ultra Quality									__1080_uq
        Ultra Quality Animation							__1080_uq_animation
        Ultra Quality Film								__1080_uq_film
        Ultra Quality Grain								__1080_uq_grain
         (High Quality- A good pick for 1080)
        High Quality									__1080_hq
        High Quality Animation							__1080_hq_animation
        High Quality Film								__1080_hq_film
        High Quality Grain								__1080_hq_grain
         (Low Quality- suggest to go down to 720)
        Low Quality										__1080
    720p:
        High Quality									__720_hq
        High Quality Animation							__720_hq_animation
        High Quality Film								__720_hq_film
        High Quality Grain								__720_hq_grain
        Low Quality										__720
    480p (from HD):
        High Quality									__480_hq
        High Quality Animation							__480_hq_animation
        High Quality Film								__480_hq_film
        High Quality Grain								__480_hq_grain
         (from DVD)
        Average 24p (Force 23.976 constant frame rate)	__480_24p
        Average 60p (Force 29.97 constant frame rate)	__480_30p
        Average 24p De-interlace						__480_24p_tv
        Average 60p De-interlace						__480_30p_tv
        Average De-interlace							__480_tv
        Average											__480

Again, these instructions are NOT OPTIONAL and must be present at the end of the
file string.

Other Notes
-----------

You might notice certain block comments go longer than 80 characters due to
indentation. This was the cleanest method of still presenting those example
strings in the best fashion. I am sorry.

"""

#===============================================================================
# IMPORTS
#===============================================================================

# Standard Imports
import os

# Ripmaster Imports
from tools import Config, Movie

#===============================================================================
# FUNCTIONS
#===============================================================================

# Utility

def get_movies(dir):
    """Gets the movies from the specified directory"""
    movieList = []

    directories = os.listdir(dir)
    for d in directories:
        # We need to remove directories without instruction sets
        if '__' not in d:
            directories.remove(d)
            continue
        files = os.listdir("{root}/{subdir}".format(root=dir, subdir=d))
        for f in files:
            if '--converted' not in f and '.mkv' in f:
                movie = Movie(dir, d, f)
                movieList.append(movie)

    return movieList

#===============================================================================
# MAIN
#===============================================================================	

def main():
    # TODO: Allow users to supply alt configs?
    config = Config('./Ripmaster.ini')
    config.debug()

    root = os.getcwd() + '/toConvert/'

    # TODO: Implement crash protection again by reading pickled movielist.
    movies = []

    print ""
    print "Found the following movies in progress:"
    for entry in movies:
        print entry.path
    print ""
    print "Adding the following new movies:"

    newMovies = get_movies(root)

    for movie in movies:
        for raw in newMovies:
            if movie.path == raw.path:
                newMovies.remove(raw)
            else:
                print raw.path

    print ""

    movies.extend(newMovies)

    # TODO: Save Point

    for movie in movies:
        if not movie.extracted:
            movie.extractTracks()
            # TODO: Save Point
    for movie in movies:
        if not movie.converted:
            movie.convertTracks()
            # TODO: Save Point
    for movie in movies:
        if not movie.encoded:
            movie.encodeMovie()
            # TODO: Save Point
    for movie in movies:
        if not movie.merged:
            # TODO: Add mkvMerge
            pass

if __name__ == "__main__":
    main()

raw_input('Press enter to close')