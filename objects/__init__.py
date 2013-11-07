#/usr/bin/python
# Ripmaster.objects
# Module containing objects used by Ripmaster
# By Sean Wallitsch, 2013/11/05

#===============================================================================
# IMPORTS
#===============================================================================

#===============================================================================
# VARIABLES
#===============================================================================

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
        1080p = 10
        720p = 10
        480p = 10

    Language = English

    Leading and trailing whitespaces are automatically removed, but all entries
    are case sensitive. Make sure there's still a space between the argument
    and the '=' sign.

    """

    java = ''
    sup2Sub = ''
    handBrake = ''
    language = ''

    quality = {}

    def __init__(self, iniFile):
        self.getSettings(iniFile)

    def getSettings(self, iniFile):

        with open(iniFile, "r") as f:
            lines = f.read().splitlines()
            for i in range(len(lines)):
                line = lines[i].lstrip()
                if line.startswith('Java'):
                    Config.java = _stripAndRemove(
                        line, 'Java ='
                    )
                elif line.startswith('BDSupToSub'):
                    Config.sup2Sub = _stripAndRemove(
                        line, 'BDSupToSub ='
                    )
                elif line.startswith('HandbrakeCLI'):
                    Config.handBrake = _stripAndRemove(
                        line, 'HandbrakeCLI ='
                    )
                elif line.startswith('x264 Speed'):
                    Config.x264Speed = _stripAndRemove(
                        line, 'x264 Speed ='
                    )
                elif line.startswith('Baseline Quality'):
                    Config.quality['1080pBQ'] = int(_stripAndRemove(
                        lines[i+1], '1080p =')
                    )
                    Config.quality['720pBQ'] = int(_stripAndRemove(
                        lines[i+2], '720p =')
                    )
                    Config.quality['480pBQ'] = int(_stripAndRemove(
                        lines[i+3], '480p =')
                    )
                elif line.startswith('High Quality'):
                    Config.quality['1080pHQ'] = int(_stripAndRemove(
                        lines[i+1], '1080p =')
                    )
                    Config.quality['720pHQ'] = int(_stripAndRemove(
                        lines[i+2], '720p =')
                    )
                    Config.quality['480pHQ'] = int(_stripAndRemove(
                        lines[i+3], '480p =')
                    )
                elif line.startswith('Ultra Quality'):
                    Config.quality['1080pUQ'] = int(_stripAndRemove(
                        lines[i+1], '1080p =')
                    )
                    Config.quality['720pUQ'] = int(_stripAndRemove(
                        lines[i+2], '720p =')
                    )
                    Config.quality['480pUQ'] = int(_stripAndRemove(
                        lines[i+3], '480p =')
                    )
                elif line.startswith('Language'):
                    Config.language = _stripAndRemove(line, 'Language =')

class audioTrack(object):
    """A single audio track.

    Args:
        file : (str)
            The source file that the track is being pulled from.

    """
    def __init__(self, file):
        self.sourceFile = file
        self.trackID = None
        self.fileType = None
        self.extracted = False
        self.extractedAudio = None

class subtitleTrack(object):
    """A single subtitle track.

    Args:
        movie : (<objects.Movie>)
            The movie object that contains the original subtitle.

    """
    def __init__(self, movie):
        self.sourceFile = movie.sourceFile
        self.trackID = None
        self.fileType = None
        self.extracted = False
        self.extractedSup = None

        self.targetRes = movie.targetRes

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


#===============================================================================
# FUNCTIONS
#===============================================================================