import requests
import json

def open_file(fileName):
    my_file = open(fileName, "r")
    content_list = my_file.readlines()
    return content_list

all_words_list = open_file("five_letter_words.txt")
print(len(all_words_list))

headers = {
     'x-rapidapi-host' : "wordsapiv1.p.rapidapi.com",
     'x-rapidapi-key' : "RAPID_API_KEY"
}
word_data = list()

for i in range(500):
    word = all_words_list[i].strip()
    url = "https://wordsapiv1.p.rapidapi.com/words/" + word
    url = url.strip()
    #response = requests.request("GET",url,headers=headers)
    if response.status_code == 200:
        data = response.json()

        if ("word" in data):
            if not (data["word"]):
                word = word
            else:
                word = (data["word"])
        else:
            word = word

        if ("frequency" in data):
            if not (data["frequency"]):
                freq = 0
            else:
                freq = (data["frequency"])
        else: 
            freq = 0

        if ("results" in data):
            if not (data["results"]):
                definition = "No defintion in database"
            elif not data["results"][0]:
                definition = "No defintion in database"
            elif ("definition" in data["results"][0] ):
                if not data["results"][0]["definition"]:
                    definition = "No defintion in database"
                else:
                    definition = data["results"][0]["definition"]
            else:
                definition = "No defintion in database"
        else:
            definition = "No defintion in database"
    else:
        word = word
        freq = 0
        definition = "No defintion in database"

    info_string = word + "/" + str(freq) + "/" + definition + "\n"
    word_data.append(info_string)
    #print(info_string)
for d in word_data:
    print(d)

with open('words_data_api.txt', 'a') as f:
    f.write("".join(word_data))
