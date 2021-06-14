import os.path
from datetime import date, timedelta

def grouped(itr, n):
    itr = iter(itr)
    end = object()
    while True:
        vals = tuple(next(itr, end) for _ in range(n))
        if vals[-1] is end:
            return
        yield vals

def days(n):
    """Return a timedelta object of n days"""
    return timedelta(days=n)

def ends(iter):
    """Return the two ends of an iterable"""
    li = list(iter)
    return li[0], li[-1]

class Course:
    def __init__(self, name, start, stop, nbr_of_exams, exercises):
        self.name         = name
        self.start        = start
        self.stop         = stop
        self.nbr_of_exams = nbr_of_exams
        self.exercises    = exercises

    @classmethod
    def from_file(cls, fn):
        """Return a Course object parsed from a file"""
        fp = os.path.join('courses', fn)
        with open(fp, 'r') as f:
            lines = f.readlines()
            name         = os.path.splitext(fn)[0]
            start, stop  = map(date.fromisoformat, lines[0].split())
            nbr_of_exams = int(lines[1].rstrip())
            exercises    = [f'{chapter.rstrip()}.{exercise}' for (chapter, exercises) in grouped(lines[2:], 2) for exercise in exercises.split()]
            return cls(name, start, stop, nbr_of_exams, exercises)

    @classmethod
    def courses(cls):
        """Parse each course file in the courses directory into a Course object and yield it."""
        for fn in os.listdir('courses'):
            yield cls.from_file(fn)
    
    @property
    def duration(self):
        return (self.stop - self.start).days

    def _date_iterator(self, start: date, stop: date):
        t = start
        incr = timedelta(days=1)
        while t < stop:
            yield t
            t += incr

    @property
    def all_dates(self):
        return self._date_iterator(self.start, self.stop)
    
    @property
    def exam_dates(self):
        return self._date_iterator(self.stop - days(self.nbr_of_exams + 1), self.stop - days(1))

    @property
    def exercise_dates(self):
        return self._date_iterator(self.start, self.stop - days(self.nbr_of_exams + 1))

    @property
    def repetition_date(self):
        return self.stop - days(1)

    @property 
    def chunk_over_days(self):
        """Chunk the exercises over a stretch of days"""
        
        # - 1 for full-day repetition
        # - nbr_of_exams for studying exams

        return self._chunk_over_days(self.duration - self.nbr_of_exams - 1)

    def _chunk_over_days(self, days):
        """Chunk the exercises over a stretch of days
        
        Imagine the list of exercises

        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        to be chunked over 3 days. That is, after doing a certain amount of 
        exercises each day (the day's chunk size), after 3 days, all exercises will be completed.

        example chunking:

        [(1, 2, 3), (4, 5, 6), (7, 8, 9, 10)]

        Note that, often, the chunks are not of the same length. To even it out
        as much as possible, we want to create a list of chunks such that:

        [(a1, a2, ..., an), (b1, b2, ..., bn), (c1, c2, ..., cn), ..., 
         (x1, x2, ..., x(n+1)), (y1, y2, ..., y(n+1)), (z1, z2, ..., z(n+1))]

        We then want to find out how many days that the chunking size is n and n + 1, respectively.
        Naturally, we only need to find out one to then know the other, so let's find out the latter. 
        How many days is the chunking size n + 1?
        
        Let:
            D be the number of days to chunk over
            d be the amount of days for which the chunking size is n + 1
            x be the amount for exercises 
            n be floor(X/D)
        
        then, we solve for **d** in the equation

        (D - d)n + d(n + 1) = x    <=>     d = x-Dn         <=>       d = x mod D 

        therefore, in plain terms, the general chunking of x exercises over D days can be described as:

        for D - (x mod D) days, do floor(x/D)     exercises
        for x mod D       days, do floor(x/D) + 1 exercises
        """
        x = len(self.exercises)  # see docs
        d = x % days             # see docs
        n = x // days            # see docs

        sliced_at = (days - d) * n
        pt1 = self.exercises[:sliced_at]
        pt2 = self.exercises[sliced_at:]

        return list(grouped(pt1, n)) + list(grouped(pt2, n + 1))
    
    def _calendar_event_string(self, *args):
        return ' | '.join((self.name, ) + args)
    
    def exercise_event_string(self, chunk):
        return self._calendar_event_string('UPPGIFTER', '  '.join(chunk))
    
    def exercise_span_event_string(self):
        return self._calendar_event_string('UPPGIFTER')
                
    def exam_event_string(self, n):
        return self._calendar_event_string('EXTENTOR', f'#{n}')         

    def exam_span_event_string(self):
        return self._calendar_event_string('EXTENTOR')    
    
    def repetition_event_string(self):
        return self._calendar_event_string('REPETITION')
    
    def main_event_string(self):
        return self._calendar_event_string('OMTENTA')
        
        