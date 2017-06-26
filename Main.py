import getpass
from edsby import Edsby
from time import sleep
from datetime import datetime, timedelta
from configparser import ConfigParser
import sys
import os

# ANSI Color Definitions
HEADER = '\033[95m'
OK_BLUE = '\033[94m'
OK_GREEN = '\033[92m'
WARNING = '\033[93m'
WHITE = '\033[37m'
CYAN = '\033[36m'
RED = '\033[31m'
MAGENTA = '\033[35m'
YELLOW = '\033[33m'
FAIL = '\033[91m'
END_C = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'
GRAY = '\033[30m'

# Checks if environment supports color - from django source code
plat = sys.platform
supported_platform = plat != 'Pocket PC' and (plat != 'win32' or 'ANSICON' in os.environ)
is_a_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
if not supported_platform or not is_a_tty:
    HEADER = OK_GREEN = OK_BLUE = WARNING = WHITE = CYAN = RED = MAGENTA = YELLOW = FAIL = END_C = BOLD = UNDERLINE = GRAY = ""


# Prints lines slower, for added effect
def printd(string, end='\n'):
    sleep(.05)
    print(string, end=end)


# Converts dates to local time
def convertDate(dateIn):
    if len(dateIn) > 10:
        newDate = datetime.strptime(dateIn, '%Y-%m-%d %H:%M:%S') - timedelta(hours=4)
    elif len(dateIn) <= 8:
        newDate = datetime.strptime(dateIn, '%Y%m%d')
    else:
        newDate = datetime.strptime(dateIn, '%Y-%m-%d')
    return newDate


# Method for 'loading' text that disappears
def loading(message):
    printd(YELLOW + "\n  " + message + WHITE, '\r')


def loaded(message):
    clean = " "
    for ii in range(len(message)):
        clean += "   "
    printd(clean, '\r')

# Read config file
config = ConfigParser()
config.read("testConfig.ini")
rHOST = config.get('auth', 'host')
rUSERNAME = config.get('auth', 'username')
rPASSWORD = config.get('auth', 'password')


