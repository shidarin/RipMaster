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
from ast import literal_eval

# Ripmaster Imports
from apps import handBrake, mkvExtract, mkvInfo, bdSup2Sub

#===============================================================================
# VARIABLES
#==============================================================================

# Valid Instructions
INSTRUCTIONS = {
    '1080_uq': 1080,
    '1080_uq_animation': 1080,
    '1080_uq_film': 1080,
    '1080_uq_grain': 1080,
    '1080_hq': 1080,
    '1080_hq_animation': 1080,
    '1080_hq_film': 1080,
    '1080_hq_grain': 1080,
    '1080': 1080,
    '720_hq': 720,
    '720_hq_animation': 720,
    '720_hq_film': 720,
    '720_hq_grain': 720,
    '720': 720,
    '480_hq': 480,
    '480_hq_animation': 480,
    '480_hq_film': 480,
    '480_hq_grain': 480,
    '480_24p': 480,
    '480_30p': 480,
    '480_24p_tv': 480,
    '480_24p_animation': 480,
    '480_30p_tv': 480,
    '480_tv': 480,
    '480': 480
    }
#===============================================================================
# FUNCTIONS
#===============================================================================

# Utility

def get_movies(dir):
    """Gets the movies from the specified directory"""
    movielist = []

    directories = os.listdir(dir)
    for d in directories:
        # We need to remove directories without instruction sets
        if '__' not in d:
            directories.remove(d)
            continue
        files = os.listdir("{root}/{subdir}".format(root=dir, subdir=d))
        for f in files:
            if '--converted' not in f and '.mkv' in f:
                fullpath = os.path.join(dir, d, f).replace('\\', '/')
                movie = objects.Movie(filepath, )

def convert_filename(movieFile):
    """Converts movie filename to: safe filename, directory, and instructions

    Args:
        movieFile: (str)
            The MKV movie filename to be converted

    Raises:
        ValueError
            If no instruction set is found or not matching the whitelisted
            instruction sets, ValueError will be raised.

    Returns:
        string_escape: (str)
            A properly formatted filepath string

        directory: (str)
            The directory the file lives in

        instruction: (str)
            The instruction set for BDSup2Sub and Handbrake

    """

    # Convert from crazy windows formatting.
    string_escape = movieFile.replace("\\", "/")

    # Creates a list where each entry is a folder
    directory = string_escape.split("/")

    instruction = directory[-1].split('__')

    try:
        instruction = instruction[1].replace('.mkv', '')
    except IndexError: # No '__' present in filename
        raise ValueError(directory[-1] + ' has no instructions in name')

    if instruction not in INSTRUCTIONS:
        raise ValueError(instruction + ' is not a valid instruction string')

    # Joins directory listing back up, minus the file
    directory = "/".join(directory[:-1])

    return string_escape, directory, instruction

# Program Functions

def extract_tracks(file, directory):
    """extracts tracks per file"""

    videoTracks, audioTracks, subtitleTracks = mkvInfo(file)

    savedSubtitles = [] # Will be list of saved subtitle files
    savedAudio = []

    # Now to extract each pgs subtitle track, one at a time
    for track in subtitleTracks:
        if subtitleTracks[track] == 'pgs':
            command = str(track)
            command += ':'

            fileDest = directory + '/Track'
            fileDest += str(track)
            fileDest += 'subtitle.sup'

            savedSubtitles.append(fileDest)

            mkvExtract(file, command, fileDest)

    # Now to extract each TrueHD track, one at a time
    for track in audioTracks:
        if audioTracks[track] == 'truehd':
            command = str(track)
            command += ':'

            fileDest = directory + '/Track'
            fileDest += str(track)
            fileDest += 'audio.truehd'

            savedAudio.append(fileDest)

            mkvExtract(file, command, fileDest)

        elif audioTracks[track] == 'acm':
            # ACM Audio is not supported
            pass

    return savedSubtitles, savedAudio

