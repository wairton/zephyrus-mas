#include "memoria2.h"

MemoriaInterna::MemoriaInterna() {
	mapa = new bool*[MAP_SIZE];
	for (int i = 0; i < MAP_SIZE; i++)
		mapa[i] = nullptr;
	sizeBool = 0;
	sizeMapa = 0;
}

MemoriaInterna::MemoriaInterna(int n) {
	sizeBool = n;
	mapa = new bool*[MAP_SIZE];
	for (int i = 0; i < MAP_SIZE; i++)
		mapa[i] = nullptr;
	sizeMapa = 0;
}

void MemoriaInterna::setItemSize(int n) {
	sizeBool = n;
}

int MemoriaInterna::pontoToKey(const Ponto& p) {
	int x = p.getX();
	int y = p.getY();
	int ret = (x - MAP_MIN) * MAP_DIM + (y - MAP_MIN);
	return ret;
}
	
Ponto MemoriaInterna::keyToPonto(int k) {
	int x = (k / MAP_DIM) + MAP_MIN;
	int y = (k % MAP_DIM) + MAP_MIN;
	return Ponto(x, y);
}
	
bool MemoriaInterna::in(const Ponto& p) {
	if (this->get(p) != nullptr)
		return true;
	return false;
}

bool* MemoriaInterna::get(const Ponto& p) {
	int key = pontoToKey(p);
	cerr << "memória em get: " << key << endl;
	return mapa[key];
}

bool* MemoriaInterna::get(int key) {
	cerr << "memória em get: " << key << endl;
	return mapa[key];
}

bool MemoriaInterna::add(const Ponto& p, bool* mem) {
	cerr << "memória add\n";
	int key = pontoToKey(p);
	bool* atual = this->get(key);
	if (atual == nullptr) {
		cerr << "memória new!\n";
		mapa[key] = mem;
		sizeMapa++;
		cerr << "memória new ok!\n";
	}
	else {
		cerr << "memória swap!\n";
		bool* swap = atual;
		mapa[key] = mem;
		delete [] swap;
		cerr << "memória swap ok!\n";
	}
	cerr << "memória add ok!\n";
}

bool* MemoriaInterna::remove(const Ponto& p) {
	int chave = pontoToKey(p);
	bool* remover = nullptr; 
	if (mapa[chave] != nullptr) {
		remover = mapa[chave];
		mapa[chave] = nullptr;
		sizeMapa--;
	}
	return remover;
}

void MemoriaInterna::del(const Ponto& p) {
	int chave = pontoToKey(p);
	bool* delme = mapa[chave];
	if (delme != nullptr) {
		delete [] delme;
		mapa[chave] = nullptr;
		sizeMapa--;
	}
}

int MemoriaInterna::size() {
	return sizeMapa;
}

Ponto* MemoriaInterna::keys() {
	Ponto* ret = new Ponto[size()];
	int posicao = 0;
	for (int i = 0; i < MAP_SIZE; i++) {
		if (mapa[i] != nullptr)
			ret[posicao++] = keyToPonto(i); 
	}
	return ret;
}

bool MemoriaInterna::inKeys(const Ponto& p) {
	int key = pontoToKey(p);
	if (mapa[key] != nullptr)
		return true;
	return false;
}

void MemoriaInterna::clear() {
	for (int i = 0; i < MAP_SIZE; i++) {
		if (mapa[i] != nullptr) {
			delete [] mapa[i];
			mapa[i] = nullptr; 
		}
	}
	sizeMapa = 0;
}

void MemoriaInterna::printVal(int key) {
	bool* print = mapa[key];
	for (int i = 0; i < sizeBool; i++)
		cout << print[i] << ' ';
}

MemoriaInterna::~MemoriaInterna() { 
	clear();
	delete [] mapa;
}


ostream& operator<< (ostream& os, MemoriaInterna& m) {
	
	Ponto p;
	for (int i = 0; i < MAP_SIZE; i++) {
		if (m.mapa[i] != nullptr) { 
			p = m.keyToPonto(i);
			os << p << " - " << ' ';
		}
		m.printVal(i);
	}
	os << '&' << endl;  
}
