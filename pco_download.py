import requests
import datetime
import os
import sys
os.chdir(sys.path[0])

pco_top_level_url = "https://api.planningcenteronline.com"
pco_realm = None
#instead of entering the app_id and secret everytime it is run, you can put them in the file with the following name
#so that they are loaded in.
pco_creds_file = "pco_creds.txt"
pco_creds_path = os.path.join(sys.path[0], pco_creds_file)

pco_org_url = pco_top_level_url + "/services/v2"
# a section would be accessed through https://api.planningcenteronline.com/services/v2/songs/s#/arrangements/a#/sections
# where s# would be replaced by the song id and a# would be replaced by the arrangement id

#This is a bit of a precomputed hack to evenly space lines over subtitles with maximum 4 lines per subtitle.
#Note that this is limited to a section being broken into 5 subtitles with maxum 4 lines each (i.e. max 20 line section)
sline = [[0,0,0,0,0],[1,1,1,1,1],[2,2,2,2,2],[3,3,3,3,3],[4,4,4,4,4],
         [3,5,5,5,5],[3,6,6,6,6],[4,7,7,7,7],[4,8,8,8,8],
         [3,6,9,9,9],[4,7,10,10,10],[4,8,11,11,11],[4,8,12,12,12],
         [4,7,10,13,13],[4,7,11,14,14],[4,8,12,15,15],[4,8,12,16,16],
         [4,8,11,14,17],[4,8,12,15,18],[4,8,12,16,19],[4,8,12,16,20]]

#Class for handling SRT timecode math and printing.  Really only used within SrtRecord
class SrtTimecode:
  HH = 0
  MM = 0
  SS = 0
  mmm = 0

  def zero(self):
    self.HH = 0
    self.MM = 0
    self.SS = 0
    self.mmm = 0

  def inc_10s(self):
    carry = False
    self.SS += 10
    if self.SS >= 60:
      self.SS -= 60
      carry = True
    if carry:
      self.MM += 1
      carry = False
      if self.MM >= 60:
        self.MM -= 60
        carry = True
      if carry:
        self.HH += 1
        carry = False
        if self.HH > 99:
          self.HH = 0

  def print(self):
    return "{:02d}:{:02d}:{:02d},{:03d}".format(self.HH, self.MM, self.SS, self.mmm)

#Class for keeping track of SRT index and timecodes.
class SrtRecord:
  index = 1
  i = SrtTimecode()
  o = SrtTimecode()

  def __init__(self):
    self.reset()

  def next_10s(self):
    self.index += 1
    self.i.inc_10s()
    self.o.inc_10s()

  def print(self):
    return "{}\n{} --> {}\n".format(self.index, self.i.print(), self.o.print())

  def reset(self):
    self.index = 1
    self.i.zero()
    self.o.zero()
    self.o.inc_10s()

