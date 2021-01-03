from parser import parser
import re


MODALS = ["must", "can", "should", "could", "may", "might"]


def getActiveTenseRule(tense):
    tenseList = {
        "PAST_SIMPLE":
            dict(aux=["did"], vtag=["VBD"]),
        "ALL": dict(aux=["do", "does", "did", "am", "is", "are", "have", "has", "was", "were", "had", "shall", "will",
                      "would", "should", "be"],
                    vtag=["VB", "VBZ", "VBP", "VBG", "VBN", "VBD"])
    }
    return tenseList.get(tense, "ALL")


def searchBatchesIndexes(text, batchSize):
    exp = r'[.?!](?= [A-Z]|$)'
    curIndex = 0
    findStart = 0
    batchIndixes = [0]
    sentenceFound = False

    while findStart < len(text):
        findStart = curIndex + batchSize
        findEnd = findStart + batchSize

        # Check if the right index is less or equal to the length of the text.
        if findEnd > len(text):
            findEnd = len(text)

        # Use Regex to find the end of a sentence in a text span.
        match = re.search(exp, text[findStart:findEnd])
        # If a match is found, recalculate the indices and add to the list.
        if match:
            curIndex = match.end() + findStart - 1
            batchIndixes.append(curIndex)
            sentenceFound = True
        else:
            # Just shift the index otherwise.
            curIndex += batchSize
            sentenceFound = False

    # Add the last index if there is significant text at the end of the raw text.
    if sentenceFound:
        batchIndixes.append(len(text))


    return batchIndixes


def searchBatchesActiveVoice(grammarTextGetter, text, grammarRule='ALL'):
    text = parser(text)
    batchIndexes = searchBatchesIndexes(text, 5000)
    textSplit = [text[batchIndexes[i - 1]:batchIndexes[i]] for i in range(1, len(batchIndexes))]

    docs = list(grammarTextGetter.pipe(textSplit))
    print(list(grammarTextGetter.pipe(textSplit)))

    tenseRule = getActiveTenseRule(grammarRule)

    activePhrases = []
    activePhrasesLexemes = []
    activePhrasesIndixes = []
    activePhrasesSent = []
    activePhrasesPos = []
    activePhrasesDep = []

    for currentBatch, doc in enumerate(docs):
        for sent in doc.sents:
            for token in sent:
                if token.tag_ in tenseRule.get('vtag'):
                    activeMatch = []
                    activeMatchIndixes = []
                    activeMatchLexemes = []
                    activeMatchPos = []
                    activeMatchDep = []

                    toInfMatch = []
                    subjectFound = False
                    prtContained = False

                    for child in token.children:
                        childLower = child.text.lower()
                        if child.dep_ == 'nsubj':
                            activeMatch.append(child.text)
                            if child.lemma_ == "-PRON-":
                                activeMatchLexemes.append(child.text)
                            else:
                                activeMatchLexemes.append(child.lemma_)
                            activeMatchIndixes.append([child.idx - sent.start_char,
                                                       child.idx + len(child) - sent.start_char])
                            activeMatchPos.append(child.pos_)
                            activeMatchDep.append(child.dep_)
                            subjectFound = True

                        if child.dep_ == 'auxpass':
                            activeMatch = []
                            activeMatchIndixes = []
                            activeMatchLexemes = []
                            activeMatchPos = []
                            activeMatchDep = []
                            break

                        if child.dep_ == 'aux':
                            if childLower in tenseRule.get('aux') or childLower in MODALS:
                                activeMatch.append(child.text)
                                activeMatchLexemes.append(child.lemma_)
                                activeMatchIndixes.append([child.idx - sent.start_char,
                                                           child.idx + len(child) - sent.start_char])
                                activeMatchPos.append(child.pos_)
                                activeMatchDep.append(child.dep_)
                            else:
                                activeMatch = []
                                activeMatchLexemes = []
                                activeMatchIndixes = []
                                activeMatchPos = []
                                activeMatchDep = []
                                break

                        if child.dep_ == 'xcomp':
                            for grandchild in child.children:
                                if grandchild.dep_ == 'aux':
                                    toInfMatch.append(grandchild)

                            toInfMatch.append(child)

                        if child.dep_ == 'neg':
                            activeMatch.append(child.text)
                            activeMatchLexemes.append(child.lemma_)
                            activeMatchIndixes.append([child.idx - sent.start_char,
                                                       child.idx + len(child) - sent.start_char])
                            activeMatchPos.append(child.pos_)
                            activeMatchDep.append(child.dep_)
                        if child.dep_ == 'prt':
                            activeMatch.append(token.text)
                            activeMatch.append(child.text)

                            activeMatchLexemes.append(token.lemma_)
                            activeMatchLexemes.append(child.lemma_)

                            activeMatchIndixes.append([token.idx - sent.start_char,
                                                       token.idx + len(token) - sent.start_char])
                            activeMatchIndixes.append([child.idx - sent.start_char,
                                                       child.idx + len(child) - sent.start_char])

                            activeMatchPos.append(token.pos_)
                            activeMatchPos.append(child.pos_)

                            activeMatchDep.append(token.dep_)
                            activeMatchDep.append(child.dep_)

                            prtContained = True
                    if activeMatch and subjectFound:
                        if not prtContained:
                            activeMatch.append(token.text)
                            activeMatchLexemes.append(token.lemma_)
                            activeMatchIndixes.append([token.idx - sent.start_char,
                                                       token.idx + len(token) - sent.start_char])
                            activeMatchPos.append(token.pos_)
                            activeMatchDep.append(token.dep_)

                        if toInfMatch:
                            [activeMatch.append(t.text) for t in toInfMatch]
                            [activeMatchLexemes.append(t.lemma_) for t in toInfMatch]
                            [activeMatchIndixes.append([t.idx - sent.start_char,
                                                        t.idx + len(t) - sent.start_char]) for t in toInfMatch]
                            [activeMatchPos.append(t.pos_) for t in toInfMatch]
                            [activeMatchDep.append(t.dep_) for t in toInfMatch]

                        batchIdx = batchIndexes[currentBatch]
                        activePhrases.append(activeMatch)
                        activePhrasesLexemes.append(activeMatchLexemes)
                        activePhrasesIndixes.append(activeMatchIndixes)
                        activePhrasesSent.append(text[batchIdx + sent.start_char:batchIdx + sent.end_char].strip())
                        activePhrasesPos.append(activeMatchPos)
                        activePhrasesDep.append(activeMatchDep)
                        pass

        result = [activePhrases, activePhrasesIndixes, activePhrasesLexemes,
                  activePhrasesSent, activePhrasesPos, activePhrasesDep]

        return result
