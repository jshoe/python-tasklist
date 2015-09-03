from colored import fg, bg, attr
from datetime import date, datetime, timedelta
from operator import itemgetter, attrgetter
from pprint import pprint
import calendar
import json
import os
import re

class TaskList:
    """A todo list of user Tasks."""

    def __init__(self, data):
        self.source = data
        self.lst = sorted(data['tasks'], key=itemgetter('start_date', 
                                                        'category'))
        self.categories = sorted(data['categories'])
        task_id = 1
        for i in range(len(self.lst)):
            self.lst[i] = Task(task_id, self.lst[i])
            task_id += 1

    def reallocate_task_ids(self):
        """Reallocate the task IDs so they show up in order to the user."""
        task_id = 1
        self.lst = sorted(self.lst, key=attrgetter('start_date', 'category'))
        for i in range(len(self.lst)):
            self.lst[i].task_id = task_id
            task_id += 1

    def dates_with_items(self):
        """Return all the dates that have any tasks to do on them."""
        dates = sorted(set(t.start_date for t in self.lst))
        return dates

    def tasks_on_date(self, date):
        """Return all the tasks to do on a given date."""
        tasks = list(filter(lambda t: t.start_date == date, self.lst))
        return tasks

    def categories_on_date(self, date):
        """Return all the categories with tasks in them on a given date."""
        categories = sorted(set(t.category for t in self.tasks_on_date(date)))
        return categories

    def tasks_by_date_category(self, date, category):
        """Return all the tasks on a given date in a given category."""
        tasks = []
        for t in self.tasks_on_date(date):
            if t.category == category and t.repeat_mode == '':
                tasks.append(t)
        return tasks

    def do_repeat(self, t, date):
        """Return whether or not the Task t should occur on the date."""
        if t.repeat_mode == 'Every':
            if t.repeat_interval == '1 day':
                return True
        return False

    def repeat_tasks_by_date_category(self, date, category):
        """Return repeat tasks scheduled on a given date in a given category."""
        #tasks = [t for t in self.tasks_on_date(date) if t.category == ]
        tasks = []
        for t in self.tasks_on_date(date):
            if t.category == category and self.do_repeat(t, date):
                tasks.append(t)
        return tasks

    def task_count(self, date):
        """Return the number of tasks scheduled on a given date."""
        return len(self.tasks_on_date(date))

    def print_task_line(self, t):
        """Print a Task readout for the user."""
        box_color = bg(20)
        repeat_color = bg(28)
        reset = attr('reset')
        if t.repeat_mode == '':
            print("    {0}[{1}]{2} {3}".format(box_color, t.task_id, reset, t.body)) 
        else:
            print("    {0}[{1}]{2} {3}[Repeat]{4} {5}".format(box_color, t.task_id, reset, repeat_color, reset, t.body)) 

    def print_date_header(self, d):
        """Print a date header for the user."""
        count = self.task_count(d)
        today = datetime.today().date()
        if d.date() < today and count == 0: return # Hide old 0-task days
        print()
        weekday = d.strftime('%A')
        rest = d.strftime(', %B %-d:')
        rest_ln = "{:19s} ({:1s} tasks)".format(rest, str(count)) 
        both = weekday + rest
        both_ln = "{:25s} ({:1s} tasks)".format(both, str(count))
        bg_code = 0
        if d.date() == today: bg_code = 5
        if weekday == 'Sunday':
            printc(weekday, 11, 25, False)
            printc(rest_ln, 11, bg_code)
        else:
            printc(both_ln, 11, bg_code)

    def print_tasks_for_date(self, date):
        """Print a formatted list of all tasks on a given date."""
        day_categories = self.categories_on_date(date)
        self.print_date_header(date)
        for c in day_categories:
            tasks = self.tasks_by_date_category(date, c)
            #repeat_tasks = self.repeat_tasks_by_date_category(date, c)
            print("  {0}:".format(c))
            #for t in repeat_tasks:
            #    self.print_task_line(t)
            for t in tasks:
                self.print_task_line(t)
                if t is tasks[-1] and c is not day_categories[-1]:
                    print()

    def first_day_ever(self):
        """Returns the very first date with an active task in the database."""
        return sorted(t.start_date for t in self.lst)[0]

    def last_day_ever(self):
        """Returns the very last date with an active task in the database."""
        return sorted(t.start_date for t in self.lst)[-1]

    def print_all_tasks(self):
        """Print a formatted list by date and category of all tasks."""
        d = self.first_day_ever()
        dt = timedelta(days=1)

        while d <= self.last_day_ever():
            self.print_tasks_for_date(d)
            d += dt
        print()

    def write_to_file(self):
        """Writes this TaskList to a data file."""
        data = self.source
        data['categories'] = self.categories
        data['tasks'] = []
        for t in self.lst:
            rep = {}
            rep["body"] = t.body
            rep["category"] = t.category
            rep["repeat_mode"] = t.repeat_mode
            rep["repeat_interval"] = t.repeat_interval
            rep["start_date"] = date2str(t.start_date)
            data['tasks'].append(rep)

        open("user_data.txt", "a")
        with open("user_data.txt", 'w') as outfile:
            json.dump(data, outfile, indent=2, sort_keys=True)

    def task_exists(self, task_id):
        """Return if task exists with the given ID."""
        for t in self.lst:
            if t.task_id == task_id:
                return True
        return False

    def get_task_from_id(self, task_id):
        """Return Task object from given labeled ID."""
        for t in self.lst:
            if t.task_id == task_id:
                return t

    def delete_task(self, args):
        """Delete a task with the labeled ID number."""
        task_id = int(args[0])
        if not self.task_exists(task_id):
            print("Error: No task is labeled #{0}.".format(str(task_id)))
        else:
            print("removed!")
            self.lst.remove(self.get_task_from_id(task_id))

    def is_valid_date(self, d):
        """Returns whether or not the target date is valid for move_task()."""
        n = datetime.now()
        cur_max = calendar.monthrange(n.year, n.month)[1]
        next_max = calendar.monthrange(n.year, n.month+1)[1]
        if d < 1:
            return False
        elif d > cur_max and d > next_max:
            return False
        return True

    def move_task(self, args):
        """
        Move a task to a new date in the current or next month.
        Ex: 4m20 means move task labeled #4 to the 20th of the current month.

        If current date is later than target, then task goes to next month.
        Ex: If today is July 21st, 4m20 moves task #4 to August 20th.
        """
        task_id = int(args[0])
        date = args[1]
        try:
            date = int(date)
        except ValueError:
            today = (date == 't')
            weekday = self.match_weekday(date)
            if today:
                date = datetime.now().day
            elif weekday:
                date = weekday
        if not self.task_exists(task_id):
            print("Error: No task is labeled #{0}.".format(str(task_id)))
        elif not self.is_valid_date(date):
            print("Error: Date {0} is not valid.".format(str(date)))
        else:
            self.get_task_from_id(task_id).move_to(date)

    def match_category(self, substr):
        """Returns a category based on a user substring."""
        for c in self.source['categories']:
            if substr in c:
                print(c)
                return c
        self.add_category(substr)
        return substr

    def add_category(self, name):
        """Add a category to the TaskList."""
        self.categories.append(name)
    
    def match_weekday(self, sub, mode=''):
        """
        Match a substring to a weekday name and return a date.
        Ex: 'Sun' yields the int date for the next upcoming Sunday.
        Ex: If today is Sunday, 'Sun' yields the next upcoming Sunday date.
        """
        weekdays = [("Sunday", 6), ("Monday", 0), ("Tuesday", 1),
                    ("Wednesday", 2), ("Thursday", 3), ("Friday", 4), 
                    ("Saturday", 5)]
        match = next(w for w in weekdays if sub in w[0])
        if match:
            d = datetime.now()
            dt = timedelta(days=1)
            d += dt
            while d.weekday() != match[1]:
                d += dt
            result = d.day
            if mode == 'full':
                result = "{0}-{1}-{2}".format(d.year, d.month, d.day)
            return result

    def match_date(self, day):
        """Match different date abbreviations to a full date string."""
        n = datetime.now()
        try:
            day = int(day)
            if not self.is_valid_date(day):
                print("Error: Date {0} is not valid.".format(str(day)))
                return
            m = n.month
            if day < n.day:
                m += 1
            result = "{0}-{1}-{2}".format(n.year, m, day)
        except ValueError:
            today = (day == 't')
            weekday = self.match_weekday(day, 'full')
            if today:
                date = n.day
                m = n.month
                result = "{0}-{1}-{2}".format(n.year, m, date)
            elif weekday:
                return weekday
            else:
                print("Error: Date {0} is not valid.".format(str(day)))
                return
        return result

    def new_task(self, args):
        """
        Make a new task in the database.
        """
        data = {}
        data['body'] = args[0] + "."
        data['category'] = self.match_category(args[1])
        data['start_date'] = self.match_date(args[2])
        if not data['start_date']:
            return
        self.lst.append(Task(0, data))

