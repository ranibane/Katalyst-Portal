from flask import Flask, render_template, request, redirect, url_for,session
from flask_sqlalchemy import SQLAlchemy
from io import TextIOWrapper
import csv, random, string, sqlite3, boto3, datetime, os,qrcode, cv2
from threading import Thread
from apscheduler.schedulers.blocking import BlockingScheduler
from werkzeug.utils import secure_filename
from pyzbar.pyzbar import decode
app = Flask(__name__)

app.secret_key = 'somesecretkeythatonlyishouldknowonly'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///KDatabase.db'
db = SQLAlchemy(app)
app.config['IMAGE_FOLDER'] = ""

#-------------------------Create SNS Topic----------------------------------------#
year1 = None
year2 = None
year3 = None
year4 = None

def create_topic():
    global year1, year2, year3, year4
    sns = boto3.resource("sns", aws_access_key_id="",
                    aws_secret_access_key= "")
    year1 = sns.create_topic(Name="year1")
    year2 = sns.create_topic(Name="year2")
    year3 = sns.create_topic(Name="year3")
    year4 = sns.create_topic(Name="year4")

#----------------------------Student Class-------------------------------------------#
class Student(db.Model):
    Id = db.Column(db.Integer, primary_key=True)
    UID = db.Column(db.Integer, unique=True)
    Fname = db.Column(db.String(30))
    Mname = db.Column(db.String(30))
    Lname = db.Column(db.String(30))
    EmailId = db.Column(db.String(120), unique=True)
    DOB = db.Column(db.String(30))
    College = db.Column(db.String(30))
    Year = db.Column(db.Integer)
    BankName = db.Column(db.String(30))
    AccountNo = db.Column(db.Integer)
    IFSCode = db.Column(db.String(30))
    Branch = db.Column(db.String(30))
    AccessKey = db.Column(db.String(30))

@app.route("/StudentHomePage")
def StudentHomePage():
    return render_template("StudentHomePage.html")

@app.route("/AddStudent")
def AddStudent():
    return render_template("AddStudent.html")

@app.route("/Student")
def Student():
    connection = sqlite3.connect('KDatabase.db')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM Student;')
    return render_template("StudentData.html", rows=cursor.fetchall())

@app.route("/uploadStudentData", methods=['POST',"GET"])
def uploadStudentData():
    if request.method == 'POST':
        csv_file = request.files['file']
        csv_file = TextIOWrapper(csv_file, encoding='utf-8')
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader)
        for row in csv_reader:
            sample = "".join(random.choices(string.ascii_lowercase, k=10))
            sample = sample+(str(random.randint(1000, 9000)))
            # sample = append_timestamp(sample)
            # passcode = generate_password_hash(sample)
            connection = sqlite3.connect('KDatabase.db')
            cursorForInsert = connection.cursor()
            cursorForInsert.execute(
                "INSERT into Student (UID, Fname, Mname, Lname, EmailId, DOB, College, Year, BankName, AccountNo, IFSCode, Branch, AccessKey) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?,?);", [row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10],row[11],sample])
            connection.commit()
        return redirect(url_for('uploadStudentData'))
    return '''<html>
            <head>
                <script>
                    alert("Students added successfully!!");
                    window.location.href = "http://127.0.0.1:5000/AddStudent";
                </script>
            <head>
        <html>
        '''

@app.route('/firstYearStudents')
def firstYearStudents():
    connection = sqlite3.connect('KDatabase.db')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM Student where Year == 1;')
    return render_template("StudentData.html", rows=cursor.fetchall(), Year = 1)

@app.route('/secondYearStudents')
def secondYearStudents():
    connection = sqlite3.connect('KDatabase.db')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM Student where Year == 2;')
    return render_template("StudentData.html", rows=cursor.fetchall(), Year = 2)

@app.route('/thirdYearStudents')
def thirdYearStudents():
    connection = sqlite3.connect('KDatabase.db')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM Student where Year == 3;')
    return render_template("StudentData.html", rows=cursor.fetchall(), Year = 3)

