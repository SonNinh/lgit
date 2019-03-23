#!/usr/bin/python3

from argparse import ArgumentParser
from os import mkdir, O_CREAT, O_RDWR, O_RDONLY, chmod, stat, getcwd, listdir
from os import path, close, unlink, lseek, walk, environ, unlink
import hashlib
from time import ctime
from datetime import datetime


def lgitRemove(srcFiles, pathLgit):
    indexContent = list()
    lsOfTracked = list()

    indexFile = open(path.join(pathLgit, 'index'), 'r')
    eachLine = indexFile.readline().split()
    while len(eachLine) > 0:
        indexContent.append(eachLine[1:])
        eachLine = indexFile.readline().split()

    dirNameOfLgit = path.dirname(pathLgit)

    for file in srcFiles:
        match = False
        relativePath = path.abspath(file)[len(dirNameOfLgit)+1:]
        for i, index in enumerate(indexContent):
            if relativePath == index[-1]:
                lsOfTracked.append(i)
                match = True
                break
            elif relativePath == index[-1][:len(relativePath)]:
                print('fatal: not removing \'{}\' recursively without -r'.format(relativePath))
                quit()

        if match is False:
            print('fatal: pathspec \'{}\' did not match any files'.format(relativePath))
            quit()

    lsOfnotAbleRemove = [[], []]
    lsForRemove = list()
    for i in lsOfTracked:
        if indexContent[i][0] != indexContent[i][1]:
            lsOfnotAbleRemove[0].append(i)
        elif indexContent[i][2] != indexContent[i][1]:
            lsOfnotAbleRemove[1].append(i)
        else:
            lsForRemove.append(i)

    if len(lsOfnotAbleRemove[0]) + len(lsOfnotAbleRemove[1]) > 0:
        if len(lsOfnotAbleRemove[0]) > 0:
            print('error: the following file has staged content different from both the\nfile and the HEAD:')
            for i in lsOfnotAbleRemove[0]:
                print('   ', indexContent[i][-1])
            print('(use -f to force removal)')
        if len(lsOfnotAbleRemove[1]) > 0:
            print('error: the following files have changes staged in the index:')
            for i in lsOfnotAbleRemove[1]:
                print('   ', indexContent[i][-1])
            print('(use --cached to keep the file, or -f to force removal)')
        quit()
    else:
        for i in lsForRemove:
            unlink(path.join(dirNameOfLgit, indexContent[i][-1]))


def printReadableTime(time):
    dictOfWeekDay = {'0': 'Sun', '1': 'Mon', '2': 'Tue', '3': 'Wed',
                     '4': 'Thu', '5': 'Fri', '6': 'Sat'}

    x = datetime(int(time[:4]), int(time[4:6]), int(time[6:8]),
                 int(time[8:10]), int(time[10:12]), int(time[12:14]))
    weekday = dictOfWeekDay[x.strftime('%w')]

    print('Date:', weekday, x.strftime('%b %d %H:%M:%S %Y'))


def lgitLog(pathLgit):

    pathLgit = getNearestLgit()
    pathCommits = path.join(pathLgit, 'commits')
    lsOfCommits = listdir(pathCommits)
    lsOfCommits.sort()
    for i, file in enumerate(lsOfCommits[::-1]):
        print('commit', file)
        commit = open(path.join(pathCommits, file), 'r')
        commitContent = commit.read().split('\n')
        print('Author:', commitContent[0])
        printReadableTime(commitContent[1])
        print('\n    ', commitContent[3])
        if i != len(lsOfCommits)-1:
            print('\n')
        commit.close()


def lgitLsFiles(pathLgit):
    pathLgit = getNearestLgit()
    relativeCurrentDir = getcwd()[len(path.dirname(pathLgit))+1:]
    indexFile = open(path.join(pathLgit, 'index'), 'r')
    eachLine = indexFile.readline().split()
    while len(eachLine) > 0:
        if eachLine[-1][:len(relativeCurrentDir)] == relativeCurrentDir:
            relativeTracked = eachLine[-1][len(relativeCurrentDir):]
            if relativeTracked[0] == '/':
                print(relativeTracked[1:])
            else:
                print(relativeTracked)
        eachLine = indexFile.readline().split()
    indexFile.close()


