# The 'requests' and 'json' libraries are imported. 
# 'requests' is used to send HTTP requests, while 'json' is used for parsing the JSON data that we receive from the API.
import requests
import json

# An API key is defined here. You'd normally get this from the service you're accessing. It's a form of authentication.
XI_API_KEY = "bd183f07a43190394545e1a32efa4358"

# This is the URL for the API endpoint we'll be making a GET request to.
url = "https://api.elevenlabs.io/v1/voices"

# Here, headers for the HTTP request are being set up. 
# Headers provide metadata about the request. In this case, we're specifying the content type and including our API key for authentication.
headers = {
"Accept": "application/json",
"xi-api-key": XI_API_KEY,
"Content-Type": "application/json"
}

# A GET request is sent to the API endpoint. The URL and the headers are passed into the request.
response = requests.get(url, headers=headers)

# The JSON response from the API is parsed using the built-in .json() method from the 'requests' library. 
# This transforms the JSON data into a Python dictionary for further processing.
data = response.json()

# A loop is created to iterate over each 'voice' in the 'voices' list from the parsed data. 
# The 'voices' list consists of dictionaries, each representing a unique voice provided by the API.
for voice in data['voices']:
# For each 'voice', the 'name' and 'voice_id' are printed out. 
# These keys in the voice dictionary contain values that provide information about the specific voice.
    print(f"{voice['name']}; {voice['voice_id']}")




# Rachel; 21m00Tcm4TlvDq8ikWAM
# Drew; 29vD33N1CtxCmqQRPOHJ
# Clyde; 2EiwWnXFnvU5JabPnv8n
# Paul; 5Q0t7uMcjvnagumLfvZi
# Domi; AZnzlk1XvdvUeBnXmlld
# Dave; CYw3kZ02Hs0563khs1Fj
# Fin; D38z5RcWu1voky8WS1ja
# Sarah; EXAVITQu4vr4xnSDxMaL
# Antoni; ErXwobaYiN019PkySvjV
# Thomas; GBv7mTt0atIp3Br8iCZE
# Charlie; IKne3meq5aSn9XLyUdCD
# George; JBFqnCBsd6RMkjVDRZzb
# Emily; LcfcDJNUP1GQjkzn1xUU
# Elli; MF3mGyEYCl7XYWbV9V6O
# Callum; N2lVS1w4EtoT3dr4eOWO
# Patrick; ODq5zmih8GrVes37Dizd
# Harry; SOYHLrjzK2X1ezoPC6cr
# Liam; TX3LPaxmHKxFdv7VOQHJ
# Dorothy; ThT5KcBeYPX3keUQqHPh
# Josh; TxGEqnHWrfWFTfGW9XjX
# Arnold; VR6AewLTigWG4xSOukaG
# Charlotte; XB0fDUnXU5powFXDhCwa
# Alice; Xb7hH8MSUJpSbSDYk0k2
# Matilda; XrExE9yKIg1WjnnlVkGX
# James; ZQe5CZNOzWyzPSCn5a3c
# Joseph; Zlb1dXrM653N07WRdFW3
# Jeremy; bVMeCyTHy58xNoL34h3p
# Michael; flq6f7yk4E4fJM5XTYuZ
# Ethan; g5CIjZEefAph4nQFvHAz
# Chris; iP95p4xoKVk53GoZ742B
# Gigi; jBpfuIE2acCO8z3wKNLl
# Freya; jsCqWAovK2LkecY7zXl4
# Brian; nPczCjzI2devNBz1zQrb
# Grace; oWAxZDx7w5VEj9dCyTzz
# Daniel; onwK4e9ZLuTAKqWW03F9
# Lily; pFZP5JQG7iQjIQuC4Bku
# Serena; pMsXgVXv3BLzUgSXRplE
# Adam; pNInz6obpgDQGcFmaJgB
# Nicole; piTKgcLEGmPE4e6mEKli
# Bill; pqHfZKP75CvOlQylNhV4
# Jessie; t0jbNlBVZ17f02VDIeMI
# Sam; yoZ06aMxZJJ28mfd3POQ
# Glinda; z9fAnlkpzviPz146aGWa
# Giovanni; zcAOhNBS3c14rBihAFp1
# Mimi; zrHiDhphv9ZnVXBqCLjz