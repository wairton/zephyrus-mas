#include <vector>
#include <iostream>

#include "pontos.h"

Pontos::Pontos() {
	cerr << "nasci!" << endl;
	mapa = new bool[MAP_SIZE];
	for (int i = 0; i < MAP_SIZE; i++)
		mapa[i] = false;
	sizeMapa = 0;
}

int Pontos::pontoToKey(const Ponto& p) {
	int x = p.getX();
	int y = p.getY();
	int ret = (x - MAP_MIN) * MAP_DIM + (y - MAP_MIN);
	return ret;
}
	
Ponto Pontos::keyToPonto(int k) {
	int x = (k / MAP_DIM) + MAP_MIN;
	int y = (k % MAP_DIM) + MAP_MIN;
	return Ponto(x, y);
}
	
bool Pontos::in(const Ponto& p) {
	int key = pontoToKey(p);
	return mapa[key];
}

bool Pontos::in(int key) {
	return mapa[key];
}

bool Pontos::add(const Ponto& p) {
	int key = pontoToKey(p);
	if (mapa[key] == false) {
		mapa[key] = true;
		sizeMapa++;
		return true;
	}
	return false;
}

bool Pontos::remove(const Ponto& p) {
	cerr << "remove" << p << endl; 
	int chave = pontoToKey(p); 
	cerr << chave << "!\n";
	if (mapa[chave] == true) {
		mapa[chave] = false;
		sizeMapa--;
		cerr << "retorno! t";
		return true;
	}
	cerr << "retorno! f";
	return false;
}

void Pontos::del(const Ponto& p) {
	int chave = pontoToKey(p); 
	if (mapa[chave] == true) {
		mapa[chave] = false;
		sizeMapa--;
	}
}

int Pontos::size() {
	return sizeMapa;
}

Ponto* Pontos::getPontos() {
	if (sizeMapa < 1) return nullptr;
	Ponto* ret = new Ponto[sizeMapa];
	int j = 0;
	for (int i = 0; i < sizeMapa; i++) {
		if (mapa[i] == true) {
			ret[j] = keyToPonto(i);
			j++;
		}
	}
	return ret;
}


Ponto* Pontos::keys() {
	if (size() < 1) 
		return nullptr;
	Ponto* ret = new Ponto[size()];
	int posicao = 0;
	for (int i = 0; i < MAP_SIZE; i++) {
		if (mapa[i] == true)
			ret[posicao++] = keyToPonto(i); 
	}
	return ret;
}

/*
bool Pontos::inKeys(const Ponto& p) {
	int key = pontoToKey(p);
	if (mapa[key] != nullptr)
		return true;
	return false;
}*/

void Pontos::clear() {
	for (int i = 0; i < MAP_SIZE; i++) {
		mapa[i] = false;
	}
	sizeMapa = 0;
}

void Pontos::printVal(int key) {
	bool print = mapa[key];
	/*
	for (int i = 0; i < sizeBool; i++)
		cout << print[i] << ' ';*/
}

Pontos::~Pontos() { 
	clear();
	cerr << "morri!" << endl;
	delete [] mapa;
}

Ponto Pontos::operator[](unsigned i) {
	int j = -1;
	if (i >= sizeMapa) return keyToPonto(-1); //força um erro
	for (int i = 0; i < MAP_SIZE; i++) {
		if (mapa[i] == true) {
			j++;
			if (j == i) return keyToPonto(i);
		}
	}
}

ostream& operator<< (ostream& os, Pontos& ps) {	
	Ponto p;
	for (int i = 0; i < MAP_SIZE; i++) {
		if (ps.mapa[i] == true) { 
			p = ps.keyToPonto(i);
			os << p << " - " << ' ';
		}
		ps.printVal(i);
	}
	os << '&' << endl;  
}

