#!/usr/bin/python3

from argparse import ArgumentParser
from os import mkdir, O_CREAT, O_RDWR, O_RDONLY, chmod, stat
from os import path, close, unlink, lseek
import hashlib
from time import ctime


def getTime(path):
    lsOfMonth = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                 'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}
    mtime = ctime(stat(path).st_mtime)
    res = mtime[-4:]
    res += lsOfMonth[mtime[4:7]]
    res += mtime[8:10]
    res += mtime[11:13]
    res += mtime[14:16]
    res += mtime[17:19]
    return res


def updateExistedIndex(indexFile, file, m, cursorPos):
    indexFile.seek(cursorPos, 0)
    mtime = getTime(file)
    indexFile.write(mtime)

    f = open(file, 'rb')
    txt = f.read()
    m.update(txt)
    hash = ' ' + m.hexdigest()
    hash *= 2
    indexFile.write(hash)


def updateIndexFile(file, indexFile):
    m = hashlib.sha1()
    cursorPos = 0
    indexFile.seek(cursorPos, 0)
    eachLine = indexFile.readline().split()

    while len(eachLine) > 1:
        if eachLine[-1] == path.abspath(file):
            updateExistedIndex(indexFile, file, m, cursorPos)
            break

        cursorPos += (139+len(eachLine[-1]))
        eachLine = indexFile.readline().split()
    else:
        indexFile.seek(0, 2)
        if cursorPos > 1:
            mtime = '\n' + getTime(file)
        else:
            mtime = getTime(file)
        indexFile.write(mtime)

        f = open(file, 'rb')
        txt = f.read()
        m.update(txt)
        hash = ' ' + m.hexdigest()
        hash *= 2
        hash += (' '*42)
        indexFile.write(hash)
        indexFile.write(path.abspath(file))


def getHash(f):
    txt = f.read()
    m = hashlib.sha1()
    m.update(txt)
    return m.hexdigest()


def createNewFoderlInObjects(file):
    f = open(file, 'rb')
    hash = getHash(f)
    newdir = '.lgit/objects/' + hash[:2]
    if not path.isdir(newdir):
        mkdir(newdir)
    newdir = newdir + '/' + hash[2:]
    f = open(newdir, 'w+')
    f.write(f.read())
    f.close()
    chmod(newdir, 0o644)


def lgitAdd(srcFiles):
    indexFile = open('.lgit/index', 'r+')
    for file in srcFiles:
        createNewFoderlInObjects(file)
        updateIndexFile(file, indexFile)

    indexFile.close()


def lgitStatus():
    cursorPos = 0
    lsOfAddedFiles = list()
    lsOfNotAddedFiles = list()
    indexFile = open('.lgit/index', 'r+')
    eachLine = indexFile.readline().split()
    print('Changes to be committed:\n  (use \"./lgit.py reset HEAD ...\" to unstage)\n')
    while len(eachLine) > 1:
        f = open(eachLine[-1], 'rb')
        # rewrite timestamp
        indexFile.seek(cursorPos, 0)
        mtime = getTime(eachLine[-1])
        indexFile.write(mtime)

        hash = getHash(f)
        indexFile.write(' ' + hash)

        print('     modified:', eachLine[-1])
        if hash != eachLine[2]:
            lsOfNotAddedFiles.append(eachLine[-1])

        cursorPos += (139+len(eachLine[-1]))
        indexFile.seek(cursorPos, 0)
        eachLine = indexFile.readline().split()

    indexFile.close()

    if len(lsOfNotAddedFiles) > 0:
        print('\nChanges not staged for commit:')
        print('  (use \"./lgit.py add ...\" to update what will be committed)')
        print('  (use \"./lgit.py checkout -- ...\" to discard changes in working directory)\n')
        for file in lsOfNotAddedFiles:
            print('     modified:', file)


def lgitInit():
    try:
        mkdir('.lgit')
        mkdir('.lgit/objects')
        mkdir('.lgit/commits')
        mkdir('.lgit/snapshots')
        f = open('.lgit/index', 'x')
        f.close()
        chmod('.lgit/index', 0o644)
        f = open('.lgit/config', 'x')
        f.close()
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
    elif args.input[0] == 'status':
        lgitStatus()


if __name__ == "__main__":
    main()
