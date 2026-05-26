from tkinter import *
from random import randrange
from threading import Thread
from time import sleep
from datetime import datetime, timedelta
from sqlite3 import connect
from os.path import exists, dirname
from atexit import register
from sys import platform

root = Tk()
GlobalBG = "#0F0F0F"
root.config(bg=GlobalBG)
root.geometry("750x450")
root.resizable(False,False)

appVersion = f"Trainer/{platform}"
currentUser = "user"
currentScreen = ""
currentSettingScreen = ""
lastQuickAnswer = False
ShowXpGain_Threads = []
baseXp = 25
baseXpRaise = 0.025
eventMultiplier = 1
currentGamemode = "+"
xp = 0
level = 1
levelCap = 2500
combo = 0
highestCombo = 0
xpToLevelUp = 27.094959668359195
questiontext = ""
most_practices_in_session = 0
total_practiced = 0
total_practiced_overall = 0
DataPath = f"{dirname(__file__)}/data.db"
IconsPath = f"{dirname(__file__)}/icons"

CurrentLevelText = Label(root, text="LEVEL 1", bg=GlobalBG, fg="white", font=("New Courier", 13))
XpProgress = Label(root, bg="#ffd700")

if exists(DataPath):
    data_conn = connect(DataPath)
    data_cur = data_conn.cursor()
    data_cur.execute("SELECT name, xp, level, current_gamemode, highest_combo, total_practiced FROM user")
    userStats = data_cur.fetchall()[0]
    currentUser = userStats[0]
    xp = userStats[1]
    level = userStats[2]
    currentGamemode = userStats[3]
    highestCombo = userStats[4]
    total_practiced_overall = userStats[5]
    xpToLevelUp = baseXp ** (baseXpRaise*level + 1) if level <= 85 else 25000
    CurrentLevelText.config(text=f"LEVEL {level}")
else:
    data_conn = connect(DataPath)
    data_cur = data_conn.cursor()

    data_cur.execute("""CREATE TABLE user (
                        name TEXT NOT NULL,
                        password TEXT NOT NULL,
                        xp INTEGER NOT NULL,
                        level INTEGER NOT NULL,
                        membership TEXT NOT NULL,
                        last_login DATETIME NOT NULL,
                        register_date DATETIME NOT NULL,
                        current_gamemode TEXT NOT NULL,
                        highest_combo INTEGER NOT NULL,
                        most_practices_in_session INTEGER NOT NULL,
                        total_practiced INTEGER NOT NULL
                        )""")
    data_cur.execute("""CREATE TABLE sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                        session_start TIMESTAMP NOT NULL,
                        session_end TIMESTAMP,
                        total_practiced TEXT,
                        duration TEXT
                        )""")
    data_cur.execute("""CREATE TABLE practices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                        session_id INTEGER NOT NULL,
                        question TEXT NOT NULL,
                        answer TEXT NOT NULL,
                        user_answer TEXT NOT NULL,
                        user_answer_iscorrect BOOLEAN NOT NULL,
                        currentGamemode TEXT NOT NULL,
                        difficulty TEXT NOT NULL,
                        combo INTEGER NOT NULL,
                        xpReward INTEGER NOT NULL,
                        globalXpMultiplier INTEGER NOT NULL,
                        practice_start DATETIME NOT NULL,
                        practice_end DATETIME NOT NULL,
                        duration TEXT NOT NULL
                        )""")
    now = datetime.now()
    data_cur.execute("INSERT INTO user VALUES (:name, :password, :xp, :level, :membership, :last_login, :register_date, :current_gamemode, :highest_combo, :most_practices_in_session, :total_practiced)", {"name":currentUser, "password":"None", "xp":0, "level":1, "membership":"VIP", "last_login":now, "register_date":now, "current_gamemode":"+", "highest_combo":highestCombo, "most_practices_in_session":most_practices_in_session, "total_practiced":0})
    data_conn.commit()
    del(now)
del(exists); del(DataPath); del(platform)

if currentGamemode == "+":
    num1 = randrange(1, 998)
    num2 = randrange(1, 1000-num1)
    answer = num1 + num2
elif currentGamemode == "-":
    num1 = randrange(2, 999)
    num2 = randrange(1, num1)
    answer = num1 - num2
elif currentGamemode == "x":
    num1 = randrange(2, 10)
    num2 = randrange(2, 10)
    answer = num1 * num2
    while answer >= 1000:
        num1 = randrange(2, 10)
        num2 = randrange(2, 10)
        answer = num1 * num2
