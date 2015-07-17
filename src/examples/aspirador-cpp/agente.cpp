#include <iostream>
#include <ctime>
#include <cstdlib>

#include "componentes.h"
#include "memoria2.h"
#include "pontos.h"

#include <string>
#include <vector>
#include <set>
#include <queue>
#include <list>

#include<zmq.hpp>


// typedef list<int> Movimentos;

class Movimentos {
	int* base;
	int actualSize;
	int actualPos;
public:
	Movimentos() {
		base = new int[100];
		actualSize = 0;
		actualPos;
	}
	int size() {
		return actualSize;
	}
	int front() {
		return base[actualPos];
	}
	void pop_front() {
		if (actualSize > 0) {
			actualPos++;
			actualSize--;
		}
	}
	void push_back(int add) {
		base[actualPos + actualSize] = add;
		actualSize++;
	}
	void insertAtBegin(int add) {
		if (actualSize == 0)
			this->push_back(add);
		else {			
			base[actualPos-1] = add;
			actualSize++;
			actualPos--;
		}
	}
};

class AspiradorIII {
	enum Plano {NENHUM, EXPLORAR, RECARREGAR, DEPOSITAR, SUJEIRA};
	
	Componentes componentes;
	
	int mid;	//id do agente
	char* endereco; 
	char* enderecoInteracao;
	int x, y;
	int px, py;	//delta do movimento pretendido
	int recuperarMovimento;
	const float ENERGIA_MAX;
	const int RESERVATORIO_MAX;
	float limiteRecarga;
	bool enviar, agindo;
	int energia;
	int nrecargas;
	int reservatorio;
	
	int memoriaPercebido;	//self.percebido
	Plano plano; 
	Ponto DELTA_POS[4];
	
	vector<string*> itens;
	
	Pontos* nvisitados;
	Pontos* depositos;
	Pontos* recargas;
	MemoriaInterna* visitados;
	
	Movimentos* movimentar;
	
	set<Ponto>* sujeiras;
	
	zmq::socket_t* socketReceive;
	zmq::socket_t* socketSend;

public:
	AspiradorIII(int id, char* _endereco, char* _enderecoInteracao, char* arqComponentes) :
		ENERGIA_MAX(75.0), RESERVATORIO_MAX(5) {
		mid = id;
		endereco = _endereco;
		enderecoInteracao = _enderecoInteracao;
		enviar = true;
		agindo = false;

		limiteRecarga = 0.4;
		cerr << "agente: " << _endereco << endl;
		cerr << "agente: " << _enderecoInteracao << endl;
		cerr << "agente: " << arqComponentes << endl;
		
		DELTA_POS[0].setX(-1);
		DELTA_POS[0].setY(0);
		DELTA_POS[1].setX(0);
		DELTA_POS[1].setY(1);
		DELTA_POS[2].setX(1);
		DELTA_POS[2].setY(0);
		DELTA_POS[3].setX(0);
		DELTA_POS[3].setY(-1);
		
		itens.push_back(new string("PAREDEN"));
		itens.push_back(new string("PAREDEL"));
		itens.push_back(new string("PAREDES"));
		itens.push_back(new string("PAREDEO"));
		itens.push_back(new string("LIXO"));
		itens.push_back(new string("LIXEIRA"));
		itens.push_back(new string("RECARGA"));
		
		componentes.carregar(arqComponentes);
		
		visitados = nullptr;
		nvisitados = nullptr;
		depositos  = nullptr;
		recargas = nullptr;
		sujeiras = nullptr;	
		movimentar = nullptr;

		reiniciarMemoria();
		
		run();
	}
	
protected:
	void reiniciarMemoria() {
		x = 0; y = 0;
		px = 0; py = 0;
		cerr<<"agente: reiniciarMemoria()\n"; 
		plano = NENHUM;
		if (visitados != nullptr) {
			visitados->clear();
			delete visitados;	
			// visitados->setItemSize(4);
		}
		visitados = new MemoriaInterna(4);
		if (nvisitados != nullptr) {
			delete nvisitados;
		}
		nvisitados = new Pontos;
		if (depositos != nullptr) {
			delete depositos;
		}
		depositos = new Pontos;
		if (recargas != nullptr) {
			delete recargas;
		}
		recargas = new Pontos;
		if (sujeiras != nullptr) {
			delete sujeiras;
		}
		sujeiras = new set<Ponto>;
		
		if (movimentar != nullptr) {
			delete movimentar;
			movimentar = nullptr;
		}
						
		energia = ENERGIA_MAX;
		reservatorio = 0;
		plano = NENHUM;

		nrecargas = 0;
		recuperarMovimento = 0;
		cerr<<"agente: reiniciarMemoria() ok!\n"; 
	}
	
