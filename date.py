def find_cent_doom(year):
    """
    Find what the doomsday is for that century
    :param year: int: Which year (century to check)
    :return: String: Weekday for doomsday
    """
    doomsday_cents = ["Sunday", "Friday", "Wednesday", "Tuesday"]
    return doomsday_cents[(int(str(year)[:2]) - 17) % 4]


def is_leap_year(year):
    """
    Find out if a year is a leap year
    :param year: int
    :return: bool
    """
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def find_doomsday(year):
    """
    Find doomsday for a certain year
    Number of years after century + number of leap year = Days after century dooms day
    :param year: int: year to find doomsday for
    :return: String: weekday for doomsday
    """
    week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    base_doom = find_cent_doom(year)
    base_doom_num = week.index(base_doom)

    century = int(str(year)[:2] + "00")

    leaps = (year - century) // 4

    dooms_day_final_num = (year - century + leaps + base_doom_num) % 7

    dooms_day_final = week[dooms_day_final_num]

    return dooms_day_final


def find_week_day(date):
    """
    Find weekday of a certain date
    :param date: String what date to find weekday for DD/MM
    :param year: int year of the date
    :return: String: weekday for date
    """
    year = int(date.split("-")[0])
    date = f"{date.split('-')[2]}/{int(date.split('-')[1])}"  # int to get rid of leading 0's
    # (4/1 leap year)
    # (29/2 leap year)
    leap = is_leap_year(year)

    week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    doomsdays = ["4/1" if leap else "3/1", "29/2" if leap else "28/2", "14/3", "4/4", "9/5", "6/6", "11/7", "8/8",
                 "5/9", "10/10", "7/11", "12/12"]

    # Weekday for doomsday
    doomsday = find_doomsday(year)

    day, month = date.split("/")
    day = int(day)
    month = int(month)

    # Find doomsday for that month
    closest_doom = doomsdays[month - 1]

    # Number of days from date to doomsday
    diff = day - int(closest_doom.split("/")[0])

    # Return weekday from doomsday to date
    return week[(week.index(doomsday) + diff) % 7]

