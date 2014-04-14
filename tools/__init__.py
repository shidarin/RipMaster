#/usr/bin/python
# Ripmaster.tools
# Module containing tools used by Ripmaster
# By Sean Wallitsch, 2013/11/10

"""

Description
-----------

This module contains all the classes that Ripmaster uses to represent the files
and processes on disk.

Classes
-------

AudioTrack
    Represents a single audio track within a <Movie>. Each AudioTrack in the mkv
    gets an AudioTrack object, not just ones Handbrake can't handle.

Config
    The Config object reads the Ripmaster.ini file for all the user set
    configuration options.

Movie
    Represents a single mkv file, contains <AudioTrack>s and <SubtitleTracks>s.
    Calls all the extraction and conversion methods of it's children.

SubtitleTrack
    Represents a single subtitle track within a <Movie>. Each subtitle track in
    the mkv gets a SubtitleTrack object, not just the ones Handbrake can't
    handle. Since one subtitle track can contain both forced and non-forced
    subtitles, it's possible that a single subtitle track gets split into
    two subtitle tracks- one forced and the other containing every subtitle
    (both forced and not forced).

Functions
---------

bdSup2Sub()
    CLI command builder for converting subtitle tracks with BDSup2Sub. For all
    intents and purposes, this is the BDSup2Sub application.

handbrake()
    CLI command builder for converting video and audio with Handbrake. For all
    intents and purposes, this is the Handbrake application.

mkvExtract()
    CLI command builder for extracting tracks with mkvextract. For all intents
    and purposes, this is the mkvextract application.

mkvInfo()
    Uses mkvmerge to fetch names, filetypes and trackIDs for all audio, video
    and subtitle tracks from a given mkv.

mkvMerge()
    Merges a converted movie, converted subtitles and any extracted audio tracks

"""

#===============================================================================
# IMPORTS
#===============================================================================

# Standard Imports
from ast import literal_eval
import ConfigParser
import os
from subprocess import Popen, PIPE

#===============================================================================
# GLOBALS
#===============================================================================

AUDIO_FALLBACKS = [
    'faac',
    'ffaac',
    'ffac3',
    'lame',
    'vorbis',
    'ffflac',
    ]
RESOLUTIONS = [1080, 720, 480]
RESOLUTION_WIDTH = {1080: 1920, 720: 1280, 480: 720}
QUALITY = ['uq', 'hq', 'bq']
H264_PRESETS = [
    'animation',
    'film',
    'grain',
    'psnr',
    'ssim',
    'fastdecode',
    'zerolatency'
]
FPS_PRESETS = ['30p', '25p', '24p']
EXTRACTABLE_AUDIO = ['pcm', 'truehd']
EXTRACTABLE_SUBTITLE = ['pgs']
BFRAMES = {
    'ultrafast': 0,
    'superfast': 3,
    'veryfast': 3,
    'faster': 3,
    'fast': 3,
    'medium': 3,
    'slow': 3,
    'slower': 3,
    'veryslow': 8,
    'placebo': 16
}
SAMPLE_CONFIG = """[Programs]
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
480p: 16"""

#===============================================================================
# PRIVATE FUNCTIONS
#===============================================================================

def _stripAndRemove(string, remove=None):
    """Strips whitespace and optional chars from both sides of the target string.

    Args:
        target : (str)
            The string to strip leading and trailing whitespace from

        remove=None : (str)
            The string to remove from the string

    Raises:
        N/A

    Returns:
        (str)
            The target string after being stripped on either end.

    """

    stringStripped = string.lstrip().rstrip()
    stringRemoved = stringStripped.replace(remove, '')
    stringFinal = stringRemoved.lstrip().rstrip()

    return stringFinal