elif currentGamemode == "/":
    num1 = randrange(2, 20, 2)
    num2 = randrange(2, 10, 2)
    answer = num1 / num2
    while answer % 2 != 0:
        num1 = randrange(2, 20, 2)
        num2 = randrange(2, 10, 2)
        answer = num1 / num2
elif currentGamemode == "()":
    num1 = randrange(2, 5, 2)
    num2 = randrange(2, 30, 2)
    num3 = randrange(2, 20, 2)
    answer = num1 * (num2 + num3)
    while answer % 2 != 0:
        num1 = randrange(2, 5, 2)
        num2 = randrange(2, 30, 2)
        num3 = randrange(2, 20, 2)
        answer = num1 * (num2 + num3)

start_answer_time = datetime.now()

class HoverButton(Button):
    def __init__(self, master, flip=False, **kw):
        Button.__init__(self, master=master, **kw)
        self.defaultforeground = self["foreground"]
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.flip = flip
        self.active = False
    
    def on_enter(self, i):
        if self.flip:
            self["background"] = "white"
        else:
            self["foreground"] = self["activeforeground"]
    
    def on_leave(self, i):
        if self.flip:
            self["background"] = "gray"

        if not self.active:
            self["foreground"] = "#a3aaaa" if self["text"].lower() != currentSettingScreen.replace("-", " ") else "white"

def LogSession(type):
    global SessionId
    now = datetime.now()
    if type == "start":
        data_cur.execute("INSERT INTO sessions (session_start) VALUES (:session_start)", {"session_start":now})
        data_cur.execute("UPDATE user SET last_login=:last_login", {"last_login":now})
        data_conn.commit()
        data_cur.execute("SELECT MAX(id) FROM sessions")
        SessionId = data_cur.fetchone()[0]
    elif type == "end":
        from re import split as _split
        data_cur.execute("SELECT session_start, MAX(id) id FROM sessions WHERE id IN (SELECT MAX(id) FROM sessions GROUP BY id)")
        session_data = data_cur.fetchone()
        ts = _split("-| |:", session_data[0])
        ts_sec = ts[5].split(".")
        login_timestamp = datetime(int(ts[0]), int(ts[1]), int(ts[2]), int(ts[3]), int(ts[4]), int(ts_sec[0]), int(ts_sec[1]))
        del(_split)
        data_cur.execute("UPDATE sessions SET session_end=:session_end, total_practiced=:total_practiced, duration=:duration WHERE id=:id", {"session_end":now, "total_practiced":total_practiced, "duration":str(timedelta.total_seconds(now - login_timestamp)), "id":session_data[1]})
        if most_practices_in_session < total_practiced:
            data_cur.execute("UPDATE user SET most_practices_in_session=:most_practices_in_session", {"most_practices_in_session":total_practiced})
        data_conn.commit()
        data_conn.close()

