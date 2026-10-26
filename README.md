Self-hosted web interface for local AI services.
Requirements

- Windows, Linux, or macOS
- Python 3.10+
- Ollama installed and available on `PATH`

Start
   just run in a terminal of some sort python start_webpage.py 
   if it throws an error about missing librays try pip install (libray name here)

Access from another device on Windows

1. Start the server and use the LAN address printed in the terminal, for example
   http://10.0.0.(deviceip):5000.
2. Allow Python through Windows Defender Firewall when Windows asks. Create an inbound TCP rule for port 5000 in Windows Defender Firewall or use:
   New-NetFirewallRule -DisplayName "Ollama Web UI" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow -Profile Private
3. Both devices must be on the same Wi-Fi/LAN. 

Services

Ollama make sure its installed or the code likes to break


# The goal of this project is to make AI localy avalible to everyone with just one decently powerfull device per user group. The goal is to have chatbots images and hopfully eventually agentic work.
This project hosts a webpage any devices on the same network can accses. Right now there is no memory or images but im working on that and it will hopfully be added later. For the text which is implemented now any ollama model should work and it has built in pulling.
Eventually I might add model recomendatons and stuff based on pc specs or mabey a benchmark or somthing. Video generation might be possible but It takes a lot of compute unless there is a new model i havent found yet. 
I also plan to add api support in the future once i have memeory and stuff to make it worthwhile. 


The setup folder is writen by ai so it hopfully will work for you for now but i plan to rewrite it by hand when i have some time.

There are now two animated backgrounds to chose between rainy moutains and prarie grain silo with more to come some based on weeks themes for Tera. 

Very helpfull website: https://docs.ollama.com/

Also if it seems like its doing nothing with bigger models just give it a while ill try to add loading or thinking later
Also make sure to allow incoming on port 5000 on your host machine

Future plans:
Full project will have to be moved over to linux for now, should create file sharing and jellyfin/samba for file sharing. There is a tag to open other websites in html apprently the <iframe src="https://example.com" width="600" height="400" title="Example Website"></iframe> This should allow it to open a jellyfin page inside of the page that the main site is running in
Local image generation is still to come hopfully. 
gogle calendar intergration or goggler calendar acses from inside of app.
forest with river animation to come in next weeks.
New backgrounds based on themes of coming weeks. 
The goal is to make this project a full smart home OS instead of just a ai interface now.

How this was made: 
Week 1: Created backend and simply had chatbot interface and pulling.
Week 2: Created 2 animated backgrounds so website is slightly visually appealing to look at.