def _trackInfo(line):
    """Takes a track line from mkvmerge -I and returns track information

    Args:
        line : (str)
            A single line from mkvmerge -I's result.

    Raises:
        ValueError
            Will be raised if line fed to _trackInfo is not a trackID line, or
            known track type.

    Returns:
        (int), (str), (dict)
            The track ID, the track type, and a dictionary
            with additional information.

    """
    # If we are for some reason fed a line without a TrackID, raise
    if not line.startswith('Track ID'):
        raise ValueError, line + ' is not a Track ID line.'

    # trackID identifies which track this is of the original mkv.
    trackID = int(line.split(':')[0].replace('Track ID ', ''))

    # The track type is right after the trackID. We'll make sure we find the
    # actual track type (and not part of a title or other text) by including
    # the whitespace and punctuation that surrounds it.
    if ': video (' in line:
        trackType = 'video'
    elif ': audio (' in line:
        trackType = 'audio'
    elif ': subtitles (' in line:
        trackType = 'subtitles'
    else:
        raise ValueError, line + ' does not contain a known track type.'

    # By splitting on the opening and removing the closing bracket, we'll
    # be left with only the track dictionary, but it will be in string form.
    trackDict = line.split('[')[-1].replace(']\r\n', '')

    # We need to add " marks around all entries, and comma seperate entries.
    trackDict = trackDict.replace(' ', '", "')
    trackDict = trackDict.replace(':', '": "')
    trackDict = '{"' + trackDict + '"}'
    trackDict = literal_eval(trackDict)

    # Now we need to set some defaults. It's possible the track dictionary
    # doesn't have these, and we'll be referencing them later.

    trackDict.setdefault('default_track', '0')
    trackDict.setdefault('forced_track', '0')
    trackDict.setdefault('language', 'eng')

    return trackID, trackType, trackDict

#===============================================================================
# CLASSES
#===============================================================================

class AudioTrack(object):
    """A single audio track.

    Args:
        movie : (<Movie>)
            The parent <Movie> object that this <AudioTrack> is a child of.

        trackID : (str)
            The trackID of the audio track this object is to represent.

        fileType : (str)
            The filetype of this audiotrack.

    """
    def __init__(self, movie, trackID, fileType, infoDict):
        self.movie = movie
        self.trackID = trackID
        self.fileType = fileType
        self.info = infoDict
        self.extracted = False
        self.extractedAudio = None

        self.default = True if self.info['default_track'] == '1' else False

    def extractTrack(self):
        """Extracts the audiotrack this object represents from the parent mkv"""
        command = "{trackID}:".format(trackID=self.trackID)

        # Derive the location to save the track to
        fileName = self.movie.fileName.replace('.mkv', '')
        fileName += "_Track{TrackID}_audio.{ext}".format(
            TrackID=self.trackID,
            ext=self.fileType
        )

        self.extractedAudio = os.path.join(
            self.movie.root,
            self.movie.subdir,
            fileName
        ).replace('\\', '/')

        print ""
        print "Extracting trackID {ID} of type {type} from {file}".format(
            ID=self.trackID,
            type=self.fileType,
            file=self.movie.path
        )
        print ""

        mkvExtract(self.movie.path, command, self.extractedAudio)

        self.extracted = True

