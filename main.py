from win32file import CreateFile, SetFileTime, GetFileTime, CloseHandle
from win32file import GENERIC_READ, GENERIC_WRITE, OPEN_EXISTING
from pywintypes import Time
import os
import sys
import time
import random
import pyexiv2
from PIL import Image


def getAllFiles(path, file_list):
    dir_list = os.listdir(path)
    for x in dir_list:
        new_x = os.path.join(path, x)
        if os.path.isdir(new_x):
            getAllFiles(new_x, file_list)
        else:
            file_list.append(new_x)

    return file_list


def modifyFileTime(filePath, createTime, modifyTime, accessTime, offset):
    """
    用来修改任意文件的相关时间属性，时间格式：YYYY-MM-DD HH:MM:SS 例如：2019-02-02 00:01:02
    :param filePath: 文件路径名
    :param createTime: 创建时间
    :param modifyTime: 修改时间
    :param accessTime: 访问时间
    :param offset: 时间偏移的秒数,tuple格式，顺序和参数时间对应
    """
    try:
        # 时间格式
        format = "%Y-%m-%d %H:%M:%S"
        cTime_t = timeOffsetAndStruct(createTime, format, offset[0])
        mTime_t = timeOffsetAndStruct(modifyTime, format, offset[1])
        aTime_t = timeOffsetAndStruct(accessTime, format, offset[2])

        fh = CreateFile(filePath, GENERIC_READ | GENERIC_WRITE,
                        0, None, OPEN_EXISTING, 0, 0)

        createTimes, accessTimes, modifyTimes = GetFileTime(fh)

        createTimes = Time(time.mktime(cTime_t))
        accessTimes = Time(time.mktime(aTime_t))
        modifyTimes = Time(time.mktime(mTime_t))
        SetFileTime(fh, createTimes, accessTimes, modifyTimes)
        CloseHandle(fh)

        return 0
    except:
        return 1


def timeOffsetAndStruct(times, format, offset):
    return time.localtime(time.mktime(time.strptime(times, format)) + offset)


def setFileCreateTime(fileName):
    format = "%Y-%m-%d %H:%M:%S"
    filestat = os.stat(fileName)
    fileat = time.strftime(format, time.localtime(filestat.st_atime))
    filemt = time.strftime(format, time.localtime(filestat.st_mtime))
    filect = time.strftime(format, time.localtime(filestat.st_ctime))

    if filestat.st_mtime < filestat.st_ctime:
        filect_pre = filect
        filect = filemt
        fileat = filemt

        # 偏移的秒数
        offset = (random.randint(1, 100), random.randint(
            1, 100), random.randint(1, 100))

        result = modifyFileTime(fileName, filect, filemt, fileat, offset)

        if result == 0:
            print('文件[%s]修改时间戳完成. [%s]-->[%s]' %
                  (fileName, filect_pre, filect))
        if result == 1:
            print('文件[%s]修改时间戳失败.' % (fileName))


def setImgDate(fileName):
    endwith = os.path.splitext(fileName)[1].lower()
    if not endwith == '.png' and not endwith == '.jpg':
        return

    if endwith == '.png':
        im = Image.open(fileName)
        im = im.convert('RGB')

        fileName_pre = fileName
        fileName = os.path.splitext(fileName)[0] + '.jpg'

        im.save(fileName, quality=100)
        im.close()

        # 处理文件时间
        filestat = os.stat(fileName_pre)

        filetimemin = min(filestat.st_atime,
                          filestat.st_mtime, filestat.st_ctime)
        filetimemin = time.localtime(filetimemin)
        filetimemin = time.strftime("%Y-%m-%d %H:%M:%S", filetimemin)

        modifyFileTime(fileName, filetimemin, filetimemin,
                       filetimemin, (0, 0, 0))

        os.remove(fileName_pre)

        # 后来发现ios这里这么处理是不行的.
        # CREATION_TIME = 'Creation Time'
        # # 处理png
        # filestat = os.stat(fileName)
        # filect = time.strftime("%Y:%m:%d %H:%M:%S",
        #                        time.localtime(filestat.st_mtime))

        # targetImage = PngImageFile(fileName)

        # if not CREATION_TIME in targetImage.text:
        #     metadata = PngInfo()
        #     metadata.add_text(CREATION_TIME, filect)
        #     targetImage.save(fileName, pnginfo=metadata)
    # elif endwith == '.jpg' or endwith == '.jpeg':

    # print(fileName)

    # 所有文件均当做jpg处理
    EXIF_IMAGE_DATE_TIME_ORIGINAL = 'Exif.Image.DateTimeOriginal'
    EXIF_PHOTO_DATE_TIME_ORIGINAL = 'Exif.Photo.DateTimeOriginal'
    EXIF_PHOTO_DATE_TIME_DIGITIZED = 'Exif.Photo.DateTimeDigitized'

    EXIF_LIST = ["Exif.Image.DateTimeOriginal",
                 "Exif.Photo.DateTimeOriginal",
                 "Exif.Photo.DateTimeDigitized"]

    img = None

    try:
        img = pyexiv2.Image(fileName)
    except RuntimeError as err:
        print('RuntimeError: ', err)

    if img == None:
        img = pyexiv2.Image(fileName, encoding='GBK')

    exif_data = img.read_exif()

    filestat = os.stat(fileName)
    filect = time.strftime("%Y:%m:%d %H:%M:%S",
                           time.localtime(filestat.st_mtime))

    # 这里有一个简单策略, 先判断文件中是否包含任意exif信息, 如果包含则不修改
    flag = False
    for exif_item in EXIF_LIST:
        if exif_item in exif_data:
            flag = True
            break

    if flag == False:
        for exif_item in EXIF_LIST:
            if not exif_item in exif_data:
                exif_data[exif_item] = filect

        # 保存修改
        img.modify_exif(exif_data)

    img.close()

    filetimemin = min(filestat.st_atime,
                      filestat.st_mtime, filestat.st_ctime)

    filetimemin = time.localtime(filetimemin)

    filetimemin = time.strftime("%Y-%m-%d %H:%M:%S", filetimemin)

    modifyFileTime(fileName, filetimemin, filetimemin,
                   filetimemin, (0, 0, 0))

    return


if __name__ == "__main__":
    files = []

    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        path = sys.argv[1]
    else:
        path = os.path.dirname(os.path.realpath(sys.argv[0]))

    print('需要转换的路径为: ' + path)

    getAllFiles(path, files)

    for filename in files:
        setImgDate(filename)
