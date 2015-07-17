#ifndef __ZEPHYRUS_PONTOS_H_INCLUDED__
#define __ZEPHYRUS_PONTOS_H_INCLUDED__

#include <iostream>

#define MAP_SIZE 66049
#define MAP_MIN -128
#define MAP_DIM 257

#include "ponto.h"

using namespace std;

class Pontos {
	bool* mapa;
	int sizeMapa;	
public:
	Pontos();
	int pontoToKey(const Ponto& p);
	Ponto keyToPonto(int k);
	bool in(const Ponto& p);
	bool in(int key);
	bool add(const Ponto& p);
	bool remove(const Ponto& p);
	void del(const Ponto& p);
	int size();
	Ponto* getPontos();
	//bool inKeys(const Ponto& p);
	Ponto* keys();
	void clear();
	void printVal(int key);
	
	~Pontos();
	Ponto operator[](unsigned i);
	friend ostream& operator<< (ostream& os, Pontos& ps);
};

#endif