class Config(object):
    """ Class containing the basic encoding environment as described by the .ini

    Args:
        iniFile : (str)
            Ripmaster's configuration file

    Sample config file:

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

    Leading and trailing whitespaces are automatically removed, but all entries
    are case sensitive.

    """

    config = None

    # Programs
    handBrake = ''
    java = ''
    mkvExtract = ''
    mkvMerge = ''
    sup2Sub = ''

    # Handbrake Settings
    bFrames = None
    audioFallback = 'ffac3'
    language = 'English'
    sorting = 'alphabetical'
    sortingReverse = False
    x264Speed = 'slow'

    # Encode Qualities
    quality = {'uq': {}, 'hq': {}, 'bq': {}}

    def __init__(self, iniFile):
        # This will either return True or raise an exception
        if self.checkConfig(iniFile):
            try:
                self.getSettings(iniFile)
            except (ConfigParser.NoOptionError,
                    ConfigParser.NoSectionError), ex:
                # NoOptionError strings to:
                # No option 'djkas' in section: 'Programs'
                # NoSectionError strings to:
                # No section: 'Programsss'
                # Both are index 2
                error = str(ex).split()[2].replace("'", '')

                if ex.__class__ is ConfigParser.NoOptionError:
                    exception = 'option'
                    # We also want to add the section to option errors, so
                    # we'll pull it from the last index.
                    error += " from section: "
                    error += str(ex).split()[-1].replace("'", '')
                elif ex.__class__ is ConfigParser.NoSectionError:
                    exception = 'section'

                message = "Missing the ini {type}: {err}. Please fill the " \
                          "missing options and retry.".format(
                    type=exception,
                    err=error,
                )
                raise ValueError(message)

    def checkConfig(self, iniFile):
        """Checks that the iniFile provided actually exists. Creates if not.

        Args:
            iniFile : (str)
                Config File location

        Raises:
            IOError
                Raised if config file is missing.

        Returns:
            If IOError not raised, that means a config file was found and this
            will return True

        """
        if os.path.exists(iniFile):
            return True
        else:
            with open(iniFile, "w") as f:
                f.write(SAMPLE_CONFIG)
            errorMsg = "\nPROCESS WILL FAIL\nYou were missing the .ini file. " \
                       "I had to create one for you. You'll find it in " \
                       "Ripmaster's folder, called Ripmaster.ini - You need " \
                       "to specify the path for the various applications\n"
            raise IOError(errorMsg)

    @classmethod
    def getSettings(cls, iniFile):
        """Opens the ini file, splits the lines into a list, and grabs input"""
        print "Reading config from:", iniFile

        with open(iniFile, "r") as f:
            cls.config = ConfigParser.ConfigParser()
            cls.config.readfp(f)
            cf = cls.config

            # Grab all of our 'Programs' settings
            cat = 'Programs'
            cls.sup2Sub = cf.get(cat, 'BDSupToSub')
            cls.handBrake = cf.get(cat, 'HandbrakeCLI')
            cls.java = cf.get(cat, 'Java')
            cls.mkvExtract = cf.get(cat, 'mkvExtract')
            cls.mkvMerge = cf.get(cat, 'mkvMerge')

            def optionalGet(category, option, default, allowed=None, type=str):
                """Returns provided default if option not found

                Args:
                    category : (str)
                        The settings category to search in

                    option : (str)
                        The option to search for

                    default : (str|int|bool)
                        The default value to return if bad/no value found

                    allowed=None : [str|int]
                        If given, only values found in this list will be
                        accepted

                    type=str : (<str>|<int>|<bool>)
                        The type of input we're looking for. Will use a
                        different get method for each.

                Raises:
                    N/A

                Returns:
                    (str|int|bool)
                        The result found in the config file, or the default if
                        that isn't found/isn't in the allowed list."""
                if type == str:
                    get = cf.get
                elif type == int:
                    get = cf.getint
                elif type == bool:
                    get = cf.getboolean

                try:
                    result = get(category, option)
                except (
                    ConfigParser.NoOptionError,
                    ConfigParser.NoSectionError,
                    ValueError
                ):
                    return default

                if allowed and result not in allowed:
                    return default
                else:
                    return result

            cat = 'Handbrake Settings'
            # All the Handbrake settings are optional, so if the settings
            # aren't found we just leave it at the default.
            cls.bFrames = optionalGet(
                cat, 'animation_BFrames', cls.bFrames, type=int
            )
            cls.audioFallback = optionalGet(
                cat, 'audio_Fallback', cls.audioFallback,
                allowed=AUDIO_FALLBACKS
            )
            cls.language = optionalGet(
                cat, 'language', cls.language, allowed=['English']
            )
            cls.sorting = optionalGet(
                cat, 'sorting', cls.sorting, allowed=[
                    'alphabetical', 'quality', 'resolution'
                ]
            )
            cls.sortingReverse = optionalGet(
                cat, 'sorting_Reverse', cls.sortingReverse, type=bool
            )
            cls.x264Speed = optionalGet(
                cat, 'x264_Speed', cls.x264Speed, allowed=BFRAMES
            )

            # Quality catagories are also optional, defaulting to 20.
            qualityCats =  [
                'Base Encode Quality',
                'High Encode Quality',
                'Ultra Encode Quality',
            ]
            qualityLevels = ['bq', 'hq', 'uq']
            for i in xrange(3):
                cat = qualityCats[i]
                level = qualityLevels[i]
                dict = cls.quality[level]

                dict['1080'] = optionalGet(cat, '1080p', 20, type=int)
                dict['720'] = optionalGet(cat, '720p', 20, type=int)
                dict['480'] = optionalGet(cat, '480p', 20, type=int)

    @classmethod
    def debug(cls):
        """Prints the current configuration"""
        print "Java at:", cls.java
        print "BDSup2Sub at:", cls.sup2Sub
        print "Handbrake at:", cls.handBrake
        print "mkvMerge at:", cls.mkvMerge
        print "mkvExtract at:", cls.mkvExtract
        print "x624speed set to:", cls.x264Speed
        print "Default language:", cls.language
        print "Audio Codec Fallback:", cls.audioFallback
        print "Sorting is set to:", cls.sorting
        print "Sorting reverse is:", cls.sortingReverse
        print "Quality dictionary:"
        for entry in cls.quality:
            print entry + ":", cls.quality[entry]