class Task:
    """Tasks that the user wants to complete."""

    def __init__(self, task_id, data):
        self.body = data['body']
        self.category = data['category']
        self.repeat_mode = data.get('repeat_mode', '')
        self.repeat_interval = data.get('repeat_interval', '')
        self.start_date = str2date(data['start_date'])
        self.task_id = task_id

    def move_to(self, date):
        """Move this task to the new date."""
        n = datetime.now()
        s = self.start_date
        if date >= n.day:
            self.start_date = datetime(n.year, n.month, date)
        elif date < n.day:
            self.start_date = datetime(n.year, n.month+1, date)

def str2date(string):
    """Convert a string formatted like 2015-07-21 to a datetime object."""
    return datetime.strptime(string, "%Y-%m-%d")

def date2str(date):
    """Convert a datetime object into a string formatted like 2015-07-21."""
    return date.strftime("%Y-%m-%d")

def printc(to_print, fg_code=15, bg_code=0, end_line=True):
    print(fg(fg_code) + bg(bg_code) + to_print + attr('reset'), end="")
    if end_line: print()

def print_month_cals():
    """Print a calendar of the current and next month for the user."""
    print()
    c = calendar.TextCalendar(calendar.SUNDAY)
    n = datetime.now()
    c.prmonth(n.year, n.month)
    print()
    c.prmonth(n.year, n.month + 1)
    print()