def switchScreen(screen, wipe=True, args=None): # XXXXXXXXXxx
    def Task():
        global currentScreen
        if screen == currentScreen:
            return 0

        if wipe:
            if currentScreen == "home":
                Home.config(bg="gray")
                UserAnswer.unbind("<Return>")
                ShowXpText.place_forget()
                CurrentLevelText.place_forget()
                title.place_forget()
                question.place_forget()
                UserAnswer.place_forget()
                CheckButton.place_forget()
                XpFrame.place_forget()
                XpBackground.place_forget()
                XpProgress.place_forget()
                AdditionGamemode.place_forget()
                MinusGamemode.place_forget()
                MultiplyGamemode.place_forget()
                DivisionGamemode.place_forget()
                Special1Gamemode.place_forget()
                if eventMultiplier != 1:
                    Notification.place_forget()
            elif currentScreen == "settings":
                Settings.config(bg="gray")
                UserDefaultImgLabel.place_forget()
                UserGreeting.place_forget()
                RegisterDate.place_forget()
                TotalPracticed.place_forget()
                ProfileSplit.place_forget()
                AppVersionLabel.place_forget()
                SettingPersonalInfo.place_forget()
                SettingStats.place_forget()
                SettingAdditionalInfo.place_forget()
                SettingPersonalInfoImgLabel.place_forget()
                SettingStatsImgLabel.place_forget()
                SettingAdditionalInfoImgLabel.place_forget()
                switchScreenSettings(onlyWipe=True)
            else:
                return 0

        if screen == "home":
            root.title("Home - Trainer")
            Home.config(bg="white")
            UserAnswer.bind("<Return>", Check)
            CurrentLevelText.place(x=3, y=4, width=127, height=20)
            title.place(x=250, y=3, width=250, height=35)
            question.place(x=150, y=125, width=450, height=50)
            UserAnswer.place(x=275, y=195, width=200, height=45)
            CheckButton.place(x=485, y=203, width=50, height=30)
            XpFrame.place(x=3, y=30, width=127, height=20)
            XpBackground.place(x=4, y=31, width=125, height=18)
            try:
                XpProgress.place(x=4, y=31, width=((xp / (xpToLevelUp/100))*1.25) if ((xp / (xpToLevelUp/100))*1.25) <= 125 else 125, height=18)
            except ZeroDivisionError:
                XpProgress.place(x=4, y=31, width=0, height=18)
            AdditionGamemode.place(x=700, y=50, width=50, height=45)
            MinusGamemode.place(x=700, y=95, width=50, height=45)
            MultiplyGamemode.place(x=700, y=140, width=50, height=50)
            DivisionGamemode.place(x=700, y=200, width=50, height=60)
            Special1Gamemode.place(x=700, y=260, width=50, height=50)
            if eventMultiplier != 1:
                Notification.place(x=475, y=7, width=275, height=30)
        elif screen == "settings":
            root.title("Settings - Trainer")
            Settings.config(bg="white")
            UserDefaultImgLabel.place(x=-10, y=-5, width=100, height=90)
            UserGreeting.place(x=90, y=0, height=30)
            RegisterDate.place(x=85, y=28, height=25)
            TotalPracticed.place(x=85, y=48, height=20)
            ProfileSplit.place(x=2, y=75, height=5)
            AppVersionLabel.place(x=630, y=360, width=120, height=20)
            SettingPersonalInfo.place(x=42, y=90, width=150, height=45)
            SettingStats.place(x=42, y=137, width=150, height=45)
            SettingAdditionalInfo.place(x=42, y=184, width=150, height=45)

            SettingPersonalInfoImgLabel.place(x=2, y=95, width=40, height=40); SettingPersonalInfoImgLabel.lift()
            SettingStatsImgLabel.place(x=6, y=142, width=32, height=32); SettingStatsImgLabel.lift()
            SettingAdditionalInfoImgLabel.place(x=6, y=189, width=32, height=32); SettingAdditionalInfoImgLabel.lift()
            switchScreenSettings("personal-info")

        currentScreen = screen
    Thread(target=Task, daemon=True).start()

def switchScreenSettings(settingScreen=None, onlyWipe=False): # XXXXXXXXXxx
    def Task():
        global currentSettingScreen
        if currentSettingScreen == settingScreen:
            return 0
        if settingScreen == "stats" or settingScreen == "additional-info":
            return 0

        if currentSettingScreen == "personal-info":
            SettingPersonalInfo.config(fg="#a3aaaa") if not onlyWipe else None
            SettingPersonalInfoImgLabel.config(bg="gray") if not onlyWipe else None
            PersonalInfo_NameLabel.place_forget()
            PersonalInfo_Name.place_forget()
            PersonalInfo_NameChangeStatus.place_forget()
            PersonalInfo_NameLabelCheckmark.place_forget()
            PersonalInfo_MembershipLabel.place_forget()
            PersonalInfo_Membership.place_forget()
            PersonalInfo_PersonalInfoDescription.place_forget()
        elif currentSettingScreen == "stats":
            SettingStats.config(fg="#a3aaaa")
            SettingStatsImgLabel.config(bg="gray")
            Stats_TotalPasswords.place_forget()
            Stats_AvgTimeSpent.place_forget()
            Stats_Description.place_forget()
        elif currentSettingScreen == "additional-info":
            SettingAdditionalInfo.config(fg="#a3aaaa")
            SettingAdditionalInfoImgLabel.config(bg="gray")

        if onlyWipe:
            SettingPersonalInfo.config(fg="white")
            SettingPersonalInfoImgLabel.config(bg="white")
            currentSettingScreen = ""
            return 0

        if settingScreen == "personal-info":
            SettingPersonalInfo.config(fg="white")
            SettingPersonalInfoImgLabel.config(bg="white")
            PersonalInfo_NameLabel.place(x=320, y=100, height=30)
            PersonalInfo_NameLabelCheckmark.place(x=499, y=129, width=22, height=20)
            PersonalInfo_Name.place(x=320, y=128, width=175, height=26)
            PersonalInfo_MembershipLabel.place(x=320, y=209, height=26)
            PersonalInfo_Membership.place(x=321, y=237, height=26)
        elif settingScreen == "stats":
            SettingStats.config(fg="white")
            SettingStatsImgLabel.config(bg="white")
            # Stats_AvgTimeSpent.place(x=285, y=95, height=36)
            # Stats_TotalPasswords.place(x=485, y=95, height=36)
            Stats_Description.place(x=270, y=290, width=510, height=70)
        elif settingScreen == "additional-info":
            SettingAdditionalInfo.config(fg="white")
            SettingAdditionalInfoImgLabel.config(bg="white")

        currentSettingScreen = settingScreen
        return 0
    Thread(target=Task, daemon=True).start()

