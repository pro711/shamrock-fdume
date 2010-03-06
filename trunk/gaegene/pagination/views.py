import re
from datetime import datetime

from django.template import loader, RequestContext
from django.http import Http404, HttpResponse
from django.core.xheaders import populate_xheaders
from django.core.exceptions import ObjectDoesNotExist

from gaegene.pagination.models import Paginator, Page


def parse_datetime(s):
    """Create datetime object representing date/time expressed in a string
    
    Takes a string in the format produced by calling str()
    on a python datetime object and returns a datetime
    instance that would produce that string.
    
    Acceptable formats are: "YYYY-MM-DD HH:MM:SS.ssssss+HH:MM",
                            "YYYY-MM-DD HH:MM:SS.ssssss",
                            "YYYY-MM-DD HH:MM:SS+HH:MM",
                            "YYYY-MM-DD HH:MM:SS",
                            "YYYY-MM-DD"
    Where ssssss represents fractional seconds.  The timezone
    is optional and may be either positive or negative
    hours/minutes east of UTC.
    """
    if s is None:
        return None
    # Split string in the form 2007-06-18 19:39:25.3300-07:00
    # into its constituent date/time, microseconds, and
    # timezone fields where microseconds and timezone are
    # optional.
    m = re.match(r'(.*?)(?:\.(\d+))?(([-+]\d{1,2}):(\d{2}))?$',
                 str(s))
    datestr, fractional, tzname, tzhour, tzmin = m.groups()
    
    # Create tzinfo object representing the timezone
    # expressed in the input string.  The names we give
    # for the timezones are lame: they are just the offset
    # from UTC (as it appeared in the input string).  We
    # handle UTC specially since it is a very common case
    # and we know its name.
    if tzname is None:
        tz = None
    else:
        tzhour, tzmin = int(tzhour), int(tzmin)
        if tzhour == tzmin == 0:
            tzname = 'UTC'
        tz = FixedOffset(timedelta(hours=tzhour,
                                   minutes=tzmin), tzname)
    
    # Convert the date/time field into a python datetime
    # object.
    try:
        x = datetime.strptime(datestr, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        x = datetime.strptime(datestr, "%Y-%m-%d")
    # Convert the fractional second portion into a count
    # of microseconds.
    if fractional is None:
        fractional = '0'
    fracpower = 6 - len(fractional)
    fractional = float(fractional) * (10 ** fracpower)
    
    # Return updated datetime object with microseconds and
    # timezone information.
    return x.replace(microsecond=int(fractional), tzinfo=tz)

def object_list(
        request, object_query, order_by, template_name,
        paginate_by=None, page_value=None, prefetch=None,
        template_loader=loader, extra_context=None,
        context_processors=None, template_object_name='object',
        mimetype=None
    ):
    if extra_context is None: extra_context = {}
    if paginate_by:
        paginator = Paginator(
            object_query, order_by, per_page=paginate_by, prefetch=prefetch
        )
        if not page_value:
            page_value = request.GET.get('page_value', None)
        page = paginator.page(page_value)
        c = RequestContext(
            request,
            {
                '%s_list' % template_object_name: page.object_list,
                'page': page
            },
            context_processors
        )
    else:
        c = RequestContext(
            request,
            {
                '%s_list' % template_object_name: object_query,
                'page': None
            },
            context_processors
        )
    for key, value in extra_context.items():
        if callable(value):
            c[key] = value()
        else:
            c[key] = value
    t = template_loader.get_template(template_name)
    return HttpResponse(t.render(c), mimetype=mimetype)