def lgitConfig(author, pathLgit):
    pathConfig = path.join(pathLgit, 'config')
    configFile = open(pathConfig, 'w+')
    configFile.write(author + '\n')
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


def lgitCommit(comment, pathLgit):
    currentTime = datetime.now().strftime('%Y%m%d%H%M%S')
    pathLgit = getNearestLgit()
    pathSnapshots = path.join(pathLgit, 'snapshots')
    snapshotsFile = open(path.join(pathSnapshots, currentTime), 'w+')

    indexContent = list()
    indexFile = open(path.join(pathLgit, 'index'), 'r')
    eachLine = indexFile.readline().split()
    firstime = 1
    while len(eachLine) > 0:
        if firstime != 1:
            snapshotsFile.write('\n')
        else:
            firstime = 0
        snapshotsFile.write(eachLine[2] + ' ' + eachLine[-1])
        if path.exists(eachLine[-1]):
            indexContent.append(eachLine)
        eachLine = indexFile.readline().split()
    indexFile.close()
    snapshotsFile.close()

    for index in indexContent:
        if len(index) == 4:
            index.insert(3, index[2])
        elif len(index) == 5:
            index[3] = index[2]

    indexFile = open(path.join(pathLgit, 'index'), 'w+')
    for i, eachLine in enumerate(indexContent):
        for j, index in enumerate(eachLine):
            if j < 4:
                indexFile.write(index + ' ')
            elif i < len(indexContent)-1:
                indexFile.write(index + '\n')
            else:
                indexFile.write(index)
    indexFile.close()

    pathCommits = path.join(pathLgit, 'commits')
    f = open(path.join(pathCommits, currentTime), 'w+')
    f.write(getUserName())
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


def lgitAdd(srcFiles, pathLgit):
    existedDir = list()

    for dir in srcFiles:
        if not path.exists(dir):
            print('fatal: pathspec \'{}\' did not match any files'.format(dir))
            quit()
        else:
            existedDir.append(dir)

    for dir in existedDir:
        if path.isfile(dir):
            createNewFoderlInObjects(dir, pathLgit)
            updateIndexFile(dir, pathLgit)
        elif path.isdir(dir):
            for root_w, _, files_w in walk(dir, topdown=True):
                for name in files_w:
                    pathFile = path.join(root_w, name)
                    createNewFoderlInObjects(pathFile, pathLgit)
                    updateIndexFile(pathFile, pathLgit)


def printStatus(lsOfAddedFiles, lsOfNotAddedFiles, lsOfDeletedFiles, lsOfTrackedFiles, pathLgit):
    print('On branch master')
    if len(listdir(path.join(pathLgit, 'commits'))) == 0:
        print('\nNo commits yet\n')
    dirNameOfLgit = path.dirname(pathLgit)
    if len(lsOfAddedFiles) + len(lsOfDeletedFiles) > 0:
        print('Changes to be committed:\n  (use \"./lgit.py reset HEAD ...\" to unstage)\n')
        for file in lsOfAddedFiles:
            print('     modified:', file)
        for file in lsOfDeletedFiles:
            print('     deleted:', file)
        print()
    if len(lsOfNotAddedFiles) > 0:
        print('Changes not staged for commit:')
        print('  (use \"./lgit.py add ...\" to update what will be committed)')
        print('  (use \"./lgit.py checkout -- ...\" to discard changes in working directory)\n')
        for file in lsOfNotAddedFiles:
            print('     modified:', file)
        print()
    numOfUntracked = 0
    firstime = 0
    for root_w, _, files_w in walk(dirNameOfLgit, topdown=True):
        for name in files_w:
            relativeDir = path.join(root_w, name)

            if relativeDir[len(dirNameOfLgit)+1:] not in lsOfTrackedFiles and relativeDir[:len(pathLgit)] != pathLgit:
                if firstime == 0:
                    firstime = 1
                    print("Untracked files:")
                    print('  (use \"./lgit.py add <file>...\" to include in what will be committed)\n')
                print('    ', relativeDir[len(dirNameOfLgit)+1:])
                numOfUntracked = 1
    if numOfUntracked == 1:
        print()

    if len(lsOfNotAddedFiles) != 0:
        print('no changes added to commit (use "git add" and/or "git commit -a")')
    elif len(lsOfAddedFiles) + len(lsOfDeletedFiles) == 0:
        if numOfUntracked == 1:
            print('nothing added to commit but untracked files present (use \"./lgit.py add\" to track)')
        else:
            print('nothing to commit, working tree clean')