	char* perceber(int percebido) {
//		#posições: N, L, S ,O e 'sujo' (true indica presença de parede/sujeira)
		cerr << "agente: em perceber\n";
		bool* st = new bool[itens.size()];
		for(int i = 0; i < itens.size(); i++) {
			st[i] = componentes.checar(*itens[i], percebido);
			//cerr << st[i]  << ' ';
		}
		return agir(st);
	}

public:	
	void run() {
		// cerr<<"agente: run().\n";
		zmq::context_t contexto(1);
		socketReceive = new zmq::socket_t(contexto, ZMQ_PULL);
		cerr << "agente: bind em " << endereco << endl;		
		socketReceive->bind(endereco);
		socketSend = new zmq::socket_t(contexto, ZMQ_PUSH);
		cerr << "agente: connect com " << enderecoInteracao << endl;
		socketSend->connect(enderecoInteracao);
		pronto();
	}
	
protected:
	void pronto() {
		cout << "agente: pronto().\n";
		char* acao;
		while (true) {
			zmq::message_t msg;
			cerr << "esperando!!!\n";
			socketReceive->recv(&msg);
			// cerr<<"agente: recebi "<<(const char*)msg.data() << endl;
			//TODO: fazer isso da maneira aconselhada.
			((char*)msg.data())[msg.size()] = 0;
			if (strcmp((char*)msg.data(), "@@@") == 0) {
				reiniciarMemoria();
				enviar = true;
				agindo = false;
				while (true) {
					if (enviar) {
						if (agindo == false) {
							char* mensagem = new char[20];
							sprintf(mensagem, "%d 0 perceber", mid);
							//cerr << "tamanho: " << strlen(mensagem) << endl; 
							zmq::message_t msgOut(strlen(mensagem));
							strcpy((char*)msgOut.data(), mensagem);
							delete [] mensagem;
							socketSend->send(msgOut);
							//cerr<<"agente: enviou "<<(const char*)msgOut.data() << endl;
							enviar = false;
						}
						else {
							char* acao = perceber(memoriaPercebido);
							char* mensagem = new char[20];
							sprintf(mensagem, "%d 0 %s", mid, acao);
							zmq::message_t msgOut(strlen(mensagem));
							strcpy((char*)msgOut.data(), mensagem);
							delete [] acao;
							delete [] mensagem;							 
							//msg = "%s %s " % (self.mid, 0)
							//TODO: tratar o caso PARAR					
							socketSend->send(msgOut);			
							//cerr<<"agente: enviou "<<(const char*)msgOut.data() << endl;
							enviar = false;
						}
					}
					else {
						if (agindo == false) {
							zmq::message_t msgResposta;
							socketReceive->recv(&msgResposta);
							enviar = true;
							agindo = true;
							char dummy[20];
							char* texto = new char[msgResposta.size() + 1];
							texto[msgResposta.size()] = 0;
							memcpy(texto, msgResposta.data(), msgResposta.size());
							sscanf(texto, "%s %s %d", dummy, dummy, &memoriaPercebido);
							delete [] texto;
							//cerr << "agente: percebi " << memoriaPercebido << endl; 
						}
						else {
							zmq::message_t msgResposta;
							socketReceive->recv(&msgResposta); //apenas um feedback (ack)
							//retorno = msg.split()[-1]
							char* texto = new char[msgResposta.size() + 1];
							memcpy(texto, msgResposta.data(), msgResposta.size());
							texto[msgResposta.size()] = 0;
							// ((char*)msgResposta.data())[msgResposta.size()] = 0;
							// char* retorno = (char*)msgResposta.data();
							int pos = msgResposta.size() - 1;
							while (pos > 0) {
								if (texto[pos] == ' ')
									break;
								pos--;
							}
							//b e l e l e u 0
							//0 1 2 3 4 5 6 7
							char* retorno = texto + pos + 1;
							
							if (strcmp(retorno, "moveu") == 0)
								mover();
							else if (strcmp(retorno, "limpou") == 0)
								limpar();
							else if (strcmp(retorno, "recarregou") == 0)
								carregar();
							else if (strcmp(retorno, "depositou") == 0)
								depositar();
							else if (strcmp(retorno, "colidiu") == 0)
								colidir();
							else if (strcmp(retorno, "parou") == 0) {
								/*cerr << "\n\nfui!\n\n";exit(1);*/
								delete [] texto;
								parar();
								break;
							}
							else if (strcmp(retorno, "nop") == 0)
								nop();
							else {
								cerr<<"Mensagem invalida" << endl;
							}
							delete [] texto;
							enviar = true;
							agindo = false;
						}
					}
				}
			}
			else if (strcmp((const char*)msg.data(),"###") == 0) {
				cerr << "Agente recebeu Mensagem de finalização de atividades.\n";
				break;
			}
			else {
				cerr << "agente: Mensagem inválida";
			}
		}
	}
	char* agir(bool* st) {
		//cerr << "agente: hora de agir!\n"; 
		memorizarAmbiente(st);
		if (energia <= 0) {
			char* acao = new char[10];
			sprintf(acao,"parar");
			return acao;
		}
		if (plano != NENHUM) {
			if (movimentar) cerr << movimentar->size() << ' ';
			switch(plano) {
				case EXPLORAR:
					cerr << "EXPLORAR" << endl;
					if (movimentar && movimentar->size() > 0) {
						recuperarMovimento = movimentar->front();
						movimentar->pop_front();
						
						px = DELTA_POS[recuperarMovimento].linha();
						py = DELTA_POS[recuperarMovimento].coluna();
						if (movimentar && movimentar->size() == 0)
							plano = NENHUM;
						char* acao = new char[10];
						sprintf(acao, "mover %d", recuperarMovimento);
						return acao;
					}
					else
						cerr << "erro na função agir\n"; //TODO: transformar isso em execeção
					break;
				case DEPOSITAR:
					cerr << "DEPOSITAR" << endl;
					if (movimentar && movimentar->size() > 0) {
						recuperarMovimento = movimentar->front();
						movimentar->pop_front();
						px = DELTA_POS[recuperarMovimento].linha();
						py = DELTA_POS[recuperarMovimento].coluna();
						energia--;
						char* acao = new char[10];
						sprintf(acao, "mover %d", recuperarMovimento);
						return acao;
					}
					else {
						plano = NENHUM;
						char* acao = new char[10];
						sprintf(acao, "depositar");						
						return acao;
					}
					break;		
				case RECARREGAR:
					cerr << "RECARREGAR" << endl;
					if (movimentar && movimentar->size() > 0) {
						recuperarMovimento = movimentar->front();
						movimentar->pop_front();
						px = DELTA_POS[recuperarMovimento].linha();
						py = DELTA_POS[recuperarMovimento].coluna();
						energia--;
						char* acao = new char[10];
						sprintf(acao, "mover %d", recuperarMovimento);
						return acao;
					}
					else {
						nrecargas--;
						if (nrecargas == 0)
							plano = NENHUM;
						char* acao = new char[10];
						sprintf(acao, "recarregar");
						return acao;
					}
					break;
				case SUJEIRA:
					cerr << "SUJEIRA" << endl;
					if (movimentar && movimentar->size() > 0) {
						recuperarMovimento = movimentar->front();
						movimentar->pop_front();
						px = DELTA_POS[recuperarMovimento].linha();
						py = DELTA_POS[recuperarMovimento].coluna();
						energia--;
						char* acao = new char[10];
						sprintf(acao, "mover %d", recuperarMovimento);
						return acao;
					}
					else {
						plano = NENHUM;
						char* acao = new char[10];
						sprintf(acao, "limpar");
						return acao;
					}
					break;		
				default:
					cerr << "agente: plano desconhecido\n";
			}
		}
		else if ((energia / ENERGIA_MAX) < limiteRecarga)
			return tracarPlanoRecarga(st);
		else if (reservatorio == RESERVATORIO_MAX)
			return tracarPlanoDeposito(st);
		else if (st[4] == true) {
			energia -= 3; //consome energia independente de limpar ou não de verdade
			char* acao = new char[10];
			sprintf(acao, "limpar");
			return acao;
		}
		else
			return escolherDirecao(st);
	}
	