@app.route('/fourthYearStudents')
def fourthYearStudents():
    connection = sqlite3.connect('KDatabase.db')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM Student where Year == 4;')
    return render_template("StudentData.html", rows=cursor.fetchall(), Year = 4)

@app.route("/StudentKatAlert")
def StudentKatAlert():
    return render_template("StudentKatAlert.html")
    
#----------------------------Training Class-------------------------------------------#
class Training(db.Model):
    Id = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(30))
    Professor = db.Column(db.String(30))
    Link = db.Column(db.String(30))
    Date = db.Column(db.String(30))
    Time = db.Column(db.Integer)
    Year = db.Column(db.Integer)

@app.route("/AddTraining", methods = ['POST'])
def AddTraining():
    connection = sqlite3.connect('KDatabase.db')
    cursor = connection.cursor()
    if request.method == 'POST':
        connection = sqlite3.connect('KDatabase.db')
        cursorForInsert = connection.cursor()
        name = request.form['name']
        professor = request.form['professor']
        link = request.form['link']
        date = request.form['date']
        time = request.form['time']
        year = request.form['year']
        training = Training(Name = name, Professor=professor, Link=link, Date=date, Time=time, Year=year)
        db.session.add(training)
        db.session.commit()
        db.session.close()
        create_topic()
        message = "Katalyst Training Details: \nName: "+name+ "\nProfessor: "+professor+ "\nLink: "+link+ "\nDate: "+str(date)+ "\nTime: "+time+ "\nYear: "+year
        if year == "1":
            response = year1.publish(Message=message)
            trainingscheduler(name, professor, link, date, time, year)
        elif year == "2":
            response = year2.publish(Message=message)
            trainingscheduler(name, professor, link, date, time, year)
        elif year == "3":
            response = year3.publish(Message=message)
            trainingscheduler(name, professor, link, date, time, year)
        elif year == "4":
            response = year4.publish(Message=message)
            trainingscheduler(name, professor, link, date, time, year)
        else:
            pass
    return render_template('TrainingData.html')

@app.route("/TrainingData")
def TrainingData():
    connection = sqlite3.connect('KDatabase.db')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM Training;')
    return render_template("TrainingData.html", rows=cursor.fetchall())

#----------------------------Forms Class-------------------------------------------#
class Forms(db.Model):
    Id = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(30))
    Link = db.Column(db.String(30))
    Year = db.Column(db.Integer)
    DueDate = db.Column(db.String(30))

@app.route("/AddForm", methods = ['POST'])
def AddForm():
    connection = sqlite3.connect('KDatabase.db')
    cursor = connection.cursor()
    if request.method == 'POST':
        title = request.form['title']
        link = request.form['link']
        duedate = request.form['duedate']
        year = request.form['year']
        forms = Forms(Title = title, Link=link, DueDate=duedate, Year=year)
        db.session.add(forms)
        db.session.commit()
        db.session.close()
        create_topic()
        message = "Katalyst!!\nPlease fill the following form. Title: "+title+  "\nLink: "+link+ "\nDue Date: "+str(duedate)+  "\nYear: "+year
        if year == "1":
            response = year1.publish(Message=message)
            formscheduler(title, link, duedate, year)
        elif year == "2":
            response = year2.publish(Message=message)
            formscheduler(title, link, duedate, year)
        elif year == "3":
            response = year3.publish(Message=message)
            formscheduler(title, link, duedate, year)
        elif year == "4":
            response = year4.publish(Message=message)
            formscheduler(title, link, duedate, year)
        else:
            pass
    return render_template('TrainingData.html')

#----------------------------Admin Class-------------------------------------------#
class Admin(db.Model):
    Id = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(30))
    EmailId = db.Column(db.String(120),unique=True)
    AccessKey = db.Column(db.String(30))

@app.route("/AdminHomePage")
def AdminHomePage():
    return render_template("AdminHomePage.html")

#----------------------------------Login----------------------------#

@app.route("/LandingPage")
def LandingPage():
    return render_template("LandingPage.html")

@app.route("/Login")
def Login():
    return render_template("Login.html")

