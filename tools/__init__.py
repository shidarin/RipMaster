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

Config
    The Config object reads the Ripmaster.ini file for all the user set
    configuration options.

AudioTrack
    Represents a single audio track within a <Movie>. Each AudioTrack in the mkv
    gets an AudioTrack object, not just ones Handbrake can't handle.

SubtitleTrack
    Represents a single subtitle track within a <Movie>. Each subtitle track in
    the mkv gets a SubtitleTrack object, not just the ones Handbrake can't
    handle. Since one subtitle track can contain both forced and non-forced
    subtitles, it's possible that a single subtitle track gets split into
    two subtitle tracks- one forced and the other containing every subtitle
    (both forced and not forced).

Movie
    Represents a single mkv file, contains <AudioTrack>s and <SubtitleTracks>s.
    Calls all the extraction and conversion methods of it's children.

Functions
---------

handbrake()
    CLI command builder for converting video and audio with Handbrake. For all
    intents and purposes, this is the Handbrake application.

mkvExtract()
    CLI command builder for extracting tracks with mkvextract. For all intents
    and purposes, this is the mkvextract application.

mkvInfo()
    Uses mkvmerge to fetch names, filetypes and trackIDs for all audio, video
    and subtitle tracks from a given mkv.

bdSup2Sub()
    CLI command builder for converting subtitle tracks with BDSup2Sub. For all
    intents and purposes, this is the BDSup2Sub application.

"""

#===============================================================================
# IMPORTS
#===============================================================================

# Standard Imports
import os

#===============================================================================
# GLOBALS
#===============================================================================

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
EXTRACTABLE_AUDIO = ['truehd']
EXTRACTABLE_SUBTITLE = ['pgs']
SAMPLE_CONFIG = """Java = C://Program Files (x86)/Java/jre7/bin/java
BDSupToSub = C://Program Files (x86)/MKVToolNix/BDSup2Sub.jar
HandbrakeCLI = C://Program Files/Handbrake/HandBrakeCLI.exe

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
    1080p = 16
    720p = 16
    480p = 16