	/*Atualiza o conhecimento do agente em relação as salas que já foram visitadas, 
	bem como suas características, e das sala que o agente sabe não ter visitado.*/
	void memorizarAmbiente (bool* st) {
		cerr << "agente: memorizarAmbiente\n";
		Ponto p(x,y);
		//cerr << "agente: batatinha 01\n";
		// cerr << *nvisitados << endl;
		nvisitados->remove(p);
		//cerr << "agente: batatinha 02\n";
		visitados->add(p, st);
		
		//cerr << "agente: memorizarAmbiente 01\n";
		if (st[0] == false) {
			p.setX(x-1);
			p.setY(y);
			if (!visitados->inKeys(p) && !nvisitados->in(p))
				nvisitados->add(p);
		}
		//cerr << "agente: memorizarAmbiente 02\n";
		if (st[1] == false){
			p.setX(x);
			p.setY(y+1);
			if (!visitados->inKeys(p) && !nvisitados->in(p))
				nvisitados->add(p);
		}	
		//cerr << "agente: memorizarAmbiente 03\n";
		if (st[2] == false) {
			p.setX(x+1);
			p.setY(y);
			if (!visitados->inKeys(p) && !nvisitados->in(p))
				nvisitados->add(p);
		}			
		//cerr << "agente: memorizarAmbiente 04\n";
		if (st[3] == false) {
			p.setX(x);
			p.setY(y-1);
			if (!visitados->inKeys(p) && !nvisitados->in(p))
				nvisitados->add(p);
		}
		//cerr << "agente: memorizarAmbiente 05\n";
		if (st[4] == true) {
			Ponto p2(x,y);
			sujeiras->insert(p2);
		}
		//cerr << "agente: memorizarAmbiente 06\n";
		if (st[5] == true) {	
			Ponto p2(x,y);
			if (!depositos->in(p2))
				depositos->add(p2);
		}
		//cerr << "agente: memorizarAmbiente 07\n";
		if (st[6] == true) {			
			Ponto p2(x,y);
			if (!recargas->in(p2))
				recargas->add(p2);
		}
		//cerr << "agente: memorizarAmbiente ok\n";
		
		//print 'Status da memória'
		//print self.visitados.keys()
		//print self.nvisitados
	}
				
