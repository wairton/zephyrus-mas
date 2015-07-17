#include "ponto.h"

Ponto::Ponto() {
	x = y = 0;
}
Ponto::Ponto(int xx, int yy) {
	x = xx;
	y = yy;
}
Ponto::Ponto(const Ponto& p) {
	x = p.x;
	y = p.y;
}

//TODO: workaround for an adapter pattern
int Ponto::linha() const {
	return getX();
}

int Ponto::coluna() const {
	return getY();
}

int Ponto::getX() const {
	return x;
}
int Ponto::getY() const {
	return y;
}

void Ponto::setX(int xx)  {
	x = xx;
}

void Ponto::setY(int yy) {
	y = yy;
}

void Ponto::setLinha(int xx) {
	setX(xx);
}

void Ponto::setColuna(int yy) {
	setY(yy);
}




ostream& operator<< (ostream& os, const Ponto& p) {
	os << "|" << p.x << ' '<< p.y;
}

bool operator< (const Ponto& p1, const Ponto& p2) {
	if (p1.x < p2.x)
		return true;
	else if ((p1.x == p2.x) && (p1.y < p2.y))
		return true;
	else
		return false;
}

bool operator== (const Ponto& p1, const Ponto& p2) {
	if ((p1.x == p2.x) && (p1.y == p2.y))
		return true;
	else
		return false;
}
