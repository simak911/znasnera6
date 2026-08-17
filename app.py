from flask import Flask, render_template, request, send_file, g
from waitress import serve
import time, os, csv
import io
from google.cloud import storage

ENV = os.getenv("ENV", "prod")
is_prod = (ENV == "prod")

bucket_name = "znasnera6_bucket"

def get_reader(filename):
    if is_prod:
        return get_csv_from_bucket(filename)
    else:
        f = open(f'./data/{filename}', 'r', encoding='utf-8', newline='')
        reader = csv.reader(f, delimiter=';')
        return reader

def write_rows(filename, rows):
    if is_prod:
        put_csv_to_bucket(filename, rows)
    else:
        g = open(f'./data/{filename}', 'w', encoding='utf-8', newline='')
        writer = csv.writer(g, delimiter=';')
        writer.writerows(rows)


def get_csv_from_bucket(filename):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(filename)
    data = blob.download_as_text()
    input_data = io.StringIO(data)
    reader = csv.reader(input_data, delimiter=';')
    return reader

def put_csv_to_bucket(filename, rows):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(filename)

    output = io.StringIO()
    writer = csv.writer(output, delimiter = ';')
    writer.writerows(rows)

    blob.upload_from_string(output.getvalue(), content_type="text/csv")

def tabletostring(headerline, lines):
    content = ''
    th = ''
    for elem in headerline:
        th += f'<th>{elem}</th>'
    content += f'<tr>{th}</tr>'    
    for row in lines:
        tr = ''
        for elem in row:
            tr += f'<td>{elem}</td>'
        content += f'<tr>{tr}</tr>'
    return f'<table id="restable">{content}</table>'

def gettimestamp():
    return round(time.time())