#TODO refactor this to have more reusable methods.  Think at how this might be used by importing at
#     an interactive python session.
def run():
  pco_app_id = ''
  pco_secret = ''

  #Try to load in credentials from file.
  try:
    with open(pco_creds_path,'r') as f:
      for l in f:
        if l.strip() == '':
          continue
        elif l.strip()[0] == '#':
          #use lines starting with # as comments
          continue
        
        if pco_app_id == '':
          pco_app_id = l.strip()
        elif pco_secret == '':
          pco_secret = l.strip()
          #Technically anything after the second non blank or comment line is not read.
          break
  except FileNotFoundError:
    print("pco_creds.txt not found.")

  if pco_app_id == "":
    pco_app_id = input("Please enter your Planning Center App_ID: ")

  if pco_secret == "":
    pco_secret = input("Please enter your Planning Center Secret: ")
  
  print("Attempting to connect to: " + pco_org_url)

  org = requests.get(pco_org_url,auth=(pco_app_id,pco_secret))
  if not org:
    print("Issue connecting to site: " + str(org))
    return
  org_json = org.json()['data']
  print("Connected to " + (org_json['attributes']['name'] or ''))
  org_ccli = (org.json())['data']['attributes']['ccli'] or ''
  print("ccli license = ", org_ccli)
  #next_page = pco_songs_url
  pco_service_types_url = org_json['links']['service_types'] or ''
  pco_songs_url = org_json['links']['songs'] or ''
  rec = SrtRecord()
  
  print("What would you like to download:")
  print("1. Arrangements for a specific service (TXT and SRT)")
  print("2. All arrangements as SRT (WARNING: Can take several minutes!)")
  print("3. All arrangements as TXT (WARNING: Can take several minutes!)")
  print("9. Quit")
  download_method = 0
  while download_method == 0:
    download_method = int(input("Enter your download choice: ")) or 0
    if download_method == 9:
      print("Quitting...\n")
      return
    if download_method < 1 or download_method > 3:
      print("ERROR: please enter a valid number\n")
      download_method = 0
  if download_method == 1: 
    print("Attempting to retrieve service types")

    st = requests.get(pco_service_types_url,auth=(pco_app_id,pco_secret))
    if not st:
      print("Issue getting service types: " + str(st))
      return
    sts = st.json()['data'] #list of all service_types
    st_link = ''
    if len(sts) == 0:
      print("No Service Types defined.  Cannot retrieve plans.")
      return
    elif len(sts) == 1:
      print("Using Service Type " + sts[0]['attributes']['name'] + ".")
      st_link = sts[0]['links']['self']
    else:
      st_list = []
      for s in sts:
        #If possible, we should make sure that a service type has plans, or indicate that a service doesn't have plans.
        print(str(len(st_list)) + ". " + s['attributes']['name'])
        st_list.append(s['links']['self'])
      print(str(len(st_list)+1) + ". Quit")
      choice = 0
      while choice == 0:
        choice = int(input("Enter the number of the Service Type to use: ")) or 0
        if choice < 1 or choice > (len(st_list)+1):
          print("ERROR: please enter a valid number\n")
          choice = 0
        if choice == (len(st_list)+1):
          print("Quitting...\n")
          return

      st_link = st_list[choice-1]

    if st_link == '':
      print('ERROR: Service Type selection failed!')
      return
 
    service_type = requests.get(st_link,auth=(pco_app_id,pco_secret))
    if not service_type:
      print("Issue getting service type: " + str(service_type))
      return
    service_type_json = service_type.json()['data']
    pco_service_plans_url = service_type_json['links']['plans']
    #plans returns all plans since inception (e.g. back to April 27, 2014)
    #the query for plans can be done on created and updated dates.
    #Updated was chosen as the plan for this week should have been updated in the past week.
    #Use 2 weeks though. This could be exposed as a question, or a date range input from user.
    query = str(datetime.date.today() - datetime.timedelta(weeks=2))
    url = pco_service_plans_url + "?where[updated_at][gt]=" + query
    plans = requests.get(url,auth=(pco_app_id,pco_secret))
    if not plans:
      print("Issue getting plans: " + str(plans))
      return
    plans_json = plans.json()['data']
    plan_list = []
    if len(plans_json) == 0:
      print("The selected service type has no plans.\n")
      return
    for plan in plans_json:
      plan_list.append(plan['links']['self'])
      print(str(len(plan_list)) + ". " + plan['attributes']['dates'])

    print(str(len(plan_list)+1) + ". Quit")
    choice = 0
    while choice == 0:
      choice = int(input("Enter the number of the plan to download: ")) or 0
      if choice < 1 or choice > (len(plan_list)+1):
        print("ERROR: please enter a valid number\n")
        choice = 0
      if choice == (len(plan_list)+1):
        print("Quitting...\n")
        return
  
    plan = requests.get(plan_list[choice-1],auth=(pco_app_id,pco_secret))
    if not plan:
      print("Issue getting plan: " + str(plan))
      return
    plan_json = plan.json()
    items = requests.get(plan_json['data']['links']['items'],auth=(pco_app_id,pco_secret))
    if not items:
      print("Issue getting items: " + str(items))
      return
    items_json = items.json()

    #now we need to go through the items and pull out the song and arragement ids
    #TODO perhaps prompt the user whether they want the arrangement?
    #     may also be helpful to print the last modified date.
    #     it may also be helpful to get all arrangements for a song as we've seen
    #     arrangements that are made that don't do as well with SRT creation
    #     (e.g. if it was reformatted for Music Stand on a TV?)
    arrangements = []
    for item in items_json['data']:
      if item['relationships']['arrangement']['data'] == None:
        continue
      arrangements.append((item['relationships']['song']['data']['id'],
          item['relationships']['arrangement']['data']['id']))
  
    if arrangements == []:
      print("Selected date has no arrangements associated with it.\n")
      return
  elif download_method == 2 or download_method == 3:
    #Load up arrangements list with all arrangements
    next_page = pco_songs_url
    arrangements = []
    while next_page:
      songs = requests.get(next_page,auth=(pco_app_id,pco_secret))
      if not songs:
        print("Issue getting songs: " + str(songs))
        return
      songs_json = songs.json()
      next_page = songs_json['links']['next'] if 'next' in songs_json['links'] else False
      for song in songs_json['data']:
        arranges = requests.get(song['links']['self']+"/arrangements",auth=(pco_app_id,pco_secret))
        if not arranges:
          print("Issue getting arrangements: " + str(arranges))
          continue
        arranges_json = arranges.json()

        for arrange in arranges_json['data']:
          arrangements.append((song['id'],arrange['id']))
    if arrangements == []:
      print("No arrangements to download.\n")
      return

  #TODO here is where we have a common block whether we want to get all songs, a specific song
  #     or songs based on a plan.
  for pa in arrangements:
    song = requests.get(pco_songs_url + '/' + pa[0],auth=(pco_app_id,pco_secret))
    if not song:
      print("Issue getting song " + pa[0] + ": " + str(song))
      continue
    song_json = song.json()['data']
    song_id = song_json['id'] or ''
    song_title = song_json['attributes']['title'] or ''
    song_author = song_json['attributes']['author'] or ''
    song_copyright = song_json['attributes']['copyright'] or ''
    song_ccli = song_json['attributes']['ccli_number'] or ''

