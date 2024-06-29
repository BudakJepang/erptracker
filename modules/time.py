import pytz

def convert_time_to_wib(dtobject):
    tz = pytz.timezone('Asia/Jakarta')
    utc = pytz.timezone('UTC')
    tz_aware = utc.localize(dtobject)
    localtime = tz_aware.astimezone(tz)
    return localtime
