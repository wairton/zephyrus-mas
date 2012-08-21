#include "componentes.h"
	
Componentes::Componentes(const char* configuracao) {
	carregar(configuracao);
}


void Componentes::carregar(const char* configuracao) {
	items.clear();
    ifstream in;
    int indice;
    in.open(configuracao);
    string aux;
    string sub;
    int val = 1;

	while (in >> aux) {
		items[aux.substr(0, aux.find(','))] = val;
		val <<= 1;
		//aux.erase(0, aux.find(',')+1);
		//aux.erase(0, aux.find(',')+1);
		//aux.erase(0, aux.find(',')+1);						
		
	}
	in.close();
}

Componentes::Componentes() {}

int Componentes::adicionar(string& item, int valor) {
    return items[item] | valor;
}
   
int Componentes::adicionarVarios(list<string> its, int valor) {
    if (its.size() == 1) { 
        return this->adicionar(its.front(), valor);
    }
    else {
    	string s = its.front();
    	its.pop_front();
        return adicionar(s, adicionarVarios(its, valor));
    }
}
    
int Componentes::remover(string item, int valor) {
    return items[item] ^ valor;
}

bool Componentes::checar(string item, int valor) { 
    //sei que não precisa de != 0
    return (items[item] & valor) != 0;
}

int Componentes::juntar(int v1, int v2) {
    return v1 | v2;
}

int Componentes::separar(int v1, int v2) {	
    return v1 ^ v2;
}

void Componentes::print() {
	map<string, int>::iterator mit;
	for (mit = items.begin(); mit != items.end(); ++mit)
		cout << (*mit).first << ' ' << (*mit).second << endl; 
}
Componentes::~Componentes() {
	//TODO
}
   
    
