from app.clock import midnights


def boundaries(event, windows, versions):
    start, end = event.start, event.end
    points = {start, end, *midnights(start, end)}
    for item in (*windows, *versions):
        if item.rink != event.rink or getattr(item, 'owner', event.owner) != event.owner:
            continue
        points.update(point for point in (item.start, item.end) if start < point < end)
    return sorted(points)


def collisions(events):
    by_rink = {}
    overlaps = {}
    for event in sorted(events, key=lambda e: (e.rink, e.start, e.key)):
        nearby = [other for other in by_rink.get(event.rink, []) if other.end > event.start]
        for other in nearby:
            overlaps.setdefault(event.key, []).append(other.line)
            overlaps.setdefault(other.key, []).append(event.line)
        by_rink[event.rink] = [*nearby, event]
    return overlaps
