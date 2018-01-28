# Parser class -a custom set of expressions gets converted to regex expressions using following (assumed)input rules:
# 1. (REQUIRED) C|W|S|L ?- C-searching for chars (added to enable subbing to replace characters as well as whole words)
#                          W-searching for whole words
#                          S-searching for sentences (from '.' to '.', returning only the trailing dot)
#                          L-searching for whole lines (^ to $ in multiline mode)
#
# 2. (OPTIONAL) R ?- enable subbing mode, the following expression rules require only 2 words, separated by a comma
#                    first word being the expression to be searched for, the second, what that expression is replaced w\
#
# 3. (OPTIONAL)n-m(numeric) ?- minimum and maximum values of C,W - letters or S,L - words
#
# 4. (REQUIRED 1 OF) word expressions ?- word expressions allow char sequences in double quotemarks ("abc")
#                                        word expressions are separated by commas ","
#                                        special characters: \N ?- a number exists in the word\sentence\line
#                                                            \U ?- several uppercase only letters in a sequence
#                                                            \L ?- several lowercase only letters in a sequence
#                                                            \u ?- one uppercase letter
#                                                            \l ?- one lowercase letter
#                                                            + ?- adding several symbols without ordering
#                                                            - ?- negation of next symbol


import re


class parser:

    # dict -substitute assigned mods with python re regex mods
    def __identifyMod(self, mod):
        return {
            'N':'(?=.*?[0-9]+)',
            'U':'[A-Z]+',
            'u':'[A-Z]',
            'L':'[a-z]+',
            'l':'[a-z]',
            r'-u':'[^A-Z]',
            r'-U':'[^A-Z]+',
            r'-L':'[^a-z]+',
            r'-N':'(?![0-9])',
            r'-l':'[^a-z]'
        }[mod]


    # dict -identify search mode, returns the front and the back of final regex pattern
    def __idMode(self, mode):
        return{
            'W':['\\b','\\w*?\\b'],
            'S':['(?:[.]|^).*?','.*?[.]'],
            'L':['^','.*?$'],
            'C':['',''],
            'R':'R'
        }[mode]

    # subbing mode, ran instead of searching when 'R' is present in input string
    def __sub(self,regex,sub,text):
        x= re.compile(regex,re.MULTILINE|re.DOTALL)
        r = x.sub(sub["word"], text)
        return r


    #searches the supplied text using last input, returns all matched strings
    def search(self,text):
        matches = []
        crit = ['{','}']
        if self.sub != None:
            return self.__sub(self.inputExpression,self.sub,text)
        regex = re.compile(self.inputExpression,re.MULTILINE|re.DOTALL)

        mList = regex.findall(text)
        if self.mode == self.__idMode('W'):
            crit = ['.{','}\\b']

        elif self.mode == self.__idMode('S') or self.__idMode('L'):
            crit =['^(\\b\w+\\b\W*){','}$']

        for i in mList:
            if self.min==-1:
                matches.append(i)
            elif self.max==-1:
                x =re.match(crit[0]+self.min +','+crit[1] ,i)
                if x is not None: matches.append(x.group(0))
            else:
                x =re.match(crit[0]+self.min +','+self.max+crit[1],i)
                if x is not None: matches.append(x.group(0))
        self.lastMatches = matches
        return matches


    # splits word expressions into actual words, separating them with empty strings on plus signs,
    # clears slashes, assigns group numbers to words to identify whether order matters
    def __wordCleanup(self, words):

        for nr,i in enumerate(words):
            i["word"] = re.sub(r',', '', i["word"])
            i["word"] = re.sub('\\\\','',i['word'])
            i["word"] = re.sub('\\\\','',i['word'])
            if r'+' in i["word"]:
                i["word"] = re.split(r'\+',i['word'])
                self.permutable = True
                for w,un in enumerate(i["word"]):
                    i['word'][w] = [un,nr]
        return words


    # regex is not very useful with searching for permutations of strings, initially for each permutation of words
    # was created, and then matched separately, this has been replaced with a less accurate solution of just searching
    # to see whether all of the words to be permuted exist past certain point, in any order. this was done to save on
    # computing time, as for every permutation program time increases twofold
    def __createPermutations(self, rExpressions):
        orGroups = []
        for n, i in enumerate(rExpressions):
            if rExpressions[n - 1][1] == i[1] or rExpressions[n + 1][1] == i[1]:
                orGroups.append(i[1])
        for i in set(orGroups):
            for j in rExpressions:
                if j[1]==i:
                    if j[0][0:2] == '.*?':
                        j[0] = '(?=' + j[0] + ')'
                    elif j[0][0:4]!='(?!.':
                        j[0] = '(?=.*?' + j[0] + ')'

        return rExpressions


    # concatenates all regex expressions
    def __createSearch(self, rExpressions):
        regex = ''
        if self.permutable == True :
            rExpressions= self.__createPermutations(rExpressions)
        for i in rExpressions:
            regex = regex + i[0]
        regex = self.mode[0] +regex + self.mode[1]
        self.inputExpression = regex


    # translates input into python regex expressions
    def __toRegexExpression(self, exp):
        retString = ''
        cont = 0
        for i in range(0,len(exp)):
            if i<cont: continue
            if exp[i]=='"':
                for j in range(i+1,len(exp)):
                    if exp[j]=='"':
                        retString = retString +exp[i+1:j]
                        cont = j+1
                        break
                continue
            if exp[i] == '-' :
                i = i + 1
                if exp[i]== '"':
                    for j in range(i + 1, len(exp)):
                        if exp[j] == '"':
                            retString = retString +'(?!.*?'+exp[i + 1:j]+')'
                            cont = j
                            break
                    continue
                retString = retString + self.__identifyMod('-' + exp[i])
                cont = i+1
            else :
                retString = retString + self.__identifyMod(exp[i])
        return retString


    # input processing function, calls everything needed to go from user input to searchable regex expression
    # the expression is returned and saved inside class variable
    def inputPattern(self,text):
        modeMinMax = re.compile("(?P<mode>[WSLC])" #get mode value
                        "(?P<replace>[R])?"
                        "(?P<minimum>\d+)?" # get minimum value if any
                        "-?"
                        "(?P<maximum>\d+)?") # get maximum value if any
        match = modeMinMax.match(text)


        self.mode = self.__idMode(match.group('mode'))
        self.sub = match.group("replace")

        if match.group('minimum') is not None:
            self.min = match.group('minimum')
            if match.group('maximum') is not None:
                self.max = match.group('maximum')
        text = text[match.span(0)[1]-1:]

        separateIntoWords = re.compile(r'(?:[WSLCR0-9]*)(?P<word>.+?(?:,|$))') #assume words are divided by ','
        match = [m.groupdict() for m in separateIntoWords.finditer(text)]

        if self.sub != None:
            self.sub = match[1]
            match = [match[0]]

        self.__wordCleanup(match)
        for n,i in enumerate(match):
            if isinstance(i['word'],list):
                for j in i['word']:
                    self.regexList.append([self.__toRegexExpression(j[0]), n])
            else :self.regexList.append([self.__toRegexExpression(i['word']), n])

        self.__createSearch(self.regexList)


    def __init__(self):
        self.permutable = False
        self.inputText = ''
        self.min = -1
        self.max = -1
        self.mode = 'W'
        self.wordMatches = []
        self.regexList = []
        self.lastMatches = []
        self.sub = None


#CLASSEND###############################################################################################################


if __name__ =='__main__':
    #fi = open(os.path.join(os.path.expanduser('~'), 'Documents', 'b.txt'))
    ini = parser()
    ini.inputPattern(r'') #passing raw strings required
    print(ini.search(''))