def CheckDifficulty(num1, num2):
    difficulty = 0
    if currentGamemode == "+" or currentGamemode == "-":
        if num1 > 99:
            difficulty += 1
        elif num1 < 10:
            difficulty -= 1

        if num2 > 99:
            difficulty += 1
        elif num2 < 10:
            difficulty -= 1

        if num1 > 9 and num2 > 9 and int(str(num1)[-1:]) + int(str(num2)[-1:]) >= 10:
            difficulty += 1
        if num1 > 99 and num2 > 99 and int(str(num1)[-2:-1]) + int(str(num2)[-2:-1]) >= 10:
            difficulty += 2
    elif currentGamemode == "()":
        difficulty = 5
    else:
        difficulty = 3

    if difficulty <= 1:
        return "Easy"
    elif difficulty == 2:
        return "Medium"
    elif difficulty == 3 or difficulty == 4:
        return "Hard"
    else:
        return "Extreme"

def ShowXpGain(amount: int, combo: int, difficulty: str, quick: bool, close: bool, length: float):
    global ShowXpGain_Threads
    def Task():
        thread_id = randrange(0, 999999999999)
        if thread_id in ShowXpGain_Threads:
            while thread_id in ShowXpGain_Threads:
                thread_id = randrange(0, 999999999999)
        ShowXpGain_Threads.append(thread_id)

        text = f"+{amount} XP!"
        second_line = ""

        if close:
            second_line = "CLOSE!"
        if combo >= 2:
            second_line = f"{combo if combo <= 9999 else 9999}x COMBO!"
        if quick:
            second_line = f"{second_line} QUICK!"
        if difficulty == "Hard" or difficulty == "Extreme":
            second_line = f"{second_line} {difficulty.upper()}!"

        
        ShowXpText.config(text=f"{text}\n{second_line}" if second_line != "" else text)

        ShowXpText.place(x=100, y=70, width=550, height=50)
        sleep(length)
        if len(ShowXpGain_Threads) == 1:
            ShowXpText.place_forget()
        ShowXpGain_Threads.pop(ShowXpGain_Threads.index(thread_id))
    Thread(target=Task, daemon=True).start()
    return 0

def AppendXp(addXp):
    global level
    global xp
    global xpToLevelUp
    xp += addXp
    while xp >= xpToLevelUp and level < levelCap:
        xp -= xpToLevelUp
        level += 1
        xpToLevelUp = baseXp ** (baseXpRaise*level + 1) if level <= 85 else 25000
    changeData("xp+level", [xp, level])
    CurrentLevelText.config(text=f"LEVEL {level}")
    XpProgress.place(x=4, y=31, width=((xp / (xpToLevelUp/100))*1.25) if ((xp / (xpToLevelUp/100))*1.25) <= 125 else 125, height=18)

def StartEvent(event_title, multiplier, end_date):
    def Task():
        date_in_seconds = timedelta.total_seconds(end_date - datetime.now())
        if date_in_seconds > 0:
            global eventMultiplier
            eventMultiplier = multiplier
            Notification.config(text=event_title)
            Notification.place(x=475, y=7, width=275, height=30)
            Notification.lift()
            
            sleep(date_in_seconds)

            eventMultiplier = 1
            Notification.place_forget()
    Thread(target=Task, daemon=True).start()

