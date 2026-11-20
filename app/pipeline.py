from . import clock, source
from .modules.balance import service as balance
from .modules.bookings import service as bookings
from .modules.calendar import service as calendar
from .modules.changes import service as changes
from .modules.debit import service as debit
from .modules.passes import service as passes


def process(raw):
    data = source.read(raw)
    cutoff = clock.stamp(data.get('cutoff'))
    windows, calendar_view = calendar.load(data['windows'])
    versions, pass_view = passes.load(data['passes'])
    events, booking_view = bookings.load(data['events'])
    active, change_view = changes.replay(events, cutoff)
    all_issues = [issue for view in (calendar_view, pass_view, booking_view, change_view) for issue in view['issues']]
    debit_view = debit.allocate(active, windows, versions)
    balance_view = balance.reconcile(active, debit_view, all_issues)
    return {'calendar': calendar_view, 'passes': pass_view, 'bookings': booking_view, 'changes': change_view,
            'debit': debit_view, 'balance': balance_view}
