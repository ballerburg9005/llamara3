Summary
=======
Llamara3 is self-hosted female ollama powered personal assistant character AI with extensive feature augmentations, that communicates to people via voice messages in an XMPP messenger (alike Whatsapp).

https://github.com/user-attachments/assets/906b3fa3-b787-47c1-af01-c4252b3fc116

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
I just uploaded this today and was amidst rewriting code ... if you want to try an older version without behavior enforcer, you can reach Llamara3 at this **XMPP handle: llamara3@xabber.org**

Some features in the diagram are still in the process of being implemented, but close to finished (punishments, behavior enforcer and Gcal).

Setup
=====

*Hint: You need to install a lot of unknown python packages first, please help by writing a requirements.txt.*

```
git clone https://github.com/ballerburg9005/llamara3
```

**Openedai-speech:**
```
conda activate conda3.11
cp llamara3/assets/voice_sample.wav voices/llamara.wav
git clone https://github.com/matatonic/openedai-speech
cp llamara3/assets/voice_sample.wav openedai-speech/voices/
cd openedai-speech
sed "s#voices/shimmer.wav#voices/shimmer.wav\n  llamara:\n    model: xtts\n    speaker: voices/llamara.wav#g" voice_to_speaker.default.yaml
pip install -U -r requirements.txt
python add_voice.py
bash startup.sh
```

**If using model from Ollama repo:**
```
# install ollama with your package manager
echo "test" | ollama run dolphin-llama3:8b-v2.9-fp16
```

**If using gguf model from Huggingface (recommended):**
```
# install ollama with your package manager
git clone https://huggingface.co/cognitivecomputations/Llama-3-8B-Instruct-abliterated-v2-gguf
cd Llama-3-8B-Instruct-abliterated-v2-gguf
echo "FROM ./Llama-3-8B-Instruct-abliterated-v2.gguf" > Modelfile
ollama create Llama-3-8B-Instruct-abliterated-v2 -f Modelfile
```

**Register XMPP account:** https://providers.xmpp.net/
Beware that some providers impose data limits, offer only 30 days trials with full features and such things. I can personally only attest very well to Disroot, but registrations are closed as of this writing.

**Set up model, XMPP login & run:**
```
cp config.json_example config.json
# edit config.json by hand
python bot.py
```

**Using XMPP:**
XMPP works just like Whatsapp, if you use a good client like [Conversations](https://f-droid.org/packages/eu.siacs.conversations/) for mobile or Gajim (Linux) or AstraChat (Windows). Conversations is only free if you get it from the free software F-Droid store.

https://xmpp.org/software/

**Talking to the model:**
Llamara3 will work out of the box with example data (excl. Google calendar). Llamara3 will send you an intro message and give you instructions (type # for commands and help).

*Hint: RESET! only resets the current model dialogue buffer for the character and the behavior enforcer. It does not affect long-term memory and other systems.*

Anyone can talk to your Llamara3 who knows the XMPP handle, and conversely Llamara3 can also message other people. The latter is currently not used. Anyone who talks to Llamara3 is just assumed to be a new user, and there is no exchange of information between them.