def Check(*args, restart=False):
    global num1
    global num2
    global answer
    global combo
    global start_answer_time
    global questiontext
    if not restart:
        xpReward = 0
        finish_answer_time = datetime.now()
        time_to_answer = timedelta.total_seconds(finish_answer_time - start_answer_time)
        result = None
        user_answer_value = UserAnswer.get()
        difficulty = CheckDifficulty(num1, num2)
        try:
            user_answer_value = int(user_answer_value)
            if user_answer_value == answer:
                result = "Correct"
            elif answer - user_answer_value >= -5 and answer - user_answer_value <= 5 and currentGamemode != "x" and currentGamemode != "/":
                result = "Close"
            else:
                result = "Incorrect"
        except ValueError:
            result = "Incorrect"
        finally:
            if result == "Correct":
                if time_to_answer < 3:
                    lastQuickAnswer = True
                else:
                    lastQuickAnswer = False
                combo += 1
                global highestCombo
                if combo > highestCombo:
                    highestCombo = combo
                    changeData("highest_combo", highestCombo)
                _xpReward = 7 if difficulty == "Hard" else 10 if difficulty == "Extreme" else 5
                xpReward = ((_xpReward*combo if _xpReward*combo < 20 else 20) * 2 if lastQuickAnswer else (_xpReward*combo if _xpReward*combo < 20 else 20)) * eventMultiplier
                AppendXp(xpReward)
                ShowXpGain(xpReward, combo, difficulty, lastQuickAnswer, False, 0.95 if combo > 10 else 1.35)
            elif result == "Close":
                combo = 0
                xpReward = 3 if difficulty == "Hard" else 4 if difficulty == "Extreme" else 2
                AppendXp(xpReward)
                ShowXpGain(xpReward, combo, difficulty, False, True, 1.35)
            else:
                combo = 0
            global total_practiced
            data_cur.execute("INSERT INTO practices (session_id, question, answer, user_answer, user_answer_iscorrect, currentGamemode, difficulty, combo, xpReward, globalXpMultiplier, practice_start, practice_end, duration) VALUES(:session_id, :question, :answer, :user_answer, :user_answer_iscorrect, :currentGamemode, :difficulty, :combo, :xpReward, :globalXpMultiplier, :practice_start, :practice_end, :duration)", {"session_id":SessionId, "question":f"{question}", "answer":answer, "user_answer":user_answer_value, "user_answer_iscorrect":True if answer == user_answer_value else False, "currentGamemode":currentGamemode, "difficulty":difficulty, "combo":combo, "xpReward":xpReward, "globalXpMultiplier":eventMultiplier, "practice_start":start_answer_time, "practice_end":finish_answer_time, "duration":time_to_answer})
            changeData("total_practiced+1", None)
            total_practiced += 1
            TotalPracticed.config(text=f"• Total Practiced: {total_practiced_overall+total_practiced}")

    if currentGamemode == "+":
        num1 = randrange(1, 998)
        num2 = randrange(1, 1000-num1)
        answer = num1 + num2
    elif currentGamemode == "-":
        num1 = randrange(2, 999)
        num2 = randrange(1, num1)
        answer = num1 - num2
    elif currentGamemode == "x":
        num1 = randrange(2, 10)
        num2 = randrange(2, 10)
        answer = num1 * num2
        if answer >= 1000:
            while answer >= 1000:
                num1 = randrange(2, 10)
                num2 = randrange(2, 10)
                answer = num1 * num2
    elif currentGamemode == "/":
        num1 = randrange(2, 20, 2)
        num2 = randrange(2, 10, 2)
        answer = num1 / num2
        if answer % 2 != 0:
            while answer % 2 != 0:
                num1 = randrange(2, 20, 2)
                num2 = randrange(2, 10, 2)
                answer = num1 / num2
    elif currentGamemode == "()":
        num1 = randrange(2, 5, 2)
        num2 = randrange(2, 30, 2)
        num3 = randrange(2, 20, 2)
        answer = num1 * (num2 + num3)
        while answer % 2 != 0:
            num1 = randrange(2, 5, 2)
            num2 = randrange(2, 30, 2)
            num3 = randrange(2, 20, 2)
            answer = num1 * (num2 + num3)
    UserAnswer.delete(0, "end")
    if currentGamemode == "()":
        questiontext = f"{num1}*({num2}+{num3})"
        question.config(text=f"{num1} x ({num2} + {num3}) = ?")
    else:
        questiontext = f"{num1}{currentGamemode}{num2}"
        question.config(text=f"{num1} {currentGamemode} {num2} = ?")
    
    start_answer_time = datetime.now()
    return 0

def SwitchGamemode(next_gamemode):
    global currentGamemode
    if currentGamemode == next_gamemode:
        return 0
    
    if currentGamemode == "+":
        AdditionGamemode.config(fg="#a3aaaa")
        AdditionGamemode.active = False
    elif currentGamemode == "-":
        MinusGamemode.config(fg="#a3aaaa")
        MinusGamemode.active = False
    elif currentGamemode == "x":
        MultiplyGamemode.config(fg="#a3aaaa")
        MultiplyGamemode.active = False
    elif currentGamemode == "/":
        DivisionGamemode.config(fg="#a3aaaa")
        DivisionGamemode.active = False
    elif currentGamemode == "()":
        Special1Gamemode.config(fg="#a3aaaa")
        Special1Gamemode.active = False
    
    if next_gamemode == "+":
        AdditionGamemode.config(fg="white")
        AdditionGamemode.active = True
    elif next_gamemode == "-":
        MinusGamemode.config(fg="white")
        MinusGamemode.active = True
    elif next_gamemode == "x":
        MultiplyGamemode.config(fg="white")
        MultiplyGamemode.active = True
    elif next_gamemode == "/":
        DivisionGamemode.config(fg="white")
        DivisionGamemode.active = True
    elif next_gamemode == "()":
        Special1Gamemode.config(fg="white")
        Special1Gamemode.active = True

    currentGamemode = next_gamemode
    data_cur.execute("UPDATE user SET current_gamemode=:current_gamemode", {"current_gamemode":currentGamemode})
    data_conn.commit()
    Check(restart=True)

