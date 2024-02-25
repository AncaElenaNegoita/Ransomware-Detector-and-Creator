import time
import threading
import os

import ctypes
from ctypes import Structure, POINTER, WINFUNCTYPE, windll, c_uint32, c_uint64, c_uint16, c_uint8, c_void_p, c_wchar_p, c_bool


processesPid = [0 for _ in range(50000)]
processInitFile = [list() for _ in range(50000)]
parentsPid = [list() for _ in range(50000)]

class ProcessStartNotification(Structure):
	_fields_ = [
		("processID", c_uint32),
		("parentProcessID", c_uint32),
		("processPath", c_wchar_p),
		("parentProcessPath", c_wchar_p),
	]

class ProcessStopNotification(Structure):
	_fields_ = [
		("processID", c_uint32),
		("parentProcessID", c_uint32),
	]

class CreateFilePreNotification(Structure):
	_fields_ = [
		("processID", c_uint32),
		("threadID", c_uint32),
		("filePath", c_wchar_p),
		("desiredAccess", c_uint32),
		("shareAccess", c_uint16),
		("fileAttributes", c_uint16),
		("createDisposition", c_uint32),
		("createOptions", c_uint32),
		("hasReadAccess", c_uint8),
		("hasWriteAccess", c_uint8),
		("hasDeleteAccess", c_uint8),
	]

class CreateFilePostNotification(Structure):
	_fields_ = [
		("processID", c_uint32),
		("threadID", c_uint32),
		("filePath", c_wchar_p),
		("fileId", c_uint64),
		("createStatus", c_uint32),
		("desiredAccess", c_uint32),
		("shareAccess", c_uint16),
		("fileAttributes", c_uint16),
		("createDisposition", c_uint32),
		("createOptions", c_uint32),
		("hasReadAccess", c_uint8),
		("hasWriteAccess", c_uint8),
		("hasDeleteAccess", c_uint8),
		("fileSize", c_uint64),
		("fileContent", c_void_p),
	]

class CloseFileNotification(Structure):
	_fields_ = [
		("processID", c_uint32),
		("threadID", c_uint32),
		("filePath", c_wchar_p),
		("fileId", c_uint64),
		("newFile", c_uint8),
		("isCopied", c_uint8),
		("isWritten", c_uint8),
		("fileSize", c_uint64),
		("fileContent", c_void_p),
	]

class SetFileInfoNotification(Structure):
	_fields_ = [
		("processID", c_uint32),
		("threadID", c_uint32),
		("oldFilePath", c_wchar_p),
		("newFilePath", c_wchar_p),
		("fileId", c_uint64),
	]

class NotificationType:
	INVALID = 0
	PROCESS_START = 1
	PROCESS_STOP = 2
	CREATE_FILE_PRE = 3
	CREATE_FILE_POST = 4
	CLOSE_FILE = 5
	SET_FILE_INFO = 6
	TEST_START = 7
	TEST_END = 8

class Notification(Structure):
	_fields_ = [
		("type", c_uint32),
		("processStart", ProcessStartNotification),
		("processStop", ProcessStopNotification),
		("createFilePre", CreateFilePreNotification),
		("createFilePost", CreateFilePostNotification),
		("closeFile", CloseFileNotification),
		("setFileInfo", SetFileInfoNotification),
	]

CallbackFunc = WINFUNCTYPE(None, POINTER(Notification), c_void_p)

EO11Init_t = WINFUNCTYPE(c_uint32, CallbackFunc, c_void_p)
EO11Uninit_t = WINFUNCTYPE(None)
EO11AddFolderWatch_t = WINFUNCTYPE(c_uint32, c_wchar_p)
EO11NotifyDetectionOnPID_t = WINFUNCTYPE(None, c_uint32)

# Load the DLL
EO11_dll = windll.LoadLibrary("C:\\Users\\EO11\\Desktop\\EO11\\EO11.dll")

# Define the function prototypes
EO11Init = EO11Init_t(("EO11Init", EO11_dll))
EO11Uninit = EO11Uninit_t(("EO11Uninit", EO11_dll))
EO11AddFolderWatch = EO11AddFolderWatch_t(("EO11AddFolderWatch", EO11_dll))
EO11NotifyDetectionOnPID = EO11NotifyDetectionOnPID_t(("EO11NotifyDetectionOnPID", EO11_dll))

# Initialize the library
@WINFUNCTYPE(None, POINTER(Notification), c_void_p)
def callback(notification, user_data):
	if notification.contents.type == NotificationType.PROCESS_START:
		pid = notification.contents.processStart.processID
		parent_pid = notification.contents.processStart.parentProcessID
		while len(processInitFile) <= parent_pid:
			parentsPid.append(list())
		parentsPid[parent_pid].append(pid)
		process_path = notification.contents.processStart.processPath
		parent_process_path = notification.contents.processStart.parentProcessPath

	elif notification.contents.type == NotificationType.CREATE_FILE_POST:
		pid = notification.contents.createFilePost.processID
		file_size = notification.contents.createFilePost.fileSize
		while len(processInitFile) <= pid:
			processInitFile.append(list())
		processInitFile[pid].append(file_size)
		file_path = notification.contents.createFilePost.filePath
		processInitFile[pid].append(file_path)
		hasRead = notification.contents.createFilePost.hasReadAccess
		processInitFile[pid].append(hasRead)
		if hasRead:
			processesPid[pid] += 1
		hasWrite = notification.contents.createFilePost.hasWriteAccess
		processInitFile[pid].append(hasWrite)
		if hasWrite:
			processesPid[pid] += 1
		hasDelete = notification.contents.createFilePost.hasDeleteAccess
		processInitFile[pid].append(hasDelete)
		if hasDelete:
			processesPid[pid] += 1
		file_content = notification.contents.createFilePost.fileContent
		processInitFile[pid].append(file_content)

	elif notification.contents.type == NotificationType.CLOSE_FILE:
		process_pid = notification.contents.closeFile.processID
		file_size = notification.contents.closeFile.fileSize
		file_path = notification.contents.closeFile.filePath
		isCopied = notification.contents.closeFile.isCopied
		isWritten = notification.contents.closeFile.isWritten
		file_content = notification.contents.closeFile.fileContent

		# Crypt without deleting
		if file_content != processInitFile[pid][5] and file_path == processInitFile[1]:
			processesPid[pid] += 1
		# Crypt and delete
		if file_path is None and isCopied:
			processesPid[pid] += 1
		# Copy and crypt
		if file_path != processInitFile[pid][1] and isCopied:
			processesPid[pid] += 1

	elif notification.contents.type == NotificationType.PROCESS_STOP:
		pid = notification.contents.processStop.processID
		if processesPid[pid] > 3:
			EO11NotifyDetectionOnPID(pid)
			secondaryPid = []
			secondaryPid.append(pid)
			for p in secondaryPid:
				if p != pid:
					EO11NotifyDetectionOnPID(p)
				for i in parentsPid[p]:
					secondaryPid.append(i)
				secondaryPid[p] = 0
		processesPid[pid] = 0
	return 0

EO11Init(callback, None)

while True:
	pass