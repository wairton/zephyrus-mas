#ifndef __ZEPHYRUS_PONTO_H_INCLUDED__
#define __ZEPHYRUS_PONTO_H_INCLUDED__

#include <iostream>

using namespace std;

class Ponto {
	int x,y;
public:	
	Ponto();
	Ponto(int xx, int yy);
	Ponto(const Ponto& p);
	int getX() const;
	int getY() const;
	int linha() const;
	int coluna() const;
	
	void setX(int xx);
	void setY(int yy);
	void setLinha(int xx);
	void setColuna(int yy);
	
	friend ostream& operator<< (ostream&, const Ponto&);
	friend bool operator< (const Ponto& p1, const Ponto& p2);
	friend bool operator== (const Ponto& p1, const Ponto& p2);
};

ostream& operator<< (ostream& os, const Ponto& p);
bool operator< (const Ponto& p1, const Ponto& p2);
bool operator== (const Ponto& p1, const Ponto& p2);

#endif