class Movie(object):
    """A movie file, with all video, audio and subtitle tracks

    Args:
        root : (str)
            The root folder that contains all the movie folders

        subdir : (str)
            The folder that contains this mkv directly. Instruction set should
            be in the folder name. Should be something like:
                Akira__1080_hq_animation

        fname : (str)
            The filename itself

    """
    def __init__(self, root, subdir, fname):
        self.root = root
        self.subdir = subdir
        self.fileName = fname

        self.path = os.path.join(
            self.root,
            self.subdir,
            self.fileName
        ).replace('\\', '/')

        self.destination = self.path.replace('.mkv', '--converted.mkv')

        self.resolution = None
        self.quality = None
        self.preset = None
        self.tv = False
        self.fps = None

        self._getInstructions()

        # Subtitle and Audio Tracks
        # TODO: Support multiple video tracks per file?
        self.videoTracks = []
        self.audioTracks = []
        self.subtitleTracks = []

        self.vobsub = False

        self._getTracks()

        # If we don't have a resolution from instructions, we need to grab it
        # from the first video track
        if not self.resolution:
            # pixel_dimensions in the video dictionary will return something
            # formatted like '1920x1080'
            self.resolution = self.videoTracks[0][1]['pixel_dimensions']
            self.resolution = int(self.resolution.split('x')[-1])
            # But if it's not a valid resolution, we'll default to 1080
            if self.resolution not in RESOLUTIONS:
                self.resolution = 1080

        # Now that we're gauranteed to have a resolution, we can find the
        # quality if it wasn't provided.
        # If our self.quality is in the QUALITY list, it hasn't been set to a
        # numerical quantity yet.
        if self.quality in QUALITY:
            self.quality = Config.quality[self.quality][str(self.resolution)]

        # Progress

        self.extracted = False
        self.converted = False
        self.encoded = False
        self.merged = False

    def _getInstructions(self):
        """Parses the directory name to grab all the given instructions"""
        try:
            instructionSet = self.subdir.split('__')[-1].split('_')
        except IndexError: # No '__' present in filename
            instructionSet = []

        # This is comparing against global variables at the top of the module
        for size in RESOLUTIONS:
            if str(size) in instructionSet:
                self.resolution = size
        for level in QUALITY:
            if level in instructionSet:
                if self.resolution:
                    self.quality = Config.quality[level][str(self.resolution)]
                else:
                    # This may seem odd- we set the quality to a provided string
                    # instead of the int stored in the quality dictionary, but
                    # we have no way of getting that int from the quality dict
                    # without a provided resolution. Since we have no res, we
                    # have to wait until we derive the resolution manually.
                    self.quality = level
        for preset in H264_PRESETS:
            if preset in instructionSet:
                self.preset = preset
        for fps in FPS_PRESETS:
            if fps in instructionSet:
                # We need to remove the 'p' off the back of the '30p'
                self.fps = int(fps.replace('p', ''))
        if 'tv' in instructionSet:
            self.tv = True

    def _getTracks(self):
        """Runs mkvInfo on the file to grab all the tracks, creating them"""
        videoTracks, audioTracks, subtitleTracks = mkvInfo(self)

        self.videoTracks = videoTracks
        self.audioTracks = audioTracks
        self.subtitleTracks = subtitleTracks

    def extractTracks(self):
        """Extracts relevant tracks"""

        for track in self.videoTracks:
            # TODO: Multiple video track support
            pass

        for track in self.audioTracks:
            # We're pulling every audio track present in the source mkv
            # straight into the final merge mkv, so no need to extract
            pass

        for track in self.subtitleTracks:
            if track.fileType in EXTRACTABLE_SUBTITLE:
                if not track.extracted:
                    track.extractTrack()

        self.extracted = True

    def convertTracks(self):
        """Converts subtitles to correct res and fileType"""

        # TODO: Is there an audio codec that handbrake AND mkvMerge can't
        # read?

        for track in self.subtitleTracks:
            if not track.converted:
                track.convertTrack()

        self.converted = True

    def encodeMovie(self):
        """Encodes the video, supported audio and subtitle tracks"""

        #
        # VIDEO OPTIONS
        #

        # File Format, Chapter Markers, Encoder, Encoder Speed
        options = '-f mkv -m -e x264 --x264-preset ' + Config.x264Speed

        # Encoder Tuning
        if self.preset:
            options += ' --x264-tune {preset}'.format(preset=self.preset)
            if self.preset == 'animation' and Config.bFrames:
                # If we've set additional animation bframes in the Config, we'll
                # add those to the preset's built in bFrames now.
                bFrames = str(BFRAMES[Config.x264Speed] + int(Config.bFrames))
                options += ' --encopts bframes={bFrames}'.format(
                    bFrames=bFrames
                )

        # Encoder Quality
        options += ' -q {quality}'.format(quality=str(self.quality))

        # Encoder Framerate
        if self.fps:
            if self.fps == 24:
                fps = '23.976'
            elif self.fps == 30:
                fps = '29.97'
            elif self.fps == 25:
                fps = '25'
            else:
                # If we got an unknown value, we're just going to go with 24p
                self.fps = '23.976'
            options += ' -r {fps}'.format(fps=fps)

        options += ' --cfr'

        #
        # AUDIO OPTIONS
        #

        # We're no longer doing any audio encoding at the handbrake stage,
        # instead merging every audio track straight from the original file.

        options += ' -a none'

        #
        # PICTURE SETTINGS
        #

        options += ' -w {width} --loose-anamorphic'.format(
            width=str(RESOLUTION_WIDTH[self.resolution])
        )

        #
        # FILTERS
        #

        if self.tv:
            options += ' -d slower'

        #
        # SUBTITLES
        #

        for track in self.subtitleTracks:
            if track.fileType == 'vobsub':
                self.vobsub = True

        if self.vobsub:
            options += ' -N {lang} -s scan'.format(lang=Config.language)

        handBrake(self.path, options, self.destination)

        self.encoded = True

    def mergeMovie(self):
        """Uses mkvmerge to merge the movie and extracted/converted tracks"""

        # First we'll set the destination filename by grabbing the movie title,
        # and the source filename.
        title = self.subdir.split('__')[0]
        dFile = '{root}/converted/{title}/{fName}'.format(
            root=os.getcwd(),
            title=title,
            fName=self.fileName
        )

        totalAudio = 0
        totalSubs = 0

        vidCommand = []
        audCommand = []
        subCommand = []

        subDefault = False

        # We do audio and subtitle commands first to see if we need to set a
        # new default Audio and Subtitle track

        # We'll be copying all the audio- and only the audio- from the source
        # file.
        #audCommand += ' -D -S -B --no-chapters -M --no-global-tags'
        #audCommand += ' "{path}"'.format(path=self.path)
        audCommand.extend(['-D', '-S', '-B', '--no-chapters', '-M', '--no-global-tags', self.path])

        # Run through our subtitle tracks
        for track in self.subtitleTracks:
            if track.extracted:
                # Check for default status
                if track.default and not subDefault:
                    subCommand.extend(['--default-track', '-1:1'])
                    subDefault = True
                else:
                    subCommand.extend(['--default-track', '-1:0'])

                # Add language flag
                subCommand.extend(['--language', '-1:{lang}'.format(
                    lang=track.info['language']
                )])

                # Deal with forced only tracks
                if track.forcedOnly:
                    subCommand.extend(['--forced-track', '-1:1', track.convertedIdxForced])
                else:
                    if track.forced:
                        subCommand.extend(['--forced-track', '-1:1', track.convertedIdxForced])

                        # Add non-default and language flag for non-forced track

                        subCommand.extend(['--default-track', '-1:0', '--language', '-1:{lang}'.format(
                            lang=track.info['language']
                        )])

                    # Add non-forced track
                    subCommand.append(track.convertedIdx)

        # We're going to create a sub-movie that represents the converted
        # mkv file, to get information on it's subtitle tracks.

        convertedFName = self.fileName.replace('.mkv', '--converted.mkv')

        converted = Movie(self.root, self.subdir, convertedFName)

        if subDefault:
            for track in converted.subtitleTracks:
                vidCommand.extend(['--default-track', '{trackID}:0'.format(
                    trackID=track.trackID
                )])

        # We'll use -A to exclude any audio tracks that snuck in. There should
        # not be any.
        vidCommand.extend(['-A', self.destination])

        command = vidCommand + audCommand + subCommand

        mkvmerge(command, dFile)

        self.merged = True