	char* escolherDirecao( bool* paredes )  {
		cerr << "agente: escolher direção" << endl;
		short ndirecoes = 0;
		int direcoes[4];
		
		//info();
		
		for (int i = 0; i < 4; i++)
			if (!paredes[i]) {
				direcoes[ndirecoes] = i;
				ndirecoes++;
			}
				
		if (ndirecoes == 0) {
			char* acao = new char[10];
			sprintf(acao, "parar");
			return acao;
		}
					
		if (nvisitados->size() == 0 && sujeiras->size() == 0) {
			char* acao = new char[10];
			sprintf(acao, "parar");
			return acao;
		}
		
		int naovisitados[4];
		int nnaovisitados = 0;
	
		Ponto p;
		
		//visitados = self.visitados.keys()
		for (int i = 0; i < ndirecoes; i++) {
			switch (direcoes[i]) {
				case 0:
					if (!visitados->in(Ponto(x-1, y)))
						naovisitados[nnaovisitados++] = 0;
					break;
				case 1:
					if (!visitados->in(Ponto(x, y+1)))
						naovisitados[nnaovisitados++] = 1;				
					break;
				case 2:
					if (!visitados->in(Ponto(x+1, y)))
						naovisitados[nnaovisitados++] = 2;				
					break;
				case 3:
					if (!visitados->in(Ponto(x, y-1)))
						naovisitados[nnaovisitados++] = 3;				
					break;
				default:
					cerr << "agente: erro em escolher direcao" << endl;							
			}
		}
					
		if (nnaovisitados == 0)
			if (nvisitados->size() == 0)
				return tracarPlanoSujeira();
			else
				return tracarPlanoExploracao();
		//print paredes, nvisitados
		recuperarMovimento = naovisitados[rand() % nnaovisitados];
		px = DELTA_POS[recuperarMovimento].linha();
		py = DELTA_POS[recuperarMovimento].coluna();		
		energia--;
		char* acao = new char[10];
		sprintf(acao, "mover %d", recuperarMovimento);
		return acao;
	}
		
