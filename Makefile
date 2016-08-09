run:
	grep -v "#" publishedPackages.txt | xargs ./buildRepo.py