class SubtitleTrack(object):
    """A single subtitle track.

    Args:
        movie : (<Movie>)
            The parent <Movie> object that this <SubtitleTrack> is a child of.

        trackID : (str)
            The trackID of the subtitle track this object is to represent.

        fileType : (str)
            The filetype of this subtitle track.

    """
    def __init__(self, movie, trackID, fileType, infoDict):
        self.movie = movie
        self.trackID = trackID
        self.fileType = fileType
        self.info = infoDict
        self.extracted = False
        self.extractedSup = None

        # When converted, there will be an Idx file and a Sub file
        self.converted = False
        self.convertedIdx = None
        self.convertedSub = None

        # forced means the track contains forced flags
        # forcedOnly means the track ONLY contains forced flags
        self.forced = False
        self.forcedOnly = False

        # If a track contains both forced and unforced tracks, there will be an
        # additional track saved out.
        self.convertedIdxForced = None
        self.convertedSubForced = None

        # Default track means this is the main subtitle track
        self.default = True if self.info['default_track'] == '1' else False

    def extractTrack(self):
        """Extracts the subtitle this object represents from the parent mkv"""
        command = "{trackID}:".format(trackID=str(self.trackID))

        # Derive the location the track should be saved to
        fileName = self.movie.fileName.replace('.mkv', '')
        # TODO: Should this be locked into .sup?
        fileName += "_Track{trackID}_sub.sup".format(trackID=self.trackID)

        self.extractedSup = os.path.join(
            self.movie.root,
            self.movie.subdir,
            fileName
        ).replace('\\', '/')

        print ""
        print "Extracting trackID {ID} of type {type} from {file}".format(
            ID=self.trackID,
            type=self.fileType,
            file=self.movie.path
        )
        print ""

        mkvExtract(self.movie.path, command, self.extractedSup)

        self.extracted = True

    def convertTrack(self):
        """Converts and resizes the subtitle track"""

        print ""
        print "Converting track {ID} at res: {res}p".format(
            ID=self.trackID,
            res=str(self.movie.resolution)
        )

        # BDSup2Sub doesn't take numerical values for resolution
        if self.movie.resolution == 480:
            res = 'ntsc'
        else:
            # Should be '1080p' or '720p'
            res = "{res}p".format(res=str(self.movie.resolution))

        # Our only option flag is really resolution
        options = "-r {res}".format(res=res)

        # Use the extractedSup as a baseline, replace the file extension
        # We check for and replace the period to make sure we grab the ext
        self.convertedIdx = self.extractedSup.replace('.sup', '.idx')
        self.convertedSub = self.extractedSup.replace('.sup', '.sub')

        print "Saving IDX file to {dest}".format(dest=self.convertedIdx)

        # Using deprecated os.popen (easier) to put shell output in list
        shellOut = bdSup2Sub(self.extractedSup, options, self.convertedIdx, popen=True)

        # We need to check the results for FORCED subtitles
        #
        # If the amount of Forced subtitles is less than the total subs
        # We'll just create a new .idx file in addition to the default one.
        #
        # If the amount of Forced subtitles is the same as the total subs,
        # the entire subtitle track is forced, so we remove the resultFiles
        # and create a new FORCED .idx

        totalCount = 0

        for line in shellOut:

            print line

            if line.startswith('#'):
                lineList = line.split(' ')
                # The last count entry from BD will set the total
                try:
                    totalCount = int(lineList[1])
                except ValueError:
                    pass

            # There should only be 1 entry with 'forced' in it, that entry
            # looks like:
            #
            # 'Detected 39 forced captions.'
            if 'forced' in line:
                forcedCaptions = int(line.split()[1])

                if forcedCaptions > 0:
                    self.forced = True
                if forcedCaptions == totalCount:
                    self.forcedOnly = True

        print ""
        print "Subtitle track has forced titles?", self.forced
        print "Subtitle track is ONLY forced titles?", self.forcedOnly
        print ""

        if self.forced:
            self.convertedIdxForced = self.convertedIdx.replace(
                '.idx',
                '_forced.idx'
            )
            self.convertedSubForced = self.convertedSub.replace(
                '.sub',
                '_forced.sub'
            )

        if self.forced and not self.forcedOnly:
            # If some forced subtitles exist (but not the entire subtitle
            # track is forced), we'll create a new _FORCED.idx in addition
            # to the one already exported.
            options += ' -D'

            bdSup2Sub(self.extractedSup, options, self.convertedIdxForced)

        elif self.forced and self.forcedOnly:
            # If the track is entirely forced subtitles, we'll rename the
            # extracted file to be the _forced file.

            # First we need to see if the file already exists, as renaming
            # will fail if it does.
            # If it exists, we'll assume that something went wrong, and
            # delete it.
            if os.path.isfile(self.convertedIdxForced):
                os.remove(self.convertedIdxForced)
            if os.path.isfile(self.convertedSubForced):
                os.remove(self.convertedSubForced)

            # Now for the renaming.
            os.rename(self.convertedIdx, self.convertedIdxForced)
            os.rename(self.convertedSub, self.convertedSubForced)

        self.converted = True

