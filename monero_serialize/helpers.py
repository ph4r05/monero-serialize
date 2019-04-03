#!/usr/bin/env python
# -*- coding: utf-8 -*-


class TrackedObj(object):
    def __init__(self, val):
        self.val = val

    def __str__(self):
        return '[%s]' % self.val


class TrackField(TrackedObj):
    pass


class TrackIndex(TrackedObj):
    pass


class TrackVariant(TrackedObj):
    pass


class Tracker(object):
    def __init__(self):
        self.cur = []

    def push(self, obj):
        self.cur.append(obj)

    def push_field(self, obj):
        self.push(TrackField(obj))

    def push_index(self, obj):
        self.push(TrackIndex(obj))

    def push_variant(self, obj):
        self.push(TrackVariant(obj))

    def pop(self):
        self.cur.pop()

    def __str__(self):
        return ''.join([str(x) for x in self.cur])


class ArchiveException(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.subexc = None if len(args) == 0 else args[0]
        self.tracker = kwargs.get('tracker', None)

    def __str__(self):
        if self.subexc and isinstance(self.subexc, ArchiveException):
            return super().__str__()

        return '%s, path: %s' % (super().__str__(), self.tracker)
