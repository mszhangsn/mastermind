import cherrypy
import random
import os.path
import sqlite3
import pickle

conn = sqlite3.connect('mydb.db',check_same_thread=False)
c = conn.cursor()
# c.execute('''CREATE TABLE highrecord (username, playtimes, highrecord)''')
# conn.commit()

basehtml = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>Mastermind</title>
    <link href="/style.css" type="text/css" rel="stylesheet">
</head>
"""

class MyApp:

    def __init__(self):
        return

    def index(self,playtimes = 0,guessnum = 0):
        if os.path.isfile("record.txt"):
            os.remove("record.txt")
        if os.path.isfile("oneroundrecord.txt"):
            os.remove("oneroundrecord.txt")
        html = """
        <body>
            <div id="container">
                <h1>Welcome to Mastermind Game!</h1>
                <form method="get" action="/result">
                    What's your name? <input type="text" name="username" id="username" required>
                    <p>Please enter 4 integers in range 1 to 6</p>
                    <p>(do not use space or comma to seperate those integers):</p>
                    <input type="text" name="text" id="text" placeholder="e.g. 1234" required>
                    <input type="submit" value="Guess">
                </form>
                <br>
            </div>
        </body>
        </html>
        """
        return basehtml + html

    def readfile(self,file):
        myfile = open(file,"r")
        record = myfile.readlines()
        return "".join(record)

    def saverecord(self,guessnum,answer):
        myfile = open("oneroundrecord.txt","wb")
        dic = {
            'guessnum' : guessnum,
            'answer' : answer,
        }
        pickle.dump(dic, myfile)
        myfile.close()

    def writefile(self,guessnum,userinput,right_num_right_place,right_num_wrong_place):
        myfile = open("record.txt","a")
        myfile.write("<p>guess " + str(guessnum) + ": " + ''.join(list(map(str,userinput))) + " right_num_right_place: " + str(right_num_right_place) + " right_num_wrong_place: " + str(right_num_wrong_place) +  "</p>")
        myfile.close()

    def savehighrecord(self,username,playtimes,guessnum):
        name = username
        playtimes = int(playtimes)
        guessnum = int(guessnum)
        c.execute('SELECT * FROM highrecord WHERE username=?', (name,))
        record = c.fetchone()
        if not record:
            c.execute("INSERT INTO highrecord VALUES (?,?,?)", (name,playtimes,guessnum))
        else:
            if int(record[2]) <= guessnum:
                c.execute("UPDATE highrecord SET playtimes = ?", (playtimes,))
            else:
                c.execute("UPDATE highrecord SET playtimes = ?, highrecord = ?", (playtimes,guessnum))
        conn.commit()

    def highrecord(self):
        cherrypy.session.load()
        name = cherrypy.session.get('name')
        c.execute('SELECT EXISTS(SELECT 1 FROM highrecord WHERE username=? LIMIT 1)', (name,))
        exist = c.fetchone()
        num = ''.join(map(str,exist))
        if num == '1':
            c.execute('SELECT * FROM highrecord WHERE username=?', (name,))
            record = c.fetchone()
            if record[2] > 12:
                return basehtml + """
                <body>
                <div id="smcontainer">
                    <p>You don't have any record.</p>
                    <a href="/index">Start a new game</a>
                    <br><br>
                    <a href="/result">Continue game</a>
                </div>
                </body>
                </html>
                """
            else:
                return basehtml + """
                <body>
                <div id="smcontainer">
                    <p>You played this game %s times.</p>
                    <p>Your best record is: guessed the right answer in %s rounds</p>
                    <a href="/index">Start a new game</a>
                    <br><br>
                    <a href="/result">Continue game</a>
                </div>
                </body>
                </html>
                """ %(record[1],record[2])
        else:
            return basehtml + """
            <body>
            <div id="smcontainer">
                <p>You haven't play the game yet.</p>
                <a href="/index">Start a new game</a>
                <br><br>
                <a href="/result">Continue game</a>
            </div>
            </body>
            </html>
            """

    def result(self,text=None,username=None):
        if username == None:
            cherrypy.session.load()
            username = cherrypy.session.get('name')
        if os.path.isfile("oneroundrecord.txt"):
            myfile = open("oneroundrecord.txt", 'rb')
            dic = pickle.load(myfile)
            guessnum = dic['guessnum']
            answer = dic['answer']
            myfile.close()
        else:
            guessnum = 0
            answer = []
            for num in range(0,4):
                answer.append(random.randint(1,6))
        cherrypy.session['name'] = username
        message = ""
        record = ""
        error = 0
        c.execute('SELECT EXISTS(SELECT 1 FROM highrecord WHERE username=? LIMIT 1)', (username,))
        exist = c.fetchone()
        num = ''.join(map(str,exist))
        if num == '1':
            c.execute('SELECT playtimes FROM highrecord WHERE username=?', (username,))
            record = c.fetchone()
            playtimes = int(''.join(map(str,record)))
        else:
            playtimes = 0
        if text:
            userinput = list(text.strip())
            if len(userinput) != 4:
                message = "Sorry, please exactly enter 4 numbers."
            else:
                try:
                    inputnum = list(map(int,userinput))
                    right_num_right_place = 0
                    right_num_wrong_place = 0
                    tempanswer = answer[:]
                    tempinput = inputnum[:]
                    for i in range(0,4):
                        if inputnum[i] > 6:
                            error += 1
                    if error != 0:
                        message = "Sorry, you must enter integers between 1 and 6."
                    else:
                        for i in range(0,4):
                            if inputnum[i] == answer[i]:
                                right_num_right_place += 1
                                tempinput.remove(answer[i])
                                tempanswer.remove(answer[i])
                        if len(tempinput) > 0:
                            for num in tempinput:
                                if num in tempanswer:
                                    right_num_wrong_place += 1
                        guessnum += 1
                        if right_num_right_place == 4:
                            playtimes += 1
                            os.remove("record.txt")
                            self.savehighrecord(username,playtimes,guessnum)
                            return basehtml + """
                            <body>
                            <div id="smcontainer">
                                <p>You got it! The right answer is %s.You guessed %s time(s).</p>
                                <a href="/index">Restart</a>
                            </div>
                            </body>
                            </html>
                            """ %(str(answer),str(guessnum))
                        elif guessnum < 12:
                            self.writefile(guessnum,userinput,right_num_right_place,right_num_wrong_place)
                            self.saverecord(guessnum,answer)
                            message = "Sorry, you are wrong. Let me give you some hints: %s right number(s) in right place, %s right number(s) in wrong place. You still have %s chances." %(str(right_num_right_place),str(right_num_wrong_place),str(12-guessnum))
                        else:
                            playtimes += 1
                            guessnum += 1
                            os.remove("record.txt")
                            self.savehighrecord(username,playtimes,guessnum)
                            return basehtml + """
                            <body>
                            <div id="smcontainer">
                                <p>Sorry, you used up your chances.</p>
                                <p>The right answer is %s.</p>
                                <a href="/index">Restart</a>
                            </div>
                            </body>
                            </html>
                            """ %str(answer)
                except ValueError:
                    message = "Sorry, you must enter four integers."
        else:
            message = "Please enter 4 integers."
        if os.path.isfile("record.txt"):
            record = self.readfile("record.txt")
            message += record
        return basehtml + """
        <body>
        <div id="largecontainer">
            <form method="get" action="/result">
                <p>Please enter 4 integers in range 1 to 6:</p>
                <p>(do not use space or comma to seperate those integers):</p>
                <input type="text" name="text" id="text" placeholder="e.g. 1234">
                <input type="submit" value="Guess">
                <a href="/index" id="restart">Restart</a>
            </form>
            <p>%s</p>
            <a href="/highrecord">My Highrecord</a>
        </div>
        </body>
        </html>
        """ %(message)

    index.exposed = True
    result.exposed = True
    highrecord.exposed = True

my_app = MyApp()
if __name__ == '__main__':
    conf = {
        '/': {
            'tools.staticdir.root': os.path.abspath(os.getcwd()),
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './',
            'tools.sessions.on': True,
            'tools.sessions.storage_path': os.path.abspath(os.getcwd()),
            'tools.sessions.timeout': 60,
        },
    }
    cherrypy.quickstart(my_app, '/', conf)
