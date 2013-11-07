#/usr/bin/python
# Ripmaster.apps
# Module containing various app callouts
# By Sean Wallitsch, 2013/11/04

#===============================================================================
# IMPORTS
#===============================================================================

import os

#===============================================================================
# VARIABLES
#===============================================================================

# TODO: Replace this with a file read!

# Java
java = '"C:/Program Files (x86)/Java/jre7/bin/java"'

# BDSup2Sub.jar
BD = '"C:/Program Files (x86)/MKVToolNix/BDSup2Sub.jar"'

# HandBrake CLI
HandBrake = 'C:/Program Files/Handbrake/HandBrakeCLI.exe'

#===============================================================================
# FUNCTIONS
#===============================================================================

def handBrake(file, options, dest):
    """CLI command builder for converting video and audio with Handbrake

    Args:
        file : (str)
            The source file the video and audio tracks are to be converted from.

        options : (str)
            The option command line arguments to pass to handbrake

        dest : (str)
            The destination file to write to.

    Raises:
        N/A

    Returns:
        None

    """
    c = '""' + HandBrake + '"' + ' -i ' + file + ' -o ' + dest + ' ' + \
        options + '"'
    print "HandBrake Settings:"
    print c
    os.system(c)


def mkvExtract(file, command, dest):
    """CLI command builder for extracting tracks with mkvextract

    Args:
        file : (str)
            The source file the tracks are to be extracted from.

        command : (str)
            The track command to be executed. Usually looks like: '3:'.

        dest : (str)
            The destination file to be written to.

    Raises:
        N/A

    Returns:
        None

    The full filepath this builds should look like:

    '"mkvextract tracks I:/src/fold/file.mkv 3:I:/dest/fold/subtitle.sup "'

    """
    os.system('"mkvextract tracks ' + file + ' ' + command + dest + ' "')


def mkvInfo(file):
    """Uses CLI to fetch names all audio, video and subtitle tracks from a mkv

    Args:
        file : (str)
            The file to get the info from

    Raises:
        N/A

    Returns:
        [[str], [str], [str]]
            A list contraining a list of video tracks, audio tracks and subtitle
            tracks.

    """

    # mkvMerge will return a listing of each track
    info = os.popen('"mkvmerge -i ' + file + '"').read()
    info = info.split('\n')

    # info is now a list, each entry a line
    #
    # Example:
    #
    # File 'I:\Rips\RawBR\Jack_Reacher\Jack_Reacher_t01.mkv': container: Matroska
    # Track ID 0: video (V_MPEG4/ISO/AVC)
    # Track ID 1: audio (A_AC3)
    # Track ID 2: audio (A_TRUEHD)
    # Track ID 3: subtitles (S_HDMV/PGS)

    AUDIO_TYPES = {
        '(A_AAC)\r': 'aac',
        '(A_DTS)\r': 'dts',
        '(A_AC3)\r': 'ac3',
        '(A_TRUEHD)\r': 'truehd',
        '(A_MP3)\r': 'mp3',
        '(A_MS/ACM)\r': 'acm',
        }

    SUBTITLE_TYPES = {
        '(S_VOBSUB)\r': 'vobsub',
        '(S_HDMV/PGS)\r': 'pgs'
        }

    trackList = []

    for line in info:
        if 'Track ID' in line:
            trackList.append(line)

    # trackList now only contains the lines with Track in them

    subtitleTracks = {}
    audioTracks = []
    videoTracks = [] # No plans to use video tracks for now

    for line in trackList:
         # Splitting on ':' gives us the ID on one side, the type on the other
        lineList = line.split(':')

        if 'subtitles' in lineList[1]:
            TrackID = int(lineList[0].replace('Track ID ', ''))
            subtitleTracks[TrackID] = lineList[1].replace(' subtitles ', '')
            subtitleTracks[TrackID] = SUBTITLE_TYPES[subtitleTracks[TrackID]]

        elif 'audio' in lineList[1]:
            track = AudioTrack(file)
            track.trackID = int(lineList[0].replace('Track ID ', ''))
            track.fileType = AUDIO_TYPES[lineList[1].replace(' audio ', '')]
            audioTracks.append(track)

        elif 'video' in lineList[1]:
            videoTracks.append(int(lineList[0].replace('Track ID ', '')))

    return videoTracks, audioTracks, subtitleTracks


def bdSup2Sub(file, options, dest, popen=False):
    """CLI command builder for converting susbtitles with BDSup2Sub

    Args:
        file : (str)
            The source file the subtitles must be converted from.

        options : (str)
            Resolution, Forced Only and other CLI commands for BDSup2Sub

        dest : (str)
            Destination filename to be written to. If a pair of files, BDSup2Sub
            will automatically write the paired file based off this string.

        popen=False : (bool)
            If True, os.popen will be used rather than os.system, and the read()
            method will be returned, rather than just executed.

    Raises:
        N/A

    Returns:
        [str]
            If popen=True, the console output of BDSup2Sub will be returned as a
            list.

    """
    c = '"' + java + ' -jar ' + BD + ' ' +  options +\
        ' -o ' + dest + ' ' + file + '"'

    if popen:
        return os.popen(c).read().split('\n')
    else:
        os.system(c)

