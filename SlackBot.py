import os
# Use the package we installed
from slack_bolt import App
# Import WebClient from Python SDK (github.com/slackapi/python-slack-sdk)
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_bolt.adapter.socket_mode import SocketModeHandler
import enum
import random
import pandas as pd
from collections import Counter
import firebase_admin
from firebase_admin import credentials,firestore
import inflect
from nltk.corpus import wordnet

p = inflect.engine()

if not firebase_admin._apps:
    cred = credentials.Certificate('firebaseKey.json') 
    default_app = firebase_admin.initialize_app(cred)

db = firestore.client()

app = App(token="SLACK_BOT_TOKEN")

def open_file(fileName):
    my_file = open(fileName, "r")
    content_list = my_file.readlines()
    return content_list

def check(todaysWord, guess): #performs wordle greens/yellows/greys
    checkWord = list("xxxxx")
    alreadyChecked = ""
    for i in range(5): #green check first
        if (todaysWord[i] == guess[i]):
            checkWord[i] = "!"
            alreadyChecked += guess[i]
    for i in range(5): #yellow check
        if (guess[i] in todaysWord and alreadyChecked.count(guess[i]) < todaysWord.count(guess[i]) and checkWord[i]!="!"):
            checkWord[i] = "*"
            alreadyChecked += guess[i]
        
        
    print("Result: ", ''.join(checkWord), "\n")
    return ''.join(checkWord)

def freq(possibleWords): #creates a dictionary of frequencies in the possible words by letter and word position. this is for final guessing
    # Create a letter occurrence dictionary
    df = pd.DataFrame()
    for i in range(5):
        letters = ''.join([word[i] for word in possible_words])
        letter_counts = dict(Counter(letters))
        new_letter_counts = dict({})
        for letter in letter_counts:
            newkey = letter + str(i)
            new_letter_counts[newkey] = letter_counts[letter]
        letter_counts = new_letter_counts
        letter_frequencies = {k:v/len(letters) for k,v in letter_counts.items()}
        letterDF = pd.DataFrame({'Letter+Num':list(letter_frequencies.keys()),'Frequency':list(letter_frequencies.values())})
        df = pd.concat([df,letterDF],ignore_index=True)
        
    return df

def freqLettersOnly(possibleWords): #creates a dictionary of frequencies in the possible words by if the letter is in the word or not. this is for fishing
    # Create a letter occurrence dictionary 
    words_string = ''.join(possibleWords)
    letter_counts = dict(Counter(words_string))
    # Create letter frequency dictionary
    letter_frequencies = {k:v/len(possibleWords) for k,v in letter_counts.items()}
    # Create letter frequency DataFrame
    letter_frequencies = pd.DataFrame({'Letter':list(letter_frequencies.keys()),'Frequency':list(letter_frequencies.values())}).sort_values('Frequency',                                                                                  ascending=False)
    return letter_frequencies
        
def isPossible(possible_word,bot_guess,result): #checks if a word is possible due to the clues that are given
    possibleWordList = list(possible_word)
    botGuessList = list(bot_guess)
    alreadyChecked = ""
    for i in range(5):
        if (result[i] == "!"): #green
            if (bot_guess[i] != possibleWordList[i]):
                return False
            else:
                alreadyChecked += bot_guess[i]
    for i in range(5):
        if (result[i] == "*"): #yellow
            if (bot_guess[i] not in possible_word or bot_guess[i] == possible_word[i] or alreadyChecked.count(bot_guess[i]) == possible_word.count(bot_guess[i])):
                return False
            else:
                alreadyChecked += bot_guess[i]
        elif (result[i] == "x"): #grey
            if (bot_guess[i] in possibleWordList and alreadyChecked.count(bot_guess[i]) != possible_word.count(bot_guess[i])):
                return False
    
    return True

def isPossibleFish(possible_fish,bot_guess,result): #eliminates words that are not possible to fish for to make program run faster
    if (result.count("!") >= 2 or result.count("*") >= 2):
        for i in range(5):
            if result[i] in ["!","*"] and bot_guess[i] in possible_fish:
                return False
    return True

def reduceWords(wordleWordsData, fullGuessPW, result, bot_guess): #reduces possible word pool to guess from. wordArr[0] is the word
     return [wordArr for wordArr in wordleWordsData if isPossible(wordArr[0],bot_guess,result)], [possible_fish for possible_fish in fullGuessPW if isPossibleFish(possible_fish,bot_guess,result)]

def calcScore(freqdf, word): #calculates the score for a guess word
    score = 0
    for i in range(5):
        dfSearch = word[i] + str(i)
        letterNumlist = list(freqdf["Letter+Num"])
        freqlist = list(freqdf["Frequency"])
        score = score + freqlist[letterNumlist.index(dfSearch)]
    return score
        
def calcFishScore(freqdf, word): #calculates the score for a fish word
    score = 0
    alreadyCounted = ""
    for i in range(5):
        if (word[i] not in alreadyCounted):
            dfSearch = word[i]
            letterNumlist = list(freqdf["Letter"])
            freqlist = list(freqdf["Frequency"])
            if (dfSearch in letterNumlist):
                score = score + freqlist[letterNumlist.index(dfSearch)]
            alreadyCounted+=word[i]
    
    return score