def convert_subtitles(file, instruction):
    """Converts a subtitle file, saving one or more sub conversions"""

    # Converts our handbrake instruction indicator to BD resolution args
    resolution = INSTRUCTIONS[instruction]

    if resolution == 480:
        resolution = 'ntsc'
    else:
        resolution = str(resolution) + 'p'

    convertedFiles = []
    forced = False
    forcedOnly = True

    # Our only option flag is really resolution
    options = '-r ' + resolution

    destFile = file[:-4] + '.idx'
    convertedFiles.append(destFile)

    # Using deprecated os.popen (easier) to put shell output in list
    shellOut = bdSup2Sub(file, options, destFile, popen=True)

    # We need to check the results for FORCED subtitles
    #
    # If the amount of Forced subtitles is less than the total subs
    # We'll just create a new .idx file in addition to the default one.
    #
    # If the amount of Forced subtitles is the same as the total subs,
    # the entire subtitle track is forced, so we remove the resultFiles
    # and create a new FORCED .idx
    for line in shellOut:

        totalCount = 0

        if line.startswith('#'):
            lineList = line.split(' ')
            # The last count entry from BD will set the total
            try:
                totalCount = int(lineList[1])
            except ValueError:
                pass

        # There should only be 1 entry with 'forced' in it, that entry looks like:
        #
        # 'Detected 39 forced captions.'
        if 'forced' in line:
            forcedCaptions = line.replace('Detected ', '')
            forcedCaptions = int(forcedCaptions.replace(' forced captions.', ''))

            if forcedCaptions > 0:
                forced = True
            if forcedCaptions == totalCount:
                forcedOnly = True

    if forced:
        # If forced, we'll create a new _FORCED.idx in addition to the one already exported.
        options += ' -D'
        forcedFile = destFile[:-4] + '_FORCED.idx'
        bdSup2Sub(file, options, forcedFile)

        if forcedOnly:
            # If forcedOnly, we'll remove the first idx and sub filesets, leaving only
            # the FORCED idx and sub.
            os.remove(destFile)
            os.remove(destFile[:-4] + '.sub')

            # We'll also remove the deleted file from the resultFiles list.
            convertedFiles.remove(destFile)

        convertedFiles.append(forcedFile)

    return convertedFiles

def encode_movie(file, dest, instruction, speed):

    resolution = INSTRUCTIONS[instruction]

    WIDTH = {
        1080: 1920,
        720: 1280,
        480: 720
        }

    videoTracks, audioTracks, subtitleTracks = mkvInfo(file)

    # Before setting the initial option string, we need to override
    # the provided speed setting if we're on an Ultra Quality convert.
    if 'uq' in instruction:
        speed = 'veryslow'

    #
    # DESTINATION & VIDEO OPTIONS
    #

    # File Format, Chapter Markers, Encoder, Encoder Speed
    options = '-f mkv -m -e x264 --x264-preset ' + speed

    # Encoder Tuning
    instruction_list = instruction.split('_')
    if len(instruction_list) > 2:
        if instruction_list[2] != 'tv':
            options += ' --x264-tune ' + instruction_list[2]

    # Encoder Quality
    if 'uq' in instruction_list:
        quality = ultraQual[resolution]
    elif 'hq' in instruction_list:
        quality = highQual[resolution]
    else:
        quality = baseQual[resolution]

    options += ' -q ' + str(quality)

    # Encoder Framerate
    if '24p' in instruction_list:
        options += ' -r 23.976'
    elif '30p' in instruction_list:
        options += ' -r 29.97'

    options += ' --cfr'

    #
    # AUDIO OPTIONS
    #

    options += ' -a '
    for track in audioTracks:
        if audioTracks[track] != 'truehd':
            options += str(track) + ','
    options = options[:-1] # Remove trailing comma

    options += ' -E '
    for track in audioTracks:
        if audioTracks[track] != 'truehd':
            options += 'copy,'
    options = options[:-1]

    options += ' --audio-fallback ffac3'

    #
    # PICTURE SETTINGS
    #

    # Picture Resolution
    options += ' -w ' + str(WIDTH[resolution]) + ' --loose-anamorphic'

    #
    # FILTERS
    #

    if 'tv' in instruction_list:
        options += ' -d slower'

    #
    # SUBTITLES
    #

    vobsub = False

    options += ' -N ' + language
    for track in subtitleTracks:
        if subtitleTracks[track] == 'vobsub':
            vobsub = True
    if vobsub:
        options += ' -s scan'

    handBrake(file, options, dest)

