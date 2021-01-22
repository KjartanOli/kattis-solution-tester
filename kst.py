#! /usr/bin/python3

# kst (Kattis Solution Tester), compare the output of SOLUTION to the expected
# output of the specified problem on kattis.com

# Copyright (C) 2020  Ágústsson, Kjartan Óli
# Author: Ágústsson, Kjartan Óli <kjartanoli@protonmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
		# if the cache doesn't exist the problem can't be in it
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

	def clear(this):
		"""Clear the cache."""
		# if the cache exists
		if this.file in os.listdir():
			# remove it
			os.remove(this.file)

	def load(this, subdomain, problem):
		"""Load a problem from the cache."""
		samples = []
		dir = f"{subdomain}/{problem}/"
		tmp = ""
		with zipfile.ZipFile(this.file, 'r') as cache:
			for name in filter(lambda name: dir in name, cache.namelist()):
				if not os.path.isdir(name):
					with cache.open(name) as file:
						if ".in" in name:
							# store the content of the file to append to the list of samples along with their output
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

def main(argc, argv):
	global python2, python3, verbose, compiler, noCache
	cacheOnly = False
	# Should you skip the current argument
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
				# the next argument is a part of the current flag
				skip = True
			elif arg == "-p2" or arg == "--python2":
				if python3:
					incompatable_python()
					return 1
				else:
					python2 = True
			elif arg == "-p3" or arg == "--python3":
				if python2:
					incompatable_python()
					return 1
				else:
					python3 = True
			elif arg == "-c" or arg == "--compiler":
				compiler = argv[i + 1]
				# the next argument is a part of the current flag
				skip = True
			elif arg == "-v" or arg == "--verbose":
				verbose = True
			elif arg == "-V" or arg == "--version":
				# print version inforation and exit
				version()
				return 0
			elif arg == "-h" or arg == "--help":
				# print help and exit
				help()
				return 0
			elif arg == "-nc" or arg == "--no-cache":
				# don't add the problem to the cache
				noCache = True
			elif arg == "-cc" or arg == "--clear-cache":
				# clear the cache and exit
				cache.clear()
				return 0
			elif arg == "-co" or arg  == "--cache-only":
				cacheOnly = True
			# the second last argument should be the id of the problem
			elif i == argc - 2:
				problem = arg
			# the last argument should bo the path to the users solution
			elif i == argc - 1:
				solution = arg

	if not cache.contains(subdomain, problem):
		if not noCache:
			samples = download_samples(subdomain, problem)
		else:
			sys.stderr.write("Problem samples not in cache\n")
			return 3

	else:
		if not cacheOnly:
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

	if is_compiled(fileType):
		if fileType is FileType.JAVA:
			# javac creates a file with the same name as the java file and the .class extention
			clean_up(solution[:-5] + ".class")
		else:
			# the default output of gcc and g++ is a.out
			clean_up("a.out")

	return 0

def version():
	"""Print version information."""
	sys.stdout.write("kst (Kattis Solution Tester) 2.1.0 Copyright (C) " + year +
		' ' + author + "\nThis program comes with ABSOLUTELY NO WARRANTY. This is " +
		"free software,\nand you are welcome to redistribute it\n")

def help():
	"""Print help."""
	# indent for options listing
	indent = "  "
	sys.stdout.write(f"Usage: kst [OPTIONS] PROBLEM SOLUTION\nCompare the output" +
	f" of SOLUTION to the sample outputs provided for the problem\nExample: kst -ice" +
	f"budarkassi1 budarkassi1.py\nDomain control:\n{indent}-ice, --iceland\t\t" +
	f"Set the subdomain to iceland\n{indent}\t--open\t\t\tSet the subdomain to" +
	f" open\n{indent}-s,\t--subdomain=SUBDOMAIN\tSet subdomain to SUBDOMAIN\n\n" +
	f"(Setting the subdomain to 'iceland' automaticly adds the 'iceland.' in" +
	f" all iceland problems to the problem's id)\n\n Testing control:\n{indent}-p2," +
	f"\t--python2\t\tSpecify that the solution should be tested with python2\n{indent}"
	f"-p3,\t--python3\t\tSpecify that the solution should be tested with python3\n" +
	f"{indent}-c,\t--compiler=COMPILER\tSpecify that the solution should be compiled" +
	f"using COMPILER\n\n Cache control:\n{indent}-nc,\t--no-cache\t\tDon't add the" +
	f"samples for this problem to the cache\n{indent}-cc,\t--clear-cache \t\tClear" +
	f" the cache and exit\n{indent}-co,\t--cache-only\t\tOnly use samples from" +
	f" the cache\n\nError codes:\n\t1\t\tIncompatable options --python2" +
	f" and --python3\n\nkst (Kattis Solution Tester) Copyright (C) {year} {author}" +
	f"\nThis program comes with ABSOLUTELY NO  WARRANTY. This is free software,\nand" +
	f" you are welcome to redistribute it\n")

def get_url(subdomain, problem):
	"""Get the url for the problem"""
	if subdomain == "iceland":
		return "https://" + subdomain + ".kattis.com/problems/iceland." + problem + "/file/statement/samples.zip"
	else:
		return "https://" +  subdomain + ".kattis.com/problems/" + problem + "/file/statement/samples.zip"

def download_samples(subdomain, problem):
	"""Download samples for the current problem."""
	files = requests.get(get_url(subdomain, problem))
	samples = []
	tmp = ""
	with zipfile.ZipFile(io.BytesIO(files.content)) as zip:
		for zipinfo in zip.infolist():
			with zip.open(zipinfo) as file:
				content = file.read().decode("utf-8").strip()
				if not noCache:
					cache.add(subdomain + '/' + problem + '/' + file.name, content)
				if ".in" in file.name:
					# store the content of the file to append to the list of samples along with their output
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
	err = err.decode("utf-8").strip()

	if err != "":
		raise RunntimeErrorException(err)
	else:
		if verbose:
			sys.stdout.write(out + "\nExpected output:\n" + sample.output + "\n")

		# compare the output to the expected output
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
			if python2:
				sys.stdout.write("python2\n\n")
				return "python2"
			if python3:
				sys.stdout.write("python3\n\n")
				return "python3"
			sys.stdout.write("python\n\n")
			return "python"

		if fileType is FileType.JS:
			sys.stdout.write("node\n\n")
			return "node"

	else:
		if fileType is FileType.PYTHON:
			if python2:
				return "python2"
			if python3:
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

def clean_up(file):
	"""Clean up executables created by compiling."""
	os.remove(file)

python2 = False
python3 = False
verbose = False
noCache = False
compiler = ""

year = "2020"
author = "Kjartan Óli Ágústsson"

cache = Cache(".cache")

sys.exit(main(len(sys.argv), sys.argv))