@app.route("/Authentication", methods=['GET', 'POST'])
def Authentication():
    if request.method == 'POST':
        connection = sqlite3.connect('KDatabase.db')
        cursor1 = connection.cursor()
        cursor2 = connection.cursor()

        EmailId = request.form['emailid']
        AccessKey = request.form['pass']
        sEmailId = None
        aEmailId = None
        aAccessKey = None
        sAccessKey = None
        try:
            data = cursor1.execute(
                'SELECT * FROM Admin WHERE EmailId=?', (EmailId,)).fetchone()
            if data:
                aEmailId=data[2]
                aAccessKey=data[3]

            data = cursor2.execute(
                'SELECT * FROM Student WHERE EmailId=?', (EmailId,)).fetchone()
            if data:
                sEmailId=data[5]
                sAccessKey=data[13]
        finally:
            connection.close()

        if sEmailId == sEmailId and sAccessKey == AccessKey:
            session['UserEmailId'] = sEmailId
            return render_template('StudentHomePage.html')
        elif aEmailId == EmailId and aAccessKey == AccessKey:
            session['AdminEmailId'] = aEmailId
            return render_template('AdminHomePage.html')
        return '''
        <html>
            <head>
                <script>
                    alert("Oops!! Your Email Id or Access Key is Wrong.");
                    window.location.href = "http://127.0.0.1:5000/Login";
                </script>
            <head>
        <html>
        '''
    return "done"

#----------------------------------KatAlert-----------------------------#

@app.route("/AdminKatAlert")
def AdminKatAlert():
    return render_template("AdminKatAlert.html")

@app.route("/AdminEventAlert")
def AdminEventAlert():
    return render_template("AdminEventAlert.html")

@app.route("/AdminFormAlert")
def AdminFormAlert():
    return render_template("AdminFormAlert.html")

@app.route("/AdminTrainingAlert")
def AdminTrainingAlert():
    return render_template("AdminTrainingAlert.html")

@app.route('/MIAlert')
def MIAlert():
    return render_template("MIAlert.html")

#---------------Training SMS----------------------------------#
def trainingalert(name, professor, link, date, time, year):
    global year1, year2, year3, year4
    global oneHourTrainingAlert
    y = int(date[0:4])
    m = int(date[5:7])
    d = int(date[8:])
    date = datetime.date(y,m,d)
    date_of_today = datetime.date.today()
    current_datetime = datetime.datetime.now()
    current_time = current_datetime.strftime("%H:%M:%S")
    hour = int(current_time[0:2])
    message = "Katalyst Training Reminder: \nName: "+name+ "\nProfessor: "+professor+ "\nLink: "+link+ "\nDate: "+str(date)+ "\nTime: "+time+ "\nYear: "+year
    if (date == date_of_today and hour == current_datetime.hour):
        if(year == "1"):
            response = year1.publish(Message=message)
            oneHourTrainingAlert.remove_job(name)
        elif(year == "2"):
            response = year2.publish(Message=message)
            oneHourTrainingAlert.remove_job(name)
        elif(year == "3"):
            response = year3.publish(Message=message)
            oneHourTrainingAlert.remove_job(name)
        elif(year == "4"):
            response = year4.publish(Message=message)
            oneHourTrainingAlert.remove_job(name)
        else:
            pass
    else:
        pass
    return "Alerted"

#---------------Training Scheduler----------------------------------#
oneHourTrainingAlert = BlockingScheduler()
def trainingscheduler(name, professor, link, date, time, year):
    global oneHourTrainingAlert
    oneHourTrainingAlert = BlockingScheduler()
    oneHourTrainingAlert.add_job(trainingalert, 'interval', [name, professor, link, date, time, year], seconds=10, id=name)
    oneHourTrainingAlert.start()  

