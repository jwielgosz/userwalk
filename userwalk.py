#!/usr/bin/python

#==========================================================
# created: wielgosz  2016-08-19
#
#  userwalk.py
#
#  Print disk usage by user
#
#==========================================================

import sys
import os
import pwd
import time
import argparse
#import pandas

from os.path import join, getsize, islink



# def uname(uid):
#     return pwd.getpwuid(uid).pw_name

uname = lambda uid: pwd.getpwuid(uid).pw_name
lcol = lambda s: '{0: <16}'.format(s)

class userwalk:

    totals = {}
    min_print = 0
    totals_only = False
    unit = 1
    header = False

    def __init__(self, basepath):
        self.basepath = basepath
        self.sum_by_user(basepath)

    def add(self, user, path, amt):
        if not (user in self.totals.keys()):
            self.totals[user] = {}
        if not (path in self.totals[user].keys()):
            self.totals[user][path] = 0
        self.totals[user][path] += amt

    def get(self, user, path):
        if not (user in self.totals.keys()):
            return 0
        if not (path in self.totals[user].keys()):
            return 0
        return self.totals[user][path]

    # def totals_as_df(self):
    #     flattened = [(u, p, s) for u, ps in self.totals.items() for p, s in ps.items() ]
    #     df = pandas.DataFrame(flattened, columns=['user','path','size'])
    #     return df

    def all_users(self):
        return sorted(self.totals.keys())

    def sum_by_user(self, basepath):

        try:
            (root, dirs, files) = next(os.walk(basepath))
        except StopIteration:
            print >> sys.stderr, "Skipped path, nothing here:", basepath

        fpaths = [join(root, f) for f in files]
        fpaths = [ f for f in fpaths if not(islink(f))]
        dpaths = [join(root, d) for d in dirs]

        for d in dpaths:
            self.sum_by_user(d)

        for f in fpaths:
            try:
                fs = os.stat(f)
            except IOError as e:
                print >> sys.stderr, "Unable to get user or size for:", f
                print >> sys.stderr, "I/O error({0}): {1}".format(e.errno, e.strerror)
                continue
            u = uname(fs.st_uid)
            sz = fs.st_size
            self.add(u, basepath, sz)

        for u in self.all_users():
            for d in dpaths:
                subsz = self.get(u, d)
                self.add(u, basepath, subsz)

    def print_header(self):
        if self.header:
            print lcol("user"), lcol("size"), lcol("path")
            print  "-" * 78

    def print_all(self):
        self.print_header()
        for u in self.all_users():
            self.print_user(u)

    def print_totals(self):
        self.print_header()
        for u in self.all_users():
            self.print_entry(u, self.basepath)

    def print_combined(self):
        gt = sum([self.get(u, self.basepath) for u in self.all_users()])
        print lcol("Combined total: "), int(gt / self.unit)

    # def sort_paths_by_size(self, u):
    #     totals_by_size = {}
    #     for k, v in totals[u]
    #         totals_by_size =

    def print_user(self, u):
        sorted_paths = sorted(self.totals[u].keys())
        for p in sorted_paths:
            self.print_entry(u, p)

    def print_entry(self, u, p):
        sz = self.get(u, p)
        sz_units = int(sz / self.unit)
        if (sz_units >= self.min_print):
            print lcol(u), lcol(sz_units), p

        #self.record('joew', path, path_total)
        #return path_total

def main():
    parser = argparse.ArgumentParser(description='Print disk usage by user')
    parser.add_argument('basepath', action='store',
                        help = 'Path to recursively search')
    parser.add_argument('-u', '--unit', action='store', default=1e6, type=float,
                        help = 'Unit to print in, e.g. 1000 for KB, 1e6 for MB, 1e9 for GB (default 1e6)')
    parser.add_argument('-m', '--min_print', action='store', default=1, type=float,
                        metavar='SIZE',
                        help = 'Minimum total size (in specified units) for folder to be printed (default 0)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help = 'Print header information')
    parser.add_argument('-t', '--totals', action='store_true',
                        help = 'Print totals per user')
    parser.add_argument('-r', '--recursive', action='store_true',
                        help = 'Print totals recursively for subfolders')
    args = parser.parse_args()

    if args.verbose:
        print "=" * 78
        print lcol("userwalk.py:"), "Usage totals by user"
        print lcol("Date: "), time.strftime("%c")
        print lcol("Base path: "), args.basepath
        print lcol("Units: "), "%g" % args.unit, "bytes"
        print lcol("Threshold: "), "%g" % (args.unit * args.min_print), "bytes"
        print lcol("Command: "), " ".join(sys.argv)
        print  "=" * 78
        print

    U = userwalk(args.basepath)
    U.min_print = args.min_print
    U.unit = args.unit
    U.header = args.verbose

    if args.totals:
        if args.verbose:
            print "TOTALS"
            print
            U.print_combined()
            print
        U.print_totals()

    if args.recursive:
        if args.verbose:
            print
            print "SUBFOLDERS"
            print 
        U.print_all()



if __name__ == "__main__":
    main()
