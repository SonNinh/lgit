#!/usr/bin/python3

from argparse import ArgumentParser
from os import open, mkdir, O_CREAT, O_RDWR, O_RDONLY, chmod, stat
from os import write, read, path, close, unlink, lseek
import hashlib
from time import ctime


def createTime(mtime):
    lsOfMonth = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                 'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}
    res = mtime[-4:]
    res += lsOfMonth[mtime[4:7]]
    res += mtime[8:10]
    res += mtime[11:13]
    res += mtime[14:16]
    res += mtime[17:19]
    return res


def createNewFoderlInObjects(file, m):
    f = open(file, O_RDONLY)
    txt = read(f, stat(f).st_size)
    m.update(txt)
    hash = m.hexdigest()
    newdir = '.lgit/objects/' + hash[:2]
    if not path.isdir(newdir):
        mkdir(newdir)
    newdir = newdir + '/' + hash[2:]
    try:
        unlink(newdir)
    except Exception:
        pass
    f = open(newdir, O_CREAT | O_RDWR)
    write(f, txt)
    close(f)
    chmod(newdir, 0o644)


def lgitAdd(srcFiles):
    m = hashlib.sha1()
    indexFile = open('.lgit/index', O_CREAT | O_RDWR)
    lseek(indexFile, stat(indexFile).st_size, 0)
    for file in srcFiles:
        createNewFoderlInObjects(file, m)

        mtime = ctime(stat(file).st_mtime)
        mtime = createTime(mtime)
        write(indexFile, ('\n' + mtime).encode())

        f = open(file, O_RDONLY)
        txt = read(f, stat(f).st_size)
        m.update(txt)
        hash = ' ' + m.hexdigest()
        hash *= 2
        hash += (' '*42)
        write(indexFile, hash.encode())
        write(indexFile, file.encode())
    close(indexFile)


def lgitInit():
    try:
        mkdir('.lgit')
        mkdir('.lgit/objects')
        mkdir('.lgit/commits')
        mkdir('.lgit/snapshots')
        f = open('.lgit/index', O_CREAT | O_RDWR)
        close(f)
        chmod('.lgit/index', 0o644)
        f = open('.lgit/config', O_CREAT | O_RDWR)
        close(f)
        chmod('.lgit/config', 0o644)
    except Exception as e:
        print(e)


def main():
    parser = ArgumentParser()
    parser.add_argument('input', type=str, nargs='+')

    args = parser.parse_args()

    if args.input[0] == 'init':
        lgitInit()
    elif args.input[0] == 'add':
        lgitAdd(args.input[1:])
    elif args.input[0] == 'commit':
        lgitCommit(args.srcFiles)


if __name__ == "__main__":
    main()