def nextGuess(wordleWordsData, fullGuessPW, guessNum, prevResult): #calculates the next guess based on the maximum fish score out of the fish pool against the maximum solve score in the solve pool
    engFreqs = []
    possible_words = []
    for wordArr in wordleWordsData:
        possible_words.append(wordArr[0])
        engFreqs.append(wordArr[1])
    
    freqdf = freq(possible_words)
    freqdfLettersOnly = freqLettersOnly(possible_words)
    freqdfLettersOnly.drop(freqdfLettersOnly.index[freqdfLettersOnly['Frequency'] > .99], inplace=True)
    lettersLeft = prevResult.count("x")
    greens = prevResult.count("!")
    guessesLeft = 6 - guessNum
    
    
    maxFishScore = 0
    bestFish = ""
    for word in fullGuessPW:
        wordScore = calcFishScore(freqdfLettersOnly, word)
        if wordScore > maxFishScore:
            maxFishScore = wordScore
            bestFish = word
    
    maxScore = 0
    guessWord = ""
    for wordArr in wordleWordsData:
        wordScore = calcScore(freqdf, wordArr[0]) + float(wordArr[1])/10 #adding the freq in english language / 10 to prioritize more common words
        if wordScore > maxScore:
            maxScore = wordScore
            guessWord = wordArr[0]
    maxScore = maxScore - greens
    
    fishingConstant = 2
    
    if (maxFishScore > maxScore and guessNum != 5):
        print("Fished")
        return bestFish
    
    print("Calced")  
    return guessWord

def sendMessage(message, channel, printTo): #this sends the message to the slack or prints to terminal
    if (printTo == "slack"):
        channel_id = channel
        result = app.client.chat_postMessage(
            channel=channel_id,
            text=message
            # You could also use a blocks[] array to send richer content
        )
    else:
        print(message)
    
def isNotPlural(word): #checks if removing 1 or 2 chars is a word and if it is equal to plural of that word
    if ((wordnet.synsets(word[:4]) and p.plural(word[:4]) == word) or (wordnet.synsets(word[:3]) and p.plural(word[:3]) == word)):
        return False
    return True

msg = ""
while (msg.strip() != "init" and msg.strip() != "solve"):
    msg = input("solve or init?")
    if (msg == "solve"):

        # ID of channel you want to post message to
        channel_id = "SLACK_CHANNEL_ID"

        wordleWordsData = open_file("words_data.txt")
        wordleWordsData = [word[:len(word)-1].split("/") for word in wordleWordsData] #this contains the word, frequency in english language (more common words appear more often we think), and definition


        possible_words = [wordArr[0] for wordArr in wordleWordsData] #[word,frequency,definition]
        freqs = [float(wordArr[1]) for wordArr in wordleWordsData]
        
        full_possible_words = open_file("five_letter_words.txt")
        full_possible_words = [word[:5] for word in full_possible_words]

        fullGuessPW = set(full_possible_words + possible_words)

        print("Welcome to Wordle")
        #INSERT TEST WORD HERE IF DESIRED
        #--------------------------------------------------------------------------------------------------------------
        #todays_word = ""
        todays_word = db.collection("rememberVars").document("WOTD").get().to_dict()["word"]
        todays_num = db.collection("rememberVars").document("wordleNumber").get().to_dict()["num"]

        first_guess = "roate"
        result = ""

        letterfrequency = freq(possible_words)

        message = "Wordle "+ str(todays_num) + " !/6\n\n"
        won = False
        print(todays_word)
        for i in range(6):
            if (i == 0):
                bot_guess = first_guess
            else:
                bot_guess = nextGuess(wordleWordsData, fullGuessPW, i, result)
            print("Bot's Guess " + str(i+1) + ": ", bot_guess, end=" ")
            result = check(todays_word, bot_guess)
            message = message + result.replace("x",":black_large_square:").replace("*",":large_yellow_square:").replace("!",":large_green_square:")+"\n"
            if (result == "!!!!!"):
                message = message.replace("!",str(i+1))
                print("I won in " + str(i+1) + " tries!\n\n\n")
                printTo = ""
                while (printTo.strip() != "terminal" and printTo.strip() != "slack"):
                    printTo = input("Send to terminal or slack?")
                    sendMessage(message, channel_id, printTo)
                won = True
                break
            wordleWordsData, fullGuessPW = reduceWords(wordleWordsData, fullGuessPW, result, bot_guess)
            possible_words = [wordArr[0] for wordArr in wordleWordsData]
            print(possible_words)

        if not won:
            print("I lost!\n\n\n")
            message = message.replace("!","X")
            printTo = ""
            while (printTo.strip() != "terminal" and printTo.strip() != "slack"):
                printTo = input("Send to terminal or slack?")
                sendMessage(message, channel_id, printTo)
    
    elif (msg == "init"):
        channel_id = "SLACK_CHANNEL_ID"
        print("hi")
        scores = db.collection("Users").document("U03BQ8FFR0A").get().to_dict()
        print("hi")
        message = "!init ShahinNazarian " + str(scores['Scores']['1']) + " " + str(scores['Scores']['2']) + " " + str(scores['Scores']['3']) + " " + str(scores['Scores']['4']) + " " + str(scores['Scores']['5']) + " " + str(scores['Scores']['6']) + " 100"
        printTo = ""
        while (printTo.strip() != "terminal" and printTo.strip() != "slack"):
            printTo = input("Send to terminal or slack?")
            sendMessage(message, channel_id, printTo)

raise Exception("Come back tomorrow! :)")
        
# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, "SLACK_APP_TOKEN").start()