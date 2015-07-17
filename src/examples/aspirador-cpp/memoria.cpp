#include "memoria.h"

MemoriaInterna::MemoriaInterna() {
	sizeBool = 0;
}

MemoriaInterna::MemoriaInterna(int n) {
	sizeBool = n;
}

void MemoriaInterna::setItemSize(int n) {
	sizeBool = n;
}

int MemoriaInterna::pontoToKey(const Ponto& p) {
	int x = p.getX();
	int y = p.getY();
	int ret = ((unsigned char)p.getX() << 8) | (unsigned char)(p.getY());
	return ret; 
}
	
Ponto* MemoriaInterna::keyToPonto(int k) {
	return new Ponto((char)(k >> 8), (char)(k & 255));
}
	
bool MemoriaInterna::in(const Ponto& p) {
	if (this->get(p) != nullptr)
		return true;
	return false;
}

bool* MemoriaInterna::get(const Ponto& p) {
	int key = pontoToKey(p);
	return m[key];
}

bool MemoriaInterna::add(const Ponto& p, bool* mem) {
	bool* atual = this->get(p);
	int key = pontoToKey(p);
	if (atual == nullptr)
		m[key] = mem;
	else {
		bool* swap = atual;
		m[key] = mem;
		delete [] swap;
	}
}

bool MemoriaInterna::remove(const Ponto& p) {
	bool* removeme = this->get(p);
	if (removeme == nullptr) { 
		m.erase(pontoToKey(p));
	}
	return removeme;
}

void MemoriaInterna::del(const Ponto& p) {
	bool* delme = this->get(p);
	if (delme != nullptr) {
		delete [] delme;
		m.erase(pontoToKey(p));
	}
}

int MemoriaInterna::size() {
	return m.size();
}

Ponto** MemoriaInterna::keys() {
	Ponto** ret = new Ponto*[size()];
	map<int,bool*>::iterator mit;
	int i = 0;
	for (mit = m.begin(); mit != m.end(); ++mit, i++) {
		ret[i] = keyToPonto((*mit).first); 
	}
	return ret;
}

bool MemoriaInterna::inKeys(const Ponto& p) {
	int key = pontoToKey(p);
	map<int,bool*>::iterator it = m.find(key);
	// bool* vector = m[pontoToKey(p)];
	return it != m.end();
}

void MemoriaInterna::clear() {
	map<int,bool*>::iterator mit;
	for (mit = m.begin(); mit != m.end(); ++mit) {
		delete [] (*mit).second; 
	}
	m.clear();
}

void MemoriaInterna::printVal(int key) {
	bool* print = m[key];
	for (int i = 0; i < sizeBool; i++)
		cout << print[i] << ' ';
}

MemoriaInterna::~MemoriaInterna() {
	clear();
}

ostream& operator<< (ostream& os, MemoriaInterna& m) {
	map<int,bool*>::iterator mit;
	Ponto* p;
	for (mit = m.m.begin(); mit != m.m.end(); ++mit) {
		p = m.keyToPonto((*mit).first);
		os << *p << " - " << ' ';
		m.printVal((*mit).first);
		delete p;
	}
	os << '&' << endl;  
}
