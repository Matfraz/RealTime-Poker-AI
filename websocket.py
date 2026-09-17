from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict
import rlcard
import json
from fastapi.responses import HTMLResponse
import os
from ai_brain import PokerBrain, load_bot
import torch
import numpy as np
import torch.nn as nn
import torch.optim as optim

NOMI_MOSSE = {
    0: "Fold 🏳️", 1: "Check / Call 💵", 
    2: "Raise Min 💰", 3: "Raise Max 🔥", 4: "All-In 🚀"
}


app = FastAPI(title="Poker Multiplayer Server")

@app.get("/", response_class=HTMLResponse)
async def get_homepage():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>File index.html non trovato nel server!</h1>"

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.env = None         
        self.player_names = [] 
        self.bankrolls = {} 
        self.model = load_bot()
        self.device = next(self.model.parameters()).device

    async def connect(self, player_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[player_id] = websocket

    def disconnect(self, player_id: str):
        if player_id in self.active_connections:
            del self.active_connections[player_id]

    async def broadcast(self, message: str):
        connessioni_morte = []
        for player_id, connection in self.active_connections.items():
            try:
                await connection.send_text(message)
            except Exception:
                connessioni_morte.append(player_id)
        
        for p_id in connessioni_morte:
            self.disconnect(p_id)

    async def send_private(self, player_id: str, message: str):
        if player_id in self.active_connections:
            try:
                await self.active_connections[player_id].send_text(message)
            except Exception:
                self.disconnect(player_id)

    async def broadcast_json(self, data: dict):
        connessioni_morte = []
        for player_id, connection in self.active_connections.items():
            try:
                await connection.send_json(data)
            except Exception:
                connessioni_morte.append(player_id)
                
        for p_id in connessioni_morte:
            self.disconnect(p_id)

    async def send_private_json(self, player_id: str, data: dict):
        if player_id in self.active_connections:
            try:
                await self.active_connections[player_id].send_json(data)
            except Exception:
                self.disconnect(player_id)

    async def aggiorna_carte_tavolo(self):
        for indice_giocatore, nome_giocatore in enumerate(self.player_names):
            stato = self.env.get_state(indice_giocatore)
            
            raw = stato.get('raw_obs', {})
            carte_in_mano = raw.get('hand', [])
            carte_pubbliche = raw.get('public_cards', [])
            pot_grezzo = raw.get('pot', 0)
            pot = int(pot_grezzo) 
            
            stakes = raw.get('stakes', [])
            
            if indice_giocatore < len(stakes):
                soldi_giocatore = int(stakes[indice_giocatore])
            else:
                soldi_giocatore = 0
            
            pacchetto = {
                "tipo": "aggiornamento_carte",
                "mano": carte_in_mano,
                "pubbliche": carte_pubbliche,
                "piatto": pot,
                "mie_fiches":soldi_giocatore
            }
            await self.send_private_json(nome_giocatore, pacchetto)


manager = ConnectionManager()

@app.websocket("/ws/{player_id}")
async def websocket_endpoint(websocket: WebSocket, player_id: str):
    await manager.connect(player_id, websocket)
    count = len(manager.active_connections)
    await manager.broadcast(f"🎉 {player_id} si è seduto al tavolo! (Totale giocatori: {count})")
    
    await manager.send_private(player_id, f"👋 Benvenuto al tavolo, {player_id}! Sei pronto a giocare?")

    try:
        while True:
            data = await websocket.receive_text()
            try:
                dati_ricevuti = json.loads(data)
                AI = False
                if dati_ricevuti.get("comando") == "START":
                    usa_ai = dati_ricevuti.get("usa_ai")
                    if (usa_ai):
                            AI = True
                    if len(manager.active_connections)>=2 or AI:
                        await manager.broadcast("🃏 La partita inizia! Il mazziere mescola le carte...")
                            
                        manager.player_names = list(manager.active_connections.keys())
                        if AI:
                            bot = 1
                            manager.player_names.append("Bot")
                            if "Bot" not in manager.bankrolls:
                                manager.bankrolls["Bot"] = 1000
                        else:
                            bot = 0

                        for nome in manager.player_names:
                            if nome not in manager.bankrolls:
                                manager.bankrolls[nome] = 1000
                        
                        manager.env = rlcard.make('no-limit-holdem', config={'game_num_players': len(manager.active_connections) + bot})
                        state, next_player = manager.env.reset()
                        await gestisci_prossimo_turno(manager)
                                           
                    else:
                        await manager.send_private(player_id, "Servono almeno 2 giocatori per iniziare!")
                        errore = {
                            "tipo": "errore_avvio", "messaggio": "Servono almeno 2 giocatori per iniziare!"
                        }
                        await manager.send_private_json(player_id, errore)
                else:
                        action = dati_ricevuti["azione"]

                        if manager.env is None:
                                await manager.send_private(player_id, "Nessuna partita in corso!")
                                continue

                        current_player_id = manager.env.get_player_id() 
                        active_player_name = manager.player_names[current_player_id]

                        if player_id != active_player_name:
                            await manager.send_private(player_id, "Non fare il furbo, non è il tuo turno!")
                            continue
                        
                        next_state, next_player = manager.env.step(action)
                        
                        nome_azione = NOMI_MOSSE.get(action, f"Mossa {action}")
                        await manager.broadcast_json({
                            "tipo": "notifica_azione", 
                            "messaggio": f"👤 {player_id} sceglie: {nome_azione}"
                        })
                        
                        await gestisci_prossimo_turno(manager)
                        await gestisci_prossimo_turno(manager)

            except (json.JSONDecodeError, TypeError, KeyError):
                await manager.broadcast(f"💬 {player_id}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(player_id)
        count = len(manager.active_connections)
        await manager.broadcast(f"🚪 {player_id} ha lasciato il tavolo. (Rimasti: {count})")

async def gestisci_prossimo_turno(manager):
    while True:
        if manager.env is None:
            return

        if manager.env.is_over():
            payoffs = manager.env.get_payoffs()
            risultato = "🏆 MANO FINITA! Risultati:\n"
            for i, nome in enumerate(manager.player_names):
                risultato += f"- {nome}: {payoffs[i]}\n"
                manager.bankrolls[nome] += int(payoffs[i]) 
            
                dati_fine = {
                    "tipo": "fine_mano", 
                    "bankrolls": manager.bankrolls,
                    "riassunto": risultato
                }
            await manager.broadcast_json(dati_fine)
            await manager.broadcast(risultato)
            manager.env = None #
            return
        
        await manager.aggiorna_carte_tavolo()
        current_player_id = manager.env.get_player_id()
        nome_giocatore = manager.player_names[current_player_id]
        stato = manager.env.get_state(current_player_id)

        if nome_giocatore != "Bot":
            raw_legal_actions = stato["legal_actions"]
            legal_actions_list = list(raw_legal_actions.keys()) if isinstance(raw_legal_actions, dict) else list(raw_legal_actions)
            
            dati_gioco = {
                "tipo": "cambio_turno",
                "giocatore_attivo": nome_giocatore,
                "azioni": legal_actions_list
            }
            await manager.broadcast_json(dati_gioco)
            return 
            
        else:
            await manager.broadcast("🤖 L'AI sta pensando...")
            raw_legal_actions = stato["legal_actions"]
            legal_actions_list = list(raw_legal_actions.keys()) if isinstance(raw_legal_actions, dict) else list(raw_legal_actions)
            obs = stato['obs'] 
            obs_tensor = torch.FloatTensor(obs).unsqueeze(0).to(manager.device)
                                            
            with torch.no_grad(): 
                q_values = manager.model(obs_tensor).cpu().numpy()[0] 
                                                
                masked_q_values = np.full(5, -1e9)
                for action_id in legal_actions_list:
                    masked_q_values[action_id] = q_values[action_id]
                                                
                best_action = int(np.argmax(masked_q_values))
                
                nome_azione_bot = NOMI_MOSSE.get(best_action, f"Mossa {best_action}")
                await manager.broadcast_json({
                    "tipo": "notifica_azione", 
                    "messaggio": f"🤖 Il Bot sceglie: {nome_azione_bot}"
                })
                
                manager.env.step(best_action)