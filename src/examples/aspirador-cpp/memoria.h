#ifndef __ZEPHYRUS_MEMORIA_H_INCLUDED__
#define __ZEPHYRUS_MEMORIA_H_INCLUDED__

#include <map>
#include <iostream>

#include "ponto.h"

using namespace std;

class MemoriaInterna {
	map<int, bool*> m;
	int sizeBool;
	
public:
	MemoriaInterna();
	MemoriaInterna(int n);
	
	void setItemSize(int n);
	
	int pontoToKey(const Ponto& p);
	Ponto* keyToPonto(int k);
	bool in(const Ponto& p);
	bool* get(const Ponto& p);
	bool add(const Ponto& p, bool* mem);
	bool remove(const Ponto& p);
	void del(const Ponto& p);
	int size();
	Ponto** keys();
	bool inKeys(const Ponto& p);
	void clear();
	void printVal(int key);
	
	~MemoriaInterna();
	
	friend ostream& operator<< (ostream& os,  MemoriaInterna& m);
};

ostream& operator<< (ostream& os, MemoriaInterna& m);

#endif
