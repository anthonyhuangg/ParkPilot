# ParkPilot 
A parking mobile app in Python and React Native enabling drivers to reserve and navigate to available parking spots. 

<div align="center"> 
  <video src="https://github.com/user-attachments/assets/8e2291eb-6029-49e3-985e-6b711cf529b6" width="360" controls></video> 
</div> 
<br>
<div align="center">
  <video src="https://github.com/user-attachments/assets/670f55ae-f30e-4178-8b99-0c3e32e9fde3" width="500" controls></video>
</div>

## Motivation
Inefficient parking allocation in large densely populated cities is a significant problem. Of the 460,000 vehicles that enter Sydney’s CBD every day, 30-50% are engaged in searching for parking at any given time. These vehicles contribute to 30% of downtown traffic congestion, resulting in 150,000 hours wasted and millions lost in fuel and productivity every year.

## Quick Start
### Requirements
- Expo (mobile app)
- Node: v18.20.4
- Npm: v10.9.3

1. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
```

2. Create a '.env' file
```bash
JWT_SECRET_KEY=your_jwt_secret_here
```

3. Start backend (Terminal 1)

```bash
cd backend
pip install -r requirements.txt
python main.py
```

4. Start frontend (Terminal 2)
```bash
cd frontend
npm install
npx expo start
```

4. Scan QR Code to open app using Expo (mobile)

## Usage
Features:
- Authentication
- Navigation
- Visualise carbon savings
- Historical occupancy (Parking Operator only)

#### UML Diagram
![Diagram](./docs/diagram.png)
[Edit the diagram](./docs/diagram.drawio)

## Contributing
### Clone the repo

```bash
git clone https://github.com/unsw-cse-comp99-3900/capstone-project-25t3-3900-f11a-date.git
cd capstone-project-25t3-3900-f11a-date
```
### Run frontend test suite
#### Download and open an Android emulator
You can follow this tutorial to set up an emulator:
https://www.youtube.com/watch?v=xKGESzemfdw

#### Run the frontend on the emulator
```bash
npx expo run:android
```

#### Run all tests
```bash
cd frontend
maestro test maestro
```

### Run backend test suite

```bash
cd backend
pytest
```

### Submit a pull request

If you'd like to contribute, please fork the repository and open a pull request to the `main` branch.

## Help
### Installing node and npm versions
1. Can get nvm or just download the node version 18.20.4. (nvm allows you to switch easily between node versions using 'nvm use 18.20.4') https://www.freecodecamp.org/news/node-version-manager-nvm-install-guide/
2. npm install -g npm@10.9.3


### Common things to watch out for
1. If you find that the frontend is not communicating with the backend (Login and Register are not taking you to the dashboard after pressing the button), check that the fetch url in the login and register screens match that in your frontend terminal (Underneath the QR code)