def invalid_input():
    print("Invalid input. Please try again.")
    return

def input_prompt(t):
    """Receive and interpret commands from the user."""
    def write(args):
        print("Saving to file... ", end="")
        t.write_to_file()
        print("done!")

    def quit(args):
        u = input("Save changes to database?\n[Y]es, (N)o, (C)ancel: ")
        u = u.lower()
        if u == "y":
            return write_quit('')
        elif u == "n":
            print("Exiting without saving...\n")
            return "quit"
        elif u == "c":
            print("...Quit aborted.")
            return
        else:
            print("Invalid input. Quit aborted.")

    def write_quit(args):
        t.write_to_file()
        print("Save successful. Exiting...\n")
        return "quit"

    options = {
        'w': write,
        'q': quit,
        'wq': write_quit
    }

    args = ""
    u = input(":")
    move_task = re.match('(\d+)m\s*(\d+|\w+)$', u)
    new_task = re.match('n (.*); (.*); (\d+|\w+)$', u)
    delete_task = re.match('(\d+)d$', u)

    if move_task:
        t.move_task(move_task.groups())
        return "reload"
    elif new_task:
        t.new_task(new_task.groups())
        return "reload"
    elif delete_task:
        t.delete_task(delete_task.groups())
        return "reload"
    else:
        try:
            return options[u](args)
        except KeyError:
            print("Invalid input. Please try again.")

def print_divide():
    print("\n==========================================================================\n")

def show_main_screen(t):
    """Show main screen of tasks to the user."""
    os.system('clear')
    t.reallocate_task_ids()
    t.print_all_tasks()
    print_month_cals()
    run = True
    while run:
        ret = input_prompt(t)
        if ret == "reload":
            print_divide()
            show_main_screen(t)
            break
        elif ret == "quit":
            break

def main():
    data = json.load(open('user_data.txt'))
    t = TaskList(data)
    show_main_screen(t)

main()