def ConvertDate(date: str):
    from re import split as _split
    _now = _split("-| ", date)
    month = "January" if int(_now[1]) == 1 else "February" if int(_now[1]) == 2 else "March" if int(_now[1]) == 3 else "April" if int(_now[1]) == 4 else "May" if int(_now[1]) == 5 else "June" if int(_now[1]) == 6 else "July" if int(_now[1]) == 7 else "August" if int(_now[1]) == 8 else "September" if int(_now[1]) == 9 else "October" if int(_now[1]) == 10 else "November" if int(_now[1]) == 11 else "December"

    del(_split)
    return f"{month} {_now[2]}, {_now[0]}"

def fetchData(dataName):
    if dataName == "password":
        data_cur.execute("SELECT password FROM user")
    elif dataName == "membership":
        data_cur.execute("SELECT membership FROM user")
    elif dataName == "last_login":
        data_cur.execute("SELECT last_login FROM user")
    elif dataName == "register_date":
        data_cur.execute("SELECT register_date FROM user")
    elif dataName == "total_practiced":
        data_cur.execute("SELECT total_practiced FROM user")
    else:
        raise Exception(f"Data {dataName} does not exist or is not defined")

    return data_cur.fetchone()[0]

def changeData(dataName, newValue):
    if dataName == "xp+level":
        data_cur.execute("UPDATE user SET xp=:xp, level=:level", {"xp":newValue[0], "level":newValue[1]})
    elif dataName == "total_practiced+1":
        data_cur.execute("UPDATE user SET total_practiced=total_practiced + 1")
    elif dataName == "highest_combo":
        data_cur.execute("UPDATE user SET highest_combo=:highest_combo", {"highest_combo":newValue if newValue <= 9999 else 9999})
    elif dataName == "name":
        data_cur.execute("UPDATE user SET name=:name", {"name":newValue})
    else:
        raise Exception(f"Data {dataName} does not exist or is not defined")

    data_conn.commit()
    return 0

def validName(name):
    if name != "" and len(name) <= 25 and name.replace(" ", "").isalnum():
        return True

    elif name == "":
        return "Name cannot be empty"
    elif len(name) > 25:
        return "Name cannot be longer than 25 characters"
    elif not name.replace(" ", "").isalnum():
        return "Name cannot include special characters"
    else:
        return False

def changeName(name: str):
    global currentUser
    currentUser = name
    UserGreeting.config(text=name)
    changeData("name", name)
    return 0

def PersonalInfo_SaveDataStatus(datatype):
    NewName = PersonalInfo_Name.get()
    PersonalInfo_NameChangeStatus.config(text="Saving...", fg="green")
    PersonalInfo_NameChangeStatus.place(x=455, y=101, height=28)
    validNameOutput = validName(NewName)
    if validNameOutput == True and NewName != currentUser:
        changeName(NewName)
        PersonalInfo_NameChangeStatus.config(text="Saved!", fg="green")
        PersonalInfo_NameChangeStatus.place(x=447, y=101, height=28)
    elif NewName == currentUser:
        PersonalInfo_NameChangeStatus.config(text="Saved!", fg="green")
        PersonalInfo_NameChangeStatus.place(x=447, y=101, height=28)
    else:
        PersonalInfo_NameChangeStatus.config(text=validNameOutput, fg="red")
        PersonalInfo_NameChangeStatus.place(x=320, y=153, height=26)

    return 0

