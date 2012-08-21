#include <ctime>
#include <cstdlib> 
#include <iostream>
#include <map>

using namespace std;

bool* gerarBools(int n) {
	bool* ret = new bool[n]; 
	for (int i = 0; i < n; i++)
		ret[i] = ((int)(rand()*10 % 2) == 0)?true:false;
	return ret;
}

void printarBools(bool* ret, int n) {
	if (ret == NULL) {
		cout << "ret\n";
		return;
	}
	for (int i = 0; i < n; i++)
		cout << ret[i] << ' ';
	cout << endl;
}


int main() {
	map<int, bool*> m;
	srand(time(NULL));
	int size, boolSize;
	cin >> size >> boolSize;
	for (int i = 0; i < size; i++)
		m.insert(pair<int, bool*>(0, gerarBools(boolSize)));
	printarBools(m[1], boolSize);
	bool* p = m[-1];
	cout<<"@";
	printarBools(m[-1], boolSize);
	cin >> size;
	
	return 0;
}
