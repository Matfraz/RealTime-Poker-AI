# Real-Time Multiplayer Poker with AI 🃏🤖

A fast, real-time No-Limit Texas Hold'em poker game built with **FastAPI**, **WebSockets**, and **PyTorch**. 
This project allows multiple players to connect to a virtual green table, play against each other, or challenge a trained AI model powered by a Deep Q-Network.

## 🚀 Features
*   **Real-Time Multiplayer:** Instant moves and state updates using asynchronous WebSockets.
*   **Deep Learning AI:** A custom neural network (`PokerBrain`) built with PyTorch, trained via Reinforcement Learning to master Texas Hold'em strategies.
*   **Interactive UI:** A modern, cyberpunk-themed HTML frontend with dynamic card rendering and action toasts.
*   **RLCard Integration:** Uses the official `rlcard` environment for robust poker logic and legal action masking.
*   **Scalable Backend:** FastAPI connection manager that handles player sessions, turn synchronization, and game states[.

## 🧠 AI Architecture & Training
The AI opponent is not rule-based; it learns entirely from experience using **Reinforcement Learning**ì.
*   **Neural Network (MLP):** The core is a Multi-Layer Perceptron built in PyTorch. It features an input layer representing the game state (54 dimensions), two hidden layers of 128 neurons each with ReLU activation, and an output layer for the 5 possible actions.
*   **Deep Q-Network (DQN):** The model predicts the expected future reward (Q-Value) for each legal action and chooses the most profitable one.
*   **Training Strategy:** The bot was trained using an epsilon-greedy strategy. A very slow epsilon decay was applied over hundreds of thousands of episodes to force the AI to aggressively explore raises and bluffs, successfully overcoming the common "always fold" local minimum.

## 📂 Project Structure
This repository contains the core files for the game engine and the web server:
*   `websocket.py`: The main backend application. It handles the FastAPI server, WebSocket connections, broadcast messages, and game loops.
*   `ai_brain.py`: Contains the PyTorch Multi-Layer Perceptron (MLP) architecture and the logic to load the AI bot into the server.
*   `poker_brain.pth`: The pre-trained weights for the neural network.
*   `index.html`: The frontend user interface. It connects to the WebSocket, displays the game, and handles user inputs.

## 🛠️ Installation and Setup

### 1. Requirements
Make sure you have Python 3.10+ installed. This project uses **`uv`**, a blazingly fast Python package manager, to handle dependencies via `pyproject.toml` and `uv.lock`.

To install the exact environment automatically, simply run:
uv sync
(Alternatively, if you don't use uv, you can install the libraries using standard pip: pip install fastapi uvicorn websockets rlcard torch numpy).

(Note: If you plan to deploy this on a free cloud service, it is highly recommended to install the CPU-only version of PyTorch to save RAM).

### 2. Running the Server
To start the game server locally, open your terminal in the project folder and run:

uv run uvicorn websocket:app --host 0.0.0.0 --port 8000
Then, open your web browser and go to http://localhost:8000. You can open multiple tabs to simulate multiple players.

### 🤖 The AI Opponent (poker_brain.pth)
This repository includes a pre-trained PyTorch model (poker_brain.pth) right out of the box!
To play against the AI:
* Start the server.
* Toggle the AI Mode switch on the table.  
* *Click Start Game.
The neural network is ready to challenge you. If you want to train your own custom bot, you can build and train a new model using RLCard and simply overwrite the existing .pth file in the root directory.

### 🎮 How to Play
* Enter your nickname to join the lobby.
* Wait for at least one more player to join (or toggle the AI Mode).  
* Click on Start Game.Use the interactive buttons (Fold, Check/Call, Raise Min, Raise Max, All-In) when it's your turn.  
* The winner is calculated automatically at the end of the hand! 