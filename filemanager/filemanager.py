from django.shortcuts import HttpResponse
import json
import subprocess, shlex
from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging
from plogical.processUtilities import ProcessUtilities
from websiteFunctions.models import Websites
from random import randint
from django.core.files.storage import FileSystemStorage
import HTMLParser
import os

class FileManager:
    def __init__(self, request, data):
        self.request = request
        self.data = data


    def ajaxPre(self, status, errorMessage):
        final_dic = {'status': status, 'error_message': errorMessage, 'uploadStatus': status}
        final_json = json.dumps(final_dic)
        return HttpResponse(final_json)

    def returnPathEnclosed(self, path):
        htmlParser = HTMLParser.HTMLParser()
        path = htmlParser.unescape(path)
        return path
        return "'" + path + "'"

    def changeOwner(self,  path):
        domainName = self.data['domainName']
        website = Websites.objects.get(domain=domainName)

        if path.find('..') > -1:
            return self.ajaxPre(0, 'Not allowed to move in this path, please choose location inside home!')

        command = "chown -R " + website.externalApp + ':' + website.externalApp + ' ' + self.returnPathEnclosed(path)
        ProcessUtilities.executioner(command, website.externalApp)

    def listForTable(self):
        try:
            finalData = {}
            finalData['status'] = 1

            domainName = self.data['domainName']
            website = Websites.objects.get(domain=domainName)

            if not self.data['completeStartingPath'].find(self.data['home']) > -1:
                return self.ajaxPre(0, 'Not allowed to browse this path, going back home!')

            command = "ls -la --group-directories-first " + self.returnPathEnclosed(
                self.data['completeStartingPath'])
            output = ProcessUtilities.outputExecutioner(command, website.externalApp).splitlines()

            counter = 0
            for items in output:
                try:
                    currentFile = items.split(' ')
                    currentFile = filter(lambda a: a != '', currentFile)
                    if currentFile[-1] == '.' or currentFile[-1] == '..' or currentFile[0] == 'total':
                        continue

                    if len(currentFile) > 9:
                        fileName = currentFile[8:]
                        currentFile[-1] = " ".join(fileName)

                    dirCheck = 0
                    if currentFile[0][0] == 'd':
                        dirCheck = 1

                    size = str(int(int(currentFile[4]) / float(1024)))
                    lastModified = currentFile[5] + ' ' + currentFile[6] + ' ' + currentFile[7]
                    finalData[str(counter)] = [currentFile[-1], currentFile[-1], lastModified, size, currentFile[0],
                                               dirCheck]
                    counter = counter + 1
                except BaseException, msg:
                    logging.writeToFile(str(msg))

            json_data = json.dumps(finalData)
            return HttpResponse(json_data)

        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def list(self):
        try:
            finalData = {}
            finalData['status'] = 1

            domainName = self.data['domainName']
            website = Websites.objects.get(domain=domainName)

            command = "ls -la --group-directories-first " + self.returnPathEnclosed(
                self.data['completeStartingPath'])
            output = ProcessUtilities.outputExecutioner(command, website.externalApp).splitlines()

            counter = 0
            for items in output:
                try:
                    currentFile = items.split(' ')
                    currentFile = filter(lambda a: a != '', currentFile)

                    if currentFile[-1] == '.' or currentFile[-1] == '..' or currentFile[0] == 'total':
                        continue

                    if len(currentFile) > 9:
                        fileName = currentFile[8:]
                        currentFile[-1] = " ".join(fileName)

                    dirCheck = False
                    if currentFile[0][0] == 'd':
                        dirCheck = True

                    finalData[str(counter)] = [currentFile[-1],
                                               self.data['completeStartingPath'] + '/' + currentFile[-1], dirCheck]
                    counter = counter + 1
                except:
                    continue

            json_data = json.dumps(finalData)
            return HttpResponse(json_data)

        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def createNewFile(self):
        try:
            finalData = {}
            finalData['status'] = 1

            domainName = self.data['domainName']
            website = Websites.objects.get(domain=domainName)

            if self.data['fileName'].find('..') > -1:
                return self.ajaxPre(0, 'Not allowed to move in this path, please choose location inside home!')


            command = "touch " + self.returnPathEnclosed(self.data['fileName'])
            ProcessUtilities.executioner(command, website.externalApp)

            self.changeOwner(self.returnPathEnclosed(self.data['fileName']))

            json_data = json.dumps(finalData)
            return HttpResponse(json_data)

        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def createNewFolder(self):
        try:
            finalData = {}
            finalData['status'] = 1
            domainName = self.data['domainName']
            website = Websites.objects.get(domain=domainName)

            command = "mkdir " + self.returnPathEnclosed(self.data['folderName'])
            ProcessUtilities.executioner(command, website.externalApp)

            self.changeOwner(self.returnPathEnclosed(self.data['folderName']))

            json_data = json.dumps(finalData)
            return HttpResponse(json_data)

        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def deleteFolderOrFile(self):
        try:
            finalData = {}
            finalData['status'] = 1

            domainName = self.data['domainName']
            website = Websites.objects.get(domain=domainName)

            for item in self.data['fileAndFolders']:
                command = 'rm -rf ' + self.returnPathEnclosed(self.data['path'] + '/' + item)
                ProcessUtilities.executioner(command, website.externalApp)

            json_data = json.dumps(finalData)
            return HttpResponse(json_data)

        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def copy(self):
        try:

            finalData = {}
            finalData['status'] = 1

            domainName = self.data['domainName']
            website = Websites.objects.get(domain=domainName)

            if not self.data['newPath'].find(self.data['home']) > -1:
                return self.ajaxPre(0, 'Not allowed to move in this path, please choose location inside home!')

            command = 'mkdir ' + self.returnPathEnclosed(self.data['newPath'])
            ProcessUtilities.executioner(command, website.externalApp)

            for item in self.data['fileAndFolders']:
                command = 'cp -R ' + self.returnPathEnclosed(self.data['basePath'] + '/' + item) + ' ' + self.returnPathEnclosed(self.data['newPath'] + '/' + item)
                ProcessUtilities.executioner(command, website.externalApp)

            self.changeOwner(self.data['newPath'])

            json_data = json.dumps(finalData)
            return HttpResponse(json_data)

        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def move(self):
        try:

            finalData = {}
            finalData['status'] = 1
            domainName = self.data['domainName']
            website = Websites.objects.get(domain=domainName)

            if not self.data['newPath'].find(self.data['home']) > -1:
                return self.ajaxPre(0, 'Not allowed to move in this path, please choose location inside home!')

            command = 'mkdir ' + self.returnPathEnclosed(self.data['newPath'])
            ProcessUtilities.executioner(command, website.externalApp)

            for item in self.data['fileAndFolders']:
                command = 'mv ' + self.returnPathEnclosed(self.data['basePath'] + '/' + item) + ' ' + self.returnPathEnclosed(self.data['newPath'] + '/' + item)
                ProcessUtilities.executioner(command, website.externalApp)

            self.changeOwner(self.data['newPath'])

            json_data = json.dumps(finalData)
            return HttpResponse(json_data)

        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def rename(self):
        try:

            finalData = {}
            finalData['status'] = 1
            domainName = self.data['domainName']
            website = Websites.objects.get(domain=domainName)

            if self.data['newFileName'].find('..') > -1:
                return self.ajaxPre(0, 'Not allowed to move in this path, please choose location inside home!')


            command = 'mv ' + self.returnPathEnclosed(self.data['basePath'] + '/' + self.data['existingName']) + ' ' + self.returnPathEnclosed(self.data['basePath'] + '/' + self.data['newFileName'])
            ProcessUtilities.executioner(command, website.externalApp)

            self.changeOwner(self.data['basePath'] + '/' + self.data['newFileName'])

            json_data = json.dumps(finalData)
            return HttpResponse(json_data)

        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def readFileContents(self):
        try:

            finalData = {}
            finalData['status'] = 1
            domainName = self.data['domainName']
            website = Websites.objects.get(domain=domainName)

            command = 'cat ' + self.returnPathEnclosed(self.data['fileName'])
            finalData['fileContents'] = ProcessUtilities.outputExecutioner(command, website.externalApp)

            json_data = json.dumps(finalData)
            return HttpResponse(json_data)

        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def writeFileContents(self):
        try:

            finalData = {}
            finalData['status'] = 1
            tempPath = "/home/cyberpanel/" + str(randint(1000, 9999))
            self.data['home'] = '/home/%s' % (self.data['domainName'])

            domainName = self.data['domainName']
            website = Websites.objects.get(domain=domainName)

            writeToFile = open(tempPath, 'w')
            writeToFile.write(self.data['fileContent'])
            writeToFile.close()

            if os.path.islink(self.data['fileName']):
                return self.ajaxPre(0, 'File exists and is symlink.')

            if not self.data['fileName'].find(self.data['home']) > -1:
                return self.ajaxPre(0, 'Not allowed to move in this path, please choose location inside home!')

            command = 'mv ' + tempPath + ' ' + self.returnPathEnclosed(self.data['fileName'])
            ProcessUtilities.executioner(command)

            command = 'chown %s:%s %s' % (website.externalApp, website.externalApp, self.data['fileName'])
            ProcessUtilities.executioner(command)

            self.changeOwner(self.data['fileName'])

            json_data = json.dumps(finalData)
            return HttpResponse(json_data)

        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def upload(self):
        try:

            finalData = {}
            finalData['uploadStatus'] = 1
            finalData['answer'] = 'File transfer completed.'

            myfile = self.request.FILES['file']
            fs = FileSystemStorage()
            filename = fs.save(myfile.name, myfile)
            finalData['fileName'] = fs.url(filename)

            if not self.data['completePath'].find(self.data['home']) > -1:
                return self.ajaxPre(0, 'Not allowed to move in this path, please choose location inside home!')

            command = 'mv ' + self.returnPathEnclosed('/home/cyberpanel/media/' + myfile.name) + ' ' + self.returnPathEnclosed(self.data['completePath'] + '/' + myfile.name)
            ProcessUtilities.executioner(command)

            domainName = self.data['domainName']
            website = Websites.objects.get(domain=domainName)

            command = 'chown %s:%s %s' % (website.externalApp, website.externalApp, self.data['completePath'] + '/' + myfile.name)
            ProcessUtilities.executioner(command)

            self.changeOwner(self.data['completePath'] + '/' + myfile.name)

            json_data = json.dumps(finalData)
            return HttpResponse(json_data)

        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def extract(self):
        try:

            finalData = {}
            finalData['status'] = 1

            domainName = self.data['domainName']
            website = Websites.objects.get(domain=domainName)

            if not self.data['extractionLocation'].find(self.data['home']) > -1:
                return self.ajaxPre(0, 'Not allowed to move in this path, please choose location inside home!')

            if self.data['extractionType'] == 'zip':
                command = 'unzip -o ' + self.returnPathEnclosed(self.data['fileToExtract']) + ' -d ' + self.returnPathEnclosed(self.data['extractionLocation'])
            else:
                command = 'tar -xf ' + self.returnPathEnclosed(self.data['fileToExtract']) + ' -C ' + self.returnPathEnclosed(self.data['extractionLocation'])

            ProcessUtilities.executioner(command, website.externalApp)

            self.changeOwner(self.data['extractionLocation'])

            json_data = json.dumps(finalData)
            return HttpResponse(json_data)

        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def compress(self):
        try:

            finalData = {}
            finalData['status'] = 1
            domainName = self.data['domainName']
            website = Websites.objects.get(domain=domainName)


            if self.data['compressionType'] == 'zip':
                compressedFileName = self.returnPathEnclosed(self.data['basePath'] + '/' + self.data['compressedFileName'] + '.zip')
                command = 'zip -r ' + compressedFileName + ' '
            else:
                compressedFileName = self.returnPathEnclosed(
                    self.data['basePath'] + '/' + self.data['compressedFileName'] + '.tar.gz')
                command = 'tar -czvf ' + compressedFileName + ' '

            for item in self.data['listOfFiles']:
                command = '%s%s ' % (command, self.returnPathEnclosed(item))


            finalCommand = 'cd %s && %s' % (self.data['basePath'], command)

            ProcessUtilities.executioner(finalCommand, website.externalApp)

            self.changeOwner(self.data['compressedFileName'])

            json_data = json.dumps(finalData)
            return HttpResponse(json_data)

        except BaseException, msg:
            return self.ajaxPre(0, str(msg))

    def changePermissions(self):
        try:

            finalData = {}
            finalData['status'] = 1
            domainName = self.data['domainName']
            website = Websites.objects.get(domain=domainName)

            if self.data['recursive'] == 1:
                command = 'chmod -R ' + self.data['newPermissions'] + ' ' + self.returnPathEnclosed(
                    self.data['basePath'] + '/' + self.data['permissionsPath'])
            else:
                command = 'chmod ' + self.data['newPermissions'] + ' ' + self.returnPathEnclosed(
                    self.data['basePath'] + '/' + self.data['permissionsPath'])


            ProcessUtilities.executioner(command, website.externalApp)

            json_data = json.dumps(finalData)
            return HttpResponse(json_data)

        except BaseException, msg:
            return self.ajaxPre(0, str(msg))