#===============================================================================
# FUNCTIONS
#===============================================================================

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
    c = '""' + Config.java + '" -jar "' + Config.sup2Sub + '" ' +  options +\
        ' -o "' + dest + '" "' + file + '""'

    print ''
    print "Sending to bdSup2Sub"
    print c
    print ''

    if popen:
        return os.popen(c).read().split('\n')
    else:
        os.system(c)

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
    c = '""' + Config.handBrake + '"' + ' -i ' + file + ' -o ' + dest + ' ' + \
        options + '"'

    print ''
    print "HandBrake Settings:"
    print c
    print ''

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
    # os.system('"mkvextract tracks ' + file + ' ' + command + dest + ' "')
    os.system('""{mkvExtract}" tracks "{file}" {command}{dest} "'.format(
        mkvExtract=Config.mkvExtract,
        file=file,
        command=command,
        dest=dest
    ))

def mkvInfo(movie):
    """Uses CLI to fetch names all audio, video and subtitle tracks from a mkv

    Args:
        movie : (<tools.Movie>)
            The file to get the info from

    Raises:
        N/A

    Returns:
        [[str], [str], [str]]
            A list contraining a list of video tracks, audio tracks and subtitle
            tracks.

    """

    file = movie.path

    # mkvMerge will return a listing of each track
    info = Popen(
        [Config.mkvMerge, '-I', file],
        shell=True,
        stdout=PIPE
    ).stdout

    # info is now a file object, each entry a line
    #
    # Example:
    #
    # File 'I:\Ripmaster\toConvert\JR__1080\JR_t01.mkv': container: Matroska []
    # Track ID 0: video (V_MPEG4/ISO/AVC) [...]
    # Track ID 1: audio (A_AC3) [...]
    # Track ID 2: audio (A_TRUEHD) [...]
    # Track ID 3: subtitles (S_HDMV/PGS) [...]

    AUDIO_TYPES = {
        'A_AAC': 'aac',
        'A_DTS': 'dts',
        'A_AC3': 'ac3',
        'A_EAC3': 'aec3',
        'A_TRUEHD': 'truehd',
        'A_MP3': 'mp3',
        'A_MS/ACM': 'acm',
        'A_PCM/INT/LIT': 'pcm'
        }

    SUBTITLE_TYPES = {
        'S_VOBSUB': 'vobsub',
        'S_HDMV/PGS': 'pgs'
        }

    subtitleTracks = []
    audioTracks = []
    videoTracks = [] # No plans to use video tracks for now

    for line in info.readlines():
        if line.startswith('Track ID'):
            trackID, trackType, trackDict = _trackInfo(line)

            if trackType == 'video':
                # Since video tracks aren't really used right now, we'll just
                # throw this stuff into a list.
                videoTracks.append([trackID, trackDict])
            elif trackType == 'audio':
                fileType = AUDIO_TYPES[trackDict['codec_id']]
                track = AudioTrack(movie, trackID, fileType, trackDict)
                audioTracks.append(track)
            elif trackType == 'subtitles':
                fileType = SUBTITLE_TYPES[trackDict['codec_id']]
                track = SubtitleTrack(movie, trackID, fileType, trackDict)
                subtitleTracks.append(track)

    return videoTracks, audioTracks, subtitleTracks

def mkvmerge(command, dest):
    """CLI command builder for merging tracks with mkvmerge

    Args:
        command : (str)
            The command to be executed. Source files must be included within
            this command.

        dest : (str)
            The destination file to be written to.

    Raises:
        N/A

    Returns:
        None

    """

    #c = Config.mkvMerge + " -o " + dest + command
    #c = '"{mkvMerge}" -o {dest}{command}'.format(
    #    mkvMerge=Config.mkvMerge,
    #    dest=dest,
    #    command=command
    #)
    commands = [Config.mkvMerge, '-o']
    commands.append(dest)
    commands.extend(command)

    print
    print commands
    print

    from subprocess import check_call
    try:
        check_call(commands)
    except:
        raw_input("oops")
