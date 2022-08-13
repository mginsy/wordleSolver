import enum
import random
from collections import Counter
from numpy import char
import pandas as pd
import matplotlib.pyplot as plt

def open_file(fileName):
    my_file = open(fileName, "r")
    content_list = my_file.readlines()
    return content_list

def first_guess(possibleWords):
    return random.choice(possibleWords)

def check(todaysWord, guess):
    checkWord = ""
    for i in range(5):
        if (todaysWord[i] == guess[i]):
            checkWord += "!"
        elif (todaysWord.find(guess[i]) != -1):
            checkWord += "*"
        else:
            checkWord += "x"
    print("Result: ", checkWord)
    print()

def freq(possibleWords):
    # Create a letter occurrence dictionary 
    words_string = ''.join(possibleWords)
    letter_counts = dict(Counter(words_string))
    # Create letter frequency dictionary
    letter_frequencies = {k:v/len(possibleWords) for k,v in letter_counts.items()}
    # Create letter frequency DataFrame
    letter_frequencies = pd.DataFrame({'Letter':list(letter_frequencies.keys()),'Frequency':list(letter_frequencies.values())}).sort_values('Frequency',                                                                                  ascending=False)
    print(letter_frequencies)
    letter_frequencies.plot(x ='Letter', y='Frequency', kind = 'bar')
    plt.show()

def freq2(possibleWords):
    print()
    rows, columns = (26, 5)
    freq = [[0]*columns]*rows
    print(freq)
    #freq = [[0] * 26 for x in range(5)]
    for word in possibleWords:
        for index, character in enumerate(word):
            # print(word)
            # print(ord(character) - 97)
            # print("index= ", index)
            # print("ord= ", (ord(character)%25))
            freq[index][(ord(character))%26] += 1

def test():
    d = []
    numWords = len(possibleWords)
    for word in possibleWords:
        prob = 1.0
        for index, letter in enumerate(word):
            prob *= (freq[index][ord(word[index]) - 97] / numWords)
        d.append([word,prob])

    bestWords = sorted(d, key=lambda x: x[1], reverse=True)
    for index in range(20):
        print(f"#{index+1:2}: {bestWords[index][0]}")


def main():
    content_list = open_file("five_letter_words.txt")

    print("Welcome to Wordle")
    todays_word = input("What is today's word: ")
    print()

    for i in range(6):
        bot_guess = first_guess(content_list)
        print("Bot's Guess: ", bot_guess, end="")
        check(todays_word, bot_guess)
    
    freq(content_list)
    #freq2(content_list)


if __name__ == "__main__":
    main()