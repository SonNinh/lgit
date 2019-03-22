#!/usr/bin/python3

from argparse import ArgumentParser
from os import mkdir, O_CREAT, O_RDWR, O_RDONLY, chmod, stat, getcwd, listdir
from os import path, close, unlink, lseek, walk, environ, unlink
import hashlib
from time import ctime
from datetime import datetime


def lgitRemove(srcFiles):
    for file in srcFiles:
        try:
            unlink(file)
        except FileNotFoundError:
            print('fatal: pathspec \'{}\' did not match any files'.format(file))


def printReadableTime(time):
    dictOfWeekDay = {'0': 'Sun', '1': 'Mon', '2': 'Tue', '3': 'Wed',
                     '4': 'Thu', '5': 'Fri', '6': 'Sat'}

    x = datetime(int(time[:4]), int(time[4:6]), int(time[6:8]),
                 int(time[8:10]), int(time[10:12]), int(time[12:14]))
    weekday = dictOfWeekDay[x.strftime('%w')]

    print('Date:', weekday, x.strftime('%b %d %H:%M:%S %Y'))


def lgitLog():

    pathLgit = getNearestLgit()
    pathCommits = path.join(pathLgit, 'commits')
    lsOfCommits = listdir(pathCommits)
    for i, file in enumerate(lsOfCommits[::-1]):
        print('commit', file)
        commit = open(path.join(pathCommits, file), 'r')
        commitContent = commit.read().split('\n')
        print('Author:', commitContent[0])
        printReadableTime(commitContent[1])
        print('\n    ', commitContent[3])
        if i != len(lsOfCommits)-1:
            print('\n\n')
        commit.close()


def lgitLsFiles():
    pathLgit = getNearestLgit()
    relativeCurrentDir = getcwd()[len(path.dirname(pathLgit))+1:]
    indexFile = open(path.join(pathLgit, 'index'), 'r')
    eachLine = indexFile.readline().split()
    while len(eachLine) > 0:
        if eachLine[-1][:len(relativeCurrentDir)] == relativeCurrentDir:
            print(eachLine[-1][len(relativeCurrentDir)+1:])
        eachLine = indexFile.readline().split()
    indexFile.close()


def lgitConfig(author, pathLgit):
    pathConfig = path.join(pathLgit, 'config')
    configFile = open(pathConfig, 'w+')
    configFile.write(author)
    configFile.close()


def getUserName():
    pathConfig = path.join(getNearestLgit(), 'config')
    if path.isfile(pathConfig):
        configFile = open(pathConfig, 'r+')
    else:
        configFile = open(pathConfig, 'w+')
    userName = configFile.read()
    if len(userName) == 0:
        userName = environ.get("LOGNAME")
        configFile.write(userName)
    configFile.close()
    return userName


def lgitCommit(comment):
    currentTime = datetime.now().strftime('%Y%m%d%H%M%S')
    pathLgit = getNearestLgit()
    pathSnapshots = path.join(pathLgit, 'snapshots')
    snapshotsFile = open(path.join(pathSnapshots, currentTime), 'w+')
    indexFile = open(path.join(pathLgit, 'index'), 'r+')
    eachLine = indexFile.readline().split()
    cursorPos = 0
    firstime = 1
    while len(eachLine) > 1:
        cursorPos += 97
        indexFile.seek(cursorPos, 0)
        indexFile.write(eachLine[2])
        if firstime != 1:
            snapshotsFile.write('\n')
        else:
            firstime = 0
        snapshotsFile.write(eachLine[2] + ' ' + eachLine[-1])
        cursorPos += (42+len(eachLine[-1]))
        indexFile.seek(cursorPos, 0)
        eachLine = indexFile.readline().split()

    snapshotsFile.close()
    indexFile.close()

    pathCommits = path.join(pathLgit, 'commits')
    f = open(path.join(pathCommits, currentTime), 'w+')
    f.write(getUserName())
    f.write('\n')
    f.write(currentTime)
    f.write('\n\n')
    f.write(comment)
    f.close()


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


def updateExistedIndex(indexFile, file, cursorPos):
    indexFile.seek(cursorPos, 0)
    mtime = getTime(file)
    indexFile.write(mtime)

    hash = (' ' + getHash(file))*2
    indexFile.write(hash)


def updateIndexFile(file, pathLgit):
    dirNameOfLgit = path.dirname(pathLgit)
    indexFile = open(path.join(pathLgit, 'index'), 'r+')
    cursorPos = 0
    eachLine = indexFile.readline().split()

    while len(eachLine) > 1:
        if eachLine[-1] == path.abspath(file)[len(dirNameOfLgit)+1:]:
            updateExistedIndex(indexFile, file, cursorPos)
            break

        cursorPos += (139+len(eachLine[-1]))
        eachLine = indexFile.readline().split()
    else:
        if cursorPos > 1:
            mtime = '\n' + getTime(file)
        else:
            mtime = getTime(file)
        indexFile.write(mtime)

        hash = (' ' + getHash(file))*2
        hash += (' '*42)
        indexFile.write(hash)
        indexFile.write(path.abspath(file)[len(dirNameOfLgit)+1:])

    indexFile.close()