#    print(song_id)
#    print(song_title, "by", song_author)
#    print("\u00A9", song_copyright)
#    print("CCLI #", song_ccli, "-- CCLI License", org_ccli)

    arrange = requests.get(song_json['links']['self']+"/arrangements/"+pa[1],auth=(pco_app_id,pco_secret))
    if not arrange:
      print("Issue getting arrangement " + pa[1] + ": " + str(arrange))
      continue
    arrange_json = arrange.json()['data']
    arrange_name = arrange_json['attributes']['name'] or ''
    arrange_seq = arrange_json['attributes']['sequence_short'] or ''
    arrange_lyrics = arrange_json['attributes']['lyrics'] or ''

    sections = requests.get(arrange_json['links']['self']+"/sections",auth=(pco_app_id,pco_secret))
    if not sections:
      print("Issue getting sections for arrangement " + pa[1] + ": " + str(sections))
      continue
    sections_json = sections.json()
    secs = {}

    for li in sections_json['data']['attributes']['sections']:
      secs[''.join(li['label'].lower().split())] = li['lyrics']

    if download_method == 1 or download_method == 3:
      with open((song_title + " by " + arrange_name + ".txt").strip().replace("/","_").replace(":","_").replace('"',"_").replace("?","_"),"w") as f:
        f.write(song_title + " by " + song_author + "\n")
        f.write("\u00A9" + song_copyright + "\n")
        f.write("CCLI # " + str(song_ccli) + " -- CCLI License " + str(org_ccli) + "\n")
        f.write(' '.join(arrange_seq) + "\n")
        f.write("\n")
        f.write(arrange_lyrics)
        f.write("\n\n")

    if download_method == 1 or download_method == 2:
      #TODO Due to inconsistencies between sequence and section specifications, as well
      #     as performance time changes, give the user a chance to modify the arrangement
      #     sequence based on section labels.
      with open((song_title + " by " + arrange_name + ".srt").strip().replace("/","_").replace(":","_").replace('"',"_").replace("?","_"),"w") as f:
        f.write(rec.print())
        rec.next_10s()
        f.write("\n")
        f.write(rec.print())
        rec.next_10s()
        f.write(song_title + " by " + song_author + "\n")
        f.write("\u00A9" + song_copyright + "\n")
        f.write("CCLI # " + str(song_ccli) + " -- CCLI License " + str(org_ccli) + "\n")
        f.write("\n")
        for si in arrange_json['attributes']['sequence']:
          #TODO There is an issue here were the arrangement seqence is not forced to be
          #     consistent with the arrangement section labels.  In fact there are instances
          #     where an arrangement is changed so it suits the needs in Music Stand, but
          #     the sequence isn't updated to reflect this. 
          #TODO Create an interactive way for a user to see the defined sections and then\
          #     input a sequence based on section labels.  e.g. print out the sequence and
          #     then let the user customize and/or interpret the sequence based on section labels
          #Planning Center is case insensitive on labels.  There have been cases where the lyrics labels
          #and sequence labels have different capitalizations (e.g. Prechorus vs PreChorus) and spacing
          #(e.g. Planning Center turns Pre-Chorus into Pre Chorus)
          si = ''.join(si.lower().split())
          #The other issue to work around is that a sequence may specify Chorus, where the section may end up as Chorus1
          if si in secs:
            pass
          elif si + "1" in secs:
            si = si + "1"
          f.write(rec.print())
          rec.next_10s()
          if si in secs:
            #need to handle sections longer than 4 lines.
            #this is pretty basic: 1-4 is 1 slide
            #then the split is: 3,2; 3,3; 4,3; 4,4;
            #3,3,3; 4,3,3; 4,4,3; 4,4,4
            #4,3,3,3; 4,3,4,3; 4,4,4,3; 4,4,4,4
            #it is up to the video editor to fix this for the specific song
            lines = secs[si].split('\r')
            l = len(lines)
            if l > 20:
              #if there is more than 20 lines, there is probably something wrong
              #output the raw lines and let the video editor take care of it
              f.writelines(lines)
              print(song_title + " by " + arrange_name + " has large section.") 
              continue
            f.writelines(lines[:sline[l][0]])
            if l > 4:
              f.write("\n")
              f.write(rec.print())
              rec.next_10s()
              f.writelines(lines[sline[l][0]:sline[l][1]])
            if l > 8:
              f.write("\n")
              f.write(rec.print())
              rec.next_10s()
              f.writelines(lines[sline[l][1]:sline[l][2]])
            if l > 12:
              f.write("\n")
              f.write(rec.print())
              rec.next_10s()
              f.writelines(lines[sline[l][2]:sline[l][3]])
            if l > 16:
              f.write("\n")
              f.write(rec.print())
              rec.next_10s()
              f.writelines(lines[sline[l][3]:sline[l][4]])
            f.write("\n")
          f.write("\n")
        f.write(rec.print())
        f.write("\n\n")
        rec.reset()


if __name__ == "__main__":
  run()

