CPPFLAGS = -std=c++0x 

all: AspiradorIII

run:
	python zephyrus.py testec.rot

AspiradorIII: memoria2.o ponto.o pontos.o componentes.o
	g++ agente.cpp memoria2.o pontos.o ponto.o componentes.o -o AspiradorIII -lzmq -std=c++0x -O -Wall

componentes.o: componentes.cpp
	g++ ${CPPFLAGS} -c componentes.cpp

pontos.o: pontos.cpp
	g++ ${CPPFLAGS} -c pontos.cpp

ponto.o: ponto.cpp
	g++ ${CPPFLAGS} -c ponto.cpp

memoria2.o: memoria2.cpp ponto.o
	g++ ${CPPFLAGS} -c memoria2.cpp

clean:
	rm *.o AspiradorIII
