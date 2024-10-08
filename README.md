Summary
=======

Llamara3 is self-hosted female ollama powered personal assistant character AI focused around productivity management that is actually useful, with extensive feature augmentations, which communicates to people via voice messages over XMPP (alike Whatsapp) or Discord in PM. 

https://github.com/user-attachments/assets/be2e3c36-11c5-4c1b-86bb-cd3e17e70158

Features
========

* keeps track of your schedule (breakfast, work, lunch, sleep, etc)
* incorporates Google calendar tasks
* helps you to fulfill everyday tasks, such as eating, sleeping or working
* motivates you when unproductive or misbehaving
* has long-term memory of today and yesterday
* has strong complex personality
* can experience various mood swings
* stalks you when you don't respond
* is enabled to enforce various interactive and non-interactive punishments
* can enter different modes at will, such as forcing aplogies, punishing or hypnotizing you
* replaces emotional need for girlfriend on a deeper level

![diagram1](https://github.com/user-attachments/assets/6d6f6c3d-66b7-4191-9baa-f16577ab8dba)

Current State of Affairs and Demo
=================================

Discord demo: [https://discord.gg/DaDJGwyXMh](https://discord.gg/WFqq6NBrkr) .

Some features in the diagram are still in the process of being implemented, but close to finished:

1. Punishments and behavior enforcer are working, but bugged here and there and not fine-tuned (see todo.txt)
2. Gcal fetching is done, but the tasks are not processed by additional logic
3. Twitter, Bitcoin and denouncer punisher unimplemented

Please do not consider this a finished product yet. You can use it, but there is still quite some work to be done. 

I am mainly busy with pushing out features at this point. Queries are not optimized and such, and testing/tuning is only rudimentary. Have a look at "todo.txt" to get an idea.

Also I have switched to hermes3:8b-llama3.1-fp16 now and there are various issues with the model being 5x more verbose.


Requirements
============

It works quite fast and well with Llama3 16GB version on a 3090. If you use a smaller model, I think the first thing that will crap out is the behavior evaluation and the diary summary (current quality of this is only about 80%, and there are some double and tripe check mechanisms to account for poor output). I think there is still a lot of room for improvement though, if the queries are somewhat rewritten. You can help by testing better queries.

When I used llama3.1 vanilla, it would produce extreme gibberish. Make sure to start with recommended model.

Setup
=====

*Hint: You need to install a lot of unknown python packages first as well as ffmpeg. Please help by writing a requirements.txt.*

```
git clone https://github.com/ballerburg9005/llamara3
```

**Openedai-speech:**
```
conda activate conda3.11
git clone https://github.com/matatonic/openedai-speech
cp llamara3/assets/voice_sample.wav openedai-speech/voices/llamara.wav
cd openedai-speech
sed -i "s#voices/shimmer.wav#voices/shimmer.wav\n  llamara:\n    model: xtts\n    speaker: voices/llamara.wav#g" voice_to_speaker.default.yaml
pip install -U -r requirements.txt
python add_voice.py
bash startup.sh
```

**If using model from Ollama repo:**
```
# install ollama with your package manager
echo "test" | ollama run hermes3:8b-llama3.1-fp16
```

**If using gguf model from Huggingface (recommended):**

I am currently testing hermes3:8b-llama3.1-fp16 , before I used this model:

```
# install ollama with your package manager
git lfs install
git clone https://huggingface.co/cognitivecomputations/Llama-3-8B-Instruct-abliterated-v2-gguf
cd Llama-3-8B-Instruct-abliterated-v2-gguf
echo "FROM ./Llama-3-8B-Instruct-abliterated-v2.gguf" > Modelfile
ollama create Llama-3-8B-Instruct-abliterated-v2 -f Modelfile
```

**Register XMPP account:** https://providers.xmpp.net/

Beware that some providers impose data limits, offer only 30 days trials with full features and such things. I can personally only attest very well to Disroot, but registrations are closed as of this writing.

You can now also set up a Discord bot instead. Don't ask me how.

**Set up model, XMPP login & run:**
```
cp config.json_example config.json
# edit config.json by hand (user/password for XMPP, or just token for Discord bot)
python run_xmpp.py
#python run_discord.py
```

**Using XMPP:**

XMPP works just like Whatsapp, if you use a good client like [Conversations](https://f-droid.org/packages/eu.siacs.conversations/) for mobile or Gajim (Linux) or AstraChat (Windows). Conversations is only free if you get it from the free software F-Droid store.

https://xmpp.org/software/

**Setting up Google calendar:**

This will probably be super annying. Follow instructions in #setgoogle_service_account_json_key

Talking to the model
====================

Llamara3 will work out of the box with example data (excl. Google calendar). Llamara3 will send you an intro message and give you instructions (type # for commands and help).

*Hint: RESET! only resets the current model dialogue buffer for the character and the behavior enforcer. It does not affect long-term memory and other systems.*

Anyone can talk to your Llamara3 who knows the XMPP handle, and conversely Llamara3 can also message other people. The latter is currently not used. At the moment, anyone who talks to Llamara3 is just assumed to be a new user, and there is no exchange of information between them.

![216_2023_4740_Figa_HTML](https://github.com/user-attachments/assets/86190512-202a-4053-934b-90f6af902f79)


Debugging
=========
You can re-run one of the last payloads with this command, to see how reproducible the output is.

```
LAST=1; wget --method=POST --header="Content-Type: application/json" --body-file=debug_last_payload${LAST}.json http://localhost:11434/api/chat -O- 2>&/dev/null | jq '.message.content'
```
License
=======

GPLv3
