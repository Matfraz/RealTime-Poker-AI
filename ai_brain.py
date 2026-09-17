import torch
import numpy as np
import torch.nn as nn
import torch.optim as optim
import os

class PokerBrain(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(PokerBrain, self).__init__()

        # 1. Primo strato (fc1): da input_dim a 128 neuroni
        # 2. Secondo strato (fc2): da 128 neuroni a 128 neuroni
        # 3. Terzo strato (fc3 - Output): da 128 neuroni a output_dim
        
        self.fc1 = nn.Linear(input_dim, 128)
        self.fc2 = nn.Linear(128, 128)
        self.fc3 = nn.Linear(128, output_dim)

    def forward(self, x):
        x = nn.functional.relu(self.fc1(x))
        x = nn.functional.relu(self.fc2(x))
        x = self.fc3(x)
        
        return x


def load_bot():
    device = torch.device("cpu")
    input_dim = 54    
    output_dim = 5 
    model = PokerBrain(input_dim, output_dim).to(device)
    if os.path.exists('poker_brain.pth'):
        model.load_state_dict(torch.load('poker_brain.pth', map_location=device))
        print("🧠 Cervello caricato con successo! Continuo l'addestramento.")   
    else:
        print("🆕 Nessun cervello trovato. Creo un'IA con pesi casuali da zero.")
    model.eval()
    return model