def Configuration():
    # home configuration
    title.config(text="Trainer", bg=GlobalBG, fg="white", font=("bold", 26))
    question.config(bg=GlobalBG, fg="white", font=("bold", 40))
    UserAnswer.config(bg=GlobalBG, fg="white", font=("bold", 24), border=2, highlightcolor="gray", highlightbackground="gray", insertbackground="white")
    CheckButton.config(text="Check", bg=GlobalBG, fg="#a3aaaa", font=("bold", 12), activebackground="white", activeforeground="white", highlightbackground=GlobalBG, command=Check)
    ShowXpText.config(bg=GlobalBG, fg="#ffd700", font=("bold", 16))
    XpFrame.config(bg="gray")
    XpBackground.config(bg=GlobalBG)
    XpProgress.lift()
    AdditionGamemode.config(text="+", font=("bold", 40), bg=GlobalBG, fg="white" if currentGamemode == "+" else "#a3aaaa", activebackground=GlobalBG, activeforeground="white", border=0, highlightbackground=GlobalBG, command=lambda:SwitchGamemode("+"))
    MinusGamemode.config(text="-", font=("bold", 40), bg=GlobalBG, fg="white" if currentGamemode == "-" else "#a3aaaa", activebackground=GlobalBG, activeforeground="white", border=0, highlightbackground=GlobalBG, command=lambda:SwitchGamemode("-")) 
    MultiplyGamemode.config(text="x", font=("bold", 40), bg=GlobalBG, fg="white" if currentGamemode == "x" else "#a3aaaa", activebackground=GlobalBG, activeforeground="white", border=0, highlightbackground=GlobalBG, command=lambda:SwitchGamemode("x"))
    DivisionGamemode.config(text="/", font=("bold", 40), bg=GlobalBG, fg="white" if currentGamemode == "/" else "#a3aaaa", activebackground=GlobalBG, activeforeground="white", border=0, highlightbackground=GlobalBG, command=lambda:SwitchGamemode("/"))
    Special1Gamemode.config(text="()", font=("bold", 40), bg=GlobalBG, fg="white" if currentGamemode == "()" else "#a3aaaa", activebackground=GlobalBG, activeforeground="white", border=0, highlightbackground=GlobalBG, command=lambda:SwitchGamemode("()"))
    Notification.config(bg="red", fg="white", font=("bold", 10))
    HomeImg.config(file=f"{IconsPath}/Home.png")
    Home.config(image=HomeImg, bg="white", borderwidth=0, activebackground="white", highlightbackground=GlobalBG, command=lambda: switchScreen("home"))
    HomeLabel.config(text="Home", bg=GlobalBG, fg="white")
    SettingsImg.config(file=f"{IconsPath}/Settings.png")
    Settings.config(image=SettingsImg, bg="gray", borderwidth=0, activebackground="white", highlightbackground=GlobalBG, command=lambda: switchScreen("settings"))
    SettingsLabel.config(text="Settings", bg=GlobalBG, fg="white")
    UserDefaultImgLabel.config(image=UserDefaultImgSmall, bg=GlobalBG, activebackground=GlobalBG)
    UserGreeting.config(text=currentUser, bg=GlobalBG, fg="white", font=("bold", 16))
    AppVersionLabel.config(text=appVersion, bg=GlobalBG, fg="white", font=("bold", 8))
    RegisterDate.config(text=f"• Member since {ConvertDate(fetchData('register_date')[:-7])}", bg=GlobalBG, fg="gray", font=("bold", 10))
    TotalPracticed.config(text=f"• Total Practiced: {fetchData('total_practiced')}", bg=GlobalBG, fg="gray", font=("bold", 10))
    ProfileSplit.config(text="─────────────────────", bg=GlobalBG, fg="#929292", font=("Arial", 16))
    LineSplitBottom.config(text="──────────────────────────────────────────────────────", bg=GlobalBG, fg="gray", font=("Arial", 16))

    # settings configuration
    UserDefaultImgSmall.config(file=f"{IconsPath}/UserMedium.png")
    SettingPersonalInfoImg.config(file=f"{IconsPath}/UserSmall.png")
    SettingStatsImg.config(file=f"{IconsPath}/Stats.png")
    SettingAdditionalInfoImg.config(file=f"{IconsPath}/Information.png")
    SettingPersonalInfoImgLabel.config(image=SettingPersonalInfoImg, bg="white")
    SettingStatsImgLabel.config(image=SettingStatsImg, bg="gray")
    SettingAdditionalInfoImgLabel.config(image=SettingAdditionalInfoImg, bg="gray")
    SettingPersonalInfo.config(text="Personal Info", font=("bold", 14), bg=GlobalBG, fg="white", command=lambda: switchScreenSettings("personal-info"), activebackground=GlobalBG, activeforeground="white", border=0, highlightbackground=GlobalBG, anchor="w")
    SettingStats.config(text="Stats", font=("bold", 14), bg=GlobalBG, fg="#a3aaaa", command=lambda: switchScreenSettings("stats"), activebackground=GlobalBG, activeforeground="white", border=0, highlightbackground=GlobalBG, anchor="w")
    SettingAdditionalInfo.config(text="Additional Info", font=("bold", 14), bg=GlobalBG, fg="#a3aaaa", command=lambda: switchScreenSettings("additional-info"), activebackground=GlobalBG, activeforeground="white", border=0, highlightbackground=GlobalBG, anchor="w")

    PersonalInfo_CheckmarkImg.config(file=f"{IconsPath}/Checkmark.png")
    PersonalInfo_NameLabel.config(text="Name", font=("bold", 11), bg=GlobalBG, fg="#A3AEAE")
    PersonalInfo_Name.config(font=("bold", 12), bg=GlobalBG, fg="white", borderwidth=2, highlightcolor=GlobalBG, highlightbackground=GlobalBG, insertbackground="white")
    PersonalInfo_Name.insert(0, currentUser)
    PersonalInfo_NameChangeStatus.config(text="Saving...", font=("bold", 10), bg=GlobalBG, fg="green")
    PersonalInfo_NameLabelCheckmark.config(image=PersonalInfo_CheckmarkImg, bg="gray", borderwidth=0, activebackground="white", highlightbackground=GlobalBG, command=lambda: PersonalInfo_SaveDataStatus("Name"))
    PersonalInfo_MembershipLabel.config(text="Membership", font=("bold", 11), bg=GlobalBG, fg="#A3AEAE")
    PersonalInfo_Membership.config(text=fetchData("membership"), font=("bold", 12), bg=GlobalBG, fg="gold")
    PersonalInfo_PersonalInfoDescription.config(text="Name", font=("bold", 8), bg=GlobalBG, fg="#A3AEAE")

    Stats_TotalPasswords.config(text="Total Passwords\n0", font=("bold", 11), bg=GlobalBG, fg="white")
    Stats_AvgTimeSpent.config(text="Average Time Spent on App:  0 seconds", font=("bold", 11), bg=GlobalBG, fg="white")
    Stats_Description.config(text="Stats offer a deeper insight about the way you use Trainer.                                              \nWhile they currently don't offer much use, they are                                                              \ncertainly interesting to look at.                                                                                                        ", font=("bold", 10), bg=GlobalBG, fg="white")

    AdditionalInfo_Description.config(text="Trainer® 2022 - All Rights Reserved")

    Home.place(x=166, y=397, width=41, height=37)
    Settings.place(x=541.5, y=395, width=40, height=40)
    LineSplitBottom.place(x=0, y=380, width=750, height=5)

    return 0

