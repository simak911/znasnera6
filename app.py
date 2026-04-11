from flask import Flask, render_template, request, send_file, g
from waitress import serve
import time, os, csv, math

def gettimestamp():
    timestamp = 1745618400
    return round(time.time() - timestamp)

def tostring(list):
    s = ''
    for elem in list:
        s+=str(elem)+','
    s=s[:-1]
    s+='\n'
    return s

def format(text):
    text = text.replace(" ", "").replace("\n","").lower()
    return text

def numberize(text, default):
    try:
        return int(text)
    except:
        return default

def lines_from_csv(filepath):
    f = open(filepath, encoding = 'utf-8')
    r = csv.reader(f, delimiter=';')
    lines = []
    for line in r:
        lines.append(line)
    lines = lines[1:]
    return lines

def load_hint_data(speed):
    filepath = './data/hints.csv'
    lines = lines_from_csv(filepath)
    hints = []
    for line in lines:
        if len(line) > 3:
            levelnumber = numberize(line[0], -1)
            code = format(line[1])
            startcode = format(line[2])
            hinttimes = []
            for i in range(3,len(line)):
                hinttimes.append(round(60 * numberize(line[i], 0) / speed))
            hint = Hint(levelnumber, code, startcode, hinttimes)
            hints.append(hint)
    return hints

def load_uids():
    filepath = './data/teams.csv'
    lines = lines_from_csv(filepath)
    uids = []
    for line in lines:
        if len(line)>0:
            uids.append(format(line[0]))
    return uids

def load_team_data(uid):
    uid = format(uid)
    filepath = './data/teams.csv'
    lines = lines_from_csv(filepath)
    for line in lines:
        if len(line)>8:
            if format(line[0]) == uid:
                name = line[1]
                startlevel = numberize(line[2], -1)
                level = numberize(line[3], -1)
                is_started = (format(line[4]) == '1')
                is_ended = (format(line[5]) == '1')
                start = numberize(line(6),-1)
                end = numberize(line[7],-1)
                levelstats = []
                for i in range(8, len(line)):
                    levelstat = numberize(line[i], -1)
                    levelstats.append(levelstat)
                teaminfo = TeamInfo(uid, name, startlevel, level, is_started, is_ended, start, end, levelstats)
                return teaminfo
    return None

def update_team_data(teaminfo):
    uid = teaminfo.uid
    name = teaminfo.name
    startlevel = str(teaminfo.startlevel)
    level = str(teaminfo.level)
    is_started = '0'
    if teaminfo.is_started:
        is_started = '1'
    is_ended = '0'
    if teaminfo.is_ended:
        is_ended = '1'
    start = str(teaminfo.start)
    end = str(teaminfo.end)
    levelstats = [str(levelstat) for levelstat in teaminfo.levelstats]
    newline = [uid, name, startlevel, level, is_started, is_ended, start, end]
    for levelstat in levelstats:
        newline.append(levelstat)
    filepath = './data/teams.csv'
    lines = lines_from_csv(filepath)
    newlines = ["TATO RADKA JE K NICEMU"]
    for line in lines:
        if len(line) == 0:
            newlines.append(line)
        elif line[0] == uid:
            newlines.append(newline)
        else:
            newlines.append(line)
    g = open(filepath, 'w', encoding='utf-8')
    writer = csv.writer(g, delimiter=';')
    writer.writerows(newlines)

class TeamInfo():
    def __init__(self, uid, name, startlevel, level, is_started, is_ended, start, end, levelstats):
        self.uid = uid
        self.name = name
        self.startlevel = startlevel
        self.level = level
        self.is_started = is_started
        self.is_ended = is_ended
        self.start = start
        self.end = end
        self.levelstats = levelstats

class Hint():
    def __init__(self, levelnumber, code, startcode, hinttimes):
        self.levelnumber = levelnumber
        self.code = code
        self.startcode = startcode
        self.hinttimes = hinttimes
    
    def get_hintinfo(self, seconds):
        hintcount = len(self.hinttimes)
        for i in range(hintcount):
            if seconds >= self.hinttimes[i]:
                seconds -= self.hinttimes[i]
            else:
                timetowait = self.hinttimes[i] - seconds
                return i, timetowait
        return hintcount, 0

class GlobalVariables():
    def __init__(self):
        self.hints = load_hint_data(1)
        self.levelcount = len(self.hints)
        self.uids = load_uids()
        self.codes = [hint.code for hint in self.hints]
        self.startcodes = [hint.startcode for hint in self.hints]
        self.levelcount = len(self.codes)
        self.admcode = 'a6d9m'  

gv = GlobalVariables()

def gettn(uid):
    teaminfo = load_team_data(uid)
    if teaminfo == None:
        return ''
    else:
        return teaminfo.name

app = Flask(__name__)
@app.route('/')
@app.route('/index')
def get_login_page():
    return render_template('index.html', msg='', msgcolor='neut')

@app.route('/main')
def get_main_page():
    uid = format(request.args.get('tname'))
    if uid == gv.admcode:
        return render_template('admin.html', msg='Logged into admin menu.', msgcolor='pos')
    elif uid in gv.uids:
        return render_template('main.html', msg='Successful login.', msgcolor='pos', tn=gettn(uid))   
    else:
        return render_template('index.html', msg='Wrong team ID.', msgcolor='neg')


