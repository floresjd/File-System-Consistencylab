#NAME:Jose Flores Martinez
#EMAIL:joseflores2395@gmail.com
#ID:404474130

build:
	rm -rf lab3b
	echo '#!/usr/local/cs/bin/python3' > lab3b
	cat lab3b.py >> lab3b
	chmod +x lab3b

clean:
	rm -rf lab3b lab3b-404474130.tar.gz

dist:
	tar -czvf lab3b-404474130.tar.gz lab3b.py README Makefile