def lgitStatus(pathLgit):
    cursorPos = 0
    lsOfAddedFiles = list()
    lsOfNotAddedFiles = list()
    lsOfTrackedFiles = list()
    lsOfDeletedFiles = list()
    indexFile = open(path.join(pathLgit, 'index'), 'r+')
    eachLine = indexFile.readline().split()
    while len(eachLine) > 1:
        # rewrite timestamp
        indexFile.seek(cursorPos, 0)
        pathName = path.join(path.dirname(pathLgit), eachLine[-1])
        if path.isfile(pathName):
            mtime = getTime(pathName)
            indexFile.write(mtime)

            hash = ' ' + getHash(pathName)
            indexFile.write(hash)

            lsOfTrackedFiles.append(eachLine[-1])
            if eachLine[2] != eachLine[3]:
                lsOfAddedFiles.append(eachLine[-1])
            if hash[1:] != eachLine[2]:
                lsOfNotAddedFiles.append(eachLine[-1])
        else:
            lsOfDeletedFiles.append(eachLine[-1])

        cursorPos += (139+len(eachLine[-1]))
        indexFile.seek(cursorPos, 0)
        eachLine = indexFile.readline().split()

    indexFile.close()
    printStatus(lsOfAddedFiles, lsOfNotAddedFiles, lsOfDeletedFiles, lsOfTrackedFiles, pathLgit)


def lgitInit():
    lsOfNeededFolders = ['commits', 'objects', 'snapshots']
    lsOfNeededFiles = ['config', 'index']
    reInit = 0

    if path.exists('.lgit'):
        reInit = 1
    else:
        mkdir('.lgit')

    for folder in lsOfNeededFolders:
        if path.exists(path.join('.lgit', folder)):
            reInit = 1
        else:
            mkdir(path.join('.lgit', folder))

    for file in lsOfNeededFiles:
        if path.exists(path.join('.lgit', file)):
            reInit = 1
        else:
            f = open(path.join('.lgit', file), 'x')
            f.close()
            chmod(path.join('.lgit', file), 0o644)

    pathLgit = path.join(getcwd(), '.lgit')
    if reInit:
        print('Git repository already initialized.')


def getNearestLgit():
    currentDir = getcwd()

    while len(currentDir) > 1:
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
            print('fatal: not a git repository (or any of the parent directories)')
    else:
        if args.input[0] == 'init':
            lgitInit()
            pathLgit = getNearestLgit()
        elif args.input[0] == 'add':
            lgitAdd(args.input[1:], pathLgit)
        elif args.input[0] == 'status':
            lgitStatus(pathLgit)
        elif args.input[0] == 'commit':
            lgitCommit(args.mm, pathLgit)
        elif args.input[0] == 'config':
            lgitConfig(args.author, pathLgit)
        elif args.input[0] == 'ls-files':
            lgitLsFiles(pathLgit)
        elif args.input[0] == 'log':
            lgitLog(pathLgit)
        elif args.input[0] == 'rm':
            lgitRemove(args.input[1:], pathLgit)


if __name__ == "__main__":
    main()
