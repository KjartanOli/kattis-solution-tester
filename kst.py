#!/usr/bin/python3

import sys, requests, subprocess, zipfile, io, os
from enum import Enum, auto

class RunntimeErrorException(Exception):
	"""Raise if the test function encounters a Runntime Error."""
	def __init__(this, message, *args):
		super(RunntimeErrorException, this).__init__(message, *args)

class CompileErrorExceptinon(Exception):
	"""Raise if the compile function encounters a Compile Error."""
	def __init__(this, message, *args):
		super(CompileErrorExceptinon, this).__init__(message, *args)

class Sample:
	"""Container for sample input and output."""
	def __init__(this, sampleInput, sampleOutput):
		this.input = sampleInput
		this.output = sampleOutput

class Cache:
	"""Cache management class."""
	def __init__(this, fileName):
		this.file = fileName

	def contains(this, subdomain, problem):
		"""Check if the cache contains the specified problem."""
		dir = subdomain + '/' + problem + '/'
		if this.file not in os.listdir():
			return False
		with zipfile.ZipFile(this.file, 'r') as cache:
			if any (dir in name for name in cache.namelist()):
				return True
		return False

	def add(this, fileName, content):
		"""Add a file to the cache."""
		with zipfile.ZipFile(this.file, 'a') as cache:
			cache.writestr(fileName, content)

	def load(this, subdomain, problem):
		"""Load a problem from the cache."""
		samples = []
		dir = subdomain + '/' + problem + '/'
		tmp = ""
		with zipfile.ZipFile(this.file, 'r') as cache:
			for name in filter(lambda name: dir in name, cache.namelist()):
				if not os.path.isdir(name):
					with cache.open(name) as file:
						if ".in" in name:
							tmp = file.read().decode("utf-8").strip()
						else:
							samples.append(Sample(tmp, file.read().decode("utf-8").strip()))
		return samples

class FileType(Enum):
	CPP = auto()
	PYTHON = auto()
	C = auto()
	JAVA = auto()
	JS = auto()

def version():
	"""Print version information."""
	sys.stdout.write("kst (Kattis Solution Tester) 2.0.0\n\nWritten by Kjartan Óli Ágústsson\n")

def help():
	"""Print help."""
	sys.stdout.write("Usage: kst [OPTIONS] PROBLEM_ID SOLUTION\nCompare the output of SOLUTION to the sample outputs provided for the problem\n")

def download_samples(url):
	"""Download samples for the current problem."""
	files = requests.get(url)
	samples = []
	tmp = ""
	with zipfile.ZipFile(io.BytesIO(files.content)) as zip:
		for zipinfo in zip.infolist():
			with zip.open(zipinfo) as file:
				content = file.read().decode("utf-8").strip()
				cache.add(subdomain + '/' + problem + '/' + file.name, content)
				if ".in" in file.name:
					tmp = content
				else:
					samples.append(Sample(tmp, content))
	return samples

