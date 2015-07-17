#include <iostream>
#include <fstream>
#include <cstdlib>
#include <string>
#include <map>
#include <list>
#include <string>

using namespace std;

class Componentes {
	map<string, int> items;
	//self.valores = {} #utilizado na busca de um nome a partir de um valor.
	
public:
	Componentes(const char* configuracao);
	Componentes();
	void carregar(const char* configuracao);
    int adicionar(string& item, int valor);
    int adicionarVarios(list<string> its, int valor);
    int remover(string item, int valor);
    bool checar(string item, int valor);
    int juntar(int v1, int v2);
    int separar(int v1, int v2);
    void print();
    ~Componentes();	
};