	//encontrar as coordenadas do mapa mental do agente
	void calcularDimensoes(int& minx, int& maxx, int& miny, int& maxy) {
		cerr << "agente: calcular dimensões -início" << endl;
		Ponto* keys = visitados->keys();
		int numKeys = visitados->size();
		minx = 1000;  //TODO: remove this hardcoded limit.
		miny = 1000;  //TODO: remove this hardcoded limit.
		maxx = -1000; //TODO: remove this hardcoded limit.
		maxy = -1000; //TODO: remove this hardcoded limit.
		int dimensao;
		
		cerr << "pontos visitados: ";
		for (int i = 0; i < numKeys; i++)
			cerr << keys[i] << '\t';
			
		for (int i = numKeys - 1; i >= 0; i--) {
			dimensao = keys[i].getX();
			if (dimensao > maxx)
				maxx = dimensao;
			else if (dimensao < minx)
				minx = dimensao;
				
			dimensao = keys[i].getY();
			if (dimensao > maxy)
				maxy = dimensao;
			else if (dimensao < miny)
				miny = dimensao;  
		}
		delete [] keys;
		
		keys = nvisitados->keys();
		numKeys = nvisitados->size();
		
		cerr << "\npontos não visitados: ";
		for (int i = 0; i < numKeys; i++)
			cerr << keys[i] << '\t';
					
		for (int i = 0; i < numKeys; i++) {
			dimensao = keys[i].getX();
			if (dimensao > maxx)
				maxx = dimensao;
			else if (dimensao < minx)
				minx = dimensao;
				
			dimensao = keys[i].getY();
			if (dimensao > maxy)
				maxy = dimensao;
			else if (dimensao < miny)
				miny = dimensao;
		}
		cerr << endl << minx << ' ' << maxx << ' ' << miny << ' ' << maxy << endl;
		delete [] keys;
	}
			
	char* tracarPlanoRecarga(bool* st) {
		cerr << "agente: plano recarga" << endl;
		//info();
		if (recargas->size() == 0)
			return escolherDirecao(st);			
		plano = RECARREGAR;
		nrecargas = (int)((ENERGIA_MAX - energia)/10.0);
		
		if (st[6]) { //o agente já está em um ponto de recarga
			if (movimentar) {
				delete movimentar;
				movimentar = nullptr;
			}
			
			nrecargas -= 1;
			char* acao = new char[10];
			sprintf(acao,"recarregar");
			return acao;
		}
			
		int minx, maxx, miny, maxy;
		calcularDimensoes(minx, maxx, miny, maxy);
		int sizex = maxx - minx + 1;
		int sizey = maxy - miny + 1;
	
		
		int** matriz = new int*[sizex];
		
		for (int i = 0; i < sizex; i++) {
			matriz[i] = new int[sizey];
			for (int j = 0; j < sizey; j++)
				matriz[i][j] = -1000;
		}
				
		Ponto* pvisitados = visitados->keys();
		int keysSize = visitados->size();
		for (int i = keysSize-1; i >= 0; i--) {
			matriz[pvisitados[i].getX()-minx][pvisitados[i].getY()-miny] = 1000;  
		}
		
		delete [] pvisitados;
		
		//cerr << "recarga: #1\n";
		
		Ponto* precargas = recargas->keys();
		for (int i = 0; i < recargas->size(); i++)
			matriz[precargas[i].getX() - minx][precargas[i].getY() - miny] = -1;
			
		delete [] precargas;
		
		//cerr << "recarga: #2\n";
		
		list<Ponto>* caminho;
		caminho = caminhoMaisCurto(matriz, x, y, minx, maxx, miny, maxy);
		
		//cerr << "batatinha #1 plano recarga" << endl;	
		if (movimentar)
			delete movimentar;
		//cerr << "batatinha #2" << endl;
		movimentar = caminhoParaMovimentos(caminho);
		recuperarMovimento = movimentar->front();
		movimentar->pop_front();
		energia--;
		px = DELTA_POS[recuperarMovimento].linha();
		py = DELTA_POS[recuperarMovimento].coluna();
		char* acao = new char[10];
		sprintf(acao, "mover %d", recuperarMovimento );
		return acao;
	}