# Main CLI loop
while True:
    # Confirm auth method
    HOST = input("\nPress enter to sign in with credentials from the config file ("+rUSERNAME+"@"+rHOST+").\nOtherwise, enter the host prefix for your edsby instance (*.edsby.com): ")
    if HOST != "":
        HOST += ".edsby.com"
        USERNAME = input("Username: ")
        PASSWORD = getpass.getpass()
    else:
        HOST = rHOST
        USERNAME = rUSERNAME
        PASSWORD = rPASSWORD

    printd(BOLD + HEADER + "–----------------------------------------------------------------------------------------------------------------------")
    edsby = Edsby(host=HOST)

    # Attempt login
    printd(HEADER + "Logging " + USERNAME + " into " + HOST + "..." + END_C)
    for i in range(1, 10):
        result = False
        try:
            result = edsby.login(username=USERNAME, password=PASSWORD)
        except:
            pass
        if result:
            printd(OK_GREEN + "Logged in (" + str(i) + " attempts)\n" + END_C)
            break
        sleep(2)

    # Logged in CLI loop
    while True:
        action = ""
        printd(UNDERLINE + WHITE + "Choose an action:" + END_C)
        printd(WHITE + "\t0: Logout")
        printd("\t1: Get class averages")
        printd("\t2: Get class assignments")
        printd("\t3: Get schedule")
        while True:
            action = input("Action: ")
            if action in ["0", "1", "2", "3"]:
                break
            else:
                printd("Invalid action, try again.")

        # Action 0 - exit
        if action == "0":
            loading("Logging out...")
            edsby.logout()
            sleep(.5)
            loaded("Logging out...")
            printd("Logged out.")
            break

        # Action 1 - class averages
        if action == "1":
            loading("Loading class averages...")
            courses = edsby.getAllClassAverages()
            loaded("Loading class averages...")
            printd(WHITE + UNDERLINE + "Grades summary:" + END_C)
            for entry in courses:
                printd(CYAN + '\t' + courses[entry]['human_name'] + ": " + WHITE + str(courses[entry]['average']) + "%")
            printd("")

        # Action 2 - class assignments
        if action == "2":
            action2 = ""
            loading("Loading class list...")
            courses = edsby.getAllClasses()
            loaded("Loading class list...")
            numberedCourses = [0]
            i = 1
            for course in courses:
                numberedCourses.append(course)
                i += 1
            printd(WHITE + UNDERLINE + "Choose an option to get class assignments for:" + END_C)
            printd("\t" + WHITE + "0:" + CYAN + " All classes")
            i = 1
            for entry in courses:
                courses[entry]['index'] = str(i)
                printd("\t" + WHITE + str(i) + ": " + CYAN + courses[entry]['human_name'])
                i += 1
            while True:
                action2 = input(WHITE + "Option: ")
                try:
                    if int(action2) in range(0, i):
                        break
                    else:
                        printd(WHITE + "Invalid option, try again.")
                except ValueError:
                    printd(WHITE + "Invalid option, try again.")
            ASSIGNMENTS = {}

            if action2 == "0":
                loading("Loading assignments from all classes...")
            else:
                loading("Loading assignments from " + str(courses[numberedCourses[int(action2)]]['human_name']) + "...")

            for course in courses:
                if action2 != "0" and course != numberedCourses[int(action2)]:
                    continue
                assignmentsByDate = {}
                courseNID = course
                courseRID = courses[course]['rid']
                average = edsby.getClassAverage(courseNID)
                courses[course]['average'] = average
                assignmentSummary = edsby.getClassAssignmentList(courseNID, courseRID)
                for entry in assignmentSummary['assignments']:
                    assignment = assignmentSummary['assignments'][entry]
                    assignmentsByDate[assignment['date'] + str(assignment['nid'])] = assignment
                    score = assignment['score']
                    outof = assignment['columns']
                    date = assignment['date'][:9]
                    try:
                        if assignment['scheme'] == "gs_outof":
                            try:
                                percent = float(score) / float(outof)*100.0
                                assignmentsByDate[assignment['date'] + str(assignment['nid'])]['info'] = str(
                                    WHITE + "\t" + date + " " + CYAN + assignment['name'] + ": " + WHITE + str(
                                        score) + "/" + str(outof) + " (" + str(format(round(percent, 2)), ) + "%)")
                            except:
                                percent = "--"
                                assignmentsByDate[assignment['date'] + str(assignment['nid'])]['info'] = str(
                                    WHITE + "\t" + date + " " + CYAN + assignment['name'] + ": " + WHITE + str(
                                        score) + "/" + str(outof) + " (--%)")
                        elif assignment['scheme'] == "gs_kica":
                            if len(assignment['weighting']) != 0:
                                percent = 0
                                weightSum = 0
                                for category in assignment['score']:
                                    percent += ((assignment['weighting'][category]) * (float(assignment['score'][category])/float(assignment['columns'][category])))
                                    weightSum += assignment['weighting'][category]
                                percent /= weightSum
                                percent *= 100
                            else:
                                percent = "--"
                            assignmentsByDate[assignment['date'] + str(assignment['nid'])]['info'] = (WHITE + "\t" + date + CYAN + " " + assignment['name'] + ":  ")
                            for s in score:
                                assignmentsByDate[assignment['date'] + str(assignment['nid'])]['info'] += (WHITE + s.upper() + ":" + str(score[s]) + "/" + str(outof[s]) + "   ")
                            assignmentsByDate[assignment['date'] + str(assignment['nid'])]['info'] += ("(" + str(round(percent, 2)) + "%)")

                        elif assignment['scheme'] == "gs_4levelplusminus" or assignment['scheme'] == "gs_4level":
                            assignmentsByDate[assignment['date'] + str(assignment['nid'])]['info'] = (WHITE + "\t" + date + " " + CYAN + assignment['name'] + ": " + WHITE + assignment['score'])

                        elif assignment['scheme'] == "gs_yesno":
                            percent = "100" if assignment['score'] == 'yes' else "0"
                            assignmentsByDate[assignment['date'] + str(assignment['nid'])]['info'] = (WHITE + "\t" + date + " " + CYAN + assignment['name'] + ": " + WHITE + assignment['score'].upper() + " (" + percent + "%)")

                    except Exception as e:
                        printd(e)
                        printd(assignment)
                if str(average) == "":
                    percentage = "--"
                else:
                    percentage = str(average)
                ASSIGNMENTS[course] = assignmentsByDate
            if action2 == "0":
                loaded("Loading assignments from all classes...")
                for course in courses:
                    printd(MAGENTA + UNDERLINE + '\nAssignment summary for ' + courses[course]['human_name'] +':' + END_C)
                    for assg in ASSIGNMENTS[course]:
                        printd(ASSIGNMENTS[course][assg]['info'])
                    printd(WHITE + 'Your average in ' + courses[course]['human_name'] + ' is currently ' + str(courses[course]['average']) + '%.')

                    printd("")
            else:
                loaded("Loading assignments from " + str(courses[numberedCourses[int(action2)]]['human_name']) + "...")
                n = int(action2)
                printd(MAGENTA + UNDERLINE + '\nAssignment summary for ' + courses[numberedCourses[n]]['human_name'] +':' + END_C)
                for entry in sorted(ASSIGNMENTS[numberedCourses[n]]):
                    printd("\t" + ASSIGNMENTS[numberedCourses[n]][entry]['info'])
                printd(WHITE + 'Your average in '+courses[numberedCourses[n]]['human_name']+' is currently '+str(average)+'%.\n')

        # Action 3 - schedule
        elif action == "3":
            NONE = (WHITE + "██" + WHITE)
            PRESENT = (OK_GREEN + "██" + WHITE)
            LATE = (YELLOW + "██" + WHITE)
            ABSENT = (RED + "██" + WHITE)
            BLANK = "  "
            attendance = {-1:NONE, 0:PRESENT, 1:LATE, 2:ABSENT, 3:ABSENT}
            printd(WHITE + "\nPress enter to get today's schedule, or type a date (YYYYMMDD).")
            dateGet = ""
            dateStr = ""
            while True:
                action3 = input(WHITE + "Date: ")
                if action3 == "":
                    dateGet = datetime.today()
                    dateStr = dateGet.strftime('%Y%m%d')
                    break
                elif not (action3.isdigit() and action3.startswith("20") and len(action3)==8):
                    printd("Invalid date, try again.")
                else:
                    dateGet = datetime.strptime(action3, '%Y%m%d')
                    dateStr = action3
                    break

            loading("Loading schedule for " + dateGet.strftime('%A, %B %e, %Y') + "...")
            try:
                schedule = edsby.getSchedule(dateStr)
                loaded("Loading schedule for " + dateGet.strftime('%A, %B %e, %Y') + "...")
            except KeyError:
                loaded("Loading schedule for " + dateGet.strftime('%A, %B %e, %Y') + "...")
                printd(UNDERLINE + "Schedule for " + dateGet.strftime('%A, %B %e, %Y') + ":" + END_C)
                printd(WHITE + "\tNothing scheduled.\n")
                continue

            scheduleOut = {}
            for r in schedule:
                newDate = convertDate(schedule[r]['sdate'])
                if newDate.day != dateGet.day:
                    continue
                scheduleOut[str(newDate) + str((len(schedule[r]['class']) !=  0)) + str(schedule[r]['nid'])] = schedule[r]

            printd(UNDERLINE + "Schedule for " + dateGet.strftime('%A, %B %e, %Y') + ":" + END_C)
            if len(scheduleOut) == 0:
                printd(WHITE + "\tNothing scheduled.\n")
            for s in sorted(scheduleOut):
                printd("\t", '')
                a = BLANK if 'objtype_13' not in scheduleOut[s] else attendance[int(scheduleOut[s]['objtype_13']['attendance'])]
                d = convertDate(scheduleOut[s]['sdate'])
                name = (CYAN + scheduleOut[s]['name'] + WHITE) if len(scheduleOut[s]['class']) == 0 else (YELLOW + scheduleOut[s]['class'] + WHITE)
                if d.strftime('%-I:%M %p') == '12:00 AM':
                    printd("{0} {1:11}{2}".format(a, "", name))
                else:
                    printd("{0} {1:11}{2}".format(a, d.strftime('%-I:%M %p'), name))
            printd("")
    printd('\n')
