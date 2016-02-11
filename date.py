#--------------------------------------------------------------------------------
# Copyright (c) 2009-2016, GMAO (NASA)
# All rights reserved.
# Authorisation to be used by Claude Gibert
#
# Author: Claude Gibert
#
#--------------------------------------------------------------------------------
import types
import calendar
import re
import copy
from collections import defaultdict
import datetime
#----------------------------------------------------------------------------
# Yet another Date class implementation. I kept my approach of "variable
# geometry" dates, e.g:
# - 2009             + 1  = 2010
# - 200902           + 1  = 200903
# - 20090201         + 1  = 20090202
# - 2009020112       + 12 = 2009020200
# - 200902011234     + 26 = 200902011300
# - 20090201123432    + 26 = 20090201123458
#----------------------------------------------------------------------------

def toComponents(value):
    if isinstance(value,basestring):
        value = re.sub('[^\d]','',value)
    value = long(value)
    components = []
    while value > 10000:  # go to the year
    	components.append(value % 100)
    	value //= 100
    components.append(value)
    components.reverse()
    l = len(components)
    while len(components) < 3:
    	components.append(1)
    return components,l

class DateIncrement(object):
    
    nulldelta = datetime.timedelta()

    def __init__(
    		self,
    		years = 0,
    		months = 0,
    		days = 0,
    		hours = 0,
    		minutes = 0,
    		seconds = 0
    	):
    	self.years = years
    	self.months = months
    	self.delta = datetime.timedelta(days=days,hours=hours,minutes=minutes,seconds=seconds)

    def add(self,date):
    	if self.delta != self.nulldelta:
    		date += self.delta
    	if self.months != 0:
    		value = abs(self.months)
    		months = value % 12
    		years = value // 12
    		if self.months < 0:
    			months = -months
    			years = -years
    		months = date.month + months
    		years = date.year + years
    		while (months < 1 ) or (months > 12):
    			if months < 1:
    				months += 12
    				years -= 1
    			elif months > 12:
    				months -= 12
    				years += 1
    		date = date.replace(year= years)
    		date = date.replace(month= months)
    	if self.years != 0:
    		date = date.replace(year= date.year+self.years)
    	return date
    	
    def __neg__(self):
    	new = DateIncrement()
    	new.delta = -self.delta
    	new.months = -self.months
    	new.years = -self.years
    	return new

    def __eq__(self,value):
    	if isinstance(value,DateIncrement):
    		return self.months == value.months and self.years == value.years and self.delta == value.delta
    	return self.months == value and self.years == value and self.delta.days == 0 and self.delta.seconds == 0

    def __str__(self):
    	return "%04d/%02d/%02d %02d:%02d:%02d" % (self.years,self.months,self.delta.days,self.delta.seconds // 3600,self.delta.seconds // 60,self.delta.seconds % 60)
    
#----------------------------------------------------------------------------
# Generic public Date entry
#----------------------------------------------------------------------------
class Date(object):

    def __new__(cls,value = None):
        if value is None:
            value = datetime.datetime.now()
    	if isinstance(value,CoreDate):
    		return value.__class__(value.date)
    	elif isinstance(value,datetime.datetime):
    		return Second(value)
        elif isinstance(value,datetime.date):
            value = datetime.datetime(value.year,value.month,value.day)
            return Second(value)
    	components,l = toComponents(value)
    	return switch[l](datetime.datetime(*components))

#----------------------------------------------------------------------------
# Generic private Date entry
#----------------------------------------------------------------------------
class CoreDate(object):
    
    no_separators = re.compile('[:\-\s]')

    def __init__(self,date):
        if isinstance(date,CoreDate):
            self.date = date.date
    	elif isinstance(date,datetime.datetime):
    		self.date = date
        elif isinstance(date,datetime.date):
    		self.date = datetime.datetime(date.year,date.month,date.day)
    	else:
    		c,l = toComponents(date)
    		self.date = datetime.datetime(*c)

    #-------------------------------------------------------------------------
    # Accessors
    #-------------------------------------------------------------------------
    def datetime(self):
    	return self.date

    def year(self):
    	return "%04d" % self.date.year

    def month(self):
    	return "%02d" % self.date.month

    def day(self):
    	return "%02d" % self.date.day

    def hour(self):
    	return "%02d" % self.date.hour
    time = hour

    def minute(self):
    	return "%02d" % self.date.minute

    def second(self):
    	return "%02d" % self.date.second

    def intvalue(self):
    	return int(re.sub(CoreDate.no_separators,'',self.__str__()))

    def stringvalue(self):
        return re.sub(CoreDate.no_separators,'',self.__str__())

    def __str__(self):
    	return self.date.strftime(self.template())
    __repr__ = __str__

    def unixTimeStamp(self):
        return calendar.timegm(self.datetime().utctimetuple())

    def format(self,format = None):
    	if not format:
    		format = self.template()
    	return self.date.strftime(format)

    def ISO8601(self,timezone=None):
    	s = self.date.strftime("%Y-%m-%dT%H:%M:%S")
        if timezone is not None:
            s += timezone
        return s

    def isRoundMultiple(self,numberIndSeconds):
        t = int(self.unixTimeStamp())
        return (t % numberIndSeconds) == 0

    def lastRoundMultiple(self,incrementInSeconds):
        t = int(self.unixTimeStamp())
        d = t // incrementInSeconds
        return dateFromTimeStamp(incrementInSeconds * d)

    def nextRoundMultiple(self,incrementInSeconds):
        return self.lastRoundMultiple(incrementInSeconds) + incrementInSeconds

    def isoDate(self):
        return self.date.strftime('%a, %d %b %Y %H:%M:%S') + ' +0000'


    #-------------------------------------------------------------------------
    # Arithmetics and comparisons
    #-------------------------------------------------------------------------
    def __add__(self,what):
    	new = Date(self)
    	new += what
    	return new
    __radd__ = __add__

    def __iadd__(self,what):
    	if not isinstance(what,(int,long,float,DateIncrement)):
    		raise ValueError("only a number or a DateIncrement can be added to a date")
    	if not isinstance(what,DateIncrement):
    		what = DateIncrement(**self.unit(what))
    	self.date = what.add(self.date)
    	return self

    def __sub__(self,what):
    	if not isinstance(what,CoreDate):
    		new = Date(self)
    		new -= what
    		return new
    	else:
    		if self.date > what.date:
    			new = self.substract(self.date,what.date)
    		else:
    			new = - self.substract(what.date,self.date)
    	return new

    def __rsub__(self,other):
    	raise SystemError('Right-hand side substraction is not implemented')

    def __isub__(self,what):
    	if not isinstance(what,(int,long,float,DateIncrement)):
    		raise ValueError("only a number or a DateIncrement can be added to a date")
    	if not isinstance(what,DateIncrement):
    		what = DateIncrement(**self.unit(-what))
    	else:
    		what = -what
    	self.date = what.add(self.date)
    	return self

    def __eq__(self,other):
    	if not isinstance(other,CoreDate):
    		other = Date(other)
    	return self.date == other.date

    def __ne__(self,other):
    	if not isinstance(other,CoreDate):
    		other = Date(other)
    	return self.date != other.date

    def __gt__(self,other):
    	if not isinstance(other,CoreDate):
    		other = Date(other)
    	return self.date > other.date

    def __ge__(self,other):
    	if not isinstance(other,CoreDate):
    		other = Date(other)
    	return self.date >= other.date

    def __lt__(self,other):
    	if not isinstance(other,CoreDate):
    		other = Date(other)
    	return self.date < other.date

    def __le__(self,other):
    	if not isinstance(other,CoreDate):
    		other = Date(other)
    	return self.date <= other.date

    def __hash__(self):
    	return self.intvalue()

#----------------------------------------------------------------------------
# Date yyyymmddhhMMss
#----------------------------------------------------------------------------
class Second(CoreDate):

    @classmethod
    def template(self):
    	return "%Y-%m-%d %H:%M:%S"

    def unit(self,value):
    	return { 'seconds': value }

    def substract(self,a,b):
    	c = a-b
    	return c.days * 86400 + c.seconds
#----------------------------------------------------------------------------
# Date yyyymmddhhMM
#----------------------------------------------------------------------------
class Minute(CoreDate):
    
    @classmethod
    def template(self):
    	return "%Y-%m-%d %H:%M"

    def unit(self,value):
    	return { 'minutes': value }

    def substract(self,a,b):
    	b = b.replace(second = 0)
    	c = a-b
    	return c.days * 1440 + c.seconds // 60

#----------------------------------------------------------------------------
# Date yyyymmddhh
#----------------------------------------------------------------------------
class Hour(CoreDate):

    @classmethod
    def template(self):
    	return "%Y-%m-%d %H"

    def unit(self,value):
    	return { 'hours': value }

    def substract(self,a,b):
    	b = b.replace(second = 0,minute = 0)
    	c = a-b
    	return c.days * 24 + c.seconds // 3600

#----------------------------------------------------------------------------
# Date yyyymmdd
#----------------------------------------------------------------------------
class Day(CoreDate):

    @classmethod
    def template(self):
    	return "%Y-%m-%d"

    def unit(self,value):
    	return { 'days': value }

    def substract(self,a,b):
    	b = b.replace(second = 0,minute = 0, hour = 0)
    	c = a-b
    	return c.days

#----------------------------------------------------------------------------
# Date yyyymm
#----------------------------------------------------------------------------
class Month(CoreDate):
    
    @classmethod
    def template(self):
    	return "%Y-%m"

    def unit(self,value):
    	return { 'months': value }

    def substract(self,a,b):
    	return a.month - b.month + (a.year - b.year) * 12

#----------------------------------------------------------------------------
# Date yyyy
#----------------------------------------------------------------------------
class Year(CoreDate):

    @classmethod
    def template(self):
    	return "%Y"

    def unit(self,value):
    	return { 'years': value }

    def substract(self,a,b):
    	return a.year - b.year

switch = {
    1: Year,
    2: Month,
    3: Day,
    4: Hour,
    5: Minute,
    6: Second,
}

#----------------------------------------------------------------------------
# arguments are taken 3 at a time
# dates = Dates(d11,d12,inc1,d21,d22,inc2,...,dn1,dn2,incn,format = '%Y%m%d')
# returns the concatenation of sequences of dates.
#----------------------------------------------------------------------------
def Dates(*args,**kargs):
    args = list(args)
    if len(args) == 2:
    	# defaults to increment 1
    	args.append(1)
    elif len(args) % 3 != 0:
    		raise ValueError('Arguments should work in triples: date1,date2,increment,...')
    result = []
    format = None
    if 'format' in kargs:
    	format = kargs['format']
    i = 0
    while i < len(args):
    	begin = Date(args[i])
    	end = Date(args[i+1])
    	incr = args[i+2]
    	i += 3
    	if incr == 0:
    		raise ValueError('An increment of 0 does not make much sense')
    	if begin <= end:
    		while begin <= end:
    			if format:
    				result.append(begin.format(format))
    			else:
    				result.append(begin.intvalue())
    			begin += incr	
    	else:
    		while begin >= end:
    			if format:
    				result.append(begin.format(format))
    			else:
    				result.append(int(begin.intvalue()))
    			begin += incr	
    return result

DateSequence = Dates

def dateFromTimeStamp(value):
    return Date(datetime.datetime.utcfromtimestamp(float(value)))

def utcNow():
    return Date(datetime.datetime.utcnow())

def isoDateToDate(date):
    all = date.split(' ')
    date = ' '.join(all[:-1])
    offset = all[-1]
    d = Date(datetime.datetime.strftime(datetime.datetime.strptime(date,'%a, %d %b %Y %H:%M:%S'),'%Y%m%d%H%M%S'))
    sign = offset[0]
    value = DateIncrement(hours=int(offset[1:])//100)
    if sign == '+':
        d -= value
    elif sign == '-':
        d += value
    else:
        raise ValueError('Cannot decode %s' % date)
    return d

def metronomeDateToDate(date):
    offset = date[19:]
    offset = re.sub(':','',offset)
    d = date[:19]
    d = re.sub('[-T:]','',d)
    d = Date(d)
    sign = offset[0]
    value = DateIncrement(hours=int(offset[1:])//100)
    if sign == '+':
        d -= value
    elif sign == '-':
        d += value
    else:
        raise ValueError('Cannot decode %s' % date)
    return d

def twitterDateToDate(date):
    all = date.split(' ')
    date = ' '.join(all[:-2]) + ' ' + all[-1]
    offset = all[-2]
    d = Date(datetime.datetime.strftime(datetime.datetime.strptime(date,'%a %b %d %H:%M:%S %Y'),'%Y%m%d%H%M%S'))
    sign = offset[0]
    value = DateIncrement(hours=int(offset[1:])//100)
    if sign == '+':
        d -= value
    elif sign == '-':
        d += value
    else:
        raise ValueError('Cannot decode %s' % date)
    return d

def mysqlDateToDate(date):
    date = re.sub('[ :-]','',date)
    return Date(date)