@app.route('/entered')
def entered():
    code = format(request.args.get('code'))
    uid = format(request.args.get('tname'))
    teaminfo = load_team_data(uid)
    if teaminfo is not None:
        is_correct_code = False
        is_correct_startcode = False
        for hint in gv.hints:
            if code == hint.code:
                is_correct_code = True
                act_hint = hint
                break
            elif code == hint.startcode:
                is_correct_startcode = True
                act_hint = hint
                break
        if is_correct_code:
            if not teaminfo.is_started:
                return render_template('main.html', msg='Game not started yet.', msgcolor='neg', tn=teaminfo.name) 
            else:
                level = act_hint.levelnumber
                teaminfo.level = level
                if level == teaminfo.startlevel and not teaminfo.is_ended:
                    teaminfo.is_ended = True
                    teaminfo.end = gettimestamp()
                    update_team_data(teaminfo)
                    return render_template('main.html', msg='Finish! Go to Jistota!', msgcolor='pos', tn=teaminfo.name) 
                else:
                    teaminfo.levelstats[level] = gettimestamp()
                    update_team_data(teaminfo)                               
                    return render_template('main.html', msg='Success!', msgcolor='pos', tn=teaminfo.name) 
        elif is_correct_startcode:
            if not teaminfo.is_started:
                teaminfo.is_started = True
                level = act_hint.levelnumber
                teaminfo.level = level
                teaminfo.startlevel = level
                teaminfo.start = gettimestamp()
                teaminfo.levelstats[level] = gettimestamp()
                update_team_data(teaminfo)
                return render_template('main.html', msg='Game started!', msgcolor='pos', tn=gettn(uid)) 
            else:
                return render_template('main.html', msg='Code not found.', msgcolor='neg', tn=gettn(uid))      
        else:
            return render_template("main.html", msg="Code not found.", msgcolor='neg', tn=gettn(uid))          
    else:
        return render_template("main.html", msg="Team not found.", msgcolor='neg', tn="")

@app.route('/get-img')
def get_image():
    try:    
        uid = format(request.args.get('tname'))
        level = load_team_data(uid).level
        if level > -1:
            return send_file(f'./imgs/s{level}.jpg', mimetype='image/jpeg')
        else:
            return send_file('./imgs/loadfail.jpg', mimetype='image/jpeg')
    except:
        return send_file('./imgs/loadfail.jpg', mimetype='image/jpeg')

@app.route('/get-hint')
def get_hint():
    try:    
        uid = format(request.args.get('tname'))
        teaminfo = load_team_data(uid)
        level = teaminfo.level
        timeonlevel = teaminfo.levelstats[level]
        timenow = gettimestamp()
        timewait = timenow - timeonlevel
        act_hint = None
        for hint in gv.hints:
            if hint.levelnumber == level:
                act_hint = hint
                break
        hintnumber, waittime = act_hint.get_hintinfo(timewait)
        if level > -1:
            if hintnumber > 0:
                return send_file(f'./imgs/h{level}_{hintnumber}.jpg', mimetype='image/jpeg')
            else:
                return send_file('./imgs/wait.jpg', mimetype='image/jpeg')
        else:
            return send_file('./imgs/loadfail.jpg', mimetype='image/jpeg')
    except:
        return send_file('./imgs/loadfail.jpg', mimetype='image/jpeg')

@app.route('/get-hinttimes')
def get_hinttimes():  
    try: 
        uid = format(request.args.get('tname'))
        teaminfo = load_team_data(uid)
        level = teaminfo.level
        timeonlevel = teaminfo.levelstats[level]
        timenow = gettimestamp()
        timewait = timenow - timeonlevel
        act_hint = None
        for hint in gv.hints:
            if hint.levelnumber == level:
                act_hint = hint
                break
        hintnumber, timetowait = act_hint.get_hintinfo()
        return {'status': 'valid', 'htime': timetowait, 'hnumber': hintnumber}
    except:
        return {'status': 'invalid'}

@app.route('/get-stats')
def get_stats():
    adminid = format(request.args.get('tname'))
    if adminid == gv.admcode:
        return send_file('./data/hints.csv', mimetype='text/csv', as_attachment=True, download_name='stats.csv')          
    else:
        return render_template('index.html', msg='You have no power here.', msgcolor = 'neg')

@app.route('/reset-game')
def reset_game():
    uid = format(request.args.get('tname'))
    if uid == gv.admcode:
        resetuid = format(request.args.get('rname'))
        teaminfo = load_team_data(resetuid)
        if teaminfo is not None:
            for stat in teaminfo.levelstats:
                stat = -1
            teaminfo.startlevel = -1
            teaminfo.level = -1
            teaminfo.is_started = False
            teaminfo.is_ended = False
            update_team_data(teaminfo)
            return render_template('admin.html', msg=f'Team {teaminfo.name} reseted.', msgcolor='pos')
        else:
            return render_template('admin.html', msg=f'Team id not found.', msgcolor='neg')
    else:
        return render_template('index.html', msg='You have no power here.', msgcolor = 'neg')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    serve(app, host="0.0.0.0", port=port)