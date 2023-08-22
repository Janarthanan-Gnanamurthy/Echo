import requests

def get_tts(link, name):
    url=link

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "AUTHORIZATION": "Bearer adfd5353bc934ff8b1223405604de8ea",
        "X-USER-ID": "WEkXcBCd5WNQiZv4QspWnEyBocT2"
    }

    response = requests.get(url, headers=headers)
    
    audio = response.content

    with open(f'static/tts/{name}.mp3','wb') as file:
        file.write(audio)
    
    
    print(f'\n <audio successfully generated for {name}> \n')


#get_tts('https://play.ht/api/v2/tts/O9V6vTg8WwCXo4GDqR?format=audio-mpeg','teszt')