	char* tracarPlanoDeposito(bool* st)  {
		cerr << "agente: plano deposito" << endl;
		//info();
		if (depositos->size() == 0)
			return escolherDirecao(st);
			
		plano = DEPOSITAR;

		if (st[5] == true) {//o agente já está em um ponto de depósito
			if (movimentar) { 
				delete movimentar;
				movimentar = nullptr;
			}
			plano = NENHUM;
			char* acao = new char[10];
			sprintf(acao,"depositar");
			return acao;
		}
		
		int minx, maxx, miny, maxy;
		calcularDimensoes(minx, maxx, miny, maxy);
		int sizex = maxx - minx + 1;
		int sizey = maxy - miny + 1;

		int** matriz = new int*[sizex];
		
		for (int i = 0; i < sizex; i++) {
			matriz[i] = new int[sizey];
			for (int j = 0; j < sizey; j++)
				matriz[i][j] = -1000;
		}
		
		Ponto* pvisitados = visitados->keys();
		int keysSize = visitados->size();
		for (int i = keysSize-1; i >= 0; i--) {
			matriz[pvisitados[i].getX()-minx][pvisitados[i].getY()-miny] = 1000;  
		}
		delete [] pvisitados;
		// cerr << endl;

		//cerr << "depositos: #1\n";
		
		Ponto* pdepositos = depositos->keys();
		for (int i = 0; i < depositos->size(); i++)
			matriz[pdepositos[i].getX() - minx][pdepositos[i].getY() - miny] = -1;
		
		delete [] pdepositos;
		
		//cerr << "depositos: #2\n";		

		list<Ponto>* caminho = caminhoMaisCurto(matriz, x, y, minx, maxx, miny, maxy);
		
		if (movimentar)
			delete movimentar;
		movimentar = caminhoParaMovimentos(caminho);
		recuperarMovimento = movimentar->front();
		movimentar->pop_front();
		energia--;
		px = DELTA_POS[recuperarMovimento].linha();
		py = DELTA_POS[recuperarMovimento].coluna();
		char* acao = new char[10];
		sprintf(acao, "mover %d", recuperarMovimento );
		return acao;
	}
		
	char* tracarPlanoSujeira() {
		cerr << "agente: plano sujeira" << endl;
		//info();
		plano = SUJEIRA;
			
		int minx, maxx, miny, maxy;
		calcularDimensoes(minx, maxx, miny, maxy);
		int sizex = maxx - minx + 1;
		int sizey = maxy - miny + 1;
		
		int** matriz = new int*[sizex];
		
		for (int i = 0; i < sizex; i++) {
			matriz[i] = new int[sizey];
			for (int j = 0; j < sizey; j++)
				matriz[i][j] = -1000;
		}
		
		
		Ponto* pvisitados = visitados->keys();
		int keysSize = visitados->size();
		for (int i = keysSize-1; i >= 0; i--) {
			matriz[pvisitados[i].getX()-minx][pvisitados[i].getY()-miny] = 1000;  
		}
		delete [] pvisitados;	
		
		for (set<Ponto>::iterator it = sujeiras->begin(); 
				it != sujeiras->end(); it++) {
			matriz[(*it).getX() - minx][(*it).getY() - miny] = -1;
		}
		
		
		list<Ponto>* caminho;
		caminho = caminhoMaisCurto(matriz, x, y, minx, maxx, miny, maxy);
		
	
		if (movimentar)
			delete movimentar;

		movimentar = caminhoParaMovimentos(caminho);
		recuperarMovimento = movimentar->front();
		movimentar->pop_front();
		energia--;
		px = DELTA_POS[recuperarMovimento].linha();
		py = DELTA_POS[recuperarMovimento].coluna();
		char* acao = new char[10];
		sprintf(acao, "mover %d", recuperarMovimento );
		return acao;		
	}
	
