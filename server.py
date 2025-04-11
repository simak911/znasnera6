from flask import Flask, render_template, request, send_file, g
from waitress import serve
import time

def timestamp():
    return round(time.time())

class GlobalVariables():
    def __init__(self):
        self.teams = {'test69': Team('test','test69')}
        self.uids = []
        self.codes = ['qwe','asd','zxc']
        self.startcodes = ['iop','jkl','bnm']
        self.hintstimes = [[10,20,30],[15,30,45],[30,60,90]]
        self.admcode = 'a6d9m'

class Team():
    def __init__(self, name, uid):
        self.name = name
        self.uid = uid
        self.level = -1
        self.stats = {}
        self.startlevel = -1
        self.isstarted = False
        self.isended = False

gv = GlobalVariables()
regteams = {}
f = open('./teams.txt','r', encoding='utf-8')
lines = f.readlines()
for line in lines:
    line = line.replace("\n","")
    line = line.replace(" ","")
    teaminfo = line.split(",")
    if len(teaminfo)==2: 
        regteams[teaminfo[1]] = teaminfo[0]
gv.uids = list(regteams.keys())
for uid in gv.uids:
    name = regteams[uid]
    team = Team(name, uid)
    gv.teams[uid] = team
gv.uids.append('test69')

app = Flask(__name__)
@app.route('/')
@app.route('/index')
def get_login_page():
    return render_template('index.html', msg='', msgcolor='neut')

@app.route('/main')
def get_main_page():
    uid = request.args.get('tname')
    if uid == gv.admcode:
        return render_template('admin.html', msg='Logged into admin menu.', msgcolor='pos')
    elif uid in gv.uids:
        return render_template('main.html', msg='Successful login.', msgcolor='pos')   
    else:
        return render_template('index.html', msg='Wrong team ID.', msgcolor='neg')


@app.route('/entered')
def entered():
    code = request.args.get('code')
    uid = request.args.get('tname')
    if uid in gv.uids:
        if code in gv.codes:
            if not gv.teams[uid].isstarted:
                return render_template('main.html', msg='Game not started yet.', msgcolor='neg') 
            else:
                level = gv.codes.index(code)
                gv.teams[uid].level = level
                if level == gv.teams[uid].startlevel and not gv.teams[uid].isended:
                    gv.teams[uid].isended = True
                    gv.teams[uid].stats['e'] = timestamp() 
                    gv.teams[uid].stats['t'] = gv.teams[uid].stats['e'] - gv.teams[uid].stats['s']
                    return render_template('main.html', msg='Finish! Go to Jistota!', msgcolor='pos') 
                else:
                    stringlevel = str(level)
                    if not (stringlevel in gv.teams[uid].stats.keys()):
                        gv.teams[uid].stats[stringlevel] = timestamp()                                
                    return render_template('main.html', msg='Success!', msgcolor='pos') 
        elif code in gv.startcodes:
            if not gv.teams[uid].isstarted:
                gv.teams[uid].isstarted = True
                level = gv.startcodes.index(code)
                gv.teams[uid].level = level
                gv.teams[uid].startlevel = level
                stringlevel = str(level)
                gv.teams[uid].stats[stringlevel] = timestamp()
                gv.teams[uid].stats['s'] = timestamp()   
                return render_template('main.html', msg='Game started!', msgcolor='pos') 
            else:
                return render_template('main.html', msg='Code not found.', msgcolor='neg')      
        else:
            return render_template("main.html", msg="Code not found.", msgcolor='neg')          
    else:
        return render_template("main.html", msg="Team not found.", msgcolor='neg')

@app.route('/get-img')
def get_image():
    try:    
        uid = request.args.get('tname') 
        level = gv.teams[uid].level
        if level > -1:
            return send_file(f'./imgs/s{level}.JPG', mimetype='image/jpeg')
        else:
            return send_file('./imgs/loadfail.jpg', mimetype='image/jpeg')
    except:
        return send_file('./imgs/loadfail.jpg', mimetype='image/jpeg')

@app.route('/get-hint')
def get_hint():
    try:    
        uid = request.args.get('tname') 
        level = gv.teams[uid].level
        stringlevel = str(level)
        timeonlevel = gv.teams[uid].stats[stringlevel]
        timenow = timestamp()
        timewait = timenow - timeonlevel
        hinttimes = gv.hintstimes[level]
        hintnumber = 0
        if timewait>hinttimes[2]: hintnumber=3
        elif timewait>hinttimes[1]: hintnumber=2
        elif timewait>hinttimes[0]: hintnumber=1
        if level > -1:
            if hintnumber > 0:
                return send_file(f'./imgs/h{level}_{hintnumber}.JPG', mimetype='image/jpeg')
            else:
                return send_file('./imgs/wait.jpg', mimetype='image/jpeg')
        else:
            return send_file('./imgs/loadfail.jpg', mimetype='image/jpeg')
    except:
        return send_file('./imgs/loadfail.jpg', mimetype='image/jpeg')

@app.route('/get-hinttimes')
def get_hinttimes():  
    try: 
        uid = request.args.get('tname') 
        level = gv.teams[uid].level
        stringlevel = str(level)
        timeonlevel = gv.teams[uid].stats[stringlevel]
        timenow = timestamp()
        timewait = timenow - timeonlevel
        hinttimes = gv.hintstimes[level]
        htime = 0
        hnumber = 0
        for i in range(3):
            if hinttimes[i] - timewait > 0:
                htime = hinttimes[i] - timewait
                hnumber = i+1
                break  
        return {'status': 'valid', 'htime': htime, 'hnumber': hnumber}
    except:
        return {'status': 'invalid'}

@app.route('/get-stats')
def get_stats():
    uid = request.args.get('tname')
    if uid == gv.admcode:
        response = {}
        for uid in gv.teams.keys():
            stats = gv.teams[uid].stats
            name = gv.teams[uid].name
            response[name] = stats
        return response
    else:
        return render_template('index.html', msg='You have no power here.', msgcolor = 'neg')

@app.route('/reset-game')
def reset_game():
    uid = request.args.get('tname')
    if uid == gv.admcode:
        resetuid = request.args.get('rname')
        if resetuid in gv.uids:
            gv.teams[resetuid].stats = {}
            gv.teams[resetuid].startlevel = -1
            gv.teams[resetuid].level = -1
            gv.teams[resetuid].isstarted = False
            gv.teams[resetuid].isended = False
            return render_template('admin.html', msg=f'Team {gv.teams[resetuid].name} reseted.', msgcolor='pos')
        else:
            return render_template('admin.html', msg=f'Team id not found.', msgcolor='neg')
    else:
        return render_template('index.html', msg='You have no power here.', msgcolor = 'neg')

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=8000)