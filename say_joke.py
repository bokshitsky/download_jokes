import pyttsx3
engine = pyttsx3.init()

voices = engine.getProperty('voices')
ru_voices = [v for v in voices if [l for l in v.languages if 'RU' in l]]
engine.setProperty('voice', ru_voices[0].id)
engine.setProperty('rate', 150)
engine.say('ыфыф')

engine.save_to_file()