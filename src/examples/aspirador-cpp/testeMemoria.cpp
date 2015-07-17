#include <ctime>
#include <cstdlib> 
#include <iostream>

#include "memoria.h"

void printarBools(bool* ret, int n) {
	if (ret == NULL) {
		cout << "ret\n";
		return;
	}
	for (int i = 0; i < n; i++)
		cout << ret[i] << ' ';
	cout << endl;
}


bool* gerarBools(int n) {
	bool* ret = new bool[n]; 
	for (int i = 0; i < n; i++)
		ret[i] = rand() % 2 == 0 ? true : false;
	printarBools(ret,n);
	return ret;
}


int main() {
	MemoriaInterna m(4);
	srand(time(NULL));
	cout << "s: " << sizeof(bool) << endl;
	int size, sizeBool;
	cin >> size >> sizeBool;
	for (int i = 0; i < size; i++)
		m.add(Ponto(i/200,i%200), gerarBools(sizeBool));
	cin >> size;
	
	return 0;
}