#---------------Form SMS----------------------------------------#
def formalert(title, link, duedate, year):
    global year1, year2, year3, year4
    global oneDayFormAlert
    y = int(duedate[0:4])
    m = int(duedate[5:7])
    d = int(duedate[8:])
    date = datetime.date(y,m,d)
    date_of_today = datetime.date.today()
    current_datetime = datetime.datetime.now()
    current_time = current_datetime.strftime("%H:%M:%S")
    hour = int(current_time[0:2])
    if (date == date_of_today and hour == current_datetime.hour):
        message = "Reminder from Katalyst!!\nPlease fill the following form. Title: "+title+  "\nLink: "+link+ "\nDue Date: "+str(duedate)+  "\nYear: "+year
        if(year == "1"):
            response = year1.publish(Message=message)
            oneDayFormAlert.remove_job(title)
        elif(year == "2"):
            response = year2.publish(Message=message)
            oneDayFormAlert.remove_job(title)
        elif(year == "3"):
            response = year3.publish(Message=message)
            oneDayFormAlert.remove_job(title)
        elif(year == "4"):
            response = year4.publish(Message=message)
            oneDayFormAlert.remove_job(title)
        else:
            pass
    else:
        pass
    return "Alerted"

#---------------Form Scheduler----------------------------------#
oneDayFormAlert = BlockingScheduler()
def formscheduler(title, link, duedate, year):
    global oneDayFormAlert
    oneDayFormAlert.add_job(formalert, 'interval', [title, link, duedate, year], seconds=10, id=title)
    oneDayFormAlert.start()  
    return "done"

#----------------------------------------Annoucements----------------------------------#
@app.route("/Announcement")
def Announcement():
    return render_template("Announcements.html")

@app.route('/AddAnnouncement')
def AddAnnouncement():
    return render_template("AddAnnouncement.html")

#---------------------------------NewsLetter------------------------------------#

@app.route("/NewsLetter")
def NewsLetter():
    connection = sqlite3.connect('KDatabase.db')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM NewsLetter;')
    return render_template("NewsLetter.html", rows=cursor.fetchall())

@app.route("/AddNewsLetter")
def AddNewsLetter():
    return render_template("AddNewsLetter.html")

@app.route("/uploadNewsLetter", methods = ["POST","GET"])
def uploadNewsLetter():
    s3 = boto3.client('s3', aws_access_key_id="",
                      aws_secret_access_key="")
    
    if request.method == 'POST':
        pdf = request.files['file']
        content_type = request.mimetype
        file_name = secure_filename(pdf.filename)
        s3.put_object(Body=pdf,Bucket="newsletterpdfhere",Key=file_name,ContentType=content_type)
        link = "https://newsletterpdfhere.s3.ap-south-1.amazonaws.com/"+file_name
        connection = sqlite3.connect('KDatabase.db')
        cursorForInsert = connection.cursor()
        cursorForInsert.execute(
                "INSERT into NewsLetter (Pdf) values (?);", [link])
        connection.commit()
        
    return '''
        <html>
            <head>
                <script>
                    alert("NewsLetter Added");
                    window.location.href = "http://127.0.0.1:5000/AdminHomePage";
                </script>
            <head>
        <html>
        '''

#-------------Student Payout-----------------------------------#
@app.route('/StudentPayout')
def StudentPayout():
    connection = sqlite3.connect('KDatabase.db')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM Student')
    return render_template('StudentPayout.html',rows=cursor.fetchall(),Email = session['UserEmailId'])


#------------Admin Payout--------------------------------------#
@app.route('/AddPayout')
def AddPayout():
    return render_template('AddPayout.html')

@app.route('/firstYearStudentsPayoutData')
def firstYearStudentsPayoutData():
    connection = sqlite3.connect('KDatabase.db')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM Student where Year == 1;')
    return render_template("PayoutData.html", rows=cursor.fetchall())

@app.route('/secondYearStudentsPayoutData')
def secondYearStudentsPayoutData():
    connection = sqlite3.connect('KDatabase.db')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM Student where Year == 2;')
    return render_template("PayoutData.html", rows=cursor.fetchall())

@app.route('/thirdYearStudentsPayoutData')
def thirdYearStudentsPayoutData():
    connection = sqlite3.connect('KDatabase.db')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM Student where Year == 3;')
    return render_template("PayoutData.html", rows=cursor.fetchall())