Language = English
Audio Fallback = ffac3"""

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

#===============================================================================
# CLASSES
#===============================================================================

class Config(object):
    """ Class containing the basic encoding environment as described by the .ini

    Args:
        iniFile : (str)
            Ripmaster's configuration file

    Sample config file:

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
        1080p = 16
        720p = 16
        480p = 16

    Language = English
    Audio Fallback = ffac3

    Leading and trailing whitespaces are automatically removed, but all entries
    are case sensitive. Make sure there's still a space between the argument
    and the '=' sign.

    """

    java = ''
    sup2Sub = ''
    handBrake = ''
    x264Speed = 'slow'
    language = 'English'
    audioFallback = 'ffac3'

    quality = {'uq': {}, 'hq': {}, 'bq': {}}

    def __init__(self, iniFile):
        self.configExists = False
        self.checkConfig(iniFile)
        if self.configExists:
            self.getSettings(iniFile)

    def checkConfig(self, iniFile):
        """Checks that the iniFile provided actually exists. Creates if not."""
        if os.path.exists(iniFile):
            self.configExists = True
            return
        else:
            with open(iniFile, "w") as f:
                f.write(SAMPLE_CONFIG)
            print ""
            print "PROCESS WILL FAIL"
            print "You were missing the .ini file. I had to create one for you."
            print "You'll find it in Ripmaster's folder, called Ripmaster.ini"
            print "You need to specify the path for" + \
                  " Java, BDSup2Sub and Handbrake.\n"
            self.configExists = False

    def getSettings(self, iniFile):
        """Opens the ini file, splits the lines into a list, and grabs input"""
        print "Reading config from:", iniFile
        print ""

        with open(iniFile, "r") as f:
            # splitlines() will give us a list of each line.
            lines = f.read().splitlines()

            for i in range(len(lines)):
                # Remove leading whitespace before comparing with startswith()
                line = lines[i].lstrip()
                if line.startswith('Java'):
                    Config.java = _stripAndRemove(
                        line, 'Java ='
                    ).replace('\\', '/')
                elif line.startswith('BDSupToSub'):
                    Config.sup2Sub = _stripAndRemove(
                        line, 'BDSupToSub ='
                    ).replace('\\', '/')
                elif line.startswith('HandbrakeCLI'):
                    Config.handBrake = _stripAndRemove(
                        line, 'HandbrakeCLI ='
                    ).replace('\\', '/')
                elif line.startswith('x264 Speed'):
                    Config.x264Speed = _stripAndRemove(
                        line, 'x264 Speed ='
                    )
                elif line.startswith('Audio Fallback ='):
                    Config.audioFallback = _stripAndRemove(
                        line, 'Audio Fallback ='
                    )
                elif line.startswith('Baseline Quality'):
                    Config.quality['bq']['1080'] = int(_stripAndRemove(
                        lines[i+1], '1080p =')
                    )
                    Config.quality['bq']['720'] = int(_stripAndRemove(
                        lines[i+2], '720p =')
                    )
                    Config.quality['bq']['480'] = int(_stripAndRemove(
                        lines[i+3], '480p =')
                    )
                elif line.startswith('High Quality'):
                    Config.quality['hq']['1080'] = int(_stripAndRemove(
                        lines[i+1], '1080p =')
                    )
                    Config.quality['hq']['720'] = int(_stripAndRemove(
                        lines[i+2], '720p =')
                    )
                    Config.quality['hq']['480'] = int(_stripAndRemove(
                        lines[i+3], '480p =')
                    )
                elif line.startswith('Ultra Quality'):
                    Config.quality['uq']['1080'] = int(_stripAndRemove(
                        lines[i+1], '1080p =')
                    )
                    Config.quality['uq']['720'] = int(_stripAndRemove(
                        lines[i+2], '720p =')
                    )
                    Config.quality['uq']['480'] = int(_stripAndRemove(
                        lines[i+3], '480p =')
                    )
                elif line.startswith('Language'):
                    Config.language = _stripAndRemove(line, 'Language =')

    def debug(self):
        """Prints the current configuration"""
        print "Java at:", Config.java
        print "BDSup2Sub at:", Config.sup2Sub
        print "Handbrake at:", Config.handBrake
        print "x624speed set to:", Config.x264Speed
        print "Default language:", Config.language
        print "Audio Codec Fallback:", Config.audioFallback
        print "Quality dictionary:"
        for entry in Config.quality:
            print entry + ":", Config.quality[entry]

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
    def __init__(self, movie, trackID, fileType):
        self.movie = movie
        self.trackID = trackID
        self.fileType = fileType
        self.extracted = False
        self.extractedAudio = None

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
    def __init__(self, movie, trackID, fileType):
        self.movie = movie
        self.trackID = trackID
        self.fileType = fileType
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
            os.rename(self.convertedIdx, self.convertedIdxForced)
            os.rename(self.convertedSub, self.convertedSubForced)

        self.converted = True

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

        # TODO: We should derive our default res based on the video track
        self.resolution = 1080
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
            if size in instructionSet:
                self.resolution = size
        for level in QUALITY:
            if level in instructionSet:
                self.quality = Config.quality[level][str(self.resolution)]
        for preset in H264_PRESETS:
            if preset in instructionSet:
                self.preset = preset
        for fps in FPS_PRESETS:
            if fps in instructionSet:
                # We need to remove the 'p' off the back of the '30p'
                self.fps = int(fps.replace('p', ''))
        if 'tv' in instructionSet:
            self.tv = True
        if not self.quality:
            self.quality = Config.quality['bq'][str(self.resolution)]

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
            if track.fileType in EXTRACTABLE_AUDIO:
                if not track.extracted:
                    track.extractTrack()

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

        passthroughAudio = []

        for track in self.audioTracks:
            if track.fileType not in EXTRACTABLE_AUDIO:
                passthroughAudio.append(track)

        if passthroughAudio:
            options += ' -a '

        for track in passthroughAudio:
            options += str(track.trackID)
            if track != passthroughAudio[-1]:
                options += ','
            else:
                options += ' -E '
        for track in passthroughAudio:
            options += 'copy'
            if track != passthroughAudio[-1]:
                options += ','

        if passthroughAudio:
            options += ' --audio-fallback {codec}'.format(
                codec=Config.audioFallback
            )

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
    os.system('"mkvextract tracks ' + file + ' ' + command + dest + ' "')

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
    # TODO: Remove deprecated popen
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
        '(A_PCM/INT/LIT)\r': 'pcm'
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

    subtitleTracks = []
    audioTracks = []
    videoTracks = [] # No plans to use video tracks for now

    for line in trackList:
         # Splitting on ':' gives us the ID on one side, the type on the other
        lineList = line.split(':')

        if 'subtitles' in lineList[1]:
            trackID = int(lineList[0].replace('Track ID ', ''))
            fileType = SUBTITLE_TYPES[lineList[1].replace(' subtitles ', '')]
            track = SubtitleTrack(movie, trackID, fileType)
            subtitleTracks.append(track)

        elif 'audio' in lineList[1]:
            trackID = int(lineList[0].replace('Track ID ', ''))
            fileType = AUDIO_TYPES[lineList[1].replace(' audio ', '')]
            track = AudioTrack(movie, trackID, fileType)
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