	char* tracarPlanoExploracao() {
		cerr << "agente: plano exploração" << endl;
		//info();
		plano = EXPLORAR;
		
		int minx, maxx, miny, maxy;
		calcularDimensoes(minx, maxx, miny, maxy);
		int sizex = maxx - minx + 1;
		int sizey = maxy - miny + 1;
		
		int** matriz = new int*[sizex];
		
		for (int i = 0; i < sizex; i++) {
			matriz[i] = new int[sizey];
			for (int j = 0; j < sizey; j++)
				matriz[i][j] = -1;
		}
		
	
		Ponto* pvisitados = visitados->keys();
		int keysSize = visitados->size();
		for (int i = keysSize-1; i >= 0; i--) {
			matriz[pvisitados[i].getX() - minx][pvisitados[i].getY() - miny] = 1000;  
		}
		delete [] pvisitados;
						
		list<Ponto>* caminho = caminhoMaisCurto(matriz, x, y, minx, maxx, miny, maxy);	
		if (movimentar)
			delete movimentar;
		movimentar = caminhoParaMovimentos(caminho);
		recuperarMovimento = movimentar->front();
		movimentar->pop_front();
		energia--;
		px = DELTA_POS[recuperarMovimento].linha();
		py = DELTA_POS[recuperarMovimento].coluna();
		char* acao = new char[10];
		sprintf(acao, "mover %d", recuperarMovimento );
		return acao;		
		
	}

	
	list<Ponto>* caminhoMaisCurto(int** matriz, int atualx, int atualy,  
								int minx, int maxx, int miny, int maxy) {
		cerr << "agente: caminho mais curto" << endl;
		queue<Ponto> fila;
		fila.push(Ponto(atualx, atualy));
		// Movimentos* caminho = new Movimentos; 
		// Pontos* caminho = new Pontos; 
		list<Ponto>* caminho = new list<Ponto>; 
		Ponto paux;
		int px = atualx;
		int py = atualy;
		int opx, opy;
		matriz[px-minx][py-miny] =  0;
		int peso = 0;
		while (fila.size() > 0) {
			cerr << "%" << fila.size() << ' ' << endl;
			debugPrintMatiz(maxx-minx+1, maxy-miny+1, matriz);
			// cerr << endl;
			paux = fila.front();
			px = paux.linha();
			py = paux.coluna();
			fila.pop();
			cerr << "atualmente em " << paux << endl;
/*			if matriz[px - minx][py - miny] ==  -1:
				return (px,py) #TODO: se entrar aqui (é possível?) vai dar bug!!!!!!*/
			peso = matriz[px - minx][py - miny];
			Pontos* pdirecoes = estadosParaDirecoes(paux, visitados->get(paux));
			Ponto* direcoes = pdirecoes->keys();
			for(int i = 0; i < pdirecoes->size(); i++) {
				Ponto direcao = direcoes[i];
				opx = direcao.getX();
				opy = direcao.getY();
				if (matriz[opx - minx][opy - miny] > peso + 1)	{//encontrou um caminho melhor.
					matriz[opx - minx][opy - miny] = peso + 1;
					fila.push(direcao);
				}
				//encontrou uma posição que ainda não foi visitada.
				else if (matriz[opx - minx][opy - miny] == -1) {
					// cerr << "ACHEI!!!!" << endl;
					caminho->push_front(direcao);
					while (peso >= 0) {
						// cerr << peso << ',' << caminho->size() << ' ';
						//Sul
						if ((opx - minx + 1 <= maxx - minx) && 
							(matriz[opx - minx + 1][opy - miny] == peso)) {
							caminho->push_front(Ponto(opx + 1, opy));
							opx += 1;
							peso -= 1;
							// cerr << "s ";
							continue;
						}
						//Oeste
						if ((opy - miny - 1 >= 0) && 
							(matriz[opx - minx][opy - 1 - miny] == peso)) {
							caminho->push_front(Ponto(opx, opy - 1));
							opy -= 1;
							peso -= 1;
							// cerr << "o ";
							continue;		
						}
						//Norte
						if ((opx - minx - 1 >= 0) && 
							(matriz[opx - minx - 1][opy - miny] == peso)) {
							caminho->push_front(Ponto(opx - 1, opy));
							peso -= 1;
							opx -= 1;
							// cerr << "n ";
							continue;
						}
						//Leste
						if ((opy - miny + 1 <= maxy - miny) && 
							(matriz[opx - minx][opy + 1 - miny] == peso)) {
							caminho->push_front(Ponto(opx, opy + 1));
							peso -= 1;
							opy += 1;
							// cerr << "l ";
							continue;
						}
					}
					// caminho->push_front(Ponto(atualx,atualy));
					delete [] direcoes;
					delete pdirecoes;						
					return caminho;
				}
			}
			delete [] direcoes;
			delete pdirecoes;
		}
		//não encontrou caminho!'
		//print self.info()	
		return nullptr;
	}
	