@app.route('/fourthYearStudentsPayoutData')
def fourthYearStudentsPayoutData():
    connection = sqlite3.connect('KDatabase.db')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM Student where Year == 4;')
    return render_template("PayoutData.html", rows=cursor.fetchall())

@app.route('/UploadPayouts', methods=['GET', 'POST'])
def UploadPayouts():
    if request.method == "POST":
        connection = sqlite3.connect('KDatabase.db')
        cursorForInsert = connection.cursor()
        csv_file = request.files['file']
        csv_file = TextIOWrapper(csv_file, encoding='utf-8')
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader)
        for row in csv_reader:
            print(row[0])
            cursorForInsert.execute(
                    "UPDATE Student SET payout1 = (?), amount1 = (?), payout2 = (?), amount2 = (?),payout3 = (?), amount3 = (?),payout4 = (?), amount4 = (?),payout5 = (?), amount5 = (?),payout6 = (?), amount6 = (?),payout7 = (?), amount7 = (?),payout8 = (?), amount8 = (?) WHERE UID = (?);", (row[4], row[5], row[6],row[7], row[8], row[9],row[10],row[11],row[12],row[13], row[14],row[15],row[16],row[17],row[18],row[19],row[0]))
            connection.commit()
        return redirect(url_for('UploadPayouts'))
        
    return '''<html>
            <head>
                <script>
                    alert("Payout added successfully!!");
                    window.location.href = "http://127.0.0.1:5000/AddPayout";
                </script>
            <head>
        <html>
        '''

#-----------------------Katalyst Attendance------------------------------#
@app.route('/')
def a():
    return "goto /attendance-admin.html" #Home - page admin

@app.route('/attendance-admin.html', methods=["GET", "POST"])
def QR_generate():
    if request.method == "POST":
        training_name = request.form.get("training_name")
        print(training_name)
        qr = qrcode.QRCode(
            version=1,
            box_size=10,
            border=5,
        )
        date = datetime.datetime.now()
        data = training_name + str(date) # this is the data being transformed to qr, so must be saved to db and will be retrieved while scanning to compare
        print(data)
        qr.add_data(data)
        qr.make(fit = True)
        qr_img = qr.make_image(fill="black", back_color = "white")
        qr_img.save("static/IMAGE_FOLDER/qr_2.png") # to save qr code image
        #direct = app.config['IMAGE_FOLDER'] + "qr_2.png"  # the directory where images are saved, here I've given it statically
        return render_template("attendance-admin.html", QR_code = "/static/IMAGE_FOLDER/qr_2.png", training_name = training_name )
    return render_template("attendance-admin.html")

@app.route('/s')
def s():
    return "goto /attendance-student.html" #home page - student

@app.route('/attendance-student.html',  methods=["GET", "POST"])
def QR_scanner():
    flag = -1
    if request.method == "POST":

        actual_data = b'Interview Prep2021-06-28 11:21:32.347034' # load the data from db (the date + training_name )
        capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)

        while True:
            try:
                _, frame = capture.read()
                decoded_qr = decode(frame)
                data = decoded_qr[0][0]
                if data == actual_data: # here we compare the scanned data and the data reterieved from db
                    print("Scanned successfully")
                    flag = 1
                    print(f"Decoded data = {decoded_qr[0][0]}")
                    break
                else:
                    print("Check QR Code") # if the shown QR isn't correct (not for this training) so check QR code
                    print(f"Decoded data = {decoded_qr[0][0]}")
                    flag = 0
                    break
            except:
                pass

            cv2.imshow('QR Code Scanner', frame)
            key = cv2.waitKey(1)

        cv2.destroyAllWindows()
    if flag ==1 :
        return render_template("attendance-student.html", QR_scan_status = "Scanned successfully")
    elif flag==0 :
        return render_template("attendance-student.html", QR_scan_status="Check QR Code")
    else:
        return render_template("attendance-student.html", QR_scan_status="Waiting to scan QR Code") # when teh qr is not processed yet

if __name__ == "__main__":
    app.run()