#===============================================================================
# MAIN
#===============================================================================	

# XXX file.read() here
# XXX Set Java, BDSup2Sub and Handbrake vars
# Detect all new movies, add to newMovies list
# Remove movies from file listing
'''
newMovies = [
    "I:\Rips\RawBR\The_Expendables_2\The_Expendables_2__720.mkv",
    "I:\Rips\RawBR\Blood_Diamond\Blood_Diamond__720_hq_film.mkv",
    "I:\Rips\RawBR\Pacific_Rim\Pacific_Rim__1080_hq_film.mkv",
    "I:\Rips\RawBR\Saving_Private_Ryan\Saving_Private_Ryan__1080_hq_film.mkv"
]
'''
newMovies = []

# If we have results in the ini file, we'll save those to a pickle list
if newMovies:
    with open("new_movies.txt", "w") as f:
        for movie in newMovies:
            f.write("%s\n" % movie)
# If no results, we'll pick up where a crash might have left off
else:
    with open("new_movies.txt", "r") as f:
        newMovies = [line.strip() for line in f]

print newMovies

with open("extracted_movies.txt", "r") as f:
    tempMovies = [line.strip() for line in f]
    extractedMovies = []
    for entry in tempMovies:
        extractedMovies.append(literal_eval(entry))

with open("converted_movies.txt", "r") as f:
    convertedMovies = [line.strip() for line in f]

if newMovies == None:
    newMovies = []
if extractedMovies == None:
    extractedMovies = []
if convertedMovies == None:
    convertedMovies = []

# Conversion of filepath, extraction of audio and subtitles
if newMovies:
    extracted = []
    for movie in newMovies:

        # File is full filepath
        # Directory is filepath minus file
        # Instructions if instruction for dictionary for conversion

        print "Converting filename..."
        file, directory, instruction = convert_filename(movie)

        # savedSubtitle is list of saved subtitle files
        # savedAudio is list of saved TrueHD files

        print "Extracting Tracks..."
        savedSubtitles, savedAudio = extract_tracks(file, directory)

        convertedSubtitles = []

        print "Converting Subtitles..."
        for subtitle in savedSubtitles:
            convertedSubtitles.extend(convert_subtitles(subtitle, instruction))

        # Crash Protection

        thisMovie = [
            file,
            directory,
            instruction,
            convertedSubtitles,
            savedAudio
            ]

        extractedMovies.append(thisMovie)

        with open("extracted_movies.txt", "w") as f:
            for entry in extractedMovies:
                f.write("%s\n" % entry)

        # If script crashes on a movie after this, new_movies.p will only
        # contain movies that have not finished extraction.
        toExtract = []

        for entry in newMovies:
            toExtract.append(entry)

        extracted.append(movie)

        for entry in extracted:
            toExtract.remove(entry)

        with open("new_movies.txt", "w") as f:
            for entry in toExtract:
                f.write("%s\n" % entry)

    with open("new_movies.txt", "r") as f:
        newMovies = [line.strip() for line in f]

    if newMovies == None:
        newMovies = []

# Conversion of movie file
if extractedMovies:
    converted = []
    for movie in extractedMovies:
        file = movie[0]
        directory = movie[1]
        instruction = movie[2]
        convertedSubtitles = movie[3]
        savedAudio = movie[4]

        destination = file[:-4] + '--Converted.mkv'

        print "Encoding movie", destination
        encode_movie(file, destination, instruction, speed)

        convertedMovies.append(destination)
        with open("converted_movies.txt", "w") as f:
            for entry in convertedMovies:
                f.write("%s\n" % entry)

        toConvert = []

        for entry in extractedMovies:
            toConvert.append(entry)

        converted.append(movie)

        for entry in converted:
            toConvert.remove(entry)

        with open("extracted_movies.txt", "w") as f:
            for entry in toConvert:
                f.write("%s\n" % entry)

    with open("extracted_movies.txt", "r") as f:
        tempMovies = [line.strip() for line in f]
        extractedMovies = []
        for entry in tempMovies:
            extractedMovies.append(literal_eval(entry))

    if extractedMovies == None:
        extractedMovies = []

raw_input("Press enter to exit")