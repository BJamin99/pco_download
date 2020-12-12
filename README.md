# pco_download
Allows one to download arrangements in Planning Center to text files.  Also will create an SRT for video subtitles.

To run this in Windows 10, go to the Microsoft Store and download the latest version of Python3 (3.9 as of this writing).

In addition to the standard Python install, you'll also need the "requests" module.  To do this, open a command prompt (cmd.exe) and execute the following:

python3 -m pip install --upgrade pip
python3 -m pip install requests

In addition to Python3, you will also need to have a developer "secret" with Planning Center (a.k.a. Personal Access Token).  To do this, login to Planning Center at https://api.planningcenteronline.com/oauth/applications and setup a New Personal Access Token.  The Description can be whatever you like (e.g. Export Lyrics).  You should then have an Application ID and Secret.  You will be asked for these when running the script.  Alternatively you can store them in the pco_creds.txt file.  If they are in there you will not have to enter them each time you run the script. (Note: if this goes well, we may look into registering the application and have an OAuth token, or perhaps we should have a read-only account dedicated to this sort of thing).

Then you can run python3 pco_download.py (note, this does not need to be done from the command line; double clicking the plan_songs_download.py file will accomplish the same thing after you've installed Python3 and the requests module).

If you have not stored your Application ID and Secret in pco_creds.txt, you'll be asked to enter your Application ID and Secret.  (note: if you store your Application ID and Secret in the pco_creds.txt, do not share that file).

If the script can successfully connect to Planning Center, you will be asked what you would like to do.  Normally you'll want to download arrangements for a specific service.  There are also options for downloading all arrangements as eiter TXT or SRT.  These are there to create a back-catalog of all arrangements, but note that this takes time.

Selecting 1, the script then checks for different service types, if applicable.  Currently Redeemer only has one service type (Sunday Worship), so this type is automatically selected.  If there were more than one, you would be asked what service type you are looking to download (this may be more relevant in the future if more than one service type is defined in Planning Center).

The script then looks for service plans that have been updated in the past two weeks and presents a list of dates to choose from.  This list probably contains a couple services from the past, this weeks service, and a few services in the future.  Select the date you'd like to download the arrangements from.  The script will then export that information. and you should have two files for each song in the plan; a text file and an SRT.

There are a few things to note about what gets downloaded:

Anything that is entered as a song with an arrangement is downloaded.  This includes scripture that was entered as a song, which works well when needing to overlay the scripture on the video.

The TXT file has the arrangement sequence followed by the lyrics as would be seen in the lyrics PDF in Planning Center.  This is a good thing to have as the way SRTs are currently generated there could be some things missing or out of order.  Having the TXT gives a good thing to look at and, if needed copy and paste text from.

The SRT file has the lyrics printed in a SRT compatible format with each subtitle lasting 10 seconds.  Unlike the TXT file that typically only has the text for each unique section once, the SRT prints out all lyrics in the sequence defined by the sequence in Planning Center.  As Planning Center does not enforce strict 

Reference:
https://developer.planning.center/docs
