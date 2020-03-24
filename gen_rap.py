import pronouncing as p
import markovify
import pickle
import random
import os

input_file = 'rap_lyrics.txt'

LINE_LENGTH = [6, 8]

class RapIndex:
    def __init__(self):
        self.rhyme_index = dict()
        self.markov_index = dict()

    # creation of a new index
    def add_markov(self, key, value):
        if key in self.markov_index:
            if value in self.markov_index[key]:
                self.markov_index[key][value] += 1
            else:
                self.markov_index[key][value] = 1
        else:
            entry = dict()
            entry[value] = 1
            self.markov_index[key] = entry
        
    def save(self, filename):
        with open(filename, "wb") as f:
            pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)

    def load(self, filename):
        with open(filename, "rb") as f:
            dump = pickle.load(f)
            self.markov_index = dump.markov_index
            self.rhyme_index = dump.rhyme_index
    
    def add_rhyme(self, word):
        # removing 'i' & 'a'
        if len(word) == 1 and word not in 'ia':
            return
        phones = p.phones_for_word(word)
        if len(phones) != 0:
            phones = phones[0].split(" ")
            i = len(phones) - 1
            stub = ""
            while i >= 0:
                if any(char.isdigit() for char in phones[i]):
                    if (stub+phones[i]) in self.rhyme_index:
                        self.rhyme_index[stub+phones[i]].add(word)
                    else:
                        self.rhyme_index[stub+phones[i]] = set([word])
                    break
                stub += phones[i]
                i -= 1

    # generation of lyrics
    def markov_next(self, word, no_stop=False, always_stop=False):
        if word not in self.markov_index:
            raise RuntimeError

        choices = []
        for key in self.markov_index[word]:
            for i in range(self.markov_index[word][key]):
                if no_stop and key == '--':
                    None # don't add
                else:
                    choices.append(key)
        if always_stop and '--' in choices:
            return '--'
        else:
            if len(choices) == 0:
                return '--'
            return random.choice(choices)
        
    def get_phonetic_end(self, word):
        phones = p.phones_for_word(word)
        if len(phones) != 0:
            phones = phones[0].split(" ")
            i = len(phones) - 1
            stub = ""
            while i >= 0:
                if any(char.isdigit() for char in phones[i]):
                    if (stub+phones[i]) in self.rhyme_index:
                        return stub+phones[i]
                stub += phones[i]
                i -= 1
        return None

    def get_rhyming_words(self, word):
        end = self.get_phonetic_end(word)
        words = [word for word in self.rhyme_index[end]]
        return words

    def get_random_rhyming_words(self, num=2):
        vowels = [key for key in self.rhyme_index]
        while len(vowels) > 0:
            choice = random.choice(vowels)
            if len(self.rhyme_index[choice]) < num:
                vowels.remove(choice)
            else:
                words = [word for word in self.rhyme_index[choice]]
                return_list = []
                while len(return_list) < num:
                    word_choice = random.choice(words)
                    return_list.append(word_choice)
                    words.remove(word_choice)
                return return_list
        return None
    
    def get_bars(self, chosen_words=None, num_bars=2):
        end_words = []
        if chosen_words == None or len(chosen_words) == 0:
            if num_bars == 1:
                end_words.extend(self.get_random_rhyming_words(num=4))
            else:
                for i in range(num_bars):
                    end_words.extend(self.get_random_rhyming_words(num=2))
        else:
            if len(chosen_words) == 2:
                end_words.extend(chosen_words)
                for word in chosen_words:
                    end_words.append(random.choice(self.get_rhyming_words(word)))
            elif len(chosen_words) == 1:
                end_words.extend(chosen_words)
                random_words = self.get_rhyming_words(end_words[0])
                for i in range(3):
                    random_word = random.choice(random_words)
                    end_words.append(random_word)
                    random_words.remove(random_word)
        bars = []
        for word in end_words:
            current_line = word
            current_word = word
            num_words = 1
            # real word
            while current_word != '--':
                # more space in the line; keep going
                if num_words < LINE_LENGTH[0]:
                    current_word = self.markov_next(current_word, no_stop=True)
                # no more space in the line; stop
                elif num_words > LINE_LENGTH[1]:
                    current_word = self.markov_next(current_word, always_stop=True)
                # in the middle; keep going or stop
                else:
                    current_word = self.markov_next(current_word)
                # don't add non-lyrics
                if current_word != '--' and current_word != " ":
                    current_line = current_word + " " + current_line
                    num_words += 1
            # this line is done
            bars.append(current_line) 
        return bars


def get_lyrics(end_words=None):
    index = RapIndex()
    index_name = input_file[0:(len(input_file)-4)]+".ind"

    if not os.path.exists(index_name):
        with open(input_file, "r") as f:
            for line in f:
                line = line.replace("\s+", " ")
                if line.strip() != "":
                    words = line.split(" ")
                    i = len(words) - 1
                    if i > 0:
                        index.add_rhyme(words[i].strip().lower())
                    while i > 0:
                        index.add_markov(words[i].strip().lower(), words[i-1].strip().lower())
                        i -= 1
                    index.add_markov(words[i].strip().lower(), "--")
        index.save(index_name)
    else:
        index.load(index_name)

    lyrics = []
    # number of verses to generate
    for i in range(1):
        # pick a rhyme scheme randomly
        if end_words == None or len(end_words) == 0:
            rhyme_scheme = random.randint(1,4)
        elif len(end_words) == 1:
            rhyme_scheme = 1
        else:
            rhyme_scheme = random.randint(2,4)
        if rhyme_scheme == 1: #AAAA
            lyrics.extend(index.get_bars(chosen_words=end_words,num_bars=1))
        elif rhyme_scheme == 2: #AABB
            lyrics.extend(index.get_bars(chosen_words=end_words,num_bars=2))
        elif rhyme_scheme == 3: #ABAB
            lyrics.extend(index.get_bars(chosen_words=end_words,num_bars=2))
            temp = lyrics[2]
            lyrics [2] = lyrics[1]
            lyrics [1] = temp
        elif rhyme_scheme == 4: #ABBA
            lyrics.extend(index.get_bars(chosen_words=end_words,num_bars=2))
            temp = lyrics[1]
            lyrics[1] = lyrics[3]
            lyrics[3] = temp
        # censoring
        for i in range(len(lyrics)):
            if "nigg" in lyrics[i]:
                lyrics[i] = lyrics[i].replace("nigg","n*gg")
            if "fag" in lyrics[i]:
                lyrics[i] = lyrics[i].replace("fag","f*g")
    return lyrics

def print_lyrics(final_lyrics):
    for i in range((len(final_lyrics))):
        print(final_lyrics[i])

if __name__ == "__main__":
    print_lyrics(get_lyrics())