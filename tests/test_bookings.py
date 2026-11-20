from app.modules.bookings import service


def test_retransmit_same_event_isolated(ledger):
    assert [x['line'] for x in ledger['bookings']['issues'] if x['code'] == 'DUP_EVENT'] == [5]


def test_naive_timestamp_not_inferred(ledger):
    assert [x['line'] for x in ledger['bookings']['issues'] if x['code'] == 'BAD_TIME'] == [18]


def test_accepts_cancel_without_interval(night):
    accepted, view = service.load([night['events'][3]])
    assert accepted[0].start is None
    assert view['rows'][0]['action'] == 'cancel' and view['rows'][0]['end'] == ''


def test_same_number_distinct_revision_kept(night):
    records, view = service.load(night['events'][:2])
    assert [(e.key, e.revision) for e in records] == [('0042', 2), ('0042', 1)]
    assert view['metrics']['采信'] == 2


def test_invalid_action_retains_raw_row(night):
    original = night['events'][1] | {'action':'延期请求'}
    _, view = service.load([original])
    assert view['issues'][0]['raw'] == original and view['issues'][0]['code'] == 'BAD_ROW'


def test_invalid_room_identity_cannot_be_coerced(night):
    row = night['events'][1] | {'rink':42}
    _, view = service.load([row])
    assert view['metrics']['异常'] == 1 and view['metrics']['采信'] == 0
