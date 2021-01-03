import json
import spacy
from flask import Flask, request, jsonify, make_response, render_template
from parser import parser
from spacyLogic import searchBatchesActiveVoice
txtPath = '/Users/controldata/PycharmProjects/-dot.creators-Grammar-App/server/'
app = Flask(__name__)



def fileWritter(parsedText, result):
    with open(txtPath + 'rawTextWithoutPerfectParsing.txt', 'w') as textFile:
        textFile.writelines(parsedText)
    with open(txtPath + 'parsedText.txt', 'w') as textFile:
        textFile.writelines(str(result))


def spacyInstallizing(spacyLanguage):
    entities = spacyLanguage.create_pipe("merge_entities")
    chunks = spacyLanguage.create_pipe("merge_noun_chunks")
    spacyLanguage.add_pipe(entities, chunks)
    return spacyLanguage
grammarTextGetter = spacyInstallizing(spacy.load("en_core_web_sm"))
# print(searchBatchesActiveVoice(grammarTextGetter, parser.text1, 'PAST_SIMPLE'))


def convertToJsonList(result):
    readyVerb = result[0]
    readyVerbListLenght = len(readyVerb)
    rawVerb = result[2]
    perhaps = result[3]
    stringToResult = '['
    for i in range(readyVerbListLenght):
        dictToResult = {}
        dictToResult["readyVerb"] = readyVerb[i][len(readyVerb[i])-1]
        dictToResult["rawVerb"] = rawVerb[i][len(rawVerb[i])-1]
        dictToResult["perhaps"] = perhaps[i]
        stringToResult += json.dumps(dictToResult)
        if i != readyVerbListLenght - 1:
            stringToResult += ', '
        else:
            stringToResult += ']'
    return stringToResult


class result():
    def __init__(self, result=None):
        self._result = result

localResult = result()
@app.route('/')
@app.route('/get-text', methods=["POST"])
def index():
    gettedJson = request.get_json()
    print(gettedJson, '\n')
    text = parser(gettedJson['text'])
    print(text)
    result = searchBatchesActiveVoice(grammarTextGetter, text, 'PAST_SIMPLE')
    localResult._result = result
    fileWritter(text, result)
    print(result[0])
    print(result[2])
    print(result[3])
    # with open(f"{txtPath}tmp.pkl", 'rw') as f:
    #     pickle.dump(list, f)
    return jsonify(gettedJson)



@app.route('/get-test')
def testSender():
    return convertToJsonList(localResult._result)

if __name__ == '__main__':
    app.debug = True
    app.run(host='192.168.0.14', port=5000)