def test(testNum, sample, solution, interpreter):
	"""Test the given solution against the given sample."""
	if verbose:
		sys.stdout.write("Testing Sample Input " + str(testNum + 1) + ":\nInput:\n" + sample.input + "\nOutput:\n")

	proc = subprocess.Popen([interpreter, solution], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out, err = proc.communicate(input=sample.input.encode())

	out = out.decode("utf-8").strip()
	err = err.decode("utf-8")

	if err != "":
		raise RunntimeErrorException(err)
	else:
		if verbose:
			sys.stdout.write(out + "\nExpected output:\n" + sample.output + "\n")

		if out == sample.output:
			return True
		else:
			return False

def get_fileType(file, verbose = False):
	"""Get the filetype of the solution given."""
	if verbose:
		sys.stdout.write("File type is: ")
		if file[-3:] == ".py":
			sys.stdout.write("Python\n")
			return FileType.PYTHON
		elif file[-4:] == ".cpp":
			sys.stdout.write("C++\n")
			return FileType.CPP
		elif file[-2:] == ".c":
			sys.stdout.write("C\n")
			return FileType.C
		elif file[-5:] == ".java":
			sys.stdout.write("Java\n")
			return FileType.JAVA
		elif file[-3:] == ".js":
			sys.stdout.write("JavaScript\n")
			return FileType.JS

	else:
		if file[-3:] == ".py":
			return FileType.PYTHON
		elif file[-4:] == ".cpp":
			return FileType.CPP
		elif file[-2:] == ".c":
			return FileType.C
		elif file[-5:] == ".java":
			return FileType.JAVA
		elif file[-3:] == ".js":
			return FileType.JS

def is_compiled(fileType):
	"""Check if the filetype of the solution requires compiling."""
	return fileType is FileType.C or fileType is FileType.CPP or fileType is FileType.JAVA

def set_interpreter(fileType):
	"""Find the appropriate interpreter for the solutions filetype."""
	if verbose:
		sys.stdout.write("Setting interpreter to: ")
		if fileType is FileType.PYTHON:
			if p2:
				sys.stdout.write("python2\n\n")
				return "python2"
			if p3:
				sys.stdout.write("python3\n\n")
				return "python3"
			sys.stdout.write("python\n\n")
			return "python"

		if fileType is FileType.JS:
			sys.stdout.write("node\n\n")
			return "node"

	else:
		if fileType is FileType.PYTHON:
			if p2:
				return "python2"
			if p3:
				return "python3"
			return "python"
		if fileType is FileType.JS:
			return "node"

def set_compiler(fileType):
	"""Find the appropriate compiler for the solutions filetype."""
	if verbose:
		sys.stdout.write("Setting compiler to: ")
		if fileType is FileType.C:
			sys.stdout.write("gcc\n\n")
			return "gcc"
		if fileType is FileType.CPP:
			sys.stdout.write("g++\n\n")
			return "g++"
		if fileType is FileType.JAVA:
			sys.stdout.write("javac\n\n")
			return "javac"
	else:
		if fileType is FileType.C:
			return "gcc"
		if fileType is FileType.CPP:
			return "g++"
		if fileType is FileType.JAVA:
			return "javac"

def compile(file):
	"""Compile the solution."""
	global compiler
	if compiler == "":
		compiler = set_compiler(get_fileType(file))
	if verbose:
		sys.stdout.write("Compiling\n")

	proc = subprocess.Popen([compiler, file], stderr=subprocess.PIPE)

	err = proc.communicate()[1].decode("utf-8")

	if err != "":
		raise CompileErrorExceptinon(err)

def incompatable_python():
	"""Print an error indicating incompatable options."""
	sys.stderr.write("Incompatable options --python2 and --python3\n")

def main(argc, argv):
	global p2, p3, verbose, compiler, problem, subdomain
	skip = False
	for i, arg in enumerate(argv):
		if skip:
			skip = False
			continue
		else:
			if arg == "-ice" or arg == "--iceland":
				subdomain = "iceland"
			elif arg == "--open":
				subdomain = "open"
			elif arg == "-s" or arg == "--subdomain":
				subdomain = argv[i + 1]
				skip = True
			elif arg == "-p2" or arg == "--python2":
				if p3:
					incompatable_python()
					return 1
				p2 = True
			elif arg == "-p3" or arg == "--python3":
				if p2:
					incompatable_python()
					return 1
				p3 = True
			elif arg == "-c" or arg == "--compiler":
				compiler = argv[i + 1]
				skip = True
			elif arg == "-v" or arg == "--verbose":
				verbose = True
			elif arg == "-V" or arg == "--version":
				version()
				return 0
			elif arg == "-h" or arg == "--help":
				help()
				return 0
			elif i == argc - 2:
				problem = arg
			elif i == argc - 1:
				solution = arg

	if subdomain == "iceland":
		url = "https://" + subdomain + ".kattis.com/problems/iceland." + problem + "/file/statement/samples.zip"
	else:
		url = "https://" +  subdomain + ".kattis.com/problems/" + problem + "/file/statement/samples.zip"

	if not cache.contains(subdomain, problem):
		samples = download_samples(url)
	else:
		samples = cache.load(subdomain, problem)

	fileType = get_fileType(solution, True if verbose else False)

	if is_compiled(fileType):
		try:
			compile(solution)
			if fileType is FileType.JAVA:
				interpreter = "java"
				solution = solution[:-5]
			else:
				interpreter = "./a.out"
		except CompileErrorExceptinon as e:
			if verbose:
				sys.stderr.write(str(e) + '\n')
			else:
				sys.stderr.write("Compile Error\n")
			return 2
	else:
		interpreter = set_interpreter(fileType)

	l = len(samples) - 1
	for i, sample in enumerate(samples):
		try:
			res = "Passed" if test(i, sample, solution, interpreter) else "Failed"
			sys.stdout.write("Test " + str(i + 1) + ": " + res + ("\n\n" if i < l and verbose else '\n'))
		except RunntimeErrorException as e:
			if verbose:
				sys.stderr.write(str(e) + '\n')
			else:
				sys.stderr.write("Test " + str(i + 1) + ": Runntime Error\n")
			#sys.stdout.write("Excpected output:\n" + sample.output + '\n')

	return 0

p2 = False
p3 = False
verbose = False
compiler = ""
problem = ""
subdomain = ""
cache = Cache(".cache")

sys.exit(main(len(sys.argv), sys.argv))