Home = HoverButton(root, flip=True)
HomeLabel = Label(root)
HomeImg = PhotoImage()
Settings = HoverButton(root, flip=True)
SettingsLabel = Label(root)
SettingsImg = PhotoImage()
LineSplitBottom = Label(root)

title = Label(root)
question = Label(root)
UserAnswer = Entry(root)
CheckButton = HoverButton(root)
ShowXpText = Label(root)
XpFrame = Label(root)
XpBackground = Label(root)
XpProgress.lift()
AdditionGamemode = HoverButton(root)
MinusGamemode = HoverButton(root)
MultiplyGamemode = HoverButton(root)
DivisionGamemode = HoverButton(root)
Special1Gamemode = HoverButton(root)
Notification = Label(root)

# Settings screen
UserDefaultImgSmall = PhotoImage()
SettingPersonalInfoImg = PhotoImage()
SettingSecurityImg = PhotoImage()
SettingOtherUsersImg = PhotoImage()
SettingStatsImg = PhotoImage()
SettingAdditionalInfoImg = PhotoImage()

SettingsLabel = Label(root)
UserDefaultImgLabel = Label(root)
UserGreeting = Label(root)
RegisterDate = Label(root)
TotalPracticed = Label(root)
ProfileSplit = Label(root)
AppVersionLabel = Label(root)
SettingPersonalInfoImgLabel = Label(root)
SettingStatsImgLabel = Label(root)
SettingAdditionalInfoImgLabel = Label(root)
SettingPersonalInfo = HoverButton(root)
SettingStats = HoverButton(root)
SettingAdditionalInfo = HoverButton(root)

PersonalInfo_CheckmarkImg = PhotoImage()
PersonalInfo_NameLabel = Label(root)
PersonalInfo_NameLabelCheckmark = HoverButton(root, flip=True)
PersonalInfo_Name = Entry(root)
PersonalInfo_NameChangeStatus = Label(root)
PersonalInfo_MembershipLabel = Label(root)
PersonalInfo_Membership = Label(root)
PersonalInfo_PersonalInfoDescription = Label(root)

Stats_TotalPasswords = Label(root)
Stats_AvgWeeklyTime = Label(root)
Stats_AvgTimeSpent = Label(root)
Stats_Description = Label(root)

AdditionalInfo_Description = Label(root)

Check(restart=True)
Configuration()
switchScreen("home", wipe=False)
StartEvent("GLOBAL LAUNCH 2x XP CELEBRATION!", 2, datetime(2023, 3, 16, 0, 0, 0))

LogSession("start")
register(LogSession, "end")

root.mainloop()
