import googleapiclient
import auth
from lib import Course, days, ends
import os
from pprint import pprint
from datetime import timedelta
import random
import time


CAL_NAME  = 'kurser' 
TZ        = 'Europe/Stockholm'

SERVICE  = auth.get_service()
CL       = SERVICE.calendarList()
CS       = SERVICE.calendars()
ES       = SERVICE.events()
COLORS   = SERVICE.colors()


def random_number_milliseconds():
    return random.randint(1, 1000)

# ------------------- Calendar functions ---------------------- #

def get_courses_calendar(create_on_None=True):
    cals = CL.list().execute()['items']

    try:
        return next(cal for cal in cals if cal["summary"] == CAL_NAME)
    except StopIteration:
        if create_on_None:
            return set_courses_calendar()

def set_courses_calendar():
    payload = {
        'summary' : CAL_NAME
    }
    return CS.insert(body=payload).execute()

def delete_courses_calendar():
    calendar_id = get_courses_calendar(create_on_None=False)['id']
    return CL.delete(calendarId=calendar_id).execute()


# --------------------- Base event functions --------------------- #

def _set_event(calendar_id, summary, start, end, color_id, **kwargs):
    payload = {
        'summary'    : summary,
        'start'      : {'date': str(start), 'timeZone': TZ},
        'end'        : {'date': str(end + days(1)), 'timeZone': TZ}, # end is exclusive, so we add 1
        'colorId'    : color_id,
    } 
    payload.update(kwargs)

    fails = 0
    sent = False
    while not sent:
        try:
            ES.insert(calendarId=calendar_id, body=payload).execute()
        except googleapiclient.errors.HttpError as e:
            constant_wait = 2 ** fails
            fails += 1
            ms = random_number_milliseconds()
            sleep_for = constant_wait + ms / 1000
            print(f"HttpError reached! #{fails} fail(s). Sleeping for {sleep_for} seconds. Good night...")
            time.sleep(sleep_for)
        else:
            sent = True

def _set_one_day_event(calendar_id, summary, date, color_id, **kwargs):
    _set_event(calendar_id, 
               summary, 
               date, date, 
               color_id, 
               **kwargs)

# --------------------- Course singleton events --------------------- #

def set_course_main_event(calendar_id, course: Course, **kwargs):
    _set_one_day_event(calendar_id, course.main_event_string(), course.stop, '11', **kwargs)

def set_course_repetition_event(calendar_id, course: Course, **kwargs):
    _set_one_day_event(calendar_id, course.repetition_event_string(), course.repetition_date, '4', **kwargs)

# --------------------- Course span events -------------------------- #

def set_course_exercise_span_event(calendar_id, course: Course, **kwargs):
    start, stop = ends(course.exercise_dates)
    _set_event(calendar_id, course.exercise_span_event_string(), start, stop, '9', **kwargs)

def set_course_exam_span_event(calendar_id, course: Course, **kwargs):
    start, stop = ends(course.exam_dates)
    _set_event(calendar_id, course.exam_span_event_string(), start, stop, '9', **kwargs)

# --------------------- Course "repeating" events ------------------- #

def set_course_exercise_events(calendar_id, course: Course, **kwargs):
    for chunk, date in zip(course.chunk_over_days, course.exercise_dates):
        _set_one_day_event(calendar_id, course.exercise_event_string(chunk), date, '7')

def set_course_exam_events(calendar_id, course: Course, **kwargs):
    for n, date in enumerate(course.exam_dates):
        _set_one_day_event(calendar_id, course.exam_event_string(n), date, '7', **kwargs)

# --------------------- Course singleton events ------------------- #

def set_course_repetition_event(calendar_id, course: Course, **kwargs):
    _set_one_day_event(calendar_id, course.repetition_event_string(), course.repetition_date, '4', **kwargs)

def set_course_main_event(calendar_id, course: Course, **kwargs):
    _set_one_day_event(calendar_id, course.main_event_string(), course.stop, '11', **kwargs)

# ---------------------- Put it all together ---------------------- #

def set_course_events(course):
    calendar_id = get_courses_calendar()['id']

    set_course_exercise_span_event(calendar_id, course)
    set_course_exam_span_event(calendar_id, course)

    set_course_exercise_events(calendar_id, course)
    set_course_exam_events(calendar_id, course)

    set_course_main_event(calendar_id, course)
    set_course_repetition_event(calendar_id, course)

def set_all_courses_all_events():
    for course in Course.courses():
        set_course_events(course)

def main():
    set_all_courses_all_events()

if __name__ == '__main__':
    main()
