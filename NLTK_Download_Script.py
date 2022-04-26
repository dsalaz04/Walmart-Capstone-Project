"""NLTK Download Script.

NLTK requires some extra steps in order to make use of all its wonderful features. Line 23 in this script will download
whatever is in the parameter to the appropriate location on your machine. This may be a stupid way to do this, but it
works for me on my machine with my very low standard for cleanliness so this is what you get.

If you get a permission denied error, run this script from your terminal with 'sudo' in front. If you're on a Windows
machine, I can't help you nor do I have any interest in doing so.

"""

import nltk
import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Change this to whatever needs to be downloaded
nltk.downloader.download('wordnet')
