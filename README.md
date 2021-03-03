# chat-program
![chat](https://user-images.githubusercontent.com/33904917/109864656-c269f180-7c6b-11eb-911b-36bde4563fe2.png) <br>
Whatsapp-like chat program. Contains a server and client written in python, with a QT frontend.

## Usage
First, run the server: `python src/backend/server.py` (port defaults to 8000) <br>
Then, the client app: `python src/app.py` <br>
The login window will pop up: <br>
![Screenshot from 2021-03-03 21-47-37](https://user-images.githubusercontent.com/33904917/109863267-1d024e00-7c6a-11eb-89cf-0e73987399b9.png) <br>
After entering your name and the IP & port of the desired server, you will be logged into the chat: <br>
![chat_window](https://user-images.githubusercontent.com/33904917/109862178-d06a4300-7c68-11eb-8851-fc8b12f9a633.jpeg)

### Commands
List of commands:
- `/help` - display this text.
- `/quit` - quit the chat group.
- `/view-managers` - view all members with manager permissions.
- `/tell [name] [msg]` - send a private message to a member.
- `/kick [name]` - remove a member from the chat group.
- `/promote [name]` - give a member manager permissions.
- `/demote [name]` - take a member's manager permissions.
- `/mute [name]` - make a member unable to send messages.
- `/unmute [name]` - make a member able to send messages.