def gethms(ts):
    if ts < 0:
        return '-'
    else:
        TIMEZONE = 2
        s = ts % 60
        m = (ts // 60) % 60
        h = (TIMEZONE + (ts // 3600)) % 24
        return f'{h}:{m}:{s}'

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
    r = get_reader(filepath)
    lines = []
    for line in r:
        lines.append(line)
    lines = lines[1:]
    return lines

def load_hint_data(speed):
    filepath = 'hints.csv'
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
    filepath = 'teams.csv'
    lines = lines_from_csv(filepath)
    uids = []
    for line in lines:
        if len(line)>0:
            uids.append(format(line[0]))
    return uids

def load_team_data(uid):
    uid = format(uid)
    filepath = 'teams.csv'
    lines = lines_from_csv(filepath)
    for line in lines:
        if len(line)>8:
            if format(line[0]) == uid:
                name = line[1]
                startlevel = numberize(line[2], -1)
                level = numberize(line[3], -1)
                is_started = (format(line[4]) == '1')
                is_ended = (format(line[5]) == '1')
                start = numberize(line[6],-1)
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
    filepath = 'teams.csv'
    lines = lines_from_csv(filepath)
    newlines = [["TATO RADKA JE K NICEMU"]]
    for line in lines:
        if len(line) == 0:
            newlines.append(line)
        elif line[0] == uid:
            newlines.append(newline)
        else:
            newlines.append(line)
    write_rows(filepath, newlines)

def is_successor(lev1, lev2, levelcount):
    if (lev2 - lev1) == 1:
        return True
    elif lev1 == levelcount - 1 and lev2 == 0:
        return True
    else:
        return False

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
                return i
        return hintcount

class GlobalVariables():
    def __init__(self):
        self.speed = 1
        self.hints = load_hint_data(self.speed)
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
        return render_template('admin.html', stats='', msg='Jsi v admin menu.', msgcolor='pos')
    elif uid in gv.uids:
        return render_template('main.html', msg='Úspěšné přihlášení.', msgcolor='pos', tn=gettn(uid))   
    else:
        return render_template('index.html', msg='Špatné týmové heslo.', msgcolor='neg')


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
                return render_template('main.html', msg='Začni kódem startovního stanoviště.', msgcolor='neg', tn=teaminfo.name) 
            else:
                level = act_hint.levelnumber
                if teaminfo.level == level:
                    return render_template('main.html', msg='Tento kód už byl zadán.', msgcolor='neg', tn=teaminfo.name) 
                elif not is_successor(teaminfo.level, level, gv.levelcount):
                    return render_template('main.html', msg='Stanoviště mimo pořadí.', msgcolor='neg', tn=teaminfo.name)
                else:
                    teaminfo.level = level
                    if level == teaminfo.startlevel and not teaminfo.is_ended:
                        teaminfo.is_ended = True
                        teaminfo.end = gettimestamp()
                        update_team_data(teaminfo)
                        return render_template('main.html', msg='Jsi v cíli, jdi do Jistoty!', msgcolor='pos', tn=teaminfo.name) 
                    else:
                        teaminfo.levelstats[level] = gettimestamp()
                        update_team_data(teaminfo)                               
                        return render_template('main.html', msg='Super!', msgcolor='pos', tn=teaminfo.name) 
        elif is_correct_startcode:
            if not teaminfo.is_started:
                teaminfo.is_started = True
                level = act_hint.levelnumber
                teaminfo.level = level
                teaminfo.startlevel = level
                teaminfo.start = gettimestamp()
                teaminfo.levelstats[level] = gettimestamp()
                update_team_data(teaminfo)
                return render_template('main.html', msg='Hra začíná!', msgcolor='pos', tn=gettn(uid)) 
            else:
                return render_template('main.html', msg='Kód nebyl nalezen.', msgcolor='neg', tn=gettn(uid))      
        else:
            return render_template("main.html", msg="Kód nebyl nalezen.", msgcolor='neg', tn=gettn(uid))          
    else:
        return render_template("main.html", msg="Tým nebyl nalezen.", msgcolor='neg', tn="")

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
        if act_hint is None:
            return send_file('./imgs/loadfail.jpg', mimetype='image/jpeg')
        hintnumber = act_hint.get_hintinfo(timewait)
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
        act_hint = None
        for hint in gv.hints:
            if hint.levelnumber == level:
                act_hint = hint
        if act_hint is None:
            return {'status': 'invalid'}
        utchinttimes = []
        utchinttime = timeonlevel
        waittimes = act_hint.hinttimes
        for waittime in waittimes:
            utchinttime += waittime
            utchinttimes.append(utchinttime)
        return {'status': 'valid', 'htimes': utchinttimes}
    except:
        return {'status': 'invalid'}

@app.route('/get-stats')
def get_stats():
    adminid = format(request.args.get('tname'))
    if adminid == gv.admcode:
        headerline = ['Teamname', 'Start', 'End']
        for i in range (gv.levelcount):
            headerline.append(str(i))
        lines = []
        for uid in gv.uids:
            line = []
            teaminfo = load_team_data(uid)
            line.append(teaminfo.name)
            line.append(gethms(teaminfo.start))
            line.append(gethms(teaminfo.end))
            for levelstat in teaminfo.levelstats:
                line.append(gethms(levelstat))
            lines.append(line)
        htmlstring = tabletostring(headerline, lines)
        return render_template('admin.html', stats=htmlstring, msg='Statistiky načteny', msgcolor='pos')          
    else:
        return render_template('index.html', msg='Ani to nezkoušej.', msgcolor = 'neg')

@app.route('/reset-game')
def reset_game():
    uid = format(request.args.get('tname'))
    if uid == gv.admcode:
        resetuid = format(request.args.get('rname'))
        teaminfo = load_team_data(resetuid)
        if teaminfo is not None:
            for i in range (len(teaminfo.levelstats)):
                teaminfo.levelstats[i] = -1
            teaminfo.startlevel = -1
            teaminfo.level = -1
            teaminfo.is_started = False
            teaminfo.start = -1
            teaminfo.end = -1
            teaminfo.is_ended = False
            update_team_data(teaminfo)
            return render_template('admin.html', stats='', msg=f'Tým {teaminfo.name} restartován.', msgcolor='pos')
        else:
            return render_template('admin.html', stats='', msg=f'Tým nenalezen.', msgcolor='neg')
    else:
        return render_template('index.html', msg='Ani to nezkoušej.', msgcolor = 'neg')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    serve(app, host="0.0.0.0", port=port)