	//Método auxiliar que realiza a conversão de estados(paredes) para direções
	Pontos* estadosParaDirecoes(Ponto& pos, bool* st) {
		cerr << "agente: estados para direções";
		for (int i = 0; i < 4; i++)
			cerr << st[i] << ' ';
		cerr << endl;
		cerr << "@\n";
		Pontos* ret = new Pontos;
		int x = pos.getX();
		int y = pos.getY();
		if (st[0] == false)
			ret->add(Ponto(x-1, y));
		if (st[1] == false)
			ret->add(Ponto(x, y+1));
		if (st[2] == false)
			ret->add(Ponto(x+1, y));
		if (st[3] == false)
			ret->add(Ponto(x, y-1));
		cerr << "agente: estados para direções ok" << endl;
		return ret;
	}
	
	//Método que transforma uma rota em uma série de movimentos. 
	Movimentos* caminhoParaMovimentos(list<Ponto>* caminho) {
		Movimentos* movimentos  = new Movimentos;
		int orix, oriy;
		int desx, desy;
		orix = caminho->front().getX();
		oriy = caminho->front().getY();
		caminho->pop_front();
		int tamanhoDoCaminho = caminho->size();
		// cerr << "caminho percorrido: " << caminho->size() << endl;
		for (int i = 0; i < tamanhoDoCaminho; i++) {
			desx = caminho->front().getX();
			desy = caminho->front().getY();
			// cerr << orix << '|' << oriy << '|' << desx << '|' << desy << endl;
			if (orix != desx)
				if (orix > desx)
					movimentos->push_back(0);
				else
					movimentos->push_back(2);
			else
				if (oriy > desy)
					movimentos->push_back(3);
				else
					movimentos->push_back(1);
			orix = desx;
			oriy = desy;
			caminho->pop_front();
		}
		return movimentos;
	}
	
						
	void limpar() {
		//O agente executa a ação de limpar em sua posição atual.
		//print 'limpei'
		sujeiras->erase(Ponto(x, y));
		reservatorio++;
	}
	
	void carregar() {
		//print 'carreguei'
		energia += 10;
	}
		
	void depositar() {
		//print 'depositei'
		energia--;
		reservatorio = 0;
	}
				
	void parar() {
		//O agente permanece parado e apenas informa esse fato ao observador.
		info();
		// cerr << "fui! =)";
	}
				
	void mover() {
		//movimento realizado com sucesso
		//print 'movi'
		x += px;
		y += py;
	}
		
	void colidir() {
		cerr << "agente: colidi" << endl;			
		energia--;
		if (plano != NENHUM && movimentar != nullptr)
			movimentar->insertAtBegin(recuperarMovimento);
	}
			
	void nop() {
		cout << "agente: recebi nop";
	}
			
	void info() {
		cerr << "**********" << endl;/*
		cerr << "posição " << x << ' ' << y << endl;
		cerr << energia << ' ' << reservatorio << ' ' << plano << endl;
		cerr << "visitados" << ' ' << visitados << endl;
		cerr << "nvisitados "; 
		for (auto& i : *nvisitados) {
			cerr << i << ' ';
		}
		cerr << endl;
		cerr << "depositos "; 
		for (auto& i : *depositos) {
			cerr << i << ' ';
		}
		cerr << endl;
		cerr << "recargas "; 
		for (auto& i : *recargas) {
			cerr << i << ' ';
		}
		cerr << endl;			
		cerr << "sujeiras:";
		for (auto& i : *sujeiras) {
			cerr << '(' << i.getX() << ',' << i.getY() << ") ";
		}*/
		cerr << endl;
		cerr << "**********" << endl;
	}
	void debugPrintMatiz(int nx, int ny, int** matriz) {
		for (int i = 0; i < nx; i++) {
			for (int j = 0; j < ny; j++)
				cerr << matriz[i][j] << '\t';
			cerr << endl;
		}
	}
public:
	~AspiradorIII() {
		if (visitados != nullptr)
			delete visitados;
		if (nvisitados != nullptr)
			delete nvisitados;
		if (depositos != nullptr)
			delete depositos;
		if (recargas != nullptr)
			delete recargas;
		if (sujeiras != nullptr)
			delete sujeiras;
		if (movimentar != nullptr)
			delete movimentar;
			
		delete socketReceive;
		delete socketSend;
	}
};

int main(int argc, char** argv) {
	srand(time(NULL));
	AspiradorIII(atoi(argv[1]), argv[2], argv[3], argv[4]);
	return 0;
}