def getHash(file):
    f = open(file, 'rb')
    txt = f.read()
    m = hashlib.sha1()
    m.update(txt)
    return m.hexdigest()


def createNewFoderlInObjects(file, pathLgit):
    hash = getHash(file)
    newdir = path.join(pathLgit, 'objects')
    newdir = path.join(newdir, hash[:2])
    if not path.isdir(newdir):
        mkdir(newdir)
    newdir = newdir + '/' + hash[2:]
    f = open(newdir, 'w+')
    f.write(open(file, 'r').read())
    f.close()
    chmod(newdir, 0o644)


def lgitAdd(srcFiles):
    pathLgit = getNearestLgit()

    for dir in srcFiles:
        if path.isfile(dir):
            createNewFoderlInObjects(dir, pathLgit)
            updateIndexFile(dir, pathLgit)
        elif path.isdir(dir):
            for root_w, _, files_w in walk(dir, topdown=True):
                for name in files_w:
                    pathFile = path.join(root_w, name)
                    createNewFoderlInObjects(pathFile, pathLgit)
                    updateIndexFile(pathFile, pathLgit)


def printStatus(lsOfAddedFiles, lsOfNotAddedFiles, pathLgit):
    if len(lsOfAddedFiles) > 0:
        print('Changes to be committed:\n  (use \"./lgit.py reset HEAD ...\" to unstage)\n')
        for file in lsOfAddedFiles:
            print('     modified:', file)

    if len(lsOfNotAddedFiles) > 0:
        print('\nChanges not staged for commit:')
        print('  (use \"./lgit.py add ...\" to update what will be committed)')
        print('  (use \"./lgit.py checkout -- ...\" to discard changes in working directory)\n')
        for file in lsOfNotAddedFiles:
            print('     modified:', file)

    dirNameOfLgit = path.dirname(pathLgit)
    firstime = 0
    for root_w, _, files_w in walk(dirNameOfLgit, topdown=True):
        for name in files_w:
            relativeDir = path.join(root_w, name)[len(dirNameOfLgit)+1:]

            if relativeDir not in lsOfAddedFiles and relativeDir[:5] != '.lgit':
                if firstime == 0:
                    firstime = 1
                    print("\nUntracked files:")
                    print('  (use \"./lgit.py add <file>...\" to include in what will be committed)\n')
                print('    ',relativeDir)

    if len(lsOfAddedFiles) == 0:
        print('\nnothing added to commit but untracked files present (use \"./lgit.py add\" to track)')


def lgitStatus():
    cursorPos = 0
    lsOfAddedFiles = list()
    lsOfNotAddedFiles = list()
    lsOfUntrackedFiles = list()

    pathLgit = getNearestLgit()
    indexFile = open(path.join(pathLgit, 'index'), 'r+')
    eachLine = indexFile.readline().split()
    while len(eachLine) > 1:
        # rewrite timestamp
        indexFile.seek(cursorPos, 0)
        pathName = path.join(path.dirname(pathLgit), eachLine[-1])
        mtime = getTime(pathName)
        indexFile.write(mtime)

        hash = ' ' + getHash(pathName)
        indexFile.write(hash)

        lsOfAddedFiles.append(eachLine[-1])
        if hash[1:] != eachLine[2]:
            lsOfNotAddedFiles.append(eachLine[-1])

        cursorPos += (139+len(eachLine[-1]))
        indexFile.seek(cursorPos, 0)
        eachLine = indexFile.readline().split()

    indexFile.close()
    printStatus(lsOfAddedFiles, lsOfNotAddedFiles, pathLgit)


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


def getNearestLgit():
    currentDir = getcwd()
    while len(currentDir) > 0:
        for dir in listdir(currentDir):
            if dir == '.lgit':
                return path.join(currentDir, dir)

        currentDir = path.dirname(currentDir)
    return None


def main():
    parser = ArgumentParser()
    parser.add_argument('input', type=str, nargs='+')
    parser.add_argument("-m", "--mm", type=str)
    parser.add_argument("-a", "--author", type=str)
    args = parser.parse_args()

    pathLgit = getNearestLgit()
    if pathLgit is None:
        if args.input[0] == 'init':
            lgitInit()
        else:
            print('fatal: not a git repository (or any of the parent directories): .git')
    else:
        if isGoodLgit():
            if args.input[0] == 'init':

            elif args.input[0] == 'add':
                lgitAdd(args.input[1:])
            elif args.input[0] == 'status':
                lgitStatus()
            elif args.input[0] == 'commit':
                lgitCommit(args.mm)
            elif args.input[0] == 'config':
                lgitConfig(args.author)
            elif args.input[0] == 'ls-files':
                lgitLsFiles()
            elif args.input[0] == 'log':
                lgitLog()
            elif args.input[0] == 'rm':
                lgitRemove(args.input[1:])



if __name__ == "__main